let LIB = { devices: [] };
let byId = {};
let layout = {
  cols: 5,
  rows: 4,
  inner_h: 25,
  edge_style: "round",
  edge_mm: 2,
  overlap: true,
  auto_size: true,
  face_tilt: 0,
  tilt_axis: "flat",
  tilts: [0, 0, 0, 0],
  devices: [],
  walls: [],
  hangs: [
    { side: "back", pos: 0, orient: "down" },
    { side: "back", pos: 4, orient: "down" },
  ],
};
window.PANEL_LAYOUT = layout;

function bumpPreview() {
  window.PANEL_LAYOUT = layout;
  window.PANEL_BY_ID = byId;
  if (window.rebuildPreview) window.rebuildPreview();
}

const $ = (id) => document.getElementById(id);

function numOr(v, d) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

function cloneLayout(src) {
  const l = JSON.parse(JSON.stringify(src || {}));
  if (!Array.isArray(l.devices)) l.devices = [];
  if (!Array.isArray(l.walls)) l.walls = [];
  if (!Array.isArray(l.tilts)) l.tilts = [];
  l.cols = numOr(l.cols, 5);
  l.rows = numOr(l.rows, 4);
  l.inner_h = numOr(l.inner_h, 25);
  l.edge_style = l.edge_style || "round";
  l.edge_mm = numOr(l.edge_mm, 2);
  l.overlap = l.overlap !== false;
  l.auto_size = l.auto_size !== false;
  l.face_tilt = Math.max(0, Math.min(45, numOr(l.face_tilt, 0)));
  if (l.tilt_axis !== "row" && l.tilt_axis !== "col") l.tilt_axis = "flat";
  if (!Array.isArray(l.hangs)) {
    l.hangs = l.hang === false ? [] : defaultHangs(l.cols);
  }
  return l;
}

function defaultHangs(cols) {
  const n = cols || 1;
  if (n > 1) {
    return [
      { side: "back", pos: 0, orient: "down" },
      { side: "back", pos: n - 1, orient: "down" },
    ];
  }
  return [{ side: "back", pos: 0, orient: "down" }];
}

function clipDevices() {
  layout.devices = layout.devices.filter((d) => {
    const def = byId[d.id];
    if (!def) return false;
    const dx = def.cells_x || 1;
    const dy = def.cells_y || 1;
    return d.c >= 0 && d.r >= 0 && d.c + dx <= layout.cols && d.r + dy <= layout.rows;
  });
}

function occMap() {
  const m = {};
  for (const d of layout.devices) {
    const def = byId[d.id];
    if (!def) continue;
    for (let x = 0; x < def.cells_x; x++) {
      for (let y = 0; y < def.cells_y; y++) {
        m[`${d.c + x},${d.r + y}`] = d;
      }
    }
  }
  return m;
}

function partSize(id) {
  const def = byId[id];
  return { dx: (def && def.cells_x) || 1, dy: (def && def.cells_y) || 1, def };
}

function overlapsOther(c, r, dx, dy, skip) {
  for (const d of layout.devices) {
    if (d === skip) continue;
    const dd = byId[d.id];
    if (!dd) continue;
    if (c < d.c + dd.cells_x && c + dx > d.c && r < d.r + dd.cells_y && r + dy > d.r) return true;
  }
  return false;
}

function ensureGrid(c, r, dx, dy) {
  if (c < 0 || r < 0) return false;
  const needC = c + dx;
  const needR = r + dy;
  if (needC > 16 || needR > 16) return false;
  let grew = false;
  if (needC > layout.cols) {
    layout.cols = needC;
    if ($("cols")) $("cols").value = layout.cols;
    grew = true;
  }
  if (needR > layout.rows) {
    layout.rows = needR;
    if ($("rows")) $("rows").value = layout.rows;
    grew = true;
  }
  if (grew) {
    padTilts();
    renderTilts();
  }
  return true;
}

function firstFit(dx, dy, skip) {
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c <= layout.cols - dx; c++) {
      if (r + dy <= layout.rows && !overlapsOther(c, r, dx, dy, skip)) return { c, r };
    }
  }
  if (layout.cols + dx <= 16 && layout.rows >= dy && !overlapsOther(layout.cols, 0, dx, dy, skip)) {
    return { c: layout.cols, r: 0 };
  }
  if (layout.rows + dy <= 16 && !overlapsOther(0, layout.rows, dx, dy, skip)) {
    return { c: 0, r: layout.rows };
  }
  if (layout.cols + dx <= 16) return { c: layout.cols, r: 0 };
  return null;
}

function refreshLayout(msg) {
  fitAutoSize();
  renderTilts();
  renderGrid();
  bumpPreview();
  renderBOM();
  if (msg && $("status")) $("status").textContent = msg;
}

function canPlaceId(id) {
  const def = byId[id];
  if (!def || def.id === "empty" || def.place === "wall" || def.place === "none") return null;
  return def;
}

function placeDevice(id, c, r, skip) {
  const def = canPlaceId(id);
  if (!def) {
    if ($("status")) $("status").textContent = "Pick a lid or floor part first.";
    return false;
  }
  const dx = def.cells_x || 1;
  const dy = def.cells_y || 1;
  c = Math.max(0, c | 0);
  r = Math.max(0, r | 0);
  if (!layout.auto_size) {
    if (c + dx > layout.cols && c < layout.cols) c = Math.max(0, layout.cols - dx);
    if (r + dy > layout.rows && r < layout.rows) r = Math.max(0, layout.rows - dy);
  }
  if (!ensureGrid(c, r, dx, dy)) {
    if ($("status")) $("status").textContent = `${def.name} needs ${dx} x ${dy} cells (max 16).`;
    return false;
  }
  if (skip) {
    if (overlapsOther(c, r, dx, dy, skip)) {
      if ($("status")) $("status").textContent = "That cell is taken.";
      return false;
    }
    skip.c = c;
    skip.r = r;
    refreshLayout(`Moved ${def.name} to ${c},${r}`);
    return true;
  }
  layout.devices = layout.devices.filter((d) => {
    const dd = byId[d.id];
    if (!dd) return false;
    const overlap =
      c < d.c + dd.cells_x && c + dx > d.c &&
      r < d.r + dd.cells_y && r + dy > d.r;
    return !overlap;
  });
  layout.devices.push({ id, c, r });
  refreshLayout(`Added ${def.name} at ${c},${r} (${layout.cols} x ${layout.rows})`);
  return true;
}

function addSelectedDevice() {
  const id = $("device")?.value;
  const def = canPlaceId(id);
  if (!def) {
    if ($("status")) $("status").textContent = "Pick a lid or floor part in the list, then Add device.";
    return;
  }
  const dx = def.cells_x || 1;
  const dy = def.cells_y || 1;
  const at = firstFit(dx, dy);
  if (!at) {
    if ($("status")) $("status").textContent = "No room left (max 16 x 16).";
    return;
  }
  placeDevice(id, at.c, at.r);
}

