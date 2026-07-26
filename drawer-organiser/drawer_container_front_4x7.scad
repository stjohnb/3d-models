// Drawer Organiser — front container of the full-drawer layout (4 x 7 cells)
// Render this file to generate drawer_container_front_4x7.stl
// 168 x 294 x 56mm assembled — too long for an A1's 250mm bed. This file
// renders the whole container; the printable pieces ship as
// drawer_container_front_4x7_front / drawer_container_front_4x7_back, split
// offset from the baseplate tile seam underneath so a solid piece straddles
// the grid join (issue #322). The customizer split_parts/part_index remain
// for other bed sizes.
//
// This is both the front-left and the front-centre container of the layout —
// neither touches a drawer wall, so print two.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X)
grid_y  = 7;          // cells deep (Y)
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
split_parts = 1;      // pieces to split into along Y for the print bed
part_index  = 0;      // which piece this render returns

container_part(grid_x, grid_y, z_units, wall_t, floor_t,
               split_y = true, parts = split_parts, index = part_index);
