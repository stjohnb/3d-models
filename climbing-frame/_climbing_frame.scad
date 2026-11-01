// =====================================
// Garden climbing frame — scale model
// Kids' climbing frame for the garden: a cuboid post-and-rail frame with a
// platform strip at one end joining a ladder to a slide, two cross beams near
// the centre carrying a swing each and doubling as monkey-bar rails, a boarded
// climbing wall up to the deck on the X = 0 end and a rope net on the X = frame_x
// end. All figures below are real millimetres at finished planed (PAR) timber
// sizes; scale_denominator divides everything at the end (20 = 1:20).
// =====================================
// Parts:
//   climbing_frame    -> climbing_frame.stl     posts, rails, beams, rungs, deck, ladder, braces,
//                                                climbing wall, net bearer
//   climbing_slide    -> climbing_slide.stl     chute, exported chute-underside down
//   climbing_swing    -> climbing_swing.stl     seat, chain rods, hanger bar; print two
//   climbing_net      -> climbing_net.stl       rope net lattice, exported flat; print once
//   climbing_assembly -> climbing_assembly.stl  viewing aid, not a printable part
//   climbing_frame_aframe, climbing_net_aframe, climbing_assembly_aframe -> the same three
//                     with aframe_end = true: raked legs and an apex tie at the X = frame_x end,
//                     a trapezoid net; they pair with each other, not with the cube frame
//
// Frame: X along the 2.61 m edge, Y along the frame_depth edge, Z up. Origin at
// ground level at the slide-end corner of the front edge (Y = 0). The slide
// leaves Y = 0 towards -Y; the ladder leaves Y = frame_y towards +Y.

$fn = 64;

scale_denominator = 20;
s = 1 / scale_denominator;

// Customizer parameters
slide_run     = 2400;   // horizontal projection of the chute, mm
ladder_angle  = 75;     // lean from horizontal, degrees
frame_depth   = 2000;   // Y extent of the frame, 1500..2500
post_size     = 94;     // finished square section of posts and square rails
corner_radius = 5;      // eased long edges on posts and rails; 0 for sharp
beam_depth    = 145;    // depth of the on-edge members (cross beams, divider and far side rails)
rung_count    = 6;      // monkey-bar rungs between the cross beams
rung_pitch    = 300;    // monkey-bar rung spacing along X, mm; 265 mm gaps clear the 89-230 head-entrapment band
knee_braces   = true;   // 44 x 94 braces from each corner post to its side top rail
climbing_wall = true;   // boarded climbing wall with holds on the X = 0 end
hold_count    = 9;      // climbing holds on the wall, 0..12
end_net       = true;   // rope net and its ground bearer on the X = frame_x end
bearer_z      = 150;    // underside of the net bearer above ground, mm
net_width     = 1500;   // Y extent of the rope net, centred on the frame depth
net_mesh      = 300;    // rope net mesh pitch, mm; keep the real net at 250..300
show_ground   = true;   // assembly only: ground slab with the buried post stubs below it

// Library switch, not a customizer parameter: the *_aframe renderables set it true after
// their include. Replaces the X = frame_x posts with two raked legs meeting under the beam
// ends, ties their tops, drops the far side rail, the far knee braces and the far halves of
// the front and rear top rails, and makes the net a trapezoid laced into the A.
aframe_end    = false;

// Envelope (real mm)
// Slide bay: bought 3 m wave slides for a 1.5 m deck are 480-506 mm wide at the top (Koala Play 480,
// DIY Play 485, Play Away Days 491, KBT and Big Game Hunters 495, Caledonia Play 500, Garden Games
// and Active Garden 506); 520 clear leaves at least 7 mm a side for all of them.
slide_opening   = 520;   // clear X between the corner post and the divider post
swing_bay_clear = 1809;  // clear X between the divider rail face and the far rail face
frame_y = frame_depth;  frame_h = 2300;
divider_c = post_size / 2 + post_size + slide_opening;   // centreline of the slide-bay divider posts
divider_x0 = divider_c - post_size / 2;
divider_x1 = divider_c + post_size / 2;
frame_x = divider_x1 + swing_bay_clear + post_size;
deck_z = 1500;  deck_x = divider_x0;   // deck top height; deck spans X 0..deck_x, Y 0..frame_y
rail_z0 = frame_h - post_size;         // underside of the square top rails
beam_z0 = frame_h - beam_depth;        // underside of the on-edge members
post_bury = 700;                       // concreted length below ground (assembly only)
ground_t = 50;                         // ground slab thickness (assembly only)
ground_margin = 300;                   // slab overhang past the slide and ladder feet

