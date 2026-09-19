let LIB = { devices: [] };
let byId = {};
let layout = {
  cols: 5,
  rows: 4,
  inner_h: 25,
  edge_style: "round",
  edge_mm: 2,
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
    const lab = document.createElement("label");
    lab.textContent = `row ${i} `;
    const inp = document.createElement("input");
    inp.type = "number";
    inp.value = layout.tilts[i];
    inp.step = 5;
    inp.addEventListener("input", () => {
      layout.tilts[i] = Number(inp.value) || 0;
      bumpPreview();
    });
    lab.appendChild(inp);
    box.appendChild(lab);
  }
}

function renderGrid() {
  const g = $("grid");
  g.style.gridTemplateColumns = `repeat(${layout.cols}, 1fr)`;
  g.innerHTML = "";
  const occ = occMap();
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c < layout.cols; c++) {
      const el = document.createElement("div");
      el.className = "cell";
      const hit = occ[`${c},${r}`];
      if (hit) {
        el.classList.add(byId[hit.id]?.place === "bottom" ? "bottom" : "on");
        if (hit.c === c && hit.r === r) el.textContent = byId[hit.id]?.name || hit.id;
      } else {
        el.textContent = `${c},${r}`;
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
}

function fillDevices() {
  const sel = $("device");
  const wsel = $("wall-dev");
  const q = ($("devfilter")?.value || "").toLowerCase();
  sel.innerHTML = "";
  wsel.innerHTML = "";
  for (const d of LIB.devices) {
    byId[d.id] = d;
    const label = `${d.category}: ${d.name}`;
    if (q && !label.toLowerCase().includes(q)) continue;
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = label;
    sel.appendChild(opt);
    if (d.place === "wall") {
      const w = document.createElement("option");
      w.value = d.id;
      w.textContent = d.name;
      wsel.appendChild(w);
    }
  }
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
}

function syncSize() {
  layout.cols = Number($("cols").value) || 1;
  layout.rows = Number($("rows").value) || 1;
  layout.inner_h = Number($("inner").value) || 25;
  layout.edge_style = $("edge")?.value || "round";
  layout.edge_mm = Number($("edgemm")?.value) || 2;
  renderTilts();
  renderGrid();
  bumpPreview();
}

$("cols").addEventListener("input", syncSize);
$("rows").addEventListener("input", syncSize);
$("inner").addEventListener("input", syncSize);
$("edge").addEventListener("change", syncSize);
$("edgemm").addEventListener("input", syncSize);
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
  $("cols").value = 5;
  $("rows").value = 4;
  $("inner").value = 25;
  layout = {
    cols: 5, rows: 4, inner_h: 25, edge_style: "round", edge_mm: 2, tilts: [0, 0, 0, 0], walls: [],
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
  $("cols").value = 4;
  $("rows").value = 6;
  $("inner").value = 25;
  layout = {
    cols: 4, rows: 6, inner_h: 25, edge_style: "round", edge_mm: 2,
    tilts: [0, 0, 0, 30, 30, -30],
    devices: [],
    walls: [],
  };
  syncSize();
});
$("go").addEventListener("click", async () => {
  $("status").textContent = "Building zip (BOM + SCAD, STL if OpenSCAD is on this host).";
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(layout),
  });
  if (!res.ok) {
    $("status").textContent = await res.text();
    return;
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "panel-case.zip";
  a.click();
  $("status").textContent = `zip ${blob.size} bytes. Includes BOM.csv / BOM.md and manufacturer links.`;
});

let signedIn = false;
let currentCaseId = "";

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
  $("casetitle").value = rec.title || "";
  if ($("folder") && rec.folder_id) $("folder").value = rec.folder_id;
  layout = rec.layout;
  $("cols").value = layout.cols;
  $("rows").value = layout.rows;
  $("inner").value = layout.inner_h;
  if ($("edge")) $("edge").value = layout.edge_style || "round";
  if ($("edgemm")) $("edgemm").value = layout.edge_mm || 2;
  syncSize();
  renderWalls();
  loadNotes();
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
      await api(`/api/cases/${rec.id}`, { method: "DELETE" });
      if (currentCaseId === rec.id) currentCaseId = "";
      await refreshCases();
    };
    li.appendChild(rm);
    ul.appendChild(li);
  }
}

async function loadNotes() {
  const ul = $("notelist");
  ul.innerHTML = "";
  if (!currentCaseId) return;
  const list = await api(`/api/cases/${currentCaseId}/notes`);
  for (const n of list) {
    const li = document.createElement("li");
    li.textContent = n.text;
    const rm = document.createElement("button");
    rm.textContent = "delete";
    rm.onclick = async () => {
      await api(`/api/cases/${currentCaseId}/notes/${n.id}`, { method: "DELETE" });
      await loadNotes();
    };
    li.appendChild(rm);
    ul.appendChild(li);
  }
}

async function loadPartCases(part) {
  const ul = $("partcases");
  if (!ul) return;
  ul.innerHTML = "";
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
  } catch {
    /* not signed in */
  }
}

async function bootLibrary() {
  const me = await api("/api/me");
  signedIn = !!me.login;
  $("wholabel").textContent = signedIn ? (me.name || me.email || "signed in") : "not signed in";
  $("loginbtn").hidden = signedIn;
  $("logoutbtn").hidden = !signedIn;
  $("libhint").hidden = signedIn;
  $("libbody").hidden = !signedIn;
  if (!signedIn) return;
  await refreshFolders();
  await refreshCases();
}

$("dosearch")?.addEventListener("click", async () => {
  const q = $("q").value.trim();
  const ul = $("hits");
  ul.innerHTML = "";
  if (!q) return;
  const hits = await api(`/api/search?q=${encodeURIComponent(q)}`);
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
  const f = await api("/api/folders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  $("foldername").value = "";
  await refreshFolders();
  $("folder").value = f.id;
  await refreshCases();
});
$("delfolder")?.addEventListener("click", async () => {
  const id = $("folder").value;
  if (!id) return;
  await api(`/api/folders/${id}`, { method: "DELETE" });
  await refreshFolders();
  await refreshCases();
});
$("folder")?.addEventListener("change", () => refreshCases());
$("savecase")?.addEventListener("click", async () => {
  const rec = {
    id: currentCaseId || undefined,
    title: $("casetitle").value.trim() || "Untitled case",
    folder_id: $("folder").value,
    layout,
  };
  const out = await api(currentCaseId ? `/api/cases/${currentCaseId}` : "/api/cases", {
    method: currentCaseId ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rec),
  });
  currentCaseId = out.id;
  $("status").textContent = `saved ${out.title}`;
  await refreshCases();
});
$("addnote")?.addEventListener("click", async () => {
  if (!currentCaseId) {
    $("status").textContent = "save the case before adding a note";
    return;
  }
  const text = $("notetext").value.trim();
  if (!text) return;
  await api(`/api/cases/${currentCaseId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  $("notetext").value = "";
  await loadNotes();
});

fetch("/api/devices")
  .then((r) => r.json())
  .then((j) => {
    LIB = j;
    fillDevices();
    window.PANEL_BY_ID = byId;
    syncSize();
    $("preset-sq").click();
    bootLibrary().catch((e) => {
      $("status").textContent = String(e);
    });
  });
