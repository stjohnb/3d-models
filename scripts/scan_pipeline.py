#!/usr/bin/env python3
"""Turn a scanning-rig capture video into a 3D mesh (operator tool, not used by CI).

Usage:
    python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV --only masks
    python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV --platter 540,1420,470,150 -o /tmp/widget.stl

Operator tool — not used by CI. Run it inside `nix develop .#scan`, which
provides ffmpeg, colmap, openmvs and the Python dependencies.
"""

import argparse
import json
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_colmap import (
    count_registered_images,
    densify_argv,
    derived_scene_path,
    exhaustive_matcher_argv,
    feature_extractor_argv,
    image_undistorter_argv,
    interface_colmap_argv,
    mapper_argv,
    pick_sparse_model,
    reconstruct_mesh_argv,
    run,
)
from scan_frames import extract_all_frames, probe_video, score_sharpness, select_sharp_frames
from scan_masks import (
    column_mask,
    frame_mask,
    mask_filename,
    parse_ellipse,
    suggest_ellipse,
    write_masked_pair,
)

STAGES = ["frames", "masks", "sfm", "dense", "mesh", "clean"]

# A mask covering more than this fraction of the frame means the ellipse is
# almost certainly not on the platter — bail rather than burn hours on SfM.
MAX_MASK_COVERAGE = 0.70

# Above this fraction of selected frames with nothing segmented above the
# platter, salient masking is not working on this capture.
MAX_EMPTY_FRACTION = 0.30

# Below this fraction of selected frames registered by the mapper, the sparse
# model is not trustworthy — almost always a mis-placed platter ellipse.
MIN_REGISTERED_FRACTION = 0.60


def stages_to_run(from_stage, to_stage, only):
    """Resolve --from/--to/--only into the ordered list of stages. Pure stdlib."""
    if only:
        return [only]
    start = STAGES.index(from_stage) if from_stage else 0
    end = STAGES.index(to_stage) if to_stage else len(STAGES) - 1
    if start > end:
        raise ValueError("--from stage comes after --to stage")
    return STAGES[start:end + 1]


def stage_stamp(work_dir, stage):
    """Path of the completion stamp for a stage."""
    return pathlib.Path(work_dir) / f".stamp-{stage}.json"