// Timber sections (finished mm)
stile_w = 44;  stile_d = 94;           // ladder stiles, 44 across the ladder, 94 in the climb direction
brace_t = 44;  brace_d = 94;           // knee braces
joist_w = 45;  joist_d = 95;           // deck joists, along Y
board_t = 27;  board_w = 120;  board_gap = 5;   // decking boards, along X
board_pitch = board_w + board_gap;

// Print-size features (printed mm x scale_denominator) so they survive a scale change
rung_d   = 1.75 * scale_denominator;   // 35 mm at 1:20, ladder and monkey-bar rungs
chain_d  = 2.4 * scale_denominator;
seat_t   = 2.0 * scale_denominator;
slide_t  = 2.0 * scale_denominator;
cheek_t  = 1.6 * scale_denominator;
hanger_h = 3.0 * scale_denominator;
rope_d   = 1.4 * scale_denominator;    // 28 mm at 1:20; the real rope is 16 mm, exaggerated to print
eps = 1;
big = 1e5;

// Cross beams along X across the swing bay, Y centrelines as fractions of the depth
beam_frac = [0.35, 0.65];
beam_y = [for (f = beam_frac) f * frame_y];
beam_w = post_size;                    // beams are post_size wide, beam_depth deep

// Monkey bars between the two beams: first rung ~150 mm clear of the divider rail
monkey_rung_start = divider_x1 + 150 + rung_d / 2;
monkey_rung_z = frame_h - 50;
max_rungs = floor((frame_x - post_size - rung_d - monkey_rung_start) / rung_pitch) + 1;
assert(monkey_rung_start + (rung_count - 1) * rung_pitch <= frame_x - post_size - rung_d,
       str("monkey-bar rungs overrun the far side rail: at rung_pitch ", rung_pitch, " use at most ", max_rungs, " rungs"));

// Ladder: ladder_x0 centred in the slide opening, ladder_w wide, foot on the ground at ladder_foot_y, top at the deck's rear edge
ladder_w = 500;  ladder_rung_pitch = 250;
ladder_x0 = post_size + (slide_opening - ladder_w) / 2;
ladder_foot_y = frame_y + deck_z / tan(ladder_angle);
stile_l = deck_z / sin(ladder_angle);

// Slide: slide_x0 centred in the slide opening, slide_w wide, top edge at (Y = 0, Z = deck_z), foot at Y = -slide_run on the ground
slide_w = 500;  cheek_h = 150;
slide_x0 = post_size + (slide_opening - slide_w) / 2;
slide_angle = atan(deck_z / slide_run);
slide_l = sqrt(deck_z * deck_z + slide_run * slide_run);

// Swings: one per cross beam, chain plane on the beam centreline, hung from the beam underside
swing_x = [divider_x1 + 528, divider_x1 + 1203];
seat_w = 440;  seat_d = 200;  seat_z = 500;   // seat top height
swing_top_z = beam_z0;                        // top of the hanger bar / beam underside

// Knee braces: 45 degrees in the Y-Z plane, foot on the post at brace_post_z
brace_post_z = 1900;
brace_l = 700;                                // overlength, clipped to the post face and rail underside

// Climbing wall: 44 x 94 boards along Y on the outside of the X = 0 posts (X -44..0),
// stacked from wall_base_z while each board's top stays at or below the deck top.
wall_board_t = 44;  wall_board_w = 94;  wall_base_z = 100;  wall_gap = 6;
wall_pitch = wall_board_w + wall_gap;
wall_board_count = floor((deck_z - wall_base_z - wall_board_w) / wall_pitch) + 1;
wall_stile_w = 44;  wall_stile_d = 94;        // mid stile behind the boards, 44 along X
hold_w = 80;  hold_h = 60;  hold_t = 40;  hold_r = 10;   // hold: Y, Z, proud of the boards, eased corners
// Hold [Y, Z] positions at frame_depth 2000; Y scales with frame_depth / 2000.
hold_xy = [[400, 350], [1250, 420], [700, 700], [1600, 650], [300, 1000], [1000, 1050],
           [1800, 1000], [600, 1300], [1400, 1350], [900, 450], [1700, 1300], [500, 1150]];
