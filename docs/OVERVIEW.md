# 3D Models — Developer Overview

## Purpose

A collection of 3D-printable models designed in OpenSCAD. A CI pipeline
automatically renders `.scad` source files into downloadable `.stl` files,
generates PNG thumbnails, validates mesh integrity, and deploys an interactive
Three.js viewer to [bstjohn.net/3d-models](https://www.bstjohn.net/3d-models/).

## Repository Structure

```
├── adjustable-bracket/   # Two-piece adjustable bracket with bolt slot
├── blast-gate/           # Inline sliding blast gate for 51mm PVC vacuum lines
├── hex-connector/        # Single-piece hexagonal male-female connector
├── macbook-pro-laptop-stand/  # Parametric vertical laptop dock with swept arch frame
├── nz-ski-fields/        # Topographic terrain model of the NZ ski-fields region (3-part split)
├── power-workshop/       # Fisher-Price Power Workshop replacement parts
├── sink-tray/            # Sink tray foot
├── toothbrush/           # Toothbrush/toothpaste holder system
├── vacuum-hose/          # Vacuum hose fittings (adapter and reducer)
├── ideas/                # Feature ideas, rejected patterns, and cross-project learnings
├── scripts/
│   ├── scad-dep-graph.sh       # Generates per-project Mermaid dependency graphs
│   ├── generate-standalone.py  # Generates self-contained single-file HTML viewers
│   ├── generate-gallery.py     # Generates README model gallery from models.json
│   ├── oembed_helpers.py       # Shared Python helpers (slugify, parse_scad_map, load_meta_failures, etc.)
│   ├── test_oembed_helpers.py  # Tests for oembed_helpers
│   ├── check_interference.py   # Geometric overlap detection for mating part pairs (meta.json mating_pairs)
│   ├── test_check_interference.py  # Tests for check_interference
│   ├── fetch_openscad_wasm.py  # Fetches pinned openscad-wasm release into .cache/ and stages to site/openscad/
│   ├── test_fetch_openscad_wasm.py # Tests for fetch_openscad_wasm (mocks urllib, verifies zip parsing)
│   ├── fetch_terrain_heightmap.py  # One-off generator: fetch a lat/lon terrain heightmap PNG (Mapzen terrarium tiles via AWS Open Data); not used by CI
│   ├── test_fetch_terrain_heightmap.py # Tests for fetch_terrain_heightmap (mocks requests, verifies slippy math and decode)
│   ├── generate_lake_bed.py        # One-off generator: bake lakebed bathymetry PNG from heightmap for nz-ski-fields; not used by CI
│   ├── render_view.py          # Render an arbitrary OpenSCAD view to PNG (developer/agent tool, not used by CI)
│   ├── test_render_view.py     # Tests for render_view
│   ├── render_cache.py         # Content-addressed render cache key computation (used by CI render step)
│   ├── test_render_cache.py    # Tests for render_cache
│   ├── test_generate_standalone.py  # Regression tests for _load_filament_colors_js HTML injection escaping
│   ├── test_wasm_customizer.mjs  # Node.js integration test for the in-browser WASM customizer pipeline
│   ├── sync_public_snapshot.py  # Builds a sanitized public snapshot for stjohnb/3d-models; not used by CI
│   └── test_sync_public_snapshot.py  # Tests for sync_public_snapshot
├── filament-colors.json  # Shared color palette (single source of truth)
├── index.html            # Single-page 3D viewer (deployed to S3)
├── embed.html            # Minimal single-model viewer for iframe/OEmbed embedding
├── openscad-worker.js    # Web Worker — runs openscad-wasm renders off the main thread
├── favicon.svg           # SVG site favicon — dark background cube glyph; deployed to site/
├── site.webmanifest      # Web app manifest (PWA metadata: name, theme, icons); deployed to site/
├── robots.txt            # Served at /3d-models/robots.txt (authoritative crawlers copy needs origin-root infra)
├── llms.txt              # AI agent discoverability file; served at /3d-models/llms.txt
├── meta.schema.json      # JSON Schema for per-project meta.json files
├── parameters.schema.json  # JSON Schema for per-model parameter manifests (<basename>.parameters.json)
├── CLAUDE.md             # Claude guidance: conventions, invariants, and doc pointers for AI agents
├── .claude/
│   └── agents/
│       ├── issue-refiner.md      # Subagent: refines GitHub issues into implementation plans
│       ├── issue-implementer.md  # Subagent: implements approved plans while preserving CI invariants
│       └── pr-reviewer.md        # Subagent: reviews PR diffs against CI-enforced invariants
├── playbooks/
│   └── iterate_with_render_view.md  # How to use render_view.py for iterative local design
├── .github/workflows/
│   ├── build.yml             # CI: render, validate, thumbnail, deploy
│   └── notify-failures.yml   # Monitors build.yml; opens/closes failure issues on main
└── docs/
    ├── OVERVIEW.md             # This file — main entry point
    ├── model-projects.md       # Per-project file tables, geometry, and key parameters
    ├── web-viewer.md           # Detailed index.html/embed.html/standalone/OEmbed reference
    ├── ci-pipeline.md          # Detailed CI/CD pipeline step-by-step documentation
    ├── OPENSCAD_LIBRARIES.md   # Catalogue of available third-party OpenSCAD libraries
    ├── claws-automation.md     # How the Claws automation service manages issues, PRs, and docs (auto-maintained)
    ├── blog-post.md            # Draft blog post about the project
    ├── website-checklist-audit.md  # specification.website checklist audit
    └── public-snapshot.md      # Policy and usage guide for sync_public_snapshot.py
```

Each model project has its own top-level directory containing `.scad` source
files and a `meta.json` metadata file. STL outputs are gitignored — they are
generated artifacts produced by CI.

## Model Projects

| Project | Summary |
|---|---|
| `adjustable-bracket/` | Two interlocking pieces (M5 bolt through adjustment slot), span ~125–155mm |
| `blast-gate/` | Sliding blast gate for 51mm OD PVC vacuum lines; related to `vacuum-hose` |
| `hex-connector/` | Single-piece hex male/female connector, 30mm tall, loose press fit |
| `macbook-pro-laptop-stand/` | Vertical laptop dock with swept arch ribbons and a slot the laptop slides into |
| `nz-ski-fields/` | Topographic NZ terrain model split into three separately-printable parts (lake/terrain/snow) |
| `power-workshop/` | Fisher-Price Power Workshop replacement parts sharing a square-peg connection |
| `sink-tray/` | Single-file sink tray foot with counterbore |
| `toothbrush/` | Multi-part holder system with dovetail-attached clips and a removable drip tray |
| `vacuum-hose/` | Adapter and reducer fittings for workshop dust collection hose |

Full per-project file tables, geometry conventions, coordinate systems, and
key parameters live in [model-projects.md](model-projects.md).

## Key Patterns

### Library vs. Renderable Files

There are two kinds of `.scad` files:

- **Library files** define shared parameters and modules but produce no
  top-level geometry. They are included by other files via `include <file.scad>`.
  CI skips these during STL rendering using three detection methods:
  underscore-prefixed filenames (`_*.scad`) are skipped by convention,
  OpenSCAD's "top level object is empty" log output catches the rest, and a
  fallback heuristic handles edge cases where the output STL is empty.

- **Renderable files** either contain top-level geometry directly or
  `include`/`use` a library and call a specific module. Each renderable file
  produces one `.stl`.

### External Libraries

The repository currently uses **no third-party OpenSCAD libraries** — every
`.scad` is self-contained. A curated catalogue of available libraries (from
openscad.org) lives in [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md). When
planning a new model, scan that list before re-implementing common patterns
(rounded corners, threads, hinged enclosures, fastener specs).

### Dependency Graph

A visual map of `include` / `use` relationships between `.scad` files is
maintained in each project's `dependency-graph.md` (e.g.,
`power-workshop/dependency-graph.md`). These are generated by
`scripts/scad-dep-graph.sh` and CI verifies they stay current. Projects
with no inter-file dependencies do not get a graph. Library nodes use
stadium-shaped Mermaid nodes to visually distinguish them from renderable
files.

