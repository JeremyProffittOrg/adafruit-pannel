"""Emit cad/devices.scad from library/devices.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    lib = json.loads((ROOT / "library" / "devices.json").read_text(encoding="utf-8"))
    lines = [
        "// Generated from library/devices.json. Do not edit by hand.",
        "$fn = 24;",
        "",
        "function dev_cells_x(id) =",
    ]
    devs = lib["devices"]
    for i, d in enumerate(devs):
        sep = ";" if i == len(devs) - 1 else ""
        prefix = "  " if i == 0 else "  "
        op = "=" if i == 0 else ""
        # chain
    chain_x = []
    chain_y = []
    chain_boss = []
    chain_bot = []
    for d in devs:
        chain_x.append(f'id == "{d["id"]}" ? {d.get("cells_x", 1)}')
        chain_y.append(f'id == "{d["id"]}" ? {d.get("cells_y", 1)}')
        chain_boss.append(f'id == "{d["id"]}" ? {d.get("boss_mm", 6)}')
        bot = "true" if d.get("place") == "bottom" else "false"
        chain_bot.append(f'id == "{d["id"]}" ? {bot}')
    def chain(items, default):
        s = items[0]
        for it in items[1:]:
            s += " :\n  " + it
        s += f" :\n  {default};"
        return s

    lines.append("  " + chain(chain_x, "1"))
    lines.append("function dev_cells_y(id) =")
    lines.append("  " + chain(chain_y, "1"))
    lines.append("function dev_boss(id) =")
    lines.append("  " + chain(chain_boss, "6"))
    lines.append("function dev_is_bottom(id) =")
    lines.append("  " + chain(chain_bot, "false"))
    lines.append("")
    lines.append("module dev_cutouts(id) {")
    for d in devs:
        cuts = d.get("cutouts") or []
        if not cuts:
            continue
        lines.append(f'  if (id == "{d["id"]}") {{')
        for c in cuts:
            t = c.get("type")
            x = c.get("x", 0)
            y = c.get("y", 0)
            if t == "hole":
                lines.append(f"    translate([{x}, {y}, -1]) cylinder(d={c['d']}, h=20);")
            elif t == "slot":
                w, l = c["w"], c["l"]
                lines.append(
                    f"    translate([{x}, {y}, 9]) cube([{w}, {l}, 20], center=true);"
                )
            elif t == "window":
                w, h = c["w"], c["h"]
                lines.append(
                    f"    translate([{x}, {y}, 9]) cube([{w}, {h}, 20], center=true);"
                )
            elif t == "grill":
                w, h = c.get("w", 12), c.get("h", 8)
                lines.append("    for (gy = [-3, 0, 3])")
                lines.append(
                    f"      translate([{x}, {y}+gy, 9]) cube([{w}, 1.4, 20], center=true);"
                )
        lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("module dev_bosses(id) {")
    for d in devs:
        holes = d.get("holes") or []
        if not holes:
            continue
        hd = d.get("hole_d", 2.5)
        boss = d.get("boss_mm", 6)
        od = 6.8 if hd <= 2.6 else 8.0
        idd = hd - 0.2
        lines.append(f'  if (id == "{d["id"]}") {{')
        for hx, hy in holes:
            lines.append(f"    translate([{hx}, {hy}, 0]) difference() {{")
            lines.append(f"      cylinder(d={od}, h={boss});")
            lines.append(f"      translate([0,0,-0.2]) cylinder(d={idd:.2f}, h={boss}+0.4);")
            lines.append("    }")
        lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("module wall_cutout_of(id) {")
    for d in devs:
        wc = d.get("wall_cutout")
        if not wc:
            continue
        lines.append(f'  if (id == "{d["id"]}") {{')
        t = wc.get("type")
        if t == "hole":
            lines.append(f"    rotate([0,90,0]) cylinder(d={wc['d']}, h=20, center=true);")
        elif t == "grill":
            w = wc.get("w", 12)
            lines.append("    for (gy = [-3, 0, 3])")
            lines.append(f"      translate([0, gy, 0]) cube([20, {w}, 1.4], center=true);")
        lines.append("  }")
    lines.append("}")
    lines.append("")
    out = ROOT / "cad" / "devices.scad"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", out, "devices", len(devs))


if __name__ == "__main__":
    main()
