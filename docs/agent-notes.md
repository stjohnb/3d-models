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
