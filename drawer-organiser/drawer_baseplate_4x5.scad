// Drawer Organiser — 4x5 baseplate tile (168 x 210mm)
// Render this file to generate drawer_baseplate_4x5.stl
// One of these fills the last column of the front row of the drawer floor
// (see layout.md).

include <_drawer_organiser.scad>

grid_x    = 4;      // cells across (X)
grid_y    = 5;      // cells deep (Y)
interlock = true;   // barbed tabs on +X/+Y, notches on -X/-Y
rear_tabs = true;   // false for the back row of the drawer (see layout.md)

baseplate(grid_x, grid_y, interlock, rear_tabs);
