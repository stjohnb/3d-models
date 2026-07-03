#!/usr/bin/env python3
"""Content-addressed render cache key computation for the CI render step.

Computes a per-model SHA-256 key over a renderable's full transitive
include/use chain, any binary assets it references via surface()/import(),
the OpenSCAD version string, and a CACHE_VERSION constant. The CI render step
uses the key to skip re-rendering models whose inputs are unchanged.

Pure stdlib, no third-party deps. Parameter manifests (*.parameters.json) are
intentionally NOT part of the key: the precomputed STL is rendered with the
defaults baked into the .scad (no -D overrides), so manifests never change the
precomputed geometry and including them would cause needless cache misses.
"""

import argparse
import hashlib
import os
import re
import sys

CACHE_VERSION = "1"  # bump to force-invalidate every cached render

# Mirrors the include/use detection in scad-dep-graph.sh.
_INCLUDE_RE = re.compile(r'^\s*(?:include|use)\s+<([^>]*)>')
_ASSET_RE = re.compile(r'(?:surface|import)\s*\(\s*(?:file\s*=\s*)?"([^"]+)"')


def collect_inputs(scad_path):
    """BFS the include/use chain from scad_path.

    Returns (scad_files, asset_files, unresolved) where scad_files and
    asset_files are sets of resolved paths and unresolved is a set of raw
    target strings that could not be resolved on disk. Guards against include
    cycles via a visited set; never crashes on a missing include or asset.
    """
    scad_files = set()
    asset_files = set()
    unresolved = set()

    scad_files.add(scad_path)
    visited = set()
    queue = [scad_path]

    while queue:
        current = queue.pop()
        key = os.path.normpath(os.path.abspath(current))
        if key in visited:
            continue
        visited.add(key)

        try:
            with open(current, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue

        base = os.path.dirname(current)

        for line in text.splitlines():
            m = _INCLUDE_RE.match(line)
            if not m:
                continue
            target = m.group(1)
            resolved = os.path.normpath(os.path.join(base, target))
            if os.path.exists(resolved) and resolved.endswith(".scad"):
                if resolved not in scad_files:
                    scad_files.add(resolved)
                    queue.append(resolved)
            else:
                unresolved.add(target)

        for m in _ASSET_RE.finditer(text):
            target = m.group(1)
            resolved = os.path.normpath(os.path.join(base, target))
            if os.path.exists(resolved):
                asset_files.add(resolved)
            else:
                unresolved.add(target)

    return scad_files, asset_files, unresolved


def compute_key(scad_path, openscad_version):
    """Compute the hex SHA-256 cache key for a renderable .scad file."""
    scad_files, asset_files, unresolved = collect_inputs(scad_path)

    h = hashlib.sha256()
    h.update(b"CACHE_VERSION=" + CACHE_VERSION.encode("utf-8") + b"\n")
    h.update(b"OPENSCAD=" + openscad_version.encode("utf-8") + b"\n")

    paths = sorted(
        scad_files | asset_files,
        key=lambda p: os.path.relpath(p),
    )
    for path in paths:
        rel = os.path.relpath(path)
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        h.update(rel.encode("utf-8") + b"\0")
        h.update(digest.encode("utf-8") + b"\n")

    for token in sorted(unresolved):
        h.update(b"UNRESOLVED=" + token.encode("utf-8") + b"\n")

    return h.hexdigest()


def main(argv):
    parser = argparse.ArgumentParser(description="Render cache key computation.")
    sub = parser.add_subparsers(dest="command", required=True)

    key_parser = sub.add_parser("key", help="Print the cache key for a .scad file.")
    key_parser.add_argument("scad_path", help="Path to the renderable .scad file.")
    key_parser.add_argument(
        "--openscad-version",
        required=True,
        help="OpenSCAD version string to include in the key.",
    )

    args = parser.parse_args(argv)

    if args.command == "key":
        sys.stdout.write(compute_key(args.scad_path, args.openscad_version))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