### Project Metadata (`meta.json`)

Each project directory contains a `meta.json` file validated against
`meta.schema.json` (JSON Schema draft 2020-12). The `description` field is
required; all other fields are optional. CI validates all `meta.json` files
at the start of the pipeline using the **deferred enforcement** pattern —
failures are recorded but don't block the build until the final enforcement
step. Invalid `meta.json` files are tracked in `.meta-failures` and excluded
from downstream consumption (models.json, structured data).

| Field | Type | Description |
|-------|------|-------------|
| `description` | `string` (required) | Human-readable project description |
| `tags` | `array` of `string` | Categories for filtering (e.g., `"toy-parts"`, `"organizer"`) |
| `version` | `string` (semver) | Version string (`^\d+\.\d+\.\d+$`) |
| `license` | `string` | SPDX identifier override (repo default implied when absent) |
| `difficulty` | `enum` | `"beginner"`, `"intermediate"`, or `"advanced"` |
| `hardware` | `array` of `{item, quantity, notes?}` | Bill of materials for non-printed parts |
| `relatedModels` | `array` of `string` | Directory names of related projects |
| `mating_pairs` | `array` of 2-element `string` arrays | Pairs of STL filenames that must fit without geometric overlap (validated by `check_interference.py`) |
| `complex_interior` | `boolean` | When `true`, CI renders three extra orthographic views (`_top`, `_bottom`, `_front`) to expose internal cavity geometry; currently only `power-workshop` uses this |

