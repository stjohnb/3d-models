// =====================================
// Busy board panel and enclosure
// Play-side panel, back tray and screwed battery door for the busy board
// PCB v0.1 (St-John-Software/electronics, hardware/busy-board/,
// docs/busy-board/PCB.md "Mechanical and enclosure"): a toddler's toy, so
// the child-safety rules in docs/busy-board/README.md apply.
// =====================================
// Parts:
//   busy_board_panel        -> busy_board_panel.stl
//       Play-side plate: window over the 7-segment display, windows over
//       both bar graphs and 16 LED holes, all placed from the board; holes
//       for four 24 mm arcade buttons, two panel pots and the EC11 encoder
//       (with anti-rotation lug slots); four PCB bosses and six tray posts
//       carrying M3 heat-set inserts; a locating lip and two cable-tie
//       loops. Every play-side edge, corner and hole edge is rounded.
//   busy_board_tray         -> busy_board_tray.stl
//       Back tray: one cavity behind the panel for the board and the
//       controls, a battery compartment behind the board with a rebated
//       door opening in the floor, six countersunk post screws through the
//       floor (no fixing is reachable from the play side).
//   busy_board_battery_door -> busy_board_battery_door.stl
//       Flat door: two hook tabs at one end, one countersunk M3 screw at
//       the other, so the compartment needs a tool to open.
//
// Orientation: Z-up, print orientation for every part, no supports. The
// panel is modelled outer face down (play face on the bed, bosses and posts
// rising); the tray prints floor down; the door prints outer face down.
//
// Layout frame: front view, X right, Y up, origin at the PCB centre, as
// seen by the child. The panel is mirrored in X by busy_board_panel() so
// its face-down print reads correctly once turned over; the tray is seen
// from the same side as the panel, so it uses the frame directly.
// Board-document coordinates (mm from the board's top-left corner, X right,
// Y DOWN, PCB.md "Layout") convert with bpos().
//
// Every board figure comes from PCB.md. VERIFY marks values that should be
// checked against the delivered parts before the final print.

$fn = 64;

// === Busy board PCB v0.1 (mm) - PCB.md "Mechanical and enclosure" ===
pcb_l         = 100;    // outline along X
pcb_w         = 100;    // outline along Y
pcb_t         = 1.6;    // FR4
pcb_holes     = [[5, 5], [95, 5], [5, 95], [95, 95]];  // M3 centres, board frame
pcb_keepout_r = 3.5;    // copper keepout round each hole: boss d <= 7
pcb_clear     = 0.5;    // board edge to anything, per side
below_pcb     = 3;      // clearance behind the board for the trimmed leads
ds1_c         = [50, 22];       // 4-digit display centre
ds1_body      = [50.4, 19.0];   // body outline
ds1_h         = 8;              // body height above the board front
bg_c          = [[30, 48], [70, 48]];  // bar graph centres
bg_body       = [25.4, 10.2];
bg_h          = 8;
led_c         = [[15, 8], [29, 8], [50, 8], [71, 8], [85, 8],     // D1-D5
                 [92, 28], [92, 48], [92, 68],                     // D6-D8
                 [85, 88], [71, 88], [50, 88], [29, 88], [15, 88], // D9-D13
                 [8, 68], [8, 48], [8, 28]];                       // D14-D16
led_lens_d    = 5;      // 5 mm LED
led_flange_d  = 5.8;    // flange must not pass the panel hole
led_h         = 8.6;    // body height, seated on the board
jst_h         = 10;     // J1-J8 JST-XH housings, bottom edge strip
jst_lead_h    = 15;     // leads leave J1-J8 upward: allow this above the board
j1_bx         = 13.3;   // J1 centre (pin 1 at 12.05, 2 pins at 2.5 mm)
u1_h          = 9;      // socketed MCU
f1_h          = 12;     // radial PTC at (3, 85.5): tallest part bar the connectors
j9_h          = 8.5;    // programming header pins; J9 stays inside the enclosure

