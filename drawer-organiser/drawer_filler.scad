// Drawer Organiser — side filler strip
// Render this file to generate drawer_filler.stl
// Takes up the width slack between the assembled baseplate and the drawer
// walls. Four of these fill a 628mm-wide drawer: two per side, end to end
// (see layout.md). Both long edges are notched, so the strip cannot be fitted
// back to front — on the +X side of the assembly the notches swallow the
// baseplate's tabs, on the -X side the notched edges just butt.

include <_drawer_organiser.scad>

grid_y = 5;      // cells long (Y), matching the baseplate tile beside it
fill_w = 19.5;   // strip width (X) in mm; 588 + 2 * fill_w = assembled width

filler(grid_y, fill_w);
