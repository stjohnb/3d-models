# Model Projects

Detailed per-project reference: files, geometry conventions, and key
parameters for every model directory. See [OVERVIEW.md](OVERVIEW.md) for
repository-wide architecture and patterns.

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
[OVERVIEW.md](OVERVIEW.md#interlocking-tile-seams-drawer-organiser)); drawer
constants `drawer_bottom_w = 630`, `drawer_top_w = 670`, `drawer_height = 69`,
`drawer_grid_x = 15`, `drawer_grid_y = 10`, `container_wall_clear = 1.5`.

**Bed-splitting**: see
[OVERVIEW.md](OVERVIEW.md#bed-splitting-pattern-for-oversized-parts-nz-ski-fields-drawer-organiser)
for the general pattern shared with `nz-ski-fields`. `bin_part()` splits a bin
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
| `turntable_platter.scad` | Renderable — platter with underside V-groove, spindle clearance bore, rim finger-grip scallops, and rotation tick marks; prints as-is, top face up (groove-side down), no supports |
| `phone_stand.scad` | Renderable — leaning phone cradle; single side profile `linear_extrude()`d along Z, print-oriented as authored (see below) |
| `scanning_rig_assembly.scad` | Renderable — preview-only assembly (platter dropped onto the base with a display-only gap, phone stand alongside); the inner `rotate([90, 0, 0])` on `phone_stand()` stands the stand up and keeps the assembly internally Z-up-consistent |
| `turntable_base.parameters.json` | Customizer manifest — `base_d`, `race_r`, `spindle_d` |
| `turntable_platter.parameters.json` | Customizer manifest — `platter_d`, `race_r`, `spindle_d`, `race_clear`, `bore_clear`, `tick_count` |
| `phone_stand.parameters.json` | Customizer manifest — `slot_w`, `lean`, `stand_w`, `backrest_h`, `lip_h`, `foot_rear` |
| `meta.json` | Project metadata (description, tags: photogrammetry/scanning/utility/desk, difficulty: beginner, version 1.0.0, `printing_notes`: support-free orientations, groove lubrication, slot-width tuning, landscape-scan overhang tip) |
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
| `Toothpaste clip test.scad` | Renderable — single paste clip, oriented for test printing |
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
tray's front 15 mm overhanging the base's front edge.

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
| `ukulele_hook.scad` | Renderable — single file, no library split, no inter-file dependencies (no `dependency-graph.md`, same as `sink-tray`/`hex-connector`) |
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