// === Panel to board ===
panel_t       = 3;      // play-side plate
pcb_to_panel  = 15;     // panel underside to board front: PCB.md's 15 mm
                        // allowance for the J1-J8 leads, which leave upward
led_raise     = 7;      // ring LEDs stand on 7 mm spacers so their lens tips
                        // just enter the panel holes (printing note; asserted)
led_hole_d    = 5.6;    // lens passes, 5.8 mm flange cannot
window_clear  = 1;      // per side round the display and bar-graph bodies
window_r      = 1.5;
hole_chamfer  = 0.6;    // play-side edge round-off on every hole and window
boss_d        = 7;      // PCB bosses: == 2 * pcb_keepout_r

// === Play-side controls (all panel-mount; the PCB carries no control) ===
row_a_y       = -62;    // knob row: encoder and two pots
row_b_y       = -96;    // button row: timer, B, C, power
encoder       = [0, row_a_y];
pots          = [[-36, row_a_y], [36, row_a_y]];
buttons       = [[-45, row_b_y], [-15, row_b_y], [15, row_b_y], [45, row_b_y]];
button_hole_d = 24.5;   // 24 mm arcade button, panel-nut type
button_bezel_d = 28;    // bezel on the play side (VERIFY)
button_nut_d  = 30;     // nut / body footprint behind the panel (VERIFY)
button_depth  = 34;     // panel underside to microswitch bottom (VERIFY)
button_switch_reach = 20;  // microswitch holder reach from the centre, toward +Y (VERIFY)
pot_hole_d    = 7.4;    // M7 bushing (VERIFY; 9.8 for a 3/8" bushing)
pot_body_d    = 17;     // 16 mm pot body plus clearance
pot_depth     = 22;     // panel underside to the solder lugs (VERIFY)
pot_lug       = true;   // anti-rotation lug slot at 12 o'clock
pot_lug_r     = 8;      // lug centre radius from the shaft (VERIFY)
pot_lug_w     = 1.8;    // slot width (tangential)
pot_lug_l     = 3.6;    // slot length (radial)
enc_hole_d    = 7.4;    // EC11 M7 bushing (VERIFY)
enc_body      = 13;     // body square plus clearance
enc_depth     = 20;     // (VERIFY)
enc_lug       = true;
enc_lug_r     = 6.5;    // (VERIFY)
enc_lug_w     = 1.8;
enc_lug_l     = 3.2;
knob_d        = 20;     // set-screw knobs on the pots and encoder (VERIFY)
tie_loops     = [[-20, -56], [20, -56]];  // cable-tie loops under the panel
tie_loop_l    = 10;
tie_loop_w    = 3;
tie_leg       = 2;
tie_loop_h    = 5;      // clear height under the bar
tie_bar_t     = 2;

// === Enclosure ===
wall          = 2.4;
floor_t       = 4;      // back of the tray; holds the door rebate and countersinks
corner_r      = 6;      // plan-view corner radius, both parts
edge_r        = 2;      // play-face and back-face edge radius
inner_w       = 132;    // cavity width
cav_top       = 56;     // cavity top edge (y) - 6 mm above the board
inner_d       = 38;     // panel underside to floor top: arcade buttons + 4 mm
lip_t         = 1.6;
lip_d         = 4;
lip_clear     = 0.3;
post_r        = 4;      // tray posts hang from the panel, 8 mm across
button_wall_clear = 22; // row B centre to the bottom cavity wall

// === Fixings: M3 heat-set inserts in every boss and post ===
insert_hole_d  = 4.0;   // 4.6 mm OD insert; 2.6 for a self-tapping M3 pilot
insert_depth   = 6;
insert_chamfer = 0.5;
pcb_screw_l    = 6;     // M3 x 6 from the board's back into the panel bosses
tray_screw_l   = 10;    // M3 x 10 countersunk through the floor into the posts
door_screw_l   = 8;     // M3 x 8 countersunk through the door
screw_clear    = 3.4;
screw_head     = 6.8;

