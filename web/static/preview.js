import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { ConvexGeometry } from "three/addons/geometries/ConvexGeometry.js";

const PITCH = 25.4;
const WALL = 8;
const BOT = 3;
const TOP = 3.2;
const FIT = 0.4;
const SKIRT = 2.2;
const SKIRT_H = 8;
const PEG_H = 2.5;
const PEG_D = 4;
const PEG_INSET = 3;
const EX = FIT + SKIRT;
const CUT = 0xff4d6d;

let renderer, scene, camera, controls, root;
let viewMode = "assembly";

function layout() {
  return window.PANEL_LAYOUT;
}
function byId() {
  return window.PANEL_BY_ID || {};
}
function isCol(l) {
  return l && l.tilt_axis === "col";
}
function tiltOf(l, i) {
  return (l.tilts && l.tilts[i]) || 0;
}
function accumY(l, i) {
  let y = 0;
  for (let j = 0; j < i; j++) y += PITCH * Math.cos((tiltOf(l, j) * Math.PI) / 180);
  return y;
}
function accumZ(l, i) {
  let z = 0;
  for (let j = 0; j < i; j++) z += PITCH * Math.sin((tiltOf(l, j) * Math.PI) / 180);
  return z;
}
function wallH(l) {
  return BOT + (l.inner_h || 25);
}
function lidWY(l, i, ly) {
  const t = (tiltOf(l, i) * Math.PI) / 180;
  return accumY(l, i) + ly * Math.cos(t) - wallH(l) * Math.sin(t);
}
function lidWZ(l, i, ly) {
  const t = (tiltOf(l, i) * Math.PI) / 180;
  return accumZ(l, i) + ly * Math.sin(t) + wallH(l) * Math.cos(t);
}
function hasOverlap(l) {
  return !l || l.overlap !== false;
}
function lidEx(l) {
  return hasOverlap(l) ? EX : 0;
}
function faceDeg(l) {
  const v = Number(l && l.face_tilt);
  return Number.isFinite(v) ? v : 0;
}
function hangBottomY(l) {
  return (l.rows || 1) * PITCH - 8;
}
function faceMatrix(deg) {
  const a = (deg * Math.PI) / 180;
  const m = new THREE.Matrix4();
  const t1 = new THREE.Matrix4().makeTranslation(0, WALL, 0);
  const r = new THREE.Matrix4().makeRotationX(a);
  const t2 = new THREE.Matrix4().makeTranslation(0, -WALL, 0);
  return m.multiply(t2).multiply(r).multiply(t1);
}
function hangOrientAngle(orient) {
  if (orient === "up") return Math.PI;
  if (orient === "left") return Math.PI / 2;
  if (orient === "right") return -Math.PI / 2;
  return 0;
}
function addHangMarker(parent, localX, localY, localZ, wallRotZ, orient, cutMat) {
  const g = new THREE.Group();
  g.position.set(localX, localY, localZ);
  g.rotation.z = wallRotZ;
  const inner = new THREE.Group();
  inner.rotation.x = Math.PI / 2;
  inner.rotation.z = hangOrientAngle(orient);
  const head = new THREE.Mesh(new THREE.CylinderGeometry(4.25, 4.25, WALL + 2, 20), cutMat);
  head.position.y = 7;
  const slot = new THREE.Mesh(new THREE.BoxGeometry(4.2, 12, WALL + 2), cutMat);
  slot.position.y = 1;
  inner.add(head);
  inner.add(slot);
  g.add(inner);
  parent.add(g);
}
function lidLY0(l, i) {
  const ex = lidEx(l);
  return (i === 0 ? -WALL - ex : 0);
}
function lidLY1(l, i) {
  const last = i === (l.rows || 1) - 1;
  const ylen = PITCH + (i === 0 ? WALL : 0) + (last ? WALL : 0);
  const ex = lidEx(l);
  return (i === 0 ? -WALL : 0) + ylen + (last ? ex : 0);
}
function rowMatrix(l, i) {
  const t = (tiltOf(l, i) * Math.PI) / 180;
  const m = new THREE.Matrix4();
  m.makeRotationX(t);
  m.setPosition(0, accumY(l, i), accumZ(l, i));
  return m;
}
function colMatrix(l, i) {
  const t = (tiltOf(l, i) * Math.PI) / 180;
  const m = new THREE.Matrix4();
  m.makeRotationY(-t);
  m.setPosition(accumY(l, i), 0, accumZ(l, i));
  return m;
}
function hullBoxes(parent, m0, a, m1, b, mat) {
  const pts = [];
  const corners = (x, y, z, w, h, d) => {
    const out = [];
    for (const dx of [0, w]) for (const dy of [0, h]) for (const dz of [0, d]) {
      out.push(new THREE.Vector3(x + dx, y + dy, z + dz));
    }
    return out;
  };
  for (const p of corners(...a)) pts.push(p.applyMatrix4(m0));
  for (const p of corners(...b)) pts.push(p.applyMatrix4(m1));
  try {
    parent.add(new THREE.Mesh(new ConvexGeometry(pts), mat));
  } catch {
    /* skip a degenerate hull */
  }
}
function zSkirtSeg(parent, x, y0, z0, y1, z1, mat) {
  const hx = SKIRT / 2;
  const pts = [
    new THREE.Vector3(x - hx, y0, z0),
    new THREE.Vector3(x + hx, y0, z0),
    new THREE.Vector3(x - hx, y0, z0 - SKIRT_H),
    new THREE.Vector3(x + hx, y0, z0 - SKIRT_H),
    new THREE.Vector3(x - hx, y1, z1),
    new THREE.Vector3(x + hx, y1, z1),
    new THREE.Vector3(x - hx, y1, z1 - SKIRT_H),
    new THREE.Vector3(x + hx, y1, z1 - SKIRT_H),
  ];
  try {
    parent.add(new THREE.Mesh(new ConvexGeometry(pts), mat));
  } catch {
    /* skip a degenerate skirt segment */
  }
}

