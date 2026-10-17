// Long Drawer Organiser — front five cells of a narrow 2 x 9 slot (the already printed 2 x 5 half)
// Render this file to generate drawer_long_container_2x10_half.stl
// 83.5 x 209.75mm — geometry identical to cells [0,5) of a 2 x 10 container, so the
// halves already printed stay valid. In the 2 x 9 slot this is the FRONT five cells
// (rows 2-6); drawer_long_container_2x9_back covers rows 7-10, putting the glue seam
// one cell behind the baseplate tile seam.
//
// Print TWO (one per narrow slot). Seat the pieces on the assembled baseplate first —
// the pads and sockets are the alignment jig — then glue the flat faces with CA.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

grid_x  = 2;          // cells across (X) of the ASSEMBLED container
grid_y  = 10;         // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                split_y = true, c0 = 0, c1 = 5);
