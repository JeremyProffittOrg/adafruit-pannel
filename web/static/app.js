let LIB = { devices: [] };
let byId = {};
let layout = {
  cols: 5,
  rows: 4,
  inner_h: 25,
  edge_style: "round",
  edge_mm: 2,
  hang: true,
  overlap: true,
  tilts: [0, 0, 0, 0],
  devices: [],
  walls: [],
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
  l.hang = l.hang !== false;
  l.overlap = l.overlap !== false;
  return l;
}

function hangXs(cols) {
  const span = (cols || 1) * 25.4;
  if (span > 28) {
    const inset = Math.min(25.4 / 2, span / 2 - 6);
    return [inset, span - inset];
  }
  return [span / 2];
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

function renderTilts() {
  const box = $("tilts");
  box.innerHTML = "";
  layout.tilts.length = layout.rows;
  for (let i = 0; i < layout.rows; i++) {
    if (layout.tilts[i] == null) layout.tilts[i] = 0;
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    const lab = document.createElement("label");
    lab.htmlFor = `tilt-${i}`;
    lab.textContent = `Row ${i}`;
    th.appendChild(lab);
    const td = document.createElement("td");
    const inp = document.createElement("input");
    inp.id = `tilt-${i}`;
    inp.type = "number";
    inp.value = layout.tilts[i];
    inp.step = 5;
    inp.addEventListener("input", () => {
      layout.tilts[i] = Number(inp.value) || 0;
      bumpPreview();
      renderBOM();
    });
    td.appendChild(inp);
    tr.appendChild(th);
    tr.appendChild(td);
    box.appendChild(tr);
  }
}

function renderGrid() {
  const g = $("grid");
  g.style.gridTemplateColumns = `repeat(${layout.cols}, 1fr)`;
  g.innerHTML = "";
  const occ = occMap();
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c < layout.cols; c++) {
      const el = document.createElement("button");
      el.type = "button";
      el.className = "cell";
      const hit = occ[`${c},${r}`];
      if (hit) {
        el.classList.add(byId[hit.id]?.place === "bottom" ? "bottom" : "on");
        if (hit.c === c && hit.r === r) el.textContent = byId[hit.id]?.name || hit.id;
        else el.textContent = "";
        el.setAttribute("aria-label", `${byId[hit.id]?.name || hit.id} at column ${c} row ${r}`);
      } else {
        el.textContent = `${c},${r}`;
        el.setAttribute("aria-label", `empty cell column ${c} row ${r}`);
      }
      el.addEventListener("click", () => stamp(c, r));
      g.appendChild(el);
    }
  }
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
    renderGrid();
    bumpPreview();
    renderBOM();
    return;
  }
  if (c + def.cells_x > layout.cols || r + def.cells_y > layout.rows) {
    $("status").textContent = `${def.name} needs ${def.cells_x} x ${def.cells_y} cells`;
    return;
  }
  layout.devices = layout.devices.filter((d) => {
    const dd = byId[d.id];
    if (!dd) return false;
    const overlap =
      c < d.c + dd.cells_x && c + def.cells_x > d.c &&
      r < d.r + dd.cells_y && r + def.cells_y > d.r;
    return !overlap;
  });
  layout.devices.push({ id, c, r });
  renderGrid();
  bumpPreview();
  renderBOM();
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

function syncSize() {
  layout.cols = numOr($("cols").value, 1);
  layout.rows = numOr($("rows").value, 1);
  layout.inner_h = numOr($("inner").value, 25);
  layout.edge_style = $("edge")?.value || "round";
  layout.edge_mm = numOr($("edgemm")?.value, 2);
  layout.hang = $("hang") ? $("hang").checked : true;
  layout.overlap = $("overlap") ? $("overlap").value !== "no" : true;
  clipDevices();
  renderTilts();
  renderGrid();
  bumpPreview();
  renderBOM();
}

function setEdgeInputs(style, mm) {
  if ($("edge")) $("edge").value = style || "round";
  if ($("edgemm")) $("edgemm").value = numOr(mm, 2);
}

function setHang(on) {
  if ($("hang")) $("hang").checked = !!on;
}

function setOverlap(on) {
  if ($("overlap")) $("overlap").value = on ? "yes" : "no";
}

