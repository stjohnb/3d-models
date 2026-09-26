# 3d-models

This repository contains OpenSCAD source for practical 3D-printable models,
the CI that renders and validates them, and an interactive Three.js gallery at
`bstjohn.net/3d-models`.

## Where to read first

- Start with [docs/PRODUCT.md](docs/PRODUCT.md) for what the product must do
  and why, then open its relevant area document.
- Read [docs/OVERVIEW.md](docs/OVERVIEW.md) for architecture and links to the
  owning technical document.
- Read [docs/OPENSCAD_LIBRARIES.md](docs/OPENSCAD_LIBRARIES.md) and
  [ideas/rejected.md](ideas/rejected.md) before proposing model geometry or a
  new pattern.

All changes land via pull request; nothing is pushed directly to the default
branch. See [docs/claws-automation.md](docs/claws-automation.md).

## Core conventions

- Library SCAD files are underscore-prefixed and have no top-level geometry;
  each renderable produces exactly one STL. Use named millimetre dimensions
  and `$fn = 64` (except hex-connector's deliberate six-sided overrides).
- Keep sources Z-up. Do not add a top-level `rotate([-90, 0, 0])` merely for
  the viewer, which performs that conversion itself.
- SCAD basenames and scan-object directories may contain only
  `[A-Za-z0-9._ -]`; renderable names and their slugs must be unique.
- `meta.json` requires `description`; update its schema before adding fields.
  Parameter manifests allow only number and boolean values.
- Never hand-edit generated models, gallery, dependency graphs, deployment
  files, QR codes, or STL outputs. Read the owning doc for their generator.
- Dynamic viewer content must use DOM APIs, never `innerHTML`. Preserve the
  four-way slugify and public-source-link parity when either changes.
- Runtime Three.js is staged same-origin with pinned hashes. Keep the
  standalone viewer's JSON and `<>&` escaping layers intact.

## CI and local verification

- Workflow jobs use self-hosted OS-labelled runners; every job runs on
  `[self-hosted, linux]` and must never pin a single runner name or use
  GitHub-hosted labels. Workflow tools come from `flake.nix`: no apt,
  setup-language actions, sudo, or Xvfb.
- Keep validation deferred: record failures during the build and enforce them
  together at its end.
- Run focused unit checks for changed scripts; do not run Docker, browser, or
  external-service integration tests locally.

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
- **Do not run an uncapped OpenSCAD STL render** on this host — it has frozen the box
  before. Prefer a CSG check, or `scripts/render_view.py` at a modest resolution, which
  caps memory and time via `scripts/capped-openscad.sh`.

## Privacy and documentation

- Before committing raster images, strip metadata with
  `python3 scripts/image_metadata.py --fix <files>` and review visible content.
- Do not edit generated artifacts or the auto-maintained
  `docs/claws-automation.md`.
- Keep technical detail in its owning `docs/` topic and durable automation
  gotchas in `docs/agent-notes.md`; keep product intent in `docs/product/`.