def _ellipse_arg(text):
    try:
        return parse_ellipse(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Reconstruct a 3D mesh from a scanning-rig capture video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("video", type=pathlib.Path, help="Capture video (e.g. IMG_3814.MOV)")
    parser.add_argument(
        "-o", "--output",
        type=pathlib.Path,
        default=None,
        help="Output STL path (default: <work-dir>/output/<video-stem>.stl)",
    )
    parser.add_argument(
        "--work-dir",
        type=pathlib.Path,
        default=None,
        help="Scratch directory (default: .cache/scan/<video-stem>; disposable)",
    )
    parser.add_argument(
        "--frames", type=int, default=150,
        help="Number of sharp frames to select from the capture (default: 150)",
    )
    parser.add_argument(
        "--platter", type=_ellipse_arg, default=None,
        help="Platter ellipse cx,cy,rx,ry in pixels. Omit to get a suggestion.",
    )
    parser.add_argument(
        "--object-height", type=float, default=400,
        help="Pixels above the platter centre to include in the mask (default: 400)",
    )
    parser.add_argument(
        "--mask-mode", choices=["salient", "roi"], default="salient",
        help="salient: rembg segmentation inside the column. roi: whole column.",
    )
    parser.add_argument(
        "--mm-per-unit", type=float, default=None,
        help="Millimetres per reconstruction unit; skips the platter fit "
             "entirely, so the mesh keeps the reconstruction's own axes and "
             "the crop bounds are measured in that frame",
    )
    parser.add_argument(
        "--platter-diameter", type=float, default=150.0,
        help="Platter diameter in mm, the scale reference (default: 150.0)",
    )
    parser.add_argument(
        "--z-min", type=float, default=1.0,
        help="Crop faces below this height above the platter, in mm (default: 1.0)",
    )
    parser.add_argument(
        "--z-max", type=float, default=200.0,
        help="Crop faces above this height above the platter, in mm (default: 200.0)",
    )
    parser.add_argument(
        "--r-max", type=float, default=72.0,
        help="Crop faces beyond this radius from the platter centre, in mm "
             "(default: 72.0 — the 75 mm platter radius less 3 mm of rim)",
    )
    parser.add_argument(
        "--keep-components", type=int, default=1,
        help="Number of largest connected components to keep (default: 1)",
    )
    parser.add_argument(
        "--max-image-size", type=int, default=1600,
        help="Longest undistorted image edge fed to densification (default: 1600)",
    )
    parser.add_argument(
        "--threads", type=int, default=os.cpu_count(),
        help="CPU threads for feature extraction and matching (default: all cores)",
    )
    parser.add_argument(
        "--from", dest="from_stage", choices=STAGES, default=None,
        help="First stage to run",
    )
    parser.add_argument(
        "--to", dest="to_stage", choices=STAGES, default=None,
        help="Last stage to run",
    )
    parser.add_argument(
        "--only", choices=STAGES, default=None, help="Run exactly one stage",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-run stages even if their stamp exists",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args(argv)
    if args.only and (args.from_stage or args.to_stage):
        parser.error("--only cannot be combined with --from/--to")

    stem = args.video.stem
    if args.work_dir is None:
        args.work_dir = pathlib.Path(".cache") / "scan" / stem
    if args.output is None:
        args.output = args.work_dir / "output" / f"{stem}.stl"
    return args


def _log(args, message):
    if not args.quiet:
        print(message)


def _raw_dir(work_dir):
    return work_dir / "raw"


def _selection_path(work_dir):
    return work_dir / "selected.json"


def run_frames(args):
    """Extract every frame, then keep the sharpest one per contiguous bin."""
    raw_dir = _raw_dir(args.work_dir)
    if raw_dir.exists():
        shutil.rmtree(raw_dir)

    stream = probe_video(args.video)
    _log(args, f"video: {stream.get('width')}x{stream.get('height')} "
               f"@ {stream.get('avg_frame_rate')}")

    paths = extract_all_frames(args.video, raw_dir, quiet=args.quiet)
    if not paths:
        sys.exit(f"error: ffmpeg extracted no frames from {args.video}")
    _log(args, f"extracted {len(paths)} frames to {raw_dir}")

    scores = score_sharpness(paths)
    selected = select_sharp_frames(scores, args.frames)
    names = [paths[i].name for i in selected]
    _selection_path(args.work_dir).write_text(json.dumps(names, indent=2) + "\n")
    _log(args, f"selected {len(names)} sharp frames -> {_selection_path(args.work_dir)}")
    return len(names)


def _selected_paths(args):
    selection = _selection_path(args.work_dir)
    if not selection.exists():
        sys.exit(f"error: {selection} missing — run the frames stage first")
    raw_dir = _raw_dir(args.work_dir)
    return [raw_dir / name for name in json.loads(selection.read_text())]


def _write_roi_preview(args, frame_path, ellipse):
    """Draw the platter ellipse and the swept column onto the first frame."""
    import cv2

    cx, cy, rx, ry = ellipse
    frame = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
    if frame is None:
        sys.exit(f"error: could not read {frame_path}")

    preview = frame.copy()
    column = column_mask(frame.shape, ellipse, args.object_height)
    contours, _ = cv2.findContours(column, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.polylines(preview, contours, True, (0, 255, 0), 2)
    cv2.ellipse(
        preview,
        (int(round(cx)), int(round(cy))),
        (int(round(rx)), int(round(ry))),
        0, 0, 360, (0, 255, 0), 2,
    )

    path = args.work_dir / "roi-preview.jpg"
    if not cv2.imwrite(str(path), preview):
        sys.exit(f"error: could not write {path}")
    print(f"wrote {path} — open it and confirm the ellipse sits on the platter rim")


def run_masks(args):
    """Mask every selected frame down to the platter and the object above it."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "cv2 (opencv-python) not importable — run inside `nix develop .#scan`"
        ) from exc

    paths = _selected_paths(args)
    for path in paths:
        if not path.exists():
            sys.exit(f"error: {path} missing — re-run the frames stage with --force")

    ellipse = args.platter
    if ellipse is None:
        if args.mask_mode == "roi":
            # roi mode's whole point is to avoid rembg/ONNX; suggest_ellipse()
            # would call straight into salient_mask() and defeat that.
            sys.exit(
                f"error: --mask-mode roi needs --platter (no ML suggestion "
                f"in this mode) — open {paths[0]}, measure the platter rim "
                f"by eye, and pass --platter cx,cy,rx,ry"
            )
        suggested = suggest_ellipse(paths[0])
        spec = ",".join(f"{v:.0f}" for v in suggested)
        print(f"no --platter given; suggestion: --platter {spec}")
        _write_roi_preview(args, paths[0], suggested)
        sys.exit(1)

    _write_roi_preview(args, paths[0], ellipse)

    # Clear stale output: re-running with a corrected ellipse is the normal
    # path, and leftovers from the previous ellipse would feed straight into SfM.
    image_dir = args.work_dir / "frames"
    mask_dir = args.work_dir / "masks"
    for directory in (image_dir, mask_dir):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    empty = []

    def note_empty(path):
        empty.append(path)
        print(f"warning: {path.name}: no salient object above the platter")

    for path in paths:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            sys.exit(f"error: could not read {path}")
        mask = frame_mask(
            path, frame.shape, ellipse, args.object_height, args.mask_mode,
            on_empty=note_empty,
        )
        coverage = float((mask > 0).mean())
        if coverage > MAX_MASK_COVERAGE:
            sys.exit(
                f"platter ellipse looks wrong (mask covers {coverage * 100:.0f}% "
                f"of frame) — re-check --platter against roi-preview.jpg"
            )
        write_masked_pair(
            frame, mask,
            image_dir / path.name,
            mask_dir / mask_filename(path.name),
        )

    if len(empty) > MAX_EMPTY_FRACTION * len(paths):
        sys.exit(
            f"too few frames with a segmented object "
            f"({len(paths) - len(empty)}/{len(paths)}) — try --mask-mode roi"
        )

    _log(args, f"wrote {len(paths)} masked frames to {image_dir} and masks to {mask_dir}")
    return len(paths)


def _image_dir(work_dir):
    return work_dir / "frames"


def _mvs_scene(work_dir):
    return work_dir / "mvs" / "scene.mvs"


def _require(path, hint):
    if not pathlib.Path(path).exists():
        sys.exit(f"error: {path} missing — {hint}")
    return path


def run_sfm(args):
    """COLMAP feature extraction, exhaustive matching and sparse mapping."""
    image_dir = _require(
        _image_dir(args.work_dir), "run the masks stage first"
    )
    mask_dir = _require(args.work_dir / "masks", "run the masks stage first")
    images = sorted(image_dir.glob("*.jpg"))
    if not images:
        sys.exit(f"error: no masked frames in {image_dir} — re-run the masks stage")

    database = args.work_dir / "database.db"
    sparse_dir = args.work_dir / "sparse"
    # COLMAP appends to an existing database and writes new models beside the
    # old ones, so both are cleared: a stale database would carry features
    # extracted under a previous platter ellipse straight into the mapper.
    database.unlink(missing_ok=True)
    if sparse_dir.exists():
        shutil.rmtree(sparse_dir)
    sparse_dir.mkdir(parents=True)

    run("colmap", feature_extractor_argv(database, image_dir, mask_dir, args.threads),
        quiet=args.quiet)
    run("colmap", exhaustive_matcher_argv(database, args.threads), quiet=args.quiet)
    run("colmap", mapper_argv(database, image_dir, sparse_dir), quiet=args.quiet)

    model = pick_sparse_model(sparse_dir)
    registered = count_registered_images(model)
    if registered < MIN_REGISTERED_FRACTION * len(images):
        print(
            f"warning: only {registered}/{len(images)} frames registered — open "
            f"{args.work_dir / 'roi-preview.jpg'}; a platter ellipse that misses "
            f"the rim texture is the usual cause"
        )
    _log(args, f"registered {registered}/{len(images)} frames in {model}")
    return registered


def run_dense(args):
    """COLMAP undistortion, then OpenMVS densification."""
    image_dir = _require(_image_dir(args.work_dir), "run the masks stage first")
    model = pick_sparse_model(
        _require(args.work_dir / "sparse", "run the sfm stage first")
    )

    dense_dir = args.work_dir / "dense"
    if dense_dir.exists():
        shutil.rmtree(dense_dir)
    run(
        "colmap",
        image_undistorter_argv(image_dir, model, dense_dir, args.max_image_size),
        quiet=args.quiet,
    )

    scene = _mvs_scene(args.work_dir)
    scene.parent.mkdir(parents=True, exist_ok=True)
    run("InterfaceCOLMAP", interface_colmap_argv(dense_dir, scene), quiet=args.quiet)
    _require(scene, "InterfaceCOLMAP wrote no scene")

    run("DensifyPointCloud", densify_argv(scene), quiet=args.quiet)
    dense_cloud = _require(
        derived_scene_path(scene, "dense", ".ply"),
        "DensifyPointCloud wrote no dense cloud",
    )
    _log(args, f"dense cloud: {dense_cloud}")
    return 1


def run_mesh(args):
    """OpenMVS mesh reconstruction from the dense cloud."""
    scene = _mvs_scene(args.work_dir)
    dense_scene = _require(
        derived_scene_path(scene, "dense", ".mvs"), "run the dense stage first"
    )
    run("ReconstructMesh", reconstruct_mesh_argv(dense_scene), quiet=args.quiet)
    mesh_ply = _require(
        derived_scene_path(dense_scene, "mesh", ".ply"),
        "ReconstructMesh wrote no mesh",
    )
    _log(args, f"mesh: {mesh_ply}")
    return 1


def _platter_frame(args, points_ply):
    """Platter-derived transform and scale, or the operator's override.

    `points_ply` is the reconstructed mesh, not the dense cloud — see run_clean.
    """
    import numpy

    from scan_mesh import load_points, platter_frame

    if args.mm_per_unit is not None:
        # Explicit scale skips the platter fit entirely, so there is no plane
        # to orient against: the mesh keeps the reconstruction's own axes.
        _log(args, f"using --mm-per-unit {args.mm_per_unit} (no platter fit)")
        return {
            "origin": numpy.zeros(3),
            "rotation": numpy.eye(3),
            "radius_units": None,
            "mm_per_unit": float(args.mm_per_unit),
            "plane_inliers": None,
        }

    points = load_points(points_ply)
    frame = platter_frame(points, platter_diameter=args.platter_diameter)
    _log(
        args,
        f"platter: radius {frame['radius_units']:.4f} units, "
        f"{frame['mm_per_unit']:.4f} mm/unit",
    )
    return frame


def run_clean(args):
    """Scale to millimetres off the platter, crop to the object, export STL."""
    import trimesh

    from scan_mesh import crop_to_object, export_stl, keep_largest_components, scale_transform

    scene = _mvs_scene(args.work_dir)
    dense_scene = derived_scene_path(scene, "dense", ".mvs")
    # The dense cloud is checked but never loaded: DensifyPointCloud writes
    # scene_dense.ply with per-vertex list properties (view_indices,
    # view_weights) that trimesh's PLY reader cannot parse — it raises
    # "PLY is unexpected length!" (issue #421). Its presence still proves the
    # dense stage ran; the platter plane is fitted on the mesh instead.
    _require(derived_scene_path(scene, "dense", ".ply"), "run the dense stage first")
    mesh_ply = _require(
        derived_scene_path(dense_scene, "mesh", ".ply"), "run the mesh stage first"
    )

    mesh = trimesh.load(str(mesh_ply), process=False)
    frame = _platter_frame(args, mesh_ply)
    mesh.apply_transform(scale_transform(frame))

    faces_before = int(len(mesh.faces))
    mesh = crop_to_object(mesh, z_min=args.z_min, z_max=args.z_max, r_max=args.r_max)
    faces_after = int(len(mesh.faces))
    mesh = keep_largest_components(mesh, count=args.keep_components)
    export_stl(mesh, args.output)
    _log(args, f"wrote {args.output} ({len(mesh.faces)} faces)")

    inliers = frame["plane_inliers"]
    sparse_dir = args.work_dir / "sparse"
    report = {
        "video": str(args.video),
        "frames_selected": len(json.loads(_selection_path(args.work_dir).read_text()))
        if _selection_path(args.work_dir).exists() else None,
        "mask_mode": args.mask_mode,
        "platter_ellipse": list(args.platter) if args.platter else None,
        "sparse_images_registered": count_registered_images(pick_sparse_model(sparse_dir))
        if sparse_dir.is_dir() else None,
        "mm_per_unit": frame["mm_per_unit"],
        "platter_radius_units": frame["radius_units"],
        "plane_inlier_count": int(inliers.sum()) if inliers is not None else None,
        "faces_before_crop": faces_before,
        "faces_after_crop": faces_after,
        "components_kept": args.keep_components,
        "bbox_mm": [[float(v) for v in row] for row in mesh.bounds],
    }
    report_path = args.work_dir / "scan-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    _log(args, f"wrote {report_path}")
    return 1


STAGE_RUNNERS = {
    "frames": run_frames,
    "masks": run_masks,
    "sfm": run_sfm,
    "dense": run_dense,
    "mesh": run_mesh,
    "clean": run_clean,
}

# External binaries each stage shells out to, so a missing tool fails before
# any work happens rather than an hour in.
STAGE_TOOLS = {
    "frames": ["ffprobe", "ffmpeg"],
    "sfm": ["colmap"],
    "dense": ["colmap", "InterfaceCOLMAP", "DensifyPointCloud"],
    "mesh": ["ReconstructMesh"],
}


def main(argv=None):
    args = parse_args(argv)
    if not args.video.exists():
        sys.exit(f"error: {args.video} not found")

    try:
        stages = stages_to_run(args.from_stage, args.to_stage, args.only)
    except ValueError as exc:
        sys.exit(f"error: {exc}")

    for stage in stages:
        for binary in STAGE_TOOLS.get(stage, []):
            if shutil.which(binary) is None:
                sys.exit(f"error: {binary} not found — run inside `nix develop .#scan`")

    args.work_dir.mkdir(parents=True, exist_ok=True)

    for stage in stages:
        stamp = stage_stamp(args.work_dir, stage)
        if stamp.exists() and not args.force:
            _log(args, f"skipping {stage} (stamp exists; --force to re-run)")
            continue
        # Delete first: an interrupted run must never look complete.
        stamp.unlink(missing_ok=True)
        _log(args, f"== {stage}")
        try:
            outputs = STAGE_RUNNERS[stage](args)
        except (RuntimeError, ValueError) as exc:
            # Operator tool: a failed subprocess, an unreachable rembg model or
            # a crop that kept nothing should read as one line, not a traceback.
            sys.exit(f"error: {exc}")
        stamp.write_text(json.dumps({"stage": stage, "outputs": int(outputs)}) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
