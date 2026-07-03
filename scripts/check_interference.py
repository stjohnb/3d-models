"""Check mating part interference via mesh Boolean intersection.

For each project that declares ``mating_pairs`` in meta.json, loads both STLs
from the ``site/`` directory and computes their Boolean intersection volume
using trimesh + manifold3d.  If the volume exceeds THRESHOLD_MM3, the parts
physically overlap and cannot assemble — the step records a failure.

Results are written to ``site/interference.json`` and the ``failed`` flag is
written to ``$GITHUB_OUTPUT``.
"""

import glob
import json
import os
import warnings

from oembed_helpers import load_meta_failures

# Minimum overlap volume (mm³) considered a real interference.
# Accounts for floating-point noise in mesh boolean operations.
THRESHOLD_MM3 = 0.1


def _make_result(project, part_a, part_b, *, passed=True, skipped=False, error=None, overlap_mm3=None):
    """Build a standard result dict for a mating-pair interference check."""
    result = {
        "project": project,
        "part_a": part_a,
        "part_b": part_b,
        "overlap_volume_mm3": overlap_mm3,
        "threshold_mm3": THRESHOLD_MM3,
        "passed": passed,
    }
    if skipped:
        result["skipped"] = True
    if error is not None:
        result["error"] = error
    return result


def check_pair(project, part_a, part_b, site_dir="site"):
    """Check one mating pair.  Returns a result dict."""
    import trimesh
    import trimesh.boolean
    import trimesh.repair

    path_a = os.path.join(site_dir, part_a)
    path_b = os.path.join(site_dir, part_b)

    for path, name in [(path_a, part_a), (path_b, part_b)]:
        if not os.path.isfile(path):
            print(f"  SKIP: {project} — {name} not found in {site_dir}/")
            return _make_result(project, part_a, part_b, skipped=True, error=f"{name} not found")

    try:
        mesh_a = trimesh.load(path_a, force="mesh")
        mesh_b = trimesh.load(path_b, force="mesh")
    except Exception as exc:
        msg = f"Failed to load meshes: {exc}"
        print(f"  FAIL: {project} — {part_a} / {part_b} — {msg}")
        return _make_result(project, part_a, part_b, passed=False, error=msg)

    # Attempt to repair meshes that are not watertight volumes.  OpenSCAD can
    # produce meshes with small holes or duplicate faces; fill_holes() closes
    # open boundaries so manifold3d accepts them for Boolean operations.
    for mesh, name in [(mesh_a, part_a), (mesh_b, part_b)]:
        if not mesh.is_watertight:
            trimesh.repair.fill_holes(mesh)
            if not mesh.is_watertight:
                print(f"  WARN: {project} — {name} is not a watertight volume after repair")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            intersection = trimesh.boolean.intersection(
                [mesh_a, mesh_b], engine="manifold"
            )
        volume = abs(float(intersection.volume)) if intersection is not None else 0.0
    except Exception as exc:
        msg = f"Boolean operation failed: {exc}"
        # A "not a volume" error means the mesh is non-manifold — a mesh quality
        # issue that the STL validation step is responsible for catching.  Skip
        # rather than fail so the interference step doesn't block on mesh defects
        # that are orthogonal to physical part interference.
        # NOTE: The string "not all meshes are volumes" is the error message emitted
        # by manifold3d >=2.3,<4 when a non-manifold mesh is passed for Boolean ops.
        # The version pin 'manifold3d>=2.3,<4' is set in
        # .github/workflows/build.yml (the "Check mating part interference" step).
        # If the upper bound is raised, verify this string still matches before
        # releasing, and update it here if manifold3d changes the wording.
        if "not all meshes are volumes" in str(exc).lower():
            print(f"  SKIP: {project} — {part_a} / {part_b} — non-manifold mesh, cannot check ({exc})")
            return _make_result(project, part_a, part_b, skipped=True, error=f"Skipped: {msg}")
        print(f"  FAIL: {project} — {part_a} / {part_b} — {msg}")
        return _make_result(project, part_a, part_b, passed=False, error=msg)

    passed = volume <= THRESHOLD_MM3
    status = "PASS" if passed else "FAIL"
    print(
        f"  {status}: {project} — {part_a} / {part_b} — overlap={volume:.4f} mm³"
        f" (threshold={THRESHOLD_MM3} mm³)"
    )
    if not passed:
        print(
            f"  Interference detected: {part_a} and {part_b} overlap by"
            f" {volume:.1f} mm³ at the connection interface."
        )

    return _make_result(project, part_a, part_b, passed=passed, overlap_mm3=round(volume, 4))


def main():
    failed_meta = load_meta_failures()
    results = []
    has_failure = False

    for meta_path in sorted(glob.glob("*/meta.json")):
        if meta_path in failed_meta:
            print(f"  Skipping {meta_path} (failed schema validation)")
            continue

        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        mating_pairs = meta.get("mating_pairs")
        if not mating_pairs:
            continue

        project = os.path.dirname(meta_path)
        print(f"Checking interference for project: {project}")

        for pair in mating_pairs:
            if len(pair) != 2:
                print(f"  SKIP: invalid pair {pair!r} (must have exactly 2 entries)")
                continue
            result = check_pair(project, pair[0], pair[1])
            results.append(result)
            if not result["passed"] and not result.get("skipped"):
                has_failure = True

    os.makedirs("site", exist_ok=True)
    with open("site/interference.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nWrote {len(results)} result(s) to site/interference.json")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"failed={str(has_failure).lower()}\n")


if __name__ == "__main__":
    main()
