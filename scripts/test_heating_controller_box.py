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
        # corner posts, relay bosses, CYD bosses
        self.assertEqual(len(re.findall(r"\binsert_hole\(\w+\);", source())), 3)

    def test_toggle_cutout_is_keyed(self):
        self.assertEqual(scad_number("toggle_hole_d"), 12)
        self.assertEqual(scad_number("toggle_key_depth"), 1)
        self.assertEqual(scad_number("toggle_key_w"), 1.5)
        self.assertIn("linear_extrude(lid_t + 2) toggle_cutout();", source())

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

    def test_relay_terminals_have_wiring_room(self):
        terminal_edge = scad_number("relay_cy") - scad_number("relay_board_w") / 2
        wall = -scad_number("inner_h") / 2
        clear = scad_number("relay_terminal_clear")
        self.assertGreaterEqual(clear, 12)
        self.assertGreaterEqual(terminal_edge - wall, clear)

    def test_relay_header_clears_the_lower_toggle(self):
        header_edge = scad_number("relay_cy") + scad_number("relay_board_w") / 2
        toggle_bottom = (
            scad_number("row_cy")
            - scad_number("row_dy")
            - scad_number("toggle_body_l") / 2
        )
        clear = scad_number("relay_header_clear")
        self.assertGreaterEqual(clear, 10)
        self.assertGreaterEqual(toggle_bottom - header_edge, clear)

    def test_vents_are_offset_by_the_floor(self):
        self.assertIn("floor_t + (vent_z0 + vent_z1)/2", source())

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