function removePlaced(d) {
  const i = layout.devices.indexOf(d);
  if (i < 0) return;
  const name = byId[d.id]?.name || d.id;
  layout.devices.splice(i, 1);
  refreshLayout(`Removed ${name}`);
}

function duplicatePlaced(d) {
  const def = canPlaceId(d.id);
  if (!def) return;
  const dx = def.cells_x || 1;
  const dy = def.cells_y || 1;
  const tries = [
    { c: d.c + dx, r: d.r },
    { c: d.c, r: d.r + dy },
    { c: d.c + dx, r: d.r + dy },
  ];
  for (const p of tries) {
    if (p.c + dx > 16 || p.r + dy > 16) continue;
    if (!ensureGrid(p.c, p.r, dx, dy)) continue;
    if (!overlapsOther(p.c, p.r, dx, dy)) {
      layout.devices.push({ id: d.id, c: p.c, r: p.r });
      refreshLayout(`Duplicated ${def.name} at ${p.c},${p.r}`);
      return;
    }
  }
  const at = firstFit(dx, dy);
  if (!at) {
    if ($("status")) $("status").textContent = "No room to duplicate.";
    return;
  }
  placeDevice(d.id, at.c, at.r);
}

function nStrips() {
  return layout.tilt_axis === "col" ? layout.cols : layout.rows;
}

function padTilts() {
  if (!Array.isArray(layout.tilts)) layout.tilts = [];
  const n = Math.max(1, nStrips());
  while (layout.tilts.length < n) layout.tilts.push(0);
  if (layout.tilt_axis === "flat") {
    for (let i = 0; i < n; i++) layout.tilts[i] = 0;
  }
}

const TILT_ANGLES = [-30, -15, 0, 15, 30, 45];
let foldSel = 0;
let foldDrag = null;

function snapTilt(deg) {
  let best = 0;
  let bestD = 1e9;
  for (const a of TILT_ANGLES) {
    const d = Math.abs(deg - a);
    if (d < bestD - 0.001 || (Math.abs(d - bestD) < 0.001 && (a === 0 || Math.abs(a) < Math.abs(best)))) {
      best = a;
      bestD = d;
    }
  }
  return best;
}

function stripName(mode, i, n) {
  if (n < 2) return mode === "col" ? "Column 1" : "Row 1";
  if (mode === "col") {
    if (i === 0) return "Left";
    if (i === n - 1) return "Right";
    return `Column ${i + 1}`;
  }
  if (i === 0) return "Front";
  if (i === n - 1) return "Back";
  return `Row ${i + 1}`;
}

function applyFold(i, deg, live) {
  padTilts();
  const a = snapTilt(deg);
  if ((Number(layout.tilts[i]) || 0) === a && live) return;
  layout.tilts[i] = a;
  if (live) {
    const cap = $("fold-caption");
    if (cap) cap.innerHTML = `<em>${stripName(layout.tilt_axis, i, nStrips())}</em>  ${a}°`;
    bumpPreview();
    return;
  }
  renderTilts();
  bumpPreview();
  renderBOM();
}

function renderTilts() {
  padTilts();
  const axis = $("tilt-axis");
  if (axis) {
    const v = layout.tilt_axis === "row" || layout.tilt_axis === "col" ? layout.tilt_axis : "flat";
    axis.value = v;
  }
  const help = $("tilt-help");
  const box = $("tilt-strips");
  const actions = $("tilt-actions");
  const match = $("tilt-match");
  if (!box) return;
  box.innerHTML = "";
  const mode = layout.tilt_axis || "flat";
  const n = nStrips();
  if (foldSel < 0 || foldSel >= n) foldSel = 0;
  if (mode === "flat") {
    if (help) help.textContent = "The lid stays one even sheet.";
    if (actions) actions.hidden = true;
    const wrap = document.createElement("div");
    wrap.className = "fold-schematic is-flat";
    wrap.innerHTML = '<p class="fold-caption"><em>FLAT</em></p>';
    box.appendChild(wrap);
    return;
  }
  if (actions) actions.hidden = false;
  if (match) match.disabled = foldSel == null;
  if (help) {
    help.textContent = mode === "col"
      ? "Each column leans on its own. 30° raises the right."
      : "Each row leans on its own. 30° raises the back.";
  }
  const L = Math.max(22, Math.min(40, 240 / Math.max(n, 1)));
  const hinges = [];
  let x = 0;
  let y = 0;
  for (let i = 0; i < n; i++) {
    const a = Number(layout.tilts[i]) || 0;
    const rad = (a * Math.PI) / 180;
    const x2 = x + L * Math.cos(rad);
    const y2 = y + L * Math.sin(rad);
    hinges.push({ i, x, y, x2, y2, a });
    x = x2 + 6 * Math.cos(rad);
    y = y2 + 6 * Math.sin(rad);
  }
  let minX = 0;
  let maxX = 0;
  let minY = 0;
  let maxY = 0;
  for (const h of hinges) {
    minX = Math.min(minX, h.x, h.x2);
    maxX = Math.max(maxX, h.x, h.x2);
    minY = Math.min(minY, -h.y, -h.y2);
    maxY = Math.max(maxY, -h.y, -h.y2);
  }
  const vb = 16;
  const svg = svgEl("svg", {
    class: "fold-svg",
    viewBox: `${minX - vb} ${minY - vb} ${maxX - minX + vb * 2} ${Math.max(36, maxY - minY) + vb * 2}`,
    width: "100%",
    height: "88",
    "aria-label": "Lid fold",
  });
  svg.style.touchAction = "none";
  svg.appendChild(svgEl("line", { class: "fold-datum", x1: minX - 8, y1: 0, x2: maxX + 8, y2: 0 }));
  for (const h of hinges) {
    const g = svgEl("g", { class: "fold-hit", "data-i": String(h.i) });
    const plate = svgEl("line", {
      class: "fold-plate" + (h.i === foldSel ? " is-on" : ""),
      x1: h.x,
      y1: -h.y,
      x2: h.x2,
      y2: -h.y2,
    });
    g.appendChild(plate);
    if (h.i === foldSel) {
      g.appendChild(svgEl("circle", { class: "fold-handle", cx: h.x2, cy: -h.y2, r: 7 }));
    }
    const hit = svgEl("line", {
      class: "fold-hot",
      x1: h.x,
      y1: -h.y,
      x2: h.x2,
      y2: -h.y2,
    });
    g.appendChild(hit);
    g.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      foldSel = h.i;
      foldDrag = {
        i: h.i,
        hx: h.x,
        hy: h.y,
        svg,
        startX: e.clientX,
        startY: e.clientY,
        moved: false,
      };
      try { g.setPointerCapture(e.pointerId); } catch { /* ignore */ }
      svg.querySelectorAll(".fold-plate").forEach((p, idx) => {
        p.classList.toggle("is-on", idx === h.i);
      });
      const cap = $("fold-caption");
      if (cap) cap.innerHTML = `<em>${stripName(mode, h.i, n)}</em>  ${h.a}°`;
      if (match) match.disabled = false;
    });
    g.addEventListener("dblclick", (e) => {
      e.preventDefault();
      applyFold(h.i, 0, false);
    });
    svg.appendChild(g);
  }
  const wrap = document.createElement("div");
  wrap.className = "fold-schematic";
  wrap.appendChild(svg);
  const ends = document.createElement("div");
  ends.className = "fold-ends";
  ends.innerHTML = mode === "col" ? "<span>Left</span><span>Right</span>" : "<span>Front</span><span>Back</span>";
  wrap.appendChild(ends);
  const cap = document.createElement("p");
  cap.className = "fold-caption";
  cap.id = "fold-caption";
  const a0 = Number(layout.tilts[foldSel]) || 0;
  cap.innerHTML = `<em>${stripName(mode, foldSel, n)}</em>  ${a0}°`;
  wrap.appendChild(cap);
  box.appendChild(wrap);
}

