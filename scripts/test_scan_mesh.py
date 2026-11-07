"""Unit tests for scan_mesh.py.

Exercises the pure geometry-fitting functions against synthetic point
clouds — no colmap/openmvs/ffmpeg invocation and no scan hardware, so
unlike scan_pipeline.py this needs numpy and trimesh directly rather than
via stubs. Both now live in the flake's `default` devShell (issue #423),
so this runs in CI's "Run Python unit tests for build scripts" step
alongside the other scripts/test_*.py modules.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_mesh import (
    crop_reasons,
    crop_to_object,
    fit_plane_ransac,
    fit_platter,
    keep_largest_components,
    platter_frame,
)


def plane_with_outliers(seed=7):
    """A z=0 plane of 900 points plus 100 scattered outliers."""
    import numpy

    rng = numpy.random.default_rng(seed)
    inliers = numpy.column_stack([
        rng.uniform(-1, 1, 900),
        rng.uniform(-1, 1, 900),
        numpy.zeros(900),
    ])
    outliers = rng.uniform(-1, 1, (100, 3))
    outliers[:, 2] = rng.uniform(0.3, 1.0, 100)
    return numpy.vstack([inliers, outliers])


def punched_disc(seed=11):
    """A unit-radius disc of surface points with 30% of its rim ring missing.

    The gap stands in for a hand across the platter: the rim is where the
    radius estimate comes from, and it is exactly what gets occluded.
    """
    import numpy

    rng = numpy.random.default_rng(seed)
    # sqrt makes the sample uniform over area rather than over radius.
    radius = numpy.sqrt(rng.uniform(0, 1, 4000))
    theta = rng.uniform(0, 2 * numpy.pi, 4000)
    keep = ~((radius > 0.9) & (theta < 0.3 * 2 * numpy.pi))
    radius, theta = radius[keep], theta[keep]
    return numpy.column_stack([
        radius * numpy.cos(theta),
        radius * numpy.sin(theta),
        numpy.zeros(len(radius)),
    ])


class FitPlaneTests(unittest.TestCase):
    def test_recovers_the_plane_normal(self):
        _, normal, mask = fit_plane_ransac(plane_with_outliers())
        self.assertAlmostEqual(abs(float(normal[2])), 1.0, places=3)
        self.assertGreaterEqual(int(mask.sum()), 900)

    def test_is_deterministic_across_runs(self):
        import numpy

        # An unseeded fit would make the exported scale differ between runs
        # over the same capture.
        points = plane_with_outliers()
        first = fit_plane_ransac(points, seed=0)
        second = fit_plane_ransac(points, seed=0)
        for a, b in zip(first, second):
            numpy.testing.assert_array_equal(a, b)


class FitPlatterTests(unittest.TestCase):
    def test_radius_survives_a_missing_sector(self):
        import numpy

        points = punched_disc()
        plane = fit_plane_ransac(points)
        centre, radius = fit_platter(points, plane)
        # The 97.5th percentile deliberately trims a little off the true rim in
        # exchange for ignoring stray points beyond it, so this is ~1-4% low.
        self.assertAlmostEqual(radius, 1.0, delta=0.05)
        self.assertLess(float(numpy.linalg.norm(centre[:2])), 0.1)

    def test_platter_frame_sets_millimetre_scale(self):
        import numpy

        frame = platter_frame(punched_disc(), platter_diameter=222.0)
        self.assertAlmostEqual(frame["mm_per_unit"], 111.0, delta=6.0)
        self.assertAlmostEqual(frame["radius_units"], 1.0, delta=0.05)
        numpy.testing.assert_allclose(
            frame["rotation"] @ frame["rotation"].T, numpy.eye(3), atol=1e-9
        )


class CropTests(unittest.TestCase):
    def test_drops_geometry_below_the_platter(self):
        import trimesh

        keep = trimesh.creation.box(extents=(10, 10, 10))
        keep.apply_translation([0, 0, 10])
        drop = trimesh.creation.box(extents=(10, 10, 10))
        drop.apply_translation([0, 0, -5])
        mesh = trimesh.util.concatenate([keep, drop])

        cropped = crop_to_object(mesh, z_min=1.0, z_max=200.0, r_max=108.0)
        self.assertGreater(float(cropped.bounds[0][2]), 0.0)
        self.assertAlmostEqual(float(cropped.bounds[1][2]), 15.0, places=3)

    def test_drops_geometry_beyond_the_rim(self):
        import trimesh

        mesh = trimesh.creation.box(extents=(10, 10, 10))
        mesh.apply_translation([200, 0, 10])
        cropped = crop_to_object(mesh)
        self.assertEqual(len(cropped.faces), 0)


class CropReasonsTests(unittest.TestCase):
    def test_counts_agree_with_the_crop(self):
        import trimesh

        keep = trimesh.creation.box(extents=(10, 10, 10))
        keep.apply_translation([0, 0, 10])
        drop = trimesh.creation.box(extents=(10, 10, 10))
        drop.apply_translation([0, 0, -5])
        mesh = trimesh.util.concatenate([keep, drop])

        reasons = crop_reasons(mesh, z_min=1.0, z_max=200.0, r_max=72.0)
        cropped = crop_to_object(mesh.copy(), z_min=1.0, z_max=200.0, r_max=72.0)
        self.assertEqual(reasons["kept"], len(cropped.faces))

    def test_radial_clip_is_reported(self):
        import trimesh

        mesh = trimesh.creation.box(extents=(10, 10, 10))
        mesh.apply_translation([100, 0, 10])

        reasons = crop_reasons(mesh, z_min=1.0, z_max=200.0, r_max=72.0)
        self.assertEqual(reasons["dropped_beyond_r_max"], reasons["faces"])
        self.assertEqual(reasons["kept"], 0)


class ComponentTests(unittest.TestCase):
    def test_keeps_only_the_largest_component(self):
        import trimesh

        big = trimesh.creation.box(extents=(20, 20, 20))
        satellite = trimesh.creation.box(extents=(1, 1, 1))
        satellite.apply_translation([50, 0, 0])
        mesh = trimesh.util.concatenate([big, satellite])

        kept = keep_largest_components(mesh, count=1)
        self.assertAlmostEqual(float(kept.area), float(big.area), places=3)

    def test_empty_mesh_raises(self):
        import numpy
        import trimesh

        empty = trimesh.Trimesh(vertices=numpy.zeros((0, 3)), faces=numpy.zeros((0, 3), int))
        with self.assertRaises(ValueError):
            keep_largest_components(empty)


if __name__ == "__main__":
    unittest.main()
