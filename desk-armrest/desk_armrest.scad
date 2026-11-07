// =====================================
// Desk Armrest
// Clip-on elbow rest for a standing desk. Slides onto the tabletop edge.
// Authored in its mounted orientation (Z-up); no viewer rotation applied.
// Y = 0 is the desk edge: the tabletop sits in -Y inside the mouth, the arm
// reaches +Y. X is the width, centred on 0. The jaw underside is Z = 0.
// One YZ profile extruded along X, so it prints on its side with no supports.
// =====================================

$fn = 64;

// ---- Parameters (mm) ----
desk_t        = 19.37; // tabletop thickness
fit_clearance = 0.3;   // printed-part allowance added to the mouth gap
reach         = 130;   // arm length out from the desk edge (+Y)
width         = 90;    // pad width (X)
over_desk     = 40;    // top plate depth over the tabletop
under_desk    = 70;    // lower jaw depth under the tabletop
pad_t         = 8;     // top plate thickness
jaw_t         = 8;     // lower jaw thickness
spine_t       = 10;    // spine thickness at the desk edge
arm_root_t    = 24;    // arm thickness at the spine
arm_tip_t     = 10;    // arm thickness at the tip
lead_in       = 3;     // mouth chamfer
edge_r        = 2;     // convex profile corner radius

// ---- Derived ----
gap        = desk_t + fit_clearance;
z_jaw_top  = jaw_t;
z_desk_top = jaw_t + gap;
z_top      = z_desk_top + pad_t;

assert(desk_t > 0, "desk_t must be positive");
assert(fit_clearance >= 0, "fit_clearance must not be negative");
assert(reach > spine_t, "reach must exceed spine_t");
assert(arm_tip_t <= arm_root_t, "arm must not widen toward the tip");
assert(arm_root_t < z_top, "arm_root_t must be below the top surface");
assert(lead_in < jaw_t && lead_in < pad_t, "lead_in must be thinner than jaw and pad");
assert(lead_in < under_desk && lead_in < over_desk, "lead_in must be shorter than jaw and plate");
assert(2 * edge_r < min(jaw_t, pad_t, arm_tip_t, spine_t), "edge_r too large for thinnest section");

profile_points = [
    [-under_desk, 0],
    [spine_t, 0],
    [spine_t, z_top - arm_root_t],
    [reach, z_top - arm_tip_t],
    [reach, z_top],
    [-over_desk, z_top],
    [-over_desk, z_desk_top + lead_in],
    [-over_desk + lead_in, z_desk_top],
    [0, z_desk_top],
    [0, z_jaw_top],
    [-under_desk + lead_in, z_jaw_top],
    [-under_desk, z_jaw_top - lead_in]
];

module armrest_profile() {
    offset(r = edge_r) offset(delta = -edge_r) polygon(profile_points);
}

module desk_armrest() {
    rotate([90, 0, 90]) linear_extrude(height = width, center = true) armrest_profile();
}

desk_armrest();