function updateSizeLock() {
  const on = !!layout.auto_size;
  if ($("autosize")) $("autosize").checked = on;
  if ($("cols")) $("cols").disabled = on;
  if ($("rows")) $("rows").disabled = on;
}

function deviceBounds() {
  let maxC = 0;
  let maxR = 0;
  let any = false;
  for (const d of layout.devices) {
    const def = byId[d.id];
    if (!def) continue;
    any = true;
    maxC = Math.max(maxC, d.c + (def.cells_x || 1));
    maxR = Math.max(maxR, d.r + (def.cells_y || 1));
  }
  return { any, maxC: Math.max(1, maxC), maxR: Math.max(1, maxR) };
}

function fitAutoSize() {
  if (!layout.auto_size) {
    updateSizeLock();
    return;
  }
  const b = deviceBounds();
  if (b.any) {
    layout.cols = Math.min(16, Math.max(1, b.maxC));
    layout.rows = Math.min(16, Math.max(1, b.maxR));
  } else {
    layout.cols = Math.min(16, Math.max(1, layout.cols || 4));
    layout.rows = Math.min(16, Math.max(1, layout.rows || 4));
  }
  if ($("cols")) $("cols").value = layout.cols;
  if ($("rows")) $("rows").value = layout.rows;
  padTilts();
  updateSizeLock();
}

function gridDims() {
  const grow = layout.auto_size && layout.cols < 16 && layout.rows < 16 ? 1 : 0;
  return {
    cols: Math.min(16, layout.cols + (layout.auto_size && layout.cols < 16 ? 1 : 0)),
    rows: Math.min(16, layout.rows + (layout.auto_size && layout.rows < 16 ? 1 : 0)),
    grow,
  };
}

function shortName(def) {
  let n = (def && (def.name || def.id)) || "part";
  n = n.replace(/^Adafruit\s+/i, "");
  n = n.replace(/\s*\([^)]*\)\s*$/, "");
  return n || "part";
}

function svgEl(name, attrs) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, String(v));
  return el;
}

function partGlyph(def) {
  const dx = def.cells_x || 1;
  const dy = def.cells_y || 1;
  const W = dx * 25.4;
  const H = dy * 25.4;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" });
  const cx = W / 2;
  const cy = H / 2;
  if (def.pcb_mm && def.pcb_mm.length >= 2) {
    const pw = def.pcb_mm[0];
    const ph = def.pcb_mm[1];
    svg.appendChild(svgEl("rect", {
      x: cx - pw / 2, y: cy - ph / 2, width: pw, height: ph, rx: 1.2, class: "glyph-pcb",
    }));
  }
  for (const cut of def.cutouts || []) {
    const x = cx + (cut.x || 0);
    const y = cy - (cut.y || 0);
    if (cut.type === "hole") {
      svg.appendChild(svgEl("circle", { cx: x, cy: y, r: (cut.d || 8) / 2, class: "glyph-cut" }));
    } else if (cut.type === "slot") {
      const w = cut.w || 4;
      const l = cut.l || 20;
      svg.appendChild(svgEl("rect", {
        x: x - w / 2, y: y - l / 2, width: w, height: l, rx: Math.min(w, l) / 2, class: "glyph-cut",
      }));
    } else if (cut.type === "window") {
      svg.appendChild(svgEl("rect", {
        x: x - (cut.w || 20) / 2, y: y - (cut.h || 12) / 2,
        width: cut.w || 20, height: cut.h || 12, rx: 1, class: "glyph-cut",
      }));
    } else if (cut.type === "grill") {
      const gw = cut.w || 12;
      for (const gy of [-3, 0, 3]) {
        svg.appendChild(svgEl("rect", {
          x: x - gw / 2, y: y + gy - 0.8, width: gw, height: 1.6, rx: 0.4, class: "glyph-cut",
        }));
      }
    }
  }
  return svg;
}

function cellFromPoint(x, y) {
  const g = $("grid");
  if (!g) return null;
  const vis = gridDims();
  if (vis.cols < 1 || vis.rows < 1) return null;
  const rec = g.getBoundingClientRect();
  const style = getComputedStyle(g);
  const padL = parseFloat(style.paddingLeft) || 0;
  const padT = parseFloat(style.paddingTop) || 0;
  const padR = parseFloat(style.paddingRight) || 0;
  const padB = parseFloat(style.paddingBottom) || 0;
  const gap = parseFloat(style.columnGap || style.gap) || 0;
  const innerW = rec.width - padL - padR;
  const innerH = rec.height - padT - padB;
  const cellW = (innerW - gap * Math.max(0, vis.cols - 1)) / vis.cols;
  const cellH = (innerH - gap * Math.max(0, vis.rows - 1)) / vis.rows;
  if (cellW <= 1 || cellH <= 1) return null;
  const c = Math.floor((x - rec.left - padL) / (cellW + gap));
  const r = Math.floor((y - rec.top - padT) / (cellH + gap));
  if (c < 0 || r < 0 || c >= vis.cols || r >= vis.rows) return null;
  return { c, r };
}

function clearDropHint() {
  $("grid")?.querySelectorAll(".drop-ok").forEach((el) => el.classList.remove("drop-ok"));
}

function showDropHint(c, r, dx, dy) {
  clearDropHint();
  if (c == null) return;
  const g = $("grid");
  if (!g) return;
  for (let y = 0; y < dy; y++) {
    for (let x = 0; x < dx; x++) {
      const el = g.querySelector(`.cell[data-c="${c + x}"][data-r="${r + y}"]`);
      if (el) el.classList.add("drop-ok");
    }
  }
}

let liveDrag = null;

