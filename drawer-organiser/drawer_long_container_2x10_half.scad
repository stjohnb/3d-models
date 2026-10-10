// Drawer Organiser — half of a narrow long-implement slot (2 x 10 cells)
// Render this file to generate drawer_long_container_2x10_half.stl
// 83.5 x 209.75mm — cells [0,5) of the container's 10-cell depth. The cut lands
// on the baseplate tile seam (rows 5|6), following the left container's
// precedent that two seam pieces beat three offset cuts.
//
// An unflared 2 x 10 container has 180-degree rotational symmetry about Z, so
// both halves are the SAME part. Print SIX: two per slot for all three slots,
// rotating one of each pair 180 degrees about Z.
//
// Seat the pieces on the assembled baseplate first — the pads and sockets are
// the alignment jig — then glue the flat faces with CA.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_long.scad>

grid_x  = 2;          // cells across (X) of the ASSEMBLED container
grid_y  = 10;         // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                split_y = true, c0 = 0, c1 = 5);
