# 3D Models — Developer Overview

## Doc map

| Doc | Read this when | Depth |
|---|---|---|
| [OVERVIEW.md](OVERVIEW.md) (this doc) | Starting any task in this repo | Entry point |
| [model-projects.md](model-projects.md) | Adding or editing a model, need per-project file tables, geometry, or parameters | Reference |
| [web-viewer.md](web-viewer.md) | Working on `index.html`, `embed.html`, standalone viewers, or OEmbed | Reference |
| [ci-pipeline.md](ci-pipeline.md) | Touching `build.yml` or any CI/build step | Reference |
| [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md) | Proposing new model geometry; check before reimplementing a common pattern | Reference |
| [claws-automation.md](claws-automation.md) | Understanding how Claws manages this repo's issues, PRs, and labels | Reference |
| [requirements.md](requirements.md) | Cross-cutting process/workflow requirements not owned by any subsystem doc | Reference |
| [agent-notes.md](agent-notes.md) | Need a durable operator/CI/automation gotcha not tied to one subsystem | Reference |
| [DESIGN.md](DESIGN.md) | Changing `index.html`'s visual design — palette tokens, display face, motion | Deep dive |
| [public-snapshot.md](public-snapshot.md) | Working on the public-mirror sync (`sync_public_snapshot.py`) | Deep dive |
| [website-checklist-audit.md](website-checklist-audit.md) | Checking spec-compliance status against the specification.website checklist | Deep dive |
| [blog-post.md](blog-post.md) | Editing the personal blog draft | Deep dive |

## Purpose

