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

from scan_colmap import interface_colmap_argv
from scan_pipeline import (
    STAGES,
    _mvs_scene,
    _select_hold_indices,
    parse_args,
    run_clean,
    run_reference,
    stage_stamp,
    stages_to_run,
)


class StagesToRunTests(unittest.TestCase):
    def test_default_runs_every_stage_in_order(self):
        self.assertEqual(stages_to_run(None, None, None), STAGES)
        self.assertEqual(
            stages_to_run(None, None, None),
            ["frames", "masks", "sfm", "dense", "mesh", "clean", "reference"],
        )

    def test_only_runs_one_stage(self):
        self.assertEqual(stages_to_run(None, None, "masks"), ["masks"])

    def test_from_to_is_inclusive(self):
        self.assertEqual(stages_to_run("masks", "sfm", None), ["masks", "sfm"])
        self.assertEqual(stages_to_run("frames", "frames", None), ["frames"])
        self.assertEqual(
            stages_to_run("dense", None, None),
            ["dense", "mesh", "clean", "reference"],
        )
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
        self.assertEqual(args.capture_mode, "continuous")
        self.assertEqual(args.min_holds, 20)
        self.assertEqual(args.work_dir, pathlib.Path(".cache/scan/IMG_3814").resolve())
        self.assertEqual(
            args.output,
            pathlib.Path(".cache/scan/IMG_3814").resolve() / "output" / "IMG_3814.stl",
        )

    def test_capture_mode_holds(self):
        args = parse_args(["a.MOV", "--capture-mode", "holds"])
        self.assertEqual(args.capture_mode, "holds")

    def test_bad_capture_mode_is_rejected(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                parse_args(["a.MOV", "--capture-mode", "bogus"])

    def test_reference_defaults(self):
        args = parse_args(["/captures/IMG_3814.MOV"])
        self.assertEqual(args.reference_mode, "hull")
        self.assertEqual(args.reference_slabs, 12)
        self.assertEqual(args.reference_max_bytes, 512000)
        self.assertEqual(
            args.reference_out,
            pathlib.Path(".cache/scan/IMG_3814").resolve()
            / "output" / "IMG_3814-reference.stl",
        )
        self.assertIsNone(args.install_as)

    def test_output_defaults_under_explicit_work_dir(self):
        args = parse_args(["/captures/IMG_3814.MOV", "--work-dir", "/tmp/scan"])
        self.assertEqual(
            args.output,
            pathlib.Path("/tmp/scan").resolve() / "output" / "IMG_3814.stl",
        )

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

    def test_relative_work_dir_is_absolutised(self):
        args = parse_args(["a.MOV", "--work-dir", ".cache/scan/IMG_3948"])
        self.assertTrue(args.work_dir.is_absolute())
        self.assertTrue(args.output.is_absolute())
        self.assertTrue(args.reference_out.is_absolute())
        self.assertEqual(
            args.work_dir, (pathlib.Path.cwd() / ".cache/scan/IMG_3948").resolve()
        )

    def test_relative_work_dir_gives_openmvs_absolute_paths(self):
        # End-to-end regression pin for issue #470.
        args = parse_args(["a.MOV", "--work-dir", ".cache/scan/IMG_3948"])
        scene = _mvs_scene(args.work_dir)
        self.assertTrue(scene.is_absolute())
        argv = interface_colmap_argv(args.work_dir / "dense", scene)
        image_folder = argv[argv.index("--image-folder") + 1]
        self.assertTrue(pathlib.Path(image_folder).is_absolute())
        self.assertEqual(image_folder.count(".cache/scan/IMG_3948/dense"), 1)


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
            self.assertEqual(report["capture_mode"], "continuous")

    def test_missing_dense_cloud_still_fails(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = self._work_dir(tmp, dense=False)
            args = parse_args(["cap.MOV", "--work-dir", str(work_dir), "--quiet"])
            with mock.patch.dict(sys.modules, self._fakes(calls)):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        run_clean(args)


class SelectHoldIndicesTests(unittest.TestCase):
    """`_select_hold_indices` against canned (scores, diffs) — no cv2/scan devShell needed."""

    def _args(self, tmp, **overrides):
        work_dir = pathlib.Path(tmp) / "work"
        work_dir.mkdir()
        argv = ["cap.MOV", "--work-dir", str(work_dir), "--quiet"]
        for name, value in overrides.items():
            argv += [f"--{name.replace('_', '-')}", str(value)]
        return parse_args(argv)

    def test_report_diff_p25_is_the_actual_percentile_when_floor_dominates(self):
        # All-quiet diffs: HOLD_DIFF_FLOOR (0.35) dominates hold_threshold's
        # max(), so diff_p25 must still report the true 25th percentile
        # (0.05), not the clamped threshold divided back out (0.2333...).
        scores = list(range(41))
        diffs = [0.05] * 40
        with tempfile.TemporaryDirectory() as tmp:
            args = self._args(tmp, min_holds=1)
            with mock.patch(
                "scan_pipeline.score_sharpness_and_diffs",
                return_value=(scores, diffs),
            ):
                _select_hold_indices(args, [pathlib.Path("x.jpg")] * len(scores))
            report = json.loads((args.work_dir / "hold-report.json").read_text())
            self.assertEqual(report["diff_threshold"], 0.35)
            self.assertEqual(report["diff_p25"], 0.05)

    def test_exits_when_selected_holds_are_below_min_holds(self):
        scores = [0] * 11
        # Alternating quiet/motion diffs: every static dip is only 1 frame
        # long, well under HOLD_MIN_RUN (10), so no run survives filtering.
        diffs = [0.1, 8, 0.1, 8, 0.1, 8, 0.1, 8, 0.1, 8]
        with tempfile.TemporaryDirectory() as tmp:
            args = self._args(tmp)  # default --min-holds 20
            with mock.patch(
                "scan_pipeline.score_sharpness_and_diffs",
                return_value=(scores, diffs),
            ):
                with self.assertRaises(SystemExit):
                    _select_hold_indices(args, [pathlib.Path("x.jpg")] * len(scores))
            report = json.loads((args.work_dir / "hold-report.json").read_text())
            self.assertEqual(report["holds_detected"], 0)
            self.assertEqual(report["selected_frame_indices"], [])

    def test_thins_selection_down_to_the_frames_cap(self):
        # Three separated 11-frame holds, each well above HOLD_MIN_RUN (10),
        # split by motion spikes so they don't merge into one run.
        scores = list(range(33))
        diffs = [0.05] * 10 + [5.0] + [0.05] * 10 + [5.0] + [0.05] * 10
        with tempfile.TemporaryDirectory() as tmp:
            args = self._args(tmp, min_holds=1, frames=2)
            with mock.patch(
                "scan_pipeline.score_sharpness_and_diffs",
                return_value=(scores, diffs),
            ):
                selected = _select_hold_indices(
                    args, [pathlib.Path("x.jpg")] * len(scores)
                )
            report = json.loads((args.work_dir / "hold-report.json").read_text())
            self.assertEqual(report["holds_detected"], 3)
            self.assertEqual(report["hold_frame_counts"], [11, 11, 11])
            # Report captures the pre-thin selection...
            self.assertEqual(report["selected_frame_indices"], [8, 19, 30])
            # ...while the returned value is thinned to the --frames cap.
            self.assertEqual(selected, [8, 19])


class RunReferenceTests(unittest.TestCase):
    """reference builds a watertight mesh, and only installs when asked to."""

    def _fakes(self, installed):
        reference = types.SimpleNamespace(
            faces=[0, 1, 2, 3],
            bounds=[[0.0, 0.0, 0.0], [1.0, 1.0, 2.0]],
        )
        mesh = types.SimpleNamespace(faces=list(range(9)))
        trimesh = types.ModuleType("trimesh")
        trimesh.load = lambda path, process=True: mesh

        scan_reference = types.ModuleType("scan_reference")
        scan_reference.build_reference = lambda m, mode, slabs: reference
        scan_reference.assert_watertight = lambda m: m
        scan_reference.write_reference = lambda m, path, max_bytes: (
            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            or pathlib.Path(path).write_bytes(b"stl")
        )
        scan_reference.sanitised_report = lambda report, extra: dict(
            report, video=pathlib.Path(report["video"]).name, reference=extra
        )

        def install(stl_path, report, object_name, repo_root, force=False):
            installed.append((pathlib.Path(stl_path), report, object_name, force))
            return pathlib.Path("scans") / object_name / "x.stl", pathlib.Path("r.json")

        scan_reference.install_reference = install
        return {"trimesh": trimesh, "scan_reference": scan_reference}

    def _work_dir(self, tmp):
        work_dir = pathlib.Path(tmp)
        (work_dir / "output").mkdir(parents=True)
        (work_dir / "output" / "cap.stl").write_bytes(b"stl")
        (work_dir / "scan-report.json").write_text(
            json.dumps({"video": "/home/someone/captures/cap.MOV"}) + "\n"
        )
        return work_dir

    def test_writes_the_reference_without_installing_it(self):
        installed = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = self._work_dir(tmp)
            args = parse_args(["cap.MOV", "--work-dir", str(work_dir), "--quiet"])
            with mock.patch.dict(sys.modules, self._fakes(installed)):
                run_reference(args)
            self.assertTrue(args.reference_out.exists())
            self.assertEqual(installed, [])

    def test_install_as_passes_the_sanitised_report(self):
        installed = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = self._work_dir(tmp)
            args = parse_args([
                "cap.MOV", "--work-dir", str(work_dir), "--quiet",
                "--reference-mode", "slabs", "--install-as", "tube",
            ])
            with mock.patch.dict(sys.modules, self._fakes(installed)):
                run_reference(args)
            self.assertEqual(len(installed), 1)
            stl_path, report, object_name, force = installed[0]
            self.assertEqual(stl_path, args.reference_out)
            self.assertEqual(object_name, "tube")
            self.assertFalse(force)
            # The absolute capture path must not reach scans/, which mirrors
            # to the public repo.
            self.assertEqual(report["video"], "cap.MOV")
            self.assertEqual(report["reference"]["mode"], "slabs")
            self.assertEqual(report["reference"]["slabs"], 12)
            self.assertEqual(report["reference"]["faces"], 4)
            self.assertTrue(report["reference"]["watertight"])

    def test_missing_clean_output_fails(self):
        installed = []
        with tempfile.TemporaryDirectory() as tmp:
            args = parse_args(["cap.MOV", "--work-dir", tmp, "--quiet"])
            with mock.patch.dict(sys.modules, self._fakes(installed)):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        run_reference(args)


if __name__ == "__main__":
    unittest.main()
