// Drawer Organiser — front piece of a front 4x7 container (4 x 7 cells)
// Render this file to generate drawer_container_front_4x7_front.stl
// 167.5 x 125.75mm — cells [0,3) of the container's 7-cell depth, split
// offset from the baseplate tile seam so a solid piece straddles the grid
// join and the cut faces meet mid-tile (issue #322). Print together with
// drawer_container_front_4x7_back to assemble the full 168 x 294 x 56mm
// container.
//
// This is a piece of both the front-left and front-centre container of the
// layout — neither touches a drawer wall, so print two of this piece.
// Seat both pieces on the assembled baseplate first — the pads and sockets
// are the alignment jig — then glue the flat faces with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X) of the ASSEMBLED container
grid_y  = 7;          // cells deep (Y) of the ASSEMBLED container
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, z_units, wall_t, floor_t,
                split_y = true, c0 = 0, c1 = 3);
