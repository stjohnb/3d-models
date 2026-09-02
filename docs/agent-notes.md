# Agent notes

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
