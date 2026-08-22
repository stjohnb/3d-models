// Scanning Rig - Assembly preview with the optional camera boost fitted
// Preview only — print the individual part files.
// Same as scanning_rig_assembly.scad but with scan_boost() behind the dock and
// the phone stand lifted onto it: the inner translate/rotate pair maps the
// stand from the dock's own pocket front onto the boost's pocket front,
// boost_setback further back, pivoting about the pocket's front edge.

include <_scanning_rig.scad>

{
    turntable_base();
    translate([0, 0, base_t + race_clear])
        turntable_platter();
    rig_link();
    scan_boost();

    // mirror([1, 0, 0]) flips the stand end-for-end so its long rear foot,
    // not the cradle, lands against the dock's front wall — see stand_origin_x
    // in _scanning_rig.scad. That puts the backrest nearest the turntable, so
    // a phone resting back against it has its camera facing the platter
    // instead of facing away, out over the long foot.
    translate([boost_x0, 0, boost_floor_z])
        rotate([0, -boost_tilt, 0])
            translate([-dock_pocket_x0, 0, -stand_lift])
                translate([stand_origin_x, stand_w / 2, stand_lift])
                    rotate([90, 0, 0])
                        mirror([1, 0, 0])
                            phone_stand();
}
