# Drawer layout

## Drawer measurements (from issue #298)

| Dimension | Value |
|---|---|
| Width at the bottom | 628 mm |
| Width at the top | 665 mm (the sides flare outward) |
| Depth | 424 mm |
| Height (bottom to top) | 69 mm |

The organiser is sized against the **bottom** width, 628 mm, because the
baseplate sits on the drawer floor. The flare to 665 mm at the top only adds
clearance above the plate, so it does not constrain anything.

## Grid

Gridfinity's cell pitch is 42 mm.

- Across: `floor(628 / 42) = 14` cells → 588 mm
- Deep: `floor(424 / 42) = 10` cells → 420 mm

A **14 × 10 grid (588 × 420 mm)** covers the floor, leaving 40 mm of width slack
(20 mm per side) and 4 mm of depth slack (2 mm per side).

> The 420 mm depth assumes 424 mm is the **internal** measurement. If 424 mm is
> an outside measurement, 10 rows will not fit — drop to 9 rows (378 mm), which
> means printing 4 × `drawer_baseplate_4x5` (or 5 × 4 and 4 × 4 tiles) instead
> of the arrangement below.

## Tiling the baseplate

588 mm cannot be printed in one piece on an A1 (250 × 250 mm usable), so the
baseplate is tiled **3 columns × 2 rows**:

- Columns of 5, 5 and 4 cells across → 210 + 210 + 168 mm = 588 mm
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
- **Width:** `588 + 1.8 = 589.8 mm`, comfortably inside 628 mm.

Both fit, so the `_back` tiles — which omit the +Y tabs — are no longer required
the way they were when tabs protruded 5.55 mm. They are still worth printing for
the rear row: the tabs there mate with nothing, and omitting them keeps the
assembly exactly 420 mm deep and its back edge flat against the drawer.

The -X and -Y edges of the assembly carry notches, which cut inward and add
nothing to the overall size.

### Tiles

| Tile | Cells | Size | Row | Quantity |
|---|---|---|---|---|
| `drawer_baseplate_5x5.scad` | 5 × 5 | 210 × 210 mm | front | 2 |
| `drawer_baseplate_4x5.scad` | 4 × 5 | 168 × 210 mm | front | 1 |
| `drawer_baseplate_5x5_back.scad` | 5 × 5 | 210 × 210 mm | back | 2 |
| `drawer_baseplate_4x5_back.scad` | 4 × 5 | 168 × 210 mm | back | 1 |

Assemble front row first, then lower each back-row tile onto it (see above).

## Filling the leftover floor

The grid covers 588 × 420 mm of a 628 × 424 mm floor. What is left over:

| Direction | Slack | Handled by |
|---|---|---|
| Width (X) | `628 − 588 = 40 mm` | 4 × `drawer_filler`, two per side |
| Depth (Y) | `424 − 420 = 4 mm` | left as-is |

`drawer_filler.scad` is a strip the same 4.65 mm thickness as a baseplate tile,
so the floor finishes flush. Default width is **19.5 mm**, which puts the
assembled floor at `588 + 2 × 19.5 = 627 mm` and leaves 1 mm of play to get it
in. Measure your own drawer and set `fill_w = (width − 588) / 2` in the
customizer if it differs.

Each strip is 5 cells (210 mm) long, so two of them end to end cover the 420 mm
depth — four strips in total.

Both long edges are notched and neither carries a tab. On the **+X** side of the
assembly those notches swallow the baseplate's protruding tabs; on the **-X**
side, where the baseplate presents notches of its own, the two notched edges
simply butt. The strip is therefore symmetric and cannot be fitted back to
front, and nothing protrudes towards the drawer wall — a tab on the outer edge
would have added its 1.8 mm to the overall width.

The 4 mm of depth slack is 2 mm per side, too thin to be worth printing. Push
the assembly against the back of the drawer, or pack the front gap.

## Bins

`drawer_bin_5x5.scad` is 5 × 5 cells — 210 × 210 mm, the largest that fits the
A1's 250 mm bed (6 cells would be 252 mm). At 8 height units it is 56 mm tall,
leaving 13 mm of clearance under the 69 mm drawer height.

