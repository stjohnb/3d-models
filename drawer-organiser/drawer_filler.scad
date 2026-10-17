// Drawer Organiser — side filler strip
// Render this file to generate drawer_filler.stl
// Optional strip for taking up width slack when the grid does not fill the
// drawer. The 15 x 10 floor leaves none, so this is not part of the standard
// print list (see layout.md). Both long edges are notched, so the strip cannot
// be fitted back to front — on the +X side of the assembly the notches swallow
// the baseplate's tabs, on the -X side the notched edges just butt.

include <_drawer_organiser.scad>

grid_y = 5;      // cells long (Y), matching the baseplate tile beside it
fill_w = 19.5;   // strip width (X) in mm; grid width + 2 * fill_w = assembled width

filler(grid_y, fill_w);
