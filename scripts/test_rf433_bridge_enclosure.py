"""Pins the rf433-bridge-enclosure customizer manifests and library against
the issue's requirement numbers.

Run with: python3 -m unittest test_rf433_bridge_enclosure
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "rf433-bridge-enclosure"
LIBRARY = PROJECT_DIR / "_rf433_bridge_enclosure.scad"
MANIFESTS = (
    PROJECT_DIR / "rf433_enclosure_base.parameters.json",
    PROJECT_DIR / "rf433_enclosure_lid.parameters.json",
)
SHARED_PARAMS = ("wall", "floor_t", "corner_r", "standoff_h", "above_pcb")


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


def scad_pair(name):
    match = re.search(rf"^{name}\s*=\s*\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return [float(match.group(1)), float(match.group(2))]


class Rf433EnclosureManifestTests(unittest.TestCase):
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

    def test_shared_parameters_are_identical(self):
        entries = [
            {e["name"]: e for e in json.loads(p.read_text(encoding="utf-8"))["parameters"]}
            for p in MANIFESTS
        ]
        for name in SHARED_PARAMS:
            self.assertEqual(entries[0][name], entries[1][name])


class Rf433EnclosureRequirementTests(unittest.TestCase):
    def test_board_outline(self):
        self.assertEqual(scad_number("pcb_l"), 62)
        self.assertEqual(scad_number("pcb_w"), 60)
        self.assertEqual(scad_number("pcb_t"), 1.6)

    def test_mounting_holes(self):
        match = re.search(r"pcb_holes\s*=\s*\[(.*?)\];", source(), re.S)
        self.assertIsNotNone(match)
        pairs = re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", match.group(1))
        points = [(float(x), float(y)) for x, y in pairs]
        for expected in [(4, 4), (58, 4), (4, 56), (58, 56)]:
            self.assertIn(expected, points)

    def test_clearances(self):
        self.assertEqual(scad_number("below_pcb"), 3)
        self.assertGreaterEqual(scad_number("standoff_h"), scad_number("below_pcb"))
        self.assertLessEqual(scad_number("standoff_d"), 7)

    def test_connector_and_antenna_positions(self):
        self.assertEqual(scad_number("usb_bx"), 22.7)
        self.assertEqual(scad_number("sma_by"), 42.81)
        self.assertEqual(scad_pair("antenna_bx"), [8, 37.5])
        self.assertEqual(scad_pair("antenna_by"), [0, 16.5])

    def test_measured_overhangs(self):
        """Caliper figures from the assembled board, 2026-11-05."""
        self.assertEqual(scad_pair("devkit_by")[1], 66.7)
        self.assertEqual(scad_number("usb_face_by"), 68.3)
        self.assertEqual(scad_pair("mod_bx")[1], 67.9)
        self.assertEqual(scad_number("sma_tip_bx"), 69.4)
        self.assertEqual(scad_number("usb_bx"), 22.7)

    def test_cavity_covers_the_overhangs(self):
        pcb_clear = scad_number("pcb_clear")
        cav_bx_hi = max(scad_number("pcb_l") + pcb_clear,
                        scad_pair("mod_bx")[1] + scad_number("mod_clear"))
        cav_by_hi = max(scad_number("pcb_w") + pcb_clear,
                        scad_number("usb_face_by") + scad_number("usb_gap"))
        self.assertGreaterEqual(cav_by_hi, 68.3 + 0.5)
        self.assertGreaterEqual(cav_bx_hi, 67.9 + 1.0)
        # the SMA jack still reaches the +X wall slot
        self.assertGreaterEqual(scad_number("sma_tip_bx"), cav_bx_hi)
        # the cavity expressions in the library match the ones checked here
        self.assertEqual(
            scad_value("cav_bx"),
            "[-pcb_clear, max(pcb_l + pcb_clear, mod_bx[1] + mod_clear)]",
        )
        self.assertEqual(
            scad_value("cav_by"),
            "[-pcb_clear, max(pcb_w + pcb_clear, usb_face_by + usb_gap)]",
        )

    def test_screw_reaches_insert(self):
        lo = scad_number("lid_t") + scad_number("above_pcb") + scad_number("pcb_t") + 4
        hi = scad_number("lid_t") + scad_number("above_pcb") + scad_number("pcb_t") \
            + scad_number("insert_depth")
        self.assertLessEqual(lo, scad_number("screw_l"))
        self.assertLessEqual(scad_number("screw_l"), hi)

    def test_manifest_ranges_keep_asserts_passing(self):
        """Worst-case customizer ranges must still satisfy the lib's layout asserts."""
        base = {e["name"]: e for e in json.loads(MANIFESTS[0].read_text(encoding="utf-8"))["parameters"]}
        lid = {e["name"]: e for e in json.loads(MANIFESTS[1].read_text(encoding="utf-8"))["parameters"]}
        devkit_top = scad_number("devkit_top")
        mod_top = scad_number("mod_top")
        above_min = base["above_pcb"]["min"]
        nut_top = base["sma_z"]["max"] + base["sma_slot_w"]["max"] / 2
        # lid lip clearance: tallest nut and lip against the smallest above_pcb
        self.assertGreater(above_min - lid["lip_d"]["max"], max(devkit_top, nut_top, mod_top) + 1)
        # USB window must stay below the lid lip at the smallest above_pcb
        self.assertLessEqual(
            base["usb_z0"]["max"] + base["usb_h"]["max"], above_min - lid["lip_d"]["max"]
        )
        # screw_l must reach the insert across the whole above_pcb / boss_extra range
        screw_l = scad_number("screw_l")
        lid_t = lid["lid_t"]["max"]
        pcb_t = scad_number("pcb_t")
        insert_depth = scad_number("insert_depth")
        self.assertGreaterEqual(screw_l, lid_t + base["above_pcb"]["max"] + pcb_t + 4)
        self.assertLessEqual(
            screw_l,
            lid["lid_t"]["min"] + above_min + lid["boss_extra"]["min"] + pcb_t + insert_depth,
        )
        # floor fixing countersink must leave floor material at the thinnest floor
        self.assertLess(scad_number("fixing_cs_h"), base["floor_t"]["min"] - 0.8)


if __name__ == "__main__":
    unittest.main()
