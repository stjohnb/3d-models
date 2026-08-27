# 3d-models — Claude guidance

This repo is a collection of 3D-printable OpenSCAD models. A CI pipeline renders `.scad` sources into STLs, generates thumbnails, validates meshes, and deploys an interactive Three.js viewer to [bstjohn.net/3d-models](https://www.bstjohn.net/3d-models/).

## Read first

Before working on any issue or change, read:

- `docs/OVERVIEW.md` — architecture, model projects, key patterns (authoritative)
- `docs/ci-pipeline.md` — CI/CD step-by-step detail (when touching CI or build)
- `docs/OPENSCAD_LIBRARIES.md` — available third-party libraries (when proposing new models or geometry)
- `docs/claws-automation.md` — how the Claws automation service manages issues, PRs, and labels for this repo
- `ideas/rejected.md` — patterns the maintainer has already declined; do not re-propose these

All changes land via pull request; nothing is pushed directly to the default branch — see [docs/claws-automation.md](docs/claws-automation.md) for the full lifecycle.

## Self-hosted runner constraint

GitHub Actions jobs in this repo **must** use self-hosted runners:

```yaml
runs-on: [self-hosted, linux]   # for Linux jobs
runs-on: [self-hosted, macos]   # for macOS jobs
```

Never use `ubuntu-latest`, `ubuntu-22.04`, `windows-latest`, `windows-2022`, or any other GitHub-hosted Linux/Windows runner. macOS GitHub-hosted runners (`macos-latest`, `macos-14`) are the only exception. Always include the OS label — bare `runs-on: self-hosted` is not acceptable.

`build.yml`'s `build` job additionally pins a third label — `runs-on: [self-hosted, linux, ryzen]` — so the OpenSCAD render memory caps (`scripts/capped-openscad.sh`) are calibrated against a host of known RAM capacity (issue #272). Preserve this pin; don't widen it back to plain `[self-hosted, linux]`.

## CI dependencies come from flake.nix

The runners are NixOS and provide only a baseline (nix, git, docker). Every tool a workflow shells out to — openscad, admesh, python3, node, imagemagick, zip, qrencode, aws, gh — comes from this repo's `flake.nix` devShells, entered via the job-level `defaults.run.shell: nix ... develop ...` (see `.github/workflows/build.yml`). If CI needs a new tool, add it to the matching devShell; never `sudo apt-get install` (no apt or sudo on the runners), never `actions/setup-node`/`actions/setup-python` (their prebuilt toolchains don't work on NixOS), never ask for the tool on the runner host. The flake's `openscad` is a headless EGL/llvmpipe wrapper — no Xvfb anywhere. Bumping `flake.lock` can bump OpenSCAD, which invalidates the render cache and forces a slow full re-render; update `.openscad-version` when it does. `scripts/test_build_workflow.py` enforces these invariants.

## OpenSCAD conventions

- **Library files**: underscore-prefixed (`_*.scad`). Define shared parameters and modules; produce no top-level geometry. CI skips these during STL rendering.
- **Renderable files**: each produces exactly one STL. Contain top-level geometry directly or include/use a library and call a module.
- **Resolution**: `$fn = 64` in all `.scad` sources (set once per project, typically in the shared library file that renderable files include). Exception: `hex-connector` has no circular geometry, so it sets per-cylinder `$fn = 6` overrides on its hexagonal prisms instead of a global `$fn = 64`.
- **Dimensions**: all dimensions declared as named variables at the top of each file, in mm.
- **Beveled transitions**: use `hull()` between thin extrusions (`0.01` mm) at different Z positions with different cross-sections.
- **Viewer rotation**: all `.scad` sources stay in OpenSCAD's native Z-up. Never add a top-level `rotate([-90, 0, 0])` for the viewer's benefit — `index.html`, `embed.html` and standalone viewers apply the Z-up→Y-up conversion to every mesh unconditionally. Pinned by `scripts/test_scad_orientation.py`.

## Filename safety

CI refuses to render any `.scad` file whose basename contains characters outside `[A-Za-z0-9._ -]`. Do not introduce filenames with other characters. Renderable (non-underscore) `.scad` basenames must also be unique across all projects, and within a project no two renderables may `slugify()` to the same value — enforced by `scripts/test_output_names.py`, which CI runs before the render step.

