import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import validate_stl_meshes


def admesh_output(
    *,
    facets=1234,
    unconnected=0,
    degenerate=0,
    volume="800",
    min_x="-1.5",
    max_x="8.5",
    min_y="2",
    max_y="22",
    min_z="0",
    max_z="10",
):
    return f"""
Number of facets       : {facets}
Number of unconnected facets: {unconnected}
Degenerate facets      : {degenerate}
Volume                 : {volume}
Min X = {min_x}
Max X = {max_x}
Min Y = {min_y}
Max Y = {max_y}
Min Z = {min_z}
Max Z = {max_z}
"""


def completed(stdout):
    return mock.Mock(stdout=stdout, stderr="")


class ExtractorTests(unittest.TestCase):
    def test_extractors_parse_admesh_labels(self):
        output = admesh_output(volume="1.25e+03")

        self.assertEqual(
            validate_stl_meshes.extract_int(output, r"Number of facets"), 1234
        )
        self.assertEqual(
            validate_stl_meshes.extract_int(output, r"Number of unconnected facets"),
            0,
        )
        self.assertEqual(validate_stl_meshes.extract_float(output, r"Volume"), 1250.0)
        self.assertEqual(
            validate_stl_meshes.extract_float(output, r"Min X", "="), -1.5
        )

    def test_missing_fields_return_zero(self):
        self.assertEqual(validate_stl_meshes.extract_int("", r"Number of facets"), 0)
        self.assertEqual(validate_stl_meshes.extract_float("", r"Volume"), 0.0)


class ValidateStlTests(unittest.TestCase):
    def test_validate_stl_returns_clean_mesh_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            stl = pathlib.Path(tmp) / "clean.stl"
            stl.write_text("placeholder", encoding="utf-8")

            with mock.patch("subprocess.run", return_value=completed(admesh_output())):
                result = validate_stl_meshes.validate_stl(stl)

        self.assertTrue(result["passed"])
        self.assertEqual(result["triangles"], 1234)
        self.assertEqual(result["volume"], 800)
        self.assertEqual(result["bbox_mm"], {"x": 10.0, "y": 20.0, "z": 10.0})
        self.assertEqual(
            result["bounds_mm"],
            {
                "min_x": -1.5,
                "max_x": 8.5,
                "min_y": 2.0,
                "max_y": 22.0,
                "min_z": 0.0,
                "max_z": 10.0,
            },
        )
        self.assertTrue(result["sits_on_bed"])
        self.assertEqual(result["estimated_minutes"], 3)

    def test_unconnected_facets_fail_but_keep_numeric_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            stl = pathlib.Path(tmp) / "broken.stl"
            stl.write_text("placeholder", encoding="utf-8")

            with mock.patch(
                "subprocess.run",
                return_value=completed(admesh_output(unconnected=2)),
            ):
                result = validate_stl_meshes.validate_stl(stl)

        self.assertFalse(result["passed"])
        self.assertEqual(result["unconnected"], 2)
        self.assertEqual(result["bbox_mm"]["z"], 10.0)
        self.assertEqual(result["bounds_mm"]["min_z"], 0.0)

    def test_min_z_drift_is_informational_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            stl = pathlib.Path(tmp) / "floating.stl"
            stl.write_text("placeholder", encoding="utf-8")

            with mock.patch(
                "subprocess.run",
                return_value=completed(admesh_output(min_z="-0.05", max_z="9.95")),
            ):
                result = validate_stl_meshes.validate_stl(stl)

        self.assertTrue(result["passed"])
        self.assertFalse(result["sits_on_bed"])
        self.assertEqual(result["bounds_mm"]["min_z"], -0.05)


class ValidateSiteTests(unittest.TestCase):
    def test_validate_site_sorts_stls_writes_json_and_reports_failure(self):
        outputs = [
            completed(admesh_output(unconnected=1)),
            completed(admesh_output(facets=20, volume="2e2")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            site = pathlib.Path(tmp) / "site"
            site.mkdir()
            (site / "b.stl").write_text("placeholder", encoding="utf-8")
            (site / "a.stl").write_text("placeholder", encoding="utf-8")
            output = pathlib.Path(tmp) / "out" / "validation.json"

            with mock.patch("subprocess.run", side_effect=outputs):
                results, has_failure = validate_stl_meshes.validate_site(site, output)

            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertTrue(has_failure)
        self.assertEqual([r["name"] for r in results], ["a", "b"])
        self.assertEqual([r["name"] for r in data], ["a", "b"])
        self.assertFalse(data[0]["passed"])
        self.assertTrue(data[1]["passed"])


class MainTests(unittest.TestCase):
    def test_main_writes_github_output_false_for_empty_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = pathlib.Path(tmp) / "site"
            site.mkdir()
            output = pathlib.Path(tmp) / "validation.json"
            github_output = pathlib.Path(tmp) / "github-output"

            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(github_output)}):
                rc = validate_stl_meshes.main(
                    ["--site-dir", str(site), "--output", str(output)]
                )

            data = json.loads(output.read_text(encoding="utf-8"))
            github_output_text = github_output.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertEqual(data, [])
        self.assertEqual(github_output_text, "failed=false\n")

    def test_main_defers_validation_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = pathlib.Path(tmp) / "site"
            site.mkdir()
            (site / "broken.stl").write_text("placeholder", encoding="utf-8")
            output = pathlib.Path(tmp) / "validation.json"
            github_output = pathlib.Path(tmp) / "github-output"

            with mock.patch("subprocess.run", return_value=completed(admesh_output(volume="0"))):
                with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(github_output)}):
                    rc = validate_stl_meshes.main(
                        ["--site-dir", str(site), "--output", str(output)]
                    )
            github_output_text = github_output.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertEqual(github_output_text, "failed=true\n")


if __name__ == "__main__":
    unittest.main()
