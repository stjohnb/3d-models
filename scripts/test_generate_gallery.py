"""Tests for generate-gallery.py's pick_thumbnail hero selection (issue #372)."""

import glob
import importlib.util
import json
import os
import unittest


def _load_module():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "generate_gallery",
        os.path.join(scripts_dir, "generate-gallery.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gg = _load_module()

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_HEROES = {
    "blast-gate": "gate_assembly.stl",
    "drawer-organiser": "drawer_assembly.stl",
    "esp32-display-case": "case_front.stl",
    "macbook-pro-laptop-stand": "laptop_stand.stl",
    "nz-ski-fields": "assembly.stl",
    "power-workshop": "screwdriver_handle.stl",
    "scanning-rig": "scanning_rig_assembly.stl",
    "toothbrush": "Toothbrush assembly.stl",
}


class PickThumbnailTests(unittest.TestCase):
    FILES = [{"stl": "phone_stand.stl"}, {"stl": "scanning_rig_assembly.stl"}]

    def test_hero_used_when_present(self):
        self.assertEqual(
            gg.pick_thumbnail(self.FILES, "scanning_rig_assembly.stl"),
            "scanning_rig_assembly.png",
        )

    def test_hero_absent_falls_back_alphabetically(self):
        self.assertEqual(gg.pick_thumbnail(self.FILES, None), "phone_stand.png")

    def test_unknown_hero_falls_back(self):
        self.assertEqual(gg.pick_thumbnail(self.FILES, "nope.stl"), "phone_stand.png")

    def test_hero_with_space_in_name(self):
        files = [{"stl": "Toothbrush assembly.stl"}, {"stl": "Toothbrush tray.stl"}]
        self.assertEqual(
            gg.pick_thumbnail(files, "Toothbrush assembly.stl"),
            "Toothbrush assembly.png",
        )

    def test_no_files_returns_none(self):
        self.assertIsNone(gg.pick_thumbnail([], None))

    def test_files_without_stl_key_ignored(self):
        self.assertIsNone(gg.pick_thumbnail([{"source": "x/y.scad"}], None))


class MetaHeroTests(unittest.TestCase):
    """Sweeps every project's meta.json for a declared `hero` and checks it."""

    def _meta_files(self):
        return sorted(glob.glob(os.path.join(REPO_ROOT, "*/meta.json")))

    def test_declared_heroes_resolve_to_renderable_scad(self):
        for path in self._meta_files():
            with open(path) as f:
                meta = json.load(f)
            hero = meta.get("hero")
            if hero is None:
                continue
            with self.subTest(path=path):
                self.assertTrue(hero.endswith(".stl"), hero)
                self.assertRegex(hero, r"^[A-Za-z0-9._ -]+\.stl$")
                project_dir = os.path.dirname(path)
                scad_name = hero[:-len(".stl")] + ".scad"
                scad_path = os.path.join(project_dir, scad_name)
                self.assertTrue(
                    os.path.isfile(scad_path), f"missing {scad_path} for {path}"
                )
                self.assertFalse(scad_name.startswith("_"), scad_name)

    def test_expected_projects_declare_hero(self):
        actual = {}
        for path in self._meta_files():
            with open(path) as f:
                meta = json.load(f)
            hero = meta.get("hero")
            if hero is not None:
                project = os.path.basename(os.path.dirname(path))
                actual[project] = hero
        self.assertEqual(actual, EXPECTED_HEROES)


if __name__ == "__main__":
    unittest.main()
