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
   scripts/request-issue-preview.sh <issue-id> new-project/candidate.scad new-project/meta.json
   ```
   `<issue-id>` is an issue number or a Claws `clw_…` id. The script accepts
   `.scad` files plus a project's `meta.json` and `dependency-graph.md`;
   anything else is rejected. This pushes the files to
   `claws/preview-issue-<id>` — no PR is opened. No rendering happens on this
   host; the push runs the existing `build.yml` pipeline on a self-hosted
   Linux runner. The script prints the branch, the viewer URL
   (`https://www.bstjohn.net/3d-models/issue-preview/<id>/<sha8>/`) and the
   summary URL (`…/<sha8>/preview-summary.json`).

   On the automation host, git's configured `libsecret` credential helper
   can't reach a Secret Service, so `git push` inside the script fails with
   `fatal: could not read Username for 'https://github.com'` unless the
   environment adds the `gh` helper:
   ```bash
   GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.helper \
   GIT_CONFIG_VALUE_0='!gh auth git-credential' \
   scripts/request-issue-preview.sh <issue-id> path/to/candidate.scad
   ```
   With the override in place, libsecret still prints `CRITICAL **: could not
   connect to Secret Service` lines to stderr; they're harmless. The same
   prefix is needed for the `git fetch origin claws/preview-issue-<id>` diff
   check in step 5 and for `--cleanup`.
3. Watch the build with `gh run list --branch claws/preview-issue-<id>`, but
   don't block the plan on it. If the build hasn't finished, note the
   pending head (`<sha8>`) in the plan. Claws' `issue-preview-sync` job
   fetches `preview-summary.json` for the branch head and mirrors its
   `markdown` into the issue's `## Preview` comment on its next tick (and
   right after a plan is posted). While the render is pending it says so.
   The planner does not post the summary itself. Post the summary or run
   `--cleanup` yourself only when Claws' `issue-preview-sync` is down, the
   issue is not tracked by Claws, or the `## Preview` comment has not
   appeared roughly 15 minutes after a green preview build.
4. Re-run step 2 only when a revision changes what the preview renders —
   dimensions, features, parameters, or which files are previewed. Skip it
   entirely for prose-only changes. Before re-running, check whether the
   candidate files actually changed:
   ```bash
   git fetch origin claws/preview-issue-<id>
   git diff origin/claws/preview-issue-<id> -- <files>
   ```
   An empty diff means skip — re-pushing an unchanged tree still costs a
   full render via the `build` job. Each re-run force-pushes the same branch and
   deploys to a new `<sha8>` under the same issue prefix. Name the
   previewed `<sha8>` in the plan's Decisions, or say why the preview wasn't
   refreshed.

## What the summary gives you

`preview-summary.json` carries everything the "🔍 Model Preview" PR comment
gives a real PR (see [docs/ci-pipeline.md](../docs/ci-pipeline.md), "Issue
previews (PR-less)"):

- PNG thumbnail URLs for every renderable changed in the preview, grouped by
  project, plus `top`/`bottom`/`front` views when present
- File size and triangle count per model
- The mesh-validation results (ADMesh: watertight, no degenerate triangles,
  positive volume)
- The interference results, if the candidate declares `mating_pairs` in
  `meta.json`
- The live, interactive `issue-preview/<id>/<sha8>/` viewer URL
- A ready-to-post `markdown` body rendering all of the above

## Seeing interior cavities

A single isometric thumbnail can hide geometry that determines whether a
part actually works. Set `complex_interior: true` in the candidate's
`meta.json` to get three extra orthographic views (`top`, `bottom`,
`front`) in the same build — this is `build.yml` step 9.5, the same
mechanism `power-workshop` and `drawer-organiser` use. Don't invent a new
view mechanism; this one already exists and the issue preview gets it for
free.

## New project directories

If the proposal introduces a directory that doesn't exist yet, include a
minimal `meta.json` (only `description` is required by
`meta.schema.json`) among the candidate files. Without it the model never
reaches `models.json` and won't appear in the preview viewer or the
grouped section of the summary.

## Library-only changes

A change confined to an underscore-prefixed library file (`_*.scad`)
produces no thumbnail — libraries render no STL, and the summary maps
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
host, and why the planner shouldn't need one now that issue previews exist.

## Claws' preview sync

Claws' `issue-preview-sync` job runs every five minutes. It finds a bare
`claws/preview-issue-<id>` branch through this repo's `claws.json`
`issuePreviewSummaryUrl` template, fetches the branch head's
`preview-summary.json`, and mirrors its `markdown` into the issue's `## Preview`
comment (writing the current or pending render status). When the plan is
Refined or the issue closes, Claws deletes the preview branch (firing
`pr-preview-cleanup.yml` the same way a manual delete does to reclaim the S3
prefix) and records the retirement in the same comment.

Claws also watches open PRs on `claws/preview-issue-*` branches as a legacy
fallback for draft preview PRs left over from before the PR-less pipeline
existed. When such a PR is open, Claws copies its "🔍 Model Preview" comment
into the issue's `## Preview` comment and closes the PR itself on Refined or
close. **Don't close a legacy preview PR by hand** — let Claws' sync job
retire it, or let `--cleanup` below close it as part of its own run.

## Cleanup (manual fallback)

Claws retires the preview branch once the plan is Refined or the issue
closes; you normally do nothing.

If Claws' sync is unavailable, the issue is not tracked by Claws, or the
`## Preview` comment hasn't appeared roughly 15 minutes after a green
preview build, manually retire the preview:

```bash
scripts/request-issue-preview.sh --cleanup <issue-id>
```

If a legacy draft preview PR is still open on the branch, `--cleanup` closes
it itself before deleting the branch — it doesn't wait for Claws to close it
first. Deleting `claws/preview-issue-<id>` fires `pr-preview-cleanup.yml`,
which reclaims the whole `issue-preview/<id>/` S3 prefix. If the branch is
already gone but the prefix is not, run `gh workflow run
pr-preview-cleanup.yml -f issue_id=<id>`.
