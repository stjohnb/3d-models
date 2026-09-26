// Drawer Organiser — 4x5 back-row baseplate tile (168 x 210mm)
// Render this file to generate drawer_baseplate_4x5_back.stl
// Back-row tile: the +Y tabs are omitted so the assembled 10-row grid stays
// exactly 420mm deep and fits the 424mm drawer. The drawer floor now uses
// three 5x5 tiles per row, so this tile is not part of that build; it is kept
// as an optional part for narrower grids (see layout.md).

include <_drawer_organiser.scad>

grid_x    = 4;       // cells across (X)
grid_y    = 5;       // cells deep (Y)
interlock = true;    // barbed tabs on +X, notches on -X/-Y
rear_tabs = false;   // no +Y tabs — this edge is the back of the drawer

baseplate(grid_x, grid_y, interlock, rear_tabs);
