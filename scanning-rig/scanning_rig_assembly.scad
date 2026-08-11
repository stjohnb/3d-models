// Scanning Rig - Assembly preview
// Shows the turntable assembled with the phone stand aimed at it.
// Preview only — print the individual part files.

include <_scanning_rig.scad>

{
    turntable_base();

    // Platter dropped over the spindle. The race_clear lift is a display gap
    // so the coincident faces don't z-fight in the preview; in use the platter
    // sits down on the base plate's flat top.
    translate([0, 0, base_t + race_clear])
        turntable_platter();

    // Phone stand stood upright, lip and camera facing the turntable.
    // rotate([90, 0, 0]) sends the profile's +Y to +Z and the extrusion to -Y,
    // so the stand_w/2 offset centres it on y = 0.
    translate([base_d / 2 + 70, stand_w / 2, 0])
        rotate([90, 0, 0])
            phone_stand();
}