// === Battery: 3 x AAA holder with leads, behind the board ===
batt_l        = 53;     // holder outline along X (VERIFY)
batt_w        = 50;     // along Y (VERIFY)
batt_h        = 16;     // thickness (VERIFY)
batt_clear    = 1;
batt_cx       = -10;    // compartment centre, layout frame
batt_cy       = -8;
batt_wall     = 2;
batt_lip      = 1.5;    // retaining lip at the wall tops, both long walls
batt_lip_t    = 1.5;
lead_notch_w  = 6;      // lead slot in the compartment's -Y wall, near J1
door_t        = 2.4;    // door plate; the rebate is this deep
door_flange   = 4;      // door overlap onto the floor, per side
door_flange_screw = 9;  // overlap at the screw end, covering the boss
door_clear    = 0.3;
door_r        = 1.5;
door_tab_x    = 15;     // hook tabs at +/- this x
door_tab_w    = 8;
door_tab_l    = 3;      // reach beyond the door edge
door_tab_t    = 1.2;
lug_depth     = 1.5;    // anti-rotation lug socket depth, from the panel underside
door_boss_d   = 8;

// === Derived ===
function bpos(p) = [p[0] - pcb_l/2, pcb_w/2 - p[1]];   // board frame -> layout frame
cav_bot    = row_b_y - button_wall_clear;
inner_h    = cav_top - cav_bot;
cav_cy     = (cav_top + cav_bot)/2;
outer_w    = inner_w + 2 * wall;
outer_h    = inner_h + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
post_x     = inner_w/2 - lip_clear - post_r;           // fused into the lip
post_y_top = cav_top - lip_clear - post_r;
post_y_bot = cav_bot + lip_clear + post_r;
post_pts   = [[-post_x, post_y_top], [post_x, post_y_top],
              [-post_x, cav_cy], [post_x, cav_cy],
              [-post_x, post_y_bot], [post_x, post_y_bot]];
post_insert_depth = max(insert_depth, tray_screw_l - floor_t + 0.5);
boss_insert_depth = insert_depth;
door_pocket  = door_screw_l - door_t + 0.5;
cs_h         = (screw_head - screw_clear)/2;           // 90 degree countersink depth
batt_il      = batt_l + batt_clear;                    // compartment interior
batt_iw      = batt_w + batt_clear;
batt_wall_h  = door_t + batt_h + batt_clear - floor_t + batt_lip_t;  // above the floor top
door_boss_off = batt_iw/2 + door_boss_d/2 + 0.2;       // boss centre from the compartment centre
door_boss_h  = door_t + door_pocket + 2 - floor_t;      // above the floor top
reb_w        = batt_il + 2 * door_flange;
reb_y0       = -batt_iw/2 - door_flange;
reb_y1       = batt_iw/2 + door_flange_screw;
lead_notch_x = -batt_il/2 + 6;                         // compartment frame, -X end of the -Y wall
led_tip      = led_h + led_raise;                      // lens tip above the board front
pcb_back     = pcb_to_panel + pcb_t;                   // panel underside to board back
led_y_min    = min([for (c = led_c) bpos(c)[1]]);
// Distance from point p to the rectangle of size sz centred on c (0 inside).
function rect_gap(p, c, sz) =
    norm([max(0, abs(p[0] - c[0]) - sz[0]/2), max(0, abs(p[1] - c[1]) - sz[1]/2)]);

// --- Board behind the panel ---
assert(pcb_to_panel >= jst_h + 2 && pcb_to_panel >= jst_lead_h,
       "pcb_to_panel must clear the JST-XH housings and their upward leads");
assert(pcb_to_panel >= max(u1_h, f1_h, j9_h) + 1, "pcb_to_panel must clear U1, F1 and J9");
assert(pcb_to_panel >= max(ds1_h, bg_h), "display bodies press on the panel");
assert(led_tip >= pcb_to_panel - 2 && led_tip <= pcb_to_panel + panel_t - 1,
       "raised LED lenses must reach the panel holes but never stand proud of the face");