assert(hold_count <= len(hold_xy), str("hold_count must be at most ", len(hold_xy)));

// A-frame end: legs rise from the X = frame_x ground corners to under the cross-beam ends.
// Rake is in the Y-Z plane, derived so a deeper frame gets a flatter A on its own.
rake = atan((beam_y[0] - post_size / 2) / beam_z0);
leg_a0 = -(post_bury / cos(rake) + post_size);   // axial start below ground, clipped per use
leg_l = beam_z0 / cos(rake) + 2 * post_size - leg_a0;
tie_z0 = beam_z0 - post_size;                    // apex tie underside
// Y of the front leg's inner (+Y) face at height z; the rear leg mirrors about frame_y / 2.
function leg_inner_y(z) = post_size / 2 + z * tan(rake) + post_size / (2 * cos(rake));
tie_y0 = leg_inner_y(tie_z0);                    // widest point of the tie's gap, so it reaches both legs

// Rope net on the X = frame_x end: tied to a bearer between the far posts, hung from the far side rail.
net_foot = bearer_z + post_size;              // bearer top, the lowest horizontal rope
net_y0 = (frame_y - net_width) / 2;
net_y1 = net_y0 + net_width;
// The A-frame net ignores net_width (its manifests drop it), so a 1500 mm deep A-frame
// must not trip on the cube net's default width.
assert(aframe_end || net_width <= frame_y - 2 * post_size,
       str("net_width must be at most ", frame_y - 2 * post_size, " to fit between the far-end posts"));

module box(x0, x1, y0, y1, z0, z1) { translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]); }
module clip(x0, x1, y0, y1, z0, z1) { intersection() { children(); box(x0, x1, y0, y1, z0, z1); } }

// Planed member along +Z: cross-section w (X) by d (Y), length l, long edges eased by corner_radius.
module member_z(w, d, l) {
    linear_extrude(l)
        if (corner_radius > 0) offset(r = corner_radius) offset(delta = -corner_radius) square([w, d]);
        else square([w, d]);
}
// Axis-aligned planed member filling the box x0..x1, y0..y1, z0..z1; long axis chosen from the box.
module member(x0, x1, y0, y1, z0, z1) {
    dx = x1 - x0;  dy = y1 - y0;  dz = z1 - z0;
    if (dx >= dy && dx >= dz)
        translate([x0, y0, z1]) rotate([0, 90, 0]) member_z(dz, dy, dx);
    else if (dy >= dz)
        translate([x0, y1, z0]) rotate([90, 0, 0]) member_z(dx, dz, dy);
    else
        translate([x0, y0, z0]) member_z(dx, dy, dz);
}

post_xs = aframe_end ? [0, divider_x0] : [0, divider_x0, frame_x - post_size];
post_ys = [0, frame_y - post_size];
corner_xs = [0, frame_x - post_size];

module posts() {
    for (x = post_xs, y = post_ys) member(x, x + post_size, y, y + post_size, 0, frame_h);
}
module rails() {
    rail_x1 = aframe_end ? divider_x1 : frame_x;                                        // stop at the divider in the A variant
    for (y = post_ys) member(0, rail_x1, y, y + post_size, rail_z0, frame_h);          // front, rear
    member(0, post_size, 0, frame_y, rail_z0, frame_h);                                 // near side
    if (!aframe_end) member(frame_x - post_size, frame_x, 0, frame_y, beam_z0, frame_h); // far side, on edge
    member(divider_x0, divider_x1, 0, frame_y, beam_z0, frame_h);                       // divider rail, on edge
}
module cross_beams() {
    for (y = beam_y) member(divider_x0, frame_x, y - beam_w / 2, y + beam_w / 2, beam_z0, frame_h);
}
module monkey_bars() {
    y0 = beam_y[0] + beam_w / 2 - eps;
    y1 = beam_y[1] - beam_w / 2 + eps;
    for (i = [0 : rung_count - 1])
        translate([monkey_rung_start + i * rung_pitch, y0, monkey_rung_z])
            rotate([-90, 0, 0]) cylinder(d = rung_d, h = y1 - y0);
}
module deck() {
    n_boards = floor((frame_y + board_gap) / board_pitch);
    for (i = [0 : n_boards - 1])
        box(0, deck_x, i * board_pitch, i * board_pitch + board_w, deck_z - board_t, deck_z);
    joist_xs = [post_size, (post_size + deck_x - joist_w) / 2, deck_x - joist_w];
    for (x = joist_xs) box(x, x + joist_w, 0, frame_y, deck_z - board_t - joist_d, deck_z - board_t);
}

