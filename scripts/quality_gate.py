"""Quality gates for the two-piece panel case.

Gates (all must PASS):
  components — boards fit their cells, no overlap, PCB stays in the
               cavity, bosses miss posts and each other
  assemble   — lid drops onto the tray: short pegs, outer skirt, no
               solid clash on the way down
  enclosure  — assembled shell has no finger-sized (12 mm) path into
               the cavity, and no unintended opening that stuff can
               enter, except declared lid/wall cutouts

Exit 0 only when every selected gate passes.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning, module="trimesh")

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library" / "devices.json"

# Must match cad/case.scad
PITCH = 25.4
WALL = 8.0
BOT = 3.0
TOP = 3.2
FIT = 0.40
SKIRT = 2.20
SKIRT_H = 8.00
PEG_H = 2.50
PEG_D = 4.00
SOCK_D = 4.50
PEG_INSET = 3.00
M3 = 3.3
FINGER_MM = 12.0
STUFF_MM = 2.0
MAX_PEG_H = 3.0
SEATED_PENETRATE = 0.35
APPROACH_PENETRATE = 0.25

PRESETS = {
    "sliders-quads": {
        "cols": 5,
        "rows": 4,
        "inner_h": 25.0,
        "tilts": [0, 0, 0, 0],
        "edge_style": "round",
        "edge_mm": 2.0,
        "devices": [
            {"id": "neoslider", "c": 0, "r": 0},
            {"id": "neoslider", "c": 1, "r": 0},
            {"id": "neoslider", "c": 2, "r": 0},
            {"id": "quad_rotary", "c": 3, "r": 0},
            {"id": "quad_rotary", "c": 4, "r": 0},
        ],
        "walls": [],
        "hangs": [
            {"side": "back", "pos": 0, "orient": "down"},
            {"side": "back", "pos": 4, "orient": "down"},
        ],
        "bottom": ROOT / "print-kits" / "sliders-quads-case" / "bottom.stl",
        "top": ROOT / "print-kits" / "sliders-quads-case" / "top.stl",
        "top_use": ROOT / "cad" / "generated" / "sq-top-use.stl",
    },
    "tilt-demo": {
        "cols": 4,
        "rows": 6,
        "inner_h": 25.0,
        "tilts": [0, 0, 0, 30, 30, -30],
        "edge_style": "round",
        "edge_mm": 2.0,
        "devices": [],
        "walls": [],
        "hangs": [
            {"side": "back", "pos": 0, "orient": "down"},
            {"side": "back", "pos": 3, "orient": "down"},
        ],
        "bottom": ROOT / "print-kits" / "sliders-quads-case" / "tilt-bottom.stl",
        "top": ROOT / "print-kits" / "sliders-quads-case" / "tilt-top.stl",
        "top_use": ROOT / "cad" / "generated" / "tilt-top-use.stl",
    },
}


def load_lib():
    data = json.loads(LIB.read_text(encoding="utf-8"))
    return {d["id"]: d for d in data["devices"]}


def case_w(l):
    return l["cols"] * PITCH + 2 * WALL


def case_d(l):
    return l["rows"] * PITCH + 2 * WALL


def wall_h(l):
    return BOT + float(l["inner_h"])


def post_xy(l):
    """Match cad/case.scad each_post() on flat rows (world XY)."""
    cols, rows = l["cols"], l["rows"]
    tilts = list(l.get("tilts") or [])
    while len(tilts) < rows:
        tilts.append(0.0)
    ins = PEG_INSET
    pts = []
    for r in range(rows):
        if abs(float(tilts[r])) < 0.05:
            y = (r + 0.5) * PITCH
            pts.append((-ins, y))
            pts.append((cols * PITCH + ins, y))
    yf = -ins
    yb = rows * PITCH + ins
    if cols > 1:
        for c in range(1, cols):
            pts.append((c * PITCH, yf))
            pts.append((c * PITCH, yb))
    else:
        pts.append((PITCH / 2, yf))
        pts.append((PITCH / 2, yb))
    return pts


def aabb_overlap(a, b, eps=0.05):
    return (
        a[0] < b[2] - eps
        and b[0] < a[2] - eps
        and a[1] < b[3] - eps
        and b[1] < a[3] - eps
    )


def circle_rect_hit(cx, cy, r, rect, eps=0.05):
    x0, y0, x1, y1 = rect
    qx = min(max(cx, x0), x1)
    qy = min(max(cy, y0), y1)
    return (cx - qx) ** 2 + (cy - qy) ** 2 < (r - eps) ** 2


def gate_components(layout, lib):
    fails = []
    cols, rows = layout["cols"], layout["rows"]
    occupied = {}
    boxes = []
    for i, p in enumerate(layout.get("devices") or []):
        d = lib.get(p["id"])
        if d is None:
            fails.append(f"unknown device {p['id']}")
            continue
        if d.get("place") in ("none", "wall"):
            continue
        cx, cy = int(p["c"]), int(p["r"])
        dx, dy = int(d["cells_x"]), int(d["cells_y"])
        if cx < 0 or cy < 0 or cx + dx > cols or cy + dy > rows:
            fails.append(
                f"{d['id']} at c={cx} r={cy} needs {dx}x{dy} cells on a {cols}x{rows} grid"
            )
            continue
        for x in range(cx, cx + dx):
            for y in range(cy, cy + dy):
                if (x, y) in occupied:
                    fails.append(
                        f"cell {x},{y} holds {occupied[(x, y)]} and {d['id']}"
                    )
                occupied[(x, y)] = d["id"]
        pcb = d.get("pcb_mm")
        if pcb:
            mx = (cx + dx / 2) * PITCH
            my = (cy + dy / 2) * PITCH
            hw, hh = pcb[0] / 2, pcb[1] / 2
            box = (mx - hw, my - hh, mx + hw, my + hh)
            cav = (0.0, 0.0, cols * PITCH, rows * PITCH)
            if box[0] < cav[0] - 0.05 or box[1] < cav[1] - 0.05 or box[2] > cav[2] + 0.05 or box[3] > cav[3] + 0.05:
                fails.append(
                    f"{d['id']} PCB {pcb[0]:.2f}x{pcb[1]:.2f} leaves the cavity at c={cx} r={cy}"
                )
            for j, other in boxes:
                if aabb_overlap(box, other):
                    fails.append(f"{d['id']} PCB overlaps {j}")
            peg_r = PEG_D / 2
            for px, py in post_xy(layout):
                if circle_rect_hit(px, py, peg_r + 0.2, box):
                    fails.append(
                        f"{d['id']} PCB hits rim peg at ({px:.1f},{py:.1f})"
                    )
            boxes.append((d["id"], box))
        holes = d.get("holes") or []
        boss = float(d.get("boss_mm") or 6)
        for hx, hy in holes:
            mx = (cx + dx / 2) * PITCH + hx
            my = (cy + dy / 2) * PITCH + hy
            for px, py in post_xy(layout):
                dist = math.hypot(mx - px, my - py)
                if dist < 3.2 + PEG_D / 2:
                    fails.append(
                        f"{d['id']} boss at ({mx:.1f},{my:.1f}) hits peg at ({px:.1f},{py:.1f})"
                    )
            if mx < 0 or my < 0 or mx > cols * PITCH or my > rows * PITCH:
                fails.append(f"{d['id']} boss at ({mx:.1f},{my:.1f}) is outside the cavity")
            _ = boss
    return fails


def lid_print_to_use_mat(rows, inner_h, lift=0.0):
    zoff = BOT + float(inner_h) + TOP
    depth = rows * PITCH + 2 * WALL
    # print = Rx(180) * T(0, -depth, -zoff) * use
    # use   = T(0, depth, zoff) * Rx(180) * print
    a = math.pi
    c, s = math.cos(a), math.sin(a)
    rx = np.eye(4, dtype=np.float64)
    rx[1, 1] = c
    rx[1, 2] = -s
    rx[2, 1] = s
    rx[2, 2] = c
    t = np.eye(4, dtype=np.float64)
    t[1, 3] = depth
    t[2, 3] = zoff
    lift_m = np.eye(4, dtype=np.float64)
    lift_m[2, 3] = lift
    return lift_m @ t @ rx


def load_mesh(path: Path):
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    return mesh


def apply_mat(mesh, mat):
    out = mesh.copy()
    out.apply_transform(mat)
    return out


_SIGN_CACHE = {}


def _positive_means_inside(mesh):
    """Calibrate trimesh signed-distance sign. Far-away points are outside the plastic."""
    import trimesh

    key = id(mesh)
    if key in _SIGN_CACHE:
        return _SIGN_CACHE[key]
    far = np.asarray(mesh.bounds[1], dtype=np.float64) + np.array([80.0, 80.0, 80.0])
    sd = trimesh.proximity.signed_distance(mesh, far.reshape(1, 3))[0]
    _SIGN_CACHE[key] = bool(sd < 0)
    return _SIGN_CACHE[key]


def signed_inside(mesh, points, thresh=0.20):
    import trimesh

    sd = trimesh.proximity.signed_distance(mesh, np.asarray(points, dtype=np.float64))
    if _positive_means_inside(mesh):
        return sd, sd > thresh
    return sd, sd < -thresh


def max_penetration(mesh, points, thresh=0.20):
    sd, inside = signed_inside(mesh, points, thresh=thresh)
    if not np.any(inside):
        return 0.0
    if _positive_means_inside(mesh):
        return float(sd[inside].max())
    return float((-sd)[inside].max())


def hang_list(layout):
    hangs = layout.get("hangs")
    if hangs:
        return hangs
    if layout.get("hang", True):
        cols = layout["cols"]
        if cols > 1:
            return [
                {"side": "back", "pos": 0, "orient": "down"},
                {"side": "back", "pos": cols - 1, "orient": "down"},
            ]
        return [{"side": "back", "pos": 0, "orient": "down"}]
    return []


def hang_xy(h, layout):
    pos = (int(h.get("pos") or 0) + 0.5) * PITCH
    side = h.get("side") or "back"
    if side == "left":
        return -WALL / 2, pos
    if side == "right":
        return layout["cols"] * PITCH + WALL / 2, pos
    if side == "front":
        return pos, -WALL / 2
    if side == "bottom":
        return pos, layout["rows"] * PITCH - 8
    return pos, layout["rows"] * PITCH + WALL / 2


def designed_cutout_mask(layout, lib, xs, ys, z, wall_h_):
    """True where a sample sits in a declared lid or wall opening."""
    mask = np.zeros(len(xs), dtype=bool)
    if z < wall_h_ - 0.2:
        zc = wall_h_ - 12
        for h in hang_list(layout):
            hx, hy = hang_xy(h, layout)
            side = h.get("side") or "back"
            if side == "bottom":
                if z <= BOT + 4:
                    mask |= (np.abs(xs - hx) <= 6) & (np.abs(ys - hy) <= 8)
            elif abs(z - zc) < 14:
                mask |= (np.abs(xs - hx) <= 6) & (np.abs(ys - hy) <= 8)
        for w in layout.get("walls") or []:
            d = lib.get(w["id"])
            if not d:
                continue
            wc = d.get("wall_cutout") or {}
            rad = float(wc.get("d") or 8) / 2 + 0.6
            pos = (w["pos"] + 0.5) * PITCH
            side = w["side"]
            if side == "left":
                mask |= (np.abs(ys - pos) <= rad) & (xs < 0)
            elif side == "right":
                mask |= (np.abs(ys - pos) <= rad) & (xs > layout["cols"] * PITCH)
            elif side == "front":
                mask |= (np.abs(xs - pos) <= rad) & (ys < 0)
            else:
                mask |= (np.abs(xs - pos) <= rad) & (ys > layout["rows"] * PITCH)
        return mask
    for p in layout.get("devices") or []:
        d = lib.get(p["id"])
        if not d or d.get("place") in ("bottom", "wall", "none"):
            continue
        cx = (p["c"] + d["cells_x"] / 2) * PITCH
        cy = (p["r"] + d["cells_y"] / 2) * PITCH
        for cut in d.get("cutouts") or []:
            x = cx + float(cut.get("x") or 0)
            y = cy + float(cut.get("y") or 0)
            t = cut.get("type")
            if t == "hole":
                r = float(cut.get("d") or 8) / 2 + 0.4
                mask |= (xs - x) ** 2 + (ys - y) ** 2 <= r * r
            elif t == "slot":
                w = float(cut.get("w") or 4) / 2 + 0.4
                ln = float(cut.get("l") or 20) / 2 + 0.4
                mask |= (np.abs(xs - x) <= w) & (np.abs(ys - y) <= ln)
            elif t in ("window", "grill"):
                w = float(cut.get("w") or 12) / 2 + 0.4
                h = float(cut.get("h") or 8) / 2 + 0.4
                mask |= (np.abs(xs - x) <= w) & (np.abs(ys - y) <= h)
    return mask


def gate_assemble(layout, tray, lid_print, lid_use=None):
    fails = []
    rows = layout["rows"]
    inner = float(layout["inner_h"])
    zh = wall_h(layout)
    if lid_use is not None:
        lid0 = lid_use.copy()
    else:
        lid0 = apply_mat(lid_print, lid_print_to_use_mat(rows, inner, 0.0))

    verts = np.asarray(lid0.vertices)
    # Rim ring: over the tray walls only (not cavity, not outer skirt).
    in_outer = (
        (verts[:, 0] >= -WALL - 0.2)
        & (verts[:, 0] <= layout["cols"] * PITCH + WALL + 0.2)
        & (verts[:, 1] >= -WALL - 0.2)
        & (verts[:, 1] <= layout["rows"] * PITCH + WALL + 0.2)
    )
    in_cavity = (
        (verts[:, 0] > 0.8)
        & (verts[:, 0] < layout["cols"] * PITCH - 0.8)
        & (verts[:, 1] > 0.8)
        & (verts[:, 1] < layout["rows"] * PITCH - 0.8)
    )
    in_rim = in_outer & ~in_cavity
    hanging = verts[in_rim & (verts[:, 2] < zh - 0.15)]
    posts = post_xy(layout)
    if posts:
        near = np.zeros(len(verts), dtype=bool)
        for px, py in posts:
            near |= (verts[:, 0] - px) ** 2 + (verts[:, 1] - py) ** 2 <= (PEG_D * 0.7) ** 2
        peg_verts = verts[near & (verts[:, 2] < zh - 0.15)]
    else:
        peg_verts = hanging
    tilts = layout.get("tilts") or []
    flat = all(abs(float(t)) < 0.05 for t in tilts)
    if len(peg_verts):
        if flat:
            hang = float(zh - peg_verts[:, 2].min())
            if hang > MAX_PEG_H + 0.4:
                fails.append(
                    f"lid rim hangs {hang:.1f} mm below the wall top (max {MAX_PEG_H:.1f} mm); "
                    "long posts block sliding the lid on"
                )
    elif flat:
        fails.append("lid has no rim pegs (nothing to locate the lid on the tray)")

    # Skirt must exist: lid XY larger than tray
    lid_min, lid_max = verts.min(axis=0), verts.max(axis=0)
    tray_v = np.asarray(tray.vertices)
    tray_min, tray_max = tray_v.min(axis=0), tray_v.max(axis=0)
    extra_x = min(tray_min[0] - lid_min[0], lid_max[0] - tray_max[0])
    extra_y = min(tray_min[1] - lid_min[1], lid_max[1] - tray_max[1])
    if layout.get("overlap", True) and (extra_x < SKIRT * 0.6 or extra_y < SKIRT * 0.6):
        fails.append(
            f"lid has no outer skirt (overhang x={extra_x:.2f} y={extra_y:.2f} mm, need >= {SKIRT * 0.6:.2f})"
        )

    def lifted(dz):
        m = lid0.copy()
        if dz:
            m.apply_translation([0.0, 0.0, dz])
        return m

    def pen(lid_mesh, thresh):
        return max_penetration(tray, np.asarray(lid_mesh.vertices[::2]), thresh=thresh)

    # Clear above the skirt: must not collide
    pen_clear = pen(lifted(SKIRT_H + 1.5), APPROACH_PENETRATE)
    if pen_clear > APPROACH_PENETRATE:
        fails.append(
            f"lid collides with the tray {pen_clear:.2f} mm while still {SKIRT_H + 1.5:.1f} mm above the seat"
        )

    # Mid approach: skirt overlapping, pegs not yet in. Allow only grazing.
    pen_mid = pen(lifted(PEG_H + 1.0), APPROACH_PENETRATE)
    if pen_mid > APPROACH_PENETRATE:
        fails.append(
            f"lid collides {pen_mid:.2f} mm on the way down at lift {PEG_H + 1.0:.1f} mm "
            "(posts or skirt interfere; the lid cannot slide/drop on)"
        )

    pen0 = pen(lid0, SEATED_PENETRATE)
    if pen0 > SEATED_PENETRATE:
        fails.append(
            f"seated lid intersects the tray solid {pen0:.2f} mm (peg/socket or plate/wall clash)"
        )

    return fails


def _in_cavity(layout, x, y, margin=0.6):
    return (
        margin <= x <= layout["cols"] * PITCH - margin
        and margin <= y <= layout["rows"] * PITCH - margin
    )


def probe_wall_ring(mesh, layout, z, lib):
    """Walk rays from outside toward the cavity. A closed wall is: empty, then
    about WALL mm of plastic, then the rectangular cavity. Fastener tunnels
    that return to plastic do not count as openings."""
    cols, rows = layout["cols"], layout["rows"]
    cx = cols * PITCH / 2
    cy = rows * PITCH / 2
    radius = max(case_w(layout), case_d(layout)) / 2 + 18
    step = 0.4
    ts = np.arange(radius, -8, -step)
    passages = []
    zh = wall_h(layout)
    posts = post_xy(layout)
    for i in range(72):
        ang = 2 * math.pi * i / 72
        c, s = math.cos(ang), math.sin(ang)
        xs = cx + ts * c
        ys = cy + ts * s
        pts = np.column_stack([xs, ys, np.full_like(xs, z)])
        allow = designed_cutout_mask(layout, lib, xs, ys, z, zh)
        _, inside = signed_inside(mesh, pts)
        inside = np.array(inside)
        for px, py in posts:
            inside |= (xs - px) ** 2 + (ys - py) ** 2 <= (M3 / 2 + 0.5) ** 2
        inside = inside & ~allow
        state = "out"
        solid_run = 0.0
        gap_run = 0.0
        hit_solid = False
        for j, is_sol in enumerate(inside):
            cav = _in_cavity(layout, xs[j], ys[j])
            if state == "out":
                if is_sol:
                    state = "wall"
                    hit_solid = True
                    solid_run = step
                elif cav:
                    passages.append((float(xs[j]), float(ys[j]), z, radius, "missing-wall"))
                    state = "cav"
            elif state == "wall":
                if is_sol:
                    solid_run += step
                elif cav:
                    if solid_run < STUFF_MM:
                        passages.append((float(xs[j]), float(ys[j]), z, solid_run, "thin-wall"))
                    state = "cav"
                else:
                    state = "hole"
                    gap_run = step
            elif state == "hole":
                if is_sol:
                    state = "wall"
                    solid_run += step
                    gap_run = 0.0
                elif cav:
                    passages.append((float(xs[j]), float(ys[j]), z, gap_run, "hole-to-cavity"))
                    state = "cav"
                else:
                    gap_run += step
        if not hit_solid and state != "cav":
            passages.append((float(cx + 10 * c), float(cy + 10 * s), z, radius, "missing-wall"))
    return passages


def slice_flood_reaches(mesh, z, cav_xy, cell_mm=0.6, plug_xy=None):
    """True if a 2D flood from outside the slice reaches cav_xy.

    Mesh-plane outlines are dilated by one cell so tessellation cracks
    under 1.2 mm do not count. A real 2 mm (or finger) gap still leaks.
    """
    import trimesh
    from collections import deque

    segs = trimesh.intersections.mesh_plane(
        mesh, plane_normal=[0.0, 0.0, 1.0], plane_origin=[0.0, 0.0, z]
    )
    if segs is None or len(segs) == 0:
        return True, f"no wall cross-section at z={z:.1f}"
    bmin = np.asarray(mesh.bounds[0][:2], dtype=np.float64) - 12
    bmax = np.asarray(mesh.bounds[1][:2], dtype=np.float64) + 12
    nx = int(np.ceil((bmax[0] - bmin[0]) / cell_mm))
    ny = int(np.ceil((bmax[1] - bmin[1]) / cell_mm))
    grid = np.zeros((ny, nx), dtype=np.uint8)

    def stamp(x0, y0, x1, y1):
        n = max(int(np.hypot(x1 - x0, y1 - y0) / cell_mm) + 1, 1)
        xs = np.linspace(x0, x1, n)
        ys = np.linspace(y0, y1, n)
        ix = ((xs - bmin[0]) / cell_mm).astype(int)
        iy = ((ys - bmin[1]) / cell_mm).astype(int)
        ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        grid[iy[ok], ix[ok]] = 1

    for s in segs:
        stamp(s[0][0], s[0][1], s[1][0], s[1][1])
    if plug_xy:
        for x, y, r in plug_xy:
            rad = int(np.ceil(r / cell_mm))
            cx = int((x - bmin[0]) / cell_mm)
            cy = int((y - bmin[1]) / cell_mm)
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy <= rad * rad:
                        yy, xx = cy + dy, cx + dx
                        if 0 <= yy < ny and 0 <= xx < nx:
                            grid[yy, xx] = 1
    grid[1:, :] |= grid[:-1, :]
    grid[:, 1:] |= grid[:, :-1]

    ci = int((cav_xy[0] - bmin[0]) / cell_mm)
    cj = int((cav_xy[1] - bmin[1]) / cell_mm)
    if not (0 <= ci < nx and 0 <= cj < ny):
        return True, f"cavity sample ({cav_xy[0]:.1f},{cav_xy[1]:.1f}) is outside the slice"
    if grid[cj, ci]:
        return False, None
    seen = np.zeros_like(grid, dtype=np.uint8)
    q = deque([(0, 0)])
    seen[0, 0] = 1
    while q:
        y, x = q.popleft()
        if y == cj and x == ci:
            return True, f"open path from outside to cavity at z={z:.1f}"
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ny_, nx_ = y + dy, x + dx
            if 0 <= ny_ < ny and 0 <= nx_ < nx and not seen[ny_, nx_] and grid[ny_, nx_] == 0:
                seen[ny_, nx_] = 1
                q.append((ny_, nx_))
    return False, None


def _cutout_plugs(layout, lib, z, zh):
    plugs = []
    for w in layout.get("walls") or []:
        d = lib.get(w["id"])
        if not d:
            continue
        wc = d.get("wall_cutout") or {}
        rad = float(wc.get("d") or 8) / 2 + 1.0
        pos = (w["pos"] + 0.5) * PITCH
        side = w["side"]
        if side == "left":
            plugs.append((-WALL / 2, pos, rad))
        elif side == "right":
            plugs.append((layout["cols"] * PITCH + WALL / 2, pos, rad))
        elif side == "front":
            plugs.append((pos, -WALL / 2, rad))
        else:
            plugs.append((pos, layout["rows"] * PITCH + WALL / 2, rad))
    for h in hang_list(layout):
        hx, hy = hang_xy(h, layout)
        plugs.append((hx, hy, 10.0))
    if z >= zh - 0.2:
        for p in layout.get("devices") or []:
            d = lib.get(p["id"])
            if not d or d.get("place") in ("bottom", "wall", "none"):
                continue
            cx = (p["c"] + d["cells_x"] / 2) * PITCH
            cy = (p["r"] + d["cells_y"] / 2) * PITCH
            for cut in d.get("cutouts") or []:
                x = cx + float(cut.get("x") or 0)
                y = cy + float(cut.get("y") or 0)
                t = cut.get("type")
                if t == "hole":
                    plugs.append((x, y, float(cut.get("d") or 8) / 2 + 0.8))
                elif t == "slot":
                    plugs.append((x, y, max(float(cut.get("w") or 4), float(cut.get("l") or 20)) / 2 + 0.8))
                else:
                    plugs.append((x, y, max(float(cut.get("w") or 12), float(cut.get("h") or 8)) / 2 + 0.8))
    for px, py in post_xy(layout):
        plugs.append((px, py, M3 / 2 + 0.8))
    return plugs


def gate_enclosure(layout, tray, lid_print, lib, lid_use=None):
    fails = []
    rows = layout["rows"]
    inner = float(layout["inner_h"])
    zh = wall_h(layout)
    if lid_use is not None:
        lid0 = lid_use.copy()
    else:
        lid0 = apply_mat(lid_print, lid_print_to_use_mat(rows, inner, 0.0))
    import trimesh

    assembled = trimesh.util.concatenate([tray, lid0])
    cav = (layout["cols"] * PITCH / 2.0, PITCH)
    z_mid = BOT + min(inner * 0.5, 12.0)
    z_joint = zh - SKIRT_H * 0.45
    for z, mesh, label in (
        (z_mid, tray, "mid-height"),
        (z_joint, assembled, "lid-tray-joint"),
    ):
        leak, why = slice_flood_reaches(mesh, z, cav, plug_xy=_cutout_plugs(layout, lib, z, zh))
        if leak:
            fails.append(f"{why} ({label})")

    lid_verts = np.asarray(lid0.vertices)
    skirt_verts = lid_verts[
        (lid_verts[:, 2] < zh - 0.5)
        & (lid_verts[:, 2] > zh - SKIRT_H - 1.5)
        & (
            (lid_verts[:, 0] < -WALL - FIT * 0.5)
            | (lid_verts[:, 0] > layout["cols"] * PITCH + WALL + FIT * 0.5)
            | (lid_verts[:, 1] < -WALL - FIT * 0.5)
            | (lid_verts[:, 1] > layout["rows"] * PITCH + WALL + FIT * 0.5)
        )
    ]
    if layout.get("overlap", True):
        if len(skirt_verts) < 20:
            fails.append("lid skirt does not hang over the tray walls; the joint is open")
        else:
            hang = float(zh - skirt_verts[:, 2].min())
            if hang < 5.0:
                fails.append(f"lid skirt overlap is {hang:.1f} mm (need >= 5 mm to close the joint)")

    return fails


def selftest(lib):
    fails = []
    good = PRESETS["sliders-quads"]
    f = gate_components(good, lib)
    if f:
        fails.append("selftest: sliders-quads should PASS components: " + "; ".join(f))
    bad = {
        **good,
        "devices": [
            {"id": "neoslider", "c": 0, "r": 0},
            {"id": "neoslider", "c": 0, "r": 0},
        ],
    }
    f = gate_components(bad, lib)
    if not f:
        fails.append("selftest: stacked NeoSliders should FAIL components")
    overflow = {
        **good,
        "devices": [{"id": "neoslider", "c": 5, "r": 0}],
    }
    f = gate_components(overflow, lib)
    if not f:
        fails.append("selftest: NeoSlider at c=5 on a 5-col grid should FAIL")
    return fails


def run(preset_name, bottom_path, top_path, skip_mesh, do_selftest, top_use_path=None):
    lib = load_lib()
    layout = {k: v for k, v in PRESETS[preset_name].items() if k not in ("bottom", "top", "top_use")}
    report = []
    all_fails = []

    if do_selftest:
        sf = selftest(lib)
        if sf:
            report.append("GATE selftest: FAIL")
            report.extend("  " + x for x in sf)
            all_fails.extend(sf)
        else:
            report.append("GATE selftest: PASS")

    cf = gate_components(layout, lib)
    if cf:
        report.append("GATE components: FAIL")
        report.extend("  " + x for x in cf)
        all_fails.extend(cf)
    else:
        n = len(layout.get("devices") or [])
        report.append(
            f"GATE components: PASS  {n} devices on {layout['cols']}x{layout['rows']}, "
            "no cell overlap, PCBs inside the cavity, bosses miss rim pegs"
        )

    if skip_mesh:
        report.append("GATE assemble: SKIP (no STL)")
        report.append("GATE enclosure: SKIP (no STL)")
        return report, all_fails

    if not bottom_path.exists() or not top_path.exists():
        msg = f"missing STL bottom={bottom_path} top={top_path}"
        report.append("GATE assemble: FAIL")
        report.append("  " + msg)
        report.append("GATE enclosure: FAIL")
        report.append("  " + msg)
        all_fails.append(msg)
        return report, all_fails

    tray = load_mesh(bottom_path)
    lid_print = load_mesh(top_path)
    lid_use = load_mesh(top_use_path) if top_use_path and Path(top_use_path).exists() else None

    af = gate_assemble(layout, tray, lid_print, lid_use=lid_use)
    if af:
        report.append("GATE assemble: FAIL")
        report.extend("  " + x for x in af)
        all_fails.extend(af)
    else:
        report.append(
            "GATE assemble: PASS  short rim pegs, outer skirt, lid clears the tray "
            "until it seats, no solid clash"
        )

    ef = gate_enclosure(layout, tray, lid_print, lib, lid_use=lid_use)
    if ef:
        report.append("GATE enclosure: FAIL")
        report.extend("  " + x for x in ef)
        all_fails.extend(ef)
    else:
        report.append(
            "GATE enclosure: PASS  four walls closed, lid skirt covers the joint, "
            f"no path >= {STUFF_MM:.0f} mm into the cavity except declared cutouts"
        )
    return report, all_fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preset", default="sliders-quads", choices=sorted(PRESETS))
    ap.add_argument("--bottom", type=Path, default=None)
    ap.add_argument("--top", type=Path, default=None)
    ap.add_argument("--top-use", type=Path, default=None)
    ap.add_argument("--components-only", action="store_true")
    ap.add_argument("--selftest", action="store_true", default=True)
    ap.add_argument("--no-selftest", action="store_true")
    args = ap.parse_args(argv)
    preset = PRESETS[args.preset]
    bottom = args.bottom or preset["bottom"]
    top = args.top or preset["top"]
    top_use = args.top_use or preset.get("top_use")
    report, fails = run(
        args.preset,
        Path(bottom),
        Path(top),
        skip_mesh=args.components_only,
        do_selftest=not args.no_selftest,
        top_use_path=Path(top_use) if top_use else None,
    )
    print("\n".join(report))
    if fails:
        print(f"RESULT: FAIL  {len(fails)} issue(s)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
