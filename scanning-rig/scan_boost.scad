// Scanning Rig - Optional camera boost (raises and pitches the phone stand)
// Render this file to generate scan_boost.stl
//
// Authored about the platter axis, in assembled position behind the rig link's
// dock, so CI's mating-pair interference check compares it against
// rig_link.stl where it actually sits. The viewers call geometry.center(), so
// the off-centre origin is invisible there.

include <_scanning_rig.scad>

scan_boost();
