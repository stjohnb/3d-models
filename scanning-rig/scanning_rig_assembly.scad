// Scanning Rig - Assembly preview
// Shows the turntable assembled with the phone stand aimed at it.
// Preview only — print the individual part files.
//
// The link's collar and rail carry no stand pocket of their own (#468), so the
// scan boost is always fitted: it is the rig's only stand mount. The riser
// then drops into the boost's own pocket and re-presents it riser_h higher —
// the camera-elevation correction (#468 review) — without changing the boost.

include <_scanning_rig.scad>

{
    turntable_base();

    // Platter dropped over the spindle. The race_clear lift is a display gap
    // so the coincident faces don't z-fight in the preview; in use the platter
    // sits down on the base plate's flat top.
    translate([0, 0, base_t + race_clear])
        turntable_platter();

    // Link: collar keyed around the base, rail carrying the boost at a fixed
    // distance.
    rig_link();
    scan_boost();

    // Riser dropped into the boost's own pocket, seat spur flush with its
    // floor — the same fit the phone stand's foot has with the boost alone.
    boost_local()
        translate([dock_clear, 0, 0])
            scan_riser();

    // Phone stand dropped into the riser's tilted pocket, riser_h above the
    // boost's own, backrest and camera facing the turntable.
    // rotate([90, 0, 0]) sends the profile's +Y to +Z and the extrusion to -Y,
    // so the stand_w/2 offset centres it on y = 0. mirror([1, 0, 0]) flips the
    // stand end-for-end so its long rear foot, not the cradle, lands against
    // the pocket's front wall — that puts the backrest nearest the turntable,
    // so a phone resting back against it has its camera facing the platter
    // instead of facing away, out over the long foot.
    boost_local()
        translate([stand_pocket_x, stand_w / 2, riser_h])
            rotate([90, 0, 0])
                mirror([1, 0, 0])
                    phone_stand();
}
