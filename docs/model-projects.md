# Model Projects

**Depth: Reference.** Read this when you're adding or editing a specific
model and need its file table, geometry conventions, coordinate system, or
parameters — or need a pattern shared across projects (bed-splitting,
interlocking seams, connection systems). For repo-wide architecture, CI, or
viewer questions, read [OVERVIEW.md](OVERVIEW.md) instead.

Detailed per-project reference: files, geometry conventions, and key
parameters for every model directory. See [OVERVIEW.md](OVERVIEW.md) for
repository-wide architecture and patterns.

## Cross-project patterns

Patterns shared by more than one model project. Per-project sections below
link back here instead of repeating the derivation.

### Bed-Splitting Pattern for Oversized Parts (nz-ski-fields, drawer-organiser)

When a printable part's footprint exceeds a target print bed, the module that
builds it takes a `split_parts`/`part_index`-style pair of parameters and
returns one re-centred slice via `intersection()` with a keep-box, rather than
shipping the oversized geometry as-is. `drawer-organiser` is the fullest
example: `bin_part()` splits a bin into equal pieces at cell boundaries (`gx`
must be evenly divisible by `parts`), while `container_part()` splits a
container using `floor(i*n/parts)`, so an odd cell count splits unevenly at a
real boundary instead of through the middle of a base pad; both run the outer
bound of the first/last slice well past the nominal edge to avoid a coincident
CGAL face at an unflared wall. Every whole-container renderable keeps
`split_parts`/`part_index` in its customizer manifest for arbitrary bed sizes,
and its default STL download is still the whole, unsplit shape.

