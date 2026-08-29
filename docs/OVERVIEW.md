# 3D Models — Developer Overview

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
│   ├── test_oembed_helpers.py  # Tests for oembed_helpers
│   ├── check_interference.py   # Geometric overlap detection for mating part pairs (meta.json mating_pairs)
│   ├── test_check_interference.py  # Tests for check_interference
│   ├── fetch_openscad_wasm.py  # Fetches pinned openscad-wasm release into $HOME/.cache/3d-models/openscad-wasm/<version>/ and stages to site/openscad/
│   ├── test_fetch_openscad_wasm.py # Tests for fetch_openscad_wasm (mocks urllib, verifies zip parsing)
│   ├── threejs_assets.py       # Single source of truth for the pinned Three.js version and SHA-256 asset hashes
│   ├── fetch_threejs.py        # Fetches the pinned Three.js release into $HOME/.cache/3d-models/threejs/ and stages it same-origin to site/vendor/three/<version>/ with hash verification (issue #403)
│   ├── test_fetch_threejs.py   # Tests for fetch_threejs (hash verification, staging)
│   ├── asset_cache.py          # Host-level download-cache root shared by threejs_assets and fetch_openscad_wasm (issue #460)
│   ├── test_asset_cache.py     # Tests for asset_cache (cache root resolution, atomic writes)
│   ├── fetch_terrain_heightmap.py  # One-off generator: fetch a lat/lon terrain heightmap PNG (Mapzen terrarium tiles via AWS Open Data); not used by CI
│   ├── test_fetch_terrain_heightmap.py # Tests for fetch_terrain_heightmap (mocks requests, verifies slippy math and decode); pillow/requests are in the `default` devShell, so this runs in CI
│   ├── generate_lake_bed.py        # One-off generator: bake lakebed bathymetry PNG from heightmap for nz-ski-fields; not used by CI
│   ├── render_view.py          # Render an arbitrary OpenSCAD view to PNG via capped-openscad.sh (developer/agent tool, not used by CI)
│   ├── test_render_view.py     # Tests for render_view
│   ├── scan_pipeline.py        # Photogrammetry CLI: scanning-rig capture video → scaled STL (operator tool, not used by CI)
│   ├── test_scan_pipeline.py   # Tests for scan_pipeline (stage selection, argument defaults)
│   ├── scan_frames.py          # Frame extraction (ffmpeg), sharpness-binned and hold-aware frame selection for scan_pipeline
│   ├── test_scan_frames.py     # Tests for scan_frames' binned and hold-detection selectors
│   ├── scan_masks.py           # Platter-ellipse + salient-object masking for scan_pipeline (COLMAP mask PNGs)
│   ├── test_scan_masks.py      # Tests for scan_masks; pure-helper tests run in CI, mask-geometry tests skip unless `cv2` is importable (`nix develop .#scan`)
│   ├── scan_colmap.py          # COLMAP/OpenMVS command lines for scan_pipeline (CPU-only: never patch_match_stereo)
│   ├── test_scan_colmap.py     # Tests for scan_colmap's argv builders and sparse-model selection; also validates option names against a real colmap when one is on PATH
│   ├── scan_mesh.py            # Platter-plane fit, mm scaling, cropping and STL export for scan_pipeline
│   ├── test_scan_mesh.py       # Tests for scan_mesh; only imports numpy/trimesh, both in the `default` devShell, so runs in CI's unit-test step
│   ├── scan_reference.py       # Watertight, size-budgeted reference meshes from a cleaned scan (convex hull / axis-aware slab-hull union) for scan_pipeline
│   ├── test_scan_reference.py  # Tests for scan_reference; only imports numpy/trimesh/manifold3d, all in the `default` devShell, so runs in CI's unit-test step
│   ├── external_assets.py      # Assets a project's .scad files reference from outside the project dir (used by CI's source-zip and parameter-manifest steps)
│   ├── test_external_assets.py # Tests for external_assets
│   ├── render_cache.py         # Content-addressed render cache key computation (used by CI render step)
│   ├── test_render_cache.py    # Tests for render_cache
│   ├── project_dates.py        # Per-project last-commit dates (models.json `updated`; landing-page recency ordering)
│   ├── test_project_dates.py   # Tests for project_dates
│   ├── test_generate_standalone.py  # Regression tests for standalone-viewer HTML injection escaping (filament colors, SEO head fields, JSON-LD)
│   ├── test_scad_fonts.py      # Pins the no-text()/no-font rule (the deployed openscad-wasm build ships no fonts)
│   ├── test_scad_orientation.py  # Pins the no-top-level-rotate([-90,0,0]) rule (see Viewer Rotation below); one allowlisted exception
│   ├── test_output_names.py    # Pins renderable basename uniqueness across projects and per-project slug uniqueness (issue #449)
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
├── CLAUDE.md             # Claude guidance: conventions, invariants, and doc pointers for AI agents
├── .claude/
│   └── agents/
│       ├── issue-refiner.md      # Subagent: refines GitHub issues into implementation plans
│       ├── issue-implementer.md  # Subagent: implements approved plans while preserving CI invariants
│       └── pr-reviewer.md        # Subagent: reviews PR diffs against CI-enforced invariants
├── playbooks/
│   ├── iterate_with_render_view.md  # How to use render_view.py for iterative local design
│   └── scan_a_capture.md            # How to run the photogrammetry pipeline on a scanning-rig capture video
├── .github/
│   ├── dependabot.yml         # Weekly grouped Dependabot updates for the github-actions ecosystem only
│   ├── actions/
│   │   └── setup-nix/
│   │       └── action.yml    # Composite action: puts the runner's system `nix` on PATH or fails fast
│   └── workflows/
│       ├── build.yml             # CI: render, validate, thumbnail, deploy
│       └── notify-failures.yml   # Monitors build.yml; opens/closes failure issues on main
└── docs/
    ├── OVERVIEW.md             # This file — main entry point
    ├── model-projects.md       # Per-project file tables, geometry, and key parameters
    ├── web-viewer.md           # Detailed index.html/embed.html/standalone/OEmbed reference
    ├── DESIGN.md               # Visual design choices for index.html (palette tokens, display face, motion)
    ├── ci-pipeline.md          # Detailed CI/CD pipeline step-by-step documentation
    ├── OPENSCAD_LIBRARIES.md   # Catalogue of available third-party OpenSCAD libraries
    ├── claws-automation.md     # How the Claws automation service manages issues, PRs, and docs (auto-maintained)
    ├── requirements.md         # Cross-cutting process/workflow requirements with no single owning subsystem doc
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
| `printing_notes` | `array` of `string` | Free-text printer/slicer guidance (layer height, seam, orientation, filament); surfaced in the viewer, embed, and standalone pages. Deliberately free-text rather than structured fields (orientation enums, support-needed flags): issue #301 proposed exactly that structured shape and explicitly backed off it, citing `ideas/rejected.md`'s prior decline of a "print orientation indicator" as the reason to stay prose-only — don't re-propose structured printing metadata on the strength of this field alone |
| `relatedModels` | `array` of `string` | Directory names of related projects |
| `mating_pairs` | `array` of 2-element `string` arrays | Pairs of STL filenames that must fit without geometric overlap (validated by `check_interference.py`) |
| `complex_interior` | `boolean` | When `true`, CI renders three extra orthographic views (`_top`, `_bottom`, `_front`) to expose internal cavity geometry; used by `power-workshop` and `drawer-organiser` |
| `hero` | `string` | Rendered STL basename featured as the project's landing-gallery and README thumbnail; defaults to the first STL alphabetically. When a new multi-model project ships, set `hero` explicitly on it if there's an obvious representative part (assembly previews, the namesake variant) rather than relying on alphabetical sort to pick the right one by luck — the owner's standing direction after `scanning-rig`'s thumbnail picked the wrong STL: "It should be specified for all projects where there's an obvious candidate, rather than getting lucky with sorting" (#372). Deliberately absent for single-model projects and for projects whose parts are co-equal (`adjustable-bracket`, `vacuum-hose`) |
| `assembly` | `object` `{stl, parts}` | Declares that one project STL's viewer card is a coloured multi-part composite rather than a single mesh — see "Composite Multi-Colour Assembly Previews" below; currently only `nz-ski-fields` uses this |

Metadata is merged into `models.json` at build time. Only viewer-relevant
fields are propagated (`description`, `tags`, `difficulty`, `version`,
`hardware`, `hero`, `assembly`, `printing_notes`). `license`, `relatedModels`, and
`mating_pairs` are intentionally excluded from the manifest.

**Directory structure, not metadata, drives UI grouping.** When the two
`vacuum-hose` models needed to appear together in the viewer, the owner's own
follow-up rejected adding a `group` field to `meta.schema.json` once moving
both files into one directory already produced the grouping in the UI:
"moving them to the same directory had the required effect... is [a group
field] used for anything at all?" (#196). Directory placement is the sole,
canonical grouping signal — don't add a metadata field to solve a grouping
problem that a directory move already solves. `relatedModels` is a separate,
narrower thing (an informational cross-reference list, not a display
grouping mechanism) and stays excluded from `models.json` for that reason.

