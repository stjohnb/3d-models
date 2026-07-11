# CI/CD Pipeline

Defined in `.github/workflows/build.yml`. Runs on a self-hosted runner on push
to `main` and on PRs.

## Workflows

Two workflow files live in `.github/workflows/`:

- **`build.yml`** — the main build pipeline, documented in detail below.
- **`notify-failures.yml`** — monitors `build.yml` for main-branch failures and
  auto-creates/closes GitHub issues. See [Failure Notification Workflow](#failure-notification-workflow).

## Trigger and Concurrency (`build.yml`)

- **Triggers**: `push` to `main`, `pull_request` (opened, synchronize, reopened).
  Documentation-only changes are skipped via `paths-ignore` (`docs/**`,
  `ideas/**`, root `*.md`, `LICENSE`); a run is skipped only when *all*
  changed files match those patterns, so any PR that also touches a `.scad`,
  script, or site source still builds.
- **Runner**: `[self-hosted, linux, ryzen]` — pinned to the `ryzen` runner
  (rather than any `[self-hosted, linux]` box) so the render memory caps
  below are calibrated against a host of known RAM capacity; the `ryzen`
  label must exist on that runner's registration or the job queues forever.
  The runner is expected to have OpenSCAD, ImageMagick, ADMesh, qrencode,
  xvfb, Python 3, and AWS CLI pre-installed. Each dependency install step
  checks availability first and only installs if missing.
- **Concurrency**: Groups by `pages-main` or `pages-pr-{N}`. In-progress runs
  are cancelled when a new commit arrives.
- **Permissions**: `contents: write`, `pull-requests: write`, `id-token: write`
  (OIDC for AWS). `contents: write` is needed for the README gallery auto-commit
  on main-branch pushes.

## Pipeline Steps

### 1. Verify Dependency Graph

Runs `scripts/scad-dep-graph.sh` and checks whether the per-project
`dependency-graph.md` files (e.g., `power-workshop/dependency-graph.md`) are
up to date. If they differ, the step emits a `::warning::` annotation and
records `failed=true` in its step output — but does **not** fail the build
immediately. The working tree is restored via `git checkout` so subsequent
render steps aren't affected. Enforcement is deferred to step 23 at the end
of the pipeline, following the same pattern as mesh validation. This step has
no external dependencies (pure Bash + grep) and runs instantly.

### 2. Validate Project Metadata

Validates all `*/meta.json` files against `meta.schema.json` using Python's
`jsonschema` library (installed into an isolated venv `.venv-meta`). The step:

- Handles both JSON parse errors and schema validation errors
- Records failed file paths to `.meta-failures` so downstream steps
  (models.json generation, structured data) can skip invalid entries
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until the final enforcement
  step

### 2.5. Validate Parameters Manifests

Validates all `*/*.parameters.json` files against `parameters.schema.json`
using the same `.venv-meta` venv as step 2 (already has `jsonschema`). The
step:

- Performs schema validation (only `number` and `boolean` types permitted)
- Cross-validates each manifest:
  - For `number` parameters: `max >= min`, and `default` must be within
    `[min, max]`
  - The manifest filename must correspond to a renderable `.scad` in the same
    directory (no underscore-prefixed files, i.e. library files cannot have
    manifests)
- Records failed file paths to `.param-failures` (always creates the file, even
  when there are no manifests, so the enforce step's check is reliable)
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until step 27

### 2.6. Run Python Unit Tests for Build Scripts

Runs `python3 -m unittest test_render_view test_oembed_helpers
test_fetch_openscad_wasm test_render_cache test_capped_openscad -v` from within the `scripts/` directory. These are
fast unit tests that mock external I/O (network, filesystem) and run on every
push. They guard the helper functions used throughout the CI pipeline against
regressions.

### 3. Install OpenSCAD and Dependencies

Checks if OpenSCAD, ImageMagick, `zip`, and `qrencode` are already available;
if not, installs via `apt-get` (along with `xvfb` for headless rendering).
Verifies with `openscad --version` to fail fast if installation failed rather
than producing a confusing error in later steps.

Uses `set -eo pipefail` so any failure in the install block is caught
immediately.

### 3.5. Prepare Xvfb Environment

Before any rendering begins, stale X display lock files and sockets from
prior interrupted CI runs are cleaned up on the self-hosted runner:

- Removes `/tmp/.X*-lock` files and `/tmp/.X11-unix/` with `sudo` (prior
  jobs may leave root-owned files)
- Recreates `/tmp/.X11-unix/` with `chmod 1777` (sticky bit — standard
  permissions for X11 socket directories)
- Verifies `xvfb-run` is installed; emits `::error::` and exits if missing

Without this step, `xvfb-run` can fail with "Server is already active for
display N" or "Cannot establish any listening sockets" when a stale lock file
from a previously interrupted job collides with a new display allocation.

### 4. Check OpenSCAD Version

Captures the current OpenSCAD version via `openscad --version 2>&1` (trimming
any trailing newline with shell parameter expansion) and compares it against
the version string committed to `.openscad-version` at the repo root. This
step:

- Writes the captured version string to `site/openscad-version.txt` for use
  by the manifest generation step
- Compares against `.openscad-version` (the committed baseline)
- If versions differ, emits a `::warning::` annotation noting the old and new
  versions
- If versions match, logs a confirmation message

The step id is `scad_version`. On version mismatch, CI continues with a full
render (the current default behavior) and warns the maintainer to update
`.openscad-version` via a dedicated commit. The `.openscad-version` file is
**not** auto-updated by CI to avoid creating commit loops.

The `.openscad-version` file contains the exact first-line output of
`openscad --version 2>&1` from the runner (e.g.,
`OpenSCAD 2024.12.06`). When the self-hosted runner's OpenSCAD installation
is updated, the first CI run after the update detects the mismatch and
triggers a warning; the maintainer then updates `.openscad-version` with a
dedicated commit. This ensures the committed baseline stays in sync with the
runner without CI having write access.

### 5. Install ADMesh

Separate from the OpenSCAD install step. Checks if `admesh` is already
available; if not, installs via `apt-get`. Follows the same idempotent
`command -v` pattern as the other tool installs.

### 6. Render STL Files

Finds all `.scad` files (excluding `.github/`) and renders each to
`site/{name}.stl` via `scripts/capped-openscad.sh --export-format binstl -o
site/{name}.stl {file}` (binary STL output). The wrapper runs OpenSCAD under
a memory ceiling and wall-clock timeout (`RENDER_MEM_MAX` / `RENDER_TIMEOUT`,
workflow-level env, default `28G` / `3600`s — sized for the heaviest models,
the full-res 512 px `nz-ski-fields` part renders, which take tens of minutes
each on a cold cache on the 32 GB ryzen runner) so a pathological render — heavy
CSG, a cold cache, an under-provisioned runner — fails the step cleanly
instead of freezing the self-hosted runner (see issue #272). Output is
captured to a log file (`> /tmp/scad.log 2>&1`) so OpenSCAD's exit code is
preserved (earlier versions piped through `tee`, which masked the exit
code). The log is replayed via `cat` for CI visibility.

Before any render attempt, the filename is validated against an allow-list
regex (`^[A-Za-z0-9._ -]+$`). Files whose basename contains characters
outside this set cause the step to exit with an error immediately. This is a
defense-in-depth security check that prevents adversarially-named files from
injecting unexpected content into generated paths, HTML, or JSON.

Failure classification checks the wrapper's exit code for a cap hit
**before** the existing library-detection strategy runs: if the exit code is
`124` (timeout fired) or `>=128` (SIGKILLed — systemd `MemoryMax` or the OOM
killer), the step emits `::error::render exceeded memory/time cap` and
hard-fails immediately. This ordering matters because a SIGKILLed render
produces a non-zero exit and no STL — the same signature the "suspected
library" heuristic (tier 3 below) looks for. Without the cap-hit check
running first, a cap hit would be silently swallowed as "suspected library"
and the build could go green with the STL missing.

Once a cap hit is ruled out, library detection uses a three-tier strategy:

1. **Convention skip**: Files with an underscore prefix (`_*.scad`) are
   skipped immediately — no render attempt.
2. **Log-based detection**: After rendering, the log is checked for
   `"top level object is empty"` or `"nothing to export"`. If found, the
   file is treated as a library and its STL is removed.
3. **Fallback heuristic**: If OpenSCAD exits non-zero and the output STL
   is missing or tiny (≤84 bytes, i.e. just the binary header), the file
   is treated as a suspected library with a warning annotation.

Genuine render errors (non-zero exit with a real STL) still hard-fail the
build. Successful renders record a mapping in `site/.scad-map`
(`stl-name → project-dir → source-path`), a tab-separated intermediate
used by subsequent steps to group models by project.

**Render cache.** To avoid re-rendering unchanged models, the step keeps a
host-level content-addressed cache at `$HOME/.cache/3d-models/render` (override
with `RENDER_CACHE_DIR`, disable with `RENDER_CACHE_DISABLED=1`). The cache lives
outside the git workspace so `git clean` from `actions/checkout` does not wipe it
across runs on the long-lived self-hosted runner. The key (computed by
`scripts/render_cache.py`) is a SHA-256 over the renderable's full transitive
`include`/`use` chain, any binary assets it references via
`surface(file=...)`/`import(...)`, the OpenSCAD version string, and a
`CACHE_VERSION` constant. On a hit the stored STL is copied into `site/` and its
mtime refreshed; on a miss the freshly rendered STL is written into the cache
atomically (`.tmp.$$` then `mv`). Because the key is content-addressed, a hit is
byte-identical regardless of which branch populated it, so the cache is safely
shared across all builds on the host. Entries untouched for 30 days are pruned by
mtime (`touch`-on-hit + `-mtime`, not `-atime`, since runners may mount
`noatime`). Parameter manifests (`*.parameters.json`) are intentionally excluded
from the key: the precomputed STL uses the defaults baked into the `.scad` (no
`-D` overrides), so manifests never affect the precomputed geometry. If the
runner's `$HOME` is ephemeral per job every build is a cold miss (correct, just no
speedup) — point `RENDER_CACHE_DIR` at a persistent volume to retain the cache.

### 7. Validate STL Meshes

After rendering, each STL is validated using [ADMesh](https://github.com/admesh/admesh):

- **Watertight (manifold)**: No unconnected facets
- **No degenerate triangles**: Zero degenerate facets
- **Positive volume**: Ensures the mesh encloses real space

Additionally, the step extracts **bounding-box dimensions** (Min/Max X/Y/Z)
from ADMesh output and computes a **rough print-time estimate**
(`estimated_minutes`) using a heuristic based on layer count (height / 0.2mm)
and perimeter travel time (at 50mm/s). For near-flat models (`bb_z < 0.5`),
a simpler volume-based fallback (`volume / 200`) is used. Results —
including `estimated_minutes` — are written to `site/validation.json` and
reported in the PR comment as a table (model name, triangle count, volume,
pass/fail). If any model fails validation, the main-branch deploy is skipped
and the job exits with failure after the PR comment is posted — ensuring
reviewers see the full report.

### 7.3. Bundle openscad-wasm and Sources for In-Browser Customizer

Stages all assets the in-browser WASM customizer needs to function:

1. **`scripts/fetch_openscad_wasm.py`** — downloads the pinned non-threaded
   openscad-wasm release (v2022.03.20) from GitHub if not already in
   `.cache/openscad-wasm/`, verifies SHA-256 hashes of each asset, and copies
   `openscad.js`, `openscad.wasm.js`, and `openscad.wasm` into `site/openscad/`.
   Font and MCAD library files are intentionally omitted — no model in this repo
   uses `text()` or MCAD.
2. **Source files** — every `.scad` file is copied to `site/sources/<project>/`
   so the browser can fetch all include-chain files needed for a render (e.g.,
   `include <_blast_gate.scad>` resolves from `site/sources/blast-gate/`).
3. **Binary render assets** — any `.png` file whose basename literally appears in
   a `.scad` in the same directory is also copied to `site/sources/<project>/`.
   This stages `surface()` heightmaps (e.g. `nz-ski-fields/heightmap.png`) so
   the WASM FS can load them during in-browser renders. A `grep` filter prevents
   unrelated tracked PNGs (e.g. screenshots) from being staged. Assets are
   written into the wasm FS as `Uint8Array` (fetched as `arrayBuffer`, not
   `text`) by the browser loader.
4. **Parameter manifests** — validated manifests (not in `.param-failures`) are
   also copied to `site/sources/<project>/` so the browser can discover which
   parameters a model exposes.
5. **Per-project `manifest.json`** — a sorted list of `.scad` and `.png`
   filenames in each `site/sources/<project>/` directory is written as
   `manifest.json`. S3 does not serve directory indexes, so this lets the browser
   discover both library files and binary assets without needing to enumerate the
   bucket.

### 7.4. Set Up Node.js and Smoke-Test WASM Customizer

Sets up Node.js 20 and runs `scripts/test_wasm_customizer.mjs`. This test
exercises the full in-browser customizer pipeline end-to-end in a Node
environment: it loads the staged WASM assets, fetches a project's source files,
applies parameter overrides, and verifies that the resulting STL bytes are
non-empty and pass a basic header check.

### 7.5. Check Mating Part Interference

After mesh validation, pairs of STL files declared in `meta.json`'s
`mating_pairs` field are checked for geometric overlap using
`scripts/check_interference.py`. This step:

- Creates an isolated venv (`.venv-interference`) and installs `trimesh>=4.0,<5`
  and `manifold3d>=2.3,<4`
- For each mating pair, loads both STL files and performs a boolean
  intersection using `manifold3d` to detect overlap volume
- Records results to `site/interference.json` with per-pair data:
  `part_a`, `part_b`, `overlap_volume_mm3`, `passed`, and `skipped` flags
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until the final enforcement
  step (step 26)
- PR comments include an interference table showing part names, overlap
  volume, and pass/fail/skip status

This catches design errors where two parts that are supposed to fit together
actually physically overlap — impossible to assemble in the real world.

### 8. Generate Standalone HTML Viewers

Runs `scripts/generate-standalone.py`, which produces one self-contained
HTML file per model at `site/standalone/<name>.html`. The script:

- Downloads Three.js 0.170.0 assets from jsDelivr CDN (once for all models)
- Verifies SHA-256 hashes of downloaded assets; caches verified copies in
  `.cache/threejs/` with a local cache fallback if the CDN is unreachable
- Cross-checks the Three.js version against both `index.html` and `embed.html`
  import maps via `_check_threejs_version()` — exits with error if either file
  uses a different version than `THREEJS_VERSION` (prevents silent version drift
  between the two viewers)
- Base64-encodes both JS libraries and STL data into the HTML via import map
  data URIs, producing files that work from `file://` with zero dependencies

### 9. Bundle Project Zips

Groups rendered STL files by project directory (from `.scad-map`) and creates
a zip bundle for each project with **2 or more** STL files. Single-file
projects are skipped (no benefit from bundling). Zip files are named after
the project directory (e.g., `toothbrush.zip`, `power-workshop.zip`) and
use `zip -j` (junk paths) so the archive contains flat filenames without
the `site/` prefix. The zip files are deployed alongside the STLs and
referenced from `models.json`.

### 9.5. Bundle Project Source Zips

A sibling step runs immediately after step 9 and creates a source zip for
**every** project (no 2+ file threshold). For each unique project directory in
`.scad-map`, the step runs `git ls-files` to enumerate all tracked files in
that directory and archives them with their `<dir>/` path prefix preserved
(so the archive extracts into its own folder). Zip files are named
`site/<dir>-source.zip` (e.g., `toothbrush-source.zip`) to avoid colliding
with the STL bundle. Files with spaces in their names (e.g.,
`toothbrush/Toothbrush holder.scad`) are handled safely via `git ls-files -z |
xargs -0`. Only git-tracked files are included — gitignored outputs (STLs,
`.mcp-claws.json`) never enter the archive. Source zips are deployed alongside
STLs via the existing `aws s3 sync` step and referenced from `models.json` as
the optional `sourceZip` field.

### 10. Render PNG Thumbnails

For each rendered STL, finds the corresponding `.scad` source and renders an
800x600 PNG thumbnail via `scripts/capped-openscad.sh`, with a step-level
`RENDER_MEM_MAX=4G` / `RENDER_TIMEOUT=120` override (lower than the STL
render cap, since thumbnails are supplementary). Xvfb is invoked with
`--auto-servernum` and retried up to 3 times to tolerate transient `Xvfb
failed to start` errors on the self-hosted runner. Falls back to direct
rendering with a warning if `xvfb-run` is not installed.

Individual thumbnail failures — including a cap hit — emit a GitHub Actions
warning but do not fail the build — STL files are the core output,
thumbnails are supplementary.

### 10.5. Render Extra Orthographic Views for Complex-Interior Models

For any model whose project has `complex_interior: true` in `meta.json`,
three additional orthographic PNGs are rendered: `top`, `bottom`, and
`front`. Each is 800×600, saved as `site/<model-name>_<view>.png` (e.g.,
`site/drill_socket_top.png`), using `--projection=ortho --viewall
--autocenter` for consistent framing, also via `scripts/capped-openscad.sh`
with the same 4G/120s step-level cap as thumbnails. Currently only
`power-workshop` declares `complex_interior: true`.

Xvfb handling here uses a simpler fallback than step 10: if `xvfb-run` is
available the render script runs under it; if Xvfb fails to start, the
script retries without a virtual display (warning only, not a failure).
Empty or missing output PNGs are removed with a warning annotation rather
than failing the build.

### 11. Generate QR Codes

Generates a QR code PNG per model at `site/qr/<name>.png` using `qrencode`.
Each QR encodes the model's deep link URL
(`https://www.bstjohn.net/3d-models/#<project-slug>/<model-slug>`). The
slugify logic replicates the JS `slugify()` in Bash. QR images use the site's
dark theme colors (`--foreground=E0E0E0 --background=1A1A2E`), module size 8,
and margin 2. QR codes are stored in a separate `site/qr/` directory to avoid
polluting the `site/*.png` glob used by the OG hero image step. Failures
emit a warning but don't break the build (same pattern as thumbnails).

### 12. Generate OG Hero Image

Composites the rendered PNG thumbnails into a single 1200×630 `og-hero.png`
for Open Graph social previews. Uses ImageMagick `montage` to tile thumbnails
in a 3-column grid against the site's dark background (`#1a1a2e`). If no
thumbnails exist (all renders failed), falls back to a solid-color image with
text using `convert`.

The image is deployed to a stable URL (`/3d-models/og-hero.png`) — it is
intentionally not cache-busted so social media crawlers can cache it reliably.

### 13. Generate Models Manifest

A Python script reads `site/.scad-map` and produces `site/models.json`:

```json
{
  "Project Name": {
    "dir": "project-dir",
    "files": [
      {
        "stl": "file.stl",
        "source": "project-dir/file.scad",
        "estimated_minutes": 25,
        "qr": "qr/file.png",
        "parameters": { "parameters": [{ "name": "pvc_od", "type": "number", … }] }
      }
    ],
    "zip": "project-dir.zip",
    "sourceZip": "project-dir-source.zip",
    "description": "Project description from meta.json",
    "tags": ["tag1", "tag2"],
    "difficulty": "beginner",
    "version": "1.0.0",
    "hardware": [{"item": "M5 bolt", "quantity": 1}],
    "rendered_with": "OpenSCAD 2024.12.06"
  }
}
```

Project names are derived from directory names (hyphens/underscores → spaces,
title-cased). The `zip` field is only present when a zip bundle was generated
(projects with 2+ files). The `sourceZip` field is present for every project
that has tracked source files; it references the per-project source zip
produced by step 9.5. The `estimated_minutes` field is merged from
`validation.json`. The `qr` field is present only when the QR PNG exists.
The `parameters` field is present on a file entry when a validated
`<basename>.parameters.json` manifest exists next to the `.scad` source; its
presence tells the viewer to show the ⚙ Customize button for that model.
Manifests in `.param-failures` are excluded — the customizer never loads an
invalid parameter set. Metadata fields (`description`, `tags`, `difficulty`,
`version`, `hardware`) are merged from `meta.json` if the file exists and
passed schema validation.
The `rendered_with` field records the OpenSCAD version used to produce the
STLs (e.g. `"OpenSCAD 2024.12.06"`), sourced from `site/openscad-version.txt`
written by the version-check step. This field is diagnostic documentation:
if a user reports that a printed part doesn't fit, knowing which OpenSCAD
version produced the STL helps isolate whether it's a source issue or a
renderer regression.
The viewer reads this manifest to populate the gallery and conditionally show
features.

### 13.5. Generate sitemap.xml

After the models manifest is written, a Python snippet reads `site/.scad-map`
via `oembed_helpers.parse_scad_map()` and generates `site/sitemap.xml` — a
standard `<urlset>` listing the gallery root and one `<url>` per standalone
viewer (`/standalone/<model>.html`). URLs are built from `BASE_URL` in
`oembed_helpers.py` and the standalone filenames are URL-encoded with
`urllib.parse.quote`. The sitemap is deployed to `/3d-models/sitemap.xml`; as
with `robots.txt`, crawlers only read the authoritative copy at the origin root
(`/sitemap.xml`), which requires a separate infra step.

### 14. Generate README Gallery (main branch only)

Runs `scripts/generate-gallery.py`, which reads `site/models.json` and
per-project `meta.json` descriptions to generate a visual gallery table in
`README.md` between `<!-- gallery:start -->` and `<!-- gallery:end -->`
markers. Each row has a thumbnail, project link, model count, and description.
On PRs, the script is smoke-tested (run then reverted with `git checkout`)
to catch breakage without modifying the PR.

### 15. Generate Structured Data

A Python script reads `site/.scad-map` and `site/validation.json` to produce
`site/structured-data.json` — a Schema.org JSON-LD object using
`CollectionPage` with an `ItemList` of `3DModel` entries. Each model gets
`contentUrl`, `encodingFormat` (model/stl), `thumbnailUrl`, `contentSize`,
`isPartOf` (project grouping), and `creator`. Project descriptions from
`meta.json` are used when available (skipping files in `.meta-failures`).
Absolute URLs are required by JSON-LD spec. Uses shared helpers from
`scripts/oembed_helpers.py`.

### 16. Generate OEmbed JSON Files

A Python script reads `site/.scad-map` and generates one OEmbed JSON file per
model at `site/oembed/<project-slug>/<model-slug>.json`. Each file is a
standard OEmbed v1.0 "rich" type response containing:

- `title`: Model display name and project (e.g., "Drill Bit – Power Workshop")
- `html`: An `<iframe>` snippet pointing to `embed.html#<project>/<model>`
  with `sandbox="allow-scripts allow-same-origin"`
- `thumbnail_url`, `thumbnail_width`, `thumbnail_height`: PNG preview reference
- `width`, `height`: Embed dimensions (800×600)
- `provider_name`, `provider_url`: Site identity

The slugify logic is imported from `scripts/oembed_helpers.py` and matches
`index.html` exactly: strip `.stl`, replace `[_\s]+` with `-`, lowercase.

### 17. Generate Changed Projects List (PR only)

Diffs the PR commit to find changed `.scad` files, extracts their top-level
directories, and writes `site/changed.json` — an array of project names.
The viewer uses this to auto-expand sections for changed models and collapse
unchanged ones.

### 18. Copy Static Assets and Inject Data

Copies `index.html`, `embed.html`, and `openscad-worker.js` to `site/`,
replacing the `__BUILD_HASH__` placeholder with the first 8 characters of the
commit SHA for cache busting. (`openscad-worker.js` uses the same placeholder
for its dynamic import of `openscad.js` so the worker's asset fetch is also
cache-busted.) Also copies unchanged static assets to `site/`:
`filament-colors.json`, `favicon.svg`, `site.webmanifest`, `robots.txt`,
and `llms.txt`. Then a Python script:

1. Reads `site/structured-data.json` and replaces the
   `<!-- __STRUCTURED_DATA__ -->` placeholder with a
   `<script type="application/ld+json">` block containing the JSON-LD.
2. Reads `site/.scad-map` and generates `<link rel="alternate"
   type="application/json+oembed">` tags for each model, replacing the
   `<!-- __OEMBED_LINKS__ -->` placeholder. Each tag references the
   corresponding OEmbed JSON endpoint (e.g.,
   `oembed/power-workshop/drill-bit.json`).

   **Limitation**: Because all `<link>` tags are injected into a single
   `index.html`, OEmbed auto-discovery does not work for individual model
   deep links (e.g., `index.html#power-workshop/drill-bit`). Hash
   fragments are not sent to the server, so a crawling platform receives
   all `<link>` tags and cannot correlate the fragment to a specific
   endpoint. For per-model OEmbed, platforms must be configured with
   explicit endpoint URLs (e.g., WordPress OEmbed allowlists) rather
   than relying on `<link>` discovery.

### 19. Install AWS CLI

Checks if `aws` is already available; if not, downloads and installs the
AWS CLI v2 from the official zip archive. Follows the same conditional-install
pattern as OpenSCAD and ImageMagick.

### 20. Deploy to S3

Uses OIDC (`aws-actions/configure-aws-credentials@v4`) with the
`AWS_ROLE_ARN` secret.

- **Main branch**: `aws s3 sync ./site s3://www.bstjohn.net/3d-models/ --delete`
  (excludes `pr-preview/`). Gated on mesh validation **and** metadata
  validation passing — broken meshes or invalid metadata never reach production.
- **Pull requests**: `aws s3 sync ./site s3://…/pr-preview/pr-{N}/{SHA}/`.
  PR deploys are not gated on validation so reviewers can inspect broken
  models in the 3D viewer.

### 21. Commit README Gallery Update (main branch only)

After a successful deploy, if the gallery script produced changes to
`README.md`, the step commits and pushes the update using the
`github-actions[bot]` identity. The commit message includes `[skip ci]`
to prevent an infinite CI loop. Uses `git pull --rebase` before pushing
to handle concurrent pushes. Gated on both the gallery step succeeding
and mesh validation passing. Uses `continue-on-error: true` so a push
race condition doesn't fail the entire workflow.

### 22. Comment on PR (PR only)

Posts or updates a bot comment on the PR with:
- A link to the interactive preview deployment
- PNG thumbnails of models changed in the PR, grouped by project
- A mesh validation table (model name, triangle count, volume, pass/fail)
- **File size and triangle count** for each changed model, displayed next to
  the model name (e.g., "45.2 KB · 3,456 triangles"). Triangle count is
  parsed from the binary STL header (bytes 80–83, little-endian uint32) and
  validated against the expected file size (`84 + triangles × 50`). If
  validation fails (e.g., ASCII STL), only the file size is shown.
- A collapsible `<details>` block listing links to all previous preview
  deployments for the PR in reverse-chronological order, parsed from the
  existing comment text using a regex pattern.

Uses `actions/github-script@v7`. Finds and updates an existing bot comment
(matched by the "Model Preview" heading) to avoid duplicate comments on
subsequent pushes.

The step uses `continue-on-error: true` so transient GitHub API failures
don't fail the entire workflow. All three GitHub API calls (`listFiles`,
`paginate(listComments)`, `createComment`/`updateComment`) are wrapped in a
`withRetry(fn, retries=3, delayMs=2000)` helper that retries with linear
backoff (delay × attempt number) on error.

### 23. Enforce Mesh Validation

If the validate step recorded any failures, this step exits with an error
after all other steps (thumbnails, manifests, PR comment, deploy) have
completed. This ensures the full report is visible to reviewers before the
job fails.

### 24. Enforce Dependency Graph Check

If the dependency graph verification (step 1) recorded a failure, this step
exits with an error telling the contributor to regenerate. Placed after all
other steps so the full pipeline output (renders, PR comment, deploy) is
available even when graphs are stale.

### 25. Enforce Metadata Validation

If the metadata validation (step 2) recorded a failure, this step exits with
an error indicating which `meta.json` files don't match the schema.

### 26. Enforce Interference Check

If the mating part interference check (step 7.5) recorded a failure, this
step exits with an error indicating which part pairs have geometric overlap.

### 27. Enforce Parameters Validation

If the parameters manifest validation (step 2.5) recorded a failure, this
step exits with an error and prints `.param-failures` so the contributor
knows which manifests to fix.

All five enforcement steps (mesh validation, dependency graph, metadata,
interference, and parameters) use `if:` conditions and run independently — if
multiple fail, all errors are visible.

## Design Decisions

- **Capped OpenSCAD renders**: Every `openscad` invocation in the render
  steps (STL, thumbnails, orthographic views) runs through
  `scripts/capped-openscad.sh`, which wraps the call in a `systemd-run
  --user --scope -p MemoryMax=...` cgroup plus a `timeout`, falling back to
  `ulimit -v` + `timeout` on runners without a working `systemd-run --user`
  session. This turns a runaway render (heavy CSG, a cold cache, an
  under-provisioned runner) into a clean, logged step failure instead of a
  frozen self-hosted runner — the pipeline's original exposure (issue #272).
  `RENDER_MEM_MAX`/`RENDER_TIMEOUT` default to `28G`/`3600s` at the workflow
  level for STL renders (sized for the heaviest models — the full-res
  `nz-ski-fields` part renders — on the 32 GB ryzen runner; see the env-block
  comment in `build.yml`) and are overridden to
  `4G`/`120s` at the step level
  for thumbnails and orthographic views. On a cap hit the wrapper prints
  `render exceeded memory/time cap` to stderr; the STL render step checks
  the exit code (`124` timeout, `>=128` SIGKILLed) **before** its
  library-detection heuristics, because those exit codes would otherwise be
  misclassified as "suspected library" and silently skipped — see the
  Render STL Files step. The build job is pinned to `[self-hosted, linux,
  ryzen]` rather than any `[self-hosted, linux]` box so the memory cap is
  calibrated against a host of known RAM capacity; `notify-failures.yml` is
  deliberately left unpinned so failure notifications still fire when
  `ryzen` is down.
- **Library detection**: Uses a three-tier strategy: (1) underscore-prefixed
  files are skipped by convention, (2) OpenSCAD's "top level object is
  empty" / "nothing to export" log output identifies libraries at render
  time, (3) a fallback heuristic catches edge cases where OpenSCAD exits
  non-zero with no real output (≤84 bytes). These tiers only run after the
  render-cap check above rules out a timeout/OOM exit. Output is captured
  via file redirect (`> /tmp/scad.log 2>&1`) rather than piped through
  `tee`, so OpenSCAD's exit code is preserved for the error-handling logic.
- **CI-generated zip bundles**: Zip files are pre-built in CI and deployed
  as static assets alongside STLs, rather than generated client-side. This
  fits the project's fully-static architecture — no new client-side
  dependencies. Only projects with 2+ files get a zip (single-file projects
  don't benefit from bundling).
- **Conditional dependency install**: Each tool (OpenSCAD, ImageMagick,
  ADMesh, qrencode, AWS CLI) checks `command -v` before installing. On a
  pre-configured self-hosted runner this is a no-op; on a fresh runner,
  dependencies are installed automatically.
- **Xvfb environment preparation**: A dedicated step (3.5) cleans stale X
  lock files (`/tmp/.X*-lock`, `/tmp/.X11-unix/`) before any rendering begins.
  Long-lived self-hosted runners accumulate stale locks from previously
  interrupted jobs; without cleanup, `xvfb-run` fails with "Server is already
  active" on the fixed display number. The step recreates `/tmp/.X11-unix/`
  with the sticky bit (`chmod 1777`) to restore standard X11 permissions.
- **Graceful xvfb degradation**: The PNG rendering step checks for `xvfb-run`
  availability rather than assuming it's installed. This ensures the pipeline
  still produces STL files even if the runner cannot generate thumbnails.
- **Complex-interior orthographic views**: Models with `complex_interior: true`
  get three extra orthographic PNGs (`_top`, `_bottom`, `_front`) to expose
  internal cavity geometry that the default isometric thumbnail obscures. These
  are supplementary; build failures do not propagate from this step. The flag
  lives in `meta.json` so no CI code change is needed when adding a new
  complex-interior model.
- **Stable OG image URL**: The `og-hero.png` URL is not cache-busted (unlike
  other assets). Social media crawlers cache by URL, so a stable path ensures
  previews update when the image content changes rather than producing stale
  entries for old URLs.
- **Fail-fast verification**: `openscad --version` runs after the install
  step to surface installation failures immediately with a clear error message.
- **Deferred enforcement pattern**: Mesh validation, dependency graph checks,
  and metadata validation all use the same non-blocking pattern: the check
  step records `failed=true` to `$GITHUB_OUTPUT` and emits a warning
  annotation, then a separate enforcement step at the end of the pipeline
  reads that output and calls `exit 1`. This allows the full pipeline
  (renders, thumbnails, manifests, PR comment, deploy) to complete before
  any enforcement step fails the job. Reviewers see the complete report even
  when checks fail. All three enforcement steps run independently — if
  multiple fail, all errors are visible.
- **Build-time structured data injection**: Schema.org JSON-LD is generated
  from `site/.scad-map` at build time and injected into the static HTML via
  placeholder replacement, following the same pattern as `__BUILD_HASH__`.
  This ensures the structured data is present in the initial HTML response
  (best practice for SEO) without requiring runtime JS generation.
- **PR deploy not validation-gated**: PR preview deployments proceed even
  when mesh or metadata validation fails, so reviewers can inspect the broken
  model in the 3D viewer. Only main-branch deploys are gated.
- **Static OEmbed endpoints**: OEmbed JSON files are generated at build time
  as static files (`oembed/<project>/<model>.json`) rather than requiring a
  server-side endpoint. `<link rel="alternate">` discovery tags are injected
  into `index.html` for completeness, but since all tags live in a single
  page, auto-discovery only works for the site root — not for individual
  model deep links (hash fragments aren't sent to the server). For per-model
  OEmbed, consuming platforms should be configured with explicit endpoint
  URLs. A dedicated `embed.html` provides a minimal iframe-friendly viewer
  without the full gallery UI.
- **Standalone viewer SHA-256 verification**: Three.js assets downloaded for
  standalone HTML generation are verified against pinned SHA-256 hashes to
  prevent supply-chain attacks from the CDN. A local cache (`.cache/threejs/`)
  avoids re-downloading on subsequent runs, with the cached copy also verified.
- **QR codes in separate directory**: QR PNGs are stored in `site/qr/` rather
  than alongside model thumbnails in `site/` to avoid being picked up by the
  OG hero image `montage` glob (`site/*.png`).
- **PR comment resilience**: The comment step uses `continue-on-error: true`
  and a `withRetry(fn, retries=3, delayMs=2000)` helper so transient GitHub
  API errors (rate limits, network blips) don't fail the workflow. The
  comment also preserves a history of prior preview links in a `<details>`
  block, parsed from the existing comment on each update.
- **README gallery auto-commit**: The gallery update uses `continue-on-error`
  and `[skip ci]` to prevent CI loops and tolerate push race conditions. The
  gallery is only committed on successful main-branch deploys (gated on
  validation passing). A separate smoke-test step on PRs catches gallery
  script regressions without modifying the PR branch.
- **Metadata schema with deferred enforcement**: `meta.json` validation uses
  the same deferred pattern as mesh validation. Invalid files are tracked in
  `.meta-failures` so downstream steps (manifest, structured data) can skip
  them rather than propagating bad data. The schema uses
  `additionalProperties: false` to catch typos early.
- **OpenSCAD version tracking**: The `.openscad-version` file commits the
  expected OpenSCAD version string (exact output of
  `openscad --version 2>&1 | head -1`) to the repo. CI captures the runner's
  actual version and compares; on mismatch, a `::warning::` annotation is
  emitted. The file is
  **not** auto-updated by CI to avoid commit loops — the maintainer updates
  it manually when the runner is upgraded. The `rendered_with` field in
  `models.json` records the actual version used for each build, serving as
  diagnostic documentation when reported parts don't fit.
- **Shared Python helpers**: `scripts/oembed_helpers.py` centralizes
  `slugify()`, `display_name()`, `thumbnail_name()`, `parse_scad_map()`, and
  `load_meta_failures()` used by multiple CI steps (structured data, OEmbed,
  link tag injection, interference check). This prevents slug logic drift and
  ensures `.meta-failures` loading is consistent across all consumers.
- **Three.js version consistency across viewers**: `generate-standalone.py`'s
  `_check_threejs_version()` validates both `index.html` and `embed.html`
  against `THREEJS_VERSION`. Both files hardcode CDN URLs independently, so a
  version bump in one without the other would silently run mismatched versions.
- **Mating part interference checking**: `check_interference.py` uses
  `trimesh` and `manifold3d` to perform boolean intersection on STL pairs
  declared in `meta.json`'s `mating_pairs` field. This catches design errors
  where two parts that should fit together physically overlap. Results are
  stored in `site/interference.json` and displayed in the PR comment as a
  table with overlap volume in mm³. The step uses the same deferred
  enforcement pattern as mesh and metadata validation — failures are
  recorded early but only block the build at the final enforcement step
  (step 27), so the full pipeline output is always available.
- **Parameters manifest deferred enforcement**: `*.parameters.json` validation
  (step 2.5) follows the same deferred pattern. Failures go to `.param-failures`;
  the manifest generation step reads that file and excludes invalid manifests from
  `models.json` so the customizer never loads a broken parameter set. Enforcement
  fires at step 27 (the last step) so the full pipeline output is always available
  even when a manifest is malformed.
- **Non-threaded openscad-wasm build**: The customizer uses the non-threaded
  WASM build (`openscad.js` / `openscad.wasm`) rather than the threaded build.
  The threaded build requires `SharedArrayBuffer`, which requires COOP/COEP
  response headers that plain S3 hosting cannot set without a CloudFront
  function. Non-threaded avoids this dependency at the cost of slightly slower
  renders (no SIMD parallelism). Assets are pinned to release `2022.03.20` with
  SHA-256 verification in `scripts/fetch_openscad_wasm.py`.
- **Filename allow-list in render step**: Before rendering any `.scad` file,
  the basename is checked against `^[A-Za-z0-9._ -]+$`. Filenames with
  characters outside this set would propagate into generated STL paths, HTML
  snippets, and JSON, creating potential injection vectors. Hard-failing early
  is safer than escaping every downstream consumer.
- **DOM API over innerHTML in viewers**: `index.html` and `embed.html` use
  `createElement` / `textContent` / `setAttribute` for all content derived
  from `models.json` (model names, STL URLs, QR paths). `innerHTML` is only
  used for static SVG icons that contain no external data. This prevents XSS
  even if the CI filename allow-list is ever bypassed or `models.json` is
  tampered with. The two defenses are independent layers.
- **Sitemap generated from `.scad-map`**: `sitemap.xml` is produced by CI
  rather than maintained by hand. It lists the gallery root and every
  standalone viewer URL, keeping it in sync with what's actually deployed
  without requiring manual updates when models are added or removed.
- **Static web assets at repo root**: `favicon.svg`, `site.webmanifest`,
  `robots.txt`, and `llms.txt` live at the repo root and are copied to `site/`
  during CI (step 18), just like `index.html` and `filament-colors.json`.
  Keeping them as committed source files means they are version-controlled and
  reviewable via PR, while the copy step ensures they land in the deployed
  directory.
- **Fresh WASM instance per render**: Each customizer render creates a new
  emscripten instance via the factory (the factory itself is cached). Reusing
  one instance across renders causes silent "empty STL" failures because
  emscripten's `exit()` call at the end of `callMain` corrupts the module's
  internal FS state. A new instance per render is more expensive but reliable.
- **Unit tests run in CI**: `python3 -m unittest test_render_view
  test_oembed_helpers test_fetch_openscad_wasm test_render_cache` runs on every push (step 2.6)
  before any heavy tools are invoked. These tests mock I/O and finish
  in seconds, catching regressions in build-script helpers before rendering
  begins.
- **site/sources/ layout**: All `.scad` source files, validated
  `*.parameters.json` manifests, and binary render assets (`.png` files whose
  basename appears in a sibling `.scad`) are staged under
  `site/sources/<project>/` during CI (step 7.3). A per-project `manifest.json`
  lists all `.scad` and `.png` filenames because S3 does not serve directory
  indexes. The browser's `loadProjectSources()` function fetches this manifest to
  discover all project files; `.scad` entries are fetched as text and written into
  the WASM FS as UTF-8; `.png` entries are fetched as `arrayBuffer` and written as
  raw bytes so `surface()` can read them.

## Failure Notification Workflow

Defined in `.github/workflows/notify-failures.yml`. Triggers on
`workflow_run` completion of `Build Models` on the `main` branch — allowing
it to observe build outcomes without requiring `contents: write` on the
build workflow itself.

### `notify` job (on failure)

Runs when `build.yml` fails on `main`:

1. Creates the `bug` label (`#d73a4a`) if it doesn't already exist — avoids
   failures in repos where the default label set was not created.
2. Searches for an existing open issue titled `"Build failure: Build Models"`.
   If none is found, creates one via `gh issue create` with a link to the
   failed run URL.
3. Deduplication prevents a flood of issues during a prolonged outage — only
   one open issue exists at a time.

### `close-on-success` job (on recovery)

Runs when `build.yml` succeeds on `main`:

Searches for the open failure issue and, if found, closes it with a
`"Build recovered — closing automatically."` comment. This gives the issue
a clear lifecycle: opened on first failure, closed on the next successful run.

### Design notes

- **`cancel-in-progress: false`** on both concurrency groups — notification
  runs must not be cancelled mid-flight (a skipped notification is a missed
  alert).
- **`branches: [main]`** on the `workflow_run` trigger scopes the listener to
  main-branch builds only; PR failures do not generate issues.
- **No `actions: read` permission** is needed because all required data
  (`workflow_run.conclusion`, `workflow_run.html_url`) comes directly from the
  event payload, not from an API call.
