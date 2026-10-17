// Drawer Organiser — 5x5 back-row baseplate tile (210 x 210mm)
// Render this file to generate drawer_baseplate_5x5_back.stl
// Back-row tile: the +Y tabs are omitted so the assembled 10-row grid stays
// exactly 420mm deep and fits the 424mm drawer. Print 3.

include <_drawer_organiser.scad>

grid_x    = 5;       // cells across (X)
grid_y    = 5;       // cells deep (Y)
interlock = true;    // barbed tabs on +X, notches on -X/-Y
rear_tabs = false;   // no +Y tabs — this edge is the back of the drawer

baseplate(grid_x, grid_y, interlock, rear_tabs);
