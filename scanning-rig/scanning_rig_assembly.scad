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

    // Link: collar around the base, dock carrying the stand at a fixed distance.
    rig_link();

    // Phone stand dropped into the link's dock, backrest and camera facing the
    // turntable. stand_lift raises the camera to the ~40-45 degree elevation
    // that single-ring scans want.
    // rotate([90, 0, 0]) sends the profile's +Y to +Z and the extrusion to -Y,
    // so the stand_w/2 offset centres it on y = 0. mirror([1, 0, 0]) flips the
    // stand end-for-end so its long rear foot, not the cradle, lands against
    // the dock's front wall — that puts the backrest nearest the turntable, so
    // a phone resting back against it has its camera facing the platter
    // instead of facing away, out over the long foot.
    translate([stand_origin_x, stand_w / 2, stand_lift])
        rotate([90, 0, 0])
            mirror([1, 0, 0])
                phone_stand();
}
