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

An enclosure holding mains-side parts alongside low-voltage electronics must keep them in separate zones, and a display lid must frame the active display area rather than expose the whole module. In the heating controller box the segregation is on the DRC-checked carrier PCB, so the box needs no partition rib; it keeps the lid-mounted toggle and lamp bodies at least 10 mm from the board edge (12 mm to the toggles, for the J3 CPC entries). Mains leads use the wiring channel under the board and the right-hand column; SELV leads cross the board's top edge to the display and stay in the top and left strips.

**Why:** the heating controller box replaces a wall programmer fed by a mains cable; the owner required safe separation and a tidy faceplate. Unmeasured or unbought parts (toggle bushings, lamps) use parametric estimates until measured.

### Heating controller fixings must use heat-set inserts and a printed insulating boss

Every screw (CYD bosses and carrier posts on the lid, lid-to-base corner posts) goes into an M3 heat-set insert pocket in a printed boss; no nylon standoffs. The lid toggle cut-out copies the switch's legend-plate profile (12 mm circle with a 1 mm key tab at 6 o'clock, the bottom of the hole), oriented so switch travel is vertical.

**Why:** the owner chose inserts for every fixing; the printed boss insulates the mains-side carrier board. The pocket diameter stays one parameter (2.6 mm gives a self-tapping pilot). This supersedes the earlier self-tapping pilot and standoff assumptions.

### The heating controller faceplate must carry the delivered 97 x 100 mm carrier board

The faceplate carries the delivered 97 x 100.0 mm carrier on printed heat-set insert posts at its 89 x 92 mm H1-H4 hole pattern, behind the display, component side toward the wall, so the display, toggles, lamps, carrier and every lead between them are wired on the bench before installation. The back box is a shell with the wall fixings, a bottom-wall cable entry for the two incoming cables and a cable-tie anchorage for strain relief; the cavity is at least 72 mm deep, sized to the 70 mm as-built wiring depth measured from the faceplate front, with 5 mm to spare, and the bottom-edge terminal row faces the wiring channel. The toggles and lamps sit beside the board, never over it. The fit is confirmed by a dry fit of the populated board on the printed faceplate, closed onto the box, not only against the KiCad file, and the design makes no change to the PCB or its generator. The bench-wired assembly measured 70 mm behind the faceplate front, so the board stack alone under-sized the box. **Supersedes** the base-mounted version, which carried the board on bosses in the back box.

**Why:** the owner ordered the PCB first (2026-10-14) so the enclosure could be designed around the real board; it has arrived and replaces the v1 relay-board, PSU and WAGO layout. Wiring the whole assembly on the bench and landing only the incoming cables at the wall is easier and safer than wiring into a box already on the wall.

### The heating controller back box must take surface-run cables from below

By default the two incoming cables enter through a slot in the bottom wall, flush with the floor, each tied to its own anchor on a straight run to its terminal, with at least 150 mm of free length beyond the anchor; the floor knockout is an opt-in for cables arriving from behind the box. The entry never intersects the vents, wall fixings, stylus sleeve or lid lip.

**Why:** the owner's cables run on the wall surface and arrive from below the box (issue filed 2026-11-04), so a floor-only entry could not be used without cutting the print.

### The heating controller box must store the touchscreen stylus

The base keeps the board's bundled stylus (87.3 mm long, with a chunky cap) in a sleeve that cannot break into the mains compartment and from which a stuck stylus can be pushed out.

**Why:** the owner wants the stylus to live with the controller.

### The busy-board enclosure must fit the owner's 250 x 250 mm print bed

Each enclosure part, and so the board outline (at most 222 x 222 mm with the wall allowance), must fit a 250 x 250 mm plate. If the board does not route, rearrange the LEDs rather than grow the enclosure.

**Why:** the owner prints on a Bambu Lab A1 and set about 2 mm of print margin.

### The busy-board enclosure must follow the chosen parts and child-safety rules

Plate and board cut-outs are sized to the owner's chosen Switch Electronics parts (APEM 5000-series toggles, 19 mm slide switch, 20 mm encoder, 16 mm pots, 20 mm CLIFF K15 knobs), with unconfirmed dimensions kept parametric. The enclosure holds three LiFePO4 14500 cells, charger, boost and protection board sealed behind a screwed door, with a recessed rear USB-C opening, a buzzer grille that is not a finger trap, radiused play-side edges, and no play-side openings other than controls, their anti-rotation tab holes, the buzzer grille and (v2) the display opening closed by a pane fixed from behind; v2's LED windows are closed skins, not openings. Controls are rigidly mounted with no small detachable parts.

