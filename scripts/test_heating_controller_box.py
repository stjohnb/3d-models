"""Pins the heating-controller-box fixing and cut-out decisions.

Every fixing is an M3 heat-set insert pocket cut by one module (no standoffs,
no self-tap pilots by default), the toggle hole matches the XT-13A legend
plate, both customizer manifests agree with the library's defaults, and
every corner of their ranges passes the library's asserts.

Run with: python3 -m unittest test_heating_controller_box
"""

import itertools
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "heating-controller-box"
LIBRARY = PROJECT_DIR / "_heating_controller_box.scad"
MANIFESTS = (
    PROJECT_DIR / "heating_controller_base.parameters.json",
    PROJECT_DIR / "heating_controller_lid.parameters.json",
)


def source():
    return LIBRARY.read_text(encoding="utf-8")


def scad_value(name):
    match = re.search(rf"^{name}\s*=\s*([^;]+);", source(), re.M)
    if match is None:
        raise AssertionError(f"{name} not found in {LIBRARY.name}")
    return match.group(1).strip()


def scad_number(name):
    return float(scad_value(name))


def strip_comments(text):
    return re.sub(r"//[^\n]*", "", text)


def to_python(expr):
    expr = expr.replace("&&", " and ").replace("||", " or ")
    expr = re.sub(r"!(?!=)", " not ", expr)
    expr = re.sub(r"\btrue\b", "True", expr)
    return re.sub(r"\bfalse\b", "False", expr)


def library_program():
    """Top-level assignments and assert conditions, compiled as Python."""
    text = strip_comments(source())
    assignments = [
        (name, compile(to_python(expr), name, "eval"))
        for name, expr in re.findall(r"^([A-Za-z_]\w*)\s*=\s*([^;]+);", text, re.M)
    ]
    asserts = [
        (message, compile(f"({to_python(cond)})", message, "eval"))
        for cond, message in re.findall(
            r'^assert\((.*?),\s*"([^"]*)"\);', text, re.M | re.S
        )
    ]
    return assignments, asserts


def failed_asserts(program, overrides):
    """Evaluates like openscad -D: an override replaces its assignment."""
    assignments, asserts = program
    env = {"min": min, "max": max}
    for name, code in assignments:
        env[name] = overrides[name] if name in overrides else eval(code, env)
    return [message for message, code in asserts if not eval(code, env)]


