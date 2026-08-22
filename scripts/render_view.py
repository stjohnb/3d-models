#!/usr/bin/env python3
"""Render an arbitrary OpenSCAD view to PNG (developer/agent tool, not used by CI).

Usage:
    python3 scripts/render_view.py power-workshop/drill_socket.scad --view top
    python3 scripts/render_view.py power-workshop/drill_socket.scad --camera=0,0,0,75,0,25,500 --projection=perspective -o ~/renders/custom.png

With no -o, the PNG is written to a fresh private temp directory and the path is printed.
"""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# Gimbal camera presets: tx,ty,tz,rx,ry,rz,dist
# rx=0,ry=0,rz=0 looks straight down the +Y axis at the XZ plane from above
# in OpenSCAD's default orientation. With --viewall the dist is cosmetic.
#
# Verified against drill_socket.scad: top shows the cavity opening, bottom
# shows the stand-off ring cavity, iso matches CI isometric thumbnail.
PRESETS = {
    "iso":    {"camera": "0,0,0,55,0,25,500",  "projection": "perspective"},
    "top":    {"camera": "0,0,0,0,0,0,500",    "projection": "ortho"},
    "bottom": {"camera": "0,0,0,180,0,0,500",  "projection": "ortho"},
    "front":  {"camera": "0,0,0,90,0,0,500",   "projection": "ortho"},
    "back":   {"camera": "0,0,0,90,0,180,500", "projection": "ortho"},
    "left":   {"camera": "0,0,0,90,0,90,500",  "projection": "ortho"},
    "right":  {"camera": "0,0,0,90,0,270,500", "projection": "ortho"},
}

# Y-up variants of the preset table. No source in this repo needs them — every
# .scad here is OpenSCAD Z-up (issue #382) — but --y-up keeps the presets usable
# for ad-hoc rendering of an externally-sourced Y-up model.
PRESETS_Y_UP = {
    "iso":    {"camera": "0,0,0,55,0,25,500",  "projection": "perspective"},
    "top":    {"camera": "0,0,0,90,0,0,500",   "projection": "ortho"},
    "bottom": {"camera": "0,0,0,270,0,0,500",  "projection": "ortho"},
    "front":  {"camera": "0,0,0,0,0,0,500",    "projection": "ortho"},
    "back":   {"camera": "0,0,0,0,0,180,500",  "projection": "ortho"},
    "left":   {"camera": "0,0,0,0,0,90,500",   "projection": "ortho"},
    "right":  {"camera": "0,0,0,0,0,270,500",  "projection": "ortho"},
}

