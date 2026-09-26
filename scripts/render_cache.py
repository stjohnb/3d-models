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

# Bump to force-invalidate every cached render. "2": discard STLs rendered
# by openscad-unstable's Manifold backend before build.yml pinned STL export
# to --backend=CGAL (Manifold emitted degenerate facets; the render flags are
# not part of the key, so a bump is the only way to evict those entries).
CACHE_VERSION = "2"

# Mirrors the include/use detection in scad-dep-graph.sh.
_INCLUDE_RE = re.compile(r'^\s*(?:include|use)\s+<([^>]*)>')
_ASSET_RE = re.compile(r'(?:surface|import)\s*\(\s*(?:file\s*=\s*)?"([^"]+)"')


def containment_root():
    """Directory that resolved include/asset paths must stay inside.

    The module is already cwd-rooted (compute_key hashes os.path.relpath(path)
    with no start), and both callers — build.yml's render step and
    external_assets.py — run from the repository root.
    """
    return os.path.realpath(os.getcwd())


def is_contained(path, root=None):
    """True if path is a regular file inside root and not under a .git dir.

    Containment is checked on os.path.realpath, so neither `..` segments nor a
    symlink can escape. Any path component named `.git` is rejected outright:
    the checkout step writes the job token into .git/config, and source zips
    built from these paths are deployed publicly, so .git must never be
    bundled or hashed.
    """
    if root is None:
        root = containment_root()
    real = os.path.realpath(path)
    if real != root and not real.startswith(root + os.sep):
        return False
    if ".git" in os.path.relpath(real, root).split(os.sep):
        return False
    return os.path.isfile(real)


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
    root = containment_root()

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
            if resolved.endswith(".scad") and is_contained(resolved, root):
                if resolved not in scad_files:
                    scad_files.add(resolved)
                    queue.append(resolved)
            else:
                if os.path.exists(resolved) and not is_contained(resolved, root):
                    sys.stderr.write(
                        "::warning::%s: refusing out-of-tree include target %r\n"
                        % (current, target)
                    )
                unresolved.add(target)

        for m in _ASSET_RE.finditer(text):
            target = m.group(1)
            resolved = os.path.normpath(os.path.join(base, target))
            if is_contained(resolved, root):
                asset_files.add(resolved)
            else:
                if os.path.exists(resolved):
                    sys.stderr.write(
                        "::warning::%s: refusing out-of-tree asset target %r\n"
                        % (current, target)
                    )
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
