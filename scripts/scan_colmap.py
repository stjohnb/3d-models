"""COLMAP and OpenMVS command lines for the photogrammetry pipeline.

Operator tool — not used by CI. Everything here is a pure argv builder plus a
thin subprocess runner, so the command lines are unit-testable without either
binary present. Stdlib only: no third-party imports at all.

This is a CPU-only pipeline. COLMAP's `patch_match_stereo` (and therefore
`stereo_fusion` and `poisson_mesher`, which consume its output) is CUDA-only
and hard-errors on a CPU build, and nixpkgs' `colmapWithCuda` is not in the
binary cache. So COLMAP does sparse reconstruction and undistortion only, and
OpenMVS (`InterfaceCOLMAP` -> `DensifyPointCloud` -> `ReconstructMesh`) does
densification and meshing. Never add the CUDA-only subcommands back.

Option names here are COLMAP 4.x's. 4.0 renamed the SIFT option groups —
`SiftExtraction.*` -> `FeatureExtraction.*`, `SiftMatching.*` ->
`FeatureMatching.*` — and the 3.x spellings are a hard parse error, not a
warning (issue #417). If a `flake.lock` bump moves COLMAP again, re-check every
`--Group.option` below against `colmap <subcommand> --help` inside
`nix develop .#scan`; `ColmapOptionNamesTests` in test_scan_colmap.py does
exactly that, but only when colmap is on PATH.
"""

import pathlib
import struct
import subprocess
import shutil
import sys


def feature_extractor_argv(db, image_dir, mask_dir, threads):
    """`colmap feature_extractor` over the masked frames.

    One camera for the whole capture (the phone never moves) and SIFT on the
    CPU, because the flake's colmap has no CUDA.
    """
    return [
        "feature_extractor",
        "--database_path", str(db),
        "--image_path", str(image_dir),
        "--ImageReader.mask_path", str(mask_dir),
        "--ImageReader.single_camera", "1",
        "--ImageReader.camera_model", "SIMPLE_RADIAL",
        "--FeatureExtraction.use_gpu", "0",
        "--FeatureExtraction.num_threads", str(threads),
    ]


def exhaustive_matcher_argv(db, threads):
    """`colmap exhaustive_matcher`.

    Exhaustive rather than sequential: the turntable brings the camera back
    past viewpoints it has already seen, and exhaustive matching is what closes
    that loop. Sequential matching would only ever link adjacent frames.
    """
    return [
        "exhaustive_matcher",
        "--database_path", str(db),
        "--FeatureMatching.use_gpu", "0",
        "--FeatureMatching.num_threads", str(threads),
    ]


def mapper_argv(db, image_dir, out_dir):
    """`colmap mapper` — incremental sparse reconstruction.

    The principal point is left fixed: a single-camera turntable capture does
    not constrain it, and refining it bends the reconstruction.
    """
    return [
        "mapper",
        "--database_path", str(db),
        "--image_path", str(image_dir),
        "--output_path", str(out_dir),
        "--Mapper.ba_refine_principal_point", "0",
    ]


def image_undistorter_argv(image_dir, sparse_model, dense_dir, max_image_size=1600):
    """`colmap image_undistorter` — the handoff format OpenMVS reads."""
    return [
        "image_undistorter",
        "--image_path", str(image_dir),
        "--input_path", str(sparse_model),
        "--output_path", str(dense_dir),
        "--output_type", "COLMAP",
        "--max_image_size", str(max_image_size),
    ]


def interface_colmap_argv(dense_dir, mvs_scene):
    """OpenMVS `InterfaceCOLMAP` — COLMAP dense workspace to an .mvs scene.

    `--image-folder` is passed explicitly: OpenMVS resolves it relative to the
    working directory otherwise, and the pipeline never chdir's.
    """
    dense_dir = pathlib.Path(dense_dir)
    return [
        "-i", str(dense_dir),
        "-o", str(mvs_scene),
        "--image-folder", str(dense_dir / "images"),
    ]


