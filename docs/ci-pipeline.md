# CI/CD Pipeline

**Depth: Reference.** Read this when you're touching `build.yml` or any
build/CI step and need the exact step order, env vars, or validation rules.
For a repo-wide summary read [OVERVIEW.md](OVERVIEW.md) instead.

Product requirements: [PRODUCT.md](PRODUCT.md#cross-cutting-constraints)

Defined in `.forgejo/workflows/build.yml` and run by Forgejo Actions at
`https://git.home.bstjohn.net/St-John-Software/3d-models/actions`. Runs on a
container-family runner on push
to `main`, on PRs, and on push to `claws/preview-issue-*` (see
[Issue previews](#issue-previews-pr-less)).

## Workflows

Four workflow files live in `.forgejo/workflows/`:

- **`build.yml`** — the main build pipeline, documented in detail below.
- **`pr-preview-cleanup.yml`** — deletes a PR's `pr-preview/pr-{N}/` S3
  prefix on close, and an issue preview's `issue-preview/{id}/` prefix when
  its `claws/preview-issue-{id}` branch is deleted; see step 18 below.
- **`render-heavy.yml`** — on-demand (`workflow_dispatch`) job on
  `[container, linux, ram-12g]` that renders the heavy models `build.yml`
  deferred and stores them in the S3 render cache; see
  [render-heavy.yml](#render-heavyyml) below.
- **`pages.yml`** ("Spec Pages") — checks the project spec pages under
  `pages/` and publishes them to the private pages host on push to `main`
  and on same-repo PRs; see [pages.yml (spec pages)](#pagesyml-spec-pages)
  below. `build.yml` ignores `pages/**`, so a pages-only change never
  renders models.

Main-branch failures of `build.yml` are not tracked by a workflow in this
repo. See [Main-branch failure monitoring](#main-branch-failure-monitoring).

## Trigger and Concurrency (`build.yml`)

- **Triggers**: `push` to `main` or `claws/preview-issue-*` (see
  [Issue previews](#issue-previews-pr-less)), `pull_request` (opened,
  synchronize, reopened).
  Documentation-only changes are skipped via `paths-ignore` (`docs/**`,
  `ideas/**`, root `*.md`, `LICENSE`); a run is skipped only when *all*
  changed files match those patterns, so any PR that also touches a `.scad`,
  script, or site source still builds.
- **Runner**: `[container, linux]` — not pinned to a single runner
  name and never tier-labelled. Forgejo's container runners are three
  in-cluster dind pods defined in St-John-Software/fleet-infra
  `clusters/my-cluster/privileged-infra/forgejo-runner/`: `forgejo-runner`
  on `k3s` (6g per job), `-ryzen` and `-nas` (12g per job). The label
  families and each runner's tiers are in fleet-infra's
  [runner-labels.md](https://git.home.bstjohn.net/St-John-Software/fleet-infra/src/branch/main/docs/runner-labels.md). Every job runs in
  a fresh job container, so `$HOME` and the nix store start cold on every
  run: the devShell closure is downloaded afresh (several extra minutes
  until a LAN nix cache exists) and the render cache comes from S3 (step
  5). The job may land on any of the three pods. It never attempts a
  renderable marked heavy (`render_memory_gb` in `meta.json`) whose cache
  miss needs more than the runner's advertised job memory cap: it defers it
  to `render-heavy.yml` on a `ram-12g` runner (ryzen or nas) and fails at
  the end with a message saying to re-run once that has finished (step 5,
  "Heavy renders"). Cached and light renders still run anywhere, including
  the `k3s` pod while ryzen and nas are off. fleet-infra sizes the ryzen
  and nas dind containers at 28Gi and 32Gi for two 12g jobs each, so
  `RENDER_MEM_MAX` (28G; the heaviest measured render peaked above 8G RSS
  over ~31 min) is above every per-job limit, and every runner pod's
  `runner.timeout` is 3h, since a fully cold render exceeds the 1h
  default. A render that hits its job container's memory limit is
  OOM-killed (exit `>=128`; a hard step failure for an unmarked
  render, a deferral for a marked one) rather than freezing the host. The job container has no `systemd-run`, so
  `scripts/capped-openscad.sh` takes its `ulimit -v` + `timeout` fallback
  and prints a warning — accepted. The job container provides almost
  nothing beyond `nix`, `git`, and `docker`. Every tool the job shells out to — OpenSCAD (a
  headless EGL/llvmpipe wrapper), ImageMagick, ADMesh, qrencode, Python 3,
  Node.js, and the AWS CLI — comes from this repo's own `flake.nix`
  `default` devShell instead, entered via the job-level
  `defaults.run.shell` (`nix develop ...#default --command bash -euo
  pipefail {0}`), so every `run:` step executes inside it automatically. If
  the runner has no `nix` at all, step 0 (Set up Nix) fails the build
  immediately with a pointer to fix the runner rather than attempting to
  install anything itself.
- **Checkout depth**: `actions/checkout` runs with `fetch-depth: 0`. The models
  manifest step calls `scripts/project_dates.py`, which asks `git log` for the
  last-commit date of each project directory to populate `updated` for the
  landing page's recency ordering (issue #345). A shallow clone doesn't fail —
  `project_updated()` returns `{}`, every `updated` is omitted and the gallery
  falls back to interest-only ordering — so the degradation is silent. Don't
  drop the setting.
- **Concurrency**: Groups by `pages-main`, `pages-pr-{N}`, or
  `pages-refs/heads/claws/preview-issue-{id}` (the full ref, so the cleanup
  workflow can rebuild it from either form of a `delete` event's `ref`). In-progress runs are cancelled when a new
  commit arrives.
- **Permissions**: `contents: write`, `pull-requests: write`, `id-token: write`
  (OIDC for AWS). `contents: write` is needed for the README gallery auto-commit
  on main-branch pushes. Forgejo ignores `permissions:` (the block is kept;
  it is harmless) and only mints an Actions ID token when the workflow sets
  `enable-openid-connect: true`, which both workflows do at top level.
  Tokens are issued by `https://www.bstjohn.net/forgejo-oidc`; see
  [Forgejo cutover](#forgejo-cutover).
- **Remote actions** are full `https://github.com/<owner>/<repo>@<sha> #
  vX.Y.Z` URLs; `./.github/actions/setup-nix` is a local composite action
  Forgejo resolves by path.

## Pipeline Steps

### 0. Set up Nix

Runs `.github/actions/setup-nix` — a small composite action shared with
`nixos-config`, which Forgejo resolves by path — as the very first step after checkout, before any step
that relies on the devShell being resolvable. It puts the runner's system
`nix` binary on `PATH` (checking
`/nix/var/nix/profiles/default/bin/nix` first, falling back to whatever
`nix` already resolves) and emits `::error::` naming the runner defect if
neither is found, then exits non-zero. In a Forgejo job container its
`command -v nix` branch is the one that fires. This is a fail-fast precondition, not
a deferred check — like the old python3 check it replaced, it hard-fails
immediately rather than recording the failure for a later enforcement step,
since every other step in the job runs inside `nix develop` and would
otherwise fail with a confusing error once that resolution fails.

The job also sets `LD_LIBRARY_PATH: ""` at workflow level. Runner units
export the nix-ld library dir there for pip wheels; it overrides nix RUNPATH,
so after the host moved to glibc 2.43 the flake's glibc-2.42 `openscad`
loaded host libraries and died with `GLIBC_2.43 not found` (run
37439885318). This repo takes all dependencies from nixpkgs and needs no such
path.

Every subsequent `run:` step executes inside `nix develop
${{ github.workspace }}#default --command bash -euo pipefail {0}` (the
job-level `defaults.run.shell`), which resolves the `default` devShell from
this repo's `flake.nix`. That devShell — not the runner host — is what
actually provides `openscad`, `admesh`, `python3`, `node`, `imagemagick`,
`zip`, `qrencode`, and `aws`. There are no more `command -v`
preflight steps for any of these (the old "Check build dependencies", "Check
ADMesh", and "Check AWS CLI" steps, and the Xvfb-preparation step, are gone
entirely): if a tool is missing from `flake.nix`, `nix develop` still
succeeds (it just doesn't put that tool on `PATH`) and the step that needs it
fails with a plain `command not found` — so a new tool must be added to
`flake.nix` before a step can shell out to it, not discovered via a
preflight check. See the root agent instructions in `AGENTS.md`.

### 1. Verify Dependency Graph

Runs `scripts/scad-dep-graph.sh` and checks whether the per-project
`dependency-graph.md` files (e.g., `power-workshop/dependency-graph.md`) are
up to date. If they differ, the step emits a `::warning::` annotation and
records `failed=true` in its step output — but does **not** fail the build
immediately. The working tree is restored via `git checkout` so subsequent
render steps aren't affected. Enforcement is deferred to step 22 at the end
of the pipeline, following the same pattern as mesh validation. This step has
no external dependencies (pure Bash + grep) and runs instantly.

### 2. Validate Project Metadata

Validates all `*/meta.json` files against `meta.schema.json` using the
`jsonschema` library from the flake's `default` devShell (pinned by
`flake.lock`, issue #423). The step:

- Handles both JSON parse errors and schema validation errors
- Records failed file paths to `.meta-failures` so downstream steps
  (models.json generation, structured data) can skip invalid entries
- Fails a `hero` or a `render_memory_gb` key that names no existing
  non-underscore renderable in the project
- Fails any `render_memory_gb` mark above the `ram-<N>g` tier in
  `render-heavy.yml`'s `runs-on` (`render_memory.check_tier`; also
  `python3 scripts/render_memory.py check-tier`), since no runner that
  workflow waits for could render it
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until the final enforcement
  step

### 2.5. Validate Parameters Manifests

Validates all `*/*.parameters.json` files against `parameters.schema.json`
using the same flake-provided `jsonschema` as step 2. The
step:

- Performs schema validation (only `number` and `boolean` types permitted)
- Cross-validates each manifest:
  - For `number` parameters: `max >= min`, and `default` must be within
    `[min, max]`
  - The manifest filename must correspond to a renderable `.scad` in the same
    directory (no underscore-prefixed files, i.e. library files cannot have
    manifests)
  - Every input in the manifest's own renderable's transitive
    `include`/`use` chain must be stageable for the browser
    (`unstageable_inputs_for(scad_path, project_dir)` in
    `scripts/external_assets.py`, which walks the chain via
    `render_cache.collect_inputs`). Stageable means an existing `.scad` or
    `.png` inside the repository — the same rule the staging step (6.3)
    applies, so the check passes exactly when the customizer can resolve
    every file. A cross-project library include
    (`include <../drawer-organiser/_drawer_organiser.scad>`) is stageable; a
    scan reference mesh `import()`ed from `scans/` (issue #439) or a missing
    include is not, so such a model must not ship a parameters manifest at
    all. Only that renderable loses its manifest — siblings in the same
    directory keep their ⚙ Customize button
- Records failed file paths to `.param-failures` (always creates the file, even
  when there are no manifests, so the enforce step's check is reliable)
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until step 25

### 2.6. Run Python Unit Tests for Build Scripts

Runs `python3 -m unittest discover -s scripts -p 'test_*.py' -v` from the
repo root. These are fast unit tests that mock external I/O (network,
filesystem) and run on every push. They guard the helper functions used
throughout the CI pipeline against regressions. `test_generate_standalone`
guards the two escaping layers in `generate-standalone.py`'s
`_load_filament_colors_js`, `test_scad_orientation` pins the
no-top-level-`rotate([-90,0,0])` source rule, `test_scad_fonts` pins the
no-`text()`/no-font rule, `test_output_names` pins renderable basename
uniqueness across all projects and per-project slug uniqueness (issue #449)
— this step runs before step 5's render, so a collision fails the build
before any STL is written, and `test_generate_gallery` covers
`pick_thumbnail` hero selection.

Discovery (issue #457) picks up every `scripts/test_*.py` automatically, so
a newly added test module can never silently go unrun — `test_build_workflow.py`'s
`UnitTestStepCoverageTests` pins the discovery invocation itself and asserts
no module is named by hand in the step. `test_sync_public_snapshot` and
`test_fetch_terrain_heightmap` (now that `pillow`/`requests` are in the
`default` devShell) run here for the first time. `test_scan_masks`' pure
helper tests (`parse_ellipse`, `mask_filename`) also run here; only
`MaskGeometryTests` self-skips via `unittest.skipUnless`, since it needs
`opencv4`, which only the `scan` devShell provides — run those with
`nix develop .#scan --command python3 -m unittest scripts/test_scan_masks.py`.
`test_check_interference` is discovered here too, in addition to its
dedicated pre-flight run immediately before `check_interference.py` (step
6.5) — the duplicate run costs milliseconds and touches nothing in the
workspace.

### 3. Verify Headless OpenSCAD Rendering

A smoke test that proves the flake's `openscadHeadless` wrapper (see
`flake.nix`) actually produces a PNG on this runner, instead of waiting to
find out from 50+ warnings in the thumbnail step much later in the
pipeline. It renders a bare `cube(10);` through `scripts/capped-openscad.sh`
(capped at `4G`/`120s`) to a tiny 64x48 PNG, then checks the output's first
8 bytes against the PNG magic number (`89504e470d0a1a0a`) rather than
relying on file size alone. There is no Xvfb or X server involved — the
wrapper forces OpenSCAD onto the EGL/llvmpipe software-GL path
(`LIBGL_ALWAYS_SOFTWARE`, a pinned Mesa EGL vendor JSON, `QT_QPA_PLATFORM=
offscreen`, `DISPLAY` unset), so this step is purely checking that the
wrapper itself still works, not that a virtual display started.

The step's own `id` (`gl_smoke`) exposes a `headless_gl` output
(`true`/`false`). It is entirely non-blocking: `continue-on-error: true` on
the step, `|| true` on the render itself, and a `::warning::` (never
`::error::`) if the PNG check fails, pointing at the `openscadHeadless`
wrapper in `flake.nix` for diagnosis. Build-blocking decisions for actual
thumbnail rendering belong to the deferred-enforcement step(s) later in the
pipeline, not to this smoke test.

### 4. Check OpenSCAD Version

Probes `command -v openscad`, then captures the version via
`openscad --version 2>&1` without letting `set -e` swallow a failure: if the
command fails or prints nothing, the step logs an `::error::` with the exit
code, resolved binary path, `LD_LIBRARY_PATH` and the full output, then exits
1 (a fail-fast toolchain precondition). Otherwise it keeps the first line and
compares it against the version string committed to `.openscad-version` at the repo root. This
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

### 5. Render STL Files

Finds all `.scad` files (excluding `.github/`) and renders each to
`site/{name}.stl` via `scripts/capped-openscad.sh --backend=CGAL
--export-format binstl -o site/{name}.stl {file}` (binary STL output). The
`--backend=CGAL` flag is pinned because openscad-unstable's default Manifold
backend emits zero-area (degenerate) facets for the drawer baseplate grids
(112 per model), which fails ADMesh validation; CGAL is the backend the
2021.01 renders used and produces clean meshes. The flag only applies to this
STL export — the PNG thumbnail and orthographic-view steps (9, 9.5) don't
pass `--render`/full-render flags, so they use the OpenCSG preview path and
are unaffected. The wrapper runs OpenSCAD under
a memory ceiling and wall-clock timeout (`RENDER_MEM_MAX` / `RENDER_TIMEOUT`,
workflow-level env, default `28G` / `3600`s — sized for the heaviest models,
the full-res 512 px `nz-ski-fields` part renders, which take tens of minutes
each on a cold cache) so a
pathological render — heavy CSG, a cold cache, an under-provisioned runner —
fails the step cleanly instead of freezing the self-hosted runner (see issue
#272). See the Runner bullet above for the runner pods and their
dind memory limits. Output is
captured to a log file (`> "$RUNNER_TEMP/scad.log" 2>&1`) so OpenSCAD's exit
code is preserved (earlier versions piped through `tee`, which masked the
exit code). The log is replayed via `cat` for CI visibility. The log lives
in the per-job `$RUNNER_TEMP` rather than a fixed `/tmp` path: on the
GitHub-era runners, which were long-lived and shared across the org's repos,
a fixed `/tmp/scad.log` was both a symlink-clobber primitive and a way for
another principal to forge the contents the library-detection heuristic
below trusts, silently dropping a model from the deploy (issue #424).
Forgejo's fresh job containers remove that sharing, but `$RUNNER_TEMP` is
kept as defence in depth.

Before any render attempt, the filename is validated against an allow-list
regex (`^[A-Za-z0-9._ -]+$`). Files whose basename contains characters
outside this set cause the step to exit with an error immediately. This is a
defense-in-depth security check that prevents adversarially-named files from
injecting unexpected content into generated paths, HTML, or JSON.

Because every renderable's output lands in the same flat `site/` namespace,
renderable basenames must additionally be unique across all projects, and
within a project no two renderables may `slugify()` to the same value.
Both checks are enforced statically in step 2.6 (`test_output_names`) rather
than in this loop, because both are functions of the file list and a runtime
guard here would only fire after the first STL is already on disk (issue
#449).

Failure classification checks the wrapper's exit code for a cap hit
**before** the existing library-detection strategy runs: if the exit code is
`124` (timeout fired) or `>=128` (SIGKILLed — systemd `MemoryMax` or the OOM
killer), the step emits `::error::render exceeded memory/time cap` and
hard-fails immediately, unless the source is marked heavy (see "Heavy
renders" below), in which case it is deferred. This ordering matters because a SIGKILLed render
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
content-addressed cache at `$HOME/.cache/3d-models/render` (override
with `RENDER_CACHE_DIR`, disable with `RENDER_CACHE_DISABLED=1`). The key (computed by
`scripts/render_cache.py`) is a SHA-256 over the renderable's full transitive
`include`/`use` chain, any binary assets it references via
`surface(file=...)`/`import(...)`, the OpenSCAD version string, and a
`CACHE_VERSION` constant (bumped to `"2"` alongside the `--backend=CGAL` pin
above, so pre-existing cache entries rendered with the old Manifold-backend
flags are treated as misses and re-rendered rather than served as CGAL-clean
STLs). On a hit the stored STL is copied into `site/` and its
mtime refreshed; on a miss the freshly rendered STL is written into the cache
atomically (`.tmp.$$` then `mv`). The key is content-addressed, so a hit is
whatever STL the first build of that key stored, regardless of which branch
populated it (see the trust note under the S3 render cache below). Entries
untouched for 30 days are pruned by
mtime (`touch`-on-hit + `-mtime`, not `-atime`, since runners may mount
`noatime`). Parameter manifests (`*.parameters.json`) are intentionally excluded
from the key: the precomputed STL uses the defaults baked into the `.scad` (no
`-D` overrides), so manifests never affect the precomputed geometry.

**S3 render cache.** Forgejo job containers start with an empty `$HOME`, so
the local cache would be cold on every run, and a fully cold render takes
longer than an hour (one cold PR render step alone took 1743s). The cache is
therefore backed by two S3 prefixes under `s3://www.bstjohn.net/3d-models/`:
`render-cache/`, written only by `push` builds of `main`, and
`render-cache-pr/`, written by PR and issue-preview builds
(`RENDER_CACHE_WRITE_PREFIX`).

- "Configure AWS credentials" (`id: aws_creds`) runs right after "Set up
  Nix" with `continue-on-error: true` and the default one-hour session. The
  cache is only an optimisation, so if assume-role fails (missing trust
  subject, missing OIDC env) the render loop gets `RENDER_CACHE_S3=0`,
  warns once, and renders from the empty local cache; rendering and
  validation still run and "Refresh AWS credentials" turns the run red
  before the deploys. A session that lapses during a long cold render only
  makes later fetches miss and uploads warn; the next run picks up what was
  stored.
- There is no bulk restore. On a local miss the render loop `aws s3 cp`s
  `<prefix>/<key>.stl` into `$CACHE_DIR` (atomically, via `.tmp.$$`), so
  each job downloads only the keys for the current tree; a failed fetch
  just renders. Main reads only `render-cache/`; other runs try
  `render-cache/` and then `render-cache-pr/`. Skipped when
  `RENDER_CACHE_DISABLED=1` or `RENDER_CACHE_S3=0`.
- On every render, right after the atomic `mv` into the local cache, the
  render loop `aws s3 cp`s the entry to
  `$RENDER_CACHE_WRITE_PREFIX/<key>.stl` (`::warning::` on failure).
  Uploading per miss, not at the end, means a run that times out mid-way
  through a cold render still leaves progress for the next run.
- The local 30-day prune still runs but only trims the job container's copy.
  The S3 prefix is bounded by a lifecycle expiry rule set at cutover.
  Expiry is by object age (a cache hit never rewrites the object), so the
  entries seeded right after cutover expire together; the long window makes
  that rare, and a re-render only costs time. Entries are content-addressed STLs of models
  that are already public, so the prefixes hold nothing private.
- The main deploy excludes `render-cache/*` and `render-cache-pr/*` from
  its `--delete` (step 18).
- "Refresh AWS credentials" always re-assumes the role after the render
  steps, before the deploys: it replaces a lapsed session and is the hard
  gate that fails the run when the role cannot be assumed.
- **Trust.** Main deploys a cache hit without re-rendering it, so only
  merged code may write the prefix main reads: a PR that changed the render
  flags or `scripts/render_cache.py` could otherwise store wrong STLs under
  keys main later trusts, and they would ship and stay cached until expiry
  even after the PR's own preview was overwritten. PR and issue-preview
  runs therefore write `render-cache-pr/`, which main never reads, while
  still reading main's entries so a PR that touches one model does not
  re-render the rest. A PR build can still be served another PR's entry,
  which only affects previews. Bumping `CACHE_VERSION` is the only way to
  flush the whole cache on demand.
Resolved `include`/`use`/`surface`/`import` targets must pass
`render_cache.is_contained()` — a regular file whose `os.path.realpath` stays
inside the repository root and has no `.git` path component — or they are
recorded as an unresolved raw string instead of being hashed or bundled
(issue #506).

**Heavy renders.** A project marks a renderable as heavy in its
`meta.json` with `render_memory_gb`, an object mapping the renderable's
basename (no `.scad`) to the peak memory in GB its full STL render needs,
for example `nz-ski-fields`' `{"terrain": 12, "snow": 12, "lake": 12,
"assembly": 8}`. Step 2 fails a key that names no existing non-underscore
`<dir>/<key>.scad`. Unmarked renderables behave exactly as before. Each
runner advertises its job memory cap as `RUNNER_JOB_MEMORY_GB`, set in
fleet-infra's `runner.envs` to match its per-job container memory limit (6
on `k3s`, 12 on ryzen and nas; until a runner exports it, its cap counts as unknown). Before the loop the step writes
`python3 scripts/render_memory.py map` (`<dir>/<name>.scad<TAB><GB>`,
rounded up to whole GB) to `$RUNNER_TEMP/render-memory.tsv` and prints it
along with the parsed cap (`render_memory.py limit`). On a cache miss:

- marked, cap known, need > cap: not attempted. The step prints
  `::warning::Deferring heavy render …` and appends
  `src<TAB>GB<TAB>key` to `.heavy-deferred`.
- marked, cap unknown (env unset or non-numeric), or need ≤ cap: rendered
  as usual. If it then hits the cap (exit `124` or `>=128`) it is deferred
  the same way instead of failing the step.
- unmarked: rendered as usual; a cap hit still hard-fails.

After the loop the step writes `heavy_deferred=true|false` to
`$GITHUB_OUTPUT`. When it is `true`, "Request heavy renders on a ram-12g
runner" (`continue-on-error`) POSTs to the Forgejo API
`/repos/{repo}/actions/workflows/render-heavy.yml/dispatches` with the run
token, for the PR head branch or the pushed branch (the JSON body is built
with `json.dumps`). The step prints and adds to the job summary the deferred
sources, that `render-heavy` was dispatched and runs once a ram-12g runner
(ryzen or nas) is online, and that re-running this workflow afterwards
completes the build. If the dispatch fails it warns and says to dispatch it
by hand (Actions → Render heavy models → Run workflow on the branch). A
deferral skips the main deploy and the README gallery commit, so main is
never half-published, but PR and issue previews still deploy (missing the
deferred models, like any red candidate build), and step 28 fails the run.
Forgejo has no API to re-run a run, so the re-run is manual. Once
`render-heavy` has stored the STLs, any runner serves them from the cache.

To measure a renderable's need, run it on ryzen under GNU time:
`RENDER_MEM_MAX=28G RENDER_TIMEOUT=3600 /usr/bin/env time -v bash
scripts/capped-openscad.sh --backend=CGAL --export-format binstl -o out.stl <dir>/<name>.scad`. Record `Maximum
resident set size` rounded up to whole GB, plus some headroom. The initial
`nz-ski-fields` values are conservative: the full-res parts' measured peak
was above 8G, and the 128 px assembly preview has not been measured.

### 6. Validate STL Meshes

After rendering, each STL is validated by
`scripts/validate_stl_meshes.py` using
[ADMesh](https://github.com/admesh/admesh):

- **Watertight (manifold)**: No unconnected facets
- **No degenerate triangles**: Zero degenerate facets
- **Positive volume**: Ensures the mesh encloses real space

**No minimum wall-thickness check.** A wall-thickness validation from STL
cross-sections was accepted and tried (#117) alongside mesh validation, but
the owner found it noisy and low-signal in practice: "these warnings aren't
useful. Lots of 0mm or 0.01mm but all the pieces have been printed and are
working well" (#169). It is not part of the current pipeline — do not
re-add a generic wall-thickness gate on the strength of "thin walls are
theoretically risky" alone; a real print failure is the bar for adding a new
mesh-level check here, not a static geometric threshold.

The script also extracts **bounding-box dimensions** (Min/Max X/Y/Z) from
ADMesh output, records whether the model appears to sit on the print bed
(`sits_on_bed`, true when `abs(min_z) <= 0.01`), and computes a **rough
print-time estimate** (`estimated_minutes`) using a heuristic based on layer
count (height / 0.2mm) and perimeter travel time (at 50mm/s). For near-flat
models (`bb_z < 0.5`), a simpler volume-based fallback (`volume / 200`) is
used. Results are written to `site/validation.json` with the existing fields
(`name`, `triangles`, `volume`, `degenerate`, `unconnected`, `passed`,
`estimated_minutes`) plus `bbox_mm`, `bounds_mm`, and `sits_on_bed`.
`sits_on_bed` is informational only and appears as a hint in the PR comment;
it is not an enforcement gate.

If any model fails validation, the step records `failed=true` but exits zero.
The main-branch deploy is skipped and the job exits with failure only after
the PR comment is posted, ensuring reviewers see the full numeric report.

### 6.1. Export DXF Cut Profiles

A renderable that also needs a 2D cut sheet (a part made by a cut-to-size
service rather than printed) opts in with a top-level `export_dxf = false;`
line and draws its 2D profile when that is true:

```openscad
export_dxf = false;   // build: -D export_dxf=true writes the cut-sheet DXF
if (export_dxf) plate_profile(); else busy_board_plate();
```

The step (`id: dxf`) finds every non-underscore `.scad` file with a line
matching `^export_dxf *= *false;` and runs
`bash scripts/capped-openscad.sh -D export_dxf=true -o "site/$name.dxf" "$file"`.
A non-zero exit, an empty file or a missing final `EOF` record appends the
source to `.dxf-failures` and sets `failed=true`; a good export writes
`name.dxf<TAB>project-dir` to `site/.dxf-map`, which step 8 reads to add the
DXF to the project zip. The DXF deploys beside the STLs, so
`busy_board_plate.dxf` is served at
`https://www.bstjohn.net/3d-models/busy_board_plate.dxf`; the viewer does not
list it. Enforcement is deferred to step 27, and a failure also skips the
main S3 deploy.

### 6.2. Vendor Three.js Runtime

Runs `scripts/fetch_threejs.py`, which downloads the three Three.js assets
declared in `scripts/threejs_assets.py` (`three.module.min.js`, `STLLoader.js`,
`OrbitControls.js`), verifies each against its pinned SHA-256, and writes them
to `site/vendor/three/<version>/` alongside a `VERSION` file. The import maps
in `index.html` and `embed.html` resolve `three` and `three/addons/` to this
same-origin tree, so no visitor ever executes unverified third-party script on
`www.bstjohn.net` (issue #403). A hash mismatch or an unreachable CDN with a
cold `$HOME/.cache/3d-models/threejs/` fails the step immediately — this is
deliberately *not* part of the deferred-enforcement pattern.

The version directory in the path means `aws s3 sync --delete` prunes the old
tree on the next main deploy, and a returning visitor's cached
`three.module.min.js` can never be paired with addons from a different release.

### 6.3. Bundle openscad-wasm and Sources for In-Browser Customizer

Stages all assets the in-browser WASM customizer needs to function:

1. **`scripts/fetch_openscad_wasm.py`** — downloads the pinned non-threaded
   openscad-wasm release (v2022.03.20) from GitHub if not already in
   `$HOME/.cache/3d-models/openscad-wasm/<version>/`, verifies SHA-256 hashes of each asset, and copies
   `openscad.js`, `openscad.wasm.js`, and `openscad.wasm` into `site/openscad/`.
   Font and MCAD library files are intentionally omitted — no model in this repo
   uses `text()` or MCAD.
2. **Source files, binary render assets and per-project `manifest.json`** —
   `python3 scripts/external_assets.py --stage site/sources` walks every
   top-level project directory with `.scad` files. For each, it collects the
   transitive `include`/`use` chain of every `.scad` (stageable inputs only:
   existing `.scad`/`.png` in the repo) plus any `.png` whose basename
   literally appears in a `.scad` in the same directory (a `surface()`
   heightmap named through a variable, e.g. `nz-ski-fields/heightmap.png`;
   unrelated screenshots are not staged). Each file is copied to
   `site/sources/<its repo-relative path>`, and the project's sorted list is
   written to `site/sources/<project>/manifest.json` as project-relative
   paths. A cross-project include appears there as
   `../drawer-organiser/_drawer_organiser.scad`, staged under its own
   project's directory. S3 does not serve directory indexes, so the manifest
   lets the browser discover library files and binary assets. The browser
   fetches each entry per path segment (so `..` survives and the URL
   normalises it) and the worker writes it at the same relative path under
   `/customizer/<project>/`, creating directories and refusing paths that
   leave `/customizer/`. Assets are written as `Uint8Array` (fetched as
   `arrayBuffer`, not `text`).
3. **Parameter manifests** — validated manifests (not in `.param-failures`) are
   also copied to `site/sources/<project>/` so the browser can discover which
   parameters a model exposes.

### 6.4. Smoke-Test WASM Customizer Rendering

Runs four Node tests using the `nodejs_22` package from the flake's
`default` devShell — there is no separate Node setup step:

- `scripts/test_wasm_customizer.mjs` — exercises the full in-browser customizer
  pipeline end-to-end in a Node environment: it loads the staged WASM assets,
  fetches a project's source files, applies parameter overrides, and verifies
  that the resulting STL bytes are non-empty and pass a basic header check. A
  cross-project case slices `resolveSourcePath()`/`writeNested()` out of
  `openscad-worker.js`, writes `../proj-a/_lib.scad` and a model including it
  through them, renders it, and checks a path escaping `/customizer/` is
  refused.
- `scripts/test_hash_routing.mjs` — slices `parseHash`/`formatHash` out of
  `index.html` between the `__HASH_ROUTING_*` markers and asserts the URL
  grammar, including that legacy `#project/model` links round-trip unchanged.
- `scripts/test_landing_order.mjs` — slices
  `interestScore`/`recencyScore`/`landingOrder` out of `index.html` between the
  `__LANDING_ORDER_*` markers and pins the landing gallery's project ranking.
- `scripts/test_hash_history.mjs` — slices `hashWriteMode()` out of
  `index.html` and pins whether a hash change is pushed, replaced, or skipped
  in browser history (issue #383's fix for dead Forward navigation).

This replaces the old `actions/setup-node` + relocate-to-`$RUNNER_TEMP` dance
(issue #356): `actions/setup-node`'s prebuilt tarball and the ryzen runner's
relocated tool cache (`/var/lib/github-runner/ryzen-tool`, writable but not
executable by the runner's systemd `DynamicUser` unit, which previously
produced `Permission denied` / exit 126) were both unusable on the NixOS
runners. Node now comes from the same Nix-store closure as every other CI
tool, so there is nothing to relocate or verify separately.

### 6.5. Check Mating Part Interference

After mesh validation, pairs of STL files declared in `meta.json`'s
`mating_pairs` field are checked for geometric overlap using
`scripts/check_interference.py`. This step:

- Uses `trimesh` + `manifold3d` from the flake's `default` devShell — no pip,
  no PyPI fetch on the credentialed runner (issue #423)
- For each mating pair, loads both STL files and performs a boolean
  intersection using `manifold3d` to detect overlap volume
- Records results to `site/interference.json` with per-pair data:
  `part_a`, `part_b`, `overlap_volume_mm3`, `passed`, and `skipped` flags
- Uses the **deferred enforcement** pattern — records `failed=true` to
  `$GITHUB_OUTPUT` but does not fail the build until the final enforcement
  step (step 24)
- PR comments include an interference table showing part names, overlap
  volume, and pass/fail/skip status

This catches design errors where two parts that are supposed to fit together
actually physically overlap — impossible to assemble in the real world.

### 7. Generate Standalone HTML Viewers

Runs `scripts/generate-standalone.py`, which produces one self-contained
HTML file per model at `site/standalone/<name>.html`. The script:

- Downloads the Three.js 0.170.0 assets declared in `scripts/threejs_assets.py`
  (once for all models) — the same URLs and pinned hashes the "Vendor Three.js
  runtime" step uses
- Verifies SHA-256 hashes of downloaded assets; verified copies are cached in
  `$HOME/.cache/3d-models/threejs/` and reused before the network on a digest
  match, so a build downloads each file at most once *across* runs, with a
  cache fallback if the CDN is unreachable
- Cross-checks the vendored Three.js version parsed from both `index.html` and
  `embed.html` import maps via `_check_threejs_version()` — exits with error if
  either file uses a different version than `THREEJS_VERSION`, or references no
  `./vendor/three/<version>/` path at all (prevents silent version drift and
  reversion to a CDN URL)
- Base64-encodes both JS libraries and STL data into the HTML via import map
  data URIs, producing files that work from `file://` with zero dependencies

### 8. Bundle Project Zips

Groups rendered STL files by project directory (from `.scad-map`) and creates
a zip bundle for each project with **2 or more** STL files. Single-file
projects are skipped (no benefit from bundling). Zip files are named after
the project directory (e.g., `toothbrush.zip`, `power-workshop.zip`) and
use `zip -j` (junk paths) so the archive contains flat filenames without
the `site/` prefix. Cut-sheet DXFs listed in `site/.dxf-map` (step 6.1)
are added to their project's zip. The zip files are deployed alongside the
STLs and referenced from `models.json`.

### 8.5. Bundle Project Source Zips

A sibling step runs immediately after step 8 and creates a source zip for
**every** project (no 2+ file threshold). For each unique project directory in
`.scad-map`, the step runs `git ls-files` to enumerate all tracked files in
that directory and archives them with their `<dir>/` path prefix preserved
(so the archive extracts into its own folder). Zip files are named
`site/<dir>-source.zip` (e.g., `toothbrush-source.zip`) to avoid colliding
with the STL bundle. Files with spaces in their names (e.g.,
`toothbrush/Toothbrush holder.scad`) are handled safely via `git ls-files -z |
xargs -0`. Only git-tracked files are included — gitignored outputs (STLs,
`.mcp-claws.json`) never enter the archive.

`git ls-files -- "$dir"` cannot see an asset a `.scad` references from outside
its own project directory, which would make the archive unrenderable. The step
therefore also appends whatever `python3 scripts/external_assets.py "$dir"`
prints — every out-of-project file in the project's include chains: committed
scan reference meshes under `scans/` that a model `import()`s (issue #439), and
another project's shared library plus everything it includes (e.g.
`long-drawer-organiser-source.zip` carries
`drawer-organiser/_drawer_organiser.scad`), so the extracted tree re-renders. Source zips are deployed alongside
STLs via the existing `aws s3 sync` step and referenced from `models.json` as
the optional `sourceZip` field. `external_assets.py` re-applies
`render_cache.is_contained()` to every asset path before printing it, since
these paths are handed straight to `zip` for an archive deployed publicly on
every build (issue #506).

### 9. Render PNG Thumbnails

For each rendered STL (read from `site/.scad-map`), renders an 800x600 PNG
thumbnail via `scripts/capped-openscad.sh`, with a step-level
`RENDER_MEM_MAX=4G` / `RENDER_TIMEOUT=120` override (lower than the STL
render cap, since thumbnails are supplementary). No Xvfb is involved: the
flake's `openscadHeadless` wrapper renders offscreen via EGL/llvmpipe with
no X server at all, so the old `xvfb-run --auto-servernum` retry-on-stale-
lock loop (up to 3 attempts) is gone.

Every output is validated against the 8-byte PNG signature
(`89 50 4e 47 0d 0a 1a 0a`, read with `od`) rather than merely checked for
non-emptiness. OpenSCAD exits 0 after `Cannot create OpenGL OffscreenView`
but leaves a 0-byte file behind, and a 0-byte PNG syncs to S3 as happily as
a real one; that is exactly what shipped a text-only landing gallery for
five consecutive main builds (issue #359). An invalid output is deleted and
its model name is appended to `.thumb-failures` at the repo root.

Individual thumbnail failures — including a cap hit — emit a GitHub Actions
warning and do not fail the step. Instead the step records `failed=true` to
`$GITHUB_OUTPUT` (`id: thumbnails`) and the separate **Enforce thumbnail
rendering** step at the end of the pipeline fails the build, listing
`.thumb-failures`. The main-branch S3 deploy is also gated on `steps.thumbnails.outputs.failed` (issue #406): because an invalid PNG is deleted and the sync runs with `--delete`, deploying after a thumbnail failure would strip the last good thumbnails off the live site. The enforcement step still runs at the end of the pipeline, so the PR comment, `validation.json` and `interference.json` are all produced before the build exits non-zero.

### 9.5. Render Extra Orthographic Views for Complex-Interior Models

For any model whose project has `complex_interior: true` in `meta.json`,
three additional orthographic PNGs are rendered: `top`, `bottom`, and
`front`. Each is 800×600, saved as `site/<model-name>_<view>.png` (e.g.,
`site/drill_socket_top.png`), using `--projection=ortho --viewall
--autocenter` for consistent framing, also via `scripts/capped-openscad.sh`
with the same 4G/120s step-level cap as thumbnails. `power-workshop` and
`drawer-organiser` declare `complex_interior: true`.

No Xvfb here either — same as step 9, the flake's `openscadHeadless` wrapper
renders offscreen directly with no virtual display involved. Empty or
missing output PNGs are removed with a warning annotation rather than
failing the build.

### 10. Generate QR Codes

Generates a QR code PNG per model at `site/qr/<name>.png` using `qrencode`.
Each QR encodes the model's deep link URL
(`https://www.bstjohn.net/3d-models/#<project-slug>/<model-slug>`). The
slugs come from the canonical `slugify()` in `scripts/oembed_helpers.py` — the
step shells into `python3` to emit a `name<TAB>url` table into `$RUNNER_TEMP`,
then loops over it in Bash to call `qrencode`. There is no Bash
re-implementation of `slugify()` (issue #398);
`scripts/test_build_workflow.py::QrSlugifyTests` enforces this. QR images use
the site's dark theme colors (`--foreground=E0E0E0 --background=1A1A2E`), module size 8,
and margin 2. QR codes are stored in a separate `site/qr/` directory to keep
QR PNGs out of the deployed thumbnail namespace. Failures
emit a warning but don't break the build (same pattern as thumbnails).

### 11. Generate OG Hero Image

Composites a fixed grid of model thumbnails into a single 1200×630
`og-hero.png` for Open Graph social previews. Tiles are chosen by
`og_hero_thumbnails()` in `scripts/oembed_helpers.py`, driven from
`site/.scad-map` rather than a `site/*.png` glob: one thumbnail per project
(the project's `meta.json` `hero` when it rendered, else the first STL
alphabetically), in project-directory order, capped at
`OG_HERO_MAX_TILES` (15, a 5×3 grid) so the montage never has more tiles than
the grid has slots. Because every candidate name is derived from an STL in
`.scad-map`, the `_top`/`_bottom`/`_front` orthographic views written by the
complex-interior step (and any other stray PNG dropped into `site/`) are
excluded by construction. If no thumbnails exist (all renders failed), the
step falls back to a solid-color image with text using `magick`/`convert`
(whichever is present — ImageMagick 7 ships `magick` and may omit the legacy
`convert` symlink).

`montage` tiles the selected thumbnails in a 5×3 grid (`-geometry
232x202+4+4 -tile 5x3`) against the site's dark background (`#1a1a2e`) and
writes MIFF to stdout, which is piped into a second `magick`/`convert`
invocation that applies `-gravity center -extent 1200x630`. This two-stage
pipe is required: `-resize`/`-extent` chained directly onto the `montage`
invocation are silently ignored by ImageMagick — confirmed by downloading
the live deployed artifact, which measured 1224×14168 (exactly the raw
`-tile 3x -geometry 400x300+4+4` canvas from the old glob-based step, with no
resize or crop applied at all). Piping through an intermediate stage is the
fix; `identify -format '%wx%h\n' site/og-hero.png` should always report
`1200x630` now.

Both the `montage` stage and the solid-color fallback pass `-font
Liberation-Sans` explicitly. ImageMagick from the flake has no
distro-supplied `type.xml` and therefore no default font; `montage` needs one
even when no visible text is requested, because it labels each tile by
default. The font resolves via fontconfig: the `default` devShell pins
`FONTCONFIG_FILE` (via `pkgs.makeFontsConf` in `flake.nix`) to a font set
containing `liberation_ttf`, so this works identically on every runner
regardless of what's installed on the host. Font names in ImageMagick's own
naming are hyphenated (`Liberation-Sans`, `DejaVu-Sans`), not the fontconfig
family names (`"Liberation Sans"`, `sans`) — the latter do not resolve.

The step is warning-only, matching the thumbnail/QR pattern: if `montage`
fails to composite, it falls back to the plain solid-color hero image; if
that also fails, the step emits `::warning::`, removes any partial
`og-hero.png`, and lets the build continue rather than blocking the deploy.

The image is deployed to a stable URL (`/3d-models/og-hero.png`) — it is
intentionally not cache-busted so social media crawlers can cache it
reliably. That also means a bad composite is sticky: crawler caches may keep
serving a stale image for a while after a fix merges.

### 12. Generate Models Manifest

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
    "printing_notes": ["Enable adaptive layer height over the arch crown"],
    "rendered_with": "OpenSCAD 2024.12.06",
    "updated": "2026-07-30T09:14:22+12:00"
  }
}
```

Project names are derived from directory names (hyphens/underscores → spaces,
title-cased) by `project_display_name()` in `scripts/oembed_helpers.py`. The
`zip` field is only present when a zip bundle was generated
(projects with 2+ files). The `sourceZip` field is present for every project
that has tracked source files; it references the per-project source zip
produced by step 8.5. The `estimated_minutes` field is merged from
`validation.json`. The `qr` field is present only when the QR PNG exists.
The `parameters` field is present on a file entry when a validated
`<basename>.parameters.json` manifest exists next to the `.scad` source; its
presence tells the viewer to show the ⚙ Customize button for that model.
Manifests in `.param-failures` are excluded — the customizer never loads an
invalid parameter set. Metadata fields (`description`, `tags`, `difficulty`,
`version`, `hardware`, `assembly`, `printing_notes`) are
merged from `meta.json` if the file exists and passed schema validation.
The `updated` field is the ISO-8601 committer date of the last commit touching
the project directory, from `scripts/project_dates.py`. It is CI-derived — not
a `meta.json` field — and drives the landing gallery's recency ordering. It is
omitted for any directory `git log` reports nothing for, which is what a
shallow clone produces for every project (see "Checkout depth" above).
The `rendered_with` field records the OpenSCAD version used to produce the
STLs (e.g. `"OpenSCAD 2024.12.06"`), sourced from `site/openscad-version.txt`
written by the version-check step. This field is diagnostic documentation:
if a user reports that a printed part doesn't fit, knowing which OpenSCAD
version produced the STL helps isolate whether it's a source issue or a
renderer regression.
The viewer reads this manifest to populate the gallery and conditionally show
features.

### 12.5. Generate sitemap.xml

After the models manifest is written, a Python snippet reads `site/.scad-map`
and `site/models.json` and calls `oembed_helpers.build_sitemap()` to generate
`site/sitemap.xml` — a standard `<urlset>` listing the gallery root and one
`<url>` per standalone viewer (`/standalone/<model>.html`). URLs are built
from `BASE_URL` in `oembed_helpers.py` and the standalone filenames are
URL-encoded with `urllib.parse.quote`.

Each `<url>` also carries a `<lastmod>`, taken via `stl_lastmods()` from the
owning project's `updated` field in `site/models.json` (the last-commit date
computed by `scripts/project_dates.py`). The gallery root URL gets the newest
such date across all standalone viewers. On a shallow clone —
`project_updated()` returns `{}` in that case — no project has an `updated`
field, so `<lastmod>` is simply omitted everywhere rather than failing the
build.

The sitemap is deployed to `/3d-models/sitemap.xml`; as with `robots.txt`,
crawlers only read the authoritative copy at the origin root
(`/sitemap.xml`), which requires a separate infra step.

### 13. Generate README Gallery (main branch only)

Runs `scripts/generate-gallery.py`, which reads `site/models.json` and
per-project `meta.json` descriptions to generate a visual gallery table in
`README.md` between `<!-- gallery:start -->` and `<!-- gallery:end -->`
markers. Each row has a thumbnail, project link, model count, and description.
On PRs, the script is smoke-tested (run then reverted with `git checkout`)
to catch breakage without modifying the PR.

### 14. Generate Structured Data

A Python script reads `site/.scad-map` and `site/validation.json` to produce
`site/structured-data.json` — a Schema.org JSON-LD `@graph` with three
hash-addressed nodes: an `Organization` (`https://www.bstjohn.net/#organization`,
with a `sameAs` list of the project's GitHub profiles), a `WebSite`
(`https://www.bstjohn.net/#website`, whose `publisher` references the
`Organization` by `@id`), and a `CollectionPage`
(`{BASE_URL}/#collection`, whose `isPartOf` references the `WebSite` and whose
`creator` references the `Organization`, both by `@id`) holding an `ItemList`
of `3DModel` entries. Each `3DModel` gets its own `@id`
(`<standalone viewer URL>#model`) plus `contentUrl`, `encodingFormat`
(model/stl), `thumbnailUrl`, `contentSize`, `isPartOf` (project grouping), and
a `creator` that references the `Organization` node by `@id` rather than
inlining it. Project descriptions from `meta.json` are used when available
(skipping files in `.meta-failures`). Absolute URLs are required by JSON-LD
spec. The whole payload is built by `build_structured_data()` in
`scripts/oembed_helpers.py`.

### 15. Generate OEmbed JSON Files

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

### 16. Generate Changed Projects List (PR and issue previews)

A "Resolve diff base" step (`id: diff_base`) runs first. Forgejo checks a
`pull_request` run out at the PR head (`refs/pull/N/head`), not a merge
commit, so `HEAD~1` would only be the PR's last commit; for PRs the base is
`git merge-base "origin/<base ref>" HEAD` (the checkout's `fetch-depth: 0`
provides `origin/<base>`), and for issue previews it stays `HEAD~1`. Both
this step and the PR comment (step 20) diff against
`steps.diff_base.outputs.base`; "Write issue preview summary" keeps
`--changed-from-git`'s `HEAD~1` default.

Diffs the PR (or issue-preview) commit against that base to find changed `.scad` files, extracts their top-level
directories, and writes `site/changed.json` — an array of project names.
The viewer uses this to auto-expand sections for changed models and collapse
unchanged ones. Project names come from the same `project_display_name()`
helper that keys `models.json`, and the PR-comment step reads its group
headers back out of `models.json` (via `scripts/preview_summary.py`), so the
three never disagree.

### 17. Copy Static Assets and Inject Data

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

### 18. Deploy to S3

Uses OIDC (`aws-actions/configure-aws-credentials`, SHA-pinned to v6.3.0) with
the `AWS_ROLE_ARN` Forgejo Actions secret; the token issuer is
`https://www.bstjohn.net/forgejo-oidc` (see
[Forgejo cutover](#forgejo-cutover)). v6 requires an explicit
`role-session-name` input for STS assume-role to succeed (a v4→v6 upgrade
broke this silently, #291); both workflows pass
`forgejo-actions-${{ github.run_id }}`. The credentials used here come from
the "Refresh AWS credentials" step (step 5's S3 render cache explains the
earlier, best-effort "Configure AWS credentials").

- **Main branch**: `aws s3 sync ./site s3://www.bstjohn.net/3d-models/ --delete`
  (excludes `pr-preview/`, `issue-preview/`, `render-cache/` and `render-cache-pr/`). Gated on mesh validation, metadata validation, the interference check, parameters-manifest validation, thumbnail rendering and DXF export all passing, and on no heavy render having been deferred (step 5) — broken meshes, invalid metadata, overlapping parts, bad manifests, missing thumbnails, missing cut sheets and a site missing its heavy models never reach production. Not gated on the dependency-graph check: `dependency-graph.md` is a repo doc, not a deployed artifact.
- **Pull requests**: `aws s3 sync ./site s3://…/pr-preview/pr-{N}/{SHA}/`.
  PR deploys are not gated on validation so reviewers can inspect broken
  models in the 3D viewer.
- **Issue previews**: `aws s3 sync ./site s3://…/issue-preview/{id}/{SHA}/`
  on `claws/preview-issue-{id}` pushes, also ungated; see
  [Issue previews](#issue-previews-pr-less).
- **PR close**: `.forgejo/workflows/pr-preview-cleanup.yml` runs on
  `pull_request: [closed]` and executes
  `aws s3 rm s3://…/pr-preview/pr-{N}/ --recursive`, reclaiming every SHA
  prefix that PR deployed. Kept out of `build.yml` on purpose: the build job
  is the full render pipeline and its preview-deploy step is gated only on
  `github.event_name == 'pull_request'`, so a `closed` event there would
  re-render everything and re-upload the preview. The cleanup job shares
  `build.yml`'s `pages-pr-{N}` concurrency group so a close can cancel an
  in-flight build for that PR before the delete; cross-workflow
  cancellation is unverified on Forgejo, though, so a render finishing after
  the close can re-create `pr-preview/pr-{N}/<sha>/`, which only a
  `pr_numbers` dispatch reclaims. Superseded SHA prefixes for
  *open* PRs are not pruned — they are reclaimed when the PR closes. A
  `workflow_dispatch` input (`pr_numbers`, space-separated) exists for
  reclaiming previews orphaned before this workflow landed.
- **Issue-preview branch delete**: the same workflow's `delete` trigger
  (gated to `claws/preview-issue-*` branches) or an `issue_id` dispatch
  validates the id and runs
  `aws s3 rm s3://…/issue-preview/{id}/ --recursive`, sharing build.yml's
  `pages-refs/heads/claws/preview-issue-{id}` concurrency group. Guarded by
  `scripts/test_pr_preview_cleanup.py`. Forgejo does fire `delete` (it is
  in its no-filter event list; the payload carries `ref` and `ref_type`),
  but whether `ref` arrives short (`claws/preview-issue-<id>`) or as
  `refs/heads/claws/preview-issue-<id>` is unverified, so the job `if:` and
  concurrency group use `contains(github.event.ref, 'claws/preview-issue-')`
  and the shell strips an optional `refs/heads/` before
  `claws/preview-issue-`, then applies the same id guard. Expressions
  cannot strip a prefix, so build.yml's group uses the full ref and the
  cleanup group prepends `refs/heads/` to a short `ref`; either form joins
  build.yml's group. Cross-workflow cancellation is still unverified on
  Forgejo, so a render finishing after a branch delete can re-upload a
  prefix that the next `issue_id` dispatch reclaims. On `delete` the job
  checks out `github.event.repository.default_branch`.
- **Spec pages on PR close**: the same workflow's "Delete spec pages
  prefix" step (on `pull_request: [closed]` or a `pr_numbers` dispatch)
  applies the same numeric guard and runs
  `aws s3 rm s3://pages/3d-models/pr/pr-{N}/ --recursive` against the
  private Garage pages host; see [pages.yml (spec pages)](#pagesyml-spec-pages).

**Action pinning**: every external action in both workflows
(`actions/checkout`, `aws-actions/configure-aws-credentials`) is a full
`https://github.com/...` URL pinned to a full commit SHA with a trailing
`# vX.Y.Z` comment, not a mutable tag — this step runs with `id-token: write`
and mints the OIDC session for the AWS deploy role, so a force-moved tag
there is a supply-chain path to the deploy role (#499). fleet-infra's
Forgejo Renovate (`apps/renovate/configmap.yaml` lists this repo) updates
both the SHA and the comment on new releases.
`scripts/test_build_workflow.py::ActionPinTests` enforces the pin and the
full-URL form.

### 19. Commit README Gallery Update (main branch only)

After a successful deploy, if the gallery script produced changes to
`README.md`, the step commits and pushes the update using the
`forgejo-actions` / `forgejo-actions@noreply.git.home.bstjohn.net`
identity. The commit message includes `[skip ci]`, which Forgejo honours,
to prevent an infinite CI loop. Uses `git pull --rebase` before pushing
to handle concurrent pushes. Gated on the gallery step succeeding, mesh
validation passing and no heavy render having been deferred (step 5). Uses
`continue-on-error: true` so a push race condition doesn't fail the entire
workflow.

### 20. Comment on PR (PR only)

Runs `python3 scripts/pr_preview_comment.py` (stdlib only), which posts or
updates a comment on the PR through the Forgejo issues API with the run
token. The body is `scripts/preview_summary.py`'s markdown — the same
renderer issue previews use — pointed at
`https://www.bstjohn.net/3d-models/pr-preview/pr-<N>/<sha8>/`, with:
- A link to the interactive preview deployment
- PNG thumbnails of models changed in the PR (`git diff --name-only
  $DIFF_BASE HEAD`, see step 16), grouped by project. Group
  headers come from a `dir → project name` map built by reading
  `site/models.json` (each entry's `dir` field), not from a
  re-implementation of the directory→display-name transform — a prior JS
  copy diverged from Python's `str.title()` on inputs like `2x4-jig` (issue
  #399). If `models.json` is missing or unparseable, group headers fall back
  to the raw directory name.
- A mesh validation table with triangle count, volume, bounding-box
  dimensions, and a min-Z bed-contact hint. This is intentionally numeric
  feedback: rendered screenshots are useful for orientation and massing, but
  they are not sufficient evidence that functional geometry is intact.
- **File size and triangle count** for each changed model, displayed next to
  the model name (e.g., "45.2 KB · 3,456 triangles"). Triangle count is
  parsed from the binary STL header (bytes 80–83, little-endian uint32) and
  validated against the expected file size (`84 + triangles × 50`). If
  validation fails (e.g., ASCII STL), only the file size is shown.
- A collapsible `<details>` block, placed after the viewer link, listing
  previous preview deployments for the PR newest first: every
  `pr-preview/pr-<N>/<sha8>/` SHA in the existing comment, deduplicated,
  excluding the current one and capped at 10 (with an "N older omitted"
  suffix).

The script skips (exit 0, with a message) when there are no changed-model
thumbnails and no `site/validation.json` rows. Otherwise it pages through
`GET {API_URL}/repos/{REPO}/issues/{N}/comments?page=P&limit=50` until a
short page, takes the first comment written by `forgejo-actions` (the user
the run token acts as; override with `COMMENT_AUTHOR`) whose body starts
with `## 🔍 Model Preview`, and `PATCH`es
`/repos/{REPO}/issues/comments/{id}` or `POST`s a new comment, with
`Authorization: token $TOKEN`. Every request is tried 3 times with linear
backoff (2s × attempt). Its inputs come from step `env:` (`PR_NUMBER`,
`HEAD_SHA`, `DIFF_BASE`, `API_URL` = `github.api_url`, `REPO`, `TOKEN` =
`secrets.GITHUB_TOKEN`). The step uses `continue-on-error: true` so a
transient API failure doesn't fail the workflow. Guarded by
`scripts/test_pr_preview_comment.py`.

### Issue previews (PR-less)

No `.scad` is rendered until something pushes it to CI, which leaves
issue-planning review blind — the maintainer can't see a proposed model's
geometry before deciding whether the plan is right (issue #518).
`scripts/request-issue-preview.sh` closes that gap by reusing this pipeline
rather than building a second render path, and without opening a PR (issue
clw_01M39H53GDR0QVMAF3WVMWQKTM): a draft PR went stale as the plan was
refined, had to be closed by hand, cluttered PR lists, and needed the
**Claws Ignore** label to stay out of the implementation pipeline.

- **Trigger.** The script commits the candidate files (`.scad`, plus a
  project's `meta.json` and `dependency-graph.md`) on top of
  `origin/main` (without touching the caller's worktree) and force-pushes
  them to `claws/preview-issue-<id>`, where `<id>` is an issue number or a
  Claws-native `clw_…` id. `build.yml`'s `push` trigger covers
  `claws/preview-issue-*`, so the ordinary render, mesh-validation,
  interference, thumbnail and manifest steps run unmodified on whichever
  self-hosted Linux runner picks up the push. The "Resolve issue preview
  target" step strips the branch prefix,
  validates the id against `^([0-9]+|clw_[A-Za-z0-9]+)$` (the run fails
  otherwise), and exposes `issue_id`, `short_sha` and `enabled` outputs that
  gate every preview-only step.
- **Concurrency.** A preview push joins group
  `pages-refs/heads/claws/preview-issue-<id>`,
  so it never cancels a main build, and a newer push for the same issue
  cancels the older render.
- **Deploy.** "Deploy issue preview" syncs `site/` to
  `s3://www.bstjohn.net/3d-models/issue-preview/<id>/<sha8>/`, ungated on
  validation like PR previews so a red candidate is still inspectable. The
  "Generate changed projects list" step also runs, so the viewer opens the
  candidate project. The main deploy excludes `issue-preview/*` from its
  `--delete`.
- **Summary.** "Write issue preview summary" runs
  `scripts/preview_summary.py`, which writes `preview-summary.json` into the
  same prefix and appends its markdown to the run's step summary. Top-level
  keys: `issue`, `sha`, `commit`, `viewer_url`, `summary_url`,
  `changed_scad`, `models` (per changed renderable: `name`, `project`,
  `scad`, `thumbnail_url`, `stl_size_bytes`, `triangles`, `extra_views`),
  `validation` and `interference` (verbatim copies of `site/validation.json`
  and `site/interference.json`), and `markdown` — the same "🔍 Model
  Preview" body the PR comment (step 20) renders, minus "Previous builds".
  Claws' `issue-preview-sync` job, configured by `claws.json`'s
  `issuePreviewSummaryUrl` template (`{issue}` = branch suffix verbatim,
  `{sha8}` = first 8 characters of the branch head), fetches the file and
  mirrors `markdown` into the issue's `## Preview` comment; a 404 is reported
  as pending for that head. The planner may manually post the summary only
  when Claws' sync is unavailable or the issue is not tracked by Claws.
- **Cleanup.** Claws deletes the branch on Refined or close (writing the
  retirement record into the `## Preview` comment first, then deleting the
  branch), which fires `pr-preview-cleanup.yml`'s `delete` trigger to reclaim
  the whole `issue-preview/<id>/` S3 prefix — the same behavior as a manual
  `git push origin --delete`. `request-issue-preview.sh --cleanup <id>` is the
  manual fallback: it deletes the branch (it no longer closes legacy preview
  PRs — none are open, and `gh` cannot reach Forgejo). The job joins the same
  `pages-refs/heads/claws/preview-issue-<id>` concurrency group, but
  cancellation is not guaranteed on Forgejo (see step 18's issue-preview
  branch-delete notes), so a render finishing after the delete can
  re-upload the prefix. A `workflow_dispatch` with `issue_id` reclaims such
  a re-uploaded or otherwise orphaned prefix. Because
  the stale-branch cleaner deleting an abandoned preview branch fires the
  same event, forgotten previews are reclaimed too. Claws' own
  `issue-preview-sync` job also watches open PRs on `claws/preview-issue-*`
  branches as a legacy fallback; if such a PR is still open when the issue
  goes Refined or closes, Claws closes it itself on its next pass, so the
  planner should not close it by hand.

Guarded by `scripts/test_request_issue_preview.py`,
`scripts/test_preview_summary.py`, `scripts/test_pr_preview_cleanup.py`
and `scripts/test_build_workflow.py::IssuePreviewTests`. See
[playbooks/preview_a_proposed_model.md](../playbooks/preview_a_proposed_model.md)
for the planner workflow.

### 21. Enforce Mesh Validation

If the validate step recorded any failures, this step exits with an error
after all other steps (thumbnails, manifests, PR comment, deploy) have
completed. This ensures the full report is visible to reviewers before the
job fails.

### 22. Enforce Dependency Graph Check

If the dependency graph verification (step 1) recorded a failure, this step
exits with an error telling the contributor to regenerate. Placed after all
other steps so the full pipeline output (renders, PR comment, deploy) is
available even when graphs are stale.

### 23. Enforce Metadata Validation

If the metadata validation (step 2) recorded a failure, this step exits with
an error indicating which `meta.json` files don't match the schema.

### 24. Enforce Interference Check

If the mating part interference check (step 6.5) recorded a failure, this
step exits with an error indicating which part pairs have geometric overlap.

### 25. Enforce Parameters Validation

If the parameters manifest validation (step 2.5) recorded a failure, this
step exits with an error and prints `.param-failures` so the contributor
knows which manifests to fix.

### 26. Enforce Thumbnail Rendering

If the thumbnail rendering step (step 9) recorded `failed=true`, this step
exits with an error and prints `.thumb-failures` so the contributor knows
which models produced no valid PNG (issue #359).

### 27. Enforce DXF Export

If the DXF export step (step 6.1) recorded `failed=true`, this step exits
with an error and prints `.dxf-failures` so the contributor knows which
cut sheets failed.

### 28. Enforce Heavy Renders

The last step. If step 5 deferred any heavy render
(`steps.render.outputs.heavy_deferred == 'true'`), it prints
`.heavy-deferred` and exits with an `::error::` that names the deferred
sources, says they need a ram-12g runner (ryzen or nas), says whether
`render-heavy.yml` was dispatched or must be dispatched by hand, and says
that re-running this workflow once it has finished will pass on any runner.

All eight enforcement steps (mesh validation, dependency graph, metadata,
interference, parameters, thumbnail rendering, DXF export and heavy
renders) use `if:` conditions and run independently, so if several fail,
all their errors are visible.

## render-heavy.yml

`.forgejo/workflows/render-heavy.yml` ("Render heavy models") renders the
heavy models `build.yml` defers (step 5, "Heavy renders") and stores them
in the S3 render cache.

- **Trigger**: `workflow_dispatch` only, with an optional `requested_by`
  input (`build.yml` passes `run <run_number>`). `build.yml` dispatches it
  for the branch that deferred; an operator can also run it from the
  Actions tab. `concurrency: render-heavy-<ref>`, cancel in progress.
- **Runner**: `[container, linux, ram-12g]`, the one job in this repo that
  waits for a tier label. `ram-12g` is advertised only by ryzen and nas
  (12g per job; the thinkcentre stops at `ram-6g`), and it must cover
  every `render_memory_gb` mark: `render_memory.py tier` reads N from this
  `runs-on` and "Validate project metadata" fails any mark above it. While both are
  off the run just queues, and since nothing `needs` it, no other check is
  blocked.
- **Steps**: checkout (`fetch-depth: 1`), setup-nix, "Configure AWS
  credentials" (not best-effort, because writing the cache is the point),
  "Check OpenSCAD version" (into `$RUNNER_TEMP/openscad-version.txt`), then
  for each source in `render_memory.py map`: compute the
  `render_cache.py` key, probe `aws s3api head-object` under the same read
  prefixes as `build.yml`, skip hits, render misses with
  `capped-openscad.sh --backend=CGAL --export-format binstl` under the same
  `RENDER_MEM_MAX`/`RENDER_TIMEOUT` (28G/3600s), fail the job on any
  non-zero exit, and upload each result. A final step prints and adds to the
  job summary what was rendered, what was already cached, and a reminder
  to re-run the requesting build.
- **Prefixes and trust**: it writes `render-cache/` only when the
  dispatched ref is `refs/heads/main` (merged code, the same rule as
  `build.yml`'s main pushes), and `render-cache-pr/` for every other
  branch, which main never reads. Reads try `render-cache/` and then, off
  main, `render-cache-pr/`.
- **Race**: it renders the branch tip at dispatch time, which may be newer
  than the build that requested it. Keys come from what it checks out, so
  re-running the newest build is what benefits.

## pages.yml (spec pages)

`.forgejo/workflows/pages.yml` ("Spec Pages") publishes `pages/`, the
project spec pages (hand-authored static HTML with inline SVG figures; see
[OVERVIEW.md](OVERVIEW.md)), to the private fleet pages host
`pages.home.bstjohn.net` (Garage behind Authentik, LAN and tailnet only),
following fleet-infra `docs/pages.md` "Adding a repo". Nothing is compiled:
the committed HTML is the artefact.

- **Trigger**: push to `main` and `pull_request` `[opened, synchronize,
  reopened]`, both filtered by `paths` to `pages/**`, the spec-pages
  scripts and tests, `pr_preview_comment.py`, the workflow itself, the
  flake and `setup-nix`. Concurrency group `spec-pages-pr-{N}` or
  `spec-pages-main`, deliberately not `build.yml`'s `pages-*` groups, and
  not cancelled in progress so a run cannot stop between the supersession
  delete and the entry page.
- **Runner**: one job on `[container, linux]` in the `default` devShell
  (checkout, setup-nix; `python3`, `node` and `aws` come from the flake).
  No OpenSCAD, no OIDC. Fork PRs are skipped by the job `if:`
  (`head.repo.full_name == github.repository`) because they get no secrets.
- **Check**: `test_spec_pages.py` runs each figure generator
  (`node pages/<project>/src/<script>.js` in a temp dir) and fails if its
  output differs from the committed `src/*.svg`, if the page's inline SVGs
  differ from the committed ones in order, or if a page loads an external
  asset. `python3 scripts/spec_pages.py --write` re-splices committed SVGs
  into the page after a generator change; `--check` reports drift.
- **Credentials**: the Forgejo org-level Actions secrets
  `PAGES_S3_ACCESS_KEY_ID` / `PAGES_S3_SECRET_ACCESS_KEY` (fleet-infra
  migration 0044), passed only through step `env:` as
  `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` with
  `AWS_ENDPOINT_URL=https://s3.home.bstjohn.net`, `AWS_DEFAULT_REGION=garage`
  and a generated `AWS_CONFIG_FILE` setting `addressing_style = path`.
  Empty secrets on a same-repo run fail the publish step.
- **Published tree**: `aws s3 sync ./pages … --delete` excluding
  `*/src/*` and `*.md`; the generators, calculation scripts and working
  notes stay in the repo.
- **URLs**:
  - Push to `main`: `s3://pages/3d-models/docs/main/<sha8>/`; then
    every other SHA under `3d-models/docs/main/` is deleted; then, after
    that delete (it would otherwise remove it), the stable entry page
    `3d-models/docs/main/index.html` (meta refresh to `./<sha8>/`,
    `--cache-control no-cache`) is written. The latest build is always at
    `https://pages.home.bstjohn.net/3d-models/docs/main/`.
  - Pull request: after checking `<N>` is numeric,
    `s3://pages/3d-models/pr/pr-<N>/<sha8>/` with the same supersession
    delete, linked from a separate `## 📄 Spec pages` PR comment posted by
    `scripts/pages_pr_comment.py` (best-effort). It is not a line in the
    Model Preview comment because `build.yml` may not run for the same PR.
  - PR close: `pr-preview-cleanup.yml` deletes
    `s3://pages/3d-models/pr/pr-<N>/` recursively (step 18). That step runs
    before "Configure AWS credentials" so the OIDC session env never reaches
    the Garage call. A publish finishing after the close can re-create the
    prefix; fleet-infra's `pages-janitor` removes `pr` keys after 30 days.
- The `issue` kind (`3d-models/issue/<id>/<sha8>/`, session and planner
  previews) is unchanged and not written by this workflow; nothing here
  writes the host-root `s3://pages/index.html`, which fleet-infra's
  `pages-index` owns.
- Guarded by `scripts/test_pages_workflow.py`.

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
  `nz-ski-fields` part renders — measured on the 32 GB `ryzen` runner; see
  the env-block comment in `build.yml`) and are overridden to `4G`/`120s`
  at the step level for thumbnails and orthographic views. On a cap hit the
  wrapper prints `render exceeded memory/time cap` to stderr; the STL
  render step checks the exit code (`124` timeout, `>=128` SIGKILLed)
  **before** its library-detection heuristics, because those exit codes
  would otherwise be misclassified as "suspected library" and silently
  skipped — see the Render STL Files step. The build job runs on any
  `[container, linux]` runner (issues clw_01M3ARSS5M37ARAEKERQY1FJ93,
  clw_01M45RK9YR5VC9XXHMQP84VKPV); the 28G cap protects a host only if the
  runner has more memory than the cap. On the `k3s` runner (6g per job) the job
  container's memory limit is the hard backstop (render OOM-killed, exit
  `>=128`). In a job container `capped-openscad.sh` uses its `ulimit -v`
  fallback. Failure detection lives outside this repo
  (Claws' `main-build-monitor`, see below), so an outage of the runner
  pool still gets reported. These caps exist because of a real incident
  (2026-07-07,
  PR #271): `nz-ski-fields/assembly.scad` (a `union()` of three `surface()`
  part trees) rendered unbounded and hard-froze `ryzen`, which was at the
  time temporarily mis-provisioned with 8G instead of 32G, then went on to
  OOM the second, GitHub-era fallback runner host after roughly 50 minutes. A frozen
  or killed runner uploads no logs for the step it died on, so a job that
  shows **no failed step and no fetchable logs** is the signature of a dead
  runner, not a code failure — don't blindly re-run it, since a second blind
  run can take down another host the same way; check runner health first.
  Don't lower `RENDER_MEM_MAX`/`RENDER_TIMEOUT` without re-measuring the
  heaviest render (`nz-ski-fields/assembly.scad` was ~31 minutes wall clock
  and >8G peak RSS on a healthy 32G runner) against the new caps.
- **Heavy renders go to a dispatched workflow, not a tier-labelled job in
  `build.yml`** (issue clw_01M55BX5C0F7WYKCACTYPY1NV4). On Forgejo (15.0.7
  here) a job whose `needs` succeeded is set to Waiting and its `if:` is
  evaluated by the runner that picks it up, not by the server. A
  `ram-12g`-labelled job in `build.yml` would therefore queue forever while
  ryzen and nas are off, even when its `if:` is false, and block every PR
  check. `build` stays on `[container, linux]`, defers marked heavy
  misses, and dispatches `render-heavy.yml`, which can wait for `ram-12g`
  without blocking anything.
- **Library detection**: Uses a three-tier strategy: (1) underscore-prefixed
  files are skipped by convention, (2) OpenSCAD's "top level object is
  empty" / "nothing to export" log output identifies libraries at render
  time, (3) a fallback heuristic catches edge cases where OpenSCAD exits
  non-zero with no real output (≤84 bytes). These tiers only run after the
  render-cap check above rules out a timeout/OOM exit. Output is captured
  via file redirect (`> "$RUNNER_TEMP/scad.log" 2>&1`) rather than piped
  through `tee`, so OpenSCAD's exit code is preserved for the error-handling
  logic. `$RUNNER_TEMP` (not a fixed `/tmp` path) because the GitHub-era
  shared, long-lived self-hosted runners made `/tmp` writable by other
  principals (issue #424); Forgejo's fresh job containers keep it as defence
  in depth.
- **CI-generated zip bundles**: Zip files are pre-built in CI and deployed
  as static assets alongside STLs, rather than generated client-side. This
  fits the project's fully-static architecture — no new client-side
  dependencies. Only projects with 2+ files get a zip (single-file projects
  don't benefit from bundling).
- **Nix-provided dependencies, no preflight checks**: Every tool (OpenSCAD,
  ImageMagick, ADMesh, qrencode, AWS CLI, Node, Python) comes from this
  repo's `flake.nix` `default` devShell, entered via the job-level
  `defaults.run.shell` (see step 0). This replaced a set of `command
  -v`-based preflight steps ("Check build dependencies", "Check ADMesh",
  "Check AWS CLI") that failed fast with `::error::` naming any tool missing
  from the runner host's own package set — those steps no longer exist. If a
  devShell package is missing, `nix develop` still succeeds but the step
  that needs the tool fails with a plain `command not found`; the fix is to
  add the tool to `flake.nix`, not to the runner host.
- **Headless OpenSCAD rendering, no Xvfb**: The flake's `openscadHeadless`
  wrapper (`flake.nix`) forces OpenSCAD onto the EGL/llvmpipe software-GL
  path (`LIBGL_ALWAYS_SOFTWARE`, a pinned Mesa EGL vendor JSON,
  `QT_QPA_PLATFORM=offscreen`, `DISPLAY` unset), so PNG export works with no
  X server at all. This replaced the "Prepare Xvfb environment" step (stale
  `/tmp/.X*-lock` cleanup, `/tmp/.X11-unix` permission checks, glvnd
  EGL-vendor pinning via `$GITHUB_ENV`) and the `xvfb-run` retry-on-stale-lock
  loops in the thumbnail and orthographic-view render steps (issue #361;
  St-John-Software/nixos-config#110, #111). The "Verify headless OpenSCAD
  rendering" smoke test (step 3) still runs to catch a wrapper regression
  fast, but it no longer needs to reason about a separate X server's startup
  failures.
- **Complex-interior orthographic views**: Models with `complex_interior: true`
  get three extra orthographic PNGs (`_top`, `_bottom`, `_front`) to expose
  internal cavity geometry that the default isometric thumbnail obscures. These
  are supplementary; build failures do not propagate from this step. The flag
  lives in `meta.json` so no CI code change is needed when adding a new
  complex-interior model. This scope is a deliberate cost/benefit call: an
  external tool (vibe-modeling) renders an unconditional ~17 views per part,
  but the owner reasoned that "S3 storage and CI time scale with the
  collection... most parts don't benefit" from that (#202) — three views,
  opt-in per project, was chosen instead of matching vibe-modeling's
  unconditional approach. Don't widen this to render extra views for every
  model on the strength of "more views could help" alone.
- **Stable OG image URL**: The `og-hero.png` URL is not cache-busted (unlike
  other assets). Social media crawlers cache by URL, so a stable path ensures
  previews update when the image content changes rather than producing stale
  entries for old URLs.
- **Fail-fast verification**: `openscad --version` (step 4) runs early,
  right after the devShell resolves the toolchain, to surface a version
  mismatch against the committed `.openscad-version` baseline before the
  (potentially very long) STL render step begins.
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
- **Three.js SHA-256 verification**: every Three.js asset — both the copies
  staged same-origin under `site/vendor/three/<version>/` for `index.html` /
  `embed.html` and the copies inlined into standalone HTML — is verified
  against the SHA-256 hashes pinned in `scripts/threejs_assets.py` to prevent
  supply-chain attacks from the CDN. A host-level cache
  (`$HOME/.cache/3d-models/threejs/`) avoids re-downloading on subsequent
  runs, with the cached copy also verified. A
  mismatch is a hard failure, deliberately outside the deferred-enforcement
  pattern. A missing or malformed pin is equally fatal: `fetch_url()` refuses
  to download at all unless an expected digest is supplied (issue #498).
  pattern — a tampered runtime must never reach S3 (issue #403).
- **QR codes in separate directory**: QR PNGs are stored in `site/qr/` rather
  than alongside model thumbnails in `site/`. The OG hero image step no
  longer globs `site/*.png` (issue #458), but `site/qr/` stays separate to
  keep QR PNGs out of the deployed thumbnail namespace.
- **Explicit ImageMagick font**: the OG hero step always passes `-font
  Liberation-Sans` because ImageMagick has no default font and `montage`
  fails outright without one (issue #352). `MAGICK_FONT` and supplying a
  `type.xml` via `MAGICK_CONFIGURE_PATH` were both tried and did not fix the
  default; naming the font on every invocation is the only fix that works.
  The `default` devShell now pins `FONTCONFIG_FILE` (via
  `pkgs.makeFontsConf` in `flake.nix`) to a font set containing
  `liberation_ttf` so `Liberation-Sans` resolves identically on every
  runner — see step 11.
- **PR comment resilience**: The comment step uses `continue-on-error: true`
  and `scripts/pr_preview_comment.py` retries each request 3 times (2s ×
  attempt backoff) so transient Forgejo API errors don't fail the workflow. The
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
  `slugify()`, `display_name()`, `project_display_name()`, `thumbnail_name()`,
  `parse_scad_map()`, and `load_meta_failures()` used by multiple CI steps
  (structured data, OEmbed, link tag injection, interference check, QR
  generation, models manifest, changed-projects list). This prevents slug and
  display-name logic drift and ensures `.meta-failures` loading is consistent
  across all consumers. `display_name()` converts an STL filename to a human
  name; `project_display_name()` converts a project *directory* name to its
  canonical display name (hyphens/underscores → spaces, title-cased) — the
  two are distinct transforms with distinct call sites, not duplicates of
  each other.
- **Three.js version consistency across viewers**: `generate-standalone.py`'s
  `_check_threejs_version()` parses `vendor/three/<version>/` out of both
  `index.html` and `embed.html` import maps and validates each against
  `THREEJS_VERSION`. Both files hardcode the vendored path independently, so a
  version bump in one without the other would silently run mismatched versions;
  an import map with no vendor path at all hard-fails the build.
- **Mating part interference checking**: `check_interference.py` uses
  `trimesh` and `manifold3d` to perform boolean intersection on STL pairs
  declared in `meta.json`'s `mating_pairs` field. This catches design errors
  where two parts that should fit together physically overlap. Results are
  stored in `site/interference.json` and displayed in the PR comment as a
  table with overlap volume in mm³. The step uses the same deferred
  enforcement pattern as mesh and metadata validation — failures are
  recorded early but only block the build at the final enforcement step
  (step 24), so the full pipeline output is always available.
- **Parameters manifest deferred enforcement**: `*.parameters.json` validation
  (step 2.5) follows the same deferred pattern. Failures go to `.param-failures`;
  the manifest generation step reads that file and excludes invalid manifests from
  `models.json` so the customizer never loads a broken parameter set. Enforcement
  fires at step 25 so the full pipeline output is always available even when a
  manifest is malformed.
- **Non-threaded openscad-wasm build**: The customizer uses the non-threaded
  WASM build (`openscad.js` / `openscad.wasm`) rather than the threaded build.
  The threaded build requires `SharedArrayBuffer`, which requires COOP/COEP
  response headers that plain S3 hosting cannot set without a CloudFront
  function. Non-threaded avoids this dependency at the cost of slightly slower
  renders (no SIMD parallelism). Assets are pinned to release `2022.03.20` with
  SHA-256 verification in `scripts/fetch_openscad_wasm.py`. Every file in
  `ASSET_FILES` must carry a pinned digest in `EXPECTED_HASHES`; an unpinned
  name raises rather than warning.
- **Filename allow-list in render step**: Before rendering any `.scad` file,
  the basename is checked against `^[A-Za-z0-9._ -]+$`. Filenames with
  characters outside this set would propagate into generated STL paths, HTML
  snippets, and JSON, creating potential injection vectors. Hard-failing early
  is safer than escaping every downstream consumer.
- **Name-collision checks are static, not runtime**: every renderable's
  output lands in one flat namespace (`site/<name>.stl`, `.png`,
  `site/qr/<name>.png`, `site/standalone/<name>.html`), and each renderable's
  OEmbed endpoint and deep link are keyed on `slugify()` within its project.
  Both basename and slug uniqueness are therefore a property of the source
  tree alone, so they are `scripts/test_output_names.py` unit tests that run
  in step 2.6 and fail in seconds — not deferred-enforcement checks or bash
  guards inside the `find | while` render loop, which would only fail after
  the first colliding STL is already on disk (issue #449).
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
  during CI (step 17), just like `index.html` and `filament-colors.json`.
  Keeping them as committed source files means they are version-controlled and
  reviewable via PR, while the copy step ensures they land in the deployed
  directory.
- **Fresh WASM instance per render**: Each customizer render creates a new
  emscripten instance via the factory (the factory itself is cached). Reusing
  one instance across renders causes silent "empty STL" failures because
  emscripten's `exit()` call at the end of `callMain` corrupts the module's
  internal FS state. A new instance per render is more expensive but reliable.
- **Unit tests run in CI**: `python3 -m unittest discover -s scripts -p
  'test_*.py' -v` runs on every push (step 2.6) before any heavy tools are
  invoked. These tests mock I/O and finish in seconds, catching regressions
  in build-script helpers before rendering begins. Discovery means every
  `scripts/test_*.py` module runs automatically — there is no hand-maintained
  list to fall out of sync (issue #457). `test_build_workflow.py`'s own
  `UnitTestStepCoverageTests` pins the discovery invocation and asserts no
  module is named individually in the step; a module whose third-party deps
  aren't all in the `default` devShell must self-skip via
  `unittest.skipUnless`/`skipIf` (see `ENV_GATED_TEST_MODULES`), never be
  silently omitted.
- **site/sources/ layout**: All `.scad` source files, validated
  `*.parameters.json` manifests, and binary render assets (`.png` files whose
  basename appears in a sibling `.scad`) are staged under
  `site/sources/<project>/` during CI (step 6.3). A per-project `manifest.json`
  lists the project's transitive include chain as project-relative paths
  (`../<other>/<lib>.scad` for a cross-project include) because S3 does not
  serve directory indexes. The browser's `loadProjectSources()` function fetches this manifest to
  discover all project files; `.scad` entries are fetched as text and written into
  the WASM FS as UTF-8; `.png` entries are fetched as `arrayBuffer` and written as
  raw bytes so `surface()` can read them.

## Forgejo cutover

The repo moved from GitHub Actions to Forgejo Actions in issue
clw_01M45RK9YR5VC9XXHMQP84VKPV. The Forgejo repo is canonical; the GitHub
repo is archived. Two AWS facts were not in any repo when the port was
written:

- **Deploy role.** The IAM role behind `AWS_ROLE_ARN` is managed in the
  bstjohn-blog tofu stack, `tofu/3d-models-deploy-role.tf` (role and trust
  policy only, with `prevent_destroy`). It was created by hand for PR #16 in
  the account holding the `www.bstjohn.net` bucket and adopted by an
  `import` block. Its permission policy stays console-owned and already
  covers `3d-models/*`, which includes the render loop's `render-cache/` and
  `render-cache-pr/` reads and writes (the main deploy's `sync --delete`
  excludes both). The Forgejo IAM OIDC provider is owned by bstjohn-blog
  `tofu/forgejo-oidc.tf`, ARN
  `arn:aws:iam::<account>:oidc-provider/www.bstjohn.net/forgejo-oidc`
  (issuer `https://www.bstjohn.net/forgejo-oidc`, audience
  `sts.amazonaws.com`).
- **Trust policy.** IAM condition keys use the issuer with its scheme
  stripped, so the prefix is `www.bstjohn.net/forgejo-oidc:`. The
  bstjohn-blog stack applies the Forgejo statement below, and the
  `github-actions-3d-models` role trusts only that statement: the GitHub
  statement was removed in bstjohn-blog #clw_01M4DW6AHJ8EJG0YM4X0NN1C0M.
  The JSON is also the console-fallback reference if adoption into
  tofu is not wanted (a later adoption must then reproduce it exactly):

  ```json
  {
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<account>:oidc-provider/www.bstjohn.net/forgejo-oidc"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "www.bstjohn.net/forgejo-oidc:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "www.bstjohn.net/forgejo-oidc:sub": [
          "repo:St-John-Software/3d-models:ref:refs/heads/*",
          "repo:St-John-Software/3d-models:pull_request"
        ]
      }
    }
  }
  ```

  `ref:refs/heads/*` covers `main` deploys, `claws/preview-issue-*` pushes
  and the cleanup workflow's `delete` and `workflow_dispatch` runs (which
  `sub` Forgejo mints for a `delete` run is unverified, but any branch ref
  is covered). `pull_request` covers PR builds and PR-close cleanups.
- **Session duration.** The workflows use the default one-hour session. The
  live role's `MaxSessionDuration` is 4 hours (the console offers only 1, 2
  or 4), and tofu pins `max_session_duration = 14400` to match in
  `tofu/3d-models-deploy-role.tf`.
- **Render-cache expiry.** Add an S3 lifecycle rule on the bucket that
  expires objects under `3d-models/render-cache/` after 365 days, and one
  for `3d-models/render-cache-pr/` (a shorter window, e.g. 90 days, is
  fine: only previews read it). Expiry
  counts from upload, not last read, so the initial burst expires together;
  keep it long so that cold render is rare. Nothing else prunes the prefix,
  and an expired entry only costs a re-render.

Dependency updates moved from Dependabot to fleet-infra's Forgejo Renovate
(`apps/renovate/configmap.yaml`), and fleet-infra sizes the runner
pods' dind memory limits for this repo (see the Runner bullet above).

## Main-branch failure monitoring

There is no failure-notification workflow in this repo. Main-branch
`push`/`schedule` runs of `build.yml` are watched centrally by Claws'
`main-build-monitor` job (St-John-Software/claws#2778), which:

- retries the run once when the failure looks transient (dead runner, cancelled
  job, infrastructure error);
- otherwise opens a `Build failure: Build Models` issue in this repo, or bumps
  the existing open one rather than filing duplicates during a prolonged
  outage;
- closes that issue with a comment when a later main-branch run of the same
  workflow succeeds.

Because the monitor runs in the Claws service rather than on the repo's
runners, an outage of every eligible `[container, linux]` runner is still
reported. PR failures never generate issues.