Metadata is merged into `models.json` at build time. Only viewer-relevant
fields are propagated (`description`, `tags`, `difficulty`, `version`,
`hardware`). `license`, `relatedModels`, and `mating_pairs` are intentionally
excluded from the manifest.

The manifest also includes a `rendered_with` field per model entry in the manifest,
recording the OpenSCAD version used to produce the STLs in that CI run
(e.g., `"OpenSCAD 2024.12.06"`). This is sourced from the runner's
`openscad --version` output captured by the version-check step. It serves
as diagnostic documentation — if a printed part doesn't fit, `rendered_with`
helps determine whether the issue is a source change or a renderer regression.
The committed `.openscad-version` file stores the expected version baseline;
CI warns when the runner's version drifts from it.

### Shared Connection Pattern (power-workshop)

All `power-workshop` attachments share a square-peg connection defined once
in `_connection.scad` (male shaft + collar, female socket + snap ridge) and
composed on top by each attachment file. Beveled-transition conventions
(`hull()` between thin extrusions) and the `drill_socket.scad` parameter
overrides are documented in [model-projects.md](model-projects.md#power-workshop).

### Multi-Part Assembly Pattern (toothbrush, adjustable-bracket)

Complex models split into:
1. A **shared library** with all parameters and modules
2. **Individual render files** that `include`/`use` the library and call one module
3. **Test print files** that orient parts for printing (e.g., dovetail face down)
4. **Assembly files** that combine parts for preview in the viewer

### Dovetail Joint System (toothbrush)

The toothbrush holder uses dovetail rails on the backplate and matching channels
on clip pieces. Clips slide onto the backplate from the top and are stopped by
a block at the rail bottom. A `dt_clearance` parameter (0.15 mm) controls
print fit tolerance.

### Parametric Design Convention

All dimensions are declared as named variables at the top of each file with
unit comments (mm). Derived dimensions are computed from base parameters.
Physical measurements taken with calipers are noted in comments.

### In-Browser Parametric Customization

Renderable models can ship a sibling `<basename>.parameters.json` manifest
that exposes a subset of their OpenSCAD variables as live controls in the
gallery viewer. The schema (`parameters.schema.json`) restricts parameter
types to `number` and `boolean` — strings are forbidden so values can be
spliced into `-Dname=value` argv without shell-quoting fragility. CI
validates every manifest against the schema using the same deferred
enforcement pattern as `meta.json`; failures go into `.param-failures`
and exclude the manifest from `models.json`.

The customizer is purely additive: the default precomputed STL still
loads instantly on page open and is what shows up in the unmaximized
card. Clicking the **⚙ Customize** button lazy-loads
[openscad-wasm](https://github.com/openscad/openscad-wasm) (~5 MB
non-threaded build, fetched from `site/openscad/`), pulls every `.scad`
in the project's directory from `site/sources/<project>/` (discovered
via a per-directory `manifest.json`), writes them into the wasm FS, and
renders into an in-memory STL when the user clicks **⟳ Re-render**. The
Three.js viewer's mesh is swapped via `replaceMesh()` and the result is
offered as a "Download customized STL" Blob URL. Customized STLs are
never persisted server-side — they live only in the current tab.

