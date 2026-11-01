// Scanning Rig - Generic leaning phone stand
// Render this file to generate phone_stand.stl
//
// No rotate([-90, 0, 0]) here: the stand is an extruded side profile whose
// "up" is already +Y, so the STL is simultaneously in print orientation and
// upright in the Y-up Three.js viewer.

include <_scanning_rig.scad>

phone_stand();
