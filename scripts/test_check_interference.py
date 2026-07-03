"""Unit tests for check_interference.py.

Uses trimesh.creation primitives to generate meshes programmatically,
so no fixture STL files are needed.
"""

import json
import os
import sys
import tempfile
import unittest
import unittest.mock

# Ensure the scripts directory is on the path so we can import check_interference
sys.path.insert(0, os.path.dirname(__file__))

import check_interference


def _make_site_with_stls(tmpdir, meshes):
    """Write meshes dict (filename -> trimesh.Trimesh) to tmpdir/site/."""
    import trimesh

    site_dir = os.path.join(tmpdir, "site")
    os.makedirs(site_dir, exist_ok=True)
    for name, mesh in meshes.items():
        mesh.export(os.path.join(site_dir, name))
    return site_dir


class TestNoMatingPairs(unittest.TestCase):
    """Projects without mating_pairs produce no results."""

    def test_no_mating_pairs_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a project meta.json with no mating_pairs key
            project_dir = os.path.join(tmpdir, "my-project")
            os.makedirs(project_dir)
            meta = {"description": "test"}
            with open(os.path.join(project_dir, "meta.json"), "w") as f:
                json.dump(meta, f)

            os.makedirs(os.path.join(tmpdir, "site"))
            with open(os.path.join(tmpdir, ".meta-failures"), "w") as f:
                f.write("")

            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with unittest.mock.patch.dict(os.environ, {"GITHUB_OUTPUT": os.devnull}):
                    check_interference.main()
            finally:
                os.chdir(orig_cwd)

            interference_json = os.path.join(tmpdir, "site", "interference.json")
            self.assertTrue(os.path.isfile(interference_json))
            with open(interference_json) as f:
                results = json.load(f)
            self.assertEqual(results, [])


class TestMissingStlSkipped(unittest.TestCase):
    """A pair referencing a missing STL is skipped gracefully."""

    def test_missing_stl_returns_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = os.path.join(tmpdir, "site")
            os.makedirs(site_dir)
            result = check_interference.check_pair(
                "test-project", "nonexistent_a.stl", "nonexistent_b.stl",
                site_dir=site_dir,
            )
            self.assertTrue(result["skipped"])
            self.assertTrue(result["passed"])
            self.assertIn("not found", result["error"])


class TestNonOverlappingCubes(unittest.TestCase):
    """Two cubes placed far apart have zero intersection volume."""

    def test_non_overlapping(self):
        import numpy as np
        import trimesh
        import trimesh.creation

        cube_a = trimesh.creation.box(extents=[10, 10, 10])
        cube_b = trimesh.creation.box(extents=[10, 10, 10])
        # Translate b 50 mm away — no overlap
        cube_b.apply_translation([50, 0, 0])

        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = _make_site_with_stls(tmpdir, {
                "part_a.stl": cube_a,
                "part_b.stl": cube_b,
            })
            result = check_interference.check_pair(
                "test-project", "part_a.stl", "part_b.stl", site_dir=site_dir
            )
            self.assertTrue(result["passed"])
            self.assertIsNotNone(result["overlap_volume_mm3"])
            self.assertLessEqual(
                result["overlap_volume_mm3"], check_interference.THRESHOLD_MM3
            )


class TestOverlappingCubes(unittest.TestCase):
    """Two overlapping cubes produce an intersection volume exceeding the threshold."""

    def test_overlapping(self):
        import trimesh.creation

        cube_a = trimesh.creation.box(extents=[10, 10, 10])
        cube_b = trimesh.creation.box(extents=[10, 10, 10])
        # Offset by 5 mm — 50% overlap in X, so intersection is 5×10×10 = 500 mm³
        cube_b.apply_translation([5, 0, 0])

        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = _make_site_with_stls(tmpdir, {
                "male.stl": cube_a,
                "female.stl": cube_b,
            })
            result = check_interference.check_pair(
                "test-project", "male.stl", "female.stl", site_dir=site_dir
            )
            self.assertFalse(result["passed"])
            self.assertGreater(
                result["overlap_volume_mm3"], check_interference.THRESHOLD_MM3
            )


