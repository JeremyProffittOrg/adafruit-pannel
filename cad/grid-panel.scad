// Modular 1.00 in control-panel grid.
// Print with the countersink face on the bed. No supports.
// Parts: strip_1x4 strip_2x4 strip_3x4 strip_4x4 strip_5x4
//        join_bar
//        adapter_4991 adapter_5295 adapter_5752 adapter_6310
//        faceplate_4991 faceplate_5295 faceplate_5752 faceplate_6310

/* [Part] */
PART = "strip_1x4"; // ["strip_1x4","strip_2x4","strip_3x4","strip_4x4","strip_5x4","join_bar","adapter_4991","adapter_5295","adapter_5752","adapter_6310","faceplate_4991","faceplate_5295","faceplate_5752","faceplate_6310"]

PITCH = 25.4;
THICK = 4.0;
HOLE = 3.3;          // M3 clearance
CSINK_D = 6.5;
CSINK_H = 1.8;
CHAMFER = 0.5;
CORNER_R = 1.6;
TONGUE_W = 8.0;
TONGUE_T = 2.0;
TONGUE_OUT = 2.0;
TONGUE_CLEAR = 0.25;
$fn = 28;

module rounded_rect(w, h, r) {
    if (r <= 0) square([w, h], center = true);
    else hull() {
        translate([ w/2 - r,  h/2 - r]) circle(r = r);
        translate([-w/2 + r,  h/2 - r]) circle(r = r);
        translate([ w/2 - r, -h/2 + r]) circle(r = r);
        translate([-w/2 + r, -h/2 + r]) circle(r = r);
    }
}

module countersunk_hole() {
    union() {
        cylinder(h = THICK + 2, d = HOLE, center = true);
        translate([0, 0, -THICK/2 - 0.01])
            cylinder(h = CSINK_H + 0.01, d1 = CSINK_D, d2 = HOLE);
        translate([0, 0, THICK/2 - CHAMFER + 0.01])
            cylinder(h = CHAMFER, d1 = HOLE, d2 = HOLE + 2 * CHAMFER);
    }
}

module tongue_groove(nx, ny, w, h) {
    // Tongues on +X and +Y (bottom 2 mm). Grooves on -X and -Y.
    for (iy = [0:ny-1]) {
        y = -h/2 + (iy + 0.5) * PITCH;
        translate([w/2 + TONGUE_OUT/2, y, -THICK/2 + TONGUE_T/2])
            cube([TONGUE_OUT, TONGUE_W, TONGUE_T], center = true);
        translate([-w/2 + TONGUE_OUT/2, y, -THICK/2 + TONGUE_T/2])
            cube([TONGUE_OUT + TONGUE_CLEAR, TONGUE_W + 2*TONGUE_CLEAR, TONGUE_T + 0.2], center = true);
    }
    for (ix = [0:nx-1]) {
        x = -w/2 + (ix + 0.5) * PITCH;
        translate([x, h/2 + TONGUE_OUT/2, -THICK/2 + TONGUE_T/2])
            cube([TONGUE_W, TONGUE_OUT, TONGUE_T], center = true);
        translate([x, -h/2 + TONGUE_OUT/2, -THICK/2 + TONGUE_T/2])
            cube([TONGUE_W + 2*TONGUE_CLEAR, TONGUE_OUT + TONGUE_CLEAR, TONGUE_T + 0.2], center = true);
    }
}

module strip(nx, ny) {
    w = nx * PITCH;
    h = ny * PITCH;
    difference() {
        union() {
            translate([0, 0, 0])
                linear_extrude(height = THICK, center = true)
                    rounded_rect(w, h, CORNER_R);
            // +X +Y tongues (solid)
            for (iy = [0:ny-1]) {
                y = -h/2 + (iy + 0.5) * PITCH;
                translate([w/2 + TONGUE_OUT/2 - 0.01, y, -THICK/2 + TONGUE_T/2])
                    cube([TONGUE_OUT, TONGUE_W, TONGUE_T], center = true);
            }
            for (ix = [0:nx-1]) {
                x = -w/2 + (ix + 0.5) * PITCH;
                translate([x, h/2 + TONGUE_OUT/2 - 0.01, -THICK/2 + TONGUE_T/2])
                    cube([TONGUE_W, TONGUE_OUT, TONGUE_T], center = true);
            }
        }
        // 1 in grid of M3 holes, cell centers
        for (ix = [0:nx-1], iy = [0:ny-1]) {
            x = -w/2 + (ix + 0.5) * PITCH;
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([x, y, 0]) countersunk_hole();
        }
        // -X -Y grooves
        for (iy = [0:ny-1]) {
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([-w/2 + (TONGUE_OUT + TONGUE_CLEAR)/2 - 0.01, y, -THICK/2 + TONGUE_T/2])
                cube([TONGUE_OUT + TONGUE_CLEAR, TONGUE_W + 2*TONGUE_CLEAR, TONGUE_T + 0.3], center = true);
        }
        for (ix = [0:nx-1]) {
            x = -w/2 + (ix + 0.5) * PITCH;
            translate([x, -h/2 + (TONGUE_OUT + TONGUE_CLEAR)/2 - 0.01, -THICK/2 + TONGUE_T/2])
                cube([TONGUE_W + 2*TONGUE_CLEAR, TONGUE_OUT + TONGUE_CLEAR, TONGUE_T + 0.3], center = true);
        }
    }
}

module join_bar() {
    // Two-hole bar that sits under a seam. 25.4 mm pitch.
    bw = 12;
    bl = 40;
    bt = 3.0;
    difference() {
        linear_extrude(height = bt, center = true)
            rounded_rect(bl, bw, 1.2);
        for (s = [-1, 1])
            translate([s * PITCH/2, 0, 0]) {
                cylinder(h = bt + 2, d = HOLE, center = true);
                translate([0, 0, -bt/2 - 0.01])
                    cylinder(h = 1.2, d1 = 6.2, d2 = HOLE);
            }
    }
}