function clearNotes() {
  if ($("notelist")) $("notelist").innerHTML = "";
  if ($("notetext")) $("notetext").value = "";
}

$("cols").addEventListener("input", syncSize);
$("rows").addEventListener("input", syncSize);
$("inner").addEventListener("input", syncSize);
$("edge").addEventListener("change", syncSize);
$("edgemm").addEventListener("input", syncSize);
$("hang")?.addEventListener("change", syncSize);
$("overlap")?.addEventListener("change", syncSize);
$("devfilter").addEventListener("input", fillDevices);
$("add-wall").addEventListener("click", () => {
  layout.walls.push({
    side: $("wall-side").value,
    id: $("wall-dev").value,
    pos: Number($("wall-pos").value) || 0,
  });
  renderWalls();
});
$("preset-sq").addEventListener("click", () => {
  currentCaseId = "";
  saveFolderId = $("folder")?.value || "";
  if ($("casetitle")) $("casetitle").value = "3 sliders + 2 quad rotaries";
  $("cols").value = 5;
  $("rows").value = 4;
  $("inner").value = 25;
  setEdgeInputs("round", 2);
  setHang(true);
  setOverlap(true);
  clearNotes();
  layout = {
    cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, hang: true, overlap: true, tilts: [0, 0, 0, 0], walls: [],
    devices: [
      { id: "neoslider", c: 0, r: 0 },
      { id: "neoslider", c: 1, r: 0 },
      { id: "neoslider", c: 2, r: 0 },
      { id: "quad_rotary", c: 3, r: 0 },
      { id: "quad_rotary", c: 4, r: 0 },
    ],
  };
  syncSize();
});
$("preset-tilt").addEventListener("click", () => {
  currentCaseId = "";
  saveFolderId = $("folder")?.value || "";
  if ($("casetitle")) $("casetitle").value = "tilt demo";
  $("cols").value = 4;
  $("rows").value = 6;
  $("inner").value = 25;
  setEdgeInputs("round", 2);
  setHang(true);
  setOverlap(true);
  clearNotes();
  layout = {
    cols: 4, rows: 6, inner_h: 25, edge_style: "round", edge_mm: 2, hang: true, overlap: true,
    tilts: [0, 0, 0, 30, 30, -30],
    devices: [],
    walls: [],
  };
  syncSize();
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
    $("status").textContent = `zip ${blob.size} bytes. BOM and OpenSCAD are inside. Print the lid face-down.`;
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
  lines.push({ qty: 1, item: "Bottom tray (printed)", url: "" });
  lines.push({
    qty: 1,
    item: layout.overlap !== false
      ? "Lid (printed, face on bed, skirt overlaps tray)"
      : "Lid (printed, face on bed, flush — no overlap)",
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
  if (layout.hang !== false) {
    lines.push({ qty: hangXs(layout.cols).length, item: "Wall screw for back keyhole (#8 / M4)", url: "" });
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
  $("cols").value = layout.cols;
  $("rows").value = layout.rows;
  $("inner").value = layout.inner_h;
  setEdgeInputs(layout.edge_style, layout.edge_mm);
  setHang(layout.hang !== false);
  setOverlap(layout.overlap !== false);
  syncSize();
  renderWalls();
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
  setHang(true);
  setOverlap(true);
  layout = { cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, hang: true, overlap: true, tilts: [0, 0, 0, 0], devices: [], walls: [] };
  syncSize();
  renderWalls();
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

const TAB_NAMES = ["view", "case", "parts", "library"];
function setTab(name) {
  if (!TAB_NAMES.includes(name)) name = "view";
  for (const t of TAB_NAMES) document.body.classList.toggle("tab-" + t, t === name);
  document.querySelectorAll("#tabs [data-tab]").forEach((b) => {
    const on = b.getAttribute("data-tab") === name;
    b.classList.toggle("on", on);
    if (on) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  window.scrollTo(0, 0);
  if (name === "view") {
    requestAnimationFrame(() => {
      if (window.rebuildPreview) window.rebuildPreview();
    });
  }
  try {
    if (location.hash.replace("#", "") !== name) history.replaceState(null, "", "#" + name);
  } catch { /* ignore */ }
}
document.querySelectorAll("#tabs [data-tab]").forEach((b) => {
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