A collection of 3D-printable models designed in OpenSCAD. A CI pipeline
automatically renders `.scad` source files into downloadable `.stl` files,
generates PNG thumbnails, validates mesh integrity, and deploys an interactive
Three.js viewer to [bstjohn.net/3d-models](https://www.bstjohn.net/3d-models/).

## Repository Structure

```
├── adjustable-bracket/   # Two-piece adjustable bracket with bolt slot
├── bench-dog-blank/      # Flush plug for countersunk 18mm bench dog holes, with a pliers-grippable recess for removal
├── bin-foot-opener/      # Toe-operated pull that screws to the inside of a pull-out bin drawer front
├── blast-gate/           # Inline sliding blast gate for 51mm PVC vacuum lines
├── drawer-organiser/     # Gridfinity-compatible drawer organiser: interlocking baseplate tiles, bins, and full-drawer container layout
├── esp32-display-case/   # Two-part snap-fit case for the ESP32-2432S028R display board, w/ stylus holder
├── hex-connector/        # Single-piece hexagonal male-female connector
├── macbook-pro-laptop-stand/  # Parametric vertical laptop dock with swept arch frame
├── nz-ski-fields/        # Topographic terrain model of the NZ ski-fields region (3-part split)
├── power-workshop/       # Fisher-Price Power Workshop replacement parts
├── scanning-rig/         # Photogrammetry rig: hand-rotated turntable + generic leaning phone stand + keyed connecting link with a low rail + camera setback/boost plinth (the stand's only mount) + optional height/angle riser + optional further-setback spacer
├── sink-tray/            # Sink tray foot
├── toothbrush/           # Toothbrush/toothpaste holder system
├── ukulele-wall-hook/    # Single-piece wall-mounted yoke that cradles a ukulele neck
├── vacuum-hose/          # Vacuum hose fittings (adapter and reducer)
├── ideas/                # Feature ideas, rejected patterns, and cross-project learnings
├── scans/                # Watertight reference meshes of scanned real-world objects, as design input; the only committed STLs (see `scans/README.md`)
├── scripts/
│   ├── scad-dep-graph.sh       # Generates per-project Mermaid dependency graphs
│   ├── capped-openscad.sh      # Wraps openscad in a memory + wall-clock cap (CI render steps; issue #272)
│   ├── test_capped_openscad.py # Tests for capped-openscad.sh (mem/timeout cap behavior, exit code propagation)
│   ├── generate-standalone.py  # Generates self-contained single-file HTML viewers
│   ├── generate-gallery.py     # Generates README model gallery from models.json
│   ├── test_generate_gallery.py  # Tests for generate-gallery's pick_thumbnail hero-selection logic (issue #372)
│   ├── oembed_helpers.py       # Shared Python helpers (slugify, parse_scad_map, load_meta_failures, etc.)
│   ├── check_interference.py   # Geometric overlap detection for mating part pairs (meta.json mating_pairs)
│   ├── fetch_openscad_wasm.py  # Fetches pinned openscad-wasm release into $HOME/.cache/3d-models/openscad-wasm/<version>/ and stages to site/openscad/
│   ├── threejs_assets.py       # Single source of truth for the pinned Three.js version and SHA-256 asset hashes
│   ├── fetch_threejs.py        # Fetches the pinned Three.js release into $HOME/.cache/3d-models/threejs/ and stages it same-origin to site/vendor/three/<version>/ with hash verification (issue #403)
│   ├── asset_cache.py          # Host-level download-cache root shared by threejs_assets and fetch_openscad_wasm (issue #460)
│   ├── fetch_terrain_heightmap.py  # One-off generator: fetch a lat/lon terrain heightmap PNG (Mapzen terrarium tiles via AWS Open Data); not used by CI
│   ├── generate_lake_bed.py        # One-off generator: bake lakebed bathymetry PNG from heightmap for nz-ski-fields; not used by CI
│   ├── render_view.py          # Render an arbitrary OpenSCAD view to PNG via capped-openscad.sh (developer/agent tool, not used by CI)
│   ├── scan_pipeline.py        # Photogrammetry CLI: scanning-rig capture video → scaled STL (operator tool, not used by CI)
│   ├── scan_frames.py          # Frame extraction (ffmpeg), sharpness-binned and hold-aware frame selection for scan_pipeline
│   ├── scan_masks.py           # Platter-ellipse + salient-object masking for scan_pipeline (COLMAP mask PNGs); mask-geometry tests skip unless `cv2` is importable (`nix develop .#scan`)
│   ├── scan_colmap.py          # COLMAP/OpenMVS command lines for scan_pipeline (CPU-only: never patch_match_stereo); its test also validates option names against a real colmap when one is on PATH
│   ├── scan_mesh.py            # Platter-plane fit, mm scaling, cropping and STL export for scan_pipeline
│   ├── scan_reference.py       # Watertight, size-budgeted reference meshes from a cleaned scan (convex hull / axis-aware slab-hull union) for scan_pipeline
│   ├── external_assets.py      # Assets a project's .scad files reference from outside the project dir (used by CI's source-zip and parameter-manifest steps)
│   ├── render_cache.py         # Content-addressed render cache key computation (used by CI render step)
│   ├── project_dates.py        # Per-project last-commit dates (models.json `updated`; landing-page recency ordering)
│   ├── test_generate_standalone.py  # Regression tests for standalone-viewer HTML injection escaping (filament colors, SEO head fields, JSON-LD)
│   ├── test_scad_fonts.py      # Pins the no-text()/no-font rule (the deployed openscad-wasm build ships no fonts)
│   ├── test_scad_orientation.py  # Pins the no-top-level-rotate([-90,0,0]) rule (see Viewer Rotation below); one allowlisted exception
│   ├── test_output_names.py    # Pins renderable basename uniqueness across projects and per-project slug uniqueness (issue #449)
│   ├── test_bin_foot_opener.py # Pins bin-foot-opener's relieved-plate geometry (relief_h/relief_t, derived screw-hole placement; issue #492)
│   ├── test_wasm_customizer.mjs  # Node.js integration test for the in-browser WASM customizer pipeline
│   ├── test_hash_routing.mjs    # Node.js test for index.html's parseHash/formatHash URL grammar
│   ├── test_hash_history.mjs    # Node.js test for index.html's hashWriteMode push/replace/skip decision
│   ├── test_landing_order.mjs   # Node.js test for index.html's landing-gallery project ranking
│   ├── test_viewer_invariants.py # Text-level checks on index.html/embed.html (build markers, slugify/PUBLIC_REPO parity, innerHTML)
│   ├── test_build_workflow.py  # Text-level invariant checks on build.yml/flake.nix (ImageMagick font args, no-toolchain-setup-actions, no-Xvfb, EGL pinning); see ci-pipeline.md
│   ├── sync_public_snapshot.py  # Builds a sanitized public snapshot for stjohnb/3d-models; not used by CI
│   └── test_sync_public_snapshot.py  # Tests for sync_public_snapshot; runs in CI's unit-test step
├── README.md             # Project readme; gallery section auto-generated (see below)
├── README.public.md      # Hand-maintained readme; staged as README.md in the public snapshot (stjohnb/3d-models)
├── filament-colors.json  # Shared color palette (single source of truth)
├── .openscad-version     # Committed expected OpenSCAD version baseline; CI warns on drift
├── flake.nix             # Repo-owned CI/dev toolchain (default/scripts/scan devShells); see ci-pipeline.md
├── flake.lock            # Pinned nixpkgs revision consumed by flake.nix
├── index.html            # Single-page 3D viewer: tree browser + 1–3 model panes (deployed to S3)
├── embed.html            # Minimal single-model viewer for iframe/OEmbed embedding
├── openscad-worker.js    # Web Worker — runs openscad-wasm renders off the main thread
├── favicon.svg           # SVG site favicon — dark background cube glyph; deployed to site/
├── site.webmanifest      # Web app manifest (PWA metadata: name, theme, icons); deployed to site/
├── robots.txt            # Served at /3d-models/robots.txt (authoritative crawlers copy needs origin-root infra)
├── llms.txt              # AI agent discoverability file; served at /3d-models/llms.txt
├── meta.schema.json      # JSON Schema for per-project meta.json files
├── parameters.schema.json  # JSON Schema for per-model parameter manifests (<basename>.parameters.json)
├── AGENTS.md             # Canonical root agent instructions: repo summary, read-first docs, and key invariants
├── CLAUDE.md             # Claude compatibility guidance; mirrors key root-agent sections still referenced by docs/tools
├── .agents/
│   ├── issue-refiner.md      # Subagent: refines GitHub issues into implementation plans
│   ├── issue-implementer.md  # Subagent: implements approved plans while preserving CI invariants
│   └── pr-reviewer.md        # Subagent: reviews PR diffs against CI-enforced invariants
├── playbooks/
│   ├── iterate_with_render_view.md  # How to use render_view.py for iterative local design
│   └── scan_a_capture.md            # How to run the photogrammetry pipeline on a scanning-rig capture video
├── .github/
│   ├── dependabot.yml         # Weekly grouped Dependabot updates for the github-actions ecosystem only
│   ├── actions/
│   │   └── setup-nix/
│   │       └── action.yml    # Composite action: puts the runner's system `nix` on PATH or fails fast
│   └── workflows/
│       └── build.yml             # CI: render, validate, thumbnail, deploy
└── docs/
    ├── OVERVIEW.md             # This file — main entry point
    ├── model-projects.md       # Per-project file tables, geometry, and key parameters
    ├── web-viewer.md           # Detailed index.html/embed.html/standalone/OEmbed reference
    ├── DESIGN.md               # Visual design choices for index.html (palette tokens, display face, motion)
    ├── ci-pipeline.md          # Detailed CI/CD pipeline step-by-step documentation
    ├── OPENSCAD_LIBRARIES.md   # Catalogue of available third-party OpenSCAD libraries
    ├── claws-automation.md     # How the Claws automation service manages issues, PRs, and docs (auto-maintained)
    ├── requirements.md         # Cross-cutting process/workflow requirements with no single owning subsystem doc
    ├── agent-notes.md          # Durable operator/automation gotchas verified from current repo behavior
    ├── blog-post.md            # Draft blog post about the project
    ├── website-checklist-audit.md  # specification.website checklist audit
    └── public-snapshot.md      # Policy and usage guide for sync_public_snapshot.py
```

Each model project has its own top-level directory containing `.scad` source
files and a `meta.json` metadata file. STL outputs are gitignored — they are
generated artifacts produced by CI.

Almost every `scripts/*.py` has a matching `scripts/test_*.py`, run by
`python3 -m pytest scripts/`; the tree above only calls out test files
individually when they pin a specific invariant worth knowing about, not for
every routine unit test.

## Model Projects

| Project | Summary |
|---|---|
| `adjustable-bracket/` | Two interlocking pieces (M5 bolt through adjustment slot), span ~125–155mm |
| `bench-dog-blank/` | Flush plug for countersunk 18mm bench dog holes in 18mm plywood, with a recessed pliers-grip bar in the top face for removal |
| `bin-foot-opener/` | Toe-operated pull that screws to the inside face of a pull-out bin drawer front |
| `blast-gate/` | Sliding blast gate for 51mm OD PVC vacuum lines; related to `vacuum-hose` |
| `drawer-organiser/` | Gridfinity-compatible drawer organiser: a 15×10 grid of interlocking 5×5 baseplate tiles covering a 630×424×69mm drawer, plus storage bins, a full-drawer assembly preview, and downloadable bed-splittable container parts |
| `esp32-display-case/` | Two-part snap-fit case for the ESP32-2432S028R ("Cheap Yellow Display") board, with an integrated snap-in stylus holder |
| `hex-connector/` | Single-piece hex male/female connector, 30mm tall, loose press fit |
| `macbook-pro-laptop-stand/` | Vertical laptop dock with swept arch ribbons; single-slot and dual-slot (two laptops side by side) variants |
| `nz-ski-fields/` | Topographic NZ terrain model split into three separately-printable parts (lake/terrain/snow); viewer shows them as a coloured composite assembly |
| `power-workshop/` | Fisher-Price Power Workshop replacement parts sharing a square-peg connection |
| `scanning-rig/` | Fully-printed photogrammetry rig: hand-rotated turntable (V-groove race + centring spindle, no bearings), a generic leaning phone stand (default fits an iPhone 15 Pro, bare or cased), a `rig_link` connecting the two so hand-turning can neither slide the base out from under the fixed masking ellipse nor twist it inside the collar (two keys in the collar bore lock into notches in the base rim), a `scan_boost` plinth standing behind the link's low rail that carries the rig's only stand pocket, an optional `scan_riser` that drops into the boost's own pocket and re-presents an identical one higher up to correct the camera's elevation over the platter without changing the boost, and an optional `scan_setback` spacer that inserts between the link and the boost for another 50mm of setback when the platter still fills the frame |
| `sink-tray/` | Single-file sink tray foot with counterbore |
| `toothbrush/` | Multi-part holder system with dovetail-attached clips and a removable drip tray |
| `ukulele-wall-hook/` | Single-piece wall-mounted yoke with two upturned prongs that cradle a ukulele neck behind the headstock |
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
| `printing_notes` | `array` of `string` | Free-text printer/slicer guidance; surfaced in the viewer, embed, and standalone pages. Deliberately free-text, not structured fields — issue #301 proposed a structured shape and backed off it, citing `ideas/rejected.md`'s prior decline of a "print orientation indicator". Don't re-propose structured printing metadata on the strength of this field alone |
| `relatedModels` | `array` of `string` | Directory names of related projects |
| `mating_pairs` | `array` of 2-element `string` arrays | Pairs of STL filenames that must fit without geometric overlap (validated by `check_interference.py`) |
| `complex_interior` | `boolean` | When `true`, CI renders three extra orthographic views (`_top`, `_bottom`, `_front`) to expose internal cavity geometry; used by `power-workshop` and `drawer-organiser` |
| `hero` | `string` | Rendered STL basename featured as the project's landing-gallery and README thumbnail; defaults to the first STL alphabetically. Set it explicitly on a new multi-model project when there's an obvious representative part, rather than relying on alphabetical luck — standing direction after `scanning-rig`'s thumbnail picked the wrong STL (#372). Deliberately absent for single-model projects and co-equal-parts projects (`adjustable-bracket`, `vacuum-hose`) |
| `assembly` | `object` `{stl, parts}` | Declares that one project STL's viewer card is a coloured multi-part composite rather than a single mesh — see "Composite Multi-Colour Assembly Previews" below; currently only `nz-ski-fields` uses this |

Metadata is merged into `models.json` at build time. Only viewer-relevant
fields are propagated (`description`, `tags`, `difficulty`, `version`,
`hardware`, `hero`, `assembly`, `printing_notes`). `license`, `relatedModels`, and
`mating_pairs` are intentionally excluded from the manifest. **Directory
structure, not metadata, drives UI grouping** — a `group` field was proposed
and rejected once moving files into one directory already produced the
grouping (#196); don't add a metadata field to solve a grouping problem a
directory move already solves.

Two further fields are CI-derived, not hand-maintained in `meta.json`:
`rendered_with` (the OpenSCAD version that produced that CI run's STLs, from
`.openscad-version`/the runner's `openscad --version`, for diagnosing a fit
issue as a source change vs. a renderer regression) and `updated` (the
project directory's last-commit date from `scripts/project_dates.py`, which
needs `build.yml`'s `fetch-depth: 0` checkout — a shallow clone silently
omits it and the landing gallery falls back to interest-only ordering; see
[web-viewer.md](web-viewer.md#landing-gallery)).

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

### Composite Multi-Colour Assembly Previews (nz-ski-fields)

STL export is monochrome, so a merged assembly mesh can't show its parts in
different colours the way an OpenSCAD `color()` preview can. A project can
instead declare an `assembly` object in `meta.json` (`{stl, parts: [{stl,
color}, ...]}`) that tells every viewer to load a set of already-co-registered
part STLs — each in its own fixed colour — into one scene. `nz-ski-fields` is
the only current user (`lake.stl`/`terrain.stl`/`snow.stl`). Full detail,
including the CI-runner-freeze history behind it, is in
[web-viewer.md](web-viewer.md#composite-multi-colour-assembly-previews).

### Dovetail Joint System (toothbrush)

The toothbrush holder uses dovetail rails on the backplate and matching channels
on clip pieces. Clips slide onto the backplate from the top and are stopped by
a block at the rail bottom. A `dt_clearance` parameter (0.15 mm) controls
print fit tolerance.

### Bed-Splitting Pattern for Oversized Parts (nz-ski-fields, drawer-organiser)

When a printable part's footprint exceeds a target print bed, the module that
builds it takes a `split_parts`/`part_index`-style pair of parameters and
returns one re-centred slice via `intersection()` with a keep-box, rather than
shipping the oversized geometry as-is; `drawer-organiser` additionally ships
**dedicated piece renderables** for containers that exceed the print bed, cut
at hand-picked boundaries offset from the baseplate seams underneath so the
pieces glue up flush. Full derivation in
[model-projects.md](model-projects.md#cross-project-patterns).

### Interlocking Tile Seams (drawer-organiser)

Baseplate tiles butt together via a genderless barbed-tab seam (tabs on
+X/+Y edges, matching notches on -X/-Y) so any tile mates with any other tile
of the same edge length. Tabs sit at the centre of each cell, not the
cell-junction corners — a corner placement (issue #309) severed the tile's
perimeter rail. Full derivation and measured tolerances in
[model-projects.md](model-projects.md#cross-project-patterns) and
`drawer-organiser/layout.md`.

### Parametric Design Convention

All dimensions are declared as named variables at the top of each file with
unit comments (mm). Derived dimensions are computed from base parameters.
Physical measurements taken with calipers are noted in comments.

### In-Browser Parametric Customization

Renderable models can ship a sibling `<basename>.parameters.json` manifest
(`number`/`boolean` params only, schema-validated) that exposes a subset of
their OpenSCAD variables as live controls in the gallery viewer. The **⚙
Customize** button lazy-loads openscad-wasm, renders in a dedicated Web
Worker, and swaps the viewer's mesh — the precomputed STL stays the default
and re-rendering is explicit (never automatic), so the customizer degrades
gracefully if wasm fails to load. Adding one for a new model is just dropping
a `<basename>.parameters.json` next to the renderable `.scad`; CI picks it up
automatically. Full architecture, worker details, and known limitations are
in [web-viewer.md](web-viewer.md#in-browser-parametric-customization).

### Viewer Rotation

OpenSCAD uses Z-up coordinates; the Three.js viewers expect Y-up. There is a
single, unconditional rule for reconciling them (issue #382):

- **Every `.scad` source stays in native OpenSCAD Z-up.** Never add a top-level
  `rotate([-90, 0, 0])` for the viewer's benefit.
- **Every viewer applies `geometry.rotateX(-Math.PI / 2)` to every mesh** it
  loads instead — `index.html`, `embed.html`, and the standalone viewers —
  before the bounding-box maths, so camera framing and the cross-section
  slider operate on the corrected axes.

Keeping sources Z-up means the PNG thumbnails CI renders and the STLs users
download for slicing are both correct, while the viewers still show every
model upright. The rule is pinned by `scripts/test_scad_orientation.py` (no
top-level `rotate([-90, 0, 0])` outside its allowlist) and
`test_viewer_invariants.py`'s `ViewerRotationTests`. The **one** allowlisted
exception is `toothbrush/Toothbrush backplate.scad`, a genuine *print*
orientation (it lays an upright module on its back for the bed), not a
viewer hack — see [model-projects.md](model-projects.md#toothbrush) and,
for the reusable "author the profile already print-oriented" pattern,
[model-projects.md](model-projects.md#scanning-rig) (`phone_stand.scad`).

### Scan Reference Meshes (`scans/`)

Real-world objects photographed on the scanning rig can be brought into the
repo as design input, so a model can be built around one — `difference()` a
scanned toothpaste tube out of a holder body (issue #439). A raw scan isn't
directly usable: it's an open shell (not watertight, so OpenSCAD's CSG
rejects it), which `scripts/scan_reference.py` closes into a watertight,
size-budgeted (≤500 KB) reference mesh at `scans/<object>/<object>-reference.stl`.
`*.stl` is gitignored everywhere else, but `scans/**/*.stl` is carved back
out — a scan is *captured input data*, not a reproducible build output, the
same category as `nz-ski-fields/heightmap.png`. Meshes are platter-centred
millimetres and stay Z-up (see Viewer Rotation above). A renderable then
`import()`s one by relative path; `scripts/external_assets.py` bridges the
source-zip and parameter-manifest steps for it, and **a renderable that both
imports a scan and ships a `<basename>.parameters.json` fails validation**
(the in-browser customizer's flat wasm FS can't resolve a `../scans/…`
path). Full contract in `scans/README.md`.

## Iterative Design Helpers

`scripts/render_view.py` renders any view of any `.scad` file to PNG during
active design work, without waiting on CI. It's an *agent-facing* tool by
design, not a persisted-artifact one (#202) — it produces no build artifacts
and is excluded from CI. Renders run under `scripts/capped-openscad.sh`
(`RENDER_MEM_MAX=2G`/`RENDER_TIMEOUT=300` by default). Full usage, view
presets, and what it does *not* check (mesh validation, interference,
bounding-box extraction — CI-only gates) are in
[playbooks/iterate_with_render_view.md](../playbooks/iterate_with_render_view.md).

## Web Viewer (index.html)

A single-page application (no build tools, no framework, ES module JS,
Three.js loaded same-origin via import map) that fetches `models.json` and
presents a tree browser plus a stage of one to three viewer panes, defaulting
to a landing gallery of project cards when nothing is loaded. Deep links use
a `#project-slug/model-slug` hash grammar (`+` joins panes, `,` joins models
within a pane). `embed.html` is a minimal single-model variant for
iframe/OEmbed embedding; CI also generates self-contained standalone HTML
viewers (`site/standalone/`) and per-model OEmbed JSON (`site/oembed/`).
Visual design choices (palette, type, motion) are in [DESIGN.md](DESIGN.md).
Every feature — XSS-safety, the customizer, composite previews, cross-section
view, split panes and focus mode, deep links, QR codes, touch gestures, and
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
- **`playbooks/scan_a_capture.md`** — how to run `scan_pipeline.py` over a
  scanning-rig capture video to reconstruct a mesh. Covers the `nix develop
  .#scan` shell, the two-step platter-ellipse confirmation via
  `roi-preview.jpg`, the seven pipeline stages and their measured wall-clock cost at 720p and 4K, the
  `--mask-mode roi` no-ML fallback, how the platter's known 222 mm diameter
  sets the exported scale, capture guidance (the camera must not move, the scene must stay rigid, and the platter needs non-repeating marks), and
  the `--capture-mode holds` selector for step-and-hold captures on a marked
  platter.