Rendering runs in a dedicated Web Worker (`openscad-worker.js`) shared
by every card on the page. CGAL booleans and STL export happen off the
main thread, so dragging the 3D view or scrolling the page stays
responsive even mid-render. The worker processes messages sequentially
(single-threaded wasm), and the resulting STL bytes are posted back as
a transferable `Uint8Array` to avoid copies.

Re-rendering is **explicit**, not automatic: editing a slider or
checkbox updates the displayed value and highlights the changed row,
but the new geometry isn't generated until the user clicks **⟳
Re-render** (or presses `R` with the card focused). This lets users
adjust several parameters at once and pay the render cost just once.
The first opening of the panel still kicks off an initial render at the
defaults so the customizer-driven mesh appears immediately.

Known limitations: the non-threaded WASM build is single-threaded and
noticeably slower than native OpenSCAD (expect 0.5–3s per render for
small parts); first use adds a ~5 MB asset download; complex models or
extreme parameter values may take several seconds. Concurrent renders are not possible: clicking Re-render while a render is
in flight is a no-op (the in-flight render continues and its result is
applied when it completes). If openscad-wasm fails to load or
a render fails, the precomputed STL remains visible — graceful
degradation is automatic.

Manifests currently ship for `adjustable-bracket` (`piece_a`, `piece_b`),
`blast-gate` (`gate_body`, `gate_blade`), `hex-connector` (`hex_connector`),
`macbook-pro-laptop-stand` (`laptop_stand`),
`nz-ski-fields` (`lake`, `terrain`, `snow`),
`sink-tray` (`tray_foot`), and `vacuum-hose` (`adapter`, `reducer`). Adding one
for a new model is just a matter of dropping a `<basename>.parameters.json` next
to the renderable `.scad`; CI picks it up automatically.

Binary assets referenced via `surface()` or `import()` (e.g.
`heightmap.png` in `nz-ski-fields`) are staged to
`site/sources/<project>/`, listed in `manifest.json`, and fetched as
`Uint8Array` so they can be written into the wasm FS as raw bytes.

### Viewer Rotation

OpenSCAD uses Z-up coordinates; the Three.js viewer expects Y-up. Files
intended for the web viewer apply `rotate([-90, 0, 0])` at the top-level
assembly.

This is applied selectively: dedicated assembly/preview files
(`gate_assembly.scad`, `Toothbrush assembly.scad`), tube-shaped models that
look awkward in Z-up orientation (`vacuum-hose/adapter.scad`,
`vacuum-hose/reducer.scad`), and terrain/surface models (`nz-ski-fields/lake.scad`,
`nz-ski-fields/terrain.scad`, `nz-ski-fields/snow.scad`)
apply it. Individual power-workshop attachment files (`flathead_attachment.scad`,
`drill_bit.scad`, etc.) do **not** apply it — they are oriented peg-down
(Z-up), matching their natural print orientation. Symmetric or upright models
(`hex-connector`, `sink-tray`, `macbook-pro-laptop-stand`) also omit it.

