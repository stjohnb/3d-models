"""Unit tests for scan_reference.py.

Exercises the reference-mesh construction against synthetic meshes — no
scan hardware and no colmap/openmvs, but unlike scan_pipeline.py this needs
numpy, trimesh and trimesh's manifold boolean engine directly rather than
via stubs. All of them live in the flake's `default` devShell, so this runs
in CI's "Run Python unit tests for build scripts" step alongside the other
scripts/test_*.py modules.
"""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_reference import (
    axis_vector,
    build_reference,
    convex_hull_reference,
    install_reference,
    principal_axis,
    safe_name,
    sanitised_report,
    slab_hull_reference,
    tightness,
    write_reference,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def open_shell(mesh):
    """Drop one face, turning a closed solid into the open shell a scan is."""
    keep = [True] * len(mesh.faces)
    keep[0] = False
    mesh.update_faces(keep)
    mesh.remove_unreferenced_vertices()
    return mesh


def dense_box(extents, z):
    """A box whose vertices are spread along Z, as a scan's would be.

    Subdivision matters: an undivided box has vertices only on its two end
    planes, so most slabs would see a single coplanar ring of points and
    Qhull would reject every one of them.
    """
    import trimesh

    box = trimesh.creation.box(extents=extents)
    for _ in range(3):
        box = box.subdivide()
    box.apply_translation([0, 0, z])
    return box


def waisted_shell():
    """Two boxes with a narrow neck between them — concave in the middle."""
    import trimesh

    parts = [
        dense_box([10, 10, 4], 2),
        dense_box([3, 3, 4], 6),
        dense_box([10, 10, 4], 10),
    ]
    return open_shell(trimesh.util.concatenate(parts))


def peanut_shell():
    """Two lobes joined by a thin neck, lying along X — concave along X, not Z.

    Stands in for a scanned object lying flat on the platter: the shape it
    varies along (X here) is horizontal, not the scan's up axis (issue #487).
    """
    import numpy
    import trimesh

    lobe_a = trimesh.creation.icosphere(subdivisions=2, radius=5.0)
    lobe_b = trimesh.creation.icosphere(subdivisions=2, radius=5.0)
    lobe_b.apply_translation([15, 0, 0])
    neck = trimesh.creation.cylinder(radius=1.5, height=15, sections=24)
    neck.apply_transform(trimesh.transformations.rotation_matrix(
        numpy.pi / 2, [0, 1, 0]
    ))
    neck.apply_translation([7.5, 0, 0])
    solid = trimesh.boolean.union([lobe_a, lobe_b, neck], engine="manifold")
    return open_shell(solid)


class ConvexHullTests(unittest.TestCase):
    def test_hull_of_an_open_shell_is_watertight(self):
        import trimesh

        shell = open_shell(trimesh.creation.box(extents=[10, 10, 10]))
        self.assertFalse(shell.is_watertight)
        hull = convex_hull_reference(shell)
        self.assertTrue(hull.is_watertight)
        self.assertTrue(hull.is_volume)


class PrincipalAxisTests(unittest.TestCase):
    def test_finds_the_long_axis_of_a_lying_bar(self):
        import trimesh

        box = trimesh.creation.box(extents=[60, 8, 8])
        for _ in range(2):
            box = box.subdivide()
        axis = principal_axis(box)
        self.assertGreater(abs(axis[0]), 0.99)

    def test_sign_is_pinned_regardless_of_eighs_raw_sign(self):
        """numpy.linalg.eigh's sign is arbitrary (LAPACK/version dependent),
        not just non-deterministic within one process — calling it twice on
        the same matrix in the same run always agrees. Pin the sign
        explicitly so the committed mesh doesn't flip across runs or numpy
        versions (#487)."""
        import numpy
        import trimesh

        box = trimesh.creation.box(extents=[60, 8, 8])
        for _ in range(2):
            box = box.subdivide()

        real_eigh = numpy.linalg.eigh

        def flipped_eigh(matrix, sign):
            values, vectors = real_eigh(matrix)
            vectors = vectors.copy()
            vectors[:, -1] *= sign
            return values, vectors

        with mock.patch("numpy.linalg.eigh", side_effect=lambda m: flipped_eigh(m, 1.0)):
            positive = principal_axis(box)
        with mock.patch("numpy.linalg.eigh", side_effect=lambda m: flipped_eigh(m, -1.0)):
            negative = principal_axis(box)

        self.assertEqual(list(positive), list(negative))
        self.assertGreater(positive[int(numpy.abs(positive).argmax())], 0)


class SlabHullTests(unittest.TestCase):
    def test_slab_hull_is_watertight_and_keeps_the_waist(self):
        mesh = waisted_shell()
        self.assertFalse(mesh.is_watertight)
        result = slab_hull_reference(mesh, slabs=6)
        self.assertTrue(result.is_watertight)
        self.assertTrue(result.is_volume)
        self.assertLess(result.volume, convex_hull_reference(mesh).volume * 0.95)

    def test_slabs_along_x_keep_a_horizontal_waist(self):
        mesh = peanut_shell()
        hull_volume = convex_hull_reference(mesh).volume

        # Old behaviour: Z-only slabs cannot see a waist that varies along X.
        z_result = slab_hull_reference(mesh, slabs=6)
        self.assertGreaterEqual(z_result.volume, 0.9 * hull_volume)

        # Fix: slabbing along X recovers the waist.
        x_result = slab_hull_reference(mesh, slabs=6, axis=[1, 0, 0])
        self.assertTrue(x_result.is_watertight)
        self.assertTrue(x_result.is_volume)
        self.assertLess(x_result.volume, 0.5 * hull_volume)

    def test_zero_z_extent_raises(self):
        import trimesh

        flat = trimesh.Trimesh(
            vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]]
        )
        with self.assertRaises(ValueError):
            slab_hull_reference(flat)


