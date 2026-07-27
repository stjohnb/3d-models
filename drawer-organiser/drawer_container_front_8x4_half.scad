// Drawer Organiser — half of the wide front container (8 x 4 cells)
// Render this file to generate drawer_container_front_8x4_half.stl
// 167.75 x 167.5mm — cells [0,4) of the container's 8-cell width. The assembled
// container is 335.5mm wide, so it splits 4 + 4 at cell 4 (columns 7|8 of the
// drawer, 1-based): that cut lands over the middle of the drawer's centre
// baseplate tile, and each half straddles one tile seam — the -X half the seam
// at columns 5|6, the +X half the seam at columns 10|11 — so a solid piece
// bridges each grid join and the cut faces meet mid-tile (issues #319/#322).
//
// The container is unflared and symmetric in both X and Y, so its two halves
// are the SAME part — as with drawer_bin_10x5_half. Print TWO, rotate one
// 180 degrees about Z, seat both on the assembled baseplate to align them —
// the pads and sockets are the alignment jig — then glue the flat faces
// with CA.
// No rotate(): the project sets viewer_rotate_x in meta.json.

include <_drawer_organiser.scad>

grid_x  = 8;          // cells across (X) of the ASSEMBLED container
grid_y  = 4;          // cells deep (Y) of the ASSEMBLED container
height  = 69;         // overall height above the drawer floor (mm); the drawer is 69mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)

container_slice(grid_x, grid_y, height, wall_t, floor_t,
                split_y = false, c0 = 0, c1 = 4);
