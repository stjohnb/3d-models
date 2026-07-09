# 3D Models

A personal collection of 3D-printable models designed in
[OpenSCAD](https://openscad.org/). A CI pipeline renders the `.scad` sources
into downloadable `.stl` files, generates PNG thumbnails, validates mesh
integrity, and deploys an interactive Three.js viewer.

**[Browse and download all models](https://www.bstjohn.net/3d-models/)**

## What's here

Each top-level directory is one model project containing OpenSCAD `.scad`
sources and a `meta.json` description:

- `adjustable-bracket/` — two-piece adjustable angle bracket joined with an M5 bolt
- `blast-gate/` — inline sliding blast gate for 51 mm OD PVC vacuum lines
- `hex-connector/` — single-piece hexagonal male/female connector
- `macbook-pro-laptop-stand/` — parametric vertical laptop dock
- `nz-ski-fields/` — topographic NZ terrain model, split into three printable parts
- `power-workshop/` — Fisher-Price Power Workshop replacement parts
- `sink-tray/` — replacement sink-tray foot
- `toothbrush/` — modular wall-mounted toothbrush holder system
- `vacuum-hose/` — workshop dust-collection hose adapter and reducer

STL outputs are not committed — they are generated artifacts produced by the
build pipeline.

## Rendering a model locally

You need [OpenSCAD](https://openscad.org/downloads.html) installed. From a clone
of this repository, render any renderable `.scad` file to an STL:

    openscad -o piece_a.stl adjustable-bracket/piece_a.scad

Files whose names begin with an underscore (`_*.scad`) are shared libraries —
they define common parameters and modules and produce no geometry on their own,
so they are not rendered directly.

## Conventions

- **Library vs. renderable files.** Underscore-prefixed files (`_*.scad`) are
  libraries: shared parameters and modules, no top-level geometry. Every other
  `.scad` file renders to exactly one STL.
- **Resolution.** Sources set `$fn = 64` for smooth curves (`hex-connector` is
  the exception — it has no circular geometry).
- **Dimensions.** All dimensions are named variables in millimetres, declared at
  the top of each file, with derived values computed from base parameters.
- **Viewer orientation.** OpenSCAD is Z-up; the web viewer is Y-up. Assembly and
  tube-shaped files apply `rotate([-90, 0, 0])` at the top level; upright or
  symmetric models omit it.
- **Metadata.** Each project has a `meta.json` validated against
  `meta.schema.json`. Models may ship a `<basename>.parameters.json` manifest
  (validated against `parameters.schema.json`) exposing numeric/boolean
  parameters as live controls in the browser viewer.

## Architecture

The build pipeline renders all sources, validates meshes, checks that mating
parts fit without geometric overlap, generates thumbnails and QR codes, builds a
`models.json` manifest, and deploys a single-page Three.js viewer (`index.html`,
with an embeddable `embed.html` variant). The viewer also offers in-browser
re-rendering of parametric models via [openscad-wasm](https://github.com/openscad/openscad-wasm).

More detail:

- `docs/OVERVIEW.md` — architecture and key patterns
- `docs/model-projects.md` — per-project file tables, geometry, and parameters
- `docs/ci-pipeline.md` — build pipeline, step by step
- `docs/web-viewer.md` — the viewer, embedding, and standalone HTML exports
- `docs/OPENSCAD_LIBRARIES.md` — catalogue of available OpenSCAD libraries

## Tests

Python scripts are tested with pytest, and the in-browser customizer pipeline
has a Node integration test:

    python3 -m pytest scripts/
    node scripts/test_wasm_customizer.mjs
