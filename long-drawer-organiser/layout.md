# Long drawer layout (422 × 425 mm)

A second drawer holds long implements: narrow ones such as spatulas and wide
ones such as a stick blender. It reuses the drawer-organiser's geometry library
by cross-project include: `_drawer_long.scad` includes
`../drawer-organiser/_drawer_organiser.scad`, adds this drawer's named
dimensions and leaves the shared library untouched. The baseplate tiles and the
flared left container pieces are the drawer-organiser project's own parts.

| Measurement | Value | Source |
|---|---|---|
| Floor width | 422 mm (`long_drawer_floor_w` = 10 × 42 + 2) | measured by fitting two 5 × 5 tiles after widening the drawer with an adjustable knife holder (issue clw_01M4R6ED006HYSY6F15NMYHMGD) |
| Depth, front to back | 425 mm (`long_drawer_depth`) | issue clw_01M43Z7AXXMZQCK6ZDVCBB6K4D |
| Height | 69 mm (`long_drawer_height`) | assumed from the first drawer; not remeasured |
| Left wall | flares outward 20 mm over 69 mm (`long_drawer_taper`) | same flare as the first drawer |
| Right wall | vertical, no taper | issue clw_01M43Z7AXXMZQCK6ZDVCBB6K4D |

**Grid.** 10 × 10 cells = 420 × 420 mm. Width slack is 2 mm
(`long_drawer_slack`), against the vertical right wall; depth slack is
425 − 420 = 5 mm, put at the front. The grid sits flush against the flared left
wall.

**Tiles.** Two `drawer_baseplate_5x5` in the front row and two
`drawer_baseplate_5x5_back` behind, so the tile seams fall at columns 5|6 and
rows 5|6. The left edge has exposed notches. The right-hand tiles' outermost +X
tabs mate with nothing and add 1.8 mm, which the 2 mm slack absorbs; if the
drawer is tight, clip them flush with side cutters.

**Flare.** Relative to the grid edge the left taper is the first drawer's:
`long_left_flare(69) = 20 − 1.5 + 0.25 = 18.75 mm`, equal to `side_flare(69)`
(an `assert` in `_drawer_long.scad` enforces this), so the flared left
wall matches the first drawer.

| Columns | Container | Clear width (front → rear) | Suits |
|---|---|---|---|
| 1–2 | flared 2 × 10, flared -X wall | 80.3 mm at the floor, ~99 mm at the rim, 416.3 mm deep | stick blender and attachments |
| 3–6 | unflared 4 × 10 | 164.3 × 416.3 mm | wide implements |
| 7–8 | 2 × 8 (rows 2–9) | 80.3 × 332.3 mm | spatulas, whisks, spoons, tongs |
| 9–10 | 2 × 8 (rows 2–9) | 80.3 × 332.3 mm | same |
| 7–10, row 1 | three-sided 4 × 1 across the front, seated rotated 180° (walls at the drawer front and against the 4 × 10; open towards the 2 × 8 slots and the right wall) | 168.2 × 40.4 mm, bounded by the neighbours' walls (adds the dropped 1.6 mm wall and 0.5 mm clearance on each axis, plus 2 mm slack on X) | small flat items |
| 7–10, row 10 | 4 × 1 seated rotated 180°: both long walls and the wall against the 4 × 10, open on the right-wall side | 168.2 × 38.3 mm | small flat items |

**Splits.** The straight 2 × 10 and 4 × 10 are each cut 5 + 5 on the tile seam (rows 5|6): the flared 2 × 10 halves (`_left_2x10_front`, `_left_2x10_back`) are mirror images because of the flare, while the 4 × 10 halves are one 180°-symmetric part (`_centre_4x10_half`) printed twice. Each 2 × 8 slot is the already printed `drawer_long_container_2x10_half` as its front five cells plus `drawer_long_container_2x8_back` for rows 7–9 (83.5 × 125.75 mm), so its glue seam sits one cell behind the tile seam. Both 4 × 1 pieces print whole: the front one has three faces (floor, +Y long wall, +X short wall); the rear one (`_4x1_rear`) keeps both long walls and the +X short wall (`open_right` flips the open short side). Both seat rotated 180°, so each open short side faces the drawer's right wall, closed by the wall across the 2 mm slack with the tiles' +X tabs at floor level; the rear piece's opening faces that slack gap, so very thin items could stand in the slit. Floors and pads keep the full 4 × 1 footprint. The largest piece is `_centre_4x10_half` at 167.5 × 209.75 mm; everything fits the 250 × 250 mm bed. `_left_2x10`, `_centre_4x10` and `_2x8` are whole-container viewing aids.

**Mating checks.** CI's interference check intersects the two STLs as rendered, both centred on the origin. Every piece pairs with `drawer_baseplate_4x5` (`2x10_half`, `2x8_back`, `4x1`, `4x1_rear`, `_left_2x10_front`, `_left_2x10_back`, `_centre_4x10_half`), whose cells then align as on the real tile. `_2x8_back` has three rows, odd like the tile's five, so its cells align on the origin.

**Print list**

| Part | Project | Qty |
|---|---|---|
| `drawer_baseplate_5x5` | drawer-organiser | 2 |
| `drawer_baseplate_5x5_back` | drawer-organiser | 2 |
| `drawer_long_container_left_2x10_front` / `_left_2x10_back` | this project | 1 each |
| `drawer_long_container_centre_4x10_half` | this project | 2 |
| `drawer_long_container_2x10_half` (already printed) | this project | 2 |
| `drawer_long_container_2x8_back` | this project | 2 |
| `drawer_long_container_4x1` | this project | 1 |
| `drawer_long_container_4x1_rear` | this project | 1 |

`drawer_long_assembly` previews the layout.