For the container sizes that actually exceed the A1's 250mm bed, though, the
project ships **dedicated piece renderables** (e.g.
`drawer_container_left_front.scad` / `_back.scad`) rather than relying on
end users to run the customizer. These call the lower-level
`container_slice(gx, gy, h, wall_t, floor_t, ..., c0, c1)` — added in issue
#319 by factoring it out of `container_part()`, which now just computes
`floor(i*n/parts)` boundaries and delegates to it — with an explicit cell
range instead of an even split. The boundaries are hand-picked to land
**offset from the baseplate tile seams underneath**, so a solid piece
straddles every grid join (stiffening the assembled floor) and the cut faces
of adjacent pieces meet over the middle of a single tile, keeping them flush
even unglued (issue #322); the left container is the sole exception, since
its 10-cell depth only yields two ≤5-cell pieces by cutting at the seam
itself, and two pieces were preferred over introducing a third cut. Printing
an oversized container means printing these named piece files directly (no
customizer needed) and gluing the cut faces (CA glue) with the baseplate
itself used as the alignment jig, since the mating pads/sockets hold the
pieces in register. Full detail, including the print/glue instructions per
part and the seam-offset cell tables, lives in
[#drawer-organiser](#drawer-organiser) below and `drawer-organiser/layout.md`.

### Interlocking Tile Seams (drawer-organiser)

Baseplate tiles that must butt together into a larger continuous floor use a
genderless barbed-tab seam: every tile carries tabs on its +X/+Y edges and the
matching notches on -X/-Y, so any tile mates with any other tile of the same
edge length — no separate male/female variants to track. Tabs sit at the
**centre of each cell** along an edge, not on the cell-junction corners; an
earlier version (issue #309) put them on the junctions because that looked
like the thickest run of material, but that material is only a thin rib and
also the sole thing joining the tile's perimeter rail to its body, so a notch
sized to hold the tab severed the rail and printed tiles fell apart. At a cell
centre the rail is backed by material running the full edge length, so a notch
there only removes a slot without detaching anything. The barb's shoulder is
perpendicular to the seam (not a dovetail or round jigsaw head, which either
cam out under load or leave almost no undercut in the ~2mm of available rail
depth), which also means tiles cannot be pressed together in-plane — a new
tile must be lowered vertically onto its already-placed neighbours so its tabs
drop straight into their slots. Clearance is applied to the tab/notch
**features only**, never to the tile's outer outline, because shrinking the
outline would drift the 42mm Gridfinity pitch across every seam past the
0.25mm pad-to-socket clearance and stop a seam-spanning bin from seating. Full
derivation and measured tolerances in `drawer-organiser/layout.md`.

### adjustable-bracket/

Two interlocking pieces connected by an M5 bolt through an adjustment slot.
Adjustable span ~125–155 mm (center 140 mm). Hardware required: M5 bolt, nut,
washers.

| File | Role |
|------|------|
| `_adjustable_bracket.scad` | Shared library — parameters and modules for both pieces (no top-level geometry) |
| `piece_a.scad` | Renderable — wall piece with rounded head and adjustment slot |
| `piece_b.scad` | Renderable — bracket piece with U-channel hook |
| `piece_a.parameters.json` | In-browser customizer manifest for `piece_a` |
| `piece_b.parameters.json` | In-browser customizer manifest for `piece_b` |
| `meta.json` | Project metadata (description, tags, difficulty, hardware BOM) |
| `dependency-graph.md` | Auto-generated `include` dependency graph |
| `bracket.md` | Design notes |
| `sketch.jpg` | Reference sketch |

### bench-dog-blank/

Flush plug for the countersunk 18mm bench dog holes in an 18mm plywood
workbench top (issue #393). A 45°-tapered head fills the top 2.5mm of the
countersink (26.5mm surface diameter) and a straight shaft fills the 18mm
bore below it.

| File | Role |
|------|------|
| `bench_dog_blank.scad` | Renderable — single self-contained file, no library split, no inter-file dependencies (same pattern as `sink-tray/tray_foot.scad`) |
| `bench_dog_blank.parameters.json` | In-browser customizer manifest (`hole_d`, `top_d`, `taper_depth`, `ply_thickness`, `clearance`) |
| `meta.json` | Project metadata (description, tags: workshop/workbench, difficulty: beginner, `printing_notes`) |

**Key parameters**: the head is modeled as two frustums plus a shaft, all
diametrically shrunk by `clearance` (0.3mm) for an easy push fit:
`top_d`→`head_base_d` (= `top_d - 2*taper_depth`) over `taper_depth`, then a
constant-diameter `shaft_d` (= `hole_d - clearance`) down to a small `lead_in`
insertion chamfer at the free end. Two `assert()`s guard customizer overrides:
`head_base_d - clearance >= shaft_d` (the taper can't pinch narrower than the
shaft) and a notch-reach check (below) against `shaft_d`.

**Removal feature — pliers grip recess.** The blanks can't be pushed out from
below (they sit flush in a countersink with nothing underneath to press
against), so the model has nothing standing proud of the bench surface;
instead two rectangular notches (`notch_w` 3.5mm × `notch_len` 7mm ×
`notch_depth` 3.5mm) are sunk into the top face, flanking a central 3mm
(`bar_w`) bar whose top stays flush with the bench. Needle-nose plier jaws
drop into the two notches and close on the bar to pull the blank straight
out — pliers must close on material, so a single notch alone gives them
nothing to grip; the bar between two notches is the minimal pliers-grippable
geometry (issue #393 maintainer feedback: "a small notch that a needle nose
plyers can catch might be the easiest"). `notch_reach` (the farthest corner
of a notch from center) is asserted `<= shaft_d/2 - 1.2` so the recess can
never breach the shaft wall.

**Print orientation and the `top_trim` fix.** The part is modeled top-face
down (bar sits on the bed; each notch is a blind pocket whose roof is a
trivial bridge), so it prints support-free as exported — `printing_notes`
says so explicitly. The first printed batch sat slightly proud of the bench
surface; PR #394 review fixed this by shaving `top_trim` (0.5mm) off the
head frustum's bed-side face rather than changing `taper_depth` or `top_d` —
`head_h` and `head_top_d` are derived from `top_trim` so the taper's slope is
preserved and only its trimmed tip changes.

**Measurement note (do not "fix"):** the four caliper measurements (⌀18 bore,
⌀26.5 top, 45°, 2.5mm) describe a head that is a 45° frustum over only the
top 2.5mm — ⌀26.5 at the surface down to ⌀21.5 at its base, then a step to
the ⌀18-nominal shaft — not a full ⌀26.5→⌀18 cone (which would be 4.25mm
deep). A full-depth cone could bind and sit proud in a shallower countersink;
the shaft-plus-shallow-taper shape seats flush on any true 45° countersink at
least 2.5mm deep.

### bin-foot-opener/

Toe-operated pull for a pull-out kitchen bin drawer front. The part is a
single support-free `linear_extrude()` of one side profile: fixing plate up
the drawer's inside face, a short base under the bottom edge, and a recessed
toe lip dropping at the front. The lip is intentionally tucked behind the
visible front face rather than sitting flush with it.

| File | Role |
|------|------|
| `bin_foot_pull.scad` | Renderable — self-contained single-profile extrusion, no library split and no dependency graph |
| `bin_foot_pull.parameters.json` | In-browser customizer manifest (`base_run`, `rear_t`, `relief_h`, `relief_t`, `rear_h`, `base_t`, `lip_t`, `lip_h`, `web_drop`, `width`, `screw_holes`) |
| `meta.json` | Project metadata (description, tags: kitchen/household/accessibility, difficulty: intermediate, hardware BOM, `printing_notes`) |

**Coordinate system and print orientation**: `x` runs through the panel,
`x = 0` is the panel's back face and `+x` points into the room; `y` is in-use
up, `y = 0` at the panel's bottom edge; the extrusion runs along
`+z = width`. Like `scanning-rig/phone_stand.scad`, the model is authored in
its print orientation directly, so the exported STL is both support-free and
viewer-sensible with no top-level viewer-rotation hack.

**Recessed lip is a requirement.** `base_run` defaults to 15mm and the source
comment explicitly says it must not exceed the real panel thickness. The owner
measured one drawer front at 22mm during the first pass, but the shipped model
deliberately moved away from "run the base all the way to the front face":
keeping the lip recessed is the point. Do not extend the base to the outer
face unless the requirement itself changes.

**Web instead of end gussets**: the stiffener is one full-width triangular web
at the base/lip corner, not two side gussets. That is not an aesthetic choice:
in the chosen print orientation one end gusset would be a horizontal island
floating in mid-air. `web_run` is therefore clamped from `web_drop` rather than
asserted, so thin-panel customizer values simply shrink the web instead of
breaking the model.

**Fastener pattern**: with `screw_holes = true`, `screw_cuts()` bores a 2×2
grid of clearance holes through the fixing plate. Row placement is derived,
not fixed: both rows must land in the full-thickness plate above the relief
ramp (see below) and clear the top edge, which is why `rear_h` defaults to
60mm and the manifest floor is 57mm — below that the top-row assert fails.
`screw_holes = false` is the intended VHB-tape variant, not just a debugging
switch.

**Relieved contact band (issue #492).** The owner reported that a uniform
4mm-thick fixing plate held the drawer front proud of its neighbors when
closed, and pinned down why: only the bottom 22mm of the drawer face actually
touches the front edge of the cabinet's bottom panel, and the screw heads
back onto nothing (there is no cabinet material behind them at that height),
so the countersink was dead weight that had been the only thing forcing
`rear_t >= 3.5`. The fix is not a uniformly thinner plate — it is a relieved
band: the plate is thinned to `relief_t` (1.6mm default) over its bottom
`relief_h` (22mm default), the part of `profile()`'s `back_face` that meets
the cabinet's bottom panel, and stays full `rear_t` (4mm) above that —
`relief_top` — for stiffness and screw purchase. Screw holes are no longer
countersunk at all: the heads bear directly on the plate face above the
relief band, and `screw_y_lo`/`screw_y_hi` are derived from `relief_top` so
they always land in the full-thickness region regardless of `relief_h`.
Setting `relief_h = 0` collapses `back_face` to an empty list and reproduces
the pre-#492 uniform-thickness profile byte-for-byte.

### blast-gate/

Inline sliding blast gate for 51mm OD PVC workshop vacuum lines. A sliding
blade controls airflow to dust-collection branches; a mounting plate with
four screw holes (M4/#8 clearance) mounts the gate to shop walls or fixtures.
Related model: `vacuum-hose`.

| File | Role |
|------|------|
| `_blast_gate.scad` | Shared library — all parameters and modules (`socket_stub`, `body_block`, `gate_blade`, `mount_plate`, `gate_body`) — no top-level geometry |
| `gate_body.scad` | Renderable — housing with two pipe sockets and mounting plate |
| `gate_blade.scad` | Renderable — sliding blade with grip handle |
| `gate_assembly.scad` | Renderable — assembly preview (blade in fully-closed position), oriented for web viewer |
| `gate_body.parameters.json` | In-browser customizer manifest for `gate_body` |
| `gate_blade.parameters.json` | In-browser customizer manifest for `gate_blade` |
| `meta.json` | Project metadata (v1.1.1, difficulty: intermediate, relatedModels: vacuum-hose) |
| `dependency-graph.md` | Auto-generated `include` dependency graph |

**Coordinate system**: pipe axis = Z, blade slides along X (positive X = open).
Body is centered at origin along both axes; the gate slot is an open through-cut
at `z = ±slot_h/2` spanning the full body depth in X. Socket stubs extend at
`±body_h/2` along Z. The mounting plate sits on the `+X` (closed/blade-out) face.

**Key parameters** (all in `_blast_gate.scad`):
- `pvc_od = 51` — pipe outer diameter (widened 1mm from 50mm nominal for slip fit)
- `socket_clearance = 0.4` — diametral slip-fit clearance
- `socket_length = 25` — pipe insertion depth per side
- `bore_d = socket_id` — internal flow bore matches socket bore for unrestricted airflow
- `gate_thickness = 3`, `slot_h = 3.4` — blade thickness with 0.4mm clearance in slot
- Mount plate: `mount_plate_t = 4`, `mount_hole_d = 4`, four corner holes at `mount_hole_inset = 5` from edges
- `catch_notch_depth = 0.8`, `catch_notch_width = 3.0` — small recesses cut into inner Y-walls at the fully-closed blade position; keeps ≥1 mm of wall remaining (`y_rail = 2mm` per side)
- `catch_bump_h = catch_notch_depth - 0.1` — matching protrusions on the blade leading edge; 0.1 mm clearance at the notch far wall so the blade snaps in and resists vibration-driven opening

### drawer-organiser/

Gridfinity-compatible drawer organiser sized for a 630×424×69mm drawer
(effective floor width; see `layout.md`'s note on the original 628mm
measurement). The floor is a 15×10 grid (630×420mm, 42mm cell pitch) tiled as
3 columns × 2 rows of 5×5 tiles, plus bins, a full-drawer assembly preview,
and a printable, bed-splittable STL for every container in that preview.
`complex_interior: true` (extra orthographic views) is set in `meta.json`. Full geometry derivation,
measured tolerances, print/glue order, and the print list live in
[`drawer-organiser/layout.md`](../drawer-organiser/layout.md) — this section
is a summary.

| File | Role |
|------|------|
| `_drawer_organiser.scad` | Shared library — all parameters (Gridfinity profile constants, seam geometry, drawer dimensions) and modules (`rrect`, `cell_grid`, `bin_base_pad`, `plate_socket`, `baseplate`, `bin`, `bin_part`, `container`, `container_shell`, `container_part`, `container_dividers`, `side_flare`); no top-level geometry |
| `drawer_baseplate_5x5.scad` / `drawer_baseplate_5x5_back.scad` | Renderable — 5×5 (210×210mm) baseplate tile; `_back` omits the +Y tabs so the rear row's outer edge stays flat against the drawer wall (×3 each for the 15×10 floor) |
| `drawer_baseplate_4x5.scad` / `drawer_baseplate_4x5_back.scad` | Renderable — 4×5 (168×210mm) tile; not part of the canonical 15×10 floor (superseded by the all-5×5 layout in issue #315) but kept as optional parts for narrower drawers |
| `drawer_bin_5x5.scad` | Renderable — 5×5×8-unit (210×210×56mm) storage bin, the largest that fits an A1's 250mm bed |
| `drawer_bin_10x5_half.scad` | Renderable — half of a 10×5 (420×210×56mm) bin, via `bin_part()`; each half is 209.75×209.5mm; the two halves are the *same part* (X/Y symmetric) — print two, rotate one 180° about Z, glue |
| `drawer_filler.scad` | Renderable — 19.5×210×4.65mm edge-filler strip (optional; the 15×10 grid has no width slack for a 630mm drawer, so this is for wider drawers via the customizer's `fill_w`) |
| `drawer_container_left.scad` | Renderable — whole 3×10-cell left container (126×420×69mm assembled), too long for the bed; ships pre-split as `drawer_container_left_front`/`_back` (customizer `split_parts`/`part_index` remain for other bed sizes) |
| `drawer_container_left_front.scad` / `drawer_container_left_back.scad` | Renderable — the left container's two printable pieces, split 5+5 cells along Y at the baseplate tile seam itself (144.25×209.75mm each); mirror images, not interchangeable, since the outer wall flares |
| `drawer_container_back_4x6.scad` | Renderable — whole unflared 4×6-cell back-row container (168×252×69mm assembled, 167.5×251.5mm actual, 1.5mm over the bed); this one file *is* both the back-left and back-centre container (neither flares); ships pre-split as `drawer_container_back_4x6_half` |
| `drawer_container_back_4x6_half.scad` | Renderable — one printable piece of the unflared back-row container, split 3+3 along Y offset from the baseplate tile seam (167.5×125.75mm); 180°-symmetric, so this one file is both halves — print four (two per container, one of each pair rotated 180° about Z) |
| `drawer_container_back_4x6_half_divided.scad` | Renderable — the same back-row half piece with five upright dividers across its width (six equal segments), 3/4 of the container height and half its interior depth, centred; identical footprint and baseplate fit to `_half` |
| `drawer_container_back_4x6_right.scad` | Renderable — whole 4×6-cell back-right container (flared on its outer/+X wall, 186.25mm at the rim); ships pre-split as `drawer_container_back_4x6_right_front`/`_back` |
| `drawer_container_back_4x6_right_front.scad` / `_back.scad` | Renderable — the back-right container's two printable pieces, split 3+3 along Y offset from the tile seam (186.25×125.75mm each); mirror images because the flare breaks the rotational symmetry that lets `_half` serve both sides |
| `drawer_container_front_5x4.scad` | Renderable — 5×4-cell unflared wide front container (210×168mm assembled, 209.5×167.5mm actual); fits the bed whole, so no piece files (issue #334 split the former 8×4 into this and a 3×4) |
| `drawer_container_front_3x4.scad` | Renderable — 3×4-cell unflared front container; fits the bed whole, so no piece files (issue #324's "3x3" — see `layout.md`); serves both front 3×4 positions (columns 9–11 and 12–14) — print two |
| `drawer_container_front_1x3.scad` | Renderable — 1×3-cell front container in the drawer's last column (flared on its outer/+X wall); fits the bed whole |
| `drawer_container_front_1x1.scad` | Renderable — single-cell container behind the 1×3 (flared on its outer/+X wall); fits the bed whole, and a 1-cell axis cannot split, so it calls `container()` directly with no `split_parts` |
| `drawer_assembly.scad` | Renderable — full-drawer preview: the whole 15×10 baseplate floor plus nine seated, coloured containers (four of which flare outward to follow the drawer's 630→670mm flare); the back-centre container's front half carries the five-plate divider bank of `drawer_container_back_4x6_half_divided`; a **viewing aid, not a printable part** — not tiled for the print bed; renders at `$fn = 32` like `nz-ski-fields/assembly.scad` |
| `<basename>.parameters.json` | In-browser customizer manifests for every renderable above |
| `meta.json` | Project metadata: `complex_interior`, `mating_pairs` (bin↔baseplate pairs), extensive `printing_notes` (seam assembly, split/glue instructions per part) |
| `dependency-graph.md` | Auto-generated `include` dependency graph — every renderable includes `_drawer_organiser.scad` |
| `layout.md` | Full design reference: grid arithmetic, Gridfinity profile constants, interlocking-seam derivation and history (issues #304/#305/#309/#310), edge fillers, container layout and flare math, bed-splitting tables, print list |

**Key parameters** (all in `_drawer_organiser.scad`): `cell_pitch = 42`
(Gridfinity pitch); Gridfinity profile constants for the bin base pad and
baseplate socket rings (four-ring hull stacks per cell, see "Beveled
Transitions" convention below); `plate_height = 4.65`, `height_unit = 7`;
seam constants `seam_tab_neck_w = 1.6`, `seam_tab_neck_len = 0.6`,
`seam_tab_head_w = 3.6`, `seam_tab_depth = 2.0`, `seam_tab_root`,
`seam_tab_fillet`, `seam_clearance = 0.4` (barbed-tab profile, see
[Cross-project patterns](#cross-project-patterns) above); drawer
constants `drawer_bottom_w = 630`, `drawer_top_w = 670`, `drawer_height = 69`,
`drawer_grid_x = 15`, `drawer_grid_y = 10`, `container_wall_clear = 1.5`.

**Bed-splitting**: see [Cross-project patterns](#cross-project-patterns)
above for the general pattern shared with `nz-ski-fields`. `bin_part()` splits a bin
along one axis at cell boundaries; `container_part()` does the same for the
assembly-preview containers. Four of the nine seated containers — left, the
back-left and back-centre 4×6s, and back-right — exceed a 250mm print bed and
ship pre-split (the 4×6 back containers miss by only 1.5mm at 251.5mm deep);
the 5×4, 3×4, 1×3 and 1×1 fit the bed whole and have no piece files.

### esp32-display-case/

Two-part snap-fit enclosure for the ESP32-2432S028R 2.8" 240×320 resistive-touch
TFT board ("Cheap Yellow Display" / CYD), with an integrated snap-in holder for
the board's bundled touchscreen stylus. A rear shell clears the back-side
components (ESP32, USB, JST connectors) and carries two saddle clips for the
stylus on one exterior long wall; a front bezel with a display window snaps
over the shell's exterior via a skirt, sandwiching the board between them.
Both parts print upright, base-down, like `hex-connector` and `sink-tray`.

| File | Role |
|------|------|
| `_esp32_display_case.scad` | Shared library — all parameters and modules (`rbox`, `pen_clip`, `case_back`, `case_front`); no top-level geometry |
| `case_back.scad` | Renderable — rear shell with cavity, corner support posts, side-wall vents, and stylus clips |
| `case_front.scad` | Renderable — front bezel with display window and snap skirt |
| `case_back.parameters.json` | In-browser customizer manifest for `case_back` (board dims, wall, fit clearance, port margin, stylus holder toggle/dims) |
| `case_front.parameters.json` | In-browser customizer manifest for `case_front` (board dims, window size/offset, skirt clearance) |
| `meta.json` | Project metadata (description, tags: electronics/enclosure/esp32, difficulty: intermediate, hardware BOM) |
| `dependency-graph.md` | Auto-generated `include` dependency graph |

**Board dimensions are published CYD community specs, not calipered** —
flagged "VERIFY w/ calipers" in the source and exposed as customizer
parameters so a test print can confirm fit. The stylus dimensions (`pen_*`)
are measured from caliper photos (issue #268): shaft diameter 4.1mm, overall
length ~87.4mm — close enough to the PCB long edge (86.5mm) that the stylus
runs the case's full length with only minor overhang at each end.

**Stylus clip (`pen_clip`)**: a saddle clip whose axis runs along Y, with the
mouth facing +Z so the pen drops in from above (support-free print). The clip
wraps `pen_clip_grip` degrees (default 220, i.e. >180) around the shaft — the
mouth opening is narrower than the shaft's diameter, which is what retains it.
Two clips sit on the shell's `+X` exterior wall, spaced `pen_clip_span` (55mm)
apart; each sinks 0.8mm into the wall so it fuses with the shell during
rendering.

**Cavity and venting**: the interior cavity is cut from the top of the floor
(`wall` thick) up through `component_depth + pcb_thickness`. Four corner
support posts stand inside the cavity (added after the cut, flush with the
cavity walls). Each of the four exterior walls gets a through-cut vent/port
slot, retaining a thin `floor_rail` (1.2mm) at the bottom; the long (X) walls'
vent width is reduced to fit between the two stylus clip footprints when
`pen_holder` is enabled.

**Front bezel skirt**: a downward skirt (`skirt_depth`, `skirt_wall`) sized to
the shell's exterior plus `skirt_clearance` (0.3mm) slides over the rear
shell and snaps by friction fit — no separate latch geometry.

### hex-connector/

A single-piece hexagonal connector: female socket at the bottom (10mm deep) and
male protrusion at the top (10mm). 7mm across-flats, 2mm walls (outer hex = 11mm
af), 30mm total height (20mm body + 10mm protrusion). 0.3mm diametral clearance
is baked into the socket so the protrusion fits with a loose press fit. A
`tip_bevel` (0.8mm taper) on the protrusion tip guides insertion. Print
protrusion-up; no supports needed.

| File | Role |
|------|------|
| `_hex_connector.scad` | Library — parameters and `hex_connector()` module (no top-level geometry) |
| `hex_connector.scad` | Renderable — includes library, calls `hex_connector()` |
| `hex_connector.parameters.json` | In-browser customizer manifest for `hex_connector` |
| `meta.json` | Project metadata (description, tags, version, difficulty) |
| `dependency-graph.md` | Auto-generated `include` dependency graph |

**Hex geometry**: `hex_prism(r, h)` sets `$fn = 6` directly on the `cylinder()`
call and applies `rotate([0, 0, 30])` to orient flat faces at top and bottom
(standard hex orientation). All hex geometry shares this primitive.

### macbook-pro-laptop-stand/

Vertical laptop dock: two swept arch ribbons joined at end-feet, with a central
slot the closed laptop slides into edge-down. Slot floor is flat (XY face) so
the laptop's bottom edge seats level between two vertical side walls. Symmetric /
upright model; prints base-down without supports. Ships in
two variants: the original single-slot stand and a dual-slot stand that holds
two laptops side by side.

| File | Role |
|------|------|
| `laptop_stand.scad` | Renderable — parametric arch stand; profiles sampled from an existing mesh and scaled by `sx`/`sy`/`sz` factors |
| `laptop_stand.parameters.json` | Parameter manifest — exposes `slot_gap` (5–40 mm, default 18), `groove_depth`, `stand_width`, `stand_depth`, `stand_height` |
| `dual_laptop_stand.scad` | Renderable — dual-slot variant; same arch profiles, two parallel channels at ±`slot_spacing`/2 in Y |
| `dual_laptop_stand.parameters.json` | Parameter manifest — exposes `slot_gap_1` (default 18), `slot_gap_2` (default 16), `slot_spacing` (default 40), `groove_depth`, `stand_width` (240), `stand_depth` (180), `stand_height` |
| `meta.json` | Project metadata (description, tags, difficulty: intermediate, version 1.1.1, `printing_notes`: adaptive layer height over the near-horizontal arch crown, seam placement) |

**Key parameters**: `slot_gap = 18 mm` (laptop thickness + clearance); `slot_length` is always
wider than the arch so no un-slotted band remains at the shoulders. The arch profiles
(`outer_half`, `inner_half`) are sampled coordinates scaled by `sx/sy/sz` from the
reference size (240 × 150 × 100 mm). The dual variant uses `stand_depth = 180 mm`
(vs 150) so both slots fit within the depth-tapered crown with a ~23 mm divider wall.

### nz-ski-fields/

Topographic 3D terrain model of the Wakatipu and Cardrona Valley region (South
Island, NZ): a 35 km x 35 km bbox centred on (-44.97, 168.80) covering Fernhill,
Coronet Peak, Coronet Peak Flight Park, The Remarkables, and the former
Snow Park NZ site (Pisa Range). 100 mm model, 2.0x vertical exaggeration,
3 mm flat base. Ships as **three separately-printable parts** (lake / terrain /
snow) that share the same footprint and stack back into the full model.

| File | Role |
|------|------|
| `_ski_fields.scad` | Shared library — all parameters and geometry modules; no top-level geometry |
| `lake.scad` | Renderable — Lake Wakatipu insert, fills lake footprint from model bottom to water surface |
| `terrain.scad` | Renderable — lower terrain from base to snow line |
| `snow.scad` | Renderable — snow caps above `snow_line_m` |
| `assembly.scad` | Renderable — thumbnail-only preview stacking all three parts in colour (blue lake / grey terrain / white snow) via `color()`; renders from a 128px heightmap downsample so the exported STL stays small. Viewers no longer load `assembly.stl` — they instead render `lake.stl`/`terrain.stl`/`snow.stl` together as a coloured composite, per `meta.json`'s `assembly` field (see [web-viewer.md](web-viewer.md#composite-multi-colour-assembly-previews)) |
| `heightmap.png` | Committed binary asset — 512×512 8-bit grayscale heightmap (0..255 → `elev_min..elev_max` metres from `heightmap.json`) |
| `lake_bed.png` | Committed binary asset — 128×128 8-bit grayscale bathymetry map (grey 255 = bed at water surface / shore; grey 0 = full depth at model bottom) baked by `scripts/generate_lake_bed.py` |
| `heightmap_preview.png` | Committed binary asset — 128×128 downsample of `heightmap.png` (Pillow `LANCZOS`), used only by `assembly.scad` |
| `heightmap.json` | Sidecar metadata — `elev_min_m`, `elev_max_m`, `elev_range_m`, bbox params, source attribution |
| `lake.parameters.json` | Parameter manifest — exposes `lake_level_m`, `model_size_mm`, `base_thickness_mm` |
| `terrain.parameters.json` | Parameter manifest — exposes `snow_line_m`, `z_exaggeration`, `model_size_mm`, `base_thickness_mm` |
| `snow.parameters.json` | Parameter manifest — exposes `snow_line_m`, `z_exaggeration`, `model_size_mm` |
| `meta.json` | Project metadata (description, tags, difficulty, version 1.3.0, `assembly` composite descriptor) |
| `README.md` | Landmarks, multi-material split guide, lake/snow tuning, data source, regeneration commands |
| `dependency-graph.md` | Auto-generated `include` dependency graph |

**Three-part split**: The three parts exactly partition the original solid with
no overlap and no gap. `terrain.scad` = `terrain_solid` minus the lake footprint
minus everything above `snow_line_m`. `snow.scad` = `terrain_solid` intersected
with everything above `snow_line_m`. `lake.scad` = lake insert up to the water
surface. All four files — like every source in the repo — stay in OpenSCAD's
native Z-up, so the three parts remain co-registered and the thumbnail agrees
with the client-side composite.

**Composite assembly preview**: `assembly.scad` exists only to produce the
gallery thumbnail PNG — a prior version tried to ship it as a real, viewer-
loaded merged STL, but the full-resolution union was heavy enough to freeze
a CI runner (issue #272) and was too large for browsers to load on the
gallery page. The interactive viewer instead composites the three already-
printable part STLs client-side (each in its declared colour, no offset
needed since they share the same footprint and origin) — see
[web-viewer.md](web-viewer.md#composite-multi-colour-assembly-previews).

**Snow**: uses a single global elevation cut — all terrain above `snow_line_m`
(default 1300 m) is capped everywhere on the map. The valley floor stays bare;
every alpine massif above the line gets a cap. (~16% of the model lies above
1300 m.) Tuning is done by changing `snow_line_m` in `_ski_fields.scad` and
previewing with `--export-format csg`.

**Lake**: `lake_bed.png` encodes an estimated sloped basin so banks incline
believably rather than dropping straight down. The bed depth grows with distance
from the nearest shore, reaching full depth `--bank-run-mm` (default 5.5 mm)
offshore. Bbox edges count as lake-continues (deep), so only true internal
shores get the incline. The slope is shallow enough that the narrow SW neck of
the terrain stays a single connected solid at the model bottom — `lake.scad` and
`terrain.scad` interlock with no overlap.

**Important z_scale detail**: OpenSCAD's `surface()` maps an 8-bit PNG's 0..255
grey range to height 0..100 (not 0..255). The library uses `z_scale = z_mm_total / 100`
(not `/255`) so renders achieve the stated `z_exaggeration` and `elev_to_z()`
agrees with the actual surface height. Using `/255` would put the snow-line plane
above the terrain peaks, rendering the snow part empty.

When the heightmap is regenerated, update `elev_min_m` and `elev_range_m` in
`_ski_fields.scad` from the sidecar JSON, then regenerate `lake_bed.png` with
`scripts/generate_lake_bed.py` (see `README.md` for commands).

### power-workshop/

Replacement parts for the Fisher-Price Power Workshop toy. All attachments
share a common square-peg connection that plugs into the power handle.

| File | Role |
|------|------|
| `_connection.scad` | Shared library — male (shaft, collar) and female (square socket) connection modules, shared tooth profile, and all connection parameters (no top-level geometry) |
| `CONNECTION_SPEC.md` | Caliper measurements for the square-peg attachment interface |
| `drill_bit.scad` | Renderable — drill bit with spiral flutes and cog teeth |
| `drill_socket.scad` | Renderable — drill socket adapter: hollow body (2mm walls, 21.5mm ID), 24 bevel teeth, 2mm axial stand-off ring cavity at body base (`socket_boss_gap`), radial ring cavity between socket boss (16mm OD) and body inner wall, female square socket (21mm deep), internally extended collar |
| `DRILL_SOCKET_SPEC.md` | Caliper measurements for the drill socket adapter |
| `flathead_attachment.scad` | Renderable — flathead screwdriver attachment |
| `screwdriver_handle.scad` | Renderable — manual handle with square socket (female end, via shared library) |
| `test_male.scad` | Renderable — male connection only (shaft + collar), for test printing fit |
| `test_female.scad` | Renderable — female socket in a short cylinder, for test printing fit (via shared library) |
| `meta.json` | Project metadata (description, tags, version 1.1.0, difficulty: intermediate, `complex_interior: true`, `mating_pairs: [[test_male.stl, test_female.stl]]`) |
| `dependency-graph.md` | Auto-generated `include` dependency graph |
| `images/`, `Screenshot 2026-02-22 at 18.00.38.png` | Reference photos |

#### Shared Connection Pattern

`_connection.scad` defines both sides of the square-peg interface: the male
connection (shaft with snap groove, collar) and the female connection (square
socket with snap ridge). All power-workshop files that need the connection do
`include <_connection.scad>` and build their unique geometry on top.
Caliper measurements are documented in `CONNECTION_SPEC.md` alongside the
source code.

Each renderable attachment assembles as a top-level `union()` of `sq_shaft()`
+ `collar()` (provided by `_connection.scad`) plus the file's own geometry
modules (e.g., `shaft()`, `flathead_blade()`). New attachments follow this
same composition pattern and only add geometry above the collar.

#### Beveled Transitions

All connection transitions use `hull()` between thin extrusions at different
Z-heights to create smooth tapers instead of sharp 90-degree steps. This applies
to four areas:

- **Tip bevel** (`tip_bevel = 0.8`): The shaft tip starts at `groove_sq` width
  (6.3 mm) at z=0 and widens to full `shaft_sq` (8.2 mm) over 0.8 mm, creating
  a tapered lead-in that guides insertion into the female socket. This replaced
  the earlier `sq_chamfer()` conical subtraction.
- **Groove bevels** (`groove_bevel = 0.8`): Both ends of the snap groove taper
  between `shaft_sq` and `groove_sq` over 0.8 mm.
- **Collar bevel** (`collar_bevel = 2.0`): The transition from square shaft to
  round collar tapers over 2 mm using a hull from a square extrusion to a
  cylinder.
- **Corner rounding** (`corner_r = 1.0`): Male shaft cross-sections use
  `_shaft_profile()` — a rounded square produced by the `offset(r)/offset(delta)`
  technique — to match the naturally rounded corners of injection-molded originals.
  This reduces the effective diagonal so the shaft clears the female socket's
  corner-only snap ridge during insertion. The female socket intentionally
  retains sharp `square()` corners — the socket defines a subtracted void
  where sharp corners provide the clearance needed for the rounded shaft.
- **Lead-in chamfer** (`socket_lead_in = 1.2`): The socket opening tapers
  inward over 1.2 mm using `linear_extrude` with a `scale` parameter (rather
  than the `hull()` technique), reducing catching during shaft insertion.
- **Ridge bevels** (`ridge_bevel = 0.8`, in `_connection.scad`): The female
  socket's internal snap ridge uses a corner-only octagonal profile (see
  `_ridge_profile()`) — both ends taper between `socket_size` and the octagonal
  ridge over 0.8 mm. A full-perimeter ridge would create too much interference
  for rigid 3D-printed plastic (unlike the original injection-molded toy that
  flexes); the octagonal profile concentrates interference at the four corners
  only, allowing the shaft to push past with moderate force.

The `hull()` technique works by hulling two paper-thin extrusions (`0.01` mm)
at different Z positions with different cross-sections, producing a smooth
linear transition between them.

#### Drill Socket Connection Overrides

`drill_socket.scad` overrides key connection parameters for its smaller male end
(`shaft_sq=6.5mm` vs standard 8.2mm; `collar_diameter=9.5mm` vs standard 12.5mm)
and its deeper female socket (`socket_depth=21mm` vs standard 13mm;
`ridge_pos=15.35mm` vs standard 7.35mm). The `ridge_pos` override is required
because the standard value (7.35mm from the opening) lands inside the 13mm nose
bore subtraction, which erases the snap ridge entirely. At 15.35mm the ridge sits
in the body+boss zone below the nose bore and aligns with the drill bit's groove
when the bit is fully seated.
The custom `ds_shaft()` has **no snap groove and no tip bevel** — the part retains
mechanically in the drill press housing, not via snap-fit. The custom `ds_collar()`
extends the collar cylinder internally through the flange and body zones all the way
to the bevel teeth base, providing structural continuity without a separate bridging
piece. Inside the hollow body (`body_inner_d=21.5mm`, `body_wall=2mm`), a
`socket_boss_d=16mm` cylinder provides solid walls for the female square socket.
The boss starts 2mm above the flange top (`socket_boss_gap = 2`), leaving a
2mm-tall axial ring cavity at the body base (full 21.5mm inner diameter, no boss
yet) for the drill housing to seat into. Above the stand-off, the boss creates a
radial annular void between its 16mm OD and the 21.5mm body inner wall. These are
two distinct cavities: the axial stand-off gap at the base and the radial void
around the boss column.
The bore (`bore_d=4mm`) extends from the bottom face through the shaft and collar,
continuing 1.5mm above the flange base within the flange (`bore_extra=1.5`). The
collar cylinder provides solid material through this zone; the bore remains clear
of the socket (socket bottom is at z=24.5, bore top at z=21.0).

### scanning-rig/

A fully-printed photogrammetry rig for scanning small objects with a phone
camera — no bearings, bolts, or other hardware required (the issue #343
request explicitly allowed adding bearings "if needed"; the shipped design
doesn't need them). Two independent parts: a hand-rotated **turntable** (base
+ platter riding on a printed 45-degree V-groove race, held concentric by a
centring spindle) and a **generic leaning phone stand** (parametric slot
width, default sized to fit an iPhone 15 Pro bare or in a case).

| File | Role |
|------|------|
| `_scanning_rig.scad` | Shared library — `$fn = 64`, all parameters, modules `turntable_base()`, `turntable_platter()`, `stand_profile()`/`notch_profile()`/`phone_stand()`; no top-level geometry |
| `turntable_base.scad` | Renderable — base plate with V-ridge race, centring spindle, and an index pointer on the exposed rim; prints as-is, Z-up, no supports |
| `turntable_platter.scad` | Renderable — platter with underside V-groove, spindle clearance bore, rim finger-grip scallops, and numbered rotation tick marks; prints as-is, top face up (groove-side down), no supports |
| `phone_stand.scad` | Renderable — leaning phone cradle; single side profile `linear_extrude()`d along Z, print-oriented as authored (see below) |
| `rig_link.scad` | Renderable — collar + spar + low rail that ties the turntable base to the phone stand (issues #434, #468, see below); the collar bore carries two keys that lock into notches in the base rim; authored about the platter axis, not its own centroid |
| `scan_boost.scad` | Renderable — setback plinth that stands on the desk behind the rig link's rail and carries the rig's only stand pocket, set back and pitched nose-down, at its own baseline `boost_floor_h` (issues #436, #444, #468, see below) |
| `scan_riser.scad` | Renderable — optional height/angle correction that drops into the scan boost's existing pocket and re-presents an identical one `riser_h` higher, for the phone stand to drop into instead (issue #468 review, see below) |
| `scan_setback.scad` | Renderable — optional spacer that straddles the rig link's rail and presents a matching rail `setback_shift` further back, so the scan boost's own saddle grips it and the whole boost moves back (issues #465, #468, see below) |
| `scanning_rig_assembly.scad` | Renderable — preview-only assembly (platter dropped onto the base with a display-only gap, `rig_link()`, `scan_boost()` behind the rail, `scan_riser()` dropped into the boost's pocket, phone stand dropped into the riser's tilted pocket via `boost_local()`); the inner `rotate([90, 0, 0])` on `phone_stand()` stands the stand up and keeps the assembly internally Z-up-consistent. The boost is always fitted, because since #468 it is the rig's only stand mount |
| `scanning_rig_setback_assembly.scad` | Renderable — preview-only assembly, `scanning_rig_assembly.scad` with the spacer fitted and the boost/riser translated `setback_shift` further back |
| `turntable_base.parameters.json` | Customizer manifest — `base_d`, `race_r`, `spindle_d`, `foot_pads` |
| `turntable_platter.parameters.json` | Customizer manifest — `platter_d`, `race_r`, `spindle_d`, `race_clear`, `bore_clear`, `tick_count`, `numerals` |
| `phone_stand.parameters.json` | Customizer manifest — `slot_w`, `lean`, `stand_w`, `backrest_h`, `lip_h`, `foot_rear` |
| `rig_link.parameters.json` | Customizer manifest — `rail_len`, `rail_w`, `rail_h`, `stand_gap`, `base_d`, `collar_wrap`, `link_clear` (deliberately no key parameters — see below) |
| `scan_boost.parameters.json` | Customizer manifest — `boost_floor_h`, `boost_setback`, `boost_tilt`, `rail_w`, `rail_h`, `boost_clear` (deliberately no `foot_rear`/`dock_clear`/`stand_w` — see below) |
| `scan_riser.parameters.json` | Customizer manifest — `riser_h` only (deliberately no wall/kerb thickness — see below) |
| `scan_setback.parameters.json` | Customizer manifest — `setback_shift`, `setback_clear`, `rail_w`, `rail_h` |
| `meta.json` | Project metadata (description, tags: photogrammetry/scanning/utility/desk, difficulty: beginner, version 3.0.0, `mating_pairs`: `[[rig_link.stl, turntable_base.stl], [scan_boost.stl, rig_link.stl], [scan_setback.stl, rig_link.stl]]` — `scan_riser.stl` deliberately excluded, see below — `printing_notes`: support-free orientations, groove lubrication, slot-width tuning, landscape-scan overhang tip, camera centring and elevation, tick-numeral engraving depth, rig-link bed size and keyed drop-in assembly, anti-slip pad recesses, scan-boost fit/size/stability, scan-riser fit and elevation, scan-setback fit and size) |
| `dependency-graph.md` | Auto-generated `include` dependency graph — every renderable includes `_scanning_rig.scad` |

**Turntable fit**: the platter's V-groove is the ridge triangle grown by
`race_clear` (0.3mm default) on both flanks, so the pair contacts on the
45-degree flanks only, `race_clear / sqrt(2)` (~0.21mm) apart — locating the
platter concentrically without binding. `race_r` and `spindle_d` must match
between `turntable_base.scad` and `turntable_platter.scad` (both customizer
manifests expose them for that reason). `platter_t` (8mm) is deliberately
**not** exposed in the customizer: below ~6mm the groove would break through
the platter's top face. `tick_count` rotation ticks on the platter (24 =
15-degree steps, one widened as the 0-degree reference) line up against a
fixed index pointer on the base rim, so a scan can be stepped through even
angular increments by hand.

**Numbered ticks (issue #432)**: the platter rim texture — evenly-spaced
ticks and knurl — is rotationally *periodic*, so it maps onto itself when the
platter is stepped by one tick, and step-and-hold photogrammetry frames alias
against it (tooth N matches tooth N+1) instead of registering real rotation.
On real captures (issue #414) this collapsed COLMAP's sparse reconstruction: a
hold-only frame selection registered 2/47 frames, and a hybrid selection
fragmented the model into 5 pieces. Each tick `i` is now engraved with the
numeral `i + 1`, 0.5mm deep, just inside the tick band — breaking the
periodicity (every angular sector is visually unique) and letting the
operator read the current increment directly. Numerals are built from
hand-rolled 7-segment strokes (`digit_2d`/`number_2d`/`platter_numerals_2d` in
`_scanning_rig.scad`) rather than `text()`, because the deployed
openscad-wasm customizer ships no font bundle and `text()` would silently
drop the numerals from any customizer download while still rendering them in
CI's native-OpenSCAD STL (see `scripts/test_scad_fonts.py`). At a crowded
`tick_count` the ring automatically thins to every `numeral_every`-th tick so
labels don't overlap.

**Rig link (issue #434)**: `scripts/scan_masks.py` confirms one platter
ellipse against the first frame of a capture and applies it to every frame,
so the whole masking design assumes the turntable base never moves. Operator
feedback (issue #414) found that hand-turning the platter tends to drag the
238mm base a few millimetres across the desk — at 4K's ~12 px/mm, a 2-3mm
slide shifts the rim 25-35 px, silently corrupting masks for every frame
captured after the slide. `rig_link.scad` fixes this structurally by tying
the base to the phone stand so they move as one rigid assembly: if the whole
rig slides, the phone (and camera) slides with it and the ellipse stays
valid. Both ends are drop-in captures — neither `turntable_base.scad` nor
`phone_stand.scad` changes shape. The collar wraps `collar_wrap` (200
degrees by default, must stay > 180) around the base rim: past 180 degrees
the wrap gives in-plane form closure, so the base can only be lifted
straight up out of the collar, never slid out sideways, while its 160-degree
mouth (facing away from the stand) leaves the platter reachable by hand. The
link's far end is a low open-top rail (`rail_w` wide, `rail_h` tall) that the
scan boost's saddle drops over; the link carries no stand pocket of its own
(#468). `rig_link.scad` is
deliberately authored about the platter axis rather than its own centroid,
so it renders in assembled position against `turntable_base.stl` for CI's
`mating_pairs` interference check; the viewers call `geometry.center()`, so
the off-centre origin is invisible there. The link must never connect to the
platter itself — only the base and the stand — so the platter stays free to
turn by hand.

**Scan boost (issues #436, #444, #468)**: a removable plinth that stands on
the desk directly behind the rig link's rail and carries the rig's only
drop-in stand pocket, set back behind that rail (`boost_setback`), raised to
an absolute height above the desk (`boost_floor_h`) and pitched nose-down
toward the turntable (`boost_tilt`). It is located by a saddle: a cross wall
that butts the rail's rear face, fixing the camera distance, and two arms
that hug the rail's outer side walls, fixing Y and blocking yaw. Since #468
the link has no dock to fall back on, so the boost is always fitted;
`boost_setback` defaults to 26mm, measured behind the rail's rear face
(`rail_x1`) — the pocket front position feeds `cam_run0` directly (see
below), so its effect on the camera's horizontal distance is tracked there
rather than as a frozen x coordinate here. `boost_floor_h` defaulted to 45mm
pre-#486 — the pre-#468 height (old `stand_lift` 25 plus `boost_lift` 20) an
already-printed boost was built to — and is now 90mm (#486; see
`cam_rise0`/`cam_run0` below). An earlier #468 draft made this an absolute-height
elevation control and defaulted it to 150mm, but that redesigns the plinth
itself (roughly double the height, a different print entirely), obsoleting
whatever boost a user already has; a review of that draft asked to keep
reusing the existing part and add a separate piece for the elevation
correction instead — see **Scan riser** below.

An earlier version of this part plugged into a dock pocket rather than
standing on the desk, but that construction cannot be stretched to this much
setback: the loaded stand's centre of mass would land well behind the rig's
own desk footprint, and the plug's few millimetres of engagement cannot
resist that tipping couple — it would rock back and lift out. Reaching the
desk from behind the link also makes any downward-facing plug an unprintable
floating island once the print's lowest plane becomes the desk instead of the
plug's underside. So the boost stands on the desk on its own footprint,
located rather than loaded by the saddle. `boost_setback` is now measured
from the rail's rear face, which is also where the plinth's own front face
lands, so its only floor is `boost_clear + boost_wall` (~3.35mm at the
defaults) and the manifest can start it at 10mm. `pocket_x`/`pocket_y` are
still sized by `foot_rear`, `stand_w` and `dock_clear`, none of which the
boost's manifest exposes — deliberate, and worth keeping that way, since a
customized pocket that no longer matches the printed stand is a silent trap
rather than an assert.

The hollow core narrows through a corbelled ledge (the same trick
the dock used) to a tilted pocket that takes the phone stand's foot. The
corbel is cut in the pocket's tilted frame, so its inset and rise are not
equal the way an untilted corbel's would be: insetting `boost_ledge` over
an equal rise would be 45 degrees locally but `45 + boost_tilt` from vertical
globally — a 65-degree overhang inside a closed cavity at the default tilt.
The rise is stretched to `boost_ledge * tan(45 + boost_tilt)`
(`boost_corbel_rise`) instead, which lands the cavity's rear face at exactly
45 degrees off the print bed at any tilt. For the same reason the core's
lower hull starts no further forward than a 45-degree run down from the
corbel's front lip (`boost_core_x0`): at large setbacks the plinth outruns
the pocket, and the nose is left solid rather than roofed by a near-flat
ceiling. At the shipped defaults that clamp is inactive (`boost_lip_x -
boost_lip_z` = 181.4mm, well forward of `boost_core_x0` = 229.85mm), so the
plinth stays a shell — the margin is about 48.5mm at the shipped 90mm default
and shrinks as `boost_floor_h` decreases, because a lower floor pulls
`boost_lip_z` up toward `boost_core_x0`; drop `boost_floor_h` toward the
manifest's 25mm floor and the clamp goes active. Gravity settles the tilted
foot against the pocket's downhill (front) kerb wall, with the fore-aft slack
landing at the rear. The boost must never link to the platter — only to the
rig link's rail and the phone stand's foot — so the platter stays free to
turn.

**Scan riser (issue #468 review)**: a #468 draft made the scan boost's own
`boost_floor_h` the camera-elevation control and defaulted it to 150mm to
clear the `ry/rx >= 0.64` floor (see below) — but that redesigns the plinth
itself, and a reviewer asked to keep reusing whatever boost is already
printed rather than obsolete it. The riser is a second, separate piece that
does the elevation correction instead: it drops into the boost's *existing*
foot pocket, in exactly the footprint and at exactly the fit the phone
stand's own foot has there today (same `dock_clear` per side, same 1mm proud
of a kerb), and re-presents an identical pocket `riser_h` further up — the
phone stand then drops into the riser's pocket instead of the boost's. The
boost does not change shape at all.

Unlike `boost_floor_h`, which is a pure vertical lift, `riser_h` is measured
along `boost_local()`'s already-tilted local Z, so it also pulls the camera
slightly closer to the turntable as it rises (`riser_h * sin(boost_tilt)`)
while lifting it (`riser_h * cos(boost_tilt)`) — `riser_checks()` echoes the
combined prediction, factoring both terms in, alongside `boost_checks()`'s
boost-alone figure. The riser is solid apart from its own top pocket, unlike
the boost's shelled, corbelled plinth: shelling it the same way would need a
floor plate roofing its own cavity over the tower's full footprint with
nothing under it — an unsupported bridge, not a corbel, since (unlike the
boost's core, which stays open all the way down to the desk) the riser's
cavity would be fully enclosed. Slicer infill settings, not this source
model, are what actually control how much plastic a solid region prints
with. It is authored in its own flat frame rather than `boost_local()`'s
tilted one — the boost's pocket floor is already flat *within* that tilted
frame, the same reason the phone stand's foot drops in flush today, so a
flat-bottomed riser seats against it at any `boost_tilt` and still prints
upright rather than at `boost_tilt` off the bed. `scan_riser.stl` is
deliberately absent from `meta.json`'s `mating_pairs`, for the same reason
`phone_stand.stl` is: both are authored in their own local frame rather than
the rig's shared assembly frame, so CI's interference check — which compares
mating STLs as exported, assuming a shared frame — cannot check them.

**Scan setback spacer (issues #465, #486)**: framing tests at the boost's
120mm setback originally showed the (then) 150mm platter spanning ~77% of a
4K portrait frame with the base plate clipped at both edges, and a tube-sized
object touching the frame edge at some rotation angles. The setback spacer is
a piece that inserts between the rig link's rail and the boost: it straddles
that rail the same way the boost's own saddle does, and re-presents an
identical rail (`rail_w` wide, `rail_h` tall) `setback_shift` further back, so
the boost's existing saddle grips the spacer's rail instead of the link's,
unchanged. Dropping the boost onto the spacer therefore moves the whole
boost — and the camera — rearward by exactly `setback_shift` at unchanged
height and pitch. At the 222mm platter (#486) `setback_shift` defaults to
135mm and is no longer optional equipment — see **Bed-limited sizing** and
**Framing is a constraint, not a comment** below. The spacer carries no load
of its own — the rig link and the boost both stand on the desk under their
own weight — its only jobs are fixing the boost's distance with a hard butt
joint at the rail's rear wall, and keeping the boost coupled to the link so
the whole rig still slides as one rigid body and `scan_masks.py`'s single
fixed platter ellipse (issue #434) stays valid.

**Anti-rotation keys, low rail, and camera elevation (issue #468)**: three
defects reported from real use.

The collar was a plain 200-degree arc around a plain cylindrical rim, so
although the base could not be *lifted* or *slid* out, it was free to *spin*
inside the collar. Hand-turning the platter twists the base with it, which
swings the index pointer off the rig axis and rotates the base annulus that
`scan_masks.py`'s fixed ellipse assumes is static. The base rim now carries
two notches and the collar bore two matching ribs, both derived from the same
`key_angle`/`key_w`/`key_depth`/`key_clear` variables in `_scanning_rig.scad`
and exposed in *neither* customizer manifest, so the two halves cannot drift
apart. They sit at ±60 degrees off +X, well inside the collar's wrap and
clear of the index pointer at 0 degrees; the rib is `key_clear` (0.35mm)
narrower than the notch on each tangential face and `link_clear` (0.4mm)
outboard of the notch floor radially. Because the notches are prisms through
the full plate thickness, the base still lifts straight out. The keys line up
at exactly one rotation, which is also the rotation that puts the pointer on
the rig axis, so the assembly is self-indexing. `link_checks()` asserts that
the keys stay inside the collar's wrap and that the notch floor stays outside
the platter rim.

The link's stand dock — a 97 x 87 x 30mm hollow plinth — is replaced by
`rig_rail()`, a 40mm-wide, 12mm-tall open-top channel. The dock's pocket was
never used: since #444 the stand always mounts on the scan boost, so the dock
was carrying a 30mm-tall empty box through the near field of every capture.
`rail_len` is 97mm precisely so the rail's rear face stays at x = 226.5mm,
where the dock's was — that face is the boost's stop, so the camera's
horizontal distance is unchanged. The rail is open-topped so nothing bridges;
do not close it with a lid. One accepted consequence: the boost's and
spacer's saddle engagement drops from 30mm to `rail_h` (12mm). Yaw is still
blocked by `boost_grip` (40mm) against `boost_clear` and the desk still
carries the load, so the rail only locates — but the boost does lift off it
more easily than before.

Camera elevation had collapsed to ~21 degrees once the #465 spacer was
fitted, and that turned out to break scans outright rather than merely soften
them. On a step-and-hold capture of uniform-grey pliers (verified ellipse
`1095,1531,820,300`, inked platter numerals), `--capture-mode continuous`
registered 18 of 150 frames and fragmented into 7 models, and
`--capture-mode holds` registered 2 of 54 — the pre-numeral aliasing
signature. Near edge-on the platter's numerals foreshorten to nothing,
leaving only the rotationally-periodic knurl to match against. A
feature-rich object survives this (a toothpaste tube scanned 150/150 in the
same session); a plain one does not. So `ry/rx >= 0.64` is a hard floor the
shipped defaults must *land* at, not a range they must merely allow.

The rig's own dimensions give a calibrated model. With the phone's rear
camera `cam_z_lead` (96mm) up the backrest's inner face and `cam_x_lead`
(6mm) behind the boost's pocket front, the camera sits `cam_rise0 =
boost_floor_h + cam_z_lead - base_t - platter_t` mm above a platter top 14mm
above the desk (`base_t + platter_t` is unchanged at 6 + 8), and `cam_run0 +
setback_shift` mm out from the platter axis (`cam_run0 = boost_x0 +
cam_x_lead`) — for the boost alone, with no riser fitted, `setback_shift = 0`.
At the shipped `boost_floor_h = 90`, `cam_rise0` is 172mm and `cam_run0` is
258.5mm, giving `atan(172/258.5)` = 33.6 degrees, `ry/rx` 0.554. Both
`cam_run0` and `cam_rise0` are declared right after `boost_x0` in
`_scanning_rig.scad` precisely so a change to `boost_x0` or `boost_floor_h`
propagates automatically — the pre-#486 version of this model froze the
run at a literal `222.4`, which is exactly the staleness that let the #486
platter scale-up outgrow the frame silently (see **Framing is a constraint,
not a comment** below).

The riser adds `riser_h` along `boost_local()`'s tilted local Z rather than a
plain vertical lift, so it changes both terms: height gains
`riser_h * cos(boost_tilt)` and distance loses `riser_h * sin(boost_tilt)` —
`elevation = atan((cam_rise0 + riser_h * cos(boost_tilt)) /
(cam_run0 + setback_shift - riser_h * sin(boost_tilt)))`, echoed by
`riser_checks()` alongside `boost_checks()`'s boost-alone figure, both now
also echoing `cam_frame_frac()` — the fraction of frame width the platter
fills.

| Config | `riser_h` | distance | slant range | elevation | `ry/rx` | platter/frame |
|---|---|---|---|---|---|---|
| boost alone, no spacer, no riser | — | 258.5 | 310.5mm | 33.6° | 0.554 | 94% |
| boost + riser (new default) | 140 | 210.6 | 369.5mm | 55.2° | **0.822** | 79% |
| boost + riser + spacer @ 135 (shipped) | 140 | 345.6 | 460.0mm | 41.3° | **0.660** | 63% |
| boost + riser + spacer @ 150 (manifest max) | 140 | 360.6 | 471.4mm | 40.1° | 0.644 | 62% |

Boost alone, with no riser, sits under the 0.64 floor at any setback — the
riser is not optional equipment for a usable capture. `riser_h` (40-170mm) is
the elevation control the customizer exposes, default 140; `boost_floor_h`
(25-110mm, default 90) is the plinth's own baseline height. The 300mm-ish
total camera height the 222mm platter needs is deliberately split between
these two rather than put entirely into one part: a riser tall enough to do
the whole job alone would be roughly 200mm on a 96mm x 86mm footprint — an
increasingly top-heavy tower for that footprint, more easily knocked
mid-capture — whereas spreading the height into the wide, desk-borne
`scan_boost` plinth as well keeps `riser_h` inside its existing manifest
ceiling.

`setback_shift` defaults to 135mm and, at the 222mm platter, is mandatory
rather than optional: without it boost + riser alone fills 79% of the frame
width, an object cannot clear the frame edge through a full rotation, and
`ry/rx` (0.822) is well past the point where headroom to spare stops
mattering — the platter itself, not the ring, becomes the binding constraint.
With the spacer at 135mm the platter fills 63% of the frame — parity with
what the 150mm platter had pre-#486 — at `ry/rx` 0.660, still comfortably
above the 0.64 floor. `boost_checks()` and `riser_checks()` both `echo()`
their predicted elevation, `ry/rx` and frame fraction at render time, so a
customizer download or a CI log says what geometry was actually asked for.
The model is fitted to a single measured ellipse, so treat the echoes as
predictions and confirm against a fresh `roi-preview.jpg`; if they land well
off, the `cam_z_lead`/`cam_x_lead` camera-position assumptions are the terms
to re-fit.

**Bed-limited sizing (issue #486)**: the platter and base are sized to the
largest turntable that fits a 250mm bed, not to any margin above it. The
constraint chain, in order: `rig_link`'s collar OD is `base_d + 2 *
link_clear + 2 * collar_wall`, which must clear the 250mm print bed —
238 + 2(0.5) + 2(4) = 247.0mm at the shipped `base_d`. The link's actual
footprint is slightly larger still once the rail and collar mouth are
accounted for: 247.95 x 246.88mm, measured on the exported STL, leaving
about 4mm clearance per side on a Bambu Lab A1's 256 x 256mm plate — no
skirt, brim, or slicer exclusion margin fits inside that. The base rim must
also stay 8mm proud of the platter for the index pointer, which spans
`base_d/2 - 2` to `base_d/2 - 7`; at `base_d = 238` that is 117 down to
112mm, so `platter_d` must be 222mm, not simply `base_d - 12`. Every other
turntable dimension (`race_r`, `race_clear`, `spindle_d`, `grip_flutes`,
`foot_pad_r`, `key_w`, `key_depth`, `link_clear`, the numeral parameters) is
derived from or scaled alongside those two, and is exercised in
`_scanning_rig.scad`'s own `link_checks()`/`boost_checks()`/`riser_checks()`
asserts rather than left to informal proportion.

**Framing is a constraint, not a comment**: before #486, the relationship
between platter size and frame width existed only as prose in this file and
in `playbooks/scan_a_capture.md` — nothing in `_scanning_rig.scad` itself
would have failed loudly if a platter scale-up outgrew the camera's field of
view, which is exactly what a first draft of the #486 scale-up did (the
222mm platter at the pre-#486 camera geometry framed at 82%, worse than the
77% that motivated creating the setback spacer in the first place).
`_scanning_rig.scad` now declares `cam_fov_tan = 0.3803` — half the
tangent of a 4K portrait phone camera's horizontal field of view, back-solved
from the #465 measurement of the 150mm platter filling ~77% of frame at a
256mm boost-alone slant — and a `cam_frame_frac(rise, run)` function that
divides `platter_d` by twice the tangent-scaled slant. Both `boost_checks()`
and `riser_checks()` echo the result at render time. Treat ~0.60 as the
threshold: below it, the platter has margin to spare inside the frame at
every rotation angle; approaching or exceeding it (as boost + riser alone
does, at 79%, or as an under-sized setback would) risks the platter or an
overhanging object clipping the frame edge partway through a revolution. Fit
or extend the setback spacer whenever `cam_frame_frac()` reads above ~0.60.

**Phone stand profile**: `stand_profile()` draws the side view in XY with
+Y up and +X rearward (the lean direction), then `phone_stand()` extrudes it
along Z (`stand_w`, the stand's width) — so every layer of the print is the
identical cross-section and no part of the wedge/lip/backrest can overhang
regardless of `lean`. Because the profile's "up" is already +Y, the exported
STL is print-oriented (flat face on the bed) and already reads upright once
the viewers apply their Z-up→Y-up conversion (see
[OVERVIEW.md](OVERVIEW.md#viewer-rotation)) — a pattern worth reusing for
future single-profile extruded parts. The cradle floor is carried above the
foot plate by a `hull()`-based wedge (tilted floor strip to a shallow strip
sunk into the foot) rather than being sunk into the foot directly, so the
tilted floor stays supported across its full width at any `lean`. A cable
notch is cut through the lip and floor in the slot's own tipped-back frame;
its deepest point is bounded (`stand_base_t - 1 + 4*sin(lean) - 0.5*cos(lean)`)
to stay well clear of severing the foot plate across the customizer's `lean`
range.

### sink-tray/

| File | Role |
|------|------|
| `tray_foot.scad` | Renderable — cylindrical foot with counterbore for screw attachment |
| `tray_foot.parameters.json` | In-browser customizer manifest for `tray_foot` |
| `meta.json` | Project metadata (description, tags, difficulty) |
| `IMG_2843.jpg`, `IMG_2844.jpg` | Reference photos |

### toothbrush/

Multi-part toothbrush and toothpaste holder system with a solid base,
vertical backplate, dovetail-attached clips, and a removable drip tray.

| File | Role |
|------|------|
| `_toothbrush_holder.scad` | Shared library — all modules and parameters for the holder system (no top-level geometry) |
| `Toothbrush holder.scad` | Renderable — full holder assembly in native Z-up |
| `Toothbrush tray.scad` | Renderable — drip tray with alignment grooves; also `use`d by `Toothbrush assembly.scad` as a module |
| `Toothbrush assembly.scad` | Renderable — assembly preview (holder + tray) |
| `Toothbrush backplate.scad` | Renderable — backplate with dovetail rails; the sole file in the repo keeping a top-level `rotate([-90, 0, 0])`, and it is a *print* orientation: `toothbrush_backplate()` stands upright in the library and this lays it on its back, flat on the bed (allowlisted in `scripts/test_scad_orientation.py`) |
| `Toothbrush clip test.scad` | Renderable — single brush clip, oriented for test printing |
| `Toothpaste clip.scad` | Renderable — single paste clip, oriented for test printing |
| `Toothpaste hanger.scad` | Renderable — cap-up paste hanger (backing block + two-prong cap-neck fork), oriented for test printing; mounts on the same rail as `Toothpaste clip.scad` |
| `Toothpaste hanger.parameters.json` | In-browser customizer manifest for `Toothpaste hanger` |
| `meta.json` | Project metadata (description, tags, difficulty) |
| `dependency-graph.md` | Auto-generated `include`/`use` dependency graph |

**Key parameters**: `Toothbrush tray.scad` carries two `head_peg()` posts and
two `support_spike()` posts (module names changed in issue #388;
`head_spike()` no longer exists). The head pegs are an 8 mm shaft
(`head_peg_d`), 30 mm tall total (`head_peg_height`), tapering over the top
10 mm (`head_peg_taper`) to a flat 6 mm-diameter tip (`head_peg_tip_d`, a
3 mm radius per PR #389 review, not a sharp point), with a 1.5 mm flare at
the base (`head_peg_flare`); they park a detached brush head upright while
it dries (issue #371) and sit at tray-local `(±head_peg_x, head_peg_y)` = `(±36,
26)`, the tray's front inner corners, inset by `head_r` (11 mm, the parked
head's own base radius — the controlling clearance, larger than the peg's
own flare radius) plus `head_peg_gap` (1 mm) so the parked head clears the
corner fillet and side walls. They were moved there in issue #388 so a
parked head can't clash with the brushes hanging in the clips. The two `support_spike()` posts keep the
unchanged 4 mm → 3 mm domed profile but are now 30 mm tall (`spike_height`,
10 mm taller, issue #388), still at `x = ±brush_spike_spacing/2` (=
`±grip_spacing/2`, exactly under the clip axes, the same X as the alignment
grooves) and `y = brush_spike_y` (−6.2 mm), acting as standoffs so a parked
toothbrush rests on a point rather than in standing water (issue #374). The
clip bore axis is at tray-local `y = −3.5`; `brush_spike_y` is pulled 2.7 mm
behind it so the flared base clears the groove footprint (`y ∈ [−2.2, 2.2]`)
— no post ever stands on the ~1.5 mm of floor above a groove. The tray is
100 × 65 × 10 mm and grows forward only (issue #377): the base and its
alignment pegs are already printed, so `base_depth` (55 mm) and `peg_y`
(30 mm) are unchanged and `tray_shift_y` (7.5 mm) offsets the shell from the
tray's local origin, which stays on the peg line. The grooves and `Toothbrush
assembly.scad`'s placement are therefore unaffected, at the cost of the
tray's front 15 mm overhanging the base's front edge. The cap-up toothpaste
hanger (`paste_hanger_piece()`, issue #476) defaults `cap_neck_d` to 27.4 mm
and `cap_flange_d` to 33.7 mm, the caliper-measured narrowest and widest
sections of the cap (issue #484), plus `prong_t` at 4 mm — all three exposed
in the customizer. `fork_z_axis` is derived from `fork_web + neck_slot_w / 2`
rather than hard-coded, so the cap's flange always clears the arm face
regardless of the `cap_neck_d` the customizer is set to. `mouth_flare` is
likewise derived, as `max(0, min(3, (cap_flange_d - neck_slot_w)/2 -
flange_bearing))`, so the insertion funnel can never open wider than the
flange — a fixed flare would otherwise let the cap drop straight through
instead of being guided into the slot. The `scans/toothpaste` reference mesh
is deliberately not imported —
it is a convex hull contaminated with platter geometry out to the capture's
85 mm crop radius, so it cannot supply the cap's neck waist (a concavity a
hull can't carry) and would only be usable as clearance geometry, not as a
`difference()` operand for the fork.

**Rejected: reworking the clips themselves to grip the brush.** Issue #371
also asked for a fix to the clips sliding brushes to the ground, and PR #373
initially added a `brush_rest_shelf()` module — a C-shaped shelf across the
bottom of each clip's bore with a drain hole — as a way to make the clip
itself hold the brush. The owner rejected this mid-PR and had it reverted:
"Keep the spikes on the tray but revert the changes to the toothbrush grips.
That approach won't work." There is no `brush_rest_shelf` module in the repo
today. The standing fix for "toothbrush falls out of / slides down the
clips" is standoff spikes on the tray floor (above), not a modification to
`c_clip()` or `brush_clip_piece()` — don't re-propose clip-side gripping
geometry on the strength of #371 alone.

See [OVERVIEW.md](OVERVIEW.md#dovetail-joint-system-toothbrush) for the
dovetail joint system used between the backplate and clips.

### ukulele-wall-hook/

Single-piece wall-mounted yoke that cradles a ukulele neck behind the
headstock. A rounded mounting plate (50×70×8mm, two counterbored screw holes
for #8/4-5mm wall screws) carries two capsule-section prongs that project
forward and curl upward, forming an upward-opening cradle. Authored
plate-upright (plate tall in +Z, prongs projecting in +Y) — an "upright"
model like `hex-connector`/`sink-tray`.

| File | Role |
|------|------|
| `ukulele_hook.scad` | Renderable — single file, no library split, no inter-file dependencies (no `dependency-graph.md`, same as `sink-tray`) |
| `ukulele_hook.parameters.json` | In-browser customizer manifest (`plate_w`, `plate_h`, `prong_len`, `screw_spacing`, `root_r`) |
| `meta.json` | Project metadata (description, tags: household/organizer/wall-mount, difficulty: beginner, hardware BOM: 2 wall screws, `printing_notes`) |

**Key parameters**: `tip_gap` (56mm, center-to-center of prong tips) sets the
neck-cradle clear width (`tip_gap - 2*prong_r` = 42mm). A ukulele neck narrows
to ~36mm at the nut (confirmed via PR #294 review comment), so `tip_gap` is
kept several mm above that so the neck drops in without binding. The prong
root is flared (`root_r = 9.5` tapering to `prong_r = 7` over `flare_len = 20`
mm along the prong axis) because a constant-radius capsule met the plate in a
sharp corner and one arm snapped there (issue #390); `prong_root_y` is
derived as `root_r + 0.5` so the root sphere's back pole never crosses the
Y=0 wall face at any customizer value; `root_r` above 10 pushes the root past
the plate outline at the default `plate_w = 50`; and screw holes are
differenced from the whole part so a flare can never fill a counterbore.

### vacuum-hose/

Vacuum hose fittings for workshop dust collection. Two models share this
directory: an adapter and a reducer.

| File | Role |
|------|------|
| `adapter.scad` | Renderable — male-to-male adapter joining 50mm OD hose to 35mm OD hose; 2mm tip taper over 10mm aids insertion |
| `reducer.scad` | Renderable — reducer connecting 49mm OD hose to 30mm ID hose; tapered ends for snug fit |
| `adapter.parameters.json` | In-browser customizer manifest for `adapter` |
| `reducer.parameters.json` | In-browser customizer manifest for `reducer` |
| `meta.json` | Project metadata (description, tags, difficulty, version) |

Both files share the same helper/module structure: `disc(d, h=0.01)` (thin
cylinder used as hull anchor), `taper_segment(d1, d2, z1, z2)` (hull of two
discs at different Z-heights), `outer_shell()` and `inner_bore()` (each a union
of taper segments). The assembly uses `difference() { outer_shell(); translate([0, 0, -0.1]) inner_bore(); }` — the `-0.1` extends the bore past the near face and the far-end inner bore adds `+0.1` beyond the last breakpoint, ensuring clean boolean cuts at both end faces (standard OpenSCAD technique to avoid Z-fighting at coplanar faces).
