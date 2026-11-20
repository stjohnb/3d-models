# Scanning

**Reference.** Read this when changing the physical scanning setup, capture
workflow, or reusable reference meshes. For ordinary model fit read
[printable-models.md](printable-models.md); for operational detail read the
scanning and model technical references.

## Problem

Measured objects sometimes need a usable digital reference before a holder or
replacement can be designed around them; poor framing, unstable geometry, and
ambiguous rotation make that unreliable.

## Users

The maintainer captures objects with a phone and printed rig, then uses the
resulting reference to design compatible models.

## Requirements

### The scanning setup must keep the object, base, and camera relationship stable

The turntable and phone support must not slide or rotate independently while
the platter is turned, and the phone must face and centre the object.

**Why:** movement invalidates the fixed capture mask and produces unusable
reconstruction geometry.

### The scanning setup must provide usable framing and camera elevation

The camera must be far enough back to contain the rotating object and high
enough to retain top-surface coverage; changes should reuse compatible printed
parts where feasible.

**Why:** the owner observed clipped framing and low-angle failures, while also
asking to avoid discarding serviceable printed components.

### Reference scans must be suitable as design inputs before being relied on

Only a clean, scaled, watertight approximation should become the geometry used
to design a mating holder or enclosure.

**Why:** a visibly poor scan cannot reliably define a physical fit.

### Capture guidance must distinguish rotational positions

The turntable must provide non-periodic visual information for step-and-hold
captures, and hand-free frames must be selected for reconstruction.

**Why:** repeated rim features and hands can create false matches or obscure
the object.

### Scan capture must support still photos, not only video

The pipeline must accept a folder of still photos as well as a capture video,
and the capture guidance should recommend stills (one per hold) when the platter
is marked.

**Why:** video compression and motion blur smooth away the surface texture
photogrammetry matches on; stills are sharper and higher resolution.

## Non-goals & rejected ideas

### Do not treat a low-quality scan as sufficient merely because it is visible

Making a scan appear in the gallery is not a substitute for validating it as a
usable physical reference.

**Why:** the owner rejected a poor toothpaste scan after inspecting it.

## Open questions

- Which objects benefit from captures in several orientations rather than one ring?
- Is phone photogrammetry accurate enough to use as a design input at all, or
  should fit-critical objects be measured, outline-traced or scanned with
  structured light instead? The next-capture checklist in
  `playbooks/scan_a_capture.md` is meant to settle this.