class AxisVectorTests(unittest.TestCase):
    def test_named_axis_returns_the_unit_vector(self):
        import trimesh

        box = trimesh.creation.box()
        self.assertEqual(list(axis_vector(box, "z")), [0.0, 0.0, 1.0])

    def test_unknown_axis_raises(self):
        import trimesh

        box = trimesh.creation.box()
        with self.assertRaises(ValueError):
            axis_vector(box, "bogus")


class TightnessTests(unittest.TestCase):
    def test_hull_is_one(self):
        shell = waisted_shell()
        hull = convex_hull_reference(shell)
        ratio, _hull_volume = tightness(hull, shell)
        self.assertAlmostEqual(ratio, 1.0, places=3)


class BuildReferenceTests(unittest.TestCase):
    def test_unknown_mode_raises(self):
        import trimesh

        with self.assertRaises(ValueError):
            build_reference(trimesh.creation.box(), mode="bogus")


class SafeNameTests(unittest.TestCase):
    def test_accepts_the_ci_charset(self):
        self.assertEqual(safe_name("tube 1.0-a_b"), "tube 1.0-a_b")

    def test_rejects_everything_else(self):
        for name in ("", ".", "..", "a/b", "tübe", "a*b"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    safe_name(name)


class WriteReferenceTests(unittest.TestCase):
    def test_over_budget_raises_and_removes_the_file(self):
        import trimesh

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "out" / "box-reference.stl"
            with self.assertRaises(ValueError):
                write_reference(trimesh.creation.box(), path, max_bytes=100)
            self.assertFalse(path.exists())

    def test_within_budget_writes_the_stl(self):
        import trimesh

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "out" / "box-reference.stl"
            write_reference(trimesh.creation.box(), path)
            self.assertGreater(path.stat().st_size, 0)
            self.assertFalse(path.with_suffix(".ply").exists())


class SanitisedReportTests(unittest.TestCase):
    def test_video_path_is_reduced_to_a_basename(self):
        report = sanitised_report(
            {"video": "/home/someone/captures/IMG_3826.MOV", "mm_per_unit": 2.0},
            {"mode": "hull"},
        )
        self.assertEqual(report["video"], "IMG_3826.MOV")
        self.assertEqual(report["mm_per_unit"], 2.0)
        self.assertEqual(report["reference"]["mode"], "hull")


class InstallReferenceTests(unittest.TestCase):
    def test_installs_both_files_and_refuses_to_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = pathlib.Path(tmp) / "tube-reference.stl"
            source.write_bytes(b"solid\n")
            root = pathlib.Path(tmp) / "repo"

            stl_dest, report_dest = install_reference(
                source, {"video": "IMG_3826.MOV"}, "tube", root
            )
            self.assertEqual(stl_dest, root / "scans" / "tube" / "tube-reference.stl")
            self.assertEqual(report_dest, root / "scans" / "tube" / "scan-report.json")
            self.assertEqual(stl_dest.read_bytes(), b"solid\n")
            self.assertEqual(
                json.loads(report_dest.read_text()), {"video": "IMG_3826.MOV"}
            )

            with self.assertRaises(ValueError):
                install_reference(source, {}, "tube", root)

            install_reference(source, {"video": "IMG_3827.MOV"}, "tube", root, force=True)
            self.assertEqual(
                json.loads(report_dest.read_text()), {"video": "IMG_3827.MOV"}
            )


class GitignoreCarveOutTests(unittest.TestCase):
    """Reference meshes are committed input data; the negation must follow *.stl."""

    def test_carve_out_follows_the_stl_ignore(self):
        lines = (REPO_ROOT / ".gitignore").read_text().splitlines()
        self.assertIn("*.stl", lines)
        self.assertIn("!scans/**/*.stl", lines)
        self.assertLess(lines.index("*.stl"), lines.index("!scans/**/*.stl"))


if __name__ == "__main__":
    unittest.main()
