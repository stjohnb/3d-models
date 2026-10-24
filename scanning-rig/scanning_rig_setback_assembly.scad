// Scanning Rig - Assembly preview with the setback spacer and boost fitted
// Preview only — print the individual part files.
// Same as scanning_rig_assembly.scad but with scan_setback() straddling the rig
// link's rail and the whole boost (and the stand on it) translated
// setback_shift further back, which is exactly what dropping the boost onto the
// spacer's rail does in reality.

include <_scanning_rig.scad>

{
    turntable_base();
    translate([0, 0, base_t + race_clear])
        turntable_platter();
    rig_link();
    scan_setback();

    translate([setback_shift, 0, 0]) {
        scan_boost();

        // Riser dropped into the boost's own pocket — see
        // scanning_rig_assembly.scad for the fit rationale.
        boost_local()
            translate([dock_clear, 0, 0])
                scan_riser();

        // See scanning_rig_assembly.scad for the mirror() rationale.
        boost_local()
            translate([stand_pocket_x, stand_w / 2, riser_h])
                rotate([90, 0, 0])
                    mirror([1, 0, 0])
                        phone_stand();
    }
}
