// Drawer Organiser — half of a 10x5 storage bin (assembled: 420 x 210 x 56mm)
// Render this file to generate drawer_bin_10x5_half.stl
// Each half prints at 209.75 x 209.5mm, inside the A1's 250mm bed.
// Print two, rotate one 180 degrees about Z, and glue the flat faces together:
// the assembled bin is symmetric in X and Y, so both halves are the same part.
// Seat both halves on a baseplate before gluing — the pads/sockets align them.

include <_drawer_organiser.scad>

grid_x  = 10;         // cells across (X) of the ASSEMBLED bin
grid_y  = 5;          // cells deep (Y)
z_units = 8;          // 7mm height units -> 56mm tall
wall_t  = 1.6;        // wall thickness (mm)
floor_t = 1.6;        // floor thickness above the base pads (mm)
stacking_lip = true;  // cut the stacking lip into the top rim
split_parts = 2;      // pieces the assembled bin is split into
part_index  = 0;      // which piece this file renders

bin_part(grid_x, grid_y, z_units, wall_t, floor_t, stacking_lip,
         split_parts, part_index);
