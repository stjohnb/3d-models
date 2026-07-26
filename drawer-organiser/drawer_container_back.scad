// Drawer Organiser — back container of the full-drawer layout (12 x 3 cells)
// Render this file to generate drawer_container_back.stl
// 504 x 126 x 56mm assembled — too long for an A1's 250mm bed. This file
// renders the whole container; the printable pieces ship as
// drawer_container_back_left / drawer_container_back_centre /
// drawer_container_back_right, split offset from the baseplate tile seams
// underneath so a solid piece straddles each grid join (issue #322). The
// customizer split_parts/part_index remain for other bed sizes.
//
// Stands against the drawer's right wall at its +X end, so its +X wall leans
// outward with height to follow the drawer (see side_flare() in
// _drawer_organiser.scad).
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 12;         // cells across (X)
grid_y  = 3;          // cells deep (Y)
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along X for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, z_units, wall_t, floor_t,
               fpx = side_flare(z_units),
               split_y = false, parts = split_parts, index = part_index);
