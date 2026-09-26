"""Tests for preview_summary.py (PR-less issue previews).

Run with: python3 -m unittest test_preview_summary
"""

import json
import pathlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import preview_summary  # noqa: E402

ISSUE = "clw_01M39H53GDR0QVMAF3WVMWQKTM"
SHA = "deadbeef"
VIEWER = f"https://www.bstjohn.net/3d-models/issue-preview/{ISSUE}/{SHA}/"


def binary_stl(triangles):
    return b"\0" * 80 + struct.pack("<I", triangles) + b"\0" * (50 * triangles)


class _SiteHarness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.site = pathlib.Path(self._tmp.name, "site")
        self.site.mkdir()
        (self.site / "shelf-bracket.png").write_bytes(b"png")
        (self.site / "shelf-bracket_top.png").write_bytes(b"png")
        (self.site / "shelf-bracket.stl").write_bytes(binary_stl(3))
        (self.site / "ascii_part.png").write_bytes(b"png")
        (self.site / "ascii_part.stl").write_bytes(b"solid x\n" * 20)
        (self.site / "models.json").write_text(json.dumps({
            "Shelf Brackets": {"dir": "shelf-brackets", "files": []},
        }))
        (self.site / "validation.json").write_text(json.dumps([
            {"name": "shelf-bracket.stl", "passed": True, "triangles": 1234,
             "volume": 10.5, "bbox_mm": {"x": 1, "y": 2, "z": 3},
             "bounds_mm": {"min_z": 0.0}, "sits_on_bed": True},
            {"name": "ascii_part.stl", "passed": False, "triangles": 7,
             "volume": -1, "bounds_mm": {"min_z": 1.5}, "sits_on_bed": False},
        ]))
        (self.site / "interference.json").write_text(json.dumps([
            {"part_a": "a.stl", "part_b": "b.stl", "passed": False,
             "overlap_volume_mm3": 2.5},
            {"part_a": "c.stl", "part_b": "d.stl", "passed": True,
             "skipped": True, "overlap_volume_mm3": None},
        ]))
        self.changed = [
            "shelf-brackets/shelf-bracket.scad",
            "misc/ascii_part.scad",
            "shelf-brackets/_lib.scad",
            "shelf-brackets/meta.json",
        ]

    def tearDown(self):
        self._tmp.cleanup()

    def summary(self, changed=None):
        return preview_summary.build_summary(
            ISSUE, SHA, "deadbeef" * 5,
            self.changed if changed is None else changed, self.site,
        )