// Knee brace from the front post at the side rail whose underside is rail_under, centred on xc.
// Mirrored about the frame's Y midplane for the rear post.
module knee_brace_front(xc, rail_under) {
    clip(xc - brace_t / 2, xc + brace_t / 2, post_size, big, -big, rail_under)
        translate([xc - brace_t / 2, post_size, brace_post_z]) rotate([-45, 0, 0])
            translate([0, 0, -brace_d]) cube([brace_t, brace_d, brace_l + brace_d]);  // runs back into the post, cut flush by the clip
}
module braces() {
    for (x = aframe_end ? [0] : corner_xs) {
        under = (x == 0) ? rail_z0 : beam_z0;
        knee_brace_front(x + post_size / 2, under);
        translate([0, frame_y, 0]) mirror([0, 1, 0]) knee_brace_front(x + post_size / 2, under);
    }
}

// Ladder in its own frame: foot at the origin, stiles along +Z, rungs along X.
// Stiles are stile_d deep centred on y = 0 so the top straddles the deck's rear edge.
module ladder_local() {
    for (x = [0, ladder_w - stile_w])
        translate([x, -stile_d / 2, 0]) cube([stile_w, stile_d, stile_l]);
    for (z = [ladder_rung_pitch : ladder_rung_pitch : stile_l - ladder_rung_pitch / 2])
        translate([stile_w - eps, 0, z]) rotate([0, 90, 0])
            cylinder(d = rung_d, h = ladder_w - 2 * stile_w + 2 * eps);
}
// Leaning -Y as it climbs; cut flush with the ground and the deck top.
module ladder() {
    clip(-big, big, -big, big, 0, deck_z)
        translate([ladder_x0, ladder_foot_y, 0]) rotate([90 - ladder_angle, 0, 0]) ladder_local();
}
// Climbing wall
function board_centre_z(i) = wall_base_z + i * wall_pitch + wall_board_w / 2;
// A hold whose height would cross a board gap snaps to the nearest board centre.
function hold_z(z) = let(i = floor((z - wall_base_z) / wall_pitch),
                         lo = wall_base_z + i * wall_pitch + hold_h / 2,
                         hi = wall_base_z + i * wall_pitch + wall_board_w - hold_h / 2)
    (z >= lo && z <= hi) ? z
    : board_centre_z(min(wall_board_count - 1, max(0, round((z - wall_base_z - wall_board_w / 2) / wall_pitch))));

// Block filling x0..x1 whose Y-Z profile has its corners eased by r.
module rounded_block_x(x0, x1, y0, y1, z0, z1, r) {
    translate([x0, y0, z0]) rotate([90, 0, 90]) linear_extrude(x1 - x0)
        offset(r = r) offset(delta = -r) square([y1 - y0, z1 - z0]);
}
module wall_boards() {
    for (i = [0 : wall_board_count - 1]) {
        z0 = wall_base_z + i * wall_pitch;
        box(-wall_board_t, 0, 0, frame_y, z0, z0 + wall_board_w);
    }
}
// Stands on the ground behind the boards, up to the deck boards' underside.
module wall_stile() {
    box(0, wall_stile_w, frame_y / 2 - wall_stile_d / 2, frame_y / 2 + wall_stile_d / 2, 0, deck_z - board_t);
}
module wall_holds() {
    if (hold_count > 0)
        for (i = [0 : hold_count - 1]) {
            y = hold_xy[i][0] * frame_y / 2000;
            z = hold_z(hold_xy[i][1]);
            rounded_block_x(-wall_board_t - hold_t, -wall_board_t,
                            y - hold_w / 2, y + hold_w / 2, z - hold_h / 2, z + hold_h / 2, hold_r);
        }
}
module wall() { wall_boards(); wall_stile(); wall_holds(); }

