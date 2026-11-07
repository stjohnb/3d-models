// Busy board enclosure - v2 clear front plate (board_v3 off); the build
// exports busy_board_plate_v2.dxf, v2's cut sheet, from it too.

include <_busy_board_enclosure.scad>

board_v3 = false;     // v2.0 board, 222 mm square
export_dxf = false;   // build: -D export_dxf=true writes the cut-sheet DXF
if (export_dxf) plate_profile(); else busy_board_plate();
