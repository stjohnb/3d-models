#!/usr/bin/env python3
"""Heavy-render markers for the CI render step.

A project marks a renderable as heavy in its meta.json with
``render_memory_gb: {"<basename>": <GB>}`` (basename without ``.scad``). The
runner advertises its job memory cap as ``RUNNER_JOB_MEMORY_GB`` (fleet-infra
``runner.envs``). build.yml's "Render STL files" defers a marked cache miss
whose need exceeds that cap instead of attempting it, and the on-demand
render-heavy.yml workflow renders every marked source on the ``ram-<N>g``
runner its ``runs-on`` requests. A mark above that N could never be rendered,
so build.yml's "Validate project metadata" fails on one (``check-tier``). See
docs/ci-pipeline.md, "Heavy renders".

Pure stdlib. Run from the repository root.

    python3 scripts/render_memory.py map         # <dir>/<name>.scad<TAB><GB> lines
    python3 scripts/render_memory.py limit       # parsed RUNNER_JOB_MEMORY_GB, or ""
    python3 scripts/render_memory.py tier        # N from render-heavy.yml's ram-<N>g
    python3 scripts/render_memory.py check-tier  # exit 1 naming marks above N
"""

import glob
import json
import math
import os
import re
import sys

ENV_VAR = "RUNNER_JOB_MEMORY_GB"
RENDER_HEAVY_YML = ".forgejo/workflows/render-heavy.yml"
_RUNS_ON_RE = re.compile(r"^\s*runs-on:\s*(.*)$")
_RAM_TIER_RE = re.compile(r"(?<![\w-])ram-(\d+)g(?![\w-])")


def _meta_failures(root):
    path = os.path.join(root, ".meta-failures")
    if not os.path.isfile(path):
        return set()
    with open(path) as f:
        return {line.strip() for line in f if line.strip()}


def load_map(root="."):
    """Return {"<dir>/<name>.scad": gb} from every valid */meta.json.

    meta.json files listed in .meta-failures (written by build.yml's
    "Validate project metadata") are skipped, like every other meta reader.
    """
    failed = _meta_failures(root)
    result = {}
    for path in sorted(glob.glob(os.path.join(root, "*", "meta.json"))):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if rel in failed:
            continue
        try:
            with open(path) as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        marks = meta.get("render_memory_gb") if isinstance(meta, dict) else None
        if not isinstance(marks, dict):
            continue
        project = os.path.dirname(rel)
        for name, gb in sorted(marks.items()):
            if isinstance(gb, bool) or not isinstance(gb, (int, float)):
                continue
            result[f"{project}/{name}.scad"] = gb
    return result


def runner_limit_gb(environ=None):
    """The runner's advertised job memory cap in GB, or None when unknown."""
    if environ is None:
        environ = os.environ
    value = environ.get(ENV_VAR, "").strip()
    try:
        return int(value)
    except ValueError:
        return None


def should_defer(need_gb, limit_gb):
    """True only when both are known and the render needs more than the cap."""
    if need_gb is None or limit_gb is None:
        return False
    return need_gb > limit_gb


def heavy_tier_gb(root="."):
    """N from the ``ram-<N>g`` label in render-heavy.yml's runs-on, or None.

    None when the file is unreadable or its runs-on lines carry no ram tier,
    or more than one.
    """
    try:
        with open(os.path.join(root, RENDER_HEAVY_YML)) as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    tiers = []
    for line in lines:
        match = _RUNS_ON_RE.match(line)
        if match:
            tiers.extend(int(n) for n in _RAM_TIER_RE.findall(match.group(1)))
    return tiers[0] if len(tiers) == 1 else None


def check_tier(root="."):
    """Error messages for a missing tier label, or for each mark above it."""
    tier = heavy_tier_gb(root)
    if tier is None:
        return [f"{RENDER_HEAVY_YML} runs-on has no single ram-<N>g tier label"]
    return [
        f"{src} is marked render_memory_gb {gb}, above render-heavy's "
        f"ram-{tier}g tier, so no runner it waits for can render it"
        for src, gb in load_map(root).items()
        if gb > tier
    ]


def main(argv):
    if argv == ["map"]:
        # Whole GB, rounded up, so the shell can compare with `-gt`.
        for src, gb in load_map().items():
            sys.stdout.write(f"{src}\t{math.ceil(gb)}\n")
        return 0
    if argv == ["limit"]:
        limit = runner_limit_gb()
        sys.stdout.write("" if limit is None else str(limit))
        return 0
    if argv == ["tier"]:
        tier = heavy_tier_gb()
        if tier is None:
            sys.stderr.write(check_tier()[0] + "\n")
            return 1
        sys.stdout.write(str(tier))
        return 0
    if argv == ["check-tier"]:
        errors = check_tier()
        for error in errors:
            sys.stdout.write(f"FAIL: {error}\n")
        return 1 if errors else 0
    sys.stderr.write("usage: render_memory.py map|limit|tier|check-tier\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
