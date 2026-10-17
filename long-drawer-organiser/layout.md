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
| 1–2 (3 at the front) | flared left, diagonal right wall | 122.3 mm → 80.3 mm at the floor, ~141 → ~99 mm at the rim | stick blender and attachments |
| 3–6 (3 at the front) | unflared centre, diagonal left wall | 122.3 mm → 164.3 mm | wide implements |
| 7–8 | 2 × 9 | 80.3 × 374.3 mm | spatulas, whisks, spoons, tongs |
| 9–10 | 2 × 9 | 80.3 × 374.3 mm | same |
| 7–10, row 1 | 4 × 1 across the front | 164.3 × 38.3 mm | small flat items |

**Diagonal.** The wide pair's boundary runs from column boundary 3|4 at the
front edge (grid y = −210) to 2|3 at the rear (y = +210): one cell over 420 mm,
5.71° off the Y axis (`long_diag_x()`, `long_diag_angle`). It is a true angled
wall, not stepped: each container is the library's rectangular `container()`
clipped by a vertical plane along the diagonal and closed with a `wall_t` wall
(`long_diag_container()`). Each outer face sits 0.25 mm inside the boundary
(`long_edge_inset`), so the pair clears by 0.5 mm like any two neighbouring
containers. Base pads in column 3 are cut by the same plane; each container
keeps its part and both share one baseplate socket.

**Splits.** The wide pair is cut 5 + 5 on the tile seam (rows 5|6) because six
cells (251.75 mm) exceed the 250 mm bed. The diagonal breaks 180° symmetry, so
there are four distinct pieces: `_left_front`, `_left_back`, `_centre_front`,
`_centre_back` (`long_diag_container_slice()`). Each 2 × 9 slot is the
already printed `drawer_long_container_2x10_half` as its front five cells plus
`drawer_long_container_2x9_back` for rows 7–10, so its glue seam sits one cell
behind the tile seam. The 4 × 1 prints whole. The largest piece is
`_centre_back` at about 167.25 × 209.75 mm; everything fits the 250 × 250 mm
bed. `_left`, `_centre` and `_2x9` are whole-container viewing aids.

**Mating checks.** CI's interference check intersects the two STLs as
rendered, both centred on the origin. Odd-width pieces (`_left_front`,
`_left_back`) pair with `drawer_baseplate_5x5`; even-width pieces
(`2x10_half`, `4x1`, `_centre_front`, `_centre_back`) pair with
`drawer_baseplate_4x5`, whose cells then align as on the real tile.
`drawer_long_container_2x9_back` is unpaired: every tile is 5 rows deep, so a
4-row piece centred on the origin lands its pads on socket ridges; its pads are
the same library pads already checked through the 2 × 5 half.

**Print list**

| Part | Project | Qty |
|---|---|---|
| `drawer_baseplate_5x5` | drawer-organiser | 2 |
| `drawer_baseplate_5x5_back` | drawer-organiser | 2 |
| `drawer_long_container_left_front` / `_left_back` | this project | 1 each |
| `drawer_long_container_centre_front` / `_centre_back` | this project | 1 each |
| `drawer_long_container_2x10_half` (already printed) | this project | 2 |
| `drawer_long_container_2x9_back` | this project | 2 |
| `drawer_long_container_4x1` | this project | 1 |

`drawer_long_assembly` previews the layout. The drawer-organiser's
`drawer_container_left_front` / `_back` are no longer used here.
