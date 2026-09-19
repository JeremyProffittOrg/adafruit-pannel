"""Parse Adafruit Eagle .brd files for outline and NPTH holes."""
from __future__ import annotations

import re
from pathlib import Path


def _attrs(tag: str) -> dict[str, str]:
    return dict(re.findall(r'([A-Za-z0-9_]+)="([^"]*)"', tag))


def parse_brd(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    holes = []
    for raw in re.findall(r"<hole\s+([^/]*?)/>", text):
        a = _attrs(raw)
        if "x" in a and "y" in a and "drill" in a:
            holes.append(
                {
                    "x_mm": round(float(a["x"]), 3),
                    "y_mm": round(float(a["y"]), 3),
                    "drill_mm": round(float(a["drill"]), 3),
                }
            )

    xs: list[float] = []
    ys: list[float] = []
    for raw in re.findall(r"<wire\s+([^>]*layer=\"20\"[^/]*?)/>", text):
        a = _attrs(raw)
        for k in ("x1", "x2"):
            if k in a:
                xs.append(float(a[k]))
        for k in ("y1", "y2"):
            if k in a:
                ys.append(float(a[k]))

    outline = None
    if xs and ys:
        outline = {
            "min_x": round(min(xs), 3),
            "min_y": round(min(ys), 3),
            "max_x": round(max(xs), 3),
            "max_y": round(max(ys), 3),
            "width_mm": round(max(xs) - min(xs), 3),
            "height_mm": round(max(ys) - min(ys), 3),
        }

    return {"file": path.name, "outline": outline, "npth_holes": holes}


if __name__ == "__main__":
    import json

    root = Path(__file__).resolve().parents[1] / "data" / "pcb"
    out = {}
    for p in sorted(root.glob("*.brd")):
        out[p.stem] = parse_brd(p)
        print(p.name, json.dumps(out[p.stem]["outline"]), "holes", len(out[p.stem]["npth_holes"]))
        for h in out[p.stem]["npth_holes"]:
            print(" ", h)
    (root / "parsed.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
