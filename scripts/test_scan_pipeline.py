"""Unit tests for scan_pipeline.py.

Covers stage resolution and argument parsing only — no ffmpeg, colmap or
openmvs invocation, and no third-party imports. run_clean is exercised
against stub trimesh/numpy/scan_mesh modules instead.
Run with: python3 -m unittest scripts/test_scan_pipeline.py
"""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_pipeline import STAGES, parse_args, run_clean, stage_stamp, stages_to_run


class StagesToRunTests(unittest.TestCase):
    def test_default_runs_every_stage_in_order(self):
        self.assertEqual(stages_to_run(None, None, None), STAGES)
        self.assertEqual(
            stages_to_run(None, None, None),
            ["frames", "masks", "sfm", "dense", "mesh", "clean"],
        )

    def test_only_runs_one_stage(self):
        self.assertEqual(stages_to_run(None, None, "masks"), ["masks"])

    def test_from_to_is_inclusive(self):
        self.assertEqual(stages_to_run("masks", "sfm", None), ["masks", "sfm"])
        self.assertEqual(stages_to_run("frames", "frames", None), ["frames"])
        self.assertEqual(stages_to_run("dense", None, None), ["dense", "mesh", "clean"])
        self.assertEqual(stages_to_run(None, "masks", None), ["frames", "masks"])

    def test_inverted_range_raises(self):
        with self.assertRaises(ValueError):
            stages_to_run("sfm", "masks", None)


class ParseArgsTests(unittest.TestCase):
    def test_defaults(self):
        args = parse_args(["/captures/IMG_3814.MOV"])
        self.assertEqual(args.frames, 150)
        self.assertEqual(args.mask_mode, "salient")
        self.assertEqual(args.object_height, 400)
        self.assertIsNone(args.platter)
        self.assertFalse(args.force)
        self.assertEqual(args.work_dir, pathlib.Path(".cache/scan/IMG_3814"))
        self.assertEqual(
            args.output, pathlib.Path(".cache/scan/IMG_3814/output/IMG_3814.stl")
        )

    def test_output_defaults_under_explicit_work_dir(self):
        args = parse_args(["/captures/IMG_3814.MOV", "--work-dir", "/tmp/scan"])
        self.assertEqual(args.output, pathlib.Path("/tmp/scan/output/IMG_3814.stl"))

    def test_platter_is_parsed_into_floats(self):
        args = parse_args(["a.MOV", "--platter", "540,1420,470,150"])
        self.assertEqual(args.platter, (540.0, 1420.0, 470.0, 150.0))

    def test_bad_platter_is_rejected(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                parse_args(["a.MOV", "--platter", "540,1420,470"])

    def test_only_with_from_raises(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                parse_args(["a.MOV", "--only", "masks", "--from", "frames"])

    def test_only_with_to_raises(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                parse_args(["a.MOV", "--only", "masks", "--to", "sfm"])


class StageStampTests(unittest.TestCase):
    def test_stamp_path(self):
        self.assertEqual(
            stage_stamp(pathlib.Path("/tmp/scan"), "masks"),
            pathlib.Path("/tmp/scan/.stamp-masks.json"),
        )


class RunCleanPlatterSourceTests(unittest.TestCase):
    """clean must fit the platter on the mesh, never the dense cloud (#421).

    trimesh cannot read the per-vertex list properties DensifyPointCloud
    writes into scene_dense.ply, so pointing the fit at it fails every
    capture with "PLY is unexpected length!".
    """

    def _fakes(self, calls):
        mesh = types.SimpleNamespace(
            faces=[0, 1, 2],
            bounds=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
            apply_transform=lambda matrix: None,
        )
        trimesh = types.ModuleType("trimesh")
        trimesh.load = lambda path, process=True: mesh
        scan_mesh = types.ModuleType("scan_mesh")
        scan_mesh.load_points = lambda path: calls.append(pathlib.Path(path))
        scan_mesh.platter_frame = lambda points, platter_diameter=150.0: {
            "origin": None, "rotation": None, "radius_units": 0.5,
            "mm_per_unit": 150.0, "plane_inliers": None,
        }
        scan_mesh.scale_transform = lambda frame: None
        scan_mesh.crop_to_object = lambda m, z_min, z_max, r_max: m
        scan_mesh.keep_largest_components = lambda m, count: m
        scan_mesh.export_stl = lambda m, path: None
        return {"trimesh": trimesh, "numpy": types.ModuleType("numpy"),
                "scan_mesh": scan_mesh}

    def _work_dir(self, tmp, dense=True, mesh=True):
        mvs = pathlib.Path(tmp) / "mvs"
        mvs.mkdir(parents=True)
        if dense:
            (mvs / "scene_dense.ply").write_text("")
        if mesh:
            (mvs / "scene_dense_mesh.ply").write_text("")
        return pathlib.Path(tmp)

    def test_platter_is_fitted_on_the_mesh_not_the_dense_cloud(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = self._work_dir(tmp)
            args = parse_args(["cap.MOV", "--work-dir", str(work_dir), "--quiet"])
            with mock.patch.dict(sys.modules, self._fakes(calls)):
                run_clean(args)
            self.assertEqual([p.name for p in calls], ["scene_dense_mesh.ply"])
            report = json.loads((work_dir / "scan-report.json").read_text())
            self.assertEqual(report["mm_per_unit"], 150.0)

    def test_missing_dense_cloud_still_fails(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = self._work_dir(tmp, dense=False)
            args = parse_args(["cap.MOV", "--work-dir", str(work_dir), "--quiet"])
            with mock.patch.dict(sys.modules, self._fakes(calls)):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        run_clean(args)


if __name__ == "__main__":
    unittest.main()
