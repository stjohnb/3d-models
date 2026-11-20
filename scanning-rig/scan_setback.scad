// Scanning Rig - Optional setback spacer (moves the scan boost further back)
// Render this file to generate scan_setback.stl
//
// Authored about the platter axis, in assembled position straddling the rig
// link's rail, so CI's mating-pair interference check compares it against
// rig_link.stl where it actually sits. The viewers call geometry.center(), so
// the off-centre origin is invisible there.

include <_scanning_rig.scad>

scan_setback();
