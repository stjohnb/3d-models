// Drawer Organiser — left piece of the back container (12 x 3 cells)
// Render this file to generate drawer_container_back_left.stl
// 167.75 x 125.5mm — cells [0,4) of the container's 12-cell width (the -X
// end), split offset from the baseplate tile seam so a solid piece straddles
// the grid join and the cut faces meet mid-tile (issue #322). Print together
// with drawer_container_back_centre and drawer_container_back_right to
// assemble the full 504 x 126 x 56mm back container.
//
// This piece does not reach the flared +X end, so it is unflared even though
// it is cut from the same flared parent container as the other back pieces.
// Seat all three pieces on the assembled baseplate first — the pads and
// sockets are the alignment jig — then glue the flat faces with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 12;         // cells across (X) of the ASSEMBLED container
grid_y  = 3;          // cells deep (Y) of the ASSEMBLED container
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, z_units, wall_t, floor_t,
                fpx = side_flare(z_units),
                split_y = false, c0 = 0, c1 = 4);
