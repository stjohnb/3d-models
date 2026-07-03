# 3d-models — Claude guidance

This repo is a collection of 3D-printable OpenSCAD models. A CI pipeline renders `.scad` sources into STLs, generates thumbnails, validates meshes, and deploys an interactive Three.js viewer to [bstjohn.net/3d-models](https://www.bstjohn.net/3d-models/).

## Read first

Before working on any issue or change, read:

- `docs/OVERVIEW.md` — architecture, model projects, key patterns (authoritative)
- `docs/ci-pipeline.md` — CI/CD step-by-step detail (when touching CI or build)
- `docs/OPENSCAD_LIBRARIES.md` — available third-party libraries (when proposing new models or geometry)
- `ideas/rejected.md` — patterns the maintainer has already declined; do not re-propose these

## Self-hosted runner constraint

GitHub Actions jobs in this repo **must** use self-hosted runners:

```yaml
runs-on: [self-hosted, linux]   # for Linux jobs
runs-on: [self-hosted, macos]   # for macOS jobs
```

Never use `ubuntu-latest`, `ubuntu-22.04`, `windows-latest`, `windows-2022`, or any other GitHub-hosted Linux/Windows runner. macOS GitHub-hosted runners (`macos-latest`, `macos-14`) are the only exception. Always include the OS label — bare `runs-on: self-hosted` is not acceptable.

## OpenSCAD conventions

- **Library files**: underscore-prefixed (`_*.scad`). Define shared parameters and modules; produce no top-level geometry. CI skips these during STL rendering.
- **Renderable files**: each produces exactly one STL. Contain top-level geometry directly or include/use a library and call a module.
- **Resolution**: `$fn = 64` in all `.scad` sources.
- **Dimensions**: all dimensions declared as named variables at the top of each file, in mm.
- **Beveled transitions**: use `hull()` between thin extrusions (`0.01` mm) at different Z positions with different cross-sections.
- **Viewer rotation**: OpenSCAD is Z-up; Three.js expects Y-up. Assembly/preview files and tube-shaped models apply `rotate([-90, 0, 0])` at the top level. Symmetric/upright models and individual print-oriented files omit it.

## Filename safety

CI refuses to render any `.scad` file whose basename contains characters outside `[A-Za-z0-9._ -]`. Do not introduce filenames with other characters.

## XSS / HTML safety

All dynamic content in `index.html`, `embed.html`, and standalone viewers that interpolates model names, filenames, or other data into the DOM must use the DOM API (`createElement`/`textContent`/`setAttribute`). Never use `innerHTML` for user-derived data.

For standalone HTML viewers, `scripts/generate-standalone.py` embeds filament color data inside a `<script>` block. The `_load_filament_colors_js()` function applies two escaping layers:
1. `json.dumps(name)` — handles `"`, `\`, control characters
2. Unicode escapes for `<`, `>`, `&` → `<`, `>`, `&`

Both layers are required. Do not regress either. Covered by `scripts/test_generate_standalone.py`.

## Slugify invariant

The `slugify()` function — strip `.stl`, replace `[_\s]+` with `-`, lowercase — must remain identical across all four locations:

- `index.html`
- `embed.html`
- `scripts/oembed_helpers.py`
- `scripts/generate-gallery.py`

If you change one, change all four in the same PR.

## `meta.json` schema

Validated against `meta.schema.json` (JSON Schema draft 2020-12). Only `description` is required. Do not add fields to `meta.json` without updating `meta.schema.json` first.

## `<basename>.parameters.json` manifests

Validated against `parameters.schema.json`. Only `number` and `boolean` types are permitted — never `string`. Strings would require shell quoting when passed via `-D name=value` to OpenSCAD and create injection risk.

## Deferred enforcement pattern

Dependency-graph checks, mesh validation, metadata validation, and interference checks record failures early but only block the build at the final enforcement step. This gives the full pipeline output even when some validations fail. Preserve this pattern when adding new CI validation.

## Generated artifacts — never hand-edit

| Artifact | Generator |
|---|---|
| `models.json` | CI build |
| README gallery between `<!-- gallery:start -->` / `<!-- gallery:end -->` | `scripts/generate-gallery.py` |
| Per-project `dependency-graph.md` | `scripts/scad-dep-graph.sh` |
| `site/oembed/**` | CI build |
| `site/standalone/**` | `scripts/generate-standalone.py` |
| `site/qr/**` | CI `qrencode` step |
| All `.stl` outputs | CI OpenSCAD render (gitignored) |

## Testing

- Python scripts: `python3 -m pytest scripts/`
- WASM customizer pipeline: `node scripts/test_wasm_customizer.mjs`
- Do not run integration tests or anything requiring Docker or external services locally — CI handles those.

## Rendering on the constrained build host (IMPORTANT)

When validating a model locally during issue work, you are running on a
**memory-constrained host (~3.8 GB RAM / 4 cores, shared across parallel
workers)**. A full-resolution STL export of a complex or procedural model can
exceed 2 GB RSS and freeze the entire host — this has caused real outages.
Full-resolution STL renders are CI's job; your only job locally is to
sanity-check geometry. Therefore:

- **Never run a bare `openscad ... -o foo.stl`.** Always cap memory and time:
  `systemd-run --user --scope -p MemoryMax=1G -- timeout 300 openscad ...`
  (or `( ulimit -v 1500000; timeout 300 openscad ... )` if `systemd-run` is
  unavailable).
- **Prefer cheap checks over full exports** while iterating:
  `openscad --export-format csg -o /dev/null file.scad` validates syntax and
  evaluates the model without meshing; render a low-`$fn` preview before any
  full STL export.
- Keep `$fn` / `$fa` / `$fs` modest while iterating. Note: committed sources use
  `$fn = 64` (see OpenSCAD conventions) — lower it only in throwaway local
  checks, never in the committed `.scad`. Do a high-resolution export only once
  geometry is correct, and still under the memory cap.
- **Don't render multiple models concurrently.**
- `scripts/render_view.py` also invokes `openscad` — run it under the same
  memory/time cap, and pass a low `--fn` / modest view while iterating.
- **If a render is OOM-killed or times out, do NOT just retry it.** Treat it as
  "too heavy for this host": reduce resolution/geometry, or leave the full
  render to CI. Blindly re-running an OOM'd render repeats the outage.

*(Durable per-worker enforcement is tracked separately in St-John-Software/claws#1463; the rules above are the advisory front-line mitigation.)*

## Local dev tool (not CI)

`scripts/render_view.py` renders arbitrary OpenSCAD views to PNG for iterative design. It is not used by CI and produces no build artifacts. Do not wire it into the build.

## Blog voice (`docs/blog-post.md`)

`docs/blog-post.md` is a personal-blog draft, not product copy. When writing or editing it, hold this voice (maintainer direction from #243):

- **It's a hobby write-up, not a pitch.** First person throughout — "I wanted", "I ended up", "honestly". The author is describing something he enjoyed making, not selling a workflow.
- **No marketing cadence.** Avoid short punchy fragments and superlatives ("the centerpiece", "it just works", "cheap insurance", "particularly happy with"). Prefer longer, calmer sentences that are allowed to ramble or hedge.
- **Admit friction.** Keep the dead ends and fiddly bits — prints that didn't fit first time, tolerances that took a few goes, the snap-ridge-too-tight problem. The post is more believable for them.
- **Don't make Claude the hero.** Claude Code (interactive) and Claws (autonomous issue work on this repo) are tools the author used, mentioned matter-of-factly and woven through — not the subject of the post.
- **Never fabricate technical detail.** Ground every concrete claim (dimensions, ADMesh checks, pipeline steps) in `docs/OVERVIEW.md` or the actual sources. If a detail can't be grounded, cut it rather than invent it.

## Ideas backlog

`ideas/` contains feature ideas, cross-project learnings, and `ideas/rejected.md` with patterns the maintainer has declined. Consult `ideas/rejected.md` before proposing any new approach.
