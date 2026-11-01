#!/usr/bin/env python3
"""Keep the project spec pages' inline SVG figures in step with their generators.

Each project spec page under pages/<project>/index.html is hand-authored,
self-contained HTML whose figures are inline SVG, so they theme with the
page. The SVGs come from Node scripts in pages/<project>/src/ (no
dependencies), which write <name>.svg into the current directory; the
outputs are committed beside them and spliced into the page in order.
pages.yml publishes the committed page as is, so nothing is assembled at
publish time; this module only checks (and on request repairs) the chain
generator -> committed SVG -> inline element. See docs/ci-pipeline.md,
"pages.yml (spec pages)".

Usage:
  python3 scripts/spec_pages.py --check   # report mismatches, exit 1 on any
  python3 scripts/spec_pages.py --write   # re-splice committed SVGs into pages
"""

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES_ROOT = REPO_ROOT / "pages"

# project -> [(generator script in src/, [figure names it writes])]. The
# figures appear in the page in the order of this concatenated list.
GENERATORS = {
    "climbing-frame": [
        ("diagrams.js", ["plan", "front", "side", "ends"]),
        ("aframe_diagram.js", ["aframe_ends", "aframe_plan"]),
    ],
}

SVG_RE = re.compile(r"<svg[\s\S]*?</svg>")
# Anything that would make the browser fetch a resource. Plain <a href>
# links are allowed; url(#id) marker references inside an SVG are local.
EXTERNAL_RE = re.compile(
    r"<script|<link|<img|<iframe|<object|<embed|@import|url\((?!#)|\ssrc\s*=",
    re.IGNORECASE,
)


def project_dir(project):
    return PAGES_ROOT / project


def figure_names(project):
    return [name for _script, names in GENERATORS[project] for name in names]


def generated_svgs(project, script):
    """Run one generator in a fresh temp dir; return {name: bytes} it wrote."""
    src = project_dir(project) / "src" / script
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["node", str(src)], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        return {p.stem: p.read_bytes() for p in pathlib.Path(tmp).glob("*.svg")}


def committed_svg(project, name):
    return (project_dir(project) / "src" / f"{name}.svg").read_text(encoding="utf-8")


def inline_svgs(html):
    """The page's <svg …</svg> elements in document order."""
    return SVG_RE.findall(html)


def splice(html, svgs):
    """Replace the page's inline SVGs, in order, with ``svgs``."""
    found = inline_svgs(html)
    if len(found) != len(svgs):
        raise ValueError(f"page has {len(found)} inline SVGs, expected {len(svgs)}")
    replacements = iter(svgs)
    return SVG_RE.sub(lambda _m: next(replacements), html)


def external_refs(html):
    """Every occurrence that would load an external asset."""
    return [m.group(0) for m in EXTERNAL_RE.finditer(html)]


def check_generators(project):
    """Mismatches between each generator's output and its committed SVGs."""
    problems = []
    for script, names in GENERATORS[project]:
        out = generated_svgs(project, script)
        if sorted(out) != sorted(names):
            problems.append(f"{project}/src/{script} wrote {sorted(out)}, expected {sorted(names)}")
        for name in names:
            path = project_dir(project) / "src" / f"{name}.svg"
            if name in out and (not path.is_file() or path.read_bytes() != out[name]):
                problems.append(f"{project}/src/{name}.svg differs from {script}'s output; "
                                f"run `node src/{script}` in pages/{project}/src/")
    return problems


def check_page(project):
    """Mismatches between the committed SVGs and the page's inline figures."""
    html = (project_dir(project) / "index.html").read_text(encoding="utf-8")
    names = figure_names(project)
    found = inline_svgs(html)
    if len(found) != len(names):
        return [f"{project}/index.html has {len(found)} inline SVGs, expected {len(names)}"]
    return [f"{project}/index.html figure {i + 1} differs from src/{name}.svg; "
            "run scripts/spec_pages.py --write"
            for i, (name, svg) in enumerate(zip(names, found))
            if svg != committed_svg(project, name).strip()]


def check(project):
    return check_generators(project) + check_page(project)


def write(project):
    page = project_dir(project) / "index.html"
    html = page.read_text(encoding="utf-8")
    svgs = [committed_svg(project, name).strip() for name in figure_names(project)]
    page.write_text(splice(html, svgs), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        for project in GENERATORS:
            write(project)
        return 0
    problems = [p for project in GENERATORS for p in check(project)]
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
