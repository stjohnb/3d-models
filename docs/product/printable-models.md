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

### Mains and low-voltage parts in an enclosure must be physically separated

An enclosure holding mains-side parts alongside low-voltage electronics must keep them in separate zones, and a display lid must frame the active display area rather than expose the whole module.

**Why:** the heating controller box replaces a wall programmer fed by a mains cable; the owner required safe separation and a tidy faceplate. Unmeasured or unbought parts (toggle bushings, lamps) use parametric estimates until measured.

### Heating controller fixings must use heat-set inserts and a printed insulating boss

Every screw (CYD bosses on the lid, relay bosses in the base, lid-to-base corner posts) goes into an M3 heat-set insert pocket in a printed boss; no nylon standoffs. The lid toggle cut-out copies the switch's legend-plate profile (12 mm circle with a 1 mm key tab at 12 o'clock), oriented so switch travel is vertical.

**Why:** the owner chose inserts for every fixing; the printed boss insulates the mains-side relay board. The pocket diameter stays one parameter (2.6 mm gives a self-tapping pilot). This supersedes the earlier self-tapping pilot and standoff assumptions.

### The heating controller box is redesigned around the 97 x 100 mm carrier board only once it arrives

The enclosure must fit the 97 x 100.0 mm board, its mounting holes, the relay module and cable entry to the screw terminals, and its dimensions are checked against the physical board, not only the KiCad file. The redesign waits (backlog) until the ordered boards arrive; it makes no change to the PCB or its generator, and the mains-separation rules still apply.

**Why:** the owner decided on 2026-10-14 to order the PCB first and design the enclosure around the real board.

### The heating controller box must store the touchscreen stylus

The base keeps the board's bundled stylus (87.3 mm long, with a chunky cap) in a sleeve that cannot break into the mains compartment and from which a stuck stylus can be pushed out.

**Why:** the owner wants the stylus to live with the controller.

### The busy-board enclosure must fit the owner's 250 x 250 mm print bed

Each enclosure part, and so the board outline (at most 222 x 222 mm with the wall allowance), must fit a 250 x 250 mm plate. If the board does not route, rearrange the LEDs rather than grow the enclosure.

**Why:** the owner prints on a Bambu Lab A1 and set about 2 mm of print margin.

### The busy-board enclosure must follow the chosen parts and child-safety rules

Plate and board cut-outs are sized to the owner's chosen Switch Electronics parts (APEM 5000-series toggles, 19 mm slide switch, 20 mm encoder, 16 mm pots, 20 mm CLIFF K15 knobs), with unconfirmed dimensions kept parametric. The enclosure holds three LiFePO4 14500 cells, charger, boost and protection board sealed behind a screwed door, with a recessed rear USB-C opening, a buzzer grille that is not a finger trap, radiused play-side edges, and no play-side openings other than controls, their anti-rotation tab holes and the buzzer grille. Controls are rigidly mounted with no small detachable parts.

**Why:** the board is a child's toy ordered from real parts; lithium is only acceptable sealed and never user-removable. Phases 1 and 2 are bought together, so the breadboard proof no longer gates ordering.

### The busy-board enclosure must fit both the v2 and v3 boards

One enclosure serves the hand-soldered v2 board and the factory-assembled v3 board (same outline, mounting holes and cut-outs); v2's clearances stay asserted alongside v3's rather than being replaced.

**Why:** the owner may still build the v2 boards already on order, and v3 sits beside v2 instead of replacing it; v3 is factory-assembled so the owner only wires the panel controls.

### The busy-board PCB must show through a fixed clear front in a black frame

The play side is a 3 mm clear polycarbonate plate (not acrylic), cut by a UK cut-to-size service from a DXF the build exports from the OpenSCAD model, which stays the source. A matte-black printed frame's rounded lip covers the plate's cut edge, and the frame screws to the black tray from behind, so no cut edge or fastener is reachable from the play side; the only play-side screws are the slide switch's two, held by nyloc nuts. The board stands 15 mm behind the plate on standoffs from the tray, with nothing fixed through the plate's play face. The plate has no LED holes or display windows.

**Why:** the owner wants the board to look like real electronics (black mask, gold title) while keeping the child-safety rules: the PCB stays unreachable behind a fixed panel. A separate faceplate PCB was rejected.

