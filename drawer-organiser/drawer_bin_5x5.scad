// Drawer Organiser — 5x5 storage bin (210 x 210 x 56mm)
// Render this file to generate drawer_bin_5x5.stl
// Largest bin that fits an A1's 250 x 250mm bed: 6 cells would be 252mm.
// 8 height units = 56mm, leaving 13mm clearance under the 69mm drawer.

include <_drawer_organiser.scad>

grid_x  = 5;          // cells across (X)
grid_y  = 5;          // cells deep (Y)
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
stacking_lip = true;  // cut the stacking lip into the top rim

bin(grid_x, grid_y, z_units, wall_t, floor_t, stacking_lip);
