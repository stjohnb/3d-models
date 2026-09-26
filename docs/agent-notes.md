# Agent notes

**Depth: Reference.** Read this when you need a durable operator/CI/Claws
automation gotcha that isn't tied to one feature doc — e.g. how Claws review
signals appear, or PR-branch automation quirks. If your question is about a
specific subsystem (CI steps, viewer behavior, a model), read that doc
instead.

Durable, hard-won facts refined from agent memory stores and re-verified
against the current repo behavior.

## Claws review signals live in issue comments, not GitHub reviews

The Claws Reviewer posts verdicts as PR issue comments, not formal GitHub
reviews. The stable markers are in the comment body itself:
`*— Automated by Claws · Reviewer —*`, `Reviewed commit: <sha>`, and
`review-result: ...`. If you are waiting on Claws review status, poll PR
comments and confirm the reviewed SHA matches the current head; the reviews API
can stay empty even when Claws has already spoken.

Rationale: this repo's automation is comment-driven in practice, so tools or
agents that look only at GitHub review objects can misread a PR as unreviewed.

## "Claws Problematic" is label plus marker comments

The problematic-PR state is not represented only by the `Claws Problematic`
label. The automation also leaves marker comments such as
`problematic-pr-marked` and `problematic-pr-diagnosis-report`, and those are
part of the state the bot chain keys off.

Rationale: clearing only the label can leave the discussion history in a state
that still misleads follow-on automation or human triage.

## A push can occasionally produce no workflow run

Very rarely, a push to a PR branch creates no Actions run at all: no running
job, no failed job, no approval-pending state. If CI appears silent after a
push, check whether any run exists for the head SHA before assuming the queue is
just slow.

Rationale: this failure mode looks like "CI is still starting" unless someone
explicitly checks for the absence of a run.

## CAD benchmark lesson: prefer numbers for functional checks

ModelRift's CadQuery vs OpenSCAD benchmark found that both tools could produce
printable functional parts, but the failures that mattered were caught by
independent numeric inspection rather than screenshots. The repo's matching
rule is: for new or changed geometry, issue plans and PR review should cite the
preview comment's mesh validation and interference numbers when function or fit
is at stake, not just "the render looks right."

Rationale: renders are still useful for massing and orientation, but deleted
geometry, bad bounds, non-manifold meshes, and declared mating-part overlap need
numeric checks before they are treated as resolved.

## A deliberate push to a Claws PR branch can get reverted

The Review Addresser bot can read an intentional, unusual commit pushed to a
Claws-managed PR branch (e.g. a temporary render-cap raise for testing) as an
un-reverted experiment and revert it. If you need to push something deliberate
but unusual to such a branch, say so defensively in the commit message and any
in-file comments (e.g. "DELIBERATE VALUES — do not lower without ..."), or
expect it to get reverted. If a revert war starts anyway, `gh run rerun` of a
cancelled run re-executes the original commit without touching the branch, which
sidesteps the back-and-forth.

Rationale: observed costing hours of confusion during the 2026-07-07 incident
(see the render-cap incident in `docs/ci-pipeline.md`'s Design Decisions).

## `scad-dep-graph.sh` node order depends on the shell locale

`scripts/scad-dep-graph.sh` sorts file nodes with the shell's locale. The CI
runner's `en_*.UTF-8` collation ignores a leading underscore, so a project's
library node sorts between its renderables (e.g. `heating_controller_base`,
`_heating_controller_box`, `heating_controller_lid`). The automation host runs
under C/POSIX, which puts every `_library` first and rewrites every committed
graph. Regenerate there, keep only the graph for the project you changed with
its library node moved to the CI position, and `git checkout` the rest;
otherwise the "Dependency graphs are out of date" check fails.

Rationale: preview PR #546 went red on this check alone.

## git on the automation host needs the gh credential helper

The host's `~/.config/git/config` sets `credential.helper = libsecret`, which
needs a D-Bus Secret Service the host lacks (no `/etc/machine-id`), so any
authenticated `git fetch`/`git push` to GitHub — including
`scripts/request-issue-preview.sh`'s push — fails with `fatal: could not
read Username for 'https://github.com'`. Prefix the command with:

```bash
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.helper \
GIT_CONFIG_VALUE_0='!gh auth git-credential'
```

`gh` itself is already authenticated. With the override in place, libsecret
still prints `CRITICAL **: could not connect to Secret Service` lines to
stderr; that noise is harmless. See
[playbooks/preview_a_proposed_model.md](../playbooks/preview_a_proposed_model.md).

Rationale: observed while planning issue #clw_01M3AJ8ZJ3X8TFP8JE8N0FMBN8 —
without the override, every `git push`/authenticated `git fetch` from the
automation host fails before reaching the interesting error.