def densify_argv(mvs_scene, resolution_level=1):
    """OpenMVS `DensifyPointCloud`.

    Writes `<stem>_dense.mvs` and `<stem>_dense.ply` next to its input — use
    `dense_scene_path()` to derive those rather than guessing.

    `-w` is the scene's own folder: `InterfaceCOLMAP` stores image paths
    relative to the scene file, but OpenMVS resolves them against its working
    folder, which defaults to the CWD (issue #419). The scene path itself is
    absolutised because OpenMVS also joins a *relative* input filename onto
    that same working folder, which would double-prefix it.
    """
    mvs_scene = pathlib.Path(mvs_scene).resolve()
    return [
        str(mvs_scene),
        "--resolution-level", str(resolution_level),
        "-w", str(mvs_scene.parent),
    ]


def reconstruct_mesh_argv(mvs_dense_scene):
    """OpenMVS `ReconstructMesh` — writes `<stem>_mesh.ply` next to its input.

    Same working-folder rule as `densify_argv` (issue #419).
    """
    mvs_dense_scene = pathlib.Path(mvs_dense_scene).resolve()
    return [str(mvs_dense_scene), "-w", str(mvs_dense_scene.parent)]


def derived_scene_path(scene, suffix, extension):
    """OpenMVS' output naming: `scene.mvs` + "dense" -> `scene_dense.mvs`."""
    scene = pathlib.Path(scene)
    return scene.with_name(f"{scene.stem}_{suffix}{extension}")


STDOUT_TAIL_LINES = 50


def _echo_failed_output(binary, proc):
    """Re-print a failed `quiet` run's captured output.

    OpenMVS logs its errors to stdout, not stderr, so echoing only stderr left
    a failed stage with no message whatsoever (issue #419).
    """
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    lines = (proc.stdout or "").splitlines()
    tail = lines[-STDOUT_TAIL_LINES:]
    if tail:
        sys.stderr.write(f"--- last {len(tail)} line(s) of {binary} stdout ---\n")
        sys.stderr.write("\n".join(tail) + "\n")
    elif not proc.stderr:
        sys.stderr.write(f"error: {binary} exited {proc.returncode} with no output\n")


def run(binary, argv, quiet=False):
    """Run one pipeline binary, failing loudly with the devShell hint."""
    path = shutil.which(binary)
    if path is None:
        sys.exit(f"error: {binary} not found — run inside `nix develop .#scan`")
    proc = subprocess.run([path, *argv], capture_output=quiet, text=True, check=False)
    if proc.returncode != 0:
        if quiet:
            _echo_failed_output(binary, proc)
        sys.exit(proc.returncode)
    return proc.returncode


def pick_sparse_model(sparse_dir):
    """Pick the sparse model directory COLMAP's mapper reconstructed.

    The mapper writes `sparse/0`, `sparse/1`, ... when the capture fragments
    into disconnected sub-models; the largest `images.bin` is the one that
    registered the most frames.
    """
    sparse_dir = pathlib.Path(sparse_dir)
    models = sorted(d for d in sparse_dir.glob("*") if (d / "images.bin").is_file())
    if not models:
        sys.exit(
            "mapper reconstructed no model — check roi-preview.jpg; the "
            "platter ellipse may be excluding the rim texture"
        )
    if len(models) > 1:
        models.sort(key=lambda d: (d / "images.bin").stat().st_size, reverse=True)
        print(f"warning: mapper produced {len(models)} models; using {models[0]}")
    return models[0]


def count_registered_images(model_dir):
    """Number of images registered in a sparse model.

    `images.bin` opens with a little-endian uint64 image count, so this needs
    no COLMAP bindings.
    """
    with open(pathlib.Path(model_dir) / "images.bin", "rb") as handle:
        header = handle.read(8)
    if len(header) < 8:
        raise RuntimeError(f"{model_dir}/images.bin is truncated")
    return int(struct.unpack("<Q", header)[0])