## Iterative Design Helpers

Utilities for use during active design work — not part of the CI pipeline.

### Rendering arbitrary views

When iterating on a model, render any view of any `.scad` file without going through CI.

```bash
# Top-down view into cavity openings
python3 scripts/render_view.py power-workshop/drill_socket.scad --view top -o /tmp/top.png

# Custom camera angle with explicit gimbal coordinates
python3 scripts/render_view.py power-workshop/drill_socket.scad --camera=0,0,0,75,0,25,500 --projection=perspective -o /tmp/custom.png
```

Available `--view` presets: `iso` (default), `top`, `bottom`, `front`, `back`, `left`, `right`, `custom`.
Pass `--camera=tx,ty,tz,rx,ry,rz,dist` to use an arbitrary angle; this implies `--view custom`.
Additional options: `--imgsize WxH`, `--projection ortho|perspective`, `--no-viewall`, `-D VAR=VALUE` (repeatable).

For files that apply `rotate([-90, 0, 0])` at the top level for the web viewer (see "Viewer Rotation" above —
`gate_assembly.scad`, `Toothbrush assembly.scad`, `vacuum-hose/adapter.scad`, `vacuum-hose/reducer.scad`,
`nz-ski-fields/lake.scad`, `nz-ski-fields/terrain.scad`, `nz-ski-fields/snow.scad`),
pass `--y-up` so the named view presets refer to the correct semantic axes.

This script is **not** used by CI and produces no build artifacts.

## Web Viewer (index.html)

A single-page application (no build tools, no framework, ES module JS,
Three.js from a CDN via import map) that fetches `models.json`, renders
each STL in an interactive canvas, and provides download/source links, a
filament color picker, cross-section and maximize views, QR codes, deep
linking, keyboard navigation, and full accessibility support. `embed.html`
is a minimal single-model variant for iframe/OEmbed embedding; CI also
generates self-contained standalone HTML viewers (`site/standalone/`) and
per-model OEmbed JSON endpoints (`site/oembed/`).

Every feature — core functionality, the XSS-safety convention, print-time
estimates, lazy loading, filament colors, 3D controls, cross-section view,
maximize preview, deep links, QR codes, touch gesture hints, and
accessibility — is documented in detail in [web-viewer.md](web-viewer.md).

## Slugify Convention

A consistent `slugify()` function is used across all JS and Python code:
strip `.stl` extension, replace `[_\s]+` with `-`, lowercase. This must
stay in sync across `index.html`, `embed.html`, `scripts/oembed_helpers.py`,
and `scripts/generate-gallery.py`. The shared Python implementation lives
in `scripts/oembed_helpers.py`.

## Auto-Generated README Gallery

The `README.md` model gallery (between `<!-- gallery:start -->` and
`<!-- gallery:end -->` markers) is auto-generated by
`scripts/generate-gallery.py` on every main-branch push. The script reads
`site/models.json` and per-project `meta.json` descriptions to build a
thumbnail table. On PRs, the gallery script is smoke-tested (run then
reverted) to catch breakage. The CI commits the updated README with
`[skip ci]` to prevent infinite loops.

## Playbooks

Reusable how-to guides for common development tasks live in `playbooks/`.

- **`playbooks/iterate_with_render_view.md`** — how to use `render_view.py` for
  rapid visual inspection across multiple angles during active model design.
  Covers view presets, the `--y-up` flag for assemblies, and an explicit list of
  what `render_view.py` does _not_ do (mesh validation, interference checks,
  bounding-box extraction — those are CI-only gates).

## AI Agent Configuration

`CLAUDE.md` at the repo root provides Claude with concise guidance on the
conventions and invariants to preserve. It points Claude to the authoritative
docs and lists things never to do (use GitHub-hosted runners, add `innerHTML`
for user data, hand-edit generated artifacts, etc.).