Four 5 × 5 bins tile onto the 14 × 10 grid (2 across × 2 deep), leaving a
4-cell-wide × 10-cell-deep strip down one side for smaller bins. The bin is
parametric — drop `grid_x` / `grid_y` in the customizer to fill that strip with
narrower bins, and `z_units` for shallower ones.

## Container layout (full assembly preview)

`drawer_assembly.scad` renders the whole drawer as a single preview so the
finished result reads at a glance: the full 14 × 10 baseplate floor (drawn as
one continuous slab, plus the four filler strips) with a fitted set of
containers seated on top. It is a **viewing aid, not a printable part** — the
containers are plain tapered tubs with no stacking lip, and the file is not
tiled for the print bed. The printable parts are the other `drawer_*` files.

Looking down, with −Y as the drawer front and +Y the back, the 14 × 10 grid is
divided into five containers:

| Container | Cells | Grid region | Flare |
|---|---|---|---|
| Left | 3 × 10 | cols 1–3, full depth | outer wall out to −X |
| Back | 11 × 3 | cols 4–14, back 3 rows | outer end out to +X |
| Front-left | 4 × 7 | cols 4–7, front 7 rows | — |
| Front-centre | 4 × 7 | cols 8–11, front 7 rows | — |
| Front-right | 3 × 7 | cols 12–14, front 7 rows | outer wall out to +X |

The left bin runs the full depth of the drawer; the back bin fills the rest of
the rear; and the remaining front block (11 × 7 cells) is split into three
roughly equal areas of 4, 4 and 3 cells across (28, 28 and 21 cells).

### Why the side containers flare

The drawer is 628 mm wide at the floor but flares to **665 mm at the top** over
its 69 mm height (see the measurements table above). A container standing
against a side wall would waste that extra top volume if its outer wall stayed
vertical, so the three containers whose outer wall faces a drawer side — Left,
Back and Front-right — lean that wall outward with height at the drawer's own
slope. Over a 56 mm-tall container that is `18.5 / 69 × 56 ≈ 15 mm` of extra
reach at the rim. The inner cavity leans out on the same slope — both shells
measure their flare against the same `pad_height`…`H` span, not their own
z-range — so the wall stays 1.6 mm thick (measured horizontally) all the way up
rather than thickening towards the floor. The `container()` module in `_drawer_organiser.scad`
takes a per-side outward offset (`fnx`/`fpx`/`fny`/`fpy`); the other three walls
of each bin, and both front bins entirely, stay vertical.

The containers still stand on Gridfinity base pads, so in the preview they
register on the baseplate sockets exactly like a real bin (the 0.25 mm
pad-to-socket clearance keeps pad and socket disjoint, so seating one costs the
merged preview nothing).

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

### The floor — ten parts

| Part | Qty | Each | Total |
|---|---|---|---|
| `drawer_baseplate_5x5` (front row) | 2 | 32.06 cm³ | 64.11 cm³ |
| `drawer_baseplate_4x5` (front row) | 1 | 25.62 cm³ | 25.62 cm³ |
| `drawer_baseplate_5x5_back` (back row) | 2 | 31.99 cm³ | 63.98 cm³ |
| `drawer_baseplate_4x5_back` (back row) | 1 | 25.56 cm³ | 25.56 cm³ |
| `drawer_filler` (2 per side) | 4 | 18.62 cm³ | 74.46 cm³ |
| **Total** | **10** | | **253.7 cm³ (≈ 315 g PLA)** |

Volumes are the solid mesh volume — the baseplate lattice is nearly all
perimeter so it slices close to this, while the filler strips come out lighter
with sparse infill.

Assembly order: lay the front row left to right, then **lower** each back-row
tile onto it (the seams do not press together in-plane — see above), then drop
the four filler strips down the sides.

### Bins

- 4 × `drawer_bin_5x5` (or as many as wanted; the grid is the constraint, not
  the design)
- 2 × `drawer_bin_10x5_half` per full-depth 10 × 5 bin

## Possible follow-ups

Deliberately out of scope for now:

- Magnet or screw holes in the bin bases
- Bin dividers and internal compartments
- Label tabs and finger scoops
