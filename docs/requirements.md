# Cross-Cutting Requirements

Process and workflow constraints the repo owner has stated that don't belong
to any single subsystem doc. Subsystem-specific constraints (CI checks, viewer
behavior, per-project geometry) live in [OVERVIEW.md](OVERVIEW.md) or the
dedicated doc that owns that subsystem instead — this file is only for
requirements that would otherwise have no home.

## Fix CI failures at the source; don't merge around them

When a PR's CI failure looks unrelated to that PR's own change, the owner's
standing direction is to fix the actual problem before merging anything, not
to treat it as noise to route around: "We should fix the actual issue rather
than ignoring it. The other branch can be merged once the issue has been
fixed on main" (#64). Flaky or unrelated-looking CI on a branch is not
grounds for bypassing the check — find and fix the root cause first.

## Research issues must land as action, not a restated summary

Issues that survey an external tool, article, or benchmark (e.g. an
OpenSCAD/LLM benchmark writeup, alternative CAD tools) are a recurring input
to planning in this repo (see the tool-survey issues cited throughout
[model-projects.md](model-projects.md) and [OPENSCAD_LIBRARIES.md](OPENSCAD_LIBRARIES.md)).
When such an issue is actually implemented, the owner has been explicit that
the PR must apply the findings, not just restate them: "This PR should be
implementing the suggestions rather than reciting them" (#219). Treat a
research issue's acceptance criteria as "the repo changed," never "a summary
was posted."

## Keep the project's surface area lean

This is a personal hobby repo, not enterprise software, and the owner
regularly declines infrastructure with no immediate concrete need even when
it's individually reasonable — semantic version tags, deprecation markers,
bounding-box regression guards, golden-STL-hash comparisons, issue templates,
maturity badges, scheduled freshness checks, cost rollups, and more were all
rejected in single large sweeps (#97, #109, #119; full list in
`ideas/rejected.md`). When proposing new process or tooling, prefer the
smallest thing that solves the concrete problem in front of you over general
machinery for problems that haven't occurred yet — consult `ideas/rejected.md`
before re-proposing something in this vein.

## Expect dimensional specs to arrive iteratively, not up front

Many issues in this repo are terse by design — a single corrected dimension
from a voice note (#111), a photo captioned "Bad layout" (#307), a bare model
request with no spec (#293) — and even issues with a full initial spec
routinely get corrected after a physical print or a closer caliper
measurement (the connector-fit saga #11→#99; drawer-organiser corrections in
#309/#313/#315/#326). This is the normal workflow here, not a sign of an
under-specified issue: implement a reasonable first pass from whatever detail
exists, and expect — and readily apply — follow-up corrections grounded in a
real print rather than holding out for a complete spec before starting. The
same pattern applies to a shipped model's fastener/fit details, not just
first-pass dimensions: bin-foot-opener's countersink and standoff thickness
were corrected twice after the owner reported the fitted part directly
(#492) — first "push it thinner," then the precise fix ("only the bottom
22mm touches the cabinet, and the screw heads back onto nothing").