**Why:** the board is a child's toy ordered from real parts; lithium is only acceptable sealed and never user-removable. Phases 1 and 2 are bought together, so the breadboard proof no longer gates ordering.

### The busy-board enclosure must fit both the v2 and v3 boards

One enclosure source serves the factory-assembled v3 board and the hand-soldered v2 board, whose outlines now differ. It defaults to v3's 210 x 222 mm board with five arcade buttons (four play and power); `board_v3 = false` gives v2's 222 mm square with five arcade play buttons, and v2's positions and clearances stay asserted alongside v3's rather than being replaced. v2's power button is a 19 mm red mushroom pushbutton, so its power hole is 19 mm while play-button holes stay 24.5 mm.

**Why:** the owner had only five arcade buttons on hand and chose a mushroom power switch over buying a sixth. On 2026-11-03 the owner deferred the v3 factory-assembled order (about $237 at checkout) and is hand-building v2 on the delivered boards with a hotplate, stencil and paste; v3 stays designed and orderable later, and sits beside v2 rather than replacing it.

### The busy-board v3 PCB must show through a fixed clear front in a black frame

On v3 the play side is a 3 mm clear polycarbonate plate (not acrylic), cut by a UK cut-to-size service from a DXF the build exports from the OpenSCAD model, which stays the source. A matte-black printed frame's rounded lip covers the plate's cut edge, and the frame screws to the black tray from behind, so no cut edge or fastener is reachable from the play side; the only play-side screws are the slide switch's two, held by nyloc nuts. The board stands 15 mm behind the plate on standoffs from the tray, with nothing fixed through the plate's play face. The plate has no LED holes or display windows.

**Why:** the owner wants the board to look like real electronics (black mask, gold title) while keeping the child-safety rules: the PCB stays unreachable behind a fixed panel. A separate faceplate PCB was rejected.

### The busy-board v2 front must be a robust, opaque printed plate

On v2 the play side is an opaque plate printed in light PETG that drops into the same frame rebate and presses on the same 15 mm standoffs: a 5 mm slab with ribs behind it, thinned to 3 mm only where a control's thread is short, carrying every control cut-out. Every chain LED and the 4-digit display stay visible with no opening a finger or probe can pass: each LED glows through a closed skin printed into the plate, and the display reads through a small clear pane fixed from behind and larger than its opening. Nothing small can detach from the play side. The frame, tray, door and standoffs are unchanged.

**Why:** on 2026-11-12 the owner chose a robust printed front for the hand-built v2 over the clear polycarbonate sheet, so the toy takes a toddler's knocks and can be made at home; v3 keeps the clear front.

**Supersedes:** the clear 3 mm polycarbonate plate and its cut-sheet DXF for v2.

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

### The RF433 bridge enclosure keeps the antenna and USB port outside the box

The enclosure keeps the SMA antenna outside the box and positionable vertically, keeps the devkit's USB port reachable with the box closed, keeps metal fixings out of the WROOM antenna keep-out, and works both freestanding and screwed down.

**Why:** the bridge's placement between the dimmer and the blind is undecided, and the antenna must stay fitted before power-up.

### The heating controller lid window must be centred on the display's active area

The lid's display window is centred on the visible glass of the CYD, not on its mounting-hole pattern, so the full 320 x 240 active area shows with no bezel inside the window. Only the lid changes; the base and the display boss positions stay, because the carrier board and faceplate hardware are already built.

**Why:** the owner's first power-up (2026-11-05) showed about 3 mm of the glass hidden on the toggle side; rotating the display 180 degrees only moves the hidden strip. The shift is an owner estimate until the owner confirms it on a reprint.

### The RF433 bridge enclosure must fit the devkit and radio module as fitted to the carrier

The enclosure is sized from the owner's caliper measurements of the assembled bridge board, where the devkit's USB end and the CC1101 module and SMA end overhang the 62 x 60 mm carrier. The USB window and antenna slot keep their test-print-confirmed positions and move outward to the real faces, erring generously for the aerial. Dimensions the owner has not measured keep their design values until a print shows a problem.

**Why:** the first print's openings were placed correctly but the board could not seat because the overhangs were underestimated.

### The Pi rack shelf must split into bed-sized bolted halves and keep each Pi's cable side open

The 2U 19-inch Raspberry Pi rack shelf prints as two halves no wider than about 250 mm that bolt together stiffly enough to carry four Pis cantilevered from the rack ears. Each Pi stands on its long edge with its network end facing out through its own faceplate window, and its power and HDMI side faces up under an open top, with headroom for right-angle plugs.

**Why:** the owner prints on a Bambu Lab A1 (256 x 256 mm bed), and keeps the Pis in their existing cases with their existing cables, which leave both a short end and a long side.

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
