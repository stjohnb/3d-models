// Scanning Rig - Assembly preview with the setback spacer and boost fitted
// Preview only — print the individual part files.
// Same as scanning_rig_boost_assembly.scad but with scan_setback() straddling
// the dock and the whole boost (and the stand on it) translated setback_shift
// further back, which is exactly what dropping the boost onto the spacer's rail
// does in reality.

include <_scanning_rig.scad>

{
    turntable_base();
    translate([0, 0, base_t + race_clear])
        turntable_platter();
    rig_link();
    scan_setback();

    translate([setback_shift, 0, 0]) {
        scan_boost();

        // See scanning_rig_boost_assembly.scad for the mirror() rationale.
        translate([boost_x0, 0, boost_floor_z])
            rotate([0, -boost_tilt, 0])
                translate([-dock_pocket_x0, 0, -stand_lift])
                    translate([stand_origin_x, stand_w / 2, stand_lift])
                        rotate([90, 0, 0])
                            mirror([1, 0, 0])
                                phone_stand();
    }
}