**Claws automation** — an autonomous agent service — manages issues, PRs, and
documentation for this repo using the subagents below. See
[claws-automation.md](claws-automation.md) for details.

Three subagent definitions live in `.claude/agents/`:

- **`issue-refiner`** — reads the docs and `ideas/rejected.md`, then produces a
  detailed implementation plan for a GitHub issue before any code is written.
  For new models it names exact filenames, decides the library/renderable split,
  and calls out viewer-rotation and parameter-manifest requirements.
- **`issue-implementer`** — executes an approved plan literally. It reads all
  referenced files before editing and enforces every CI invariant (runner labels,
  filename charset, slugify parity, XSS safety, deferred enforcement pattern,
  no hand-edits to generated artifacts).
- **`pr-reviewer`** — reviews a PR diff against the plan it implements and against
  the CI-enforced invariants (runner labels, filename charset, slugify parity,
  XSS safety, schema-validated metadata, deferred enforcement pattern). Flags
  anything that hand-edits generated artifacts or adds scope beyond the plan.

## CI/CD Pipeline

See [ci-pipeline.md](ci-pipeline.md) for detailed documentation.

**Summary**: On push to `main` or PR, the pipeline (`build.yml`) runs on a
**self-hosted Linux runner** (`[self-hosted, linux]`), verifies dependency graphs, validates project metadata,
installs tools (OpenSCAD, ImageMagick, ADMesh, qrencode, zip), prepares the
Xvfb environment (clears stale X lock files from prior interrupted runs),
renders all `.scad` files to STL (using `--export-format binstl` for binary
output), validates mesh integrity (including bounding-box extraction for
print-time estimates), checks mating part interference for pairs declared in
`meta.json`'s `mating_pairs` field (using `trimesh` and `manifold3d` to detect
geometric overlap — stored as `interference.json`, with CI warning annotations
and PR comment table), generates standalone HTML viewers, bundles multi-file
projects into zip archives, generates PNG thumbnails, renders extra orthographic
views for models with `complex_interior: true` in their `meta.json`, generates
QR codes, composites an OG hero image, builds `models.json` (with metadata,
print times, and QR references), generates a `sitemap.xml` listing the
gallery and all standalone viewer URLs, generates the README gallery, builds
Schema.org structured data and OEmbed endpoints, and deploys to S3. PRs get preview deployments and an
auto-generated comment showing thumbnails, file sizes, triangle counts, mesh
validation results, and interference check results for changed models.
Dependency graph checks, mesh validation, metadata validation, and
interference checks all use a **deferred enforcement** pattern — failures are
recorded early but only block the build at the very end, so the full pipeline
output is always available.

A separate **`notify-failures.yml`** workflow monitors for `build.yml` failures
on `main`. On failure it opens a `bug` issue (deduplicated — one open issue at
a time). On the next successful run it auto-closes the issue with a recovery
comment.

## Configuration