### Small utility models start from the owner's rough size and a plain design

A resistor box, component box or replacement peg takes the stated size (e.g. 70 x 100 x 70 mm box; peg hole 6 mm deep) and is only made fancier when clearly better.

**Why:** the owner supplies rough dimensions and photos and expects a sensible default.

### Drawer organisers must follow the stated drawer outline

Each drawer organiser is sized to the owner's measured drawer (width, depth, which side tapers) and reuses the existing organiser's style and taper dimensions when the owner says "similar".

**Why:** drawers differ per side; the owner specifies the floor outline and expects the existing design as the baseline.

### A drawer that shares a design with another must still appear as its own project

A drawer organiser built from another organiser's parts (the long-implement drawer) is a separate gallery project with its own card, thumbnail, description, notes and downloads, while the shared geometry is reused rather than copied. Its floor is sized from the owner's measured width, not a rough figure.

**Why:** the owner wants it to look like an independent project; the width was confirmed by fitting two 5 x 5 tiles after widening the drawer, superseding the rough 390 mm figure. The grid is 10 x 10 using the first drawer's 5 x 5 tiles, with no right-hand filler strip.

### Already-printed container halves must be kept when a drawer layout changes

The long-implement drawer keeps the two printed 2 x 5 halves and pairs each with a new 2 x 3 back piece (a 2 x 8 slot), puts a 4 x 1 container across the front of those slots and a second 4 x 1, open on one short side, at their back, and fills columns 1-6 with a straight flared 2 x 10 and an unflared 4 x 10. Both 4 x 1 pieces seat with their open short side toward the drawer's right (vertical) wall.

**Why:** the owner has already printed the 2 x 5 halves and wants to reuse them rather than reprint; the owner chose the straight wide pair over the diagonal split; the owner later asked for the open sides on the right.

**Supersedes:** the diagonal split and the 2 x 9 slots with 2 x 4 back pieces, as well as the earlier full-depth 2 x 10 slots.

### External controls on the muesli dispenser must remain outside the box

The user handle and dispensing chute must be accessible from outside the cereal
box; an internal turning mechanism is not an acceptable design.

**Why:** the owner rejected the earlier arrangement as nonsensical to operate.

### A replacement model must preserve the installed interfaces that already fit

When modifying an installed assembly, retain unchanged mating bases, hooks, or
locations unless the reported failure requires changing them.

**Why:** the owner has printed and relies on existing companion parts, such as
the toothbrush base and tray connection.

### Scale models of planned builds are drawn in real millimetres and scaled at the end

A model of something the owner plans to build (house, garden room, climbing
frame) uses real-millimetre named dimensions with a `scale_denominator`
applied at the end, declares print-size features as printed mm times the
denominator, and splits printable parts from a viewing-aid assembly.

**Why:** the owner wants to check the layout in 3D and in the hand before
building it, and the same source must survive a scale change.

### A planned-build model uses real timber sections and ships with a priced cut list

The climbing-frame model uses finished planed (PAR) timber sizes, not nominal
sizes, and carries a hand-written cut list with stock lengths and local
merchant prices, plus a short beam check marked as not an engineer's check.

**Why:** the owner intends to build it and needs to buy the right stock.
The frame deliberately has no canopy, guard rails or infill above the deck.

### The climbing-frame slide bay is sized for real 1.5 m-deck slides

The slide and ladder are centred in a bay opening wide enough for the common
480-506 mm wave slides, and the frame's overall length grows to fit (2611 mm);
the earlier 2.5 m limit no longer applies. Swing-bay clearances are kept.

**Why:** the owner decided on 2026-10-20 that the bay follows the products that
will actually be bought, not the nominal 500 mm deck in the first issue.
**Supersedes:** the original 2.5 m footprint of the climbing frame.

### A planned build keeps its design record as a private spec page

Each project with a real-world build keeps its design record (agreed
geometry, drawings, structural checks, sourcing and costings, and the
issues and PRs that built it) as a self-contained static spec page under
`pages/<project>/`, with the scripts that generate its figures and run its
checks beside it. CI publishes it only to the private pages host, never the
public site, from `main` and from every pull request.

**Why:** the prices and the home garden layout are private, and the record
must change in the same pull request as the model or cut list so the
reviewer sees both.

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