function dragFootprint(e) {
  if (liveDrag) return liveDrag;
  const { placed, catalog } = dropPayload(e);
  if (placed !== "") {
    const d = layout.devices[Number(placed)];
    const def = d && byId[d.id];
    if (def) return { dx: def.cells_x || 1, dy: def.cells_y || 1 };
  }
  if (catalog && catalog !== "empty") {
    const def = byId[catalog];
    if (def) return { dx: def.cells_x || 1, dy: def.cells_y || 1 };
  }
  return { dx: 1, dy: 1 };
}

let boardDrag = null;
let skipClick = false;

function endBoardDrag(apply, ev) {
  const drag = boardDrag;
  boardDrag = null;
  clearDropHint();
  document.querySelectorAll(".part.dragging").forEach((el) => el.classList.remove("dragging"));
  if (!apply || !drag || !ev) return;
  skipClick = true;
  const at = cellFromPoint(ev.clientX, ev.clientY);
  if (!at) return;
  if (drag.kind === "placed") {
    const d = layout.devices[drag.index];
    if (d) placeDevice(d.id, at.c, at.r, d);
    return;
  }
  if (drag.id) placeDevice(drag.id, at.c, at.r);
}

function renderGrid() {
  const g = $("grid");
  if (!g) return;
  const vis = gridDims();
  g.style.gridTemplateColumns = `repeat(${vis.cols}, minmax(28px, 1fr))`;
  g.style.gridTemplateRows = `repeat(${vis.rows}, minmax(28px, 1fr))`;
  g.innerHTML = "";
  for (let r = 0; r < vis.rows; r++) {
    for (let c = 0; c < vis.cols; c++) {
      const el = document.createElement("div");
      el.className = "cell";
      const growC = c >= layout.cols;
      const growR = r >= layout.rows;
      if (growC) el.classList.add("grow", "grow-col");
      if (growR) el.classList.add("grow", "grow-row");
      el.style.gridColumn = String(c + 1);
      el.style.gridRow = String(r + 1);
      el.dataset.c = String(c);
      el.dataset.r = String(r);
      let cellLab = `cell column ${c} row ${r}`;
      if (growC && growR) cellLab = "grow corner";
      else if (growC) cellLab = "grow column";
      else if (growR) cellLab = "grow row";
      el.setAttribute("aria-label", cellLab);
      el.addEventListener("click", () => {
        if (skipClick) {
          skipClick = false;
          return;
        }
        stamp(c, r);
      });
      g.appendChild(el);
    }
  }
  layout.devices.forEach((hit, i) => {
    const def = byId[hit.id];
    if (!def) return;
    const dx = def.cells_x || 1;
    const dy = def.cells_y || 1;
    const el = document.createElement("div");
    el.className = "part" + (def.place === "bottom" ? " bottom" : "");
    el.style.gridColumn = `${hit.c + 1} / span ${dx}`;
    el.style.gridRow = `${hit.r + 1} / span ${dy}`;
    el.draggable = true;
    el.tabIndex = 0;
    el.setAttribute("aria-label", `${shortName(def)} at column ${hit.c} row ${hit.r}`);
    el.appendChild(partGlyph(def));
    const name = document.createElement("span");
    name.className = "part-name";
    name.textContent = shortName(def);
    el.appendChild(name);
    const actions = document.createElement("span");
    actions.className = "part-actions";
    const dup = document.createElement("button");
    dup.type = "button";
    dup.textContent = "+";
    dup.title = "Duplicate";
    dup.setAttribute("aria-label", "Duplicate");
    dup.addEventListener("click", (e) => {
      e.stopPropagation();
      duplicatePlaced(hit);
    });
    const rm = document.createElement("button");
    rm.type = "button";
    rm.className = "danger";
    rm.textContent = "×";
    rm.title = "Remove";
    rm.setAttribute("aria-label", "Remove");
    rm.addEventListener("click", (e) => {
      e.stopPropagation();
      removePlaced(hit);
    });
    actions.appendChild(dup);
    actions.appendChild(rm);
    el.appendChild(actions);
    el.addEventListener("dragstart", (e) => {
      if (boardDrag && boardDrag.moved) {
        e.preventDefault();
        return;
      }
      boardDrag = null;
      liveDrag = { dx, dy };
      e.dataTransfer.setData("application/x-panel-placed", String(i));
      e.dataTransfer.setData("text/plain", hit.id);
      e.dataTransfer.effectAllowed = "copyMove";
      el.classList.add("dragging");
    });
    el.addEventListener("dragend", () => {
      liveDrag = null;
      el.classList.remove("dragging");
      clearDropHint();
    });
    el.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      if (e.target.closest("button")) return;
      boardDrag = {
        kind: "placed",
        index: i,
        id: hit.id,
        startX: e.clientX,
        startY: e.clientY,
        moved: false,
      };
    });
    g.appendChild(el);
  });
}

function stamp(c, r) {
  const id = $("device").value;
  const def = byId[id];
  if (!def || def.id === "empty") {
    layout.devices = layout.devices.filter((d) => {
      const dd = byId[d.id];
      if (!dd) return false;
      return !(c >= d.c && c < d.c + dd.cells_x && r >= d.r && r < d.r + dd.cells_y);
    });
    refreshLayout("Cleared cell");
    return;
  }
  placeDevice(id, c, r);
}

function fillDevices() {
  const sel = $("device");
  const wsel = $("wall-dev");
  const q = ($("devfilter")?.value || "").toLowerCase();
  const keepDev = sel.value;
  const keepWall = wsel.value;
  sel.innerHTML = "";
  wsel.innerHTML = "";
  const rest = [];
  let emptyOpt = null;
  for (const d of LIB.devices) {
    byId[d.id] = d;
    if (d.place === "wall") {
      const w = document.createElement("option");
      w.value = d.id;
      w.textContent = d.name;
      wsel.appendChild(w);
    }
    const hay = `${d.category} ${d.name} ${d.brand || ""} ${d.id}`.toLowerCase();
    if (q && d.id !== "empty" && !hay.includes(q)) continue;
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = d.id === "empty" ? "eraser — click a cell to clear" : `${d.category}: ${d.name}`;
    if (d.id === "empty") emptyOpt = opt;
    else rest.push(opt);
  }
  for (const o of rest) sel.appendChild(o);
  if (emptyOpt) sel.appendChild(emptyOpt);
  if (keepDev && [...sel.options].some((o) => o.value === keepDev)) sel.value = keepDev;
  else if (![...sel.options].some((o) => o.value === sel.value) && rest[0]) sel.value = rest[0].value;
  if (keepWall && [...wsel.options].some((o) => o.value === keepWall)) wsel.value = keepWall;
  if (!sel.dataset.bound) {
    sel.dataset.bound = "1";
    sel.addEventListener("change", () => {
      showDevice(byId[sel.value]);
    });
  }
  if (sel.value) showDevice(byId[sel.value]);
}

