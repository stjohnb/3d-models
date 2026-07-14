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

### esp32-display-case/

Two-part snap-fit enclosure for the ESP32-2432S028R 2.8" 240×320 resistive-touch
TFT board ("Cheap Yellow Display" / CYD), with an integrated snap-in holder for
the board's bundled touchscreen stylus. A rear shell clears the back-side
components (ESP32, USB, JST connectors) and carries two saddle clips for the
stylus on one exterior long wall; a front bezel with a display window snaps
over the shell's exterior via a skirt, sandwiching the board between them.
Both parts print upright (Z-up) with no viewer rotation — symmetric/upright
model, like `hex-connector` and `sink-tray`.

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
upright model — no viewer rotation; prints base-down without supports.

| File | Role |
|------|------|
| `laptop_stand.scad` | Renderable — parametric arch stand; profiles sampled from an existing mesh and scaled by `sx`/`sy`/`sz` factors |
| `laptop_stand.parameters.json` | Parameter manifest — exposes `slot_gap` (5–40 mm, default 18), `groove_depth`, `stand_width`, `stand_depth`, `stand_height` |
| `meta.json` | Project metadata (description, tags, difficulty: intermediate, version 1.0.0) |

**Key parameters**: `slot_gap = 18 mm` (laptop thickness + clearance); `slot_length` is always
wider than the arch so no un-slotted band remains at the shoulders. The arch profiles
(`outer_half`, `inner_half`) are sampled coordinates scaled by `sx/sy/sz` from the
reference size (240 × 150 × 100 mm).

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
| `lake.scad` | Renderable — Lake Wakatipu insert, fills lake footprint from model bottom to water surface; applies `rotate([-90, 0, 0])` for the web viewer |
| `terrain.scad` | Renderable — lower terrain from base to snow line; applies `rotate([-90, 0, 0])` for the web viewer |
| `snow.scad` | Renderable — snow caps above `snow_line_m`; applies `rotate([-90, 0, 0])` for the web viewer |
| `assembly.scad` | Renderable — thumbnail-only preview stacking all three parts in colour (blue lake / grey terrain / white snow) via `color()`; renders Z-up (no viewer rotation, unlike the parts above) from a 128px heightmap downsample so the exported STL stays small. Viewers no longer load `assembly.stl` — they instead render `lake.stl`/`terrain.stl`/`snow.stl` together as a coloured composite, per `meta.json`'s `assembly` field (see [web-viewer.md](web-viewer.md#composite-multi-colour-assembly-previews)) |
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
surface. All three apply `rotate([-90, 0, 0])` at the top level.

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
| `meta.json` | Project metadata (description, tags, difficulty) |
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
| `Toothbrush holder.scad` | Renderable — full holder assembly, oriented for web viewer |
| `Toothbrush tray.scad` | Renderable — drip tray with alignment grooves; also `use`d by `Toothbrush assembly.scad` as a module |
| `Toothbrush assembly.scad` | Renderable — assembly preview (holder + tray) |
| `Toothbrush backplate.scad` | Renderable — backplate with dovetail rails, oriented for printing |
| `Toothbrush clip test.scad` | Renderable — single brush clip, oriented for test printing |
| `Toothpaste clip test.scad` | Renderable — single paste clip, oriented for test printing |
| `meta.json` | Project metadata (description, tags, difficulty) |
| `dependency-graph.md` | Auto-generated `include`/`use` dependency graph |

See [OVERVIEW.md](OVERVIEW.md#dovetail-joint-system-toothbrush) for the
dovetail joint system used between the backplate and clips.

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