class SummaryTests(_SiteHarness):
    def test_url_shapes(self):
        s = self.summary()
        self.assertEqual(s["viewer_url"], VIEWER)
        self.assertEqual(s["summary_url"], VIEWER + "preview-summary.json")
        urls = {m["scad"]: m["thumbnail_url"] for m in s["models"]}
        self.assertEqual(
            urls["shelf-brackets/shelf-bracket.scad"], VIEWER + "shelf-bracket.png"
        )

    def test_changed_scad_only_and_library_has_no_model(self):
        s = self.summary()
        self.assertNotIn("shelf-brackets/meta.json", s["changed_scad"])
        self.assertIn("shelf-brackets/_lib.scad", s["changed_scad"])
        self.assertEqual(
            sorted(m["scad"] for m in s["models"]),
            ["misc/ascii_part.scad", "shelf-brackets/shelf-bracket.scad"],
        )

    def test_triangle_parsing(self):
        by_scad = {m["scad"]: m for m in self.summary()["models"]}
        bracket = by_scad["shelf-brackets/shelf-bracket.scad"]
        self.assertEqual(bracket["triangles"], 3)
        self.assertEqual(bracket["stl_size_bytes"], 84 + 150)
        ascii_part = by_scad["misc/ascii_part.scad"]
        self.assertIsNone(ascii_part["triangles"])
        self.assertEqual(ascii_part["stl_size_bytes"], 160)

    def test_project_name_mapping_with_fallback(self):
        by_scad = {m["scad"]: m for m in self.summary()["models"]}
        self.assertEqual(
            by_scad["shelf-brackets/shelf-bracket.scad"]["project"], "Shelf Brackets"
        )
        self.assertEqual(by_scad["misc/ascii_part.scad"]["project"], "misc")

    def test_extra_views_only_when_present(self):
        by_scad = {m["scad"]: m for m in self.summary()["models"]}
        self.assertEqual(
            by_scad["shelf-brackets/shelf-bracket.scad"]["extra_views"],
            {"top": VIEWER + "shelf-bracket_top.png"},
        )
        self.assertEqual(by_scad["misc/ascii_part.scad"]["extra_views"], {})

    def test_validation_and_interference_copied_verbatim(self):
        s = self.summary()
        self.assertEqual(
            s["validation"], json.loads((self.site / "validation.json").read_text())
        )
        self.assertEqual(
            s["interference"], json.loads((self.site / "interference.json").read_text())
        )

    def test_missing_files_are_tolerated(self):
        for name in ("models.json", "validation.json", "interference.json",
                     "shelf-bracket.stl"):
            (self.site / name).unlink()
        s = self.summary()
        self.assertEqual(s["validation"], [])
        self.assertEqual(s["interference"], [])
        bracket = [m for m in s["models"] if m["scad"].startswith("shelf")][0]
        self.assertEqual(bracket["project"], "shelf-brackets")
        self.assertIsNone(bracket["stl_size_bytes"])
        self.assertIsNone(bracket["triangles"])

    def test_markdown_sections(self):
        md = self.summary()["markdown"]
        self.assertTrue(md.startswith("## 🔍 Model Preview\n"))
        self.assertIn(f"**[View interactive 3D models]({VIEWER})**", md)
        self.assertIn("### Shelf Brackets", md)
        self.assertIn("**shelf bracket** — 234 bytes · 3 triangles", md)
        self.assertIn("**ascii part** — 160 bytes\n", md)
        self.assertIn("### ⚠️ Mesh Validation", md)
        self.assertIn("| shelf-bracket.stl | 1 × 2 × 3 | 0.00 | 1,234 | 10.5 | ✅ Pass |", md)
        self.assertIn("| ascii_part.stl | unknown | 1.50 ⚠️ | 7 | -1 | ❌ Fail |", md)
        self.assertIn("| a.stl | b.stl | 2.5 mm³ | ❌ Fail |", md)
        self.assertIn("| c.stl | d.stl | N/A | ⏭️ Skip |", md)
        self.assertIn(f"*Preview deployed to [{VIEWER}]({VIEWER})*", md)
        self.assertNotIn("Previous builds", md)

    def test_format_size(self):
        self.assertEqual(preview_summary.format_size(512), "512 bytes")
        self.assertEqual(preview_summary.format_size(2048), "2.0 KB")
        self.assertEqual(preview_summary.format_size(3 * 1048576), "3.0 MB")


class CliTests(_SiteHarness):
    def test_writes_json_and_optional_markdown(self):
        out = pathlib.Path(self._tmp.name, "preview-summary.json")
        md = pathlib.Path(self._tmp.name, "step-summary.md")
        rc = preview_summary.main([
            "--issue", ISSUE, "--sha", SHA, "--commit", "c" * 40,
            "--site", str(self.site), "--out", str(out),
            "--markdown-out", str(md),
            "--changed", "shelf-brackets/shelf-bracket.scad",
        ])
        self.assertEqual(rc, 0)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(data),
            sorted(["issue", "sha", "commit", "viewer_url", "summary_url",
                    "changed_scad", "models", "validation", "interference",
                    "markdown"]),
        )
        self.assertEqual(md.read_text(encoding="utf-8"), data["markdown"])

    def test_empty_markdown_out_is_skipped(self):
        out = pathlib.Path(self._tmp.name, "preview-summary.json")
        rc = preview_summary.main([
            "--issue", "518", "--sha", SHA, "--commit", "c" * 40,
            "--site", str(self.site), "--out", str(out), "--markdown-out", "",
            "--changed", "misc/ascii_part.scad",
        ])
        self.assertEqual(rc, 0)
        self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