function edgeR(l) {
  if (!l || l.edge_style === "square") return 0;
  const e = Number(l.edge_mm);
  return Number.isFinite(e) && e > 0.2 ? Math.min(e, 8) : 2;
}
function addExtrudedRounded(parent, x, y, w, h, depth, z, r, mat) {
  const shape = new THREE.Shape();
  roundedRectPath(shape, x, y, w, h, r);
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 16 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.z = z;
  parent.add(mesh);
  return mesh;
}
function addRoundedRing(parent, ox, oy, ow, oh, ix, iy, iw, ih, rOut, rIn, depth, z, mat) {
  const shape = new THREE.Shape();
  roundedRectPath(shape, ox, oy, ow, oh, rOut);
  const hole = new THREE.Path();
  roundedRectPath(hole, ix, iy, iw, ih, rIn);
  shape.holes.push(reversePath(hole));
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 16 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.z = z;
  parent.add(mesh);
  return mesh;
}
function roundedRectPath(shape, x, y, w, h, r) {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  shape.moveTo(x + r, y);
  shape.lineTo(x + w - r, y);
  shape.quadraticCurveTo(x + w, y, x + w, y + r);
  shape.lineTo(x + w, y + h - r);
  shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  shape.lineTo(x + r, y + h);
  shape.quadraticCurveTo(x, y + h, x, y + h - r);
  shape.lineTo(x, y + r);
  shape.quadraticCurveTo(x, y, x + r, y);
}

function reversePath(p) {
  const pts = p.getPoints(32);
  const out = new THREE.Path();
  if (!pts.length) return p;
  out.moveTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
  for (let i = pts.length - 2; i >= 0; i--) out.lineTo(pts[i].x, pts[i].y);
  out.autoClose = true;
  return out;
}

function offsetPath(p, dx, dy) {
  const pts = p.getPoints(32);
  const out = new THREE.Path();
  if (!pts.length) return p;
  out.moveTo(pts[0].x + dx, pts[0].y + dy);
  for (let i = 1; i < pts.length; i++) out.lineTo(pts[i].x + dx, pts[i].y + dy);
  out.autoClose = true;
  return out;
}

function holePath(cut) {
  const p = new THREE.Path();
  const x = cut.x || 0;
  const y = cut.y || 0;
  if (cut.type === "hole") {
    const r = (cut.d || 8) / 2;
    p.absarc(x, y, r, 0, Math.PI * 2, true);
    return p;
  }
  if (cut.type === "slot") {
    const w = cut.w || 4;
    const len = cut.l || 20;
    roundedRectPath(p, x - w / 2, y - len / 2, w, len, Math.min(w, len) / 2);
    return reversePath(p);
  }
  if (cut.type === "window") {
    const w = cut.w || 20;
    const h = cut.h || 12;
    roundedRectPath(p, x - w / 2, y - h / 2, w, h, 1.2);
    return reversePath(p);
  }
  if (cut.type === "grill") {
    const w = cut.w || 12;
    const h = cut.h || 8;
    roundedRectPath(p, x - w / 2, y - h / 2, w, h, 0.6);
    return reversePath(p);
  }
  return p;
}

function deviceCenterLocal(placed, def, row) {
  return {
    x: (placed.c + def.cells_x / 2) * PITCH,
    y: (placed.r - row + def.cells_y / 2) * PITCH,
  };
}