// A-frame legs. Front leg: foot centred on (frame_x - post_size / 2, post_size / 2) on the ground,
// top centred under the front beam; overlength along its axis and clipped by the caller so the
// foot is flat on the ground and the top is a horizontal cut the beam bears on. The rear leg
// mirrors it about frame_y / 2 (beam_frac is symmetric).
module leg_front() {
    translate([frame_x - post_size, post_size / 2, 0]) rotate([-rake, 0, 0])
        translate([0, -post_size / 2, leg_a0]) member_z(post_size, post_size, leg_l);
}
module legs_clipped(z0, z1) {
    clip(-big, big, -big, big, z0, z1) leg_front();
    clip(-big, big, -big, big, z0, z1) translate([0, frame_y, 0]) mirror([0, 1, 0]) leg_front();
}
module legs() { legs_clipped(0, beam_z0); }
// Apex tie between the legs' inner faces, just under the beams; replaces the far side rail.
module apex_tie() {
    member(frame_x - post_size, frame_x, tie_y0, frame_y - tie_y0, tie_z0, beam_z0);
}

// Rope net
// Bearer between the far posts, or between the legs' inner faces at its underside in the A variant.
module net_bearer() {
    y0 = aframe_end ? leg_inner_y(bearer_z) : post_size;
    member(frame_x - post_size, frame_x, y0, frame_y - y0, bearer_z, bearer_z + post_size);
}
// Net in its print frame: lattice flat on z = 0, local X = frame Y, local Y = frame Z.
// Verticals at net_mesh from the near edge, plus a closing rope on the far edge when the
// pitch misses it, running from the bottom rope's underside to just past the far side
// rail's eased lower edge so the assembly union overlaps the bearer and rail by volume.
module net_print() {
    if (aframe_end) net_print_aframe(); else net_print_cube();
}
module net_print_cube() {
    v0 = net_foot - rope_d / 2;
    v1 = beam_z0 + corner_radius + eps;
    vert_ys = [for (y = [net_y0 : net_mesh : net_y1 + eps]) y];
    ys = (net_y1 - vert_ys[len(vert_ys) - 1] > eps) ? concat(vert_ys, [net_y1]) : vert_ys;
    for (y = ys) translate([y, v0, rope_d / 2]) rotate([-90, 0, 0]) cylinder(d = rope_d, h = v1 - v0);
    for (z = [net_foot : net_mesh : beam_z0 - eps])
        translate([net_y0, z, rope_d / 2]) rotate([0, 90, 0]) cylinder(d = rope_d, h = net_y1 - net_y0);
}
// A-frame net: a trapezoid filling the A between the bearer top and the tie underside. Rows every
// net_mesh run leg face to leg face at their height (a row within half a mesh of the tie is
// dropped: the tie is the top rope); columns every net_mesh straddle frame_y / 2 and run from the
// bottom rope up to the leg face or just past the tie underside, kept only when they cross at
// least two rows; two border rods lie along the leg faces so the lattice prints as one piece.
// Built as the rectangular lattice intersected with the A's inside outline, plus the borders.
module net_print_aframe() {
    v0 = net_foot - rope_d / 2;
    v1 = tie_z0 + corner_radius + eps;
    y_lim = leg_inner_y(net_foot + net_mesh);
    col_ys = [for (y = [frame_y / 2 + net_mesh / 2 : net_mesh : frame_y - y_lim]) each [y, frame_y - y]];
    intersection() {
        union() {
            for (y = col_ys) translate([y, v0, rope_d / 2]) rotate([-90, 0, 0]) cylinder(d = rope_d, h = v1 - v0);
            for (z = [net_foot : net_mesh : tie_z0 - net_mesh / 2])
                translate([0, z, rope_d / 2]) rotate([0, 90, 0]) cylinder(d = rope_d, h = frame_y);
        }
        linear_extrude(rope_d)
            polygon([[leg_inner_y(v0 - eps), v0 - eps], [frame_y - leg_inner_y(v0 - eps), v0 - eps],
                     [frame_y - leg_inner_y(v1), v1], [leg_inner_y(v1), v1]]);
    }
    net_border_front(v0, v1);
    translate([frame_y, 0, 0]) mirror([1, 0, 0]) net_border_front(v0, v1);
}
// Border rod centred on the front leg's inner-face line from local y = v0 to v1, ends cut square.
module net_border_front(v0, v1) {
    clip(-big, big, v0, v1, -big, big)
        translate([leg_inner_y(v0), v0, rope_d / 2]) rotate([0, 0, -rake]) rotate([-90, 0, 0])
            cylinder(d = rope_d, h = (v1 - v0) / cos(rake));
}
// Real position: standing on the outside of the X = frame_x face, eps into it; in the A variant
// centred in the leg plane, where the rods overlap the legs, bearer and tie by volume.
module net_real() {
    net_x = aframe_end ? frame_x - post_size / 2 - rope_d / 2 : frame_x - eps;
    translate([net_x, 0, 0]) rotate([90, 0, 90]) net_print();
}

