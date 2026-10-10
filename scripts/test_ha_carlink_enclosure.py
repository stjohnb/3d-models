"""Pins the ha-carlink-enclosure customizer manifests and library against
the issue's requirement numbers.

Run with: python3 -m unittest test_ha_carlink_enclosure
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "ha-carlink-enclosure"
LIBRARY = PROJECT_DIR / "_ha_carlink_enclosure.scad"
MANIFESTS = (
    PROJECT_DIR / "carlink_enclosure_base.parameters.json",
    PROJECT_DIR / "carlink_enclosure_lid.parameters.json",
)
SHARED_PARAMS = ("wall", "floor_t", "corner_r", "standoff_h", "cell_d", "cell_l")


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


class HaCarlinkEnclosureManifestTests(unittest.TestCase):
    def test_manifests_match_the_library(self):
        for path in MANIFESTS:
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                with self.subTest(manifest=path.name, name=entry["name"]):
                    value = scad_value(entry["name"])
                    if entry["type"] == "boolean":
                        self.assertEqual(value, str(entry["default"]).lower())
                    else:
                        self.assertAlmostEqual(float(value), entry["default"])
                        self.assertLessEqual(entry["min"], entry["default"])
                        self.assertLessEqual(entry["default"], entry["max"])

    def test_manifests_share_the_board_parameters(self):
        names = [
            {e["name"] for e in json.loads(p.read_text(encoding="utf-8"))["parameters"]}
            for p in MANIFESTS
        ]
        for name in SHARED_PARAMS:
            for manifest in names:
                self.assertIn(name, manifest)


class HaCarlinkEnclosureRequirementTests(unittest.TestCase):
    """Pins the board figures from the issue and electronics' docs/ha-carlink/PCB.md."""

    def test_board_outline(self):
        self.assertEqual(scad_number("pcb_l"), 100)
        self.assertEqual(scad_number("pcb_w"), 70)
        self.assertEqual(scad_number("pcb_t"), 1.6)

    def test_mounting_holes(self):
        # pcb_holes is OpenSCAD vector syntax, not JSON; parse the four pairs directly.
        match = re.search(r"pcb_holes\s*=\s*\[(.*?)\];", source(), re.S)
        self.assertIsNotNone(match)
        pairs = re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", match.group(1))
        points = [(float(x), float(y)) for x, y in pairs]
        for expected in [(4, 4), (96, 4), (4, 66), (96, 66)]:
            self.assertIn(expected, points)

    def test_clearances(self):
        self.assertEqual(scad_number("above_pcb"), 22)
        self.assertEqual(scad_number("below_pcb"), 3)
        self.assertGreaterEqual(scad_number("standoff_h"), scad_number("below_pcb"))
        self.assertLessEqual(scad_number("standoff_d"), 7)

    def test_connector_positions(self):
        self.assertEqual(scad_number("usb_by"), 22.7)
        self.assertEqual(scad_number("obd_by0"), 27)
        self.assertEqual(scad_number("obd_by1"), 53)
        self.assertEqual(scad_number("jst_bx"), 53)

    def test_cell_pocket(self):
        self.assertGreaterEqual(scad_number("cell_d"), 14)
        self.assertGreaterEqual(scad_number("cell_l"), 50)


if __name__ == "__main__":
    unittest.main()