## AI Agent Configuration

`AGENTS.md` at the repo root is the canonical short-form agent guide; `CLAUDE.md`
is a compatibility document for consumers that still expect named sections to
live there. Claws — an autonomous agent service — manages this repo's issues,
PRs, and docs; see [claws-automation.md](claws-automation.md). Cross-cutting
process requirements live in [requirements.md](requirements.md); durable
operator/automation gotchas that belong to no feature doc live in
[agent-notes.md](agent-notes.md).

Three subagent role definitions live in `.agents/` — `issue-refiner`,
`issue-implementer`, and `pr-reviewer` — each self-documenting the invariants
and output format for its stage of the issue→PR lifecycle. Read the relevant
one directly rather than a summary here.

## CI/CD Pipeline

`build.yml` runs on push to `main` and on PRs, on a self-hosted Linux runner
pinned to `ryzen` (render memory caps are calibrated to that host). All
tooling comes from this repo's own `flake.nix` devShell, not the runner
host. The pipeline renders every `.scad` to STL, validates meshes and
metadata, checks mating-part interference, generates thumbnails/QR
codes/standalone viewers/`models.json`, and deploys to S3 — PRs get a preview
deployment and an auto-generated comment. Dependency-graph, mesh, metadata,
and interference checks all use the **deferred enforcement** pattern:
failures are recorded early but only block the build at the very end.
Main-branch build failures are monitored centrally by Claws'
`main-build-monitor` job, not a per-repo notifier workflow. Full step-by-step
detail, including every env var and validation rule, is in
[ci-pipeline.md](ci-pipeline.md).