The same charset applies to `scans/<object>/` directory names — `scan_reference.py` validates it before installing. `scans/**/*.stl` is the one carve-out from the `*.stl` gitignore: scan reference meshes are captured input data, not build output, and are the only committed STLs in the repo (#439). See `scans/README.md`.

## XSS / HTML safety

All dynamic content in `index.html`, `embed.html`, and standalone viewers that interpolates model names, filenames, or other data into the DOM must use the DOM API (`createElement`/`textContent`/`setAttribute`). Never use `innerHTML` for user-derived data.

For standalone HTML viewers, `scripts/generate-standalone.py` embeds filament color data inside a `<script>` block. The `_load_filament_colors_js()` function applies two escaping layers:
1. `json.dumps(name)` — handles `"`, `\`, control characters
2. Unicode escapes for `<`, `>`, `&` → `<`, `>`, `&`

Both layers are required. Do not regress either. Covered by `scripts/test_generate_standalone.py`.

## Third-party runtime JS

The deployed viewers must load Three.js from `./vendor/three/<version>/` —
staged same-origin and SHA-256-verified by `scripts/fetch_threejs.py` (issue
#403). Never reintroduce a CDN URL into the import maps in `index.html` or
`embed.html`; `_check_threejs_version()` hard-fails the build if either import
map stops referencing the vendor path. The pinned version and the three asset
hashes live in exactly one place — `scripts/threejs_assets.py` — and
`scripts/generate-standalone.py` inlines the same verified bytes.

## Slugify invariant

The `slugify()` function — strip `.stl`, replace `[_\s]+` with `-`, lowercase — must remain identical across all four locations:

- `index.html`
- `embed.html`
- `scripts/oembed_helpers.py`
- `scripts/generate-gallery.py`

If you change one, change all four in the same PR.

`.github/workflows/build.yml`'s "Generate QR codes" step consumes `slugify()` by importing it from `scripts/oembed_helpers.py`. Never re-derive slugs with `sed`/`tr` in a workflow step — a shell copy is invisible to the parity tests. Pinned by `scripts/test_build_workflow.py::QrSlugifyTests`.

## Public source links

Every model card, embed overlay, and standalone-viewer footer links back to the model's `.scad` source in the **public mirror** at `https://github.com/stjohnb/3d-models` (not the private repo). The `PUBLIC_REPO` constant / `publicSourceUrl()` helper must remain identical across `index.html`, `embed.html`, and `scripts/oembed_helpers.py` (`PUBLIC_REPO_URL` / `public_source_url()`) — the same class of invariant as `slugify()`. If you change one, change all three in the same PR.

## `meta.json` schema

Validated against `meta.schema.json` (JSON Schema draft 2020-12). Only `description` is required. Do not add fields to `meta.json` without updating `meta.schema.json` first.

## `<basename>.parameters.json` manifests

Validated against `parameters.schema.json`. Only `number` and `boolean` types are permitted — never `string`. Strings would require shell quoting when passed via `-D name=value` to OpenSCAD and create injection risk.

## Deferred enforcement pattern

Dependency-graph checks, mesh validation, metadata validation, interference checks, and thumbnail rendering (PNG-signature validation — OpenSCAD can exit 0 while writing a 0-byte file, issue #359) record failures early but only block the build at the final enforcement step. This gives the full pipeline output even when some validations fail. Preserve this pattern when adding new CI validation.

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
- CI runs the same suite as `python3 -m unittest discover -s scripts -p 'test_*.py'` from the repo root; every `scripts/test_*.py` is discovered automatically — never add a module to a hand-maintained list.
- WASM customizer pipeline: `node scripts/test_wasm_customizer.mjs`
- Do not run integration tests or anything requiring Docker or external services locally — CI handles those.

## Automation host policy

Claws agents work on a shared, resource-constrained automation host that also runs the
Claws service itself. When working on this repo as an agent:

- **Do not start dev servers or other long-running processes** (`npm run dev`, `npm start`,
  `docker compose up`, watchers, tunnels). Verify with fast one-shot checks — type-check,
  lint, unit tests — and let CI run anything that needs a live app or an end-to-end browser.
- **Do not install system packages or browser binaries** on the host: no `sudo`, no
  `apt-get install`, no `npx playwright install`, no `brew install`. If CI needs a tool,
  add it to `flake.nix` in the same PR.
- **Never kill a process or free a port you do not own.** `lsof -ti:PORT | xargs kill` and
  `pkill -f node` will take down the Claws service, whose dashboard listens on port 3000.

The OpenSCAD render caps in "Rendering on the constrained build host" below are the
model-specific corollary of the same constraint: this is the machine your renders run on.

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
- `scripts/render_view.py` now routes every render through
  `scripts/capped-openscad.sh` itself (defaults `RENDER_MEM_MAX=2G`,
  `RENDER_TIMEOUT=300`; override either env var to raise the ceiling), so you
  do not need to wrap it by hand — but still keep resolution modest while
  iterating (`-D '$fn=16'`, smaller `--imgsize`).
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
