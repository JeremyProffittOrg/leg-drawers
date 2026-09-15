// Table-leg zip-tie drawer set
// Housing and drawers are separate printable parts.
// Housing prints with drawer openings UP (back of housing on the bed).
// Drawers print bottom-down.
// Always sized for a Bambu Lab H2D single-nozzle envelope:
//   320 x 315 x 320 mm (5 mm margin under 325 x 320 x 325).
//
// Customizer: set Part, then Render (F6) and export STL.
// CLI example:
//   openscad -D part='"housing_print"' -D drawer_count=3 -o housing.stl leg-drawers.scad

/* [Part] */
// assembled = in-use pose with drawers and a ghost table leg
// exploded  = housing plus drawers pulled forward
// housing / drawer = in-use orientation (for drawings)
// housing_print / drawer_print = print orientation (export these)
part = "assembled"; // [assembled, exploded, housing, drawer, housing_print, drawer_print, dims]

/* [Drawers] */
drawer_count  = 3;    // [1:8]
drawer_height = 36;   // mm, inner cavity height of each bay
drawer_width  = 110;  // mm, inner cavity width (left-right)
drawer_depth  = 130;  // mm, inner cavity depth (front-back)

/* [Table leg] */
leg_x       = 50;    // mm, leg cross-section along housing width
leg_y       = 50;    // mm, leg cross-section along housing depth
leg_on_left = true;  // true = mount on left of housing, false = right

/* [Top ledges] */
// Raised tray walls on top of the housing. 0 = no wall on that edge.
ledge_left  = 10;
ledge_right = 10;
ledge_back  = 10;
ledge_front = 3;

/* [Structure] */
wall            = 2.4;  // mm, housing walls, bay floors, top plate
drawer_wall     = 2.0;  // mm, drawer side walls
drawer_floor    = 1.6;  // mm, drawer floor
slide_gap       = 0.45; // mm, per-side clearance in the bay
back_gap        = 0.8;  // mm, drawer shorter than cavity so it does not hit the back
leg_clearance   = 0.8;  // mm, per-side pocket clearance around the leg
mount_arm       = 4.5;  // mm, thickness of the zip-tie arms
zip_tie_count   = 0;    // 0 = auto from housing height
zip_slot_w      = 5.0;  // mm, slot length along housing depth (Y)
zip_slot_h      = 8.0;  // mm, slot height (Z); 4.8 mm and 7.6 mm ties pass flat
show_context    = true; // ghost table leg in assembled / exploded views
show_table      = false; // thin table-top slab above the ledges (mounted-under-desk view)

$fn = 28;
eps = 0.08;

// ---- derived ----
cav_w = drawer_width;
cav_h = drawer_height;
cav_d = drawer_depth;

body_w = cav_w + 2 * wall;
body_d = cav_d + wall;
body_h = drawer_count * cav_h + (drawer_count + 1) * wall;

inner_x = leg_x + 2 * leg_clearance;
inner_y = leg_y + 2 * leg_clearance;
mount_x_span = inner_x + mount_arm;
mount_y_span = body_d;

ledge_max = max(max(ledge_left, ledge_right), max(ledge_back, ledge_front));

housing_print_x = body_w + mount_x_span;
housing_print_y = body_h + ledge_max;
housing_print_z = mount_y_span;

dw = cav_w - 2 * slide_gap;
dh = cav_h - slide_gap;
dd = cav_d - back_gap;

drawer_print_x = dw;
drawer_print_y = dd;
drawer_print_z = dh;

H2D_X = 320;
H2D_Y = 315;
H2D_Z = 320;

auto_zips = zip_tie_count > 0
    ? zip_tie_count
    : (body_h < 80 ? 2 : (body_h < 170 ? 3 : 4));

function bay_z(i) = wall + i * (cav_h + wall);

function zip_z(i, n) =
    let (margin = 14,
         span   = body_h - 2 * margin,
         step   = n <= 1 ? 0 : span / (n - 1))
    margin + i * step;

