"""Schema-level guards for meta.json (assembly descriptor, issue #505; render_memory_gb)."""

import glob
import json
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(REPO_ROOT, "meta.schema.json")
BASENAME_RE = r"[A-Za-z0-9._ -]+\.stl"


class AssemblyPatternTests(unittest.TestCase):
    def setUp(self):
        with open(SCHEMA_PATH) as f:
            self.schema = json.load(f)

    def test_assembly_stl_has_basename_pattern(self):
        pattern = self.schema["properties"]["assembly"]["properties"]["stl"]["pattern"]
        self.assertEqual(pattern, "^[A-Za-z0-9._ -]+\\.stl$")

    def test_assembly_part_stl_has_basename_pattern(self):
        pattern = self.schema["properties"]["assembly"]["properties"]["parts"]["items"][
            "properties"
        ]["stl"]["pattern"]
        self.assertEqual(pattern, "^[A-Za-z0-9._ -]+\\.stl$")

    def test_pattern_matches_hero_pattern(self):
        hero_pattern = self.schema["properties"]["hero"]["pattern"]
        stl_pattern = self.schema["properties"]["assembly"]["properties"]["stl"]["pattern"]
        part_pattern = self.schema["properties"]["assembly"]["properties"]["parts"]["items"][
            "properties"
        ]["stl"]["pattern"]
        self.assertEqual(stl_pattern, hero_pattern)
        self.assertEqual(part_pattern, hero_pattern)

    def test_committed_meta_assembly_values_are_basenames(self):
        for meta_path in glob.glob(os.path.join(REPO_ROOT, "*", "meta.json")):
            with open(meta_path) as f:
                meta = json.load(f)
            assembly = meta.get("assembly")
            if not isinstance(assembly, dict):
                continue
            with self.subTest(meta_path=meta_path, field="stl"):
                self.assertIsNotNone(re.fullmatch(BASENAME_RE, assembly.get("stl", "")))
            for i, part in enumerate(assembly.get("parts", [])):
                with self.subTest(meta_path=meta_path, part=i):
                    self.assertIsNotNone(re.fullmatch(BASENAME_RE, part.get("stl", "")))


class RenderMemoryTests(unittest.TestCase):
    """render_memory_gb heavy-render markers (clw_01M55BX5C0F7WYKCACTYPY1NV4)."""

    def setUp(self):
        with open(SCHEMA_PATH) as f:
            self.schema = json.load(f)

    def _errors(self, marks):
        from jsonschema import Draft202012Validator

        instance = {"description": "x", "render_memory_gb": marks}
        return list(Draft202012Validator(self.schema).iter_errors(instance))

    def test_accepts_the_nz_ski_fields_shape(self):
        with open(os.path.join(REPO_ROOT, "nz-ski-fields", "meta.json")) as f:
            marks = json.load(f)["render_memory_gb"]
        self.assertEqual(marks, {"terrain": 12, "snow": 12, "lake": 12, "assembly": 8})
        self.assertEqual(self._errors(marks), [])

    def test_rejects_a_string_value(self):
        self.assertNotEqual(self._errors({"terrain": "12"}), [])

    def test_rejects_a_value_below_one(self):
        self.assertNotEqual(self._errors({"terrain": 0.5}), [])

    def test_rejects_a_key_with_a_slash(self):
        self.assertNotEqual(self._errors({"nz-ski-fields/terrain": 12}), [])


if __name__ == "__main__":
    unittest.main()