module frame_real() {
    posts(); rails();
    if (aframe_end) { legs(); apex_tie(); } cross_beams(); monkey_bars(); deck(); ladder();
    if (knee_braces) braces();
    if (climbing_wall) wall();
    if (end_net) net_bearer();
}

// Slide in its own frame: chute along -Y from the top edge at the origin, bed top on z = 0.
module slide_local() {
    translate([0, -slide_l, -slide_t]) cube([slide_w, slide_l, slide_t]);
    for (x = [0, slide_w - cheek_t])
        translate([x, -slide_l, -slide_t]) cube([cheek_t, slide_l, slide_t + cheek_h]);
}
// Real position: top edge on the deck's front edge, falling to the ground at Y = -slide_run;
// clipped to Y <= 0 so the top end mates flat against the deck, and to Z >= 0 for a flat foot.
module slide_real() {
    clip(-big, big, -big, 0, 0, big)
        translate([slide_x0, 0, deck_z]) rotate([slide_angle, 0, 0]) slide_local();
}
// Print orientation: chute underside flat on the bed, running along +Y.
module slide_print() {
    translate([0, slide_l, slide_t]) rotate([-slide_angle, 0, 0]) translate([-slide_x0, 0, -deck_z]) slide_real();
}

// Swing in its own frame: seat centred on x = 0, chain plane at y = 0 with the seat
// extending +Y so the whole part lies flat on its back for printing.
module swing_real() {
    translate([-seat_w / 2, -chain_d / 2, seat_z - seat_t]) cube([seat_w, seat_d, seat_t]);
    for (x = [-1, 1] * (seat_w - chain_d) / 2)
        translate([x, 0, seat_z - seat_t]) cylinder(d = chain_d, h = swing_top_z - hanger_h - seat_z + seat_t + eps);
    translate([-seat_w / 2, -chain_d / 2, swing_top_z - hanger_h]) cube([seat_w, chain_d, hanger_h + eps]);  // eps up into the beam
}
// Print orientation: on its back, chains and hanger on the bed, seat standing as a fin.
module swing_print() { translate([0, swing_top_z, chain_d / 2]) rotate([90, 0, 0]) swing_real(); }

// Ground slab with the concreted post stubs below it (viewing aid only).
module ground() {
    box(-ground_margin, frame_x + ground_margin,
        -slide_run - ground_margin, ladder_foot_y + ground_margin, -ground_t, 0);
    for (x = post_xs, y = post_ys) member(x, x + post_size, y, y + post_size, -post_bury, eps);
    if (aframe_end) legs_clipped(-post_bury, eps);
}

module climbing_assembly_real() {
    frame_real();
    translate([0, eps, 0]) slide_real();   // eps into the deck edge so the union is solid
    for (i = [0, 1]) translate([swing_x[i], beam_y[i], 0]) swing_real();
    if (end_net) net_real();
    if (show_ground) ground();
}