## Configuration

| Item | Location | Notes |
|------|----------|-------|
| CI runner | `[self-hosted, linux, ryzen]` in `build.yml` | Runner provides only `nix`/`git`/`docker`; OpenSCAD, ImageMagick, ADMesh, qrencode, zip, Python 3, Node.js, and the AWS CLI all come from this repo's `flake.nix` `default` devShell, entered via `.github/actions/setup-nix` + the job-level `defaults.run.shell`. `build.yml`'s `build` job is pinned to `ryzen` so render memory caps are calibrated to a known host (issue #272) — the label must exist on the runner or the job queues forever |
| Render memory/time caps | `scripts/capped-openscad.sh`; `RENDER_MEM_MAX`/`RENDER_TIMEOUT` env in `build.yml` | Wraps every `openscad` call (STL render: `28G`/`3600s`, sized to the heaviest model's measured cost after the 2026-07-07 runner-freeze incident; thumbnails and orthographic views: `4G`/`120s`). Timeout (124) or SIGKILL (≥128) hard-fails the build before the "suspected library" heuristic can silently swallow it. `scripts/render_view.py` also invokes the wrapper, defaulting to `2G`/`300s` |
| OpenSCAD version baseline | `.openscad-version` | Committed expected version string; CI warns on mismatch |
| AWS deployment role | `secrets.AWS_ROLE_ARN` | OIDC role for S3 sync |
| S3 bucket path | `s3://www.bstjohn.net/3d-models/` | Production deployment target |
| PR preview path | `s3://…/pr-preview/pr-{N}/{SHA}/` | Per-PR, per-commit previews |
| Source zip naming | `site/<dir>-source.zip` | Per-project zip of git-tracked source files; referenced as `sourceZip` in `models.json` |
| Three.js version | `0.170.0` (`scripts/threejs_assets.py`; staged same-origin to `site/vendor/three/0.170.0/` by `scripts/fetch_threejs.py`, import maps in `index.html`/`embed.html`) | STLLoader + OrbitControls; all three assets SHA-256 verified before staging, and `generate-standalone.py` inlines the same verified bytes; unpinned/malformed hash is a hard failure |
| Viewer max pixel ratio | `MAX_PIXEL_RATIO = 1.5` in `index.html`, `embed.html`, `generate-standalone.py` | Caps Retina drawing-buffer cost; MSAA (`antialias: true`) kept |
| Viewer render policy | On-demand (`invalidate()` / `needsRender`); rAF loop suspends after ~90 idle frames; `powerPreference: 'low-power'` | Issue #341 — continuous rAF rendering overheated client laptops. Any external scene/material mutation must call `viewer.invalidate()` (see [web-viewer.md](web-viewer.md#render-budget)) |
| OpenSCAD resolution | `$fn = 64` | Set per-file in `.scad` sources |
| Thumbnail size | `800x600` | Set in build.yml render step |
| OG hero image | `og-hero.png` (1200x630) | Composited by CI from one thumbnail per project (5x3 grid, max 15); stable URL, not cache-busted |
| Structured data | `<!-- __STRUCTURED_DATA__ -->` in `index.html` | Replaced by CI with Schema.org JSON-LD |
| OEmbed links | `<!-- __OEMBED_LINKS__ -->` in `index.html` | Replaced by CI with `<link rel="alternate">` tags |
| Filament colors | `filament-colors.json` | 8 preset colors; Blue is default. Single source of truth loaded by `index.html` at runtime and injected into standalone viewers at build time by `generate-standalone.py` |
| Analytics | Plausible script tag in `index.html` and `embed.html` | Self-hosted at `plausible.bstjohn.net`, `data-domain="bstjohn.net"`; cookieless. Standalone viewers (`site/standalone/`) deliberately omit it so they stay self-contained/offline |
| Touch hint timeout | 5000 ms in `showTouchHint()` | Fade-out delay for gesture overlay |
| Zip bundle threshold | 2+ STL files per project | Single-file projects don't get an STL zip; all projects get a source zip |
| Deep link format | `#project-slug/model-slug`, panes joined by `+`, models within a pane by `,` | URL hash routing; legacy `#project/model` and `#project` links parse unchanged |
| Landing gallery ordering | `__LANDING_ORDER_START__`/`__LANDING_ORDER_END__` block in `index.html` | `interestScore` (0–7, from `models.json` fields) + `recencyScore` (0–2, from `updated`); ties break on date then name. Pinned by `scripts/test_landing_order.mjs` |
| QR code style | `-s 8 -m 2`, `E0E0E0` on `1A1A2E` | Module size 8, margin 2, dark theme colors |
| Print-time heuristic | 0.2mm layers, 50mm/s, 5x multiplier | Conservative defaults; volume fallback for flat models |
| Metadata schema | `meta.schema.json` (JSON Schema draft 2020-12) | Validated in CI; `description` required, all others optional |
| README gallery markers | `<!-- gallery:start -->` / `<!-- gallery:end -->` | Auto-replaced by `scripts/generate-gallery.py` |
| Standalone viewer cache | `$HOME/.cache/3d-models/threejs` (override `ASSET_CACHE_DIR`) | Host-level cache for the upstream Three.js downloads, shared by `fetch_threejs.py` and `generate-standalone.py`; lives outside the checkout so `actions/checkout`'s `git clean -ffdx` can't wipe it, and is consulted before the network when the SHA-256 pin matches (issue #460) |
| Render cache | `$HOME/.cache/3d-models/render` (override `RENDER_CACHE_DIR`, disable `RENDER_CACHE_DISABLED=1`) | Host-level content-addressed STL cache; key = SHA-256 over transitive include/use chain + binary assets + OpenSCAD version + `CACHE_VERSION` via `scripts/render_cache.py`; pruned at 30 days by mtime |
| Interference check | `mating_pairs` in `meta.json` | Pairs of STL filenames validated by `check_interference.py` using `trimesh` + `manifold3d` |
| Interference threshold | overlap volume > 0 | Any geometric overlap between mating parts is a failure |
| Interference output | `site/interference.json` | Per-pair results with overlap volume in mm³, shown in PR comment table |
| Parameter manifest schema | `parameters.schema.json` (JSON Schema draft 2020-12) | Validated in CI; only `number` and `boolean` types permitted; strings forbidden to avoid `-D` shell-quoting issues |
| openscad-wasm version | `scripts/fetch_openscad_wasm.py` | Pinned to release `2022.03.20` (non-threaded build, no COOP/COEP headers required); staged into `site/openscad/` with SHA-256 verification; unpinned/malformed hash is a hard failure |
| Source staging | `site/sources/<project>/` | All `.scad` files, validated manifests, and binary render assets (`.png` files whose basename appears in a sibling `.scad`) copied here by CI; per-project `manifest.json` lists `.scad` and `.png` filenames for browser discovery |
| External libraries | none vendored | See [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md) for a catalogue of available libraries |
| Favicon | `favicon.svg` (repo root) | SVG cube glyph on `#1a1a2e`; copied to `site/favicon.svg` by CI |
| Web app manifest | `site.webmanifest` (repo root) | PWA metadata; copied to `site/site.webmanifest` by CI |
| robots.txt | `robots.txt` (repo root) | Served at `/3d-models/robots.txt`; crawler-authoritative copy requires origin-root infra |
| llms.txt | `llms.txt` (repo root) | AI agent discoverability; served at `/3d-models/llms.txt`; same sub-path caveat |
| sitemap.xml | Generated by CI "Generate sitemap.xml" step | Lists gallery root + all standalone viewer URLs, each with a `<lastmod>` from the project's last-commit date; deployed to `site/sitemap.xml` |
| Dependency updates | `.github/dependabot.yml` | `github-actions` ecosystem only, weekly, grouped into a single PR (`open-pull-requests-limit: 5`), no default label (#288). No `npm`/`pip` entries — the repo has no root `package.json` and OpenSCAD/Python tooling isn't a Dependabot-supported ecosystem |