The manifest also includes a `rendered_with` field per model entry in the manifest,
recording the OpenSCAD version used to produce the STLs in that CI run
(e.g., `"OpenSCAD 2024.12.06"`). This is sourced from the runner's
`openscad --version` output captured by the version-check step. It serves
as diagnostic documentation — if a printed part doesn't fit, `rendered_with`
helps determine whether the issue is a source change or a renderer regression.
The committed `.openscad-version` file stores the expected version baseline;
CI warns when the runner's version drifts from it.

Each project entry also carries an `updated` field: the ISO-8601 committer
date of the last commit touching that project's directory, produced by
`scripts/project_dates.py`. It is **CI-derived, not a `meta.json` field** —
there is nothing to hand-maintain and `meta.schema.json` is unaffected. Its
only consumer is the landing gallery's recency ordering (see
[web-viewer.md](web-viewer.md#landing-gallery)). Because the date comes from
`git log`, `build.yml`'s checkout uses `fetch-depth: 0`; on a shallow clone
`project_updated()` returns `{}`, `updated` is omitted everywhere, and the
gallery silently falls back to interest-only ordering.

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
different colours the way an OpenSCAD `color()` preview can — and a full-
resolution merged mesh for `nz-ski-fields` was heavy enough to freeze a CI
runner (issue #272) and crash browsers loading the viewer page. Instead, a
project can declare an `assembly` object in `meta.json` (`{stl, parts:
[{stl, color}, ...]}`, schema-validated) that tells every viewer to load a
set of already-co-registered part STLs — each rendered in its own fixed
colour — into one scene in place of the single named STL. `nz-ski-fields`'s
`lake.stl` / `terrain.stl` / `snow.stl` share the same footprint and origin,
so loading them together with no offset reproduces the full stacked model.
The `assembly.scad` source itself stays Z-up (no viewer rotation) and
renders at reduced heightmap resolution — it now exists purely as the
gallery thumbnail source, not as a viewer-loaded mesh; the interactive
composite is assembled client-side from the printable parts' own STLs.
`index.html`, `embed.html`, and `generate-standalone.py` all implement this
composite path; a composite card also suppresses the filament color picker,
since colours are fixed per part. Full detail in
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
shipping the oversized geometry as-is. `drawer-organiser` is the fullest
example: `bin_part()` splits a bin into equal pieces at cell boundaries (`gx`
must be evenly divisible by `parts`), while `container_part()` splits a
container using `floor(i*n/parts)`, so an odd cell count splits unevenly at a
real boundary instead of through the middle of a base pad; both run the outer
bound of the first/last slice well past the nominal edge to avoid a coincident
CGAL face at an unflared wall. Every whole-container renderable keeps
`split_parts`/`part_index` in its customizer manifest for arbitrary bed sizes,
and its default STL download is still the whole, unsplit shape.

For the container sizes that actually exceed the A1's 250mm bed, though, the
project ships **dedicated piece renderables** (e.g.
`drawer_container_left_front.scad` / `_back.scad`) rather than relying on
end users to run the customizer. These call the lower-level
`container_slice(gx, gy, h, wall_t, floor_t, ..., c0, c1)` — added in issue
#319 by factoring it out of `container_part()`, which now just computes
`floor(i*n/parts)` boundaries and delegates to it — with an explicit cell
range instead of an even split. The boundaries are hand-picked to land
**offset from the baseplate tile seams underneath**, so a solid piece
straddles every grid join (stiffening the assembled floor) and the cut faces
of adjacent pieces meet over the middle of a single tile, keeping them flush
even unglued (issue #322); the left container is the sole exception, since
its 10-cell depth only yields two ≤5-cell pieces by cutting at the seam
itself, and two pieces were preferred over introducing a third cut. Printing
an oversized container means printing these named piece files directly (no
customizer needed) and gluing the cut faces (CA glue) with the baseplate
itself used as the alignment jig, since the mating pads/sockets hold the
pieces in register. Full detail, including the print/glue instructions per
part and the seam-offset cell tables, lives in
[model-projects.md](model-projects.md#drawer-organiser) and
`drawer-organiser/layout.md`.

### Interlocking Tile Seams (drawer-organiser)

Baseplate tiles that must butt together into a larger continuous floor use a
genderless barbed-tab seam: every tile carries tabs on its +X/+Y edges and the
matching notches on -X/-Y, so any tile mates with any other tile of the same
edge length — no separate male/female variants to track. Tabs sit at the
**centre of each cell** along an edge, not on the cell-junction corners; an
earlier version (issue #309) put them on the junctions because that looked
like the thickest run of material, but that material is only a thin rib and
also the sole thing joining the tile's perimeter rail to its body, so a notch
sized to hold the tab severed the rail and printed tiles fell apart. At a cell
centre the rail is backed by material running the full edge length, so a notch
there only removes a slot without detaching anything. The barb's shoulder is
perpendicular to the seam (not a dovetail or round jigsaw head, which either
cam out under load or leave almost no undercut in the ~2mm of available rail
depth), which also means tiles cannot be pressed together in-plane — a new
tile must be lowered vertically onto its already-placed neighbours so its tabs
drop straight into their slots. Clearance is applied to the tab/notch
**features only**, never to the tile's outer outline, because shrinking the
outline would drift the 42mm Gridfinity pitch across every seam past the
0.25mm pad-to-socket clearance and stop a seam-spanning bin from seating. Full
derivation and measured tolerances in `drawer-organiser/layout.md`.

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
loads instantly when the model is opened in a pane. Clicking the **⚙ Customize** button lazy-loads
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
`bench-dog-blank` (`bench_dog_blank`),
`bin-foot-opener` (`bin_foot_pull`),
`blast-gate` (`gate_body`, `gate_blade`),
`drawer-organiser` (`drawer_baseplate_5x5`, `drawer_baseplate_5x5_back`,
`drawer_baseplate_4x5`, `drawer_baseplate_4x5_back`, `drawer_bin_5x5`,
`drawer_bin_10x5_half`, `drawer_filler`, `drawer_container_left`,
`drawer_container_left_front`, `drawer_container_left_back`,
`drawer_container_back_4x6`, `drawer_container_back_4x6_half`,
`drawer_container_back_4x6_half_divided`, `drawer_container_back_4x6_right`,
`drawer_container_back_4x6_right_front`, `drawer_container_back_4x6_right_back`,
`drawer_container_front_5x4`, `drawer_container_front_3x4`,
`drawer_container_front_1x3`, `drawer_container_front_1x1`),
`esp32-display-case` (`case_back`, `case_front`), `hex-connector` (`hex_connector`),
`macbook-pro-laptop-stand` (`laptop_stand`, `dual_laptop_stand`),
`nz-ski-fields` (`lake`, `terrain`, `snow`),
`scanning-rig` (`turntable_base`, `turntable_platter`, `phone_stand`, `rig_link`, `scan_boost`, `scan_riser`, `scan_setback`),
`sink-tray` (`tray_foot`), `ukulele-wall-hook` (`ukulele_hook`), and
`vacuum-hose` (`adapter`, `reducer`). Adding one
for a new model is just a matter of dropping a `<basename>.parameters.json` next
to the renderable `.scad`; CI picks it up automatically.

Binary assets referenced via `surface()` or `import()` (e.g.
`heightmap.png` in `nz-ski-fields`) are staged to
`site/sources/<project>/`, listed in `manifest.json`, and fetched as
`Uint8Array` so they can be written into the wasm FS as raw bytes.

### Viewer Rotation

OpenSCAD uses Z-up coordinates; the Three.js viewers expect Y-up. There is a
single, unconditional rule for reconciling them (issue #382):

- **Every `.scad` source stays in native OpenSCAD Z-up.** Never add a top-level
  `rotate([-90, 0, 0])` for the viewer's benefit.
- **Every viewer applies `geometry.rotateX(-Math.PI / 2)` to every mesh** it
  loads — `index.html` (both the single-mesh and composite paths, plus
  `replaceGeometry()` for customizer output), `embed.html`, and the standalone
  viewers generated by `scripts/generate-standalone.py`. It happens before the
  bounding-box maths, so camera framing and the cross-section slider operate on
  the corrected axes.

Keeping sources Z-up means the PNG thumbnails CI renders with OpenSCAD's
default (Z-up) camera and the STLs users download for slicing are both correct,
while the viewers still show every model upright. Previously the rotation lived
in nine sources, which stood them up in the viewer at the cost of tipping their
thumbnails and downloaded STLs onto their back — and left every other project
upright in the gallery but tipped in the viewer.

The rule is pinned by `scripts/test_scad_orientation.py` (no top-level
`rotate([-90, 0, 0])` outside its allowlist) and `test_viewer_invariants.py`'s
`ViewerRotationTests` (the viewers' rotation is present and unguarded).

The **one** allowlisted top-level `rotate([-90, 0, 0])` in the tree is
`toothbrush/Toothbrush backplate.scad`, and it is a genuine *print*
orientation, not a viewer hack: `toothbrush_backplate()` stands upright in the
shared library and that file lays it on its back, flat on the bed.

`scanning-rig/phone_stand.scad` illustrates a pattern worth reusing: it's a
single side profile `linear_extrude()`d along Z with the profile drawn "+Y up",
so the exported STL is simultaneously print-oriented (flat face on the bed) and
sensible in the viewer — a model built this way never needs the print and
viewer orientations reconciled at all.

### Scan Reference Meshes (`scans/`)

Real-world objects photographed on the scanning rig can be brought into the
repo as design input, so a model can be built around one — `difference()` a
scanned toothpaste tube out of a holder body (issue #439).

Two things stand in the way of using a raw scan directly, and `scans/` answers
both:

- **The raw scan is not a solid.** `scan_pipeline.py`'s `clean` stage exports
  the OpenMVS mesh as an open shell — a single low camera ring never sees the
  underside of the object — so `trimesh.is_watertight` is `False` and OpenSCAD's
  CSG rejects it as an operand. The `reference` stage
  (`scripts/scan_reference.py`) closes it, by default as a union of
  overlapping per-slab convex hulls taken perpendicular to the mesh's
  principal axis (`--reference-mode slabs`, `--reference-axis auto`), which
  keeps concavity that varies along the object's own length — including for
  an object lying flat, where that axis is horizontal rather than Z (issue
  #487) — or, for convex-ish objects, as a single convex hull
  (`--reference-mode hull`; tiny, always available). Both are watertight by
  construction. Quadric decimation is deliberately not offered: it lowers the
  face count but leaves the boundary open.
- **`*.stl` is gitignored.** `.gitignore` carves these back out with
  `!scans/**/*.stl`. The rejected "committed revision snapshots" pattern (#198)
  covered *derived outputs* of committed `.scad` sources, which CI can always
  reproduce. A scan mesh is *captured input data* — unreproducible from
  anything in this repo — the same category as `nz-ski-fields/heightmap.png`.
  A size budget (≤500 KB, enforced by the stage) keeps that carve-out honest.

Each object gets `scans/<object>/<object>-reference.stl` plus a sanitised
`scan-report.json` for provenance; `scans/README.md` has the full contract. The
meshes are in platter-centred millimetres and stay Z-up like every other source
(see Viewer Rotation above).

A renderable may then `import()` one by relative path.
`scripts/render_cache.py` already hashes `import()`/`surface()` targets into the
cache key, so editing a mesh invalidates the render. Two build steps assume a
project is self-contained, and `scripts/external_assets.py` bridges both: the
source zip gains the external asset, and the parameter-manifest validation step
**fails a renderable that both imports an external asset and ships a
`<basename>.parameters.json`** — the in-browser customizer writes a project's
files flat into the wasm FS, where a `../scans/…` path cannot resolve.

## Iterative Design Helpers

Utilities for use during active design work — not part of the CI pipeline.
`render_view.py` exists specifically as an *agent-facing* tool, not a
persisted-artifact one: analyzing an external tool's approach of storing
committed multi-angle renders as build artifacts, the owner's own reframing
was "I think where this would be most useful is for Claude itself when
iterating on a design, it should be able to render any angle it needs to
verify its designs, they don't particularly need to be stored as build
artifacts" (#202) — this is why the script produces no build artifacts and is
excluded from CI (see also CLAUDE.md's "Local dev tool (not CI)" note).

### Rendering arbitrary views

When iterating on a model, render any view of any `.scad` file without going through CI.

```bash
# Top-down view into cavity openings
python3 scripts/render_view.py power-workshop/drill_socket.scad --view top

# Custom camera angle with explicit gimbal coordinates
python3 scripts/render_view.py power-workshop/drill_socket.scad --camera=0,0,0,75,0,25,500 --projection=perspective -o ~/renders/custom.png
```

With no `-o`, the PNG is written into a fresh private temp directory (0700, created per invocation) and the path is printed — the old fixed `/tmp/render.png` default was replaceable via a planted symlink on the shared build hosts (#429).

Renders run under `scripts/capped-openscad.sh` with `RENDER_MEM_MAX=2G` / `RENDER_TIMEOUT=300` defaults, both overridable via env — a cap hit exits 124 (timeout) or ≥128 (SIGKILL) with a diagnostic instead of freezing the host.

Available `--view` presets: `iso` (default), `top`, `bottom`, `front`, `back`, `left`, `right`, `custom`.
Pass `--camera=tx,ty,tz,rx,ry,rz,dist` to use an arbitrary angle; this implies `--view custom`.
Additional options: `--imgsize WxH`, `--projection ortho|perspective`, `--no-viewall`, `-D VAR=VALUE` (repeatable).

`--y-up` switches the named view presets to a Y-up semantic axis table. No
source in this repo currently needs it — every `.scad` here is Z-up (see
"Viewer Rotation" above) — but the flag is retained for ad-hoc rendering of
externally-sourced Y-up models.

This script is **not** used by CI and produces no build artifacts.

## Web Viewer (index.html)

A single-page application (no build tools, no framework, ES module JS,
Three.js loaded same-origin from `./vendor/three/<version>/` via import map)
that fetches `models.json` and presents
a tree browser of every project and model alongside a stage of one to three
viewer panes. With nothing loaded — the default on arrival, and after the
header's **← All models** button or a Back-navigation to the bare URL — the
stage shows a landing gallery instead: a card grid of every project with
hero and per-model thumbnails, ordered by an interest score (model count,
difficulty, assembly, hardware, customizer manifests) plus a recency score
from `updated`, so involved and recently-touched projects come first (#345).
Clicking a model loads it into the active pane; Ctrl/Cmd-click
(or the **+ Add to scene** toggle) adds it to the pane alongside what's
already there, laid out side by side along world X. Panes provide
download/source links, a filament color picker, cross-section and focus
views, QR codes, and the in-browser parametric customizer, with deep
linking, keyboard navigation, and full accessibility support. `embed.html`
is a minimal single-model variant for iframe/OEmbed embedding; CI also
generates self-contained standalone HTML viewers (`site/standalone/`) and
per-model OEmbed JSON endpoints (`site/oembed/`).

The URL hash grammar separates panes with `+` and models within a pane with
`,`. Since no slug can contain either character, every link already in the
wild — `#project/model` from QR codes and `#project` from the README gallery
— keeps working unchanged, and an incoming hash is never rewritten.
`scripts/test_hash_routing.mjs` extracts `parseHash`/`formatHash` out of
`index.html` and asserts that; `scripts/test_landing_order.mjs` does the same
for the landing gallery's ranking functions; `scripts/test_viewer_invariants.py`
checks the build-time markers, the `slugify()`/`PUBLIC_REPO` copies, and the
no-`innerHTML`-for-user-data rule.

Visual design choices for `index.html` — the palette tokens, the Space Grotesk
display face, the layered background, and the reduced-motion rule — are
recorded in [DESIGN.md](DESIGN.md).

Every feature — core functionality, the XSS-safety convention, print-time
estimates, the tree browser, filament colors, composite multi-colour assembly
previews, 3D controls, cross-section view, split panes and focus mode, deep
links, QR codes, touch gesture hints, and accessibility — is documented in
detail in [web-viewer.md](web-viewer.md).

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

`CLAUDE.md` at the repo root provides Claude with concise guidance on the
conventions and invariants to preserve. It points Claude to the authoritative
docs and lists things never to do (use GitHub-hosted runners, add `innerHTML`
for user data, hand-edit generated artifacts, etc.).

**Claws automation** — an autonomous agent service — manages issues, PRs, and
documentation for this repo using the subagents below. See
[claws-automation.md](claws-automation.md) for details, and the "Automation host
policy" section of `CLAUDE.md` for the constraints on the shared host those runs
execute on.

**Cross-cutting requirements** — [requirements.md](requirements.md) holds
process/workflow requirements the owner has stated that don't belong to any
single subsystem doc (e.g. how to handle CI flakiness, how research issues
should land, how specced-up-front vs. iteratively-corrected issues are
expected to work here). Subsystem-specific requirements are recorded as
constraints-with-rationale directly in the doc that owns that subsystem
(this file, [model-projects.md](model-projects.md),
[web-viewer.md](web-viewer.md), [ci-pipeline.md](ci-pipeline.md),
[public-snapshot.md](public-snapshot.md)) rather than in a separate log.

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
**self-hosted Linux runner pinned to `ryzen`** (`[self-hosted, linux, ryzen]`,
so the render memory caps below are calibrated against a host of known RAM
capacity — see issue #272). The very first step (`Set up Nix`, running
`.github/actions/setup-nix`) fails fast with a pointer to
`St-John-Software/nixos-config` if the runner has no working `nix` binary —
the workflow never tries to locate or install its own prerequisites (issue
#348). Every subsequent step then runs inside `nix develop
...#default --command bash -euo pipefail {0}`, which resolves this repo's own
`flake.nix` `default` devShell; that devShell — not the runner host —
provides OpenSCAD (a headless EGL/llvmpipe wrapper; no Xvfb involved),
ImageMagick, ADMesh, qrencode, zip, Python 3, Node.js, and the AWS CLI (this
also replaced the old `actions/setup-node` dance for the WASM smoke test,
issue #356). It then verifies dependency graphs, validates project metadata,
renders all `.scad` files to STL via
`scripts/capped-openscad.sh` (wrapping
`openscad --export-format binstl` under a memory ceiling and wall-clock
timeout — `RENDER_MEM_MAX`/`RENDER_TIMEOUT`, default `28G`/`3600s` — so a
pathological render fails the step cleanly instead of freezing the runner; a
timeout or SIGKILL exit is checked and hard-fails the build *before* the
library-detection heuristic runs, so a cap hit can't be silently swallowed as
"suspected library"), validates mesh integrity (including bounding-box extraction for
print-time estimates), checks mating part interference for pairs declared in
`meta.json`'s `mating_pairs` field (using `trimesh` and `manifold3d` to detect
geometric overlap — stored as `interference.json`, with CI warning annotations
and PR comment table), generates standalone HTML viewers, bundles multi-file
projects into zip archives, generates PNG thumbnails (each validated against the
PNG signature — OpenSCAD exits 0 but writes a 0-byte file when it cannot open an
OpenGL context, and those empties shipped a text-only landing gallery in issue
#359), renders extra orthographic
views for models with `complex_interior: true` in their `meta.json`, generates
QR codes, composites an OG hero image, builds `models.json` (with metadata,
print times, and QR references), generates a `sitemap.xml` listing the
gallery and all standalone viewer URLs, generates the README gallery, builds
Schema.org structured data and OEmbed endpoints, and deploys to S3. PRs get preview deployments and an
auto-generated comment showing thumbnails, file sizes, triangle counts, mesh
validation results, and interference check results for changed models.
Dependency graph checks, mesh validation, metadata validation,
interference checks, and thumbnail rendering all use a **deferred
enforcement** pattern — failures are
recorded early but only block the build at the very end, so the full pipeline
output is always available.

A separate **`notify-failures.yml`** workflow monitors for `build.yml` failures
on `main`. On failure it opens a `bug` issue (deduplicated — one open issue at
a time). On the next successful run it auto-closes the issue with a recovery
comment.

## Configuration

| Item | Location | Notes |
|------|----------|-------|
| CI runner | `[self-hosted, linux, ryzen]` in `build.yml`; `[self-hosted, linux]` in `notify-failures.yml` | Runner provides only `nix`/`git`/`docker`; OpenSCAD, ImageMagick, ADMesh, qrencode, zip, Python 3, Node.js, and the AWS CLI all come from this repo's `flake.nix` devShells (`default` for `build.yml`, `scripts` for `notify-failures.yml`), entered via `.github/actions/setup-nix` + the job-level `defaults.run.shell`. `build.yml`'s `build` job is pinned to `ryzen` so render memory caps are calibrated to a known host (issue #272) — the label must exist on the runner or the job queues forever |
| Render memory/time caps | `scripts/capped-openscad.sh`; `RENDER_MEM_MAX`/`RENDER_TIMEOUT` env in `build.yml` | Wraps every `openscad` call (STL render: `28G`/`3600s`, sized to the heaviest model's measured cost after the 2026-07-07 runner-freeze incident; thumbnails and orthographic views: `4G`/`120s`). Timeout (124) or SIGKILL (≥128) hard-fails the build before the "suspected library" heuristic can silently swallow it. `scripts/render_view.py` also invokes the wrapper, defaulting to `2G`/`300s` |
| OpenSCAD version baseline | `.openscad-version` | Committed expected version string; CI warns on mismatch |
| AWS deployment role | `secrets.AWS_ROLE_ARN` | OIDC role for S3 sync |
| S3 bucket path | `s3://www.bstjohn.net/3d-models/` | Production deployment target |
| PR preview path | `s3://…/pr-preview/pr-{N}/{SHA}/` | Per-PR, per-commit previews |
| Source zip naming | `site/<dir>-source.zip` | Per-project zip of git-tracked source files; referenced as `sourceZip` in `models.json` |
| Three.js version | `0.170.0` (`scripts/threejs_assets.py`; staged same-origin to `site/vendor/three/0.170.0/` by `scripts/fetch_threejs.py`, import maps in `index.html`/`embed.html`) | STLLoader + OrbitControls; all three assets SHA-256 verified before staging, and `generate-standalone.py` inlines the same verified bytes |
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
| openscad-wasm version | `scripts/fetch_openscad_wasm.py` | Pinned to release `2022.03.20` (non-threaded build, no COOP/COEP headers required); staged into `site/openscad/` with SHA-256 verification |
| Source staging | `site/sources/<project>/` | All `.scad` files, validated manifests, and binary render assets (`.png` files whose basename appears in a sibling `.scad`) copied here by CI; per-project `manifest.json` lists `.scad` and `.png` filenames for browser discovery |
| External libraries | none vendored | See [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md) for a catalogue of available libraries |
| Favicon | `favicon.svg` (repo root) | SVG cube glyph on `#1a1a2e`; copied to `site/favicon.svg` by CI |
| Web app manifest | `site.webmanifest` (repo root) | PWA metadata; copied to `site/site.webmanifest` by CI |
| robots.txt | `robots.txt` (repo root) | Served at `/3d-models/robots.txt`; crawler-authoritative copy requires origin-root infra |
| llms.txt | `llms.txt` (repo root) | AI agent discoverability; served at `/3d-models/llms.txt`; same sub-path caveat |
| sitemap.xml | Generated by CI "Generate sitemap.xml" step | Lists gallery root + all standalone viewer URLs, each with a `<lastmod>` from the project's last-commit date; deployed to `site/sitemap.xml` |
| Dependency updates | `.github/dependabot.yml` | `github-actions` ecosystem only, weekly, grouped into a single PR (`open-pull-requests-limit: 5`), no default label (#288). No `npm`/`pip` entries — the repo has no root `package.json` and OpenSCAD/Python tooling isn't a Dependabot-supported ecosystem |