class TestIdenticalMeshes(unittest.TestCase):
    """Using the same mesh twice produces full-volume overlap — fails."""

    def test_identical(self):
        import trimesh.creation

        cube = trimesh.creation.box(extents=[10, 10, 10])

        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = _make_site_with_stls(tmpdir, {
                "partX.stl": cube,
            })
            # Copy the same STL to a second name
            import shutil
            shutil.copy(
                os.path.join(site_dir, "partX.stl"),
                os.path.join(site_dir, "partY.stl"),
            )
            result = check_interference.check_pair(
                "test-project", "partX.stl", "partY.stl", site_dir=site_dir
            )
            self.assertFalse(result["passed"])
            # Intersection of identical 10^3 cube = 1000 mm³
            self.assertGreater(result["overlap_volume_mm3"], 100)


class TestNonManifoldMeshSkipped(unittest.TestCase):
    """A pair where one mesh is non-manifold is skipped, not failed.

    This test guards against regressions if the manifold3d error string changes:
    a broken string match would promote a SKIP to a FAIL, blocking the build.
    The version pin 'manifold3d>=2.3,<4' in .github/workflows/build.yml is the
    other half of this guard — see check_interference.py for the note.
    """

    def test_non_manifold_returns_skipped(self):
        import trimesh.creation

        cube_a = trimesh.creation.box(extents=[10, 10, 10])
        cube_b = trimesh.creation.box(extents=[10, 10, 10])

        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = _make_site_with_stls(tmpdir, {
                "good.stl": cube_a,
                "also_good.stl": cube_b,
            })
            # Mock the Boolean call to raise the manifold3d "not a volume" error.
            # This directly exercises the string-match skip branch regardless of
            # mesh content or trimesh version — the actual regression risk is that
            # the error string changes and the skip becomes a fail.
            with unittest.mock.patch(
                "trimesh.boolean.intersection",
                side_effect=Exception("not all meshes are volumes"),
            ):
                result = check_interference.check_pair(
                    "test-project", "good.stl", "also_good.stl", site_dir=site_dir
                )
            self.assertTrue(result["skipped"], msg="non-manifold pair should be skipped")
            self.assertTrue(result["passed"], msg="skipped pair should not count as failure")
            self.assertIn("error", result)


class TestMetaFailuresSkipped(unittest.TestCase):
    """Projects listed in .meta-failures are not checked."""

    def test_skipped_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a fake .meta-failures file
            failures_path = os.path.join(tmpdir, ".meta-failures")
            with open(failures_path, "w") as f:
                f.write("bad-project/meta.json\n")

            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                failed = check_interference.load_meta_failures()
                self.assertIn("bad-project/meta.json", failed)
            finally:
                os.chdir(orig_cwd)


class TestMainWritesJsonAndOutput(unittest.TestCase):
    """main() writes site/interference.json with correct structure."""

    def test_main_writes_results(self):
        import trimesh.creation

        cube_a = trimesh.creation.box(extents=[10, 10, 10])
        cube_b = trimesh.creation.box(extents=[10, 10, 10])
        cube_b.apply_translation([50, 0, 0])  # no overlap

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up project structure
            project_dir = os.path.join(tmpdir, "my-project")
            os.makedirs(project_dir)
            meta = {
                "description": "test",
                "mating_pairs": [["part_a.stl", "part_b.stl"]],
            }
            with open(os.path.join(project_dir, "meta.json"), "w") as f:
                json.dump(meta, f)

            site_dir = os.path.join(tmpdir, "site")
            os.makedirs(site_dir)
            cube_a.export(os.path.join(site_dir, "part_a.stl"))
            cube_b.export(os.path.join(site_dir, "part_b.stl"))

            # Write empty .meta-failures
            with open(os.path.join(tmpdir, ".meta-failures"), "w") as f:
                f.write("")

            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Suppress GITHUB_OUTPUT writing
                with unittest.mock.patch.dict(os.environ, {"GITHUB_OUTPUT": os.devnull}):
                    check_interference.main()
            except SystemExit:
                pass
            finally:
                os.chdir(orig_cwd)

            interference_json = os.path.join(site_dir, "interference.json")
            self.assertTrue(os.path.isfile(interference_json))
            with open(interference_json) as f:
                results = json.load(f)
            self.assertEqual(len(results), 1)
            r = results[0]
            self.assertIn("part_a", r)
            self.assertIn("part_b", r)
            self.assertIn("overlap_volume_mm3", r)
            self.assertIn("passed", r)
            self.assertTrue(r["passed"])


if __name__ == "__main__":
    unittest.main()
