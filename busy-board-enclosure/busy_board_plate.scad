// Busy board enclosure - 3 mm clear polycarbonate front plate
// Render this file to generate busy_board_plate.stl (for viewing only); the
// build exports busy_board_plate.dxf, the play-side cut sheet, from it too.

include <_busy_board_enclosure.scad>

export_dxf = false;   // build: -D export_dxf=true writes the cut-sheet DXF
if (export_dxf) plate_profile(); else busy_board_plate();