assert(led_hole_d > led_lens_d + 0.3 && led_hole_d < led_flange_d,
       "LED hole must pass the lens and stop the flange");
assert(boss_d <= 2 * pcb_keepout_r, "PCB bosses intrude on the 3.5 mm hole keepout");
for (c = led_c, h = pcb_holes)
    assert(norm(c - h) >= boss_d/2 + led_hole_d/2 + 1, "an LED hole runs into a PCB boss");
for (c = led_c, w = concat([[ds1_c, ds1_body]], [for (g = bg_c) [g, bg_body]]))
    assert(rect_gap(c, w[0], w[1] + 2 * [window_clear, window_clear]) >= led_hole_d/2 + 0.5,
           "an LED hole runs into a display window: lower window_clear");
assert(pcb_l/2 + pcb_clear <= inner_w/2 - lip_clear - lip_t, "board wider than the cavity");
assert(pcb_w/2 + pcb_clear <= cav_top - lip_clear - lip_t, "board runs into the top lip");

// --- Controls ---
assert(button_depth + 2 <= inner_d && pot_depth + 2 <= inner_d && enc_depth + 2 <= inner_d,
       "a control is deeper than the cavity");
assert(row_a_y + max(pot_body_d, enc_body)/2 + 1 <= -pcb_w/2 - pcb_clear,
       "knob-row bodies overlap the board: lower row_a_y");
assert(row_a_y + knob_d/2 + 2 <= led_y_min - led_hole_d/2,
       "knobs run into the bottom LED row");
assert(row_a_y - pot_body_d/2 - 1 >= row_b_y + button_switch_reach,
       "button microswitch holders hit the pot bodies: lower row_b_y");
assert(row_a_y - row_b_y >= button_bezel_d/2 + knob_d/2 + 2, "button bezels touch the knobs");
for (b = buttons) {
    assert(abs(b[0]) + button_nut_d/2 + 1 <= inner_w/2 - lip_clear - lip_t,
           "a button nut runs into the side wall");
    assert(b[1] - button_nut_d/2 - 1 >= cav_bot + lip_clear + lip_t,
           "a button nut runs into the bottom wall");
    assert(abs(b[0]) + button_bezel_d/2 <= outer_w/2 - corner_r,
           "a button bezel runs onto the rounded panel corner");
    for (p = post_pts)
        assert(norm(b - p) >= post_r + button_nut_d/2 + 1, "a button hits a tray post");
}
for (q = concat(pots, [encoder]), p = post_pts)
    assert(norm(q - p) >= post_r + max(pot_body_d, enc_body)/2 + 1, "a pot or the encoder hits a tray post");
assert(abs(pots[0][0]) - knob_d/2 >= enc_body/2 + 2
       && abs(pots[1][0]) - knob_d/2 >= enc_body/2 + 2, "pot knobs touch the encoder");
assert(pot_lug_r - pot_lug_l/2 > pot_hole_d/2 + 0.5 && enc_lug_r - enc_lug_l/2 > enc_hole_d/2 + 0.5,
       "lug slots break into the bushing holes");
for (t = tie_loops)
    assert(t[1] + tie_loop_w/2 + 1 <= -pcb_w/2 - pcb_clear, "a tie loop sits over the board");

// --- Battery compartment ---
assert(floor_t + batt_wall_h + 0.5 <= floor_t + inner_d - pcb_back - below_pcb,
       "battery compartment walls reach the board's solder side");
assert(abs(batt_cx) + batt_il/2 + batt_wall <= inner_w/2 - lip_clear - lip_t - 1
       && batt_cy - batt_iw/2 - batt_wall >= cav_bot + lip_clear + lip_t + 1
       && batt_cy + door_boss_off + door_boss_d/2 <= cav_top - lip_clear - lip_t - 1,
       "battery compartment runs into the cavity walls");