function showDevice(d) {
  const info = $("devinfo");
  const link = $("devurl");
  if (!d) {
    info.textContent = "";
    link.hidden = true;
    return;
  }
  info.textContent = `${d.cells_x} x ${d.cells_y} cells. place ${d.place}. ${d.brand || ""}`;
  if (d.url) {
    link.hidden = false;
    link.href = d.url;
    link.textContent = `Manufacturer page — ${d.name}`;
  } else {
    link.hidden = true;
  }
  loadPartCases(d.id);
}

function renderWalls() {
  const ul = $("walls");
  ul.innerHTML = "";
  layout.walls.forEach((w, i) => {
    const li = document.createElement("li");
    li.textContent = `${w.side} pos ${w.pos}: ${byId[w.id]?.name || w.id} `;
    const rm = document.createElement("button");
    rm.textContent = "remove";
    rm.onclick = () => {
      layout.walls.splice(i, 1);
      renderWalls();
    };
    li.appendChild(rm);
    ul.appendChild(li);
  });
  bumpPreview();
  renderBOM();
}

function renderHangs() {
  const ul = $("hangs");
  if (!ul) return;
  ul.innerHTML = "";
  if (!Array.isArray(layout.hangs)) layout.hangs = [];
  layout.hangs.forEach((h, i) => {
    const li = document.createElement("li");
    li.textContent = `${h.side} cell ${h.pos}, slot ${h.orient || "down"} `;
    const rm = document.createElement("button");
    rm.textContent = "remove";
    rm.onclick = () => {
      layout.hangs.splice(i, 1);
      renderHangs();
    };
    li.appendChild(rm);
    ul.appendChild(li);
  });
  bumpPreview();
  renderBOM();
}

function syncSize() {
  layout.auto_size = $("autosize") ? $("autosize").checked : true;
  if (!layout.auto_size) {
    layout.cols = numOr($("cols").value, 1);
    layout.rows = numOr($("rows").value, 1);
    clipDevices();
  } else {
    fitAutoSize();
  }
  layout.inner_h = numOr($("inner").value, 25);
  layout.edge_style = $("edge")?.value || "round";
  layout.edge_mm = numOr($("edgemm")?.value, 2);
  layout.overlap = $("overlap") ? $("overlap").checked : true;
  layout.face_tilt = $("facetilt") ? numOr($("facetilt").value, 0) : 0;
  updateSizeLock();
  renderTilts();
  renderGrid();
  bumpPreview();
  renderBOM();
}

function setEdgeInputs(style, mm) {
  if ($("edge")) $("edge").value = style || "round";
  if ($("edgemm")) $("edgemm").value = numOr(mm, 2);
}

function setOverlap(on) {
  if ($("overlap")) $("overlap").checked = !!on;
}

function setFaceTilt(deg) {
  const n = Math.max(0, Math.min(45, numOr(deg, 0)));
  const el = $("facetilt");
  if (!el) return;
  const s = String(n);
  if (![...el.options].some((o) => o.value === s)) {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = `${n}°`;
    el.appendChild(opt);
  }
  el.value = s;
}

function clearNotes() {
  if ($("notelist")) $("notelist").innerHTML = "";
  if ($("notetext")) $("notetext").value = "";
}

$("autosize")?.addEventListener("change", syncSize);
$("cols").addEventListener("input", syncSize);
$("rows").addEventListener("input", syncSize);
$("inner").addEventListener("input", syncSize);
$("edge").addEventListener("change", syncSize);
$("edgemm").addEventListener("input", syncSize);
$("overlap")?.addEventListener("change", syncSize);
$("facetilt")?.addEventListener("change", syncSize);
$("tilt-axis")?.addEventListener("change", () => {
  layout.tilt_axis = $("tilt-axis").value || "flat";
  padTilts();
  renderTilts();
  bumpPreview();
  renderBOM();
});
$("tilt-all-0")?.addEventListener("click", () => {
  padTilts();
  for (let i = 0; i < nStrips(); i++) layout.tilts[i] = 0;
  renderTilts();
  bumpPreview();
  renderBOM();
});
$("tilt-match")?.addEventListener("click", () => {
  padTilts();
  const a = Number(layout.tilts[foldSel]) || 0;
  for (let i = 0; i < nStrips(); i++) layout.tilts[i] = a;
  renderTilts();
  bumpPreview();
  renderBOM();
});
document.addEventListener("pointermove", (e) => {
  if (!foldDrag) return;
  const dx = e.clientX - foldDrag.startX;
  const dy = e.clientY - foldDrag.startY;
  if (!foldDrag.moved && dx * dx + dy * dy < 64) return;
  foldDrag.moved = true;
  const ctm = foldDrag.svg.getScreenCTM();
  if (!ctm) return;
  const p = foldDrag.svg.createSVGPoint();
  p.x = e.clientX;
  p.y = e.clientY;
  const loc = p.matrixTransform(ctm.inverse());
  const mx = loc.x - foldDrag.hx;
  const my = -loc.y - foldDrag.hy;
  const deg = Math.atan2(my, mx) * (180 / Math.PI);
  applyFold(foldDrag.i, deg, true);
});
document.addEventListener("pointerup", () => {
  if (!foldDrag) return;
  const drag = foldDrag;
  foldDrag = null;
  renderTilts();
  if (drag.moved) renderBOM();
});
document.addEventListener("pointercancel", () => { foldDrag = null; });
$("devfilter").addEventListener("input", fillDevices);
$("add-wall").addEventListener("click", () => {
  layout.walls.push({
    side: $("wall-side").value,
    id: $("wall-dev").value,
    pos: Number($("wall-pos").value) || 0,
  });
  renderWalls();
});
$("add-dev")?.addEventListener("click", () => addSelectedDevice());
$("device")?.addEventListener("dblclick", () => addSelectedDevice());
$("devdrag")?.addEventListener("dragstart", (e) => {
  const id = $("device")?.value || "";
  const sz = partSize(id);
  liveDrag = { dx: sz.dx, dy: sz.dy };
  e.dataTransfer.setData("application/x-panel-device", id);
  e.dataTransfer.setData("text/plain", id);
  e.dataTransfer.effectAllowed = "copy";
});
$("devdrag")?.addEventListener("dragend", () => {
  liveDrag = null;
  clearDropHint();
});

function dropPayload(e) {
  const placed = e.dataTransfer.getData("application/x-panel-placed");
  const catalog = e.dataTransfer.getData("application/x-panel-device") || e.dataTransfer.getData("text/plain");
  return { placed, catalog };
}

function handleDropAt(c, r, e) {
  const { placed, catalog } = dropPayload(e);
  if (placed !== "") {
    const d = layout.devices[Number(placed)];
    if (d) placeDevice(d.id, c, r, d);
    return;
  }
  if (catalog && catalog !== "empty") placeDevice(catalog, c, r);
}

