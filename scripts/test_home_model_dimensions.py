"""Checks that home-model's generated house-model export is intact and unshadowed.

home-model/_house_dimensions.scad is a verbatim copy of house-model's
exports/3d-models/_house_dimensions.scad. Its first line records the sha256 of
the rest of the file; a hand edit breaks that hash. _home_model.scad includes
it and must not reassign any of its names, since an OpenSCAD reassignment
would silently override the canonical value.
"""

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "home-model" / "_house_dimensions.scad"
LIBRARY = ROOT / "home-model" / "_home_model.scad"

HEADER = re.compile(
    r"^// house-model house\.yaml sha256:[0-9a-f]{64} body sha256:(?P<body>[0-9a-f]{64})$"
)
ASSIGNMENT = re.compile(r"(?<![\w$.])([A-Za-z_]\w*)\s*=(?!=)")


def split_export(text):
    """Return (header line, body) of an export file."""
    header, sep, body = text.partition("\n")
    if not sep:
        raise ValueError("export has no body")
    return header, body


def assigned_names(scad):
    """Top-level-style assignments in SCAD source, ignoring comments."""
    scad = re.sub(r"/\*.*?\*/", "", scad, flags=re.S)
    scad = re.sub(r"//[^\n]*", "", scad)
    names = set()
    for line in scad.splitlines():
        stripped = line.strip()
        if stripped.startswith(("module ", "function ")):
            continue
        names.update(ASSIGNMENT.findall(stripped))
    return names


class TestHelpers(unittest.TestCase):
    def test_assigned_names_skips_comments_and_module_lines(self):
        src = "a = 1;  b=2; // c = 3\n/* d = 4 */\nmodule m(e = 5) {}\nf == g;\n"
        self.assertEqual(assigned_names(src), {"a", "b"})

    def test_header_rejects_tampered_body(self):
        body = "x = 1;\n"
        digest = hashlib.sha256(body.encode()).hexdigest()
        header = f"// house-model house.yaml sha256:{'0' * 64} body sha256:{digest}"
        match = HEADER.match(header)
        self.assertIsNotNone(match)
        tampered = hashlib.sha256(b"x = 2;\n").hexdigest()
        self.assertNotEqual(match["body"], tampered)


class TestHomeModelDimensions(unittest.TestCase):
    def setUp(self):
        self.export_text = EXPORT.read_text(encoding="utf-8")
        self.library_text = LIBRARY.read_text(encoding="utf-8")

    def test_body_hash_matches_header(self):
        header, body = split_export(self.export_text)
        match = HEADER.match(header)
        self.assertIsNotNone(match, f"unexpected export header: {header!r}")
        actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.assertEqual(
            match["body"],
            actual,
            "home-model/_house_dimensions.scad was edited; re-copy it verbatim "
            "from house-model exports/3d-models/_house_dimensions.scad",
        )

    def test_library_includes_export(self):
        self.assertRegex(self.library_text, r"(?m)^include <_house_dimensions\.scad>")

    def test_library_assigns_no_exported_name(self):
        exported = assigned_names(split_export(self.export_text)[1])
        self.assertIn("plot_y1", exported)
        self.assertIn("house_cuts_north", exported)
        clashes = sorted(exported & assigned_names(self.library_text))
        self.assertEqual(clashes, [], f"_home_model.scad reassigns exported names: {clashes}")


if __name__ == "__main__":
    unittest.main()
