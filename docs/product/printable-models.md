# Printable models

**Reference.** Read this when planning a new physical object or changing a
model's fit, layout, or printability. For gallery behavior read
[gallery-experience.md](gallery-experience.md); for implementation details read
[../model-projects.md](../model-projects.md).

## Problem

Useful household, workshop, and hobby objects often need a replacement or a
fit-specific solution that commercial parts do not provide.

## Users

The maintainer is the primary printer and tester. Visitors may download models
and need the same practical guidance to make a successful print.

## Requirements

### Model fit must be refined from physical measurements and test prints

Use named, adjustable dimensions and accept subsequent measured corrections to
fit, clearance, and geometry rather than treating an initial issue as final.

**Why:** physical parts, drawers, and printers reveal constraints that are not
reliably known before the first print.

### Oversized drawer parts must respect the available print bed

Parts that cannot fit the printer must be delivered as practical pieces whose
joints can be assembled; where possible, joints must not coincide with the
supporting base joins.

**Why:** the owner's printer has a limited bed, and offset joins make the
assembled drawer organizer stronger and sit flatter.

### Every intended printable component must be directly downloadable

An assembly preview must not be the sole way to obtain a constituent part.

**Why:** the maintainer needs to print individual replacement and organizer
pieces without extracting them from an assembly.

### Printing guidance must remain free-text and model-specific

Models may provide practical slicer and printer advice as prose, rather than a
new structured orientation or support taxonomy.

**Why:** non-obvious print advice matters, while structured print metadata was
explicitly rejected as premature and too rigid.

### External controls on the muesli dispenser must remain outside the box

The user handle and dispensing chute must be accessible from outside the cereal
box; an internal turning mechanism is not an acceptable design.

**Why:** the owner rejected the earlier arrangement as nonsensical to operate.

### A replacement model must preserve the installed interfaces that already fit

When modifying an installed assembly, retain unchanged mating bases, hooks, or
locations unless the reported failure requires changing them.

**Why:** the owner has printed and relies on existing companion parts, such as
the toothbrush base and tray connection.

## Non-goals & rejected ideas

### Never derive model outlines by tracing a reference photograph

Reference photos may inform measurements, but are not a geometry template.

**Why:** prior attempts produced poor, unstable shapes; measured parametric
design is the accepted approach.

### Do not reintroduce rejected toothbrush-grip changes

Drying spikes may be improved independently, but the rejected grip approach
must not return without a new owner decision.

**Why:** the owner said that approach would not work.

## Open questions

- Which future real-world objects need scan references rather than direct measurement?
