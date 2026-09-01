# 3d-models

This repo is a collection of 3D-printable OpenSCAD models plus the tooling that
renders them, validates them, and publishes an interactive Three.js gallery at
`bstjohn.net/3d-models`. Most changes touch either model geometry, the CI/build
pipeline, or the web viewer that serves the generated artifacts.

## Where to read first

- Start with `docs/OVERVIEW.md` for architecture, key patterns, configuration,
  and links to the owning docs for each subsystem.
- Read the owning doc before editing that subsystem: `docs/ci-pipeline.md` for
  CI/build work, `docs/model-projects.md` for model geometry and per-project
  conventions, `docs/web-viewer.md` for `index.html`/`embed.html`, and
  `docs/claws-automation.md` for issue/PR lifecycle details.
- Read `docs/OPENSCAD_LIBRARIES.md` before proposing new model geometry that
  might duplicate an existing library.
- Read `ideas/rejected.md` before proposing a new pattern or workflow; do not
  re-propose ideas the maintainer has already declined.
- `CLAUDE.md` is a compatibility copy of this file's content, kept for tools
  and docs that still reference specific named sections there (e.g.
  `flake.nix`, `index.html`). If a rule below doesn't have enough detail,
  check `CLAUDE.md` for the fuller version.

All changes land via pull request; nothing is pushed directly to the default
branch. See `docs/claws-automation.md` for the full convention.

## Key conventions

- Do not hand-edit generated artifacts such as `models.json`, `site/oembed/**`,
  `site/standalone/**`, README gallery output, per-project
  `dependency-graph.md`, or CI-rendered STL/PNG outputs.
- This repo is often worked on from a shared automation host: do not start dev
  servers, install system packages, or kill processes you do not own; use
  one-shot checks and leave heavy/integration work to CI.
- CI workflows must use self-hosted runners with an OS label:
  `runs-on: [self-hosted, linux]` or `runs-on: [self-hosted, macos]`. Never use
  GitHub-hosted Linux or Windows runners, and never use bare
  `runs-on: self-hosted`.
- Preserve `build.yml`'s `runs-on: [self-hosted, linux, ryzen]` pin. The render
  memory caps are calibrated to that host class.
- CI tools are repo-owned: beyond the runner baseline (`nix`, `git`, `docker`),
  every tool a workflow shells out to must come from this repo's `flake.nix`
  devShells, entered via `nix develop`. Do not add `apt`, `sudo`,
  `actions/setup-node`, `actions/setup-python`, `nix-env`, or hard-coded
  `/nix/store` paths to workflows.
- `.scad` basenames must stay within `[A-Za-z0-9._ -]`. Renderable
  non-underscore basenames must be unique across projects, and within a
  project no two renderables may collide after slugification.
- Library `.scad` files are underscore-prefixed and must produce no top-level
  geometry. Each renderable `.scad` must produce exactly one STL.
- Keep OpenSCAD sources in native Z-up. Do not add top-level
  `rotate([-90, 0, 0])` to compensate for the viewer; the viewers handle the
  Z-up to Y-up conversion centrally.
- Dynamic viewer content derived from model names, filenames, metadata, or
  manifests must use DOM APIs, not `innerHTML`.
- The `slugify()` rule must stay identical across `index.html`, `embed.html`,
  `scripts/oembed_helpers.py`, and `scripts/generate-gallery.py`: strip `.stl`,
  replace `[_\\s]+` with `-`, and lowercase.
- The `PUBLIC_REPO` constant / `publicSourceUrl()` helper (source links back
  to `https://github.com/stjohnb/3d-models`) must stay identical across
  `index.html`, `embed.html`, and `scripts/oembed_helpers.py`
  (`PUBLIC_REPO_URL` / `public_source_url()`) — the same class of invariant as
  `slugify()`. If you change one, change all three in the same PR.
- If you touch standalone viewer filament-color injection in
  `scripts/generate-standalone.py`, preserve both escaping layers:
  `json.dumps(...)` and the `<`, `>`, `&` unicode escapes. Both are required.
- `*.parameters.json` manifests only permit `number` and `boolean` parameter
  types. Never add `string`.
- Preserve the deferred-enforcement CI pattern: dependency-graph checks, mesh
  validation, metadata validation, interference checks, and related validation
  steps record failures early and block only at the end of the pipeline.

## Testing

- Run `python3 -m pytest scripts/` after Python script changes.
- Run `node scripts/test_wasm_customizer.mjs` after customizer-pipeline changes.
- Do not run integration tests, end-to-end browser tests, Docker-dependent
  checks, or other heavy/long-running processes on the shared host; CI handles
  those.

## Shared automation host policy

Claws agents work on a shared, resource-constrained automation host that also
runs the Claws service itself. When working on this repo as an agent:

- Do not start dev servers or other long-running processes (`npm run dev`,
  `npm start`, `docker compose up`, watchers, tunnels). Verify with fast
  one-shot checks such as type-checks, lint, and unit tests, and let CI run
  anything that needs a live app or an end-to-end browser.
- Do not install system packages or browser binaries on the host: no `sudo`,
  no `apt-get install`, no `npx playwright install`, no `brew install`. If CI
  needs a tool, add it to `flake.nix` in the same PR.
- Never kill a process or free a port you do not own. `lsof -ti:PORT | xargs
  kill` and `pkill -f node` can take down the Claws service, whose dashboard
  listens on port 3000.

The OpenSCAD render caps below are the model-specific corollary of the same
constraint: this is the machine your renders run on.

## Rendering on the constrained build host

When validating a model locally during issue work, you are running on a
memory-constrained shared automation host. A full-resolution STL export of a
complex or procedural model can freeze the host. Full-resolution STL renders
are CI's job; local work should stay focused on cheap geometry sanity checks.

- Never run a bare `openscad ... -o foo.stl`. Always cap memory and time:
  `systemd-run --user --scope -p MemoryMax=1G -- timeout 300 openscad ...`
  or `( ulimit -v 1500000; timeout 300 openscad ... )` if `systemd-run` is
  unavailable.
- Prefer cheap checks over full exports while iterating:
  `openscad --export-format csg -o /dev/null file.scad` validates syntax and
  evaluates the model without meshing; render a low-`$fn` preview before any
  full STL export.
- Keep `$fn` / `$fa` / `$fs` modest while iterating. Committed sources still
  use their normal values; lower them only in throwaway local checks.
- Do not render multiple models concurrently.
- `scripts/render_view.py` already routes renders through
  `scripts/capped-openscad.sh` (`RENDER_MEM_MAX=2G`,
  `RENDER_TIMEOUT=300` by default). You still need to keep preview resolution
  modest while iterating (`-D '$fn=16'`, smaller `--imgsize`).
- If a render is OOM-killed or times out, treat it as "too heavy for this
  host". Reduce geometry or resolution, or leave the full render to CI instead
  of retrying blindly.
