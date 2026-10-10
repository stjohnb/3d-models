// Drawer Organiser — right-hand filler strip for the long-implement drawer
// Render this file to generate drawer_long_filler.stl
// 10 x 210 x 4.65mm. Print TWO (one per 5-cell tile row, front and back).
// Symmetric. Takes up the width slack beside the vertical right wall: its
// notches swallow the right-hand tile tabs. Raise fill_w if the drawer is
// wider than 390mm.

include <_drawer_long.scad>

grid_y = 5;      // cells long (Y), matching the baseplate tile beside it
fill_w = 10;     // strip width (X) in mm; = long_drawer_fill_w

filler(grid_y, fill_w);