for (p = post_pts)
    assert(abs(p[0] - batt_cx) > reb_w/2 + post_r + 1
           || p[1] < batt_cy + reb_y0 - post_r - 1 || p[1] > batt_cy + reb_y1 + post_r + 1,
           "a post screw lands in the door rebate");
assert(lug_depth <= panel_t - 1, "lug sockets break the play face");
assert(abs(batt_cx + lead_notch_x - bpos([j1_bx, 0])[0]) <= 10, "lead notch too far from J1");
assert(door_t < floor_t, "door must be thinner than the floor");
assert(door_tab_t + 0.4 <= floor_t - door_t, "hook tabs too thick for the floor");
assert(door_flange_screw >= door_boss_off - batt_iw/2 + door_boss_d/2,
       "door flange does not cover the screw boss");
assert(door_tab_x + door_tab_w/2 + door_clear <= batt_il/2, "hook tabs run off the door");
assert(batt_lip < batt_il/2 && batt_lip_t <= batt_wall_h - 2, "battery lips oversize");

// --- Fixings and edges ---
assert(insert_hole_d >= 2.4 && insert_hole_d <= min(boss_d, 2 * post_r, door_boss_d) - 2.5,
       "insert_hole_d must leave a wall in every boss and post");
assert(pcb_screw_l - pcb_t <= boss_insert_depth, "PCB screws bottom out in the bosses");
assert(boss_insert_depth <= pcb_to_panel + panel_t - 1.2, "PCB boss pockets break the play face");
assert(tray_screw_l - floor_t <= post_insert_depth - 0.5, "tray screws bottom out in the posts");
assert(post_insert_depth <= inner_d - 2, "post pockets too deep");
assert(door_screw_l - door_t <= door_pocket, "door screw bottoms out");
assert(cs_h < floor_t && cs_h + 0.6 <= door_t, "floor or door too thin for the countersink");
assert(edge_r < corner_r && edge_r <= panel_t - 0.8 && hole_chamfer < panel_t - 1,
       "edge radii must fit the plate");
assert(tie_loop_h + tie_bar_t < pcb_to_panel, "tie loops reach the board");

// === Modules ===

// Rounded-rect vertical prism: hull of four corner cylinders.
// Centred on X/Y, base at z=0.
module rbox(w, l, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - r), sy * (l/2 - r), 0])
                cylinder(r = r, h = h);
}

// Corner post for rounded_slab: radius rc in plan, its z=0 rim rounded to
// re. The lowest 45 degrees of the round are replaced by a chamfer so the
// edge prints on the bed without a drooping first layer.
module edge_post(rc, re, h) {
    rotate_extrude()
        polygon(concat(
            [[0, 0], [rc - 2 * re * (1 - cos(45)), 0]],
            [for (a = [-45 : 5 : 0]) [rc - re + re * cos(a), re + re * sin(a)]],
            [[rc, h], [0, h]]));
}

// Rounded-rect slab with its z=0 face edges rounded: the play face of the
// panel and the back face of the tray. Centred on X/Y, base at z=0.
module rounded_slab(w, l, h, rc, re) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - rc), sy * (l/2 - rc), 0])
                edge_post(rc, re, h);
}

// Heat-set insert pocket: blind hole running along -Z from its mouth at
// z=0, with an entry chamfer.
module insert_hole(depth) {
    translate([0, 0, -depth]) cylinder(d = insert_hole_d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = insert_hole_d, d2 = insert_hole_d + 2 * insert_chamfer,
                 h = insert_chamfer + 0.01);
}

// Through hole along Z from z=-1 past h, with a chamfer on the z=0 face.
module chamfered_hole(d, h) {
    translate([0, 0, -1]) cylinder(d = d, h = h + 2);
    translate([0, 0, -0.01])
        cylinder(d1 = d + 2 * hole_chamfer, d2 = d, h = hole_chamfer);
}