module h2d_guard() {
    assert(housing_print_x <= H2D_X,
        str("housing print X ", housing_print_x, " mm exceeds H2D ", H2D_X, " mm"));
    assert(housing_print_y <= H2D_Y,
        str("housing print Y ", housing_print_y, " mm exceeds H2D ", H2D_Y, " mm"));
    assert(housing_print_z <= H2D_Z,
        str("housing print Z ", housing_print_z, " mm exceeds H2D ", H2D_Z, " mm"));
    assert(drawer_print_x <= H2D_X,
        str("drawer print X ", drawer_print_x, " mm exceeds H2D ", H2D_X, " mm"));
    assert(drawer_print_y <= H2D_Y,
        str("drawer print Y ", drawer_print_y, " mm exceeds H2D ", H2D_Y, " mm"));
    assert(drawer_print_z <= H2D_Z,
        str("drawer print Z ", drawer_print_z, " mm exceeds H2D ", H2D_Z, " mm"));
    assert(dw > 2 * drawer_wall + 8, "drawer too narrow");
    assert(dh > drawer_floor + 8, "drawer too short");
    assert(dd > drawer_wall + 8, "drawer too shallow");
}

module housing_shell() {
    difference() {
        cube([body_w, body_d, body_h]);
        for (i = [0 : drawer_count - 1]) {
            translate([wall, -eps, bay_z(i)])
                cube([cav_w, cav_d + eps, cav_h]);
            // 45-degree flare at the opening so the drawer starts easily.
            // Opening is at y=0, which becomes the top of the print.
            translate([wall, 0, bay_z(i)])
                chamfer_opening(cav_w, cav_h, 1.2);
        }
    }
}

module chamfer_opening(w, h, c) {
    // Triangular prism along the four edges of the front opening.
    translate([0, -eps, 0])
        rotate([0, 0, 0])
            linear_extrude(height = h)
                polygon([[-eps, -eps], [c, -eps], [-eps, c]]);
    translate([w, -eps, 0])
        linear_extrude(height = h)
            polygon([[eps, -eps], [-c, -eps], [eps, c]]);
    translate([0, -eps, 0])
        rotate([0, 90, 0])
            linear_extrude(height = w)
                polygon([[eps, -eps], [-c, -eps], [eps, c]]);
    translate([0, -eps, h])
        rotate([0, 90, 0])
            linear_extrude(height = w)
                polygon([[-eps, -eps], [c, -eps], [-eps, c]]);
}

module ledges() {
    if (ledge_left > 0)
        translate([0, 0, body_h - eps])
            cube([wall, body_d, ledge_left + eps]);
    if (ledge_right > 0)
        translate([body_w - wall, 0, body_h - eps])
            cube([wall, body_d, ledge_right + eps]);
    if (ledge_back > 0)
        translate([0, body_d - wall, body_h - eps])
            cube([body_w, wall, ledge_back + eps]);
    if (ledge_front > 0)
        translate([0, 0, body_h - eps])
            cube([body_w, wall, ledge_front + eps]);
}

module mount_left() {
    // C-channel on the left of the housing, open at the front:
    //   - outer wall (thin in X) spans the full housing depth and height
    //     so it prints as a vertical wall from the bed to the top
    //   - back stop (thin in Y) sits on the bed after the openings-up rotation
    // Slide the channel onto a standing table leg from the front, then
    // zip-tie through the outer-wall windows around the leg.
    ox = -mount_x_span;
    leg_y_min = body_d - mount_arm - inner_y;
    difference() {
        translate([ox, 0, 0])
            cube([mount_arm, body_d, body_h]);
        n = auto_zips;
        slot_y = leg_y_min + inner_y / 2 - zip_slot_w / 2;
        for (i = [0 : n - 1]) {
            translate([ox - eps, slot_y, zip_z(i, n) - zip_slot_h / 2])
                cube([mount_arm + 2 * eps, zip_slot_w, zip_slot_h]);
        }
        // lead-in on the front inner corner of the outer wall
        translate([ox + mount_arm, 0, -eps])
            linear_extrude(height = body_h + 2 * eps)
                polygon([[eps, -eps], [-2.0, -eps], [eps, 2.0]]);
    }
    translate([ox, body_d - mount_arm, 0])
        cube([mount_x_span, mount_arm, body_h]);
}

module mount() {
    if (leg_on_left)
        mount_left();
    else
        translate([body_w, 0, 0])
            mirror([1, 0, 0])
                mount_left();
}

module housing() {
    h2d_guard();
    union() {
        housing_shell();
        ledges();
        mount();
    }
}