module m3_clear(h=4) {
    cylinder(h = h + 2, d = HOLE, center = true);
}

module m25_clear(h=4) {
    cylinder(h = h + 2, d = 2.7, center = true); // M2.5 clearance
}

// Adapter plates sit on the 1 in standoffs. Board screws into the M2.5 holes.
module adapter_plate(nx, ny, thick=2.4) {
    w = nx * PITCH;
    h = ny * PITCH;
    linear_extrude(height = thick, center = true)
        rounded_rect(w, h, 1.2);
}

module adapter_4991() {
    // 1x2 cell so two M3 standoffs stop rotation. Board is 1 in square.
    nx = 1; ny = 2; t = 2.4;
    w = nx * PITCH; h = ny * PITCH;
    difference() {
        adapter_plate(nx, ny, t);
        for (iy = [0:ny-1]) {
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([0, y, 0]) m3_clear(t);
        }
        // Board origin at lower-left of the lower cell, offset so board is centered on lower cell.
        // Lower cell center is (0, -PITCH/2). Board LL is center - 12.7.
        bx = -12.7;
        by = -PITCH/2 - 12.7;
        for (p = [[2.54,2.54],[22.86,2.54],[2.54,22.86],[22.86,22.86]])
            translate([bx + p[0], by + p[1], 0]) m25_clear(t);
        // cable window under STEMMA QT (left/right of board)
        translate([0, -PITCH/2, 0]) cube([12, 8, t+2], center = true);
    }
}

module adapter_5295() {
    // 1x4, board 76.2 x 21.59 centered.
    nx = 1; ny = 4; t = 2.4;
    w = nx * PITCH; h = ny * PITCH;
    difference() {
        adapter_plate(nx, ny, t);
        for (iy = [0:ny-1]) {
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([0, y, 0]) m3_clear(t);
        }
        for (p = [[19.05,8.255],[-19.05,8.255],[19.05,-8.255],[-19.05,-8.255]])
            // board long axis along Y (the 4 in length)
            translate([p[1], p[0], 0]) m25_clear(t);
        // QT cable window
        translate([0, 0, 0]) cube([10, 20, t+2], center = true);
    }
}

module adapter_5752() {
    adapter_5295(); // same outline and mounting holes
}

module adapter_6310() {
    nx = 2; ny = 2; t = 2.4;
    w = nx * PITCH; h = ny * PITCH;
    difference() {
        adapter_plate(nx, ny, t);
        for (ix = [0:nx-1], iy = [0:ny-1]) {
            x = -w/2 + (ix + 0.5) * PITCH;
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([x, y, 0]) m3_clear(t);
        }
        for (p = [[15.24,17.78],[-15.24,17.78],[15.24,-17.78],[-15.24,-17.78]])
            translate([p[0], p[1], 0]) m25_clear(t);
        // leave the 4 mm encoder posts clear
        for (p = [[0,15],[0,-15],[15,0],[-15,0]])
            translate([p[0], p[1], 0]) cylinder(h = t+2, d = 4.4, center = true);
        translate([0, 0, 0]) cube([16, 10, t+2], center = true);
    }
}

module faceplate_blank(nx, ny, t=2.6) {
    w = nx * PITCH; h = ny * PITCH;
    difference() {
        linear_extrude(height = t, center = true)
            rounded_rect(w, h, 1.2);
        for (ix = [0:nx-1], iy = [0:ny-1]) {
            x = -w/2 + (ix + 0.5) * PITCH;
            y = -h/2 + (iy + 0.5) * PITCH;
            translate([x, y, 0]) cylinder(h = t+2, d = HOLE, center = true);
        }
    }
}

module faceplate_4991() {
    nx = 1; ny = 2; t = 2.6;
    w = nx * PITCH; h = ny * PITCH;
    difference() {
        faceplate_blank(nx, ny, t);
        // shaft over lower cell
        translate([0, -PITCH/2, 0]) cylinder(h = t+2, d = 7.5, center = true);
    }
}

module faceplate_5295() {
    nx = 1; ny = 4; t = 2.6;
    difference() {
        faceplate_blank(nx, ny, t);
        // slider slot along length
        cube([4.0, 75.0, t+2], center = true);
    }
}

module faceplate_5752() {
    nx = 1; ny = 4; t = 2.6;
    difference() {
        faceplate_blank(nx, ny, t);
        for (y = [-28.575, -9.525, 9.525, 28.575])
            translate([0, y, 0]) cylinder(h = t+2, d = 7.5, center = true);
    }
}

module faceplate_6310() {
    nx = 2; ny = 2; t = 2.6;
    difference() {
        faceplate_blank(nx, ny, t);
        cylinder(h = t+2, d = 22.0, center = true);
    }
}

if (PART == "strip_1x4") strip(1, 4);
else if (PART == "strip_2x4") strip(2, 4);
else if (PART == "strip_3x4") strip(3, 4);
else if (PART == "strip_4x4") strip(4, 4);
else if (PART == "strip_5x4") strip(5, 4);
else if (PART == "join_bar") join_bar();
else if (PART == "adapter_4991") adapter_4991();
else if (PART == "adapter_5295") adapter_5295();
else if (PART == "adapter_5752") adapter_5752();
else if (PART == "adapter_6310") adapter_6310();
else if (PART == "faceplate_4991") faceplate_4991();
else if (PART == "faceplate_5295") faceplate_5295();
else if (PART == "faceplate_5752") faceplate_5752();
else if (PART == "faceplate_6310") faceplate_6310();
else strip(1, 4);
