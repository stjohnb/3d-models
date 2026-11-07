# Gallery experience

**Reference.** Read this when changing how visitors find, inspect, customize,
or download models. For product privacy read [publication-safety.md](publication-safety.md);
for technical viewer behavior read [../web-viewer.md](../web-viewer.md).

## Problem

As the collection grows, visitors need a calm, usable way to explore models
without making the gallery expensive to run on ordinary hardware.

## Users

Visitors browse and download models on desktop and mobile devices; the
maintainer also uses the gallery to inspect current designs.

## Requirements

### Existing model links must continue to resolve after gallery redesigns

Navigation and presentation may change, but previously shared model links must
remain usable.

**Why:** the owner explicitly required continuity when the viewer was redesigned.

### The gallery must prioritize current and interesting models while retaining the full collection

The landing experience should surface recent or substantial projects first,
without hiding older or simpler models from discovery.

**Why:** a growing collection needs a useful first view, not an arbitrary list.

### Viewing multiple models must remain possible without an always-on rendering cost

Visitors may compare or compose models, while idle and unopened views should
avoid disproportionate heat and battery use.

**Why:** the owner wanted multi-model viewing and reported that the page
overheated a 2019 laptop.

### Print notes and descriptions must yield space to the model view by default

Supplementary prose should be available but initially collapsed where it would
reduce viewing space.

**Why:** the owner asked to give the actual model more room.

## Non-goals & rejected ideas

### Do not add maturity badges or an automatic print-orientation indicator

The gallery must not present speculative lifecycle labels or rigid orientation
metadata.

**Why:** these ideas are recorded as rejected by the maintainer.

## Open questions

- Which additional accessibility improvements are most valuable for the model browser?
