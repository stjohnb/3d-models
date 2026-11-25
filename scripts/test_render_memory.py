"""Unit tests for render_memory.py (heavy-render markers, issue
clw_01M55BX5C0F7WYKCACTYPY1NV4)."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import render_memory
from render_memory import (
    RENDER_HEAVY_YML,
    check_tier,
    heavy_tier_gb,
    load_map,
    runner_limit_gb,
    should_defer,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LoadMapTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _meta(self, project, data):
        os.makedirs(os.path.join(self.root, project), exist_ok=True)
        with open(os.path.join(self.root, project, "meta.json"), "w") as f:
            json.dump(data, f)

    def test_maps_marked_renderables_to_repo_relative_sources(self):
        self._meta("terrain-model", {
            "description": "x",
            "render_memory_gb": {"terrain": 12, "assembly": 8},
        })
        self._meta("plain", {"description": "no markers"})
        self.assertEqual(
            load_map(self.root),
            {"terrain-model/assembly.scad": 8, "terrain-model/terrain.scad": 12},
        )

    def test_skips_meta_failures(self):
        self._meta("bad", {"description": "x", "render_memory_gb": {"a": 12}})
        self._meta("good", {"description": "x", "render_memory_gb": {"b": 9}})
        with open(os.path.join(self.root, ".meta-failures"), "w") as f:
            f.write("bad/meta.json")
        self.assertEqual(load_map(self.root), {"good/b.scad": 9})

    def test_skips_invalid_json(self):
        os.makedirs(os.path.join(self.root, "broken"))
        with open(os.path.join(self.root, "broken", "meta.json"), "w") as f:
            f.write("{")
        self.assertEqual(load_map(self.root), {})

    def test_repo_map_marks_the_nz_ski_fields_parts(self):
        mapping = load_map(REPO_ROOT)
        for name in ("terrain", "snow", "lake", "assembly"):
            src = f"nz-ski-fields/{name}.scad"
            self.assertIn(src, mapping)
            self.assertTrue(os.path.isfile(os.path.join(REPO_ROOT, src)), src)

    def test_cli_map_prints_tab_separated_whole_gb(self):
        self._meta("p", {"description": "x", "render_memory_gb": {"a": 7.2}})
        out = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out):
                self.assertEqual(render_memory.main(["map"]), 0)
        finally:
            os.chdir(cwd)
        self.assertEqual(out.getvalue(), "p/a.scad\t8\n")


class RunnerLimitTests(unittest.TestCase):
    def test_unset(self):
        self.assertIsNone(runner_limit_gb({}))

    def test_empty(self):
        self.assertIsNone(runner_limit_gb({"RUNNER_JOB_MEMORY_GB": ""}))

    def test_non_numeric(self):
        self.assertIsNone(runner_limit_gb({"RUNNER_JOB_MEMORY_GB": "4Gi"}))

    def test_integer(self):
        self.assertEqual(runner_limit_gb({"RUNNER_JOB_MEMORY_GB": "4"}), 4)

    def test_cli_limit_reads_the_environment(self):
        for value, expected in (("28", "28"), ("", ""), ("x", "")):
            out = io.StringIO()
            with mock.patch.dict(os.environ, {"RUNNER_JOB_MEMORY_GB": value}), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(render_memory.main(["limit"]), 0)
            self.assertEqual(out.getvalue(), expected, value)


class HeavyTierTests(unittest.TestCase):
    """render-heavy.yml's ram-<N>g tier bounds every mark (issue
    clw_01M5HEP2DE1JYFZEW1S1WXSDSJ)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _workflow(self, runs_on):
        path = os.path.join(self.root, RENDER_HEAVY_YML)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(
                "jobs:\n"
                "  render:\n"
                "    # not a runs-on: [container, linux, ram-99g] line\n"
                f"    runs-on: {runs_on}\n"
            )

    def _meta(self, project, marks):
        os.makedirs(os.path.join(self.root, project), exist_ok=True)
        with open(os.path.join(self.root, project, "meta.json"), "w") as f:
            json.dump({"description": "x", "render_memory_gb": marks}, f)

    def _cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = render_memory.main(argv)
        finally:
            os.chdir(cwd)
        return rc, out.getvalue(), err.getvalue()

    def test_parses_the_ram_tier(self):
        self._workflow("[container, linux, ram-12g]")
        self.assertEqual(heavy_tier_gb(self.root), 12)
        self.assertEqual(self._cli(["tier"]), (0, "12", ""))

    def test_ignores_other_labels(self):
        self._workflow("[container, linux, disk-60g, ram-8g, gpu]")
        self.assertEqual(heavy_tier_gb(self.root), 8)

    def test_missing_tier_label(self):
        self._workflow("[container, linux]")
        self.assertIsNone(heavy_tier_gb(self.root))
        rc, out, err = self._cli(["tier"])
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("no single ram-<N>g tier label", err)
        self.assertEqual(len(check_tier(self.root)), 1)
        self.assertEqual(self._cli(["check-tier"])[0], 1)

    def test_missing_workflow(self):
        self.assertIsNone(heavy_tier_gb(self.root))

    def test_marks_within_the_tier_pass(self):
        self._workflow("[container, linux, ram-12g]")
        self._meta("p", {"a": 12, "b": 4})
        self.assertEqual(check_tier(self.root), [])
        self.assertEqual(self._cli(["check-tier"]), (0, "", ""))

    def test_over_tier_mark_names_each_renderable(self):
        self._workflow("[container, linux, ram-12g]")
        self._meta("p", {"a": 12, "b": 12.5, "c": 16})
        rc, out, _ = self._cli(["check-tier"])
        self.assertEqual(rc, 1)
        self.assertNotIn("p/a.scad", out)
        self.assertIn("p/b.scad", out)
        self.assertIn("p/c.scad", out)
        self.assertIn("ram-12g", out)

    def test_repo_marks_fit_render_heavy_tier(self):
        self.assertIsNotNone(heavy_tier_gb(REPO_ROOT))
        self.assertEqual(check_tier(REPO_ROOT), [])


class ShouldDeferTests(unittest.TestCase):
    def test_truth_table(self):
        cases = [
            (None, None, False),
            (12, None, False),   # unknown cap: attempt the render
            (None, 4, False),    # unmarked: behave as today
            (12, 4, True),
            (12, 12, False),
            (12, 28, False),
        ]
        for need, limit, expected in cases:
            with self.subTest(need=need, limit=limit):
                self.assertIs(should_defer(need, limit), expected)


if __name__ == "__main__":
    unittest.main()
