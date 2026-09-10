# Playbook: Preview a Proposed Model During Issue Planning

Use `scripts/request-issue-preview.sh` to get rendered, mesh-validated
geometry on an issue **before** a plan is approved (issue #518). This
playbook is for the **planner**, running on `openclaw` — a shared,
memory-constrained host that must never run `openscad` locally. For
iterating on a model's geometry once an implementation PR already exists,
use [playbooks/iterate_with_render_view.md](iterate_with_render_view.md)
instead; that one is for the implementer, working locally with
`render_view.py`.

## The loop

1. Write the candidate `.scad` file(s) into the worktree (and a minimal
   `meta.json` if the proposal is a new project directory — see below).
2. Request a preview:
   ```bash
   scripts/request-issue-preview.sh <issue-number> path/to/candidate.scad
   ```
   This pushes the files to `claws/preview-issue-<N>` and opens (or
   updates) a draft PR labelled `Claws Ignore`. No rendering happens on
   this host — everything below runs on the `ryzen` runner via the
   existing `build.yml` `pull_request` pipeline.
3. Watch the build: `gh pr checks <N> --watch`.
4. Read the "🔍 Model Preview" comment `build.yml` posts on the PR.
5. If the geometry needs a change, edit the `.scad` and re-run step 2 — the
   script force-pushes the same `claws/preview-issue-<N>` branch, which
   updates the same PR and the same comment in place.

## What the comment gives you

Everything `build.yml` normally gives a real PR (see
[docs/ci-pipeline.md](../docs/ci-pipeline.md), "Comment on PR" and "Preview
PRs for issue planning"):

- PNG thumbnails for every model changed in the preview, grouped by project
- File size and triangle count per model
- A mesh-validation table (ADMesh: watertight, no degenerate triangles,
  positive volume)
- An interference table, if the candidate declares `mating_pairs` in
  `meta.json`
- A link to the live, interactive `pr-preview/pr-<N>/<sha8>/` viewer

## Seeing interior cavities

A single isometric thumbnail can hide geometry that determines whether a
part actually works. Set `complex_interior: true` in the candidate's
`meta.json` to get three extra orthographic views (`top`, `bottom`,
`front`) in the same build — this is `build.yml` step 9.5, the same
mechanism `power-workshop` and `drawer-organiser` use. Don't invent a new
view mechanism; this one already exists and the preview PR gets it for
free.

## New project directories

If the proposal introduces a directory that doesn't exist yet, include a
minimal `meta.json` (only `description` is required by
`meta.schema.json`) among the candidate files. Without it the model never
reaches `models.json` and won't appear in the preview viewer or the
gallery-grouped section of the comment.

## Library-only changes

A change confined to an underscore-prefixed library file (`_*.scad`)
produces no thumbnail — libraries render no STL, and the PR comment maps
changed `.scad` basenames to PNGs. Include at least one renderable that
`include`s the library so the change is visible, or point the maintainer
at the interactive viewer link instead.

## A failed preview build is signal, not noise

If the build goes red — mesh validation, interference, or a thumbnail
render failure — that's a real problem with the candidate geometry. Fold
it into the plan; don't just re-run the helper hoping it clears on its
own.

## Never render locally

This script performs zero local rendering by design. Never run
`openscad` directly on `openclaw` to "double check" a candidate before
requesting a preview — see `AGENTS.md`'s "Rendering on the constrained
build host" section for why a capped local render is even risky on this
host, and why the planner shouldn't need one now that a preview PR exists.

## Cleanup

The preview PR is disposable: draft, labelled `Claws Ignore`, and must
never be merged. Once the plan is decided, close it —
`pr-preview-cleanup.yml` reclaims its `pr-preview/pr-<N>/` S3 prefix
automatically on close.
