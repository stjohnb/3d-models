#!/usr/bin/env python3
"""Write the machine-readable summary for a PR-less issue preview.

build.yml runs this on a ``claws/preview-issue-<id>`` push, after site/ is
fully built, and deploys the result as ``preview-summary.json`` under
``issue-preview/<id>/<sha8>/``. It carries what the "🔍 Model Preview" PR
comment shows (thumbnails, size and triangle counts, mesh validation,
interference, viewer link) plus a ready-to-post ``markdown`` body, so the
issue planner can post or update it on the issue instead of reading a PR
comment. Stdlib only; see docs/ci-pipeline.md, "Issue previews (PR-less)".

Usage:
  python3 scripts/preview_summary.py --issue ID --sha SHA8 --commit SHA \\
      (--changed-from-git | --changed PATH ...) --site site \\
      --out site/preview-summary.json [--markdown-out FILE]
"""

import argparse
import json
import os
import pathlib
import struct
import subprocess
import sys
import urllib.parse

BASE_URL = "https://www.bstjohn.net/3d-models/issue-preview"
EXTRA_VIEWS = ("top", "bottom", "front")


def viewer_url(issue, sha):
    return f"{BASE_URL}/{issue}/{sha}/"


def stl_metadata(path):
    """Return (size_bytes, triangles) for an STL, or None if unreadable.

    Triangle count comes from the binary header (bytes 80-83, little-endian
    uint32) and is only trusted when the file size matches 84 + 50*n;
    otherwise (ASCII STL, truncation) it is None, like the PR comment.
    """
    try:
        size = os.path.getsize(path)
        if size < 84:
            return size, None
        with open(path, "rb") as f:
            header = f.read(84)
    except OSError:
        return None
    (triangles,) = struct.unpack_from("<I", header, 80)
    if size != 84 + triangles * 50:
        return size, None
    return size, triangles


def format_size(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} bytes"
    if num_bytes < 1048576:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / 1048576:.1f} MB"


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def changed_from_git():
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [line for line in out.splitlines() if line.endswith(".scad")]


def build_summary(issue, sha, commit, changed, site):
    site = pathlib.Path(site)
    base = viewer_url(issue, sha)

    # Canonical project names come from models.json (entry["dir"] -> key),
    # exactly as the PR comment reads them; fall back to the raw directory.
    dir_to_project = {}
    models_json = _load_json(site / "models.json", {})
    if isinstance(models_json, dict):
        for project, entry in models_json.items():
            if isinstance(entry, dict) and entry.get("dir"):
                dir_to_project[entry["dir"]] = project

    changed_scad = sorted({p for p in changed if p.endswith(".scad")})
    models = []
    for scad in changed_scad:
        stem = pathlib.PurePosixPath(scad).stem
        png = f"{stem}.png"
        if not (site / png).is_file():
            continue
        directory = scad.split("/")[0]
        meta = stl_metadata(site / f"{stem}.stl")
        models.append({
            "name": stem.replace("-", " ").replace("_", " "),
            "project": dir_to_project.get(directory, directory),
            "scad": scad,
            "thumbnail_url": base + urllib.parse.quote(png),
            "stl_size_bytes": meta[0] if meta else None,
            "triangles": meta[1] if meta else None,
            "extra_views": {
                view: base + urllib.parse.quote(f"{stem}_{view}.png")
                for view in EXTRA_VIEWS
                if (site / f"{stem}_{view}.png").is_file()
            },
        })
    models.sort(key=lambda m: (m["project"], m["thumbnail_url"]))

    validation = _load_json(site / "validation.json", [])
    interference = _load_json(site / "interference.json", [])
    if not isinstance(validation, list):
        validation = []
    if not isinstance(interference, list):
        interference = []

    summary = {
        "issue": issue,
        "sha": sha,
        "commit": commit,
        "viewer_url": base,
        "summary_url": base + "preview-summary.json",
        "changed_scad": changed_scad,
        "models": models,
        "validation": validation,
        "interference": interference,
    }
    summary["markdown"] = render_markdown(summary)
    return summary