function bindDropTarget(el, from3d) {
  if (!el || el.dataset.dropBound) return;
  el.dataset.dropBound = "1";
  el.addEventListener("dragover", (e) => {
    e.preventDefault();
    el.classList.add("drop-over");
    if (!from3d) {
      const at = cellFromPoint(e.clientX, e.clientY);
      const fp = dragFootprint(e);
      if (at) showDropHint(at.c, at.r, fp.dx, fp.dy);
    }
  });
  el.addEventListener("dragleave", (e) => {
    if (!el.contains(e.relatedTarget)) {
      el.classList.remove("drop-over");
      if (!from3d) clearDropHint();
    }
  });
  el.addEventListener("drop", (e) => {
    e.preventDefault();
    el.classList.remove("drop-over");
    clearDropHint();
    if (from3d) {
      const at = window.PANEL_CELL_AT && window.PANEL_CELL_AT(e.clientX, e.clientY);
      if (!at) {
        if ($("status")) $("status").textContent = "Drop on the lid of the case.";
        return;
      }
      handleDropAt(at.c, at.r, e);
      return;
    }
    const at = cellFromPoint(e.clientX, e.clientY);
    if (!at) return;
    handleDropAt(at.c, at.r, e);
  });
}
bindDropTarget($("grid"), false);
bindDropTarget($("view3d"), true);

document.addEventListener("pointermove", (e) => {
  if (!boardDrag || boardDrag.kind !== "placed") return;
  const dx = e.clientX - boardDrag.startX;
  const dy = e.clientY - boardDrag.startY;
  if (!boardDrag.moved) {
    if (dx * dx + dy * dy < 36) return;
    boardDrag.moved = true;
    const g = $("grid");
    const part = g && g.querySelectorAll(".part")[boardDrag.index];
    if (part) {
      part.classList.add("dragging");
      try { part.setPointerCapture(e.pointerId); } catch { /* ignore */ }
    }
  }
  const at = cellFromPoint(e.clientX, e.clientY);
  const d = layout.devices[boardDrag.index];
  const def = d && byId[d.id];
  showDropHint(at && at.c, at && at.r, (def && def.cells_x) || 1, (def && def.cells_y) || 1);
});
document.addEventListener("pointerup", (e) => {
  if (!boardDrag) return;
  const apply = boardDrag.moved;
  endBoardDrag(apply, e);
});
document.addEventListener("pointercancel", () => endBoardDrag(false));

$("add-hang")?.addEventListener("click", () => {
  if (!Array.isArray(layout.hangs)) layout.hangs = [];
  layout.hangs.push({
    side: $("hang-side").value,
    pos: Number($("hang-pos").value) || 0,
    orient: $("hang-orient").value || "down",
  });
  renderHangs();
});
$("preset-sq").addEventListener("click", () => {
  currentCaseId = "";
  saveFolderId = $("folder")?.value || "";
  if ($("casetitle")) $("casetitle").value = "3 sliders + 2 quad rotaries";
  $("cols").value = 5;
  $("rows").value = 4;
  $("inner").value = 25;
  setEdgeInputs("round", 2);
  setOverlap(true);
  setFaceTilt(0);
  clearNotes();
  layout = {
    cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, overlap: true, auto_size: true, face_tilt: 0, tilt_axis: "flat", tilts: [0, 0, 0, 0], walls: [],
    hangs: defaultHangs(5),
    devices: [
      { id: "neoslider", c: 0, r: 0 },
      { id: "neoslider", c: 1, r: 0 },
      { id: "neoslider", c: 2, r: 0 },
      { id: "quad_rotary", c: 3, r: 0 },
      { id: "quad_rotary", c: 4, r: 0 },
    ],
  };
  updateSizeLock();
  syncSize();
  renderHangs();
});
$("preset-tilt").addEventListener("click", () => {
  currentCaseId = "";
  saveFolderId = $("folder")?.value || "";
  if ($("casetitle")) $("casetitle").value = "tilt demo";
  $("cols").value = 4;
  $("rows").value = 6;
  $("inner").value = 25;
  setEdgeInputs("round", 2);
  setOverlap(true);
  setFaceTilt(0);
  clearNotes();
  layout = {
    cols: 4, rows: 6, inner_h: 25, edge_style: "round", edge_mm: 2, overlap: true, auto_size: true, face_tilt: 0, tilt_axis: "row",
    tilts: [0, 0, 0, 30, 30, -30],
    devices: [],
    walls: [],
    hangs: defaultHangs(4),
  };
  updateSizeLock();
  syncSize();
  renderHangs();
});
$("go").addEventListener("click", async () => {
  const btn = $("go");
  btn.disabled = true;
  $("status").textContent = "Building zip…";
  try {
    const payload = { ...layout, title: $("casetitle")?.value || "" };
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      $("status").textContent = await res.text();
      return;
    }
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const dispo = res.headers.get("Content-Disposition") || "";
    const m = /filename="([^"]+)"/.exec(dispo);
    a.download = m ? m[1] : "panel-case.zip";
    a.click();
    $("status").textContent = `zip ${blob.size} bytes. BOM, OpenSCAD, and case.3mf (when STL rendered) are inside. Print the lid face-down.`;
  } catch (e) {
    $("status").textContent = String(e);
  } finally {
    btn.disabled = false;
  }
});
$("bambu")?.addEventListener("click", async () => {
  const btn = $("bambu");
  btn.disabled = true;
  $("status").textContent = "Building Bambu Studio project…";
  try {
    const payload = { ...layout, title: $("casetitle")?.value || "" };
    const res = await fetch("/api/bambu-open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch { data = null; }
    if (!res.ok) {
      $("status").textContent = (data && data.error) || text || res.status;
      return;
    }
    if (data && data.url) {
      const a = document.createElement("a");
      a.href = data.url;
      a.download = data.name || "panel-case.3mf";
      a.click();
    }
    const ua = navigator.userAgent || "";
    const mac = /Mac|iPhone|iPad/i.test(ua);
    const href = mac ? data.open_macos : data.open_windows;
    if (href) {
      window.location.href = href;
    }
    $("status").textContent = "Opened Bambu Studio (or downloaded case.3mf). Tray and lid are on one plate.";
  } catch (e) {
    $("status").textContent = String(e);
  } finally {
    btn.disabled = false;
  }
});

let signedIn = false;
let currentCaseId = "";
let saveFolderId = "";
let persistBusy = false;

function screwLabel(d) {
  if (!(d > 0)) return "";
  if (d < 2.35) return "M2x6 screw into PCB";
  if (d < 2.75) return "M2.5x6 screw into PCB";
  return "M3x6 screw into PCB";
}

function renderBOM() {
  const tb = document.querySelector("#bom tbody");
  if (!tb) return;
  tb.innerHTML = "";
  const lines = [];
  lines.push({
    qty: 1,
    item: (layout.face_tilt || 0) > 0.05
      ? `Bottom tray (printed, sitting face tilt ${Number(layout.face_tilt)} deg)`
      : "Bottom tray (printed)",
    url: "",
  });
  lines.push({
    qty: 1,
    item: layout.overlap !== false
      ? "Lid (printed, face on bed, rounded top overhang)"
      : "Lid (printed, face on bed, flush — no overhang)",
    url: "",
  });
  const screws = {};
  for (const d of layout.devices) {
    const def = byId[d.id];
    if (!def || !(def.holes || []).length) continue;
    const lab = screwLabel(def.hole_d);
    if (!lab) continue;
    screws[lab] = (screws[lab] || 0) + def.holes.length;
  }
  let posts = 0;
  for (let r = 0; r < layout.rows; r++) {
    const t = (layout.tilts && layout.tilts[r]) || 0;
    if (Math.abs(t) < 0.05) posts += 2;
  }
  const firstTilt = Math.abs((layout.tilts && layout.tilts[0]) || 0) < 0.05;
  const lastTilt = Math.abs((layout.tilts && layout.tilts[layout.rows - 1]) || 0) < 0.05;
  if (firstTilt && lastTilt) posts += layout.cols > 1 ? 2 * (layout.cols - 1) : 2;
  else if (firstTilt || lastTilt) posts += layout.cols > 1 ? (layout.cols - 1) : 1;
  if (posts) lines.push({ qty: posts, item: "M3 screw from below (tray into lid peg)", url: "" });
  if ((layout.hangs || []).length) {
    lines.push({ qty: layout.hangs.length, item: "Wall screw for keyhole (#8 / M4)", url: "" });
  }
  for (const lab of Object.keys(screws).sort()) {
    lines.push({ qty: screws[lab], item: lab, url: "" });
  }
  const qty = {};
  const add = (id) => {
    if (!id || id === "empty") return;
    qty[id] = (qty[id] || 0) + 1;
  };
  for (const d of layout.devices) add(d.id);
  for (const w of layout.walls) add(w.id);
  for (const id of Object.keys(qty).sort()) {
    const def = byId[id] || {};
    lines.push({ qty: qty[id], item: def.name || id, url: def.url || "" });
  }
  for (const row of lines) {
    const tr = document.createElement("tr");
    const q = document.createElement("td");
    q.textContent = row.qty;
    const n = document.createElement("td");
    if (row.url) {
      const a = document.createElement("a");
      a.href = row.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = row.item;
      n.appendChild(a);
    } else n.textContent = row.item;
    tr.appendChild(q);
    tr.appendChild(n);
    tb.appendChild(tr);
  }
}

async function api(path, opt) {
  const res = await fetch(path, opt);
  if (res.status === 204) return null;
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) throw new Error((data && data.error) || text || res.status);
  return data;
}

