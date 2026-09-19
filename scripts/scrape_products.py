"""Scrape Adafruit product pages for mechanical dimensions."""
from __future__ import annotations

import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "AdafruitControlPanelBuilder/1.0 (mechanical catalog; local 3D-print project)"

DIM_RE = re.compile(
    r"Product Dimensions:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm"
    r"(?:\s*/\s*([0-9.]+)\"\s*x\s*([0-9.]+)\"\s*x\s*([0-9.]+)\")?",
    re.I,
)
WEIGHT_RE = re.compile(r"Product Weight:\s*([0-9.]+)\s*g", re.I)
MOUNT_RE = re.compile(
    r"Mounting Holes?(?: Distance| Dimensions)?:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
    re.I,
)
MOUNT_DIA_RE = re.compile(
    r"Mounting Hole Diameter:\s*([0-9.]+)\s*mm",
    re.I,
)
BOARD_RE = re.compile(
    r"(?:PCB|Board):\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
    re.I,
)
SCREEN_RE = re.compile(
    r"(?:Screen|Display area|Viewing Area):\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
    re.I,
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_page(html: str) -> dict:
    out: dict = {}
    m = DIM_RE.search(html)
    if m:
        out["body_mm"] = [float(m.group(1)), float(m.group(2)), float(m.group(3))]
        if m.group(4):
            out["body_in"] = [float(m.group(4)), float(m.group(5)), float(m.group(6))]
    m = WEIGHT_RE.search(html)
    if m:
        out["weight_g"] = float(m.group(1))
    m = MOUNT_RE.search(html)
    if m:
        out["mounting_span_mm"] = [float(m.group(1)), float(m.group(2))]
    m = MOUNT_DIA_RE.search(html)
    if m:
        out["mounting_hole_dia_mm"] = float(m.group(1))
    m = BOARD_RE.search(html)
    if m:
        out["pcb_mm"] = [float(m.group(1)), float(m.group(2))]
    m = SCREEN_RE.search(html)
    if m:
        out["view_mm"] = [float(m.group(1)), float(m.group(2))]
    title = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    if title:
        out["title"] = re.sub(r"<[^>]+>", "", title.group(1)).strip()
    return out


def wanted_ids() -> list[str]:
    featured = ["5295", "5752", "6310", "5880", "4991"]
    catalog = json.loads((ROOT / "data" / "adafruit-products.json").read_text(encoding="utf-8"))
    display_cats = {"97", "98", "96", "150", "99", "110", "506"}
    name_re = re.compile(
        r"\b(oled|tft|lcd|eink|e-ink|e-paper|epaper|display|neoslider|rotary encoder)\b",
        re.I,
    )
    skip_re = re.compile(
        r"(hdmi cable|adapter|backpack driver|extension cable|stand for|light valve|backlight display -)",
        re.I,
    )
    ids = list(featured)
    for p in catalog:
        if p.get("discontinue_status") == "Discontinued":
            continue
        pid = str(p["product_id"])
        name = p.get("product_name") or ""
        cat = str(p.get("product_master_category") or "")
        if pid in ids:
            continue
        if skip_re.search(name):
            continue
        if cat in display_cats or name_re.search(name):
            # keep panel-mountable-ish: skip huge 13" pimoroni as still listed
            ids.append(pid)
    return ids


def main() -> None:
    cache_dir = ROOT / "data" / "pages"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ids = wanted_ids()
    print("ids", len(ids))
    results = {}

    def one(pid: str):
        cache = cache_dir / f"{pid}.html"
        if cache.exists() and cache.stat().st_size > 2000:
            html = cache.read_text(encoding="utf-8", errors="replace")
        else:
            html = fetch(f"https://www.adafruit.com/product/{pid}")
            cache.write_text(html, encoding="utf-8")
            time.sleep(0.05)
        parsed = parse_page(html)
        parsed["product_id"] = pid
        parsed["url"] = f"https://www.adafruit.com/product/{pid}"
        return pid, parsed

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(one, pid) for pid in ids]
        for i, fut in enumerate(as_completed(futs), 1):
            pid, parsed = fut.result()
            results[pid] = parsed
            if i % 25 == 0:
                print(i, "of", len(ids), "last", pid, parsed.get("body_mm"))

    out = ROOT / "data" / "scraped-products.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    with_dim = sum(1 for v in results.values() if "body_mm" in v)
    print("wrote", out, "n", len(results), "with body_mm", with_dim)


if __name__ == "__main__":
    main()