VIEW_CHOICES = list(PRESETS.keys()) + ["custom"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Render an arbitrary OpenSCAD view to PNG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("scad_file", type=pathlib.Path, help=".scad file to render")
    parser.add_argument(
        "-o", "--output",
        type=pathlib.Path,
        default=None,
        help="Output PNG path (default: a new private temp directory, "
             "created per invocation; the chosen path is printed).",
    )
    parser.add_argument(
        "--view",
        choices=VIEW_CHOICES,
        default=None,
        help="Named view preset. Use 'custom' when passing --camera explicitly.",
    )
    parser.add_argument(
        "--camera",
        default=None,
        help=(
            "Raw gimbal camera string tx,ty,tz,rx,ry,rz,dist. "
            "Implies --view custom. Cannot be combined with a non-custom --view."
        ),
    )
    parser.add_argument(
        "--projection",
        choices=["ortho", "perspective"],
        default=None,
        help="Override projection (default depends on view preset).",
    )
    parser.add_argument(
        "--imgsize",
        default="800x600",
        help="Image size as WxH (default: 800x600)",
    )
    parser.add_argument(
        "--viewall",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pass --viewall to openscad (default: on). Use --no-viewall to disable.",
    )
    parser.add_argument(
        "--autocenter",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pass --autocenter to openscad (default: on). Use --no-autocenter to disable.",
    )
    parser.add_argument(
        "--color-scheme",
        default=None,
        dest="color_scheme",
        help="Optional colorscheme passthrough to openscad.",
    )
    parser.add_argument(
        "-D",
        action="append",
        default=[],
        dest="defines",
        metavar="VAR=VALUE",
        help="Override an OpenSCAD variable (repeatable).",
    )
    parser.add_argument(
        "--y-up",
        action="store_true",
        default=False,
        help="Use the Y-up preset table (for externally-sourced Y-up models; "
             "no file in this repo needs it).",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="Suppress the success line; openscad output still shown on failure.",
    )
    args = parser.parse_args(argv)

    # --camera implies --view custom; reject any explicit named view combined with --camera
    if args.camera is not None:
        if args.view is not None and args.view != "custom":
            parser.error("--camera cannot be combined with a non-custom --view")
        args.view = "custom"
    if args.view is None:
        args.view = "iso"

    # --view custom requires --camera
    if args.view == "custom" and args.camera is None:
        parser.error("--view custom requires --camera")

    return args


def build_openscad_argv(args):
    """Return the full argv list for openscad (without the executable itself)."""
    # Resolve camera and projection
    if args.view == "custom":
        camera = args.camera
        projection = args.projection or "perspective"
    else:
        table = PRESETS_Y_UP if args.y_up else PRESETS
        preset = table[args.view]
        camera = preset["camera"]
        projection = args.projection or preset["projection"]

    # Parse imgsize WxH -> W,H
    w, _, h = args.imgsize.partition("x")
    if not w or not h:
        w, _, h = args.imgsize.partition("X")
    imgsize_arg = f"{w},{h}"

    argv = [
        f"--imgsize={imgsize_arg}",
        f"--camera={camera}",
        f"--projection={projection}",
    ]

    if args.viewall:
        argv.append("--viewall")
    if args.autocenter:
        argv.append("--autocenter")
    if args.color_scheme:
        argv.append(f"--colorscheme={args.color_scheme}")

    for define in args.defines:
        argv.extend(["-D", define])

    argv.extend(["-o", str(args.output)])
    argv.append(str(args.scad_file))

    return argv


def resolve_output_path(output, scad_file):
    """Resolve the PNG output path, creating a private temp dir when needed.

    An explicit --output is returned unchanged, with no temp dir. With no
    --output, a fresh 0700 directory is created via tempfile.mkdtemp() and
    the render goes to <dir>/<sanitized scad stem>.png. The old default was
    the fixed, world-writable path /tmp/render.png, which any other local
    account on a shared build host could pre-plant as a symlink so that
    openscad -o truncated the symlink's target (issue #429).

    Returns (path, temp_dir) where temp_dir is the created directory as a
    pathlib.Path, or None when --output was explicit.
    """
    if output is not None:
        return output, None
    stem = re.sub(r"[^A-Za-z0-9._ -]", "_", scad_file.stem)
    if not stem.strip("."):
        stem = "render"
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="render_view-"))
    return temp_dir / f"{stem}.png", temp_dir


def main():
    args = parse_args()

    if not args.scad_file.exists():
        print(f"error: {args.scad_file} not found", file=sys.stderr)
        sys.exit(1)

    openscad = shutil.which("openscad")
    if openscad is None:
        print(
            "error: openscad not found on PATH; install it from https://openscad.org/downloads.html",
            file=sys.stderr,
        )
        sys.exit(1)

    output, temp_dir = resolve_output_path(args.output, args.scad_file)
    args.output = output
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [openscad] + build_openscad_argv(args)

    # Wrap with xvfb-run on headless hosts (no DISPLAY set)
    if shutil.which("xvfb-run") and not os.environ.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd

    result = subprocess.run(cmd, check=False, capture_output=False)

    if result.returncode != 0:
        if temp_dir is not None and not output.exists():
            try:
                temp_dir.rmdir()
            except OSError:
                pass
        sys.exit(result.returncode)

    if not args.quiet:
        print(f"Rendered {args.scad_file} [{args.view}] -> {output}")
    elif temp_dir is not None:
        print(output)


if __name__ == "__main__":
    main()
