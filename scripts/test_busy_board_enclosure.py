"""Pins the busy-board-enclosure customizer manifests and library against
the busy board's docs/busy-board/PCB.md (St-John-Software/electronics).

Run with: python3 -m unittest test_busy_board_enclosure
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "busy-board-enclosure"
LIBRARY = PROJECT_DIR / "_busy_board_enclosure.scad"
PANEL = PROJECT_DIR / "busy_board_panel.parameters.json"
TRAY = PROJECT_DIR / "busy_board_tray.parameters.json"
DOOR = PROJECT_DIR / "busy_board_battery_door.parameters.json"
MANIFESTS = (PANEL, TRAY, DOOR)
# Parameters that size more than one part, and the manifests that must expose them.
SHARED_PARAMS = {
    ("wall", "corner_r", "edge_r", "inner_d", "insert_hole_d"): (PANEL, TRAY),
    ("floor_t", "batt_l", "batt_w", "door_t", "door_clear"): (TRAY, DOOR),
    ("pcb_to_panel",): (PANEL, TRAY),
}


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


def scad_points(name):
    # OpenSCAD vector syntax, not JSON: pull every [x, y] pair.
    pairs = re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", scad_value(name))
    return [(float(x), float(y)) for x, y in pairs]


def manifest_names(path):
    return {e["name"] for e in json.loads(path.read_text(encoding="utf-8"))["parameters"]}


class BusyBoardEnclosureManifestTests(unittest.TestCase):
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

    def test_shared_parameters_are_exposed_together(self):
        for names, manifests in SHARED_PARAMS.items():
            for name in names:
                for path in manifests:
                    with self.subTest(name=name, manifest=path.name):
                        self.assertIn(name, manifest_names(path))

    def test_shared_parameters_agree(self):
        entries = {}
        for path in MANIFESTS:
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                entries.setdefault(entry["name"], []).append(entry)
        for name, found in entries.items():
            with self.subTest(name=name):
                self.assertEqual(len({(e.get("min"), e.get("max"), e["default"]) for e in found}), 1)


class BusyBoardEnclosureRequirementTests(unittest.TestCase):
    """Pins the board figures from PCB.md "Mechanical and enclosure"."""

    def test_board_outline(self):
        self.assertEqual(scad_number("pcb_l"), 100)
        self.assertEqual(scad_number("pcb_w"), 100)
        self.assertEqual(scad_number("pcb_t"), 1.6)

    def test_mounting_holes(self):
        self.assertEqual(
            sorted(scad_points("pcb_holes")),
            sorted([(5, 5), (95, 5), (5, 95), (95, 95)]),
        )
        self.assertEqual(scad_number("pcb_keepout_r"), 3.5)
        self.assertLessEqual(scad_number("boss_d"), 7)

    def test_displays(self):
        self.assertEqual(scad_points("ds1_c"), [(50, 22)])
        self.assertEqual(scad_points("ds1_body"), [(50.4, 19.0)])
        self.assertEqual(scad_points("bg_c"), [(30, 48), (70, 48)])
        self.assertEqual(scad_points("bg_body"), [(25.4, 10.2)])

    def test_ring_leds(self):
        expected = (
            [(x, 8) for x in (15, 29, 50, 71, 85)]      # D1-D5
            + [(92, y) for y in (28, 48, 68)]           # D6-D8
            + [(x, 88) for x in (85, 71, 50, 29, 15)]   # D9-D13
            + [(8, y) for y in (68, 48, 28)]            # D14-D16
        )
        self.assertEqual(scad_points("led_c"), expected)
        self.assertLess(scad_number("led_hole_d"), scad_number("led_flange_d"))
        self.assertGreater(scad_number("led_hole_d"), scad_number("led_lens_d"))

    def test_connector_and_part_heights(self):
        self.assertEqual(scad_number("jst_h"), 10)
        self.assertEqual(scad_number("jst_lead_h"), 15)
        self.assertEqual(scad_number("f1_h"), 12)
        self.assertEqual(scad_number("u1_h"), 9)
        self.assertEqual(scad_number("below_pcb"), 3)
        pcb_to_panel = scad_number("pcb_to_panel")
        self.assertGreaterEqual(pcb_to_panel, scad_number("jst_h") + 2)
        self.assertGreaterEqual(pcb_to_panel, scad_number("jst_lead_h"))

    def test_lenses_never_stand_proud(self):
        tip = scad_number("led_h") + scad_number("led_raise")
        self.assertLessEqual(tip, scad_number("pcb_to_panel") + scad_number("panel_t") - 1)


if __name__ == "__main__":
    unittest.main()
