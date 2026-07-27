// Drawer Organiser — back-right container of the full-drawer layout (4 x 6 cells)
// Render this file to generate drawer_container_back_4x6_right.stl
// 168 x 252 x 69mm nominal (186.25mm wide at the rim, where the flared wall
// leans out) — 1.5mm too deep for an A1's 250mm bed. This file renders the
// whole container; the printable pieces ship as
// drawer_container_back_4x6_right_front / drawer_container_back_4x6_right_back,
// split offset from the baseplate tile seam underneath so a solid piece
// straddles the grid join (issue #322). The customizer split_parts/part_index
// remain for other bed sizes.
//
// Stands against the drawer's right wall, so its +X wall leans outward with
// height to follow the drawer (see side_flare() in _drawer_organiser.scad).
// The two unflared back-row containers are the separate renderable
// drawer_container_back_4x6.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X)
grid_y  = 6;          // cells deep (Y)
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, height, wall_t, floor_t,
               fpx = side_flare(height),
               split_y = true, parts = split_parts, index = part_index);