class HeatingControllerBoxTests(unittest.TestCase):
    def test_insert_pockets(self):
        self.assertEqual(scad_number("insert_hole_d"), 4.0)
        self.assertEqual(scad_number("insert_depth"), 6)
        self.assertEqual(scad_number("insert_chamfer"), 0.5)
        self.assertGreaterEqual(2 * scad_number("post_r"), 8)

    def test_no_standoffs_or_self_tap_pilots(self):
        for name in ("relay_standoff", "screw_pilot", "pilot_depth"):
            self.assertNotIn(name, source())

    def test_every_fixing_uses_insert_hole(self):
        # corner posts, carrier posts, CYD bosses
        self.assertEqual(len(re.findall(r"\binsert_hole\(\w+\);", source())), 3)

    def test_toggle_cutout_is_keyed(self):
        self.assertEqual(scad_number("toggle_hole_d"), 12)
        self.assertEqual(scad_number("toggle_key_depth"), 1)
        self.assertEqual(scad_number("toggle_key_w"), 1.5)
        self.assertIn("linear_extrude(lid_t + 2) toggle_cutout();", source())
        self.assertIn("translate([-toggle_key_w/2, -toggle_hole_d/2 - 1])", source())
        self.assertNotIn("toggle_hole_d/2 - toggle_key_depth", source())

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

    def test_carrier_hangs_from_faceplate_posts(self):
        self.assertEqual(scad_number("board_w"), 97)
        self.assertEqual(scad_number("board_h"), 100)
        self.assertEqual(scad_number("board_hole_dx"), 89)
        self.assertEqual(scad_number("board_hole_dy"), 92)
        self.assertGreaterEqual(scad_number("carrier_post_d1"), 10)
        self.assertIn("carrier_positions()", source())
        self.assertIn("tie_anchor", source())
        for name in (
            "carrier_boss",
            "module partition",
            "module cradle",
            "module relay_positions",
            "wago_cx",
            "psu_cx",
            "rib_x",
        ):
            self.assertNotIn(name, source())

    def test_wiring_channel_and_faceplate_stack(self):
        self.assertGreaterEqual(scad_number("board_clear_bottom"), 20)
        self.assertGreaterEqual(scad_number("inner_d"), 72)
        self.assertGreaterEqual(
            scad_number("lid_t") + scad_number("inner_d"),
            scad_number("wiring_depth") + scad_number("wiring_clear"),
        )
        self.assertGreaterEqual(scad_number("cyd_board_clear"), 5)
        stack = (
            scad_number("cyd_boss_gap")
            + scad_number("cyd_thickness")
            + scad_number("cyd_board_clear")
            + scad_number("board_t")
            + scad_number("module_standoff_h")
            + scad_number("module_h")
        )
        self.assertGreaterEqual(
            scad_number("inner_d") - stack, scad_number("stack_floor_clear")
        )

    def test_wall_screws_and_knockout_follow_the_board(self):
        program = library_program()
        for inner_h in (132, 150):
            with self.subTest(inner_h=inner_h):
                self.assertEqual(failed_asserts(program, {"inner_h": inner_h}), [])
        # the derived positions must be what the asserts police
        self.assertIn("inner_h", scad_value("cable_floor_y"))
        self.assertIn("board_bottom", scad_value("tie_anchor_y"))
        self.assertIn("channel_y", scad_value("mount_holes"))
        self.assertIn("top_screw_y", scad_value("mount_holes"))
        # a channel too narrow for the screws is caught
        failed = failed_asserts(program, {"board_clear_bottom": 8})
        self.assertTrue(any("under the board" in m for m in failed))

    def test_cables_enter_from_below(self):
        self.assertEqual(scad_value("cable_wall"), "true")
        self.assertEqual(scad_value("cable_floor"), "false")
        self.assertGreaterEqual(
            scad_number("cable_w"),
            2 * scad_number("tie_anchor_w") + scad_number("tie_anchor_gap"),
        )
        src = source()
        self.assertIn("translate([cable_x, -inner_h/2 + 1, floor_t])", src)
        self.assertIn("cube([tie_anchor_w + 2, tie_w + 0.6, tie_slot_h])", src)

    def test_vents_are_offset_by_the_floor(self):
        self.assertIn("floor_t + (vent_z0 + vent_z1)/2", source())
        self.assertIn("inner_d", scad_value("vent_z1"))

    def test_library_parser_sees_the_asserts(self):
        assignments, asserts = library_program()
        self.assertGreater(len(asserts), 30)
        self.assertEqual(failed_asserts((assignments, asserts), {}), [])

    def test_manifest_range_corners_pass_the_asserts(self):
        # Every combination of up to three parameters at their range ends
        program = library_program()
        for path in MANIFESTS:
            ends = []
            for entry in json.loads(path.read_text(encoding="utf-8"))["parameters"]:
                if entry["type"] == "boolean":
                    values = (False, True)
                else:
                    values = (entry["min"], entry["max"])
                ends.append([(entry["name"], v) for v in values])
            for group in itertools.combinations(ends, 3):
                for combo in itertools.product(*group):
                    failures = failed_asserts(program, dict(combo))
                    self.assertEqual(failures, [], f"{path.name}: {dict(combo)}")

    def test_manifests_share_the_enclosure_size(self):
        names = [
            {e["name"] for e in json.loads(p.read_text(encoding="utf-8"))["parameters"]}
            for p in MANIFESTS
        ]
        for name in ("inner_w", "inner_h", "wall"):
            for manifest in names:
                self.assertIn(name, manifest)


if __name__ == "__main__":
    unittest.main()
