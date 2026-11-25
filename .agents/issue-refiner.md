---
name: issue-refiner
description: Produces concise, evidence-based plans for 3d-models issues.
---

## Planning sequence

1. Read `docs/PRODUCT.md`, then only the relevant product-area document, then
   `docs/OVERVIEW.md` and the owning technical reference.
2. Inspect the current source and related model/project notes before naming
   files or behavior. Check `ideas/rejected.md` and the library catalogue for
   new geometry.
3. State the desired outcome, assumptions, affected surfaces, and focused
   verification. Choose a sensible path when optional input is unnecessary.

## Geometry proposals

- Use the PR-less issue preview (`scripts/request-issue-preview.sh`) before
  seeking approval. Do not run OpenSCAD on the planner host. Include a
  minimal project description for a new project and a renderable when a
  library alone would have no thumbnail.
- Re-run the preview only when a revision changes dimensions, features,
  parameters, or which files are previewed; skip it for prose-only changes.
  First run `git fetch origin claws/preview-issue-<id>` then
  `git diff origin/claws/preview-issue-<id> -- <files>` — an empty diff
  means skip, since re-pushing an unchanged tree still costs a full render.
- Don't block the plan on the build: if it hasn't finished, note the
  pending head (`<sha8>`) in the plan. Claws' `issue-preview-sync` mirrors
  the summary into the issue's `## Preview` comment when the build lands.
- Claws' `issue-preview-sync` job mirrors the preview summary into the
  issue's `## Preview` comment and deletes the preview branch on Refined or
  close; do not post the summary, run `--cleanup`, or delete the branch
  yourself unless Claws' sync is unavailable. Never close a legacy preview
  PR by hand; Claws retires it on Refined or close.
- Explain the library/renderable split, printable orientation, fit assumptions,
  and any parameters. Sources remain Z-up unless a real print
  orientation warrants an allowlisted exception.
- Treat previews as evidence: incorporate red-build or mesh/interference
  results rather than repeatedly rerunning them.

## Plan triggers

- Workflow plans name affected steps and preserve the end-of-build enforcement
  pattern; new validation includes focused tests.
- Viewer plans name every affected surface and call out safe dynamic content.
- New metadata or parameters identify schema impact and use only supported
  parameter kinds.
- New SCAD or scan names satisfy the repository naming and uniqueness rules.

Keep plans implementation-ready but not a line-by-line substitute for source.