function placedDevices(l) {
  const lib = byId();
  return (l.devices || [])
    .map((p) => ({ p, def: lib[p.id] }))
    .filter((x) => x.def && x.def.place !== "none");
}

function punchDeviceHoles(shape, l, rowFilter, colFilter) {
  for (const { p, def } of placedDevices(l)) {
    if (def.place === "bottom" || def.place === "wall") continue;
    const dx = def.cells_x || 1;
    const dy = def.cells_y || 1;
    if (rowFilter != null && !(p.r <= rowFilter && p.r + dy > rowFilter)) continue;
    if (colFilter != null && !(p.c <= colFilter && p.c + dx > colFilter)) continue;
    let c;
    if (colFilter != null) {
      c = { x: (p.c - colFilter + dx / 2) * PITCH, y: (p.r + dy / 2) * PITCH };
    } else if (rowFilter == null) {
      c = { x: (p.c + dx / 2) * PITCH, y: (p.r + dy / 2) * PITCH };
    } else {
      c = deviceCenterLocal(p, def, rowFilter);
    }
    for (const cut of def.cutouts || []) {
      shape.holes.push(offsetPath(holePath(cut), c.x, c.y));
    }
  }
}

function addCutoutMarkers(parent, cx, cy, z, cuts) {
  const mat = new THREE.MeshBasicMaterial({ color: CUT, side: THREE.DoubleSide });
  for (const cut of cuts || []) {
    const x = cx + (cut.x || 0);
    const y = cy + (cut.y || 0);
    let mesh;
    if (cut.type === "hole") {
      mesh = new THREE.Mesh(new THREE.CylinderGeometry((cut.d || 8) / 2, (cut.d || 8) / 2, TOP + 1.2, 24), mat);
      mesh.rotation.x = Math.PI / 2;
    } else if (cut.type === "slot") {
      mesh = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 4, cut.l || 20, TOP + 1.2), mat);
    } else if (cut.type === "window") {
      mesh = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 20, cut.h || 12, TOP + 1.2), mat);
    } else if (cut.type === "grill") {
      const g = new THREE.Group();
      for (const gy of [-3, 0, 3]) {
        const sl = new THREE.Mesh(new THREE.BoxGeometry(cut.w || 12, 1.6, TOP + 1.2), mat);
        sl.position.y = gy;
        g.add(sl);
      }
      g.position.set(x, y, z);
      parent.add(g);
      continue;
    } else continue;
    mesh.position.set(x, y, z);
    parent.add(mesh);
  }
}

function lidWithHoles(l, inner) {
  const cols = l.cols;
  const rows = l.rows;
  const ex = lidEx(l);
  const w = cols * PITCH + 2 * WALL + 2 * ex;
  const d = rows * PITCH + 2 * WALL + 2 * ex;
  const shape = new THREE.Shape();
  roundedRectPath(shape, -WALL - ex, -WALL - ex, w, d, edgeR(l));
  punchDeviceHoles(shape, l, null);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: TOP, bevelEnabled: false, curveSegments: 12 });
  const mesh = new THREE.Mesh(
    geo,
    new THREE.MeshLambertMaterial({ color: 0xd6dee8, side: THREE.DoubleSide })
  );
  mesh.position.z = BOT + inner;
  return mesh;
}

function lidRowWithHoles(l, i, inner) {
  const cols = l.cols;
  const rows = l.rows;
  const ex = lidEx(l);
  const y0 = i === 0 ? -WALL - ex : 0;
  const y1 = PITCH + (i === rows - 1 ? WALL + ex : 0);
  const shape = new THREE.Shape();
  roundedRectPath(shape, -WALL - ex, y0, cols * PITCH + 2 * WALL + 2 * ex, y1 - y0, 0);
  punchDeviceHoles(shape, l, i);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: TOP, bevelEnabled: false, curveSegments: 12 });
  const mesh = new THREE.Mesh(
    geo,
    new THREE.MeshLambertMaterial({ color: 0xd6dee8, side: THREE.DoubleSide })
  );
  mesh.position.z = BOT + inner;
  return mesh;
}

