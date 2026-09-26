# Product requirements

**Entry point.** Read this first when planning a feature or deciding whether a
change belongs in this repository. It states what the collection and gallery
must do and why; use the area table to find the applicable constraint, then
read [OVERVIEW.md](OVERVIEW.md) for implementation context.

This is a personal collection of useful, printable objects and a gallery for
finding, inspecting, and downloading them. It is for the maintainer making and
iterating on physical prints, and for visitors who need an understandable,
safe way to view and reuse the models.

## Goals

- Deliver practical, printable models that can be refined from real measurements and test prints.
- Make models easy to discover, inspect, customize where useful, and download.
- Publish reusable source without exposing private material or image metadata.
- Keep the supporting workflow proportionate to a personal hobby repository.

## Non-goals

- Replacing measured parametric design with photo-outline extraction.
- Adding speculative process machinery, badges, or generated-artifact history.
- Adding structured printing-orientation metadata or automatic site promotion before its pilot is accepted.

## Areas

| Area | Read this when | Doc |
|---|---|---|
| Printable models | Adding, correcting, or splitting a physical model | [product/printable-models.md](product/printable-models.md) |
| Scanning | Changing the scanning rig, capture process, or scan references | [product/scanning.md](product/scanning.md) |
| Gallery experience | Changing discovery, viewing, downloading, or print guidance | [product/gallery-experience.md](product/gallery-experience.md) |
| Public publication | Publishing source or handling images and privacy | [product/publication-safety.md](product/publication-safety.md) |

## Cross-cutting constraints

- CI failures must be fixed at their source; unrelated-looking failures are not grounds to bypass a check. **Why:** a green merge must mean the delivered build is healthy.
- Research work must produce the agreed repository change, not merely restate findings. **Why:** the owner asked for action rather than summaries.
- Keep tooling and process lean until a concrete need exists. **Why:** this is a hobby repository, not an enterprise platform.
- Treat incomplete dimensions as a normal starting point and incorporate corrections from real prints. **Why:** fit and measurements are learned iteratively.
