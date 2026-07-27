// Drawer Organiser — unflared back-row container of the full-drawer layout (4 x 6 cells)
// Render this file to generate drawer_container_back_4x6.stl
// 168 x 252 x 69mm nominal — the actual footprint is 167.5 x 251.5mm, so it
// misses an A1's 250mm bed by 1.5mm in Y. This file renders the whole
// container; the printable pieces ship as drawer_container_back_4x6_half
// (x2 per container), split offset from the baseplate tile seam underneath so
// a solid piece straddles the grid join (issue #322). The customizer
// split_parts/part_index remain for other bed sizes.
//
// This one file is BOTH the back-left and back-centre container of the layout
// in issue #324: neither reaches a drawer wall, so neither flares. The
// back-right container stands against the wall and is a separate renderable,
// drawer_container_back_4x6_right.
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
               split_y = true, parts = split_parts, index = part_index);