// Rounded-rect window along Z from z=-1 past h, chamfered on the z=0 face.
module chamfered_window(w, l, r, h) {
    translate([0, 0, -1]) rbox(w, l, h + 2, r);
    translate([0, 0, -0.01]) hull() {
        rbox(w + 2 * hole_chamfer, l + 2 * hole_chamfer, 0.01, r + hole_chamfer);
        translate([0, 0, hole_chamfer]) rbox(w, l, 0.01, r);
    }
}

// Anti-rotation lug slot at 12 o'clock, radial length l, width w.
// Blind socket cut from the panel underside so the play face stays unbroken.
module lug_slot(r_lug, w, l, h) {
    translate([-w/2, r_lug - l/2, h - lug_depth]) cube([w, l, lug_depth + 1]);
}

// Countersunk M3 through hole: shank from z=-1, 90 degree head cone at z=0.
module csk_hole(t) {
    translate([0, 0, -1]) cylinder(d = screw_clear, h = t + 2);
    translate([0, 0, -0.01]) cylinder(d1 = screw_head, d2 = screw_clear, h = cs_h);
}

module post_positions() {
    for (p = post_pts) translate([p[0], p[1], 0]) children();
}

module hole_positions() {
    for (p = pcb_holes) translate(bpos(p)) children();
}

// Cable-tie loop: a bridge along X standing on z=0.
module tie_loop() {
    for (sx = [-1, 1])
        translate([sx * (tie_loop_l/2 - tie_leg/2) - tie_leg/2, -tie_loop_w/2, 0])
            cube([tie_leg, tie_loop_w, tie_loop_h + tie_bar_t]);
    translate([-tie_loop_l/2, -tie_loop_w/2, tie_loop_h])
        cube([tie_loop_l, tie_loop_w, tie_bar_t]);
}