function applyCase(rec) {
  currentCaseId = rec.id;
  saveFolderId = rec.folder_id || "";
  $("casetitle").value = rec.title || "";
  if ($("folder")) $("folder").value = rec.folder_id || "";
  layout = cloneLayout(rec.layout);
  updateSizeLock();
  $("cols").value = layout.cols;
  $("rows").value = layout.rows;
  $("inner").value = layout.inner_h;
  setEdgeInputs(layout.edge_style, layout.edge_mm);
  setOverlap(layout.overlap !== false);
  setFaceTilt(layout.face_tilt);
  syncSize();
  renderWalls();
  renderHangs();
  loadNotes().catch((e) => { $("status").textContent = String(e); });
}

function resetOpenCase() {
  currentCaseId = "";
  saveFolderId = $("folder")?.value || "";
  $("casetitle").value = "";
  clearNotes();
  $("cols").value = 5;
  $("rows").value = 4;
  $("inner").value = 25;
  setEdgeInputs("round", 2);
  setOverlap(true);
  setFaceTilt(0);
  layout = { cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, overlap: true, auto_size: true, face_tilt: 0, tilt_axis: "flat", tilts: [0, 0, 0, 0], devices: [], walls: [], hangs: defaultHangs(5) };
  updateSizeLock();
  syncSize();
  renderWalls();
  renderHangs();
}

async function refreshFolders() {
  const list = await api("/api/folders");
  const sel = $("folder");
  const cur = sel.value;
  sel.innerHTML = `<option value="">(no folder)</option>`;
  for (const f of list) {
    const o = document.createElement("option");
    o.value = f.id;
    o.textContent = f.name;
    sel.appendChild(o);
  }
  if (cur) sel.value = cur;
}

async function refreshCases() {
  const folder = $("folder").value;
  const q = folder ? `/api/cases?folder=${encodeURIComponent(folder)}` : "/api/cases";
  const list = await api(q);
  const ul = $("caselist");
  ul.innerHTML = "";
  for (const rec of list) {
    const li = document.createElement("li");
    li.textContent = rec.title;
    li.onclick = () => applyCase(rec);
    const rm = document.createElement("button");
    rm.textContent = "delete";
    rm.onclick = async (ev) => {
      ev.stopPropagation();
      if (!confirm(`Delete case “${rec.title}”?`)) return;
      try {
        await api(`/api/cases/${rec.id}`, { method: "DELETE" });
        if (currentCaseId === rec.id) {
          resetOpenCase();
          $("status").textContent = "case deleted";
        }
        await refreshCases();
      } catch (e) {
        $("status").textContent = String(e);
      }
    };
    li.appendChild(rm);
    ul.appendChild(li);
  }
}

async function loadNotes() {
  const ul = $("notelist");
  ul.innerHTML = "";
  if (!currentCaseId) return;
  try {
    const list = await api(`/api/cases/${currentCaseId}/notes`);
    for (const n of list) {
      const li = document.createElement("li");
      li.textContent = n.text;
      const rm = document.createElement("button");
      rm.textContent = "delete";
      rm.onclick = async () => {
        if (!confirm("Delete this note?")) return;
        try {
          await api(`/api/cases/${currentCaseId}/notes/${n.id}`, { method: "DELETE" });
          await loadNotes();
        } catch (e) {
          $("status").textContent = String(e);
        }
      };
      li.appendChild(rm);
      ul.appendChild(li);
    }
  } catch (e) {
    $("status").textContent = String(e);
  }
}

async function loadPartCases(part) {
  const ul = $("partcases");
  if (!ul) return;
  ul.innerHTML = "";
  const hint = $("partcases-hint");
  if (hint) hint.hidden = signedIn;
  if (!signedIn || !part) return;
  try {
    const list = await api(`/api/parts/${encodeURIComponent(part)}/cases`);
    for (const rec of list) {
      const li = document.createElement("li");
      li.textContent = rec.title;
      li.onclick = () => applyCase(rec);
      ul.appendChild(li);
    }
    if (!list.length) {
      const li = document.createElement("li");
      li.textContent = "none saved yet";
      ul.appendChild(li);
    }
  } catch (e) {
    const msg = String(e);
    if (!/sign in/i.test(msg) && !/401/.test(msg)) $("status").textContent = msg;
  }
}