module drawer_finger_slot() {
    slot_h = min(8, dh - drawer_floor - 6);
    slot_w = min(42, dw * 0.42);
    if (slot_h >= 5 && slot_w >= 16) {
        zc = dh - 5 - slot_h / 2;
        hull() {
            translate([dw / 2 - slot_w / 2 + slot_h / 2, -eps, zc])
                rotate([-90, 0, 0])
                    cylinder(d = slot_h, h = drawer_wall + 2 * eps);
            translate([dw / 2 + slot_w / 2 - slot_h / 2, -eps, zc])
                rotate([-90, 0, 0])
                    cylinder(d = slot_h, h = drawer_wall + 2 * eps);
        }
    }
}

module drawer() {
    h2d_guard();
    difference() {
        cube([dw, dd, dh]);
        translate([drawer_wall, drawer_wall, drawer_floor])
            cube([
                dw - 2 * drawer_wall,
                dd - drawer_wall + eps,
                dh - drawer_floor + eps
            ]);
        drawer_finger_slot();
        // light chamfer on the outer front top edge for insertion
        translate([-eps, -eps, dh - 1.0])
            cube([dw + 2 * eps, 1.0 + eps, 1.0 + eps]);
    }
}

module drawers_in_place(pull = 18) {
    for (i = [0 : drawer_count - 1]) {
        translate([
            wall + slide_gap,
            -pull,
            bay_z(i) + slide_gap / 2
        ])
            drawer();
    }
}

module ghost_leg() {
    // Ghost of the table leg in the U-pocket, plus a hint of table top.
    gx = inner_x - 2 * leg_clearance;
    gy = inner_y - 2 * leg_clearance;
    gz = body_h + ledge_max + 40;
    xoff = leg_on_left
        ? -inner_x + leg_clearance
        : body_w + leg_clearance;
    yoff = body_d - mount_arm - inner_y + leg_clearance;
    translate([xoff, yoff, -20])
        cube([gx, gy, gz]);
    if (show_table) {
        overhang = 30;
        translate([-overhang, -overhang, body_h + ledge_max + 8])
            cube([body_w + 2 * overhang, body_d + 2 * overhang, 16]);
    }
}

module assembled() {
    h2d_guard();
    color("BurlyWood")
        render(convexity = 12)
            housing();
    color("SteelBlue")
        render(convexity = 8)
            drawers_in_place(22);
    if (show_context) {
        color([0.45, 0.28, 0.16, 0.28])
            ghost_leg();
    }
}

module exploded() {
    h2d_guard();
    color("BurlyWood")
        render(convexity = 12)
            housing();
    for (i = [0 : drawer_count - 1]) {
        translate([
            wall + slide_gap,
            -35 - i * (14),
            bay_z(i) + slide_gap / 2
        ])
            color("SteelBlue")
                render(convexity = 8)
                    drawer();
    }
}

module housing_print() {
    // Openings up: back of housing on the bed, front openings at +Z.
    h2d_guard();
    translate([leg_on_left ? mount_x_span : 0, 0, mount_y_span])
        rotate([-90, 0, 0])
            housing();
}

module drawer_print() {
    h2d_guard();
    drawer();
}

module emit_dims() {
    echo(str("JSON:{",
        "\"body_w\":", body_w, ",",
        "\"body_d\":", body_d, ",",
        "\"body_h\":", body_h, ",",
        "\"mount_x_span\":", mount_x_span, ",",
        "\"mount_y_span\":", mount_y_span, ",",
        "\"housing_print_x\":", housing_print_x, ",",
        "\"housing_print_y\":", housing_print_y, ",",
        "\"housing_print_z\":", housing_print_z, ",",
        "\"drawer_print_x\":", drawer_print_x, ",",
        "\"drawer_print_y\":", drawer_print_y, ",",
        "\"drawer_print_z\":", drawer_print_z, ",",
        "\"dw\":", dw, ",",
        "\"dh\":", dh, ",",
        "\"dd\":", dd, ",",
        "\"auto_zips\":", auto_zips, ",",
        "\"ledge_max\":", ledge_max,
    "}"));
    cube(0.01);
}

if (part == "assembled")
    assembled();
else if (part == "exploded")
    exploded();
else if (part == "housing")
    housing();
else if (part == "drawer")
    drawer();
else if (part == "housing_print")
    housing_print();
else if (part == "drawer_print")
    drawer_print();
else if (part == "dims")
    emit_dims();
else
    assembled();
