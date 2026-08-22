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

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_reference import (
    build_reference,
    convex_hull_reference,
    install_reference,
    safe_name,
    sanitised_report,
    slab_hull_reference,
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


class ConvexHullTests(unittest.TestCase):
    def test_hull_of_an_open_shell_is_watertight(self):
        import trimesh

        shell = open_shell(trimesh.creation.box(extents=[10, 10, 10]))
        self.assertFalse(shell.is_watertight)
        hull = convex_hull_reference(shell)
        self.assertTrue(hull.is_watertight)
        self.assertTrue(hull.is_volume)


class SlabHullTests(unittest.TestCase):
    def test_slab_hull_is_watertight_and_keeps_the_waist(self):
        mesh = waisted_shell()
        self.assertFalse(mesh.is_watertight)
        result = slab_hull_reference(mesh, slabs=6)
        self.assertTrue(result.is_watertight)
        self.assertTrue(result.is_volume)
        self.assertLess(result.volume, convex_hull_reference(mesh).volume * 0.95)

    def test_zero_z_extent_raises(self):
        import trimesh

        flat = trimesh.Trimesh(
            vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]]
        )
        with self.assertRaises(ValueError):
            slab_hull_reference(flat)


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