async function bootLibrary() {
  const me = await api("/api/me");
  signedIn = !!me.login;
  document.body.classList.toggle("signed-in", signedIn);
  $("wholabel").textContent = signedIn ? (me.name || me.email || "signed in") : "not signed in";
  $("loginbtn").hidden = signedIn;
  $("logoutbtn").hidden = !signedIn;
  $("libhint").hidden = signedIn;
  $("libbody").hidden = !signedIn;
  if ($("partcases-hint")) $("partcases-hint").hidden = signedIn;
  if (!signedIn) return;
  saveFolderId = $("folder")?.value || "";
  await refreshFolders();
  await refreshCases();
  const dev = $("device")?.value;
  if (dev) await loadPartCases(dev);
}

$("dosearch")?.addEventListener("click", async () => {
  const q = $("q").value.trim();
  const ul = $("hits");
  ul.innerHTML = "";
  if (!q) return;
  let hits;
  try {
    hits = await api(`/api/search?q=${encodeURIComponent(q)}`);
  } catch (e) {
    $("status").textContent = String(e);
    return;
  }
  for (const h of hits) {
    const li = document.createElement("li");
    li.textContent = `${h.kind}: ${h.title || ""} ${h.text || ""}`.trim();
    li.onclick = async () => {
      if (h.kind === "case") applyCase(await api(`/api/cases/${h.id}`));
      if (h.kind === "note" && h.case_id) applyCase(await api(`/api/cases/${h.case_id}`));
      if (h.kind === "folder") {
        $("folder").value = h.id;
        await refreshCases();
      }
    };
    ul.appendChild(li);
  }
});
$("q")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("dosearch").click();
});
$("addfolder")?.addEventListener("click", async () => {
  const name = $("foldername").value.trim();
  if (!name) return;
  try {
    const f = await api("/api/folders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    $("foldername").value = "";
    await refreshFolders();
    $("folder").value = f.id;
    await refreshCases();
  } catch (e) {
    $("status").textContent = String(e);
  }
});
$("delfolder")?.addEventListener("click", async () => {
  const id = $("folder").value;
  if (!id) return;
  const name = $("folder").selectedOptions[0]?.textContent || "folder";
  if (!confirm(`Delete folder “${name}”? Cases move to no folder.`)) return;
  try {
    await api(`/api/folders/${id}`, { method: "DELETE" });
    if (saveFolderId === id) saveFolderId = "";
    await refreshFolders();
    await refreshCases();
  } catch (e) {
    $("status").textContent = String(e);
  }
});
$("folder")?.addEventListener("change", () => {
  refreshCases().catch((e) => { $("status").textContent = String(e); });
});
async function persistCase(asCopy) {
  if (persistBusy) return;
  persistBusy = true;
  $("savecase") && ($("savecase").disabled = true);
  $("saveas") && ($("saveas").disabled = true);
  try {
    const rec = {
      id: asCopy ? undefined : (currentCaseId || undefined),
      title: $("casetitle").value.trim() || "Untitled case",
      folder_id: saveFolderId,
      layout,
    };
    const updating = !asCopy && currentCaseId;
    const out = await api(updating ? `/api/cases/${currentCaseId}` : "/api/cases", {
      method: updating ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rec),
    });
    currentCaseId = out.id;
    saveFolderId = out.folder_id || "";
    $("status").textContent = `saved ${out.title}`;
    await refreshCases();
    await loadNotes();
  } finally {
    persistBusy = false;
    $("savecase") && ($("savecase").disabled = false);
    $("saveas") && ($("saveas").disabled = false);
  }
}
$("savecase")?.addEventListener("click", async () => {
  try { await persistCase(false); } catch (e) { $("status").textContent = String(e); }
});
$("saveas")?.addEventListener("click", async () => {
  const t = $("casetitle").value.trim() || "Untitled case";
  if (!/ copy$/i.test(t)) $("casetitle").value = `${t} copy`;
  try { await persistCase(true); } catch (e) { $("status").textContent = String(e); }
});
$("newcase")?.addEventListener("click", () => {
  resetOpenCase();
  $("status").textContent = "new empty case — not saved yet";
});
$("addnote")?.addEventListener("click", async () => {
  if (!currentCaseId) {
    $("status").textContent = "save the case before adding a note";
    return;
  }
  const text = $("notetext").value.trim();
  if (!text) return;
  try {
    await api(`/api/cases/${currentCaseId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    $("notetext").value = "";
    await loadNotes();
  } catch (e) {
    $("status").textContent = String(e);
  }
});

const TAB_NAMES = ["library", "case", "device", "bom"];
function setTab(name) {
  if (name === "parts") name = "device";
  if (name === "view" || !TAB_NAMES.includes(name)) name = "case";
  for (const t of TAB_NAMES) document.body.classList.toggle("tab-" + t, t === name);
  document.querySelectorAll("#side-tabs [data-tab]").forEach((b) => {
    const on = b.getAttribute("data-tab") === name;
    b.classList.toggle("on", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
    if (on) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  requestAnimationFrame(() => {
    if (window.rebuildPreview) window.rebuildPreview();
  });
  try {
    if (location.hash.replace("#", "") !== name) history.replaceState(null, "", "#" + name);
  } catch { /* ignore */ }
}
document.querySelectorAll("#side-tabs [data-tab]").forEach((b) => {
  b.addEventListener("click", () => setTab(b.getAttribute("data-tab")));
});
window.addEventListener("hashchange", () => setTab(location.hash.replace("#", "")));
if (location.hash) setTab(location.hash.replace("#", ""));

const brand = $("brand");
const brandBtn = $("brandbtn");
if (brand && brandBtn) {
  brandBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = !brand.classList.contains("open");
    brand.classList.toggle("open", open);
    brandBtn.setAttribute("aria-expanded", open ? "true" : "false");
  });
  document.addEventListener("click", (e) => {
    if (!brand.contains(e.target)) {
      brand.classList.remove("open");
      brandBtn.setAttribute("aria-expanded", "false");
    }
  });
}

fetch("/api/devices")
  .then((r) => r.json())
  .then((j) => {
    LIB = j;
    fillDevices();
    window.PANEL_BY_ID = byId;
    syncSize();
    $("preset-sq").click();
    renderBOM();
    bootLibrary().catch((e) => {
      $("status").textContent = String(e);
    });
  })
  .catch((e) => {
    $("status").textContent = String(e);
    bootLibrary().catch((err) => { $("status").textContent = String(err); });
  });
