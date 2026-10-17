"""Pins output-name uniqueness for renderable .scad sources (issue #449).

Every renderable lands in one flat namespace — site/<name>.stl, .png,
site/qr/<name>.png, site/standalone/<name>.html — and its OEmbed endpoint
and deep link are site/oembed/<project_slug>/<model_slug>.json and
#<project_slug>/<model_slug>. A repeated basename means the second render
silently overwrites the first's STL and thumbnail while both projects keep
a row in site/.scad-map, so one project's card serves the other's mesh. A
repeated slug within a project means the second OEmbed endpoint overwrites
the first and the deep link becomes ambiguous.

Both are functions of the file list alone, so they are checked here — in
the unit-test step, which runs before "Render STL files" — rather than
inside the render loop, where a failure comes after the clobber.

Run with: python3 -m unittest test_output_names
"""

import pathlib
import re
import sys
import unittest
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from oembed_helpers import slugify

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._ -]+$")


def scad_sources():
    """Repo-relative posix paths of every .scad build.yml's render loop sees.

    Mirrors `find . -name '*.scad' -not -path './.github/*'`.
    """
    for path in sorted(REPO_ROOT.rglob("*.scad")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.split("/")[0] in (".git", ".github"):
            continue
        yield rel


def renderables():
    """(project_dir, stem, rel) for each non-library source.

    Underscore-prefixed basenames are libraries; build.yml skips them
    before they claim an output name, so two projects may both ship
    _common.scad. Everything else claims site/<stem>.stl.
    """
    for rel in scad_sources():
        basename = rel.rsplit("/", 1)[-1]
        if basename.startswith("_"):
            continue
        stem = basename[: -len(".scad")]
        project_dir = rel.split("/")[0] if "/" in rel else "."
        yield project_dir, stem, rel


class OutputNameTests(unittest.TestCase):
    def test_enumeration_is_not_vacuous(self):
        found = list(renderables())
        self.assertGreaterEqual(
            len(found), 50,
            f"renderables() found {len(found)} sources; the enumeration is "
            "broken and the uniqueness tests below are vacuous",
        )
        rels = {rel for _, _, rel in found}
        self.assertIn("toothbrush/Toothbrush tray.scad", rels)

    def test_basenames_use_the_safe_charset(self):
        offenders = []
        for rel in scad_sources():
            basename = rel.rsplit("/", 1)[-1]
            stem = basename[: -len(".scad")]
            if not SAFE_NAME_RE.match(stem):
                offenders.append(rel)
        self.assertEqual(
            offenders, [],
            f"{offenders} contain characters outside [A-Za-z0-9._ -]; CI "
            "refuses to render these",
        )

    def test_renderable_basenames_are_globally_unique(self):
        by_stem = defaultdict(list)
        for _, stem, rel in renderables():
            by_stem[stem].append(rel)
        collisions = {stem: rels for stem, rels in by_stem.items() if len(rels) > 1}
        messages = [
            f"{stem!r} is claimed by {', '.join(sorted(rels))} — both render "
            f"to site/{stem}.stl, and the second silently overwrites the "
            "first. Rename one."
            for stem, rels in sorted(collisions.items())
        ]
        self.assertEqual(collisions, {}, "; ".join(messages))

    def test_renderable_slugs_are_unique_within_a_project(self):
        by_slug = defaultdict(list)
        for project_dir, stem, rel in renderables():
            key = (slugify(project_dir), slugify(stem))
            by_slug[key].append(rel)
        collisions = {key: rels for key, rels in by_slug.items() if len(rels) > 1}
        messages = [
            f"{rels} all slugify to project={project_slug!r} "
            f"model={model_slug!r} within the same project — the second "
            f"would overwrite site/oembed/{project_slug}/{model_slug}.json "
            f"and make #{project_slug}/{model_slug} ambiguous. Rename one."
            for (project_slug, model_slug), rels in sorted(collisions.items())
        ]
        self.assertEqual(collisions, {}, "; ".join(messages))

    def test_libraries_may_share_a_basename_across_projects(self):
        for _, _, rel in renderables():
            basename = rel.rsplit("/", 1)[-1]
            self.assertFalse(
                basename.startswith("_"),
                f"{rel} is underscore-prefixed and should have been "
                "excluded as a library",
            )


if __name__ == "__main__":
    unittest.main()