function build(l) {
  const g = new THREE.Group();
  if (!l) return g;
  const inner = l.inner_h || 25;
  const H = BOT + inner;
  const cols = l.cols || 1;
  const rows = l.rows || 1;
  const tray = new THREE.Group();
  const lid = new THREE.Group();
  const wallC = 0x1e293b;
  const postC = 0x64748b;
  const pcbC = 0x166534;
  const bossC = 0xf59e0b;
  const lidRows = [];
  const trayRows = [];

  const wallMat = new THREE.MeshLambertMaterial({ color: wallC });
  function box(parent, w, h, d, x, y, z, mat) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || wallMat);
    m.position.set(x, y, z);
    parent.add(m);
    return m;
  }

  const colMode = isCol(l);
  const flat = (l.tilt_axis === "flat") || (l.tilts || []).every((v) => !v);
  const er = edgeR(l);
  if (flat) {
    const cw = cols * PITCH + 2 * WALL;
    const cd = rows * PITCH + 2 * WALL;
    addExtrudedRounded(tray, -WALL, -WALL, cw, cd, BOT, 0, er, wallMat);
    addRoundedRing(tray, -WALL, -WALL, cw, cd, 0, 0, cols * PITCH, rows * PITCH, er, 0, H - BOT, BOT, wallMat);
  }
  if (colMode) {
    const cd = rows * PITCH + 2 * WALL;
    for (let i = 0; i < cols; i++) {
      const t = (tiltOf(l, i) * Math.PI) / 180;
      const col = new THREE.Group();
      col.position.set(accumY(l, i), 0, accumZ(l, i));
      col.rotation.y = -t;
      const x0 = i === 0 ? -WALL : 0;
      const xl = PITCH + (i === 0 ? WALL : 0) + (i === cols - 1 ? WALL : 0);
      if (!flat) {
        box(col, xl, cd, BOT, x0 + xl / 2, rows * PITCH / 2, BOT / 2);
        box(col, xl, WALL, H, x0 + xl / 2, -WALL / 2, H / 2);
        box(col, xl, WALL, H, x0 + xl / 2, rows * PITCH + WALL / 2, H / 2);
        if (i === 0) box(col, WALL, cd, H, -WALL / 2, rows * PITCH / 2, H / 2);
        if (i === cols - 1) box(col, WALL, cd, H, PITCH + WALL / 2, rows * PITCH / 2, H / 2);
      }
      tray.add(col);
      trayRows[i] = col;
    }
  } else {
    for (let i = 0; i < rows; i++) {
      const t = (tiltOf(l, i) * Math.PI) / 180;
      const row = new THREE.Group();
      row.position.set(0, accumY(l, i), accumZ(l, i));
      row.rotation.x = t;
      const y0 = i === 0 ? -WALL : 0;
      const yl = PITCH + (i === 0 ? WALL : 0) + (i === rows - 1 ? WALL : 0);
      const cw = cols * PITCH + 2 * WALL;
      if (!flat) {
        box(row, cw, yl, BOT, cols * PITCH / 2, y0 + yl / 2, BOT / 2);
        box(row, WALL, yl, H, -WALL / 2, y0 + yl / 2, H / 2);
        box(row, WALL, yl, H, cols * PITCH + WALL / 2, y0 + yl / 2, H / 2);
        if (i === 0) box(row, cw, WALL, H, cols * PITCH / 2, -WALL / 2, H / 2);
        if (i === rows - 1) box(row, cw, WALL, H, cols * PITCH / 2, PITCH + WALL / 2, H / 2);
      }
      tray.add(row);
      trayRows[i] = row;
    }
  }
  const hangList = Array.isArray(l.hangs)
    ? l.hangs
    : (l.hang === false ? [] : [
      { side: "back", pos: 0, orient: "down" },
      { side: "back", pos: Math.max(0, cols - 1), orient: "down" },
    ]);
  const cutMat = new THREE.MeshBasicMaterial({ color: CUT });
  if (hangList.length) {
    const zc = H - 12;
    for (const h of hangList) {
      const pos = (Number(h.pos) || 0) + 0.5;
      const orient = h.orient || "down";
      if (h.side === "bottom") continue;
      if (colMode) {
        if (h.side === "left" && trayRows[0]) {
          addHangMarker(trayRows[0], -WALL / 2, pos * PITCH, zc, Math.PI / 2, orient, cutMat);
        } else if (h.side === "right" && trayRows[cols - 1]) {
          addHangMarker(trayRows[cols - 1], PITCH + WALL / 2, pos * PITCH, zc, -Math.PI / 2, orient, cutMat);
        } else if (h.side === "front") {
          const ci = Math.min(cols - 1, Math.max(0, Math.floor(h.pos || 0)));
          const lx = (pos - ci) * PITCH;
          if (trayRows[ci]) addHangMarker(trayRows[ci], lx, -WALL / 2, zc, Math.PI, orient, cutMat);
        } else if (h.side === "back") {
          const ci = Math.min(cols - 1, Math.max(0, Math.floor(h.pos || 0)));
          const lx = (pos - ci) * PITCH;
          if (trayRows[ci]) addHangMarker(trayRows[ci], lx, rows * PITCH + WALL / 2, zc, 0, orient, cutMat);
        }
      } else if (h.side === "back" && trayRows[rows - 1]) {
        addHangMarker(trayRows[rows - 1], pos * PITCH, PITCH + WALL / 2, zc, 0, orient, cutMat);
      } else if (h.side === "front" && trayRows[0]) {
        addHangMarker(trayRows[0], pos * PITCH, -WALL / 2, zc, Math.PI, orient, cutMat);
      } else if (h.side === "left") {
        const r = Math.min(rows - 1, Math.max(0, Math.floor(h.pos || 0)));
        const ly = (pos - r) * PITCH;
        if (trayRows[r]) addHangMarker(trayRows[r], -WALL / 2, ly, zc, Math.PI / 2, orient, cutMat);
      } else if (h.side === "right") {
        const r = Math.min(rows - 1, Math.max(0, Math.floor(h.pos || 0)));
        const ly = (pos - r) * PITCH;
        if (trayRows[r]) addHangMarker(trayRows[r], cols * PITCH + WALL / 2, ly, zc, -Math.PI / 2, orient, cutMat);
      }
    }
  }
  if (!flat) {
    if (colMode) {
      for (let i = 0; i < cols - 1; i++) {
        const m0 = colMatrix(l, i);
        const m1 = colMatrix(l, i + 1);
        hullBoxes(tray, m0, [PITCH - 0.05, -WALL, 0, 0.05, WALL, H], m1, [0, -WALL, 0, 0.05, WALL, H], wallMat);
        hullBoxes(tray, m0, [PITCH - 0.05, rows * PITCH, 0, 0.05, WALL, H], m1, [0, rows * PITCH, 0, 0.05, WALL, H], wallMat);
        hullBoxes(tray, m0, [PITCH - 0.05, -WALL, 0, 0.05, rows * PITCH + 2 * WALL, BOT], m1, [0, -WALL, 0, 0.05, rows * PITCH + 2 * WALL, BOT], wallMat);
      }
    } else {
      for (let i = 0; i < rows - 1; i++) {
        const m0 = rowMatrix(l, i);
        const m1 = rowMatrix(l, i + 1);
        hullBoxes(tray, m0, [-WALL, PITCH - 0.05, 0, WALL, 0.05, H], m1, [-WALL, 0, 0, WALL, 0.05, H], wallMat);
        hullBoxes(tray, m0, [cols * PITCH, PITCH - 0.05, 0, WALL, 0.05, H], m1, [cols * PITCH, 0, 0, WALL, 0.05, H], wallMat);
        hullBoxes(tray, m0, [-WALL, PITCH - 0.05, 0, cols * PITCH + 2 * WALL, 0.05, BOT], m1, [-WALL, 0, 0, cols * PITCH + 2 * WALL, 0.05, BOT], wallMat);
      }
    }
  }

  if (flat) {
    lid.add(lidWithHoles(l, inner));
  } else if (colMode) {
    for (let i = 0; i < cols; i++) {
      const t = (tiltOf(l, i) * Math.PI) / 180;
      const lidCol = new THREE.Group();
      lidCol.position.set(accumY(l, i), 0, accumZ(l, i));
      lidCol.rotation.y = -t;
      const shape = new THREE.Shape();
      const x0 = i === 0 ? -WALL - lidEx(l) : 0;
      const x1 = PITCH + (i === cols - 1 ? WALL + lidEx(l) : 0);
      roundedRectPath(shape, x0, -WALL - lidEx(l), x1 - x0, rows * PITCH + 2 * WALL + 2 * lidEx(l), 0);
      punchDeviceHoles(shape, l, null, i);
      const geo = new THREE.ExtrudeGeometry(shape, { depth: TOP, bevelEnabled: false, curveSegments: 8 });
      const mesh = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: 0xd6dee8, side: THREE.DoubleSide }));
      mesh.position.z = BOT + inner;
      lidCol.add(mesh);
      lid.add(lidCol);
      lidRows[i] = lidCol;
    }
  } else {
    for (let i = 0; i < rows; i++) {
      const t = (tiltOf(l, i) * Math.PI) / 180;
      const lidRow = new THREE.Group();
      lidRow.position.set(0, accumY(l, i), accumZ(l, i));
      lidRow.rotation.x = t;
      lidRow.add(lidRowWithHoles(l, i, inner));
      lid.add(lidRow);
      lidRows[i] = lidRow;
    }
  }

  const zCut = BOT + inner + TOP / 2;
  for (const { p, def } of placedDevices(l)) {
    const strip = colMode ? p.c : p.r;
    const parent = (!flat && lidRows[strip]) ? lidRows[strip] : lid;
    const loc = (!flat && lidRows[strip])
      ? (colMode
        ? { x: (p.c - strip + def.cells_x / 2) * PITCH, y: (p.r + def.cells_y / 2) * PITCH }
        : deviceCenterLocal(p, def, p.r))
      : { x: (p.c + def.cells_x / 2) * PITCH, y: (p.r + def.cells_y / 2) * PITCH };
    if (def.place !== "bottom" && def.place !== "wall") {
      addCutoutMarkers(parent, loc.x, loc.y, zCut, def.cutouts);
      if (def.pcb_mm) {
        const pcb = new THREE.Mesh(
          new THREE.BoxGeometry(def.pcb_mm[0], def.pcb_mm[1], 1.6),
          new THREE.MeshLambertMaterial({ color: pcbC })
        );
        pcb.position.set(loc.x, loc.y, BOT + inner - (def.boss_mm || 6) - 0.8);
        parent.add(pcb);
      }
      for (const h of def.holes || []) {
        const b = new THREE.Mesh(
          new THREE.CylinderGeometry(3.2, 3.2, def.boss_mm || 6, 12),
          new THREE.MeshLambertMaterial({ color: bossC })
        );
        b.rotation.x = Math.PI / 2;
        b.position.set(loc.x + h[0], loc.y + h[1], BOT + inner - (def.boss_mm || 6) / 2);
        parent.add(b);
      }
    }
    if (def.place === "bottom" && def.pcb_mm) {
      const pcb = new THREE.Mesh(
        new THREE.BoxGeometry(def.pcb_mm[0], def.pcb_mm[1], 1.6),
        new THREE.MeshLambertMaterial({ color: pcbC })
      );
      pcb.position.set(loc.x, loc.y, BOT + 4);
      tray.add(pcb);
    }
  }

  for (const w of l.walls || []) {
    const def = byId()[w.id];
    if (!def) continue;
    const cuts = def.cutouts || (def.wall_cutout ? [def.wall_cutout] : []);
    const pos = (w.pos + 0.5) * PITCH;
    const z = BOT + inner / 2;
    const grp = new THREE.Group();
    if (w.side === "left") grp.position.set(-WALL / 2, pos, z);
    else if (w.side === "right") {
      grp.position.set(cols * PITCH + WALL / 2, pos, z);
      grp.rotation.z = Math.PI;
    } else if (w.side === "front") {
      grp.position.set(pos, -WALL / 2, z);
      grp.rotation.z = -Math.PI / 2;
    } else {
      grp.position.set(pos, rows * PITCH + WALL / 2, z);
      grp.rotation.z = Math.PI / 2;
    }
    const wc = def.wall_cutout || cuts[0];
    if (wc && wc.type === "hole") {
      const m = new THREE.Mesh(
        new THREE.CylinderGeometry((wc.d || 8) / 2, (wc.d || 8) / 2, WALL + 2, 20),
        new THREE.MeshBasicMaterial({ color: CUT })
      );
      m.rotation.z = Math.PI / 2;
      grp.add(m);
    } else if (wc && wc.type === "grill") {
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(WALL + 2, wc.w || 12, wc.h || 8),
        new THREE.MeshBasicMaterial({ color: CUT })
      );
      grp.add(m);
    }
    tray.add(grp);
  }

  const pegGeom = new THREE.CylinderGeometry(PEG_D / 2, PEG_D / 2, PEG_H, 12);
  const postMat = new THREE.MeshLambertMaterial({ color: postC });
  function addPeg(x, y, z) {
    const p = new THREE.Mesh(pegGeom, postMat);
    p.rotation.x = Math.PI / 2;
    p.position.set(x, y, z - PEG_H / 2);
    lid.add(p);
  }
  for (let r = 0; r < rows; r++) {
    if (Math.abs(tiltOf(l, r)) >= 0.05) continue;
    addPeg(-PEG_INSET, lidWY(l, r, PITCH / 2), lidWZ(l, r, PITCH / 2));
    addPeg(cols * PITCH + PEG_INSET, lidWY(l, r, PITCH / 2), lidWZ(l, r, PITCH / 2));
  }
  if (Math.abs(tiltOf(l, 0)) < 0.05) {
    const yf = lidWY(l, 0, -PEG_INSET);
    const zf = lidWZ(l, 0, -PEG_INSET);
    if (cols > 1) {
      for (let c = 1; c < cols; c++) addPeg(c * PITCH, yf, zf);
    } else addPeg(PITCH / 2, yf, zf);
  }
  if (Math.abs(tiltOf(l, rows - 1)) < 0.05) {
    const yb = lidWY(l, rows - 1, PITCH + PEG_INSET);
    const zb = lidWZ(l, rows - 1, PITCH + PEG_INSET);
    if (cols > 1) {
      for (let c = 1; c < cols; c++) addPeg(c * PITCH, yb, zb);
    } else addPeg(PITCH / 2, yb, zb);
  }

  const skirtMat = new THREE.MeshLambertMaterial({ color: 0xcbd5e1 });
  const zSk = BOT + inner - SKIRT_H / 2;
  const lidPlateMat = new THREE.MeshLambertMaterial({ color: 0xd6dee8 });
  const ex = lidEx(l);
  if (flat) {
    if (hasOverlap(l)) {
      const cw = cols * PITCH + 2 * WALL;
      const cd = rows * PITCH + 2 * WALL;
      const lw = cw + 2 * ex;
      const ld = cd + 2 * ex;
      addRoundedRing(
        lid,
        -WALL - ex, -WALL - ex, lw, ld,
        -WALL - FIT, -WALL - FIT, cw + 2 * FIT, cd + 2 * FIT,
        er, er, SKIRT_H, BOT + inner - SKIRT_H, skirtMat
      );
    }
  } else {
    for (let i = 0; i < rows - 1; i++) {
      const m0 = rowMatrix(l, i);
      const m1 = rowMatrix(l, i + 1);
      hullBoxes(
        lid, m0, [-WALL - ex, PITCH - 0.05, BOT + inner, cols * PITCH + 2 * WALL + 2 * ex, 0.05, TOP],
        m1, [-WALL - ex, 0, BOT + inner, cols * PITCH + 2 * WALL + 2 * ex, 0.05, TOP],
        lidPlateMat
      );
    }
    if (hasOverlap(l)) {
      const xl = -WALL - ex + SKIRT / 2;
      const xr = cols * PITCH + WALL + ex - SKIRT / 2;
      for (let i = 0; i < rows; i++) {
        const a = { y: lidWY(l, i, lidLY0(l, i)), z: lidWZ(l, i, lidLY0(l, i)) };
        const b = { y: lidWY(l, i, lidLY1(l, i)), z: lidWZ(l, i, lidLY1(l, i)) };
        zSkirtSeg(lid, xl, a.y, a.z, b.y, b.z, skirtMat);
        zSkirtSeg(lid, xr, a.y, a.z, b.y, b.z, skirtMat);
      }
      for (let i = 0; i < rows - 1; i++) {
        const a = { y: lidWY(l, i, lidLY1(l, i)), z: lidWZ(l, i, lidLY1(l, i)) };
        const b = { y: lidWY(l, i + 1, lidLY0(l, i + 1)), z: lidWZ(l, i + 1, lidLY0(l, i + 1)) };
        zSkirtSeg(lid, xl, a.y, a.z, b.y, b.z, skirtMat);
        zSkirtSeg(lid, xr, a.y, a.z, b.y, b.z, skirtMat);
      }
      const cw = cols * PITCH + 2 * WALL + 2 * ex;
      const yf = lidWY(l, 0, lidLY0(l, 0));
      const zf = lidWZ(l, 0, lidLY0(l, 0));
      box(lid, cw, SKIRT, SKIRT_H, cols * PITCH / 2, yf + SKIRT / 2, zf - SKIRT_H / 2, skirtMat);
      const yb = lidWY(l, rows - 1, lidLY1(l, rows - 1));
      const zb = lidWZ(l, rows - 1, lidLY1(l, rows - 1));
      box(lid, cw, SKIRT, SKIRT_H, cols * PITCH / 2, yb - SKIRT / 2, zb - SKIRT_H / 2, skirtMat);
    }
  }

  const shell = new THREE.Group();
  if (viewMode === "bottom") shell.add(tray);
  else if (viewMode === "top") {
    lid.position.z += 10;
    shell.add(lid);
  } else {
    shell.add(tray);
    shell.add(lid);
  }
  const face = faceDeg(l);
  if (Math.abs(face) > 0.05) {
    const pivot = new THREE.Group();
    pivot.position.set(0, -WALL, 0);
    const inner = new THREE.Group();
    inner.position.set(0, WALL, 0);
    inner.add(shell);
    pivot.rotation.x = (face * Math.PI) / 180;
    pivot.add(inner);
    g.add(pivot);
    if (viewMode !== "top") {
      const cw = cols * PITCH + 2 * WALL;
      const cd = rows * PITCH + 2 * WALL;
      box(g, cw, cd, BOT, cols * PITCH / 2, rows * PITCH / 2, BOT / 2);
      const m0 = new THREE.Matrix4();
      const m1 = faceMatrix(face);
      hullBoxes(g, m0, [-WALL, -WALL, 0, WALL, cd, BOT], m1, [-WALL, -WALL, 0, WALL, cd, BOT], wallMat);
      hullBoxes(g, m0, [cols * PITCH, -WALL, 0, WALL, cd, BOT], m1, [cols * PITCH, -WALL, 0, WALL, cd, BOT], wallMat);
      hullBoxes(g, m0, [-WALL, rows * PITCH, 0, cw, WALL, BOT], m1, [-WALL, rows * PITCH, 0, cw, WALL, BOT], wallMat);
    }
  } else {
    g.add(shell);
  }
  if (viewMode !== "top") {
    for (const h of hangList) {
      if (h.side !== "bottom") continue;
      const pos = (Number(h.pos) || 0) + 0.5;
      addHangMarker(g, pos * PITCH, hangBottomY(l), BOT / 2, 0, h.orient || "down", cutMat);
    }
  }
  const dropZ = BOT + inner + (viewMode === "top" ? 10 : 0);
  const dw = (cols + 3) * PITCH;
  const dh = (rows + 3) * PITCH;
  const drop = new THREE.Mesh(
    new THREE.PlaneGeometry(dw, dh),
    new THREE.MeshBasicMaterial({ visible: false, side: THREE.DoubleSide })
  );
  drop.position.set(cols * PITCH / 2, rows * PITCH / 2, dropZ);
  drop.userData.drop = true;
  drop.userData.ox = cols * PITCH / 2;
  drop.userData.oy = rows * PITCH / 2;
  shell.add(drop);
  g.rotation.x = -Math.PI / 2;
  return g;
}

