#!/usr/bin/env python3
"""Assets a project's .scad files reference from outside the project directory.

A renderable may `import()` a scan reference mesh from `scans/<object>/`
(issue #439). That path resolves for the CI render and for the render cache —
`render_cache.collect_inputs` already hashes it — but not for two build steps
that assume a project is self-contained:

- "Bundle project source zips" bundles `git ls-files -- "$dir"`, which would
  produce a zip that cannot be re-rendered.
- The in-browser customizer writes a project's files flat into the wasm FS,
  where a `../scans/…` path cannot resolve at all.

The first is fixed by adding what this prints to the zip; the second by
refusing the combination in the parameter-manifest validation step.

Pure stdlib, no third-party deps.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from render_cache import collect_inputs


def external_assets(project_dir):
    """Sorted relative paths of assets referenced from outside project_dir."""
    prefix = os.path.normpath(project_dir) + os.sep
    external = set()

    for root, _dirs, files in os.walk(project_dir):
        for name in sorted(files):
            if not name.endswith(".scad"):
                continue
            _scad_files, asset_files, _unresolved = collect_inputs(
                os.path.join(root, name)
            )
            for asset in asset_files:
                rel = os.path.relpath(asset)
                if not rel.startswith(prefix):
                    external.add(rel)

    return sorted(external)


def main(argv):
    if len(argv) != 1:
        sys.stderr.write("usage: external_assets.py <project-dir>\n")
        return 2
    for rel in external_assets(argv[0]):
        print(rel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