def _num(value):
    return f"{value:,}" if isinstance(value, (int, float)) else str(value)


def render_markdown(summary):
    base = summary["viewer_url"]
    out = ["## 🔍 Model Preview\n\n", f"**[View interactive 3D models]({base})**\n\n"]

    projects = {}
    for model in summary["models"]:
        projects.setdefault(model["project"], []).append(model)
    for project in sorted(projects):
        out.append(f"### {project}\n\n")
        for m in projects[project]:
            stats = ""
            if m["stl_size_bytes"] is not None:
                stats = format_size(m["stl_size_bytes"])
                if m["triangles"] is not None:
                    stats += f" · {m['triangles']:,} triangles"
                stats = f" — {stats}"
            out.append(f"**{m['name']}**{stats}\n")
            out.append(f"![{m['name']}]({m['thumbnail_url']})\n\n")

    validation = summary["validation"]
    if validation:
        any_failed = any(not r.get("passed") for r in validation)
        out.append(f"### {'⚠️' if any_failed else '✅'} Mesh Validation\n\n")
        out.append("| Model | Size X/Y/Z mm | Min Z | Triangles | Volume | Status |\n")
        out.append("|-------|---------------|-------|-----------|--------|--------|\n")
        for r in validation:
            status = "✅ Pass" if r.get("passed") else "❌ Fail"
            bbox = r.get("bbox_mm") or {}
            if all(isinstance(bbox.get(k), (int, float)) for k in "xyz"):
                size = f"{bbox['x']} × {bbox['y']} × {bbox['z']}"
            else:
                size = "unknown"
            min_z = (r.get("bounds_mm") or {}).get("min_z")
            min_z = f"{min_z:.2f}" if isinstance(min_z, (int, float)) else "unknown"
            if r.get("sits_on_bed") is False:
                min_z += " ⚠️"
            out.append(
                f"| {r.get('name')} | {size} | {min_z} | {_num(r.get('triangles'))} "
                f"| {r.get('volume')} | {status} |\n"
            )
        out.append("\n")
        if any_failed:
            out.append(
                "> **Mesh issues detected.** Models with ❌ have non-manifold "
                "geometry, degenerate triangles, or non-positive volume. These "
                "will slice incorrectly and produce failed prints.\n\n"
            )

    interference = summary["interference"]
    if interference:
        any_failed = any(not r.get("passed") for r in interference)
        all_skipped = all(r.get("skipped") for r in interference)
        icon = "⚠️" if any_failed else "⏭️" if all_skipped else "✅"
        out.append(f"### {icon} Mating Part Interference\n\n")
        out.append("| Part A | Part B | Overlap | Status |\n")
        out.append("|--------|--------|---------|--------|\n")
        for r in interference:
            if r.get("skipped"):
                status = "⏭️ Skip"
            elif r.get("passed"):
                status = "✅ Pass"
            else:
                status = "❌ Fail"
            vol = r.get("overlap_volume_mm3")
            vol = f"{vol:.1f} mm³" if isinstance(vol, (int, float)) else (r.get("error") or "N/A")
            out.append(f"| {r.get('part_a')} | {r.get('part_b')} | {vol} | {status} |\n")
        out.append("\n")
        if any_failed:
            out.append(
                "> **Interference detected.** Mating parts with ❌ physically "
                "overlap and won't assemble correctly.\n\n"
            )

    out.append(f"---\n*Preview deployed to [{base}]({base})*\n")
    return "".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--issue", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--site", default="site")
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown-out", default="")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--changed-from-git", action="store_true")
    source.add_argument("--changed", action="append")
    args = parser.parse_args(argv)

    changed = changed_from_git() if args.changed_from_git else args.changed
    summary = build_summary(args.issue, args.sha, args.commit, changed, args.site)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    # GITHUB_STEP_SUMMARY is unset outside Actions; an empty path skips it.
    if args.markdown_out:
        with open(args.markdown_out, "a", encoding="utf-8") as f:
            f.write(summary["markdown"])
    print(f"Wrote {args.out}: {len(summary['models'])} model(s), viewer {summary['viewer_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
