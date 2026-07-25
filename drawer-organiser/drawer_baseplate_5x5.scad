// Drawer Organiser — 5x5 baseplate tile (210 x 210mm)
// Render this file to generate drawer_baseplate_5x5.stl
// Two of these plus one 4x5 tile make the front row of the drawer floor;
// the back row uses the _back variants (see layout.md).

include <_drawer_organiser.scad>

grid_x    = 5;      // cells across (X)
grid_y    = 5;      // cells deep (Y)
interlock = true;   // barbed tabs on +X/+Y, notches on -X/-Y
rear_tabs = true;   // false for the back row of the drawer (see layout.md)

baseplate(grid_x, grid_y, interlock, rear_tabs);
