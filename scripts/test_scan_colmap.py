"""Unit tests for scan_colmap.py.

Command lines only — nothing here runs colmap or OpenMVS, and there are no
third-party imports. Run with: python3 -m unittest scripts/test_scan_colmap.py
"""

import contextlib
import io
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_colmap import (
    STDOUT_TAIL_LINES,
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

ALL_BUILDERS = [
    feature_extractor_argv("db", "images", "masks", 4),
    exhaustive_matcher_argv("db", 4),
    mapper_argv("db", "images", "sparse"),
    image_undistorter_argv("images", "sparse/0", "dense"),
    interface_colmap_argv("dense", "mvs/scene.mvs"),
    densify_argv("mvs/scene.mvs"),
    reconstruct_mesh_argv("mvs/scene_dense.mvs"),
]


class ArgvBuilderTests(unittest.TestCase):
    def assert_pair(self, argv, flag, value):
        self.assertIn(flag, argv, f"{flag} missing from {argv}")
        self.assertEqual(argv[argv.index(flag) + 1], value)

    def test_feature_extractor(self):
        argv = feature_extractor_argv("work/db.db", "work/frames", "work/masks", 8)
        self.assertEqual(argv[0], "feature_extractor")
        self.assert_pair(argv, "--database_path", "work/db.db")
        self.assert_pair(argv, "--image_path", "work/frames")
        self.assert_pair(argv, "--ImageReader.mask_path", "work/masks")
        self.assert_pair(argv, "--ImageReader.single_camera", "1")
        self.assert_pair(argv, "--ImageReader.camera_model", "SIMPLE_RADIAL")
        self.assert_pair(argv, "--FeatureExtraction.use_gpu", "0")
        self.assert_pair(argv, "--FeatureExtraction.num_threads", "8")

    def test_feature_extractor_accepts_paths(self):
        argv = feature_extractor_argv(
            pathlib.Path("work/db.db"),
            pathlib.Path("work/frames"),
            pathlib.Path("work/masks"),
            2,
        )
        self.assert_pair(argv, "--image_path", "work/frames")

    def test_exhaustive_matcher_is_cpu_only(self):
        argv = exhaustive_matcher_argv("work/db.db", 8)
        self.assertEqual(argv[0], "exhaustive_matcher")
        self.assert_pair(argv, "--database_path", "work/db.db")
        self.assert_pair(argv, "--FeatureMatching.use_gpu", "0")
        self.assert_pair(argv, "--FeatureMatching.num_threads", "8")

    def test_matching_is_exhaustive_not_sequential(self):
        # The turntable revisits viewpoints; sequential matching would only
        # ever link adjacent frames and never close the loop.
        self.assertNotIn("sequential_matcher", exhaustive_matcher_argv("db", 1))

    def test_mapper_fixes_the_principal_point(self):
        argv = mapper_argv("work/db.db", "work/frames", "work/sparse")
        self.assertEqual(argv[0], "mapper")
        self.assert_pair(argv, "--output_path", "work/sparse")
        self.assert_pair(argv, "--Mapper.ba_refine_principal_point", "0")

    def test_image_undistorter(self):
        argv = image_undistorter_argv("work/frames", "work/sparse/0", "work/dense")
        self.assertEqual(argv[0], "image_undistorter")
        self.assert_pair(argv, "--input_path", "work/sparse/0")
        self.assert_pair(argv, "--output_path", "work/dense")
        self.assert_pair(argv, "--output_type", "COLMAP")
        self.assert_pair(argv, "--max_image_size", "1600")

    def test_interface_colmap_names_the_image_folder(self):
        argv = interface_colmap_argv("work/dense", "work/mvs/scene.mvs")
        self.assert_pair(argv, "-i", "work/dense")
        self.assert_pair(argv, "-o", "work/mvs/scene.mvs")
        self.assert_pair(argv, "--image-folder", str(pathlib.Path("work/dense/images")))

    def test_densify_names_the_scene_folder_as_working_folder(self):
        scene = pathlib.Path("work/mvs/scene.mvs").resolve()
        argv = densify_argv("work/mvs/scene.mvs")
        self.assertEqual(argv[0], str(scene))
        self.assertTrue(pathlib.Path(argv[0]).is_absolute())
        self.assert_pair(argv, "--resolution-level", "1")
        # OpenMVS resolves scene-relative image paths against -w (issue #419).
        self.assert_pair(argv, "-w", str(scene.parent))

    def test_reconstruct_mesh_names_the_scene_folder_as_working_folder(self):
        scene = pathlib.Path("work/mvs/scene_dense.mvs").resolve()
        argv = reconstruct_mesh_argv("work/mvs/scene_dense.mvs")
        self.assertEqual(argv, [str(scene), "-w", str(scene.parent)])

    def test_openmvs_scene_paths_are_absolute_so_w_cannot_double_prefix(self):
        # A relative input filename would be joined onto -w by OpenMVS.
        for argv in (densify_argv("mvs/scene.mvs"),
                     reconstruct_mesh_argv("mvs/scene_dense.mvs")):
            with self.subTest(argv=argv[0]):
                self.assertTrue(pathlib.Path(argv[0]).is_absolute())

    def test_no_builder_uses_a_cuda_only_subcommand(self):
        # patch_match_stereo is CUDA-only and hard-errors on the CPU colmap in
        # this flake; stereo_fusion and poisson_mesher consume its output.
        # Dense reconstruction goes through OpenMVS instead — deliberately.
        for argv in ALL_BUILDERS:
            joined = " ".join(argv)
            for forbidden in ("patch_match_stereo", "stereo_fusion", "poisson_mesher"):
                with self.subTest(argv=argv[0], forbidden=forbidden):
                    self.assertNotIn(forbidden, joined)

    def test_no_builder_uses_colmap_3_option_names(self):
        # COLMAP 4.0 renamed these groups; the 3.x spellings are a hard parse
        # error on the flake's colmap, not a warning (issue #417).
        for argv in ALL_BUILDERS:
            joined = " ".join(argv)
            for stale in ("SiftExtraction", "SiftMatching"):
                with self.subTest(argv=argv[0], stale=stale):
                    self.assertNotIn(stale, joined)


class RunOutputTests(unittest.TestCase):
    def test_quiet_failure_echoes_stdout(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                run(sys.executable,
                    ["-c", "import sys; print('boom on stdout'); sys.exit(1)"],
                    quiet=True)
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("boom on stdout", stderr.getvalue())

    def test_quiet_failure_still_echoes_stderr(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                run(sys.executable,
                    ["-c", "import sys; sys.stderr.write('stderr line\\n'); sys.exit(1)"],
                    quiet=True)
        self.assertIn("stderr line", stderr.getvalue())

    def test_quiet_failure_truncates_stdout_to_the_tail(self):
        stderr = io.StringIO()
        script = (
            "for i in range(200): print(f'line{i}')\n"
            "import sys; sys.exit(1)\n"
        )
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                run(sys.executable, ["-c", script], quiet=True)
        output = stderr.getvalue()
        self.assertIn("line199", output)
        self.assertNotIn("line0\n", output)
        # Count only the echoed `lineNNN` tokens, not the "line(s)" in the
        # header _echo_failed_output writes above the tail.
        self.assertEqual(len(re.findall(r"line\d+", output)), STDOUT_TAIL_LINES)

    def test_quiet_failure_with_no_output_still_says_something(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                run(sys.executable, ["-c", "import sys; sys.exit(3)"], quiet=True)
        self.assertEqual(ctx.exception.code, 3)
        self.assertTrue(stderr.getvalue().strip())

    def test_quiet_success_prints_nothing(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = run(sys.executable,
                         ["-c", "print('all good')"],
                         quiet=True)
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_missing_binary_exits_with_the_devshell_hint(self):
        with self.assertRaises(SystemExit) as ctx:
            run("definitely-not-a-real-binary-419", [], quiet=True)
        self.assertIn("nix develop .#scan", str(ctx.exception.code))


class DerivedScenePathTests(unittest.TestCase):
    def test_openmvs_output_naming(self):
        scene = pathlib.Path("work/mvs/scene.mvs")
        self.assertEqual(
            derived_scene_path(scene, "dense", ".ply"),
            pathlib.Path("work/mvs/scene_dense.ply"),
        )
        self.assertEqual(
            derived_scene_path("work/mvs/scene_dense.mvs", "mesh", ".ply"),
            pathlib.Path("work/mvs/scene_dense_mesh.ply"),
        )


class PickSparseModelTests(unittest.TestCase):
    def _model(self, root, name, size):
        directory = pathlib.Path(root) / name
        directory.mkdir(parents=True)
        (directory / "images.bin").write_bytes(b"\0" * size)
        return directory

    def test_picks_the_largest_images_bin(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._model(tmp, "0", 100)
            bigger = self._model(tmp, "1", 5000)
            self.assertEqual(pick_sparse_model(tmp), bigger)

    def test_single_model_is_used_as_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            only = self._model(tmp, "0", 10)
            self.assertEqual(pick_sparse_model(tmp), only)

    def test_no_model_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                pick_sparse_model(tmp)


class CountRegisteredImagesTests(unittest.TestCase):
    def test_reads_the_images_bin_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = pathlib.Path(tmp)
            (model / "images.bin").write_bytes(struct.pack("<Q", 142) + b"junk")
            self.assertEqual(count_registered_images(model), 142)

    def test_truncated_header_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = pathlib.Path(tmp)
            (model / "images.bin").write_bytes(b"\0\0")
            with self.assertRaises(RuntimeError):
                count_registered_images(model)


COLMAP_SUBCOMMAND_ARGV = [
    feature_extractor_argv("db", "images", "masks", 4),
    exhaustive_matcher_argv("db", 4),
    mapper_argv("db", "images", "sparse"),
    image_undistorter_argv("images", "sparse/0", "dense"),
]


@unittest.skipUnless(shutil.which("colmap"),
                     "colmap not on PATH — run inside `nix develop .#scan`")
class ColmapOptionNamesTests(unittest.TestCase):
    """Validate the argv builders against the colmap that is actually installed.

    Skipped everywhere colmap is absent, which includes CI — the `default`
    devShell has no colmap, only `scan` does. Issue #417: the unit tests above
    pin argv strings, and nothing caught COLMAP 4.0 renaming the SIFT option
    groups until the pipeline failed on the first binary invocation.
    """

    def test_every_option_name_appears_in_colmaps_help(self):
        colmap = shutil.which("colmap")
        for argv in COLMAP_SUBCOMMAND_ARGV:
            subcommand = argv[0]
            proc = subprocess.run([colmap, subcommand, "--help"],
                                  capture_output=True, text=True, check=False)
            help_text = proc.stdout + proc.stderr
            self.assertTrue(help_text.strip(),
                            f"`colmap {subcommand} --help` printed nothing")
            for option in (a for a in argv[1:] if a.startswith("--")):
                with self.subTest(subcommand=subcommand, option=option):
                    self.assertIn(option, help_text)


if __name__ == "__main__":
    unittest.main()
