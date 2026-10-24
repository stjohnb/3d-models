#!/usr/bin/env python3
"""Files a project's .scad files reference from outside the project directory.

A renderable may `import()` a scan reference mesh from `scans/<object>/`
(issue #439), or `include` another project's shared underscore library by
relative path (`include <../drawer-organiser/_drawer_organiser.scad>`,
issue clw_01M4R6ED006HYSY6F15NMYHMGD). Those paths resolve for the CI render
and for the render cache — `render_cache.collect_inputs` already hashes them —
but two build steps assume a project is self-contained:

- "Bundle project source zips" bundles `git ls-files -- "$dir"`, so it adds
  what `external_assets()` reports (out-of-project assets and .scad files) to
  keep the zip re-renderable.
- The in-browser customizer fetches `site/sources/<project>/manifest.json`
  and writes each listed file into the wasm FS at its project-relative path.
  `--stage` builds that tree, and the parameter-manifest validation refuses a
  manifest whose include chain is not fully staged. Both use one rule
  (`browser_sources_for`): an input is stageable when it is an existing
  `.scad` or `.png` inside the repository. A `scans/` mesh is not.

Paths that escape the repository root or land under `.git/` are dropped, not
bundled — `render_cache.is_contained()` already enforces this in
`collect_inputs`, and this module re-applies the same check as a second,
independent layer since these paths are handed straight to `zip` for a
publicly deployed artifact.

Usage (from the repository root):
  external_assets.py <dir>                 out-of-project inputs, one per line
  external_assets.py --manifest <dir>      the project's browser manifest (JSON)
  external_assets.py --stage <sources-dir> stage every project for the browser

Pure stdlib, no third-party deps.
"""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from render_cache import collect_inputs, is_contained

STAGEABLE_EXTS = (".scad", ".png")
STAGE_SKIP_DIRS = {"site"}


def _repo_rel(path):
    """Repo-relative path, or None when path is outside the repo or not a file."""
    if not is_contained(path):
        return None
    rel = os.path.relpath(path)
    if rel.startswith(".." + os.sep) or rel == "..":
        return None
    return rel


def external_assets_for(scad_path, project_dir):
    """Sorted relative paths of inputs scad_path pulls in from outside project_dir.

    Covers both binary assets and .scad files, so a cross-project include
    brings the shared library (and everything it includes) into the source
    zip. Scoped to one renderable's own transitive include chain — unlike
    external_assets(), which unions every .scad in the directory.
    """
    prefix = os.path.normpath(project_dir) + os.sep
    scad_files, asset_files, _unresolved = collect_inputs(scad_path)
    external = []
    for path in scad_files | asset_files:
        rel = _repo_rel(path)
        if rel is not None and not rel.startswith(prefix):
            external.append(rel)
    return sorted(external)


def external_assets(project_dir):
    """Sorted relative paths of inputs referenced from outside project_dir."""
    external = set()

    for root, _dirs, files in os.walk(project_dir):
        for name in sorted(files):
            if not name.endswith(".scad"):
                continue
            external.update(
                external_assets_for(os.path.join(root, name), project_dir)
            )

    return sorted(external)


def _project_rel(rel, project_dir):
    """POSIX path of repo-relative `rel` as seen from project_dir (may start ../)."""
    return os.path.relpath(rel, os.path.normpath(project_dir)).replace(os.sep, "/")


def browser_sources_for(scad_path, project_dir):
    """(stageable, unstageable) inputs of scad_path for the in-browser customizer.

    stageable: sorted project-relative POSIX paths (possibly `../other/…`) of
    every existing .scad/.png in the include chain — exactly what --stage
    copies and lists in manifest.json. unstageable: everything else the chain
    needs (e.g. a scans/ STL, a missing or out-of-tree include), which the
    browser can never resolve.
    """
    scad_files, asset_files, unresolved = collect_inputs(scad_path)
    stageable, unstageable = set(), set(unresolved)
    for path in scad_files | asset_files:
        rel = _repo_rel(path)
        if rel is None:
            unstageable.add(path)
        elif rel.endswith(STAGEABLE_EXTS):
            stageable.add(_project_rel(rel, project_dir))
        else:
            unstageable.add(rel)
    return sorted(stageable), sorted(unstageable)


def unstageable_inputs_for(scad_path, project_dir):
    """Inputs of scad_path the customizer cannot stage; empty means customizable."""
    return browser_sources_for(scad_path, project_dir)[1]


def project_manifest(project_dir):
    """Sorted project-relative paths the browser fetches for project_dir.

    The union of browser_sources_for() over every .scad under the directory.
    A surface() heightmap named through a variable is invisible to
    collect_inputs, so a project's own .png files whose basename appears in
    a sibling .scad are added too (the old staging rule).
    """
    entries = set()
    for root, _dirs, files in os.walk(project_dir):
        scads = sorted(f for f in files if f.endswith(".scad"))
        texts = []
        for name in scads:
            path = os.path.join(root, name)
            entries.update(browser_sources_for(path, project_dir)[0])
            with open(path, encoding="utf-8", errors="replace") as f:
                texts.append(f.read())
        for name in sorted(files):
            if name.endswith(".png") and any(name in t for t in texts):
                rel = _repo_rel(os.path.join(root, name))
                if rel is not None:
                    entries.add(_project_rel(rel, project_dir))
    return sorted(entries)


def stage_projects():
    """Top-level project directories (sorted) that contain .scad files."""
    projects = []
    for name in sorted(os.listdir(".")):
        if name.startswith(".") or name in STAGE_SKIP_DIRS or not os.path.isdir(name):
            continue
        for _root, _dirs, files in os.walk(name):
            if any(f.endswith(".scad") for f in files):
                projects.append(name)
                break
    return projects


def stage(sources_dir):
    """Copy every project's browser sources under sources_dir and write manifests.

    Each file lands at <sources_dir>/<repo-relative path>, so a manifest
    entry `../other/_lib.scad` for project `proj` resolves (by URL
    normalisation) to the staged <sources_dir>/other/_lib.scad.
    """
    for project in stage_projects():
        entries = project_manifest(project)
        for entry in entries:
            rel = os.path.normpath(os.path.join(project, entry))
            dest = os.path.join(sources_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(rel, dest)
        os.makedirs(os.path.join(sources_dir, project), exist_ok=True)
        with open(os.path.join(sources_dir, project, "manifest.json"), "w") as out:
            json.dump(entries, out)


def main(argv):
    if len(argv) == 2 and argv[0] == "--manifest":
        print(json.dumps(project_manifest(argv[1])))
        return 0
    if len(argv) == 2 and argv[0] == "--stage":
        stage(argv[1])
        return 0
    if len(argv) == 1 and not argv[0].startswith("--"):
        for rel in external_assets(argv[0]):
            print(rel)
        return 0
    sys.stderr.write(
        "usage: external_assets.py <project-dir> | --manifest <project-dir>"
        " | --stage <site-sources-dir>\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
