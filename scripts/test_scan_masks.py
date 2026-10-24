"""Unit tests for scan_masks.py.

The pure helpers (parse_ellipse, mask_filename) have no third-party
dependencies and run in CI's default devShell. MaskGeometryTests needs
opencv4, which lives in the `scan` devShell rather than `default`, so it
self-skips unless `cv2` is importable — run those with:

    nix develop .#scan --command python3 -m unittest scripts/test_scan_masks.py
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_masks import column_mask, mask_filename, parse_ellipse, platter_mask

try:
    import cv2  # noqa: F401
    _HAVE_CV2 = True
except ImportError:  # opencv4 lives in the `scan` devShell, not `default`
    _HAVE_CV2 = False


class ParseEllipseTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(parse_ellipse("540,1420,470,150"), (540.0, 1420.0, 470.0, 150.0))
        self.assertEqual(parse_ellipse("1.5,2.5,3.5,4.5"), (1.5, 2.5, 3.5, 4.5))

    def test_wrong_arity_raises(self):
        for text in ("540,1420,470", "540,1420,470,150,9", ""):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_ellipse(text)

    def test_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            parse_ellipse("540,1420,470,wide")

    def test_non_positive_radii_raise(self):
        for text in ("540,1420,0,150", "540,1420,470,-1"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_ellipse(text)


@unittest.skipUnless(_HAVE_CV2, "needs opencv4 — run inside `nix develop .#scan`")
class MaskGeometryTests(unittest.TestCase):
    SHAPE = (200, 200)
    ELLIPSE = (100.0, 150.0, 50.0, 20.0)

    def test_platter_mask_is_set_at_the_centre_and_clear_at_the_corner(self):
        mask = platter_mask(self.SHAPE, self.ELLIPSE)
        self.assertEqual(mask.dtype.name, "uint8")
        self.assertEqual(mask[150, 100], 255)
        self.assertEqual(mask[0, 0], 0)

    def test_column_mask_reaches_above_the_platter(self):
        mask = column_mask(self.SHAPE, self.ELLIPSE, 100)
        self.assertEqual(mask.dtype.name, "uint8")
        # 90 px above the platter centre, still inside the swept column.
        self.assertEqual(mask[60, 100], 255)
        # Well outside the ellipse horizontally.
        self.assertEqual(mask[10, 10], 0)

    def test_column_mask_contains_the_platter(self):
        platter = platter_mask(self.SHAPE, self.ELLIPSE)
        column = column_mask(self.SHAPE, self.ELLIPSE, 100)
        import numpy

        self.assertTrue(numpy.all(column[platter > 0] == 255))


class MaskFilenameTests(unittest.TestCase):
    def test_colmap_convention_appends_png(self):
        self.assertEqual(mask_filename("000001.jpg"), "000001.jpg.png")


if __name__ == "__main__":
    unittest.main()
