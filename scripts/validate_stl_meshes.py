#!/usr/bin/env python3
"""Validate rendered STL meshes with ADMesh and write a JSON audit report."""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import re
import subprocess
import sys


def extract_int(output: str, pattern: str) -> int:
    match = re.search(pattern + r"\s*:\s*(\d+)", output, re.MULTILINE)
    return int(match.group(1)) if match else 0


def extract_float(output: str, pattern: str, sep: str = ":") -> float:
    match = re.search(
        pattern + r"\s*" + re.escape(sep) + r"\s*([-+]?[\d.]+(?:[eE][-+]?\d+)?)",
        output,
        re.MULTILINE,
    )
    return float(match.group(1)) if match else 0.0


def estimated_minutes(volume: float, bb_z: float) -> int | None:
    if volume <= 0:
        return None
    if bb_z < 0.5:
        return max(1, round(volume / 200))

    layer_count = bb_z / 0.2
    xy_area = volume / bb_z
    perimeter = 4 * math.sqrt(xy_area)
    time_per_layer = perimeter / 50
    total_seconds = layer_count * time_per_layer * 5
    return max(1, round(total_seconds / 60))


def validate_stl(path: pathlib.Path, admesh_bin: str = "admesh") -> dict:
    proc = subprocess.run([admesh_bin, str(path)], capture_output=True, text=True)
    output = proc.stdout + proc.stderr

    triangles = extract_int(output, r"Number of facets")
    unconnected = extract_int(output, r"Number of unconnected facets")
    degenerate = extract_int(output, r"Degenerate facets")
    volume = extract_float(output, r"Volume")

    min_x = extract_float(output, r"Min X", "=")
    max_x = extract_float(output, r"Max X", "=")
    min_y = extract_float(output, r"Min Y", "=")
    max_y = extract_float(output, r"Max Y", "=")
    min_z = extract_float(output, r"Min Z", "=")
    max_z = extract_float(output, r"Max Z", "=")
    bb_x = max_x - min_x
    bb_y = max_y - min_y
    bb_z = max_z - min_z

    passed = unconnected == 0 and degenerate == 0 and volume > 0

    return {
        "name": path.stem,
        "triangles": triangles,
        "volume": round(volume, 2),
        "degenerate": degenerate,
        "unconnected": unconnected,
        "passed": passed,
        "estimated_minutes": estimated_minutes(volume, bb_z),
        "bbox_mm": {
            "x": round(bb_x, 2),
            "y": round(bb_y, 2),
            "z": round(bb_z, 2),
        },
        "bounds_mm": {
            "min_x": round(min_x, 2),
            "max_x": round(max_x, 2),
            "min_y": round(min_y, 2),
            "max_y": round(max_y, 2),
            "min_z": round(min_z, 2),
            "max_z": round(max_z, 2),
        },
        "sits_on_bed": abs(min_z) <= 0.01,
    }


def validate_site(
    site_dir: pathlib.Path,
    output_path: pathlib.Path,
    admesh_bin: str = "admesh",
) -> tuple[list[dict], bool]:
    results = []
    has_failure = False

    for stl in sorted(site_dir.glob("*.stl")):
        result = validate_stl(stl, admesh_bin=admesh_bin)
        if not result["passed"]:
            has_failure = True
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"  {status}: {result['name']} — {result['triangles']} triangles, "
            f"volume={result['volume']:.2f}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    return results, has_failure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", default="site", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--admesh", default="admesh")
    args = parser.parse_args(argv)

    output_path = args.output or args.site_dir / "validation.json"

    try:
        _, has_failure = validate_site(args.site_dir, output_path, args.admesh)
    except OSError as exc:
        print(f"error: could not write validation report: {exc}", file=sys.stderr)
        return 1

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"failed={str(has_failure).lower()}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