| Item | Location | Notes |
|------|----------|-------|
| CI runner | `[self-hosted, linux]` in `build.yml` and `notify-failures.yml` | Expects OpenSCAD, ImageMagick, ADMesh, qrencode, zip, xvfb, Python 3, AWS CLI |
| OpenSCAD version baseline | `.openscad-version` | Committed expected version string; CI warns on mismatch |
| AWS deployment role | `secrets.AWS_ROLE_ARN` | OIDC role for S3 sync |
| S3 bucket path | `s3://www.bstjohn.net/3d-models/` | Production deployment target |
| PR preview path | `s3://…/pr-preview/pr-{N}/{SHA}/` | Per-PR, per-commit previews |
| Source zip naming | `site/<dir>-source.zip` | Per-project zip of git-tracked source files; referenced as `sourceZip` in `models.json` |
| Three.js version | `0.170.0` (CDN import map in `index.html`) | STLLoader + OrbitControls; also pinned in `generate-standalone.py` with SHA-256 verification |
| OpenSCAD resolution | `$fn = 64` | Set per-file in `.scad` sources |
| Thumbnail size | `800x600` | Set in build.yml render step |
| OG hero image | `og-hero.png` (1200x630) | Composited by CI; stable URL, not cache-busted |
| Structured data | `<!-- __STRUCTURED_DATA__ -->` in `index.html` | Replaced by CI with Schema.org JSON-LD |
| OEmbed links | `<!-- __OEMBED_LINKS__ -->` in `index.html` | Replaced by CI with `<link rel="alternate">` tags |
| Filament colors | `filament-colors.json` | 8 preset colors; Blue is default. Single source of truth loaded by `index.html` at runtime and injected into standalone viewers at build time by `generate-standalone.py` |
| Touch hint timeout | 5000 ms in `showTouchHint()` | Fade-out delay for gesture overlay |
| Zip bundle threshold | 2+ STL files per project | Single-file projects don't get an STL zip; all projects get a source zip |
| Lazy-load margin | `rootMargin: '200px'` | IntersectionObserver pre-loads 200px before viewport |
| Deep link format | `#project-slug/model-slug` | URL hash routing for per-model links |
| QR code style | `-s 8 -m 2`, `E0E0E0` on `1A1A2E` | Module size 8, margin 2, dark theme colors |
| Print-time heuristic | 0.2mm layers, 50mm/s, 5x multiplier | Conservative defaults; volume fallback for flat models |
| Metadata schema | `meta.schema.json` (JSON Schema draft 2020-12) | Validated in CI; `description` required, all others optional |
| README gallery markers | `<!-- gallery:start -->` / `<!-- gallery:end -->` | Auto-replaced by `scripts/generate-gallery.py` |
| Standalone viewer cache | `.cache/threejs/` | Local cache for Three.js CDN assets |
| Render cache | `$HOME/.cache/3d-models/render` (override `RENDER_CACHE_DIR`, disable `RENDER_CACHE_DISABLED=1`) | Host-level content-addressed STL cache; key = SHA-256 over transitive include/use chain + binary assets + OpenSCAD version + `CACHE_VERSION` via `scripts/render_cache.py`; pruned at 30 days by mtime |
| Interference check | `mating_pairs` in `meta.json` | Pairs of STL filenames validated by `check_interference.py` using `trimesh` + `manifold3d` |
| Interference threshold | overlap volume > 0 | Any geometric overlap between mating parts is a failure |
| Interference output | `site/interference.json` | Per-pair results with overlap volume in mm³, shown in PR comment table |
| Parameter manifest schema | `parameters.schema.json` (JSON Schema draft 2020-12) | Validated in CI; only `number` and `boolean` types permitted; strings forbidden to avoid `-D` shell-quoting issues |
| openscad-wasm version | `scripts/fetch_openscad_wasm.py` | Pinned to release `2022.03.20` (non-threaded build, no COOP/COEP headers required); staged into `site/openscad/` with SHA-256 verification |
| Source staging | `site/sources/<project>/` | All `.scad` files, validated manifests, and binary render assets (`.png` files whose basename appears in a sibling `.scad`) copied here by CI; per-project `manifest.json` lists `.scad` and `.png` filenames for browser discovery |
| External libraries | none vendored | See [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md) for a catalogue of available libraries |
| Favicon | `favicon.svg` (repo root) | SVG cube glyph on `#1a1a2e`; copied to `site/favicon.svg` by CI |
| Web app manifest | `site.webmanifest` (repo root) | PWA metadata; copied to `site/site.webmanifest` by CI |
| robots.txt | `robots.txt` (repo root) | Served at `/3d-models/robots.txt`; crawler-authoritative copy requires origin-root infra |
| llms.txt | `llms.txt` (repo root) | AI agent discoverability; served at `/3d-models/llms.txt`; same sub-path caveat |
| sitemap.xml | Generated by CI "Generate sitemap.xml" step | Lists gallery root + all standalone viewer URLs; deployed to `site/sitemap.xml` |