function fitCamera() {
  if (!root || !camera || !controls) return;
  const hidden = [];
  root.traverse((o) => {
    if (o.userData && o.userData.drop) {
      hidden.push(o);
      o.visible = false;
    }
  });
  const box = new THREE.Box3().setFromObject(root);
  for (const o of hidden) o.visible = true;
  if (box.isEmpty()) return;
  const c = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const fov = (camera.fov * Math.PI) / 180;
  const aspect = Math.max(camera.aspect, 0.1);
  const fitH = size.y / 2 / Math.tan(fov / 2);
  const fitW = size.x / 2 / (Math.tan(fov / 2) * aspect);
  const dist = Math.max(fitH, fitW, size.z, 40) * 1.45;
  controls.target.copy(c);
  camera.position.set(c.x + dist * 0.75, c.y + dist * 0.62, c.z + dist * 0.82);
  camera.near = 0.5;
  camera.far = Math.max(4000, dist * 20);
  camera.updateProjectionMatrix();
  controls.update();
}

export function rebuildPreview() {
  if (!scene) return;
  if (root) {
    scene.remove(root);
    root.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of mats) m.dispose();
      }
    });
  }
  root = build(layout());
  scene.add(root);
  fitCamera();
}

function init() {
  const el = document.getElementById("view3d");
  if (!el) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x02080d);
  const w = Math.max(el.clientWidth, 1);
  const h = Math.max(el.clientHeight, 1);
  camera = new THREE.PerspectiveCamera(40, w / h, 1, 4000);
  camera.position.set(200, 170, 240);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(w, h);
  el.appendChild(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.85);
  dir.position.set(90, 160, 70);
  scene.add(dir);
  scene.add(new THREE.GridHelper(420, 16, 0x155e75, 0x0b2a33));
  rebuildPreview();
  const sizeView = () => {
    const nw = Math.max(el.clientWidth, 1);
    const nh = Math.max(el.clientHeight, 1);
    camera.aspect = nw / nh;
    camera.updateProjectionMatrix();
    renderer.setSize(nw, nh);
  };
  window.addEventListener("resize", sizeView);
  if (window.ResizeObserver) new ResizeObserver(sizeView).observe(el);
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.addEventListener("click", () => {
      viewMode = b.getAttribute("data-view");
      rebuildPreview();
    });
  });
  (function loop() {
    requestAnimationFrame(loop);
    controls.update();
    renderer.render(scene, camera);
  })();
}

const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();

function cellFromPointer(clientX, clientY) {
  if (!renderer || !camera || !root) return null;
  const el = renderer.domElement;
  const rect = el.getBoundingClientRect();
  if (rect.width < 1 || rect.height < 1) return null;
  ndc.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  ndc.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(ndc, camera);
  const drops = [];
  root.traverse((o) => {
    if (o.userData && o.userData.drop) drops.push(o);
  });
  const hits = raycaster.intersectObjects(drops, false);
  if (!hits.length) return null;
  const hit = hits[0];
  const loc = hit.object.worldToLocal(hit.point.clone());
  const ox = hit.object.userData.ox || 0;
  const oy = hit.object.userData.oy || 0;
  const c = Math.floor((loc.x + ox) / PITCH);
  const r = Math.floor((loc.y + oy) / PITCH);
  if (c < -2 || r < -2 || c > 16 || r > 16) return null;
  return { c: Math.max(0, Math.min(15, c)), r: Math.max(0, Math.min(15, r)) };
}

window.rebuildPreview = rebuildPreview;
window.PANEL_CELL_AT = cellFromPointer;
init();
