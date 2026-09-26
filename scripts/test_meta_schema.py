"""Schema-level guards for meta.json's assembly descriptor (issue #505)."""

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


if __name__ == "__main__":
    unittest.main()