// Panel in the layout frame: play face at z=0, features rising toward +Z.
module panel_frame() {
    difference() {
        union() {
            translate([0, cav_cy, 0])
                rounded_slab(outer_w, outer_h, panel_t, corner_r, edge_r);
            translate([0, 0, panel_t - 0.01]) {
                // Locating lip inside the tray walls
                translate([0, cav_cy, 0]) difference() {
                    rbox(inner_w - 2 * lip_clear, inner_h - 2 * lip_clear,
                         lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        rbox(inner_w - 2 * (lip_clear + lip_t),
                             inner_h - 2 * (lip_clear + lip_t), lip_d + 3,
                             max(0.5, inner_r - lip_clear - lip_t));
                }
                // Tray posts, down to the floor
                post_positions() cylinder(r = post_r, h = inner_d + 0.01);
                // PCB bosses: the board front sits pcb_to_panel behind the panel
                hole_positions() cylinder(d = boss_d, h = pcb_to_panel + 0.01);
                for (t = tie_loops) translate([t[0], t[1], 0]) tie_loop();
            }
        }
        // Inserts at the post and boss tips
        post_positions()
            translate([0, 0, panel_t + inner_d]) insert_hole(post_insert_depth);
        hole_positions()
            translate([0, 0, panel_t + pcb_to_panel]) insert_hole(boss_insert_depth);
        // Display and bar-graph windows, LED holes: all from the board
        translate(bpos(ds1_c))
            chamfered_window(ds1_body[0] + 2 * window_clear,
                             ds1_body[1] + 2 * window_clear, window_r, panel_t);
        for (c = bg_c) translate(bpos(c))
            chamfered_window(bg_body[0] + 2 * window_clear,
                             bg_body[1] + 2 * window_clear, window_r, panel_t);
        for (c = led_c) translate(bpos(c)) chamfered_hole(led_hole_d, panel_t);
        // Controls
        for (b = buttons) translate(b) chamfered_hole(button_hole_d, panel_t);
        for (p = pots) translate(p) {
            chamfered_hole(pot_hole_d, panel_t);
            if (pot_lug) lug_slot(pot_lug_r, pot_lug_w, pot_lug_l, panel_t);
        }
        translate(encoder) {
            chamfered_hole(enc_hole_d, panel_t);
            if (enc_lug) lug_slot(enc_lug_r, enc_lug_w, enc_lug_l, panel_t);
        }
    }
}

// Panel in print orientation: play face on the bed. Mirrored so the layout
// reads correctly from the front once the printed panel is turned over.
module busy_board_panel() {
    mirror([1, 0, 0]) panel_frame();
}

// Battery compartment walls on the floor top (z=0 here), in the
// compartment's own frame, with retaining lips, the lead notch and the
// door-screw boss merged into the +Y wall.
module battery_compartment() {
    difference() {
        union() {
            difference() {
                translate([-batt_il/2 - batt_wall, -batt_iw/2 - batt_wall, 0])
                    cube([batt_il + 2 * batt_wall, batt_iw + 2 * batt_wall, batt_wall_h]);
                translate([-batt_il/2, -batt_iw/2, -1])
                    cube([batt_il, batt_iw, batt_wall_h + 2]);
            }
            // Lips along both long (X) walls, 45 degree underside
            for (sy = [-1, 1])
                translate([-batt_il/2 + 2, sy * batt_iw/2, batt_wall_h - batt_lip_t])
                    rotate([90, 0, 90]) linear_extrude(batt_il - 4)
                        polygon([[0, 0], [0, batt_lip_t], [-sy * batt_lip, batt_lip_t]]);
            translate([0, door_boss_off, 0]) cylinder(d = door_boss_d, h = door_boss_h);
        }
        // Lead notch through the -Y wall, full height
        translate([lead_notch_x - lead_notch_w/2, -batt_iw/2 - batt_wall - 1, -1])
            cube([lead_notch_w, batt_wall + batt_lip + 2, batt_wall_h + 3]);
    }
}

// Door opening, rebate, hook slots and screw pocket, cut from the tray in
// the compartment's frame with the floor's outer face at z=0.
module battery_door_cuts() {
    translate([-batt_il/2, -batt_iw/2, -1]) cube([batt_il, batt_iw, floor_t + 2]);
    translate([0, (reb_y0 + reb_y1)/2, -1]) rbox(reb_w, reb_y1 - reb_y0, door_t + 1, door_r);
    for (sx = [-1, 1])
        translate([sx * door_tab_x - door_tab_w/2 - door_clear,
                   reb_y0 - door_tab_l - door_clear, door_t])
            cube([door_tab_w + 2 * door_clear,
                  door_tab_l + door_clear + door_flange + 0.01, floor_t - door_t + 0.01]);
    translate([0, door_boss_off, door_t]) mirror([0, 0, 1]) insert_hole(door_pocket);
}

// Back tray: floor at z=0, opening toward +Z.
module busy_board_tray() {
    difference() {
        union() {
            difference() {
                translate([0, cav_cy, 0])
                    rounded_slab(outer_w, outer_h, floor_t + inner_d, corner_r, edge_r);
                translate([0, cav_cy, floor_t]) rbox(inner_w, inner_h, inner_d + 1, inner_r);
            }
            translate([batt_cx, batt_cy, floor_t - 0.01]) battery_compartment();
        }
        // Post screws, countersunk on the back face
        post_positions() csk_hole(floor_t);
        translate([batt_cx, batt_cy, 0]) battery_door_cuts();
    }
}

// Battery door in print orientation: outer face at z=0, tabs rising.
module busy_board_battery_door() {
    dw = reb_w - 2 * door_clear;
    y0 = reb_y0 + door_clear;
    y1 = reb_y1 - door_clear;
    difference() {
        union() {
            translate([0, (y0 + y1)/2, 0])
                rbox(dw, y1 - y0, door_t, max(0.5, door_r - door_clear));
            for (sx = [-1, 1])
                translate([sx * door_tab_x - door_tab_w/2, y0 - door_tab_l, door_t - 0.01])
                    cube([door_tab_w, door_tab_l + door_flange - 2 * door_clear,
                          door_tab_t + 0.01]);
        }
        translate([0, door_boss_off, 0]) csk_hole(door_t);
    }
}
