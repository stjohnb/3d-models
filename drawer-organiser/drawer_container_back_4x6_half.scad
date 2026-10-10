// Drawer Organiser — half of an unflared back-row container (4 x 6 cells)
// Render this file to generate drawer_container_back_4x6_half.stl
// 167.5 x 125.75mm — cells [0,3) of the container's 6-cell depth. The assembled
// 4 x 6 container is 251.5mm deep, 1.5mm over an A1's 250mm bed, so it splits
// 3 + 3 at cell 3 (rows 7|8 of the drawer, 1-based): that cut lands over the
// middle of the back baseplate tile while the front half straddles the tile
// seam at rows 5|6, so a solid piece bridges the grid join and the cut faces
// meet mid-tile (issues #319/#322).
//
// An unflared 4 x 6 container has 180-degree rotational symmetry about Z, so
// its two halves are the SAME part — as with drawer_bin_10x5_half. Print FOUR
// of these: two per container, for both the back-left and back-centre positions
// of the layout in issue #324, rotating one of each pair 180 degrees about Z.
// The back-right container's wall flares, which breaks that symmetry; its
// pieces are the separate drawer_container_back_4x6_right_front / _back.
//
// Seat the pieces on the assembled baseplate first — the pads and sockets are
// the alignment jig — then glue the flat faces with CA.
// No rotate(): sources stay OpenSCAD Z-up; the viewer applies the Z-up -> Y-up conversion itself.

include <_drawer_organiser.scad>

grid_x  = 4;          // cells across (X) of the ASSEMBLED container
grid_y  = 6;          // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                split_y = true, c0 = 0, c1 = 3);
