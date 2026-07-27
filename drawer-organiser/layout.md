# Drawer layout

## Drawer measurements (from issue #298)

| Dimension | Value |
|---|---|
| Width at the bottom | 628 mm |
| Width at the top | 669–670 mm (the sides flare outward; remeasured in issue #326 — an earlier 665 mm reading was low). The model uses 670 mm. |
| Depth | 424 mm |
| Height (bottom to top) | 69 mm |

Three 210 mm tiles (630 mm) were confirmed to fit the drawer floor in issue
#315, so the model uses **630 mm** as the effective floor width; the 628 mm
figure above was a conservative measurement.

The organiser is sized against the **bottom** width, because the baseplate sits
on the drawer floor. The flare to ~670 mm at the top only adds clearance above
the plate, so it does not constrain anything.

## Grid

Gridfinity's cell pitch is 42 mm.

- Across: the floor takes **15** cells → 630 mm
- Deep: `floor(424 / 42) = 10` cells → 420 mm

A **15 × 10 grid (630 × 420 mm)** covers the floor, with **no width slack** and
4 mm of depth slack (2 mm per side).

> The 420 mm depth assumes 424 mm is the **internal** measurement. If 424 mm is
> an outside measurement, 10 rows will not fit — drop to 9 rows (378 mm), which
> needs 4-row tiles. This project does not ship those as files; set `grid_y = 4`
> in the customizer.

## Tiling the baseplate

630 mm cannot be printed in one piece on an A1 (250 × 250 mm usable), so the
baseplate is tiled **3 columns × 2 rows**:

- Columns of 5, 5 and 5 cells across → 210 × 3 = 630 mm
- Rows of 5 and 5 cells deep → 210 + 210 mm = 420 mm

Tiles have **no margin** around their outer footprint — a 5 × 5 tile is exactly
210 × 210 mm — so they butt together and the 42 mm pitch continues unbroken
across the seams. The top edge of the perimeter feathers to nothing; that is
correct Gridfinity behaviour, not a defect.

## Interlocking tile seams

The tiles interlock with **genderless barbed tabs**, so there is no male/female
variant to keep track of — every tile mates with every other tile of the same
edge length. Each tile carries tabs on its +X and +Y edges and the matching
notches on -X and -Y.

| Feature | Value (nominal) |
|---|---|
| Neck width at the seam | 1.6 mm |
| Seam line → shoulder | 0.6 mm |
| Head width | 3.6 mm |
| Seam line → tab tip | 2.0 mm |
| Clearance across a seam | 0.4 mm total (0.2 mm per side) |
| Tab protrusion past the seam | 1.8 mm |
| Retention per side | 0.6 mm |

Tabs sit at the **centre of each cell** along an edge, not on the junctions
between cells. That matters more than it sounds — see below. The mated tab head
is 3.2 mm wide and the notch throat is 2.0 mm, so 0.6 mm of shoulder per side
holds the seam closed; the engagement runs from the plate's underside up to
about z = 3.8 mm of its 4.65 mm thickness.

The tile footprint stays exactly `gx × 42` by `gy × 42` mm — the clearance is
applied to the tab and notch **features only**, never to the tile outline. If
the outline were shrunk instead, the 42 mm pitch would drift by 0.4 mm at every
seam, which exceeds the 0.25 mm pad-to-socket clearance, and a bin spanning two
tiles would stop seating.

### Assembly: lower each tile in, don't press it

The barb's shoulder is perpendicular to the seam, which is what stops a loaded
seam from wedging itself open — but it also means two tiles **cannot** be
pressed together in the plane of the plate. Instead, hold the new tile above the
plane and lower it onto its already-placed neighbours so its tabs drop straight
down into their slots. The notch is cut with a prism running the full height of
the plate while the tab is trimmed by the sockets, so the tab's cross-section
fits the slot at every height and the tile slides in cleanly.

### Why not on the cell junctions (issue #309)

The first version of this seam put a round jigsaw tab on each cell junction, on
the reasoning that the junction carries the thickest run of material. It does —
but that material is a 4.3 mm rib, and it is also the *only* thing joining the
perimeter rail to the rest of the plate. A notch big enough to hold a jigsaw
head (5.9 mm across) cut straight through it, and the printed tiles came off the
bed with the entire perimeter rail hanging off the four corners.

At a cell centre the rail is instead backed by material running the full length
of the edge, so a notch takes a slot out of the rail and leaves it attached at
the junctions either side. The trade is depth: there the rail is only
`4 − sock_r` deep — 2.15 mm through the socket's straight section — so the tab
has about 2 mm to work in. That rules out a round head (a circle tangent to the
seam has almost no undercut) and a dovetail (its angled face cams out under
load), which is why the profile is a barb.

### Depth budget

A tab protrudes 1.8 mm beyond the nominal footprint. Where two tiles mate that
costs nothing, because the tab sits inside its neighbour's notch. It only shows
up at the **outer** edges of the assembly:

- **Depth:** `420 + 1.8 = 421.8 mm`, inside 424 mm.
- **Width:** `630 + 1.8 = 631.8 mm`, against a floor width of 630 mm. Unlike the
  depth, this is a real fit consideration rather than a comfortable margin: the
  right-hand tile column's outboard +X tabs mate with nothing, so if the drawer
  is tight, clip them flush with side cutters.

Both fit, so the `_back` tiles — which omit the +Y tabs — are no longer required
the way they were when tabs protruded 5.55 mm. They are still worth printing for
the rear row: the tabs there mate with nothing, and omitting them keeps the
assembly exactly 420 mm deep and its back edge flat against the drawer.

The -X and -Y edges of the assembly carry notches, which cut inward and add
nothing to the overall size.

### Tiles

| Tile | Cells | Size | Row | Quantity |
|---|---|---|---|---|
| `drawer_baseplate_5x5.scad` | 5 × 5 | 210 × 210 mm | front | 3 |
| `drawer_baseplate_5x5_back.scad` | 5 × 5 | 210 × 210 mm | back | 3 |

The 4 × 5 tiles (`drawer_baseplate_4x5.scad` and `drawer_baseplate_4x5_back.scad`)
remain in the project as optional parts for narrower grids.

Assemble front row first, then lower each back-row tile onto it (see above).

## Filling the leftover floor

The grid covers 630 × 420 mm of a 630 × 424 mm floor, so there is no width
slack and `drawer_filler` is not needed for this drawer. The 4 mm of depth
slack is 2 mm per side, too thin to be worth printing — push the assembly
against the back of the drawer, or pack the front gap.

`drawer_filler.scad` is retained as an optional part: a strip the same 4.65 mm
thickness as a baseplate tile, so the floor finishes flush, with a customizable
`fill_w` (default **19.5 mm**) for drawers wider than 630 mm. Each strip is
5 cells (210 mm) long, so two of them end to end cover the 420 mm depth.

Both long edges are notched and neither carries a tab. On the **+X** side of the
assembly those notches swallow the baseplate's protruding tabs; on the **-X**
side, where the baseplate presents notches of its own, the two notched edges
simply butt. The strip is therefore symmetric and cannot be fitted back to
front, and nothing protrudes towards the drawer wall — a tab on the outer edge
would have added its 1.8 mm to the overall width.

## Bins

`drawer_bin_5x5.scad` is 5 × 5 cells — 210 × 210 mm, the largest that fits the
A1's 250 mm bed (6 cells would be 252 mm). At 8 height units it is 56 mm tall,
leaving 13 mm of clearance under the 69 mm drawer height.

Six 5 × 5 bins tile onto the 15 × 10 grid (3 across × 2 deep) with nothing left
over. The bin is parametric — drop `grid_x` / `grid_y` in the customizer for
narrower bins, and `z_units` for shallower ones.

## Container layout (full assembly preview)

`drawer_assembly.scad` renders the whole drawer as a single preview so the
finished result reads at a glance: the full 15 × 10 baseplate floor (drawn as
one continuous slab) with a fitted set of containers seated on top. The
assembly file itself is a **viewing aid, not a printable part** — it is not
tiled for the print bed — but each container is now also available
individually as a printable part (see "Printing the containers" below). The
containers remain plain tapered tubs with no stacking lip.

The containers are **69 mm tall, the full drawer height** (issue #326); unlike
the bins they have no stacking lip and are not Gridfinity-stackable, so their
height is not quantized to the 7 mm unit.

Looking down, with −Y as the drawer front and +Y the back, the 15 × 10 grid is
divided into eight containers (the layout sketched in issue #324):

| Container | Cells | Grid region | Flare | Source file |
|---|---|---|---|---|
| Left | 3 × 10 | cols 1–3, full depth | outer wall out to −X | `drawer_container_left` |
| Back-left | 4 × 6 | cols 4–7, rows 5–10 | — | `drawer_container_back_4x6` (×2) |
| Back-centre | 4 × 6 | cols 8–11, rows 5–10 | — | `drawer_container_back_4x6` (×2) |
| Back-right | 4 × 6 | cols 12–15, rows 5–10 | outer wall out to +X | `drawer_container_back_4x6_right` |
| Front wide | 8 × 4 | cols 4–11, rows 1–4 | — | `drawer_container_front_8x4` |
| Front middle | 3 × 4 | cols 12–14, rows 1–4 | — | `drawer_container_front_3x4` |
| Front narrow | 1 × 3 | col 15, rows 1–3 | outer wall out to +X | `drawer_container_front_1x3` |
| Front corner | 1 × 1 | col 15, row 4 | outer wall out to +X | `drawer_container_front_1x1` |

The left bin runs the full depth of the drawer. The remaining 12 × 10 block is
split front-to-back at rows 4|5: the back six rows carry three equal 4-wide
tubs, and the front four rows carry an 8-wide tub, a 3-wide one, and then the
last column on its own — a 1 × 3 with the single 1 × 1 cell behind it. The
eight containers tile the grid exactly: 30 + 3 × 24 + 32 + 12 + 3 + 1 = 150
cells.

### The "3x3" in issue #324 → 3 × 4

Issue #324's text lists the front row as "8x4, 3x3 and then 1x3 and 1x1". The
middle container is implemented here as **3 × 4**, not 3 × 3, for two reasons:
the sketch draws its back edge on the same line as the 8 × 4's, i.e. the full
4-row front depth; and 3 × 3 would leave an unclaimed 3 × 1 hole between it and
the back row, where 3 × 4 tiles the grid exactly. If 3 × 3 was meant literally,
setting `grid_y = 3` in `drawer_container_front_3x4`'s customizer gives it,
and the hole can be filled with a 3 × 1 tub.

### Why the side containers flare

The drawer is 630 mm wide at the floor but flares to **~670 mm at the top** over
its 69 mm height (see the measurements table above). A flaring container's
outer face starts at 314.75 mm from centre (`grid_x*cell_pitch/2 - 4 + pad_r_top`),
just 0.25 mm inboard of the drawer wall's 315 mm at the floor — the 15 × 10 grid
fills the floor edge to edge, so there is nothing left to reclaim down there.
All of the reclaimable volume is higher up, where the wall has flared out.

So the four containers whose outer wall faces a drawer side — Left on the −X
side, and Back-right, Front narrow and Front corner on the +X side — aim that
wall straight at the drawer wall: it leans out **18.75 mm** over the
container's 4.75 → 69 mm shell, landing 1.5 mm short of the drawer wall at its
top edge (335 mm from centre). That is a 16.3° lean from vertical, well inside
the usual 45° overhang rule, though these tubs remain a viewing aid rather
than a printable part. Resulting preview widths: floor ≈ 630 mm, rim
≈ 667 mm — so the preview reads wider at the top, as the drawer is.

The inner cavity flares against the same `pad_height`…`H` reference span, so the
wall stays a true 1.6 mm horizontally (1.34 mm measured perpendicular to the
leaning face). The `container()` module in `_drawer_organiser.scad` takes a
per-side outward offset (`fnx`/`fpx`/`fny`/`fpy`); the other three walls of each
flaring bin, and the four interior bins entirely, stay vertical.

The drawer's walls *curve* rather than taper straight: they curve away rapidly
just above the floor (confirmed on the first printed part, issue #326), so the
real wall sits outside the straight taper at every mid-height and a straight
flared wall aimed at the top edge cannot touch it. The 1.5 mm clearance
(container_wall_clear) applies at the top edge, where the two meet.

The containers still stand on Gridfinity base pads, so in the preview they
register on the baseplate sockets exactly like a real bin (the 0.25 mm
pad-to-socket clearance keeps pad and socket disjoint, so seating one costs the
merged preview nothing).

### Printing the containers

Four of the eight containers are longer than the A1's 250 mm bed, and each of
those ships pre-split into printable pieces (issue #319) with seams offset from
the baseplate tile seams underneath (issue #322) so a solid piece bridges each
grid join — stiffening the floor assembly — and cut faces meet over the
middle of a single tile, which keeps them flush even without glue. The left
container is the exception: its 10-cell depth only splits into two ≤5-cell
pieces at cell 5, which is the tile seam itself — two pieces were preferred
over introducing a third cut. No piece spans more than 5 cells along its
split axis.

The other four — `drawer_container_front_3x4` (125.5 × 167.5 mm),
`drawer_container_front_1x3` (≈ 60.25 × 125.5 mm at the rim) and
`drawer_container_front_1x1` (≈ 60.25 × 41.5 mm) — **fit the bed whole**, so the
whole-container file *is* the printable part and there are no piece files for
them. The 4 × 6 back containers only miss by 1.5 mm (251.5 mm deep against a
250 mm bed), but they do miss.

All seven whole-container files remain in the project for preview and
customization; their default STL download is the whole assembled shape
(`split_parts = 1`), built on `container_part()` in `_drawer_organiser.scad`.
`drawer_container_front_1x1` is the one exception — a single cell cannot be
split on either axis, so it calls `container()` directly and exposes no
`split_parts`. The piece files call the lower-level `container_slice()`, which
takes an explicit cell range instead of an even split.

Seat the pieces on the assembled baseplate first — the pads and sockets are
the alignment jig — then glue the cut faces with CA.

| File | Parent container | Cells | Footprint |
|---|---|---|---|
| `drawer_container_left_front` | left | 5 (of 10, Y) | 144.25 × 209.75 mm |
| `drawer_container_left_back` | left | 5 (of 10, Y) | 144.25 × 209.75 mm |
| `drawer_container_back_4x6_half` | back-left / back-centre | 3 (of 6, Y) | 167.5 × 125.75 mm |
| `drawer_container_back_4x6_right_front` | back-right | 3 (of 6, Y) | 186.25 × 125.75 mm |
| `drawer_container_back_4x6_right_back` | back-right | 3 (of 6, Y) | 186.25 × 125.75 mm |
| `drawer_container_front_8x4_half` | front wide | 4 (of 8, X) | 167.75 × 167.5 mm |

Where the cuts fall, against the 5 × 5 tile grid underneath (1-based drawer
columns and rows):

- The **4 × 6** back containers split 3 + 3 in Y, cutting at rows 7|8 — over
  the middle of the back tile row — while the front half straddles the tile
  seam at rows 5|6.
- The **8 × 4** front container splits 4 + 4 in X, cutting at columns 7|8 —
  over the middle of the centre tile column — with the −X half straddling the
  seam at columns 5|6 and the +X half the seam at columns 10|11.

The flared pieces (left, back-right) are wider than their nominal footprint
because the outer wall leans out ≈ 18.75 mm at the rim (see "Why the side
containers flare" above).

Two of the piece files are the **same part twice over**, because an unflared
container is unchanged by a 180° rotation about Z:

- `drawer_container_back_4x6_half` is both halves of both unflared back
  containers — print **four**, rotating one of each pair 180° about Z.
- `drawer_container_front_8x4_half` is both halves of the 8 × 4 — print
  **two**, rotating one 180° about Z.

The flared containers do not get that: rotating a flared half puts the leaning
wall on the wrong side, so the left container's two pieces are mirror images
(print `drawer_container_left_front` and `drawer_container_left_back`, one
each), and so are the back-right container's (`_right_front` and
`_right_back`, one each).

## Bins longer than the print bed

There is **no official Gridfinity spec** for bins that exceed the print bed. The
community-standard method is to split the bin at a cell boundary, print the
pieces, and glue them — optionally with printed alignment tabs. See
[Gridfinity Split bins](https://www.printables.com/model/707095-gridfinity-split-bins)
and [MakerWorld split bins](https://makerworld.com/en/models/815089-gridfinity-split-bin-all-sizes).

`drawer_bin_10x5_half.scad` does this for a 10 × 5 bin (assembled 420 × 210 ×
56 mm, spanning two baseplate tiles in X). Each half prints at
**209.75 × 209.5 mm**, inside the A1's 250 mm bed.

The bin is symmetric in both X and Y, so the two halves are the **same part**:
print two, rotate one 180° about Z, and glue the flat faces together.

This is a plain butt-glue joint with no printed alignment tabs, deliberately.
Below `pad_height` (4.75 mm) the split plane passes through the 0.5 mm air gap
between adjacent base pads, so any horizontal tab there would be an unsupported
overhang. Instead, **the baseplate is the alignment jig** — seat both halves on
a baseplate before gluing and the pads/sockets hold them in register to
0.25 mm. Glue with CA.

Because the assembled bin spans two tiles, this is the case that depends on the
42 mm pitch continuing exactly across a seam (see above).

## Print list

### The floor — six parts

| Part | Qty | Each | Total |
|---|---|---|---|
| `drawer_baseplate_5x5` (front row) | 3 | 32.06 cm³ | 96.18 cm³ |
| `drawer_baseplate_5x5_back` (back row) | 3 | 31.99 cm³ | 95.97 cm³ |
| **Total** | **6** | | **192.15 cm³ (≈ 238 g PLA)** |

Volumes are the solid mesh volume — the baseplate lattice is nearly all
perimeter so it slices close to this, while the filler strips come out lighter
with sparse infill.

Assembly order: lay the front row left to right, then **lower** each back-row
tile onto it (the seams do not press together in-plane — see above).

### Bins

- 6 × `drawer_bin_5x5` (or as many as wanted; the grid is the constraint, not
  the design)
- 2 × `drawer_bin_10x5_half` per full-depth 10 × 5 bin

### Containers (optional)

The full-drawer layout previewed by `drawer_assembly.scad` needs the
following parts (see "Printing the containers" above — the last three are
whole containers, the rest are pre-split pieces):

| Part | Qty |
|---|---|
| `drawer_container_left_front` | 1 |
| `drawer_container_left_back` | 1 |
| `drawer_container_back_4x6_half` | 4 |
| `drawer_container_back_4x6_right_front` | 1 |
| `drawer_container_back_4x6_right_back` | 1 |
| `drawer_container_front_8x4_half` | 2 |
| `drawer_container_front_3x4` | 1 |
| `drawer_container_front_1x3` | 1 |
| `drawer_container_front_1x1` | 1 |

## Possible follow-ups

Deliberately out of scope for now:

- Magnet or screw holes in the bin bases
- Bin dividers and internal compartments
- Label tabs and finger scoops
