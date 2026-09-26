# Public publication safety

**Reference.** Read this when deciding what can be exposed publicly or when
handling photos and source publication. For gallery behavior read
[gallery-experience.md](gallery-experience.md); for the publication mechanism
read [../public-snapshot.md](../public-snapshot.md).

## Problem

The public source mirror and gallery make the project useful to others, but a
single published image or internal document can expose private information.

## Users

The maintainer needs a safe publication path; public visitors need stable,
reusable source and model information.

## Requirements

### Published raster images must contain no embedded personal metadata

Images made available through the repository must be free of location,
capture, device, authoring, and comment metadata; an ICC colour profile may
remain.

**Why:** previously published photo metadata exposed the maintainer's home GPS
coordinates and related personal details.

### Public publication must not preserve an accumulating history of exposed material

The public mirror must be republished as a fresh, single snapshot rather than
retain a browsable history of prior publications.

**Why:** mirror history is not consumed, while old history can make an accidental
publication persist.

### Publication must stop when a private or unsafe input is detected

The publication path must fail before exposing material that is outside the
approved public set or has unsafe image metadata.

**Why:** safety must not depend on a later manual review catching every leak.

## Non-goals & rejected ideas

### Do not opt into automated site promotion before the pilot is accepted

This repository must not join the promotion workflow until the designated pilot
has run successfully and the owner confirms its output is suitable.

**Why:** the owner closed the proposed opt-in pending evidence from that pilot.

## Open questions

- Whether the private repository's historical image blobs should ever be rewritten remains a maintainer decision.
