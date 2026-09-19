"""Build devices.json from Eagle PCBs + scraped Adafruit product pages."""
from __future__ import annotations

import html as htmlmod
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PITCH = 25.4  # 1.00 inch grid
STRIP_LEN_U = 4  # standard printable length in grid units
MAX_U = 5

FEATURED = {
    "5295": {
        "name": "Adafruit NeoSlider I2C QT Slide Potentiometer",
        "kind": "slider",
        "source": "eagle Adafruit-NeoSlider-PCB",
        "pcb_mm": [76.2, 21.59, 1.6],
        "shop_body_mm": [76.2, 29.8, 21.5],
        "mount_holes": {
            "dia_mm": 2.5,
            "centers_mm": [[19.05, 8.255], [-19.05, 8.255], [19.05, -8.255], [-19.05, -8.255]],
            "origin": "board center",
        },
        "cutouts": [
            {
                "type": "slot",
                "purpose": "75 mm slide pot travel (faceplate)",
                "length_mm": 75.0,
                "width_mm": 4.0,
                "center_mm": [0, 0],
            }
        ],
        "notes": "PCB is 3.00 x 0.85 in. Shop height 21.5 mm includes the slider knob. STEMMA QT is on the bottom; use 10-12 mm M3 standoffs.",
    },
    "5752": {
        "name": "Adafruit I2C Quad Rotary Encoder Breakout",
        "kind": "quad-encoder",
        "source": "eagle Adafruit-I2C-Quad-Rotary-Encoder-Breakout-PCB",
        "pcb_mm": [76.2, 21.59, 1.6],
        "mount_holes": {
            "dia_mm": 2.5,
            "centers_mm": [[19.05, 8.255], [-19.05, 8.255], [19.05, -8.255], [-19.05, -8.255]],
            "origin": "board center",
        },
        "cutouts": [
            {
                "type": "circle",
                "purpose": "PEC11 bushing (faceplate)",
                "dia_mm": 7.5,
                "centers_mm": [[-28.575, 0], [-9.525, 0], [9.525, 0], [28.575, 0]],
            }
        ],
        "notes": "Same PCB outline as NeoSlider. Four PEC11 footprints on 19.05 mm (0.75 in) pitch. Encoders not included.",
    },
    "4991": {
        "name": "Adafruit I2C Stemma QT Rotary Encoder Breakout (no encoder)",
        "kind": "encoder",
        "source": "eagle Adafruit-I2C-QT-Rotary-Encoder-PCB",
        "pcb_mm": [25.4, 25.4, 1.6],
        "shop_body_mm": [25.6, 25.3, 4.6],
        "mount_holes": {
            "dia_mm": 2.5,
            "centers_mm": [[2.54, 2.54], [22.86, 2.54], [2.54, 22.86], [22.86, 22.86]],
            "origin": "board lower-left",
        },
        "cutouts": [
            {
                "type": "circle",
                "purpose": "PEC11 bushing (faceplate)",
                "dia_mm": 7.5,
                "centers_mm": [[12.7, 12.7]],
            }
        ],
        "notes": "Exactly 1.00 in square. Encoder at 45 degrees, shaft at board center. Same PCB as 5880.",
    },
    "5880": {
        "name": "Adafruit I2C Stemma QT Rotary Encoder Breakout (encoder soldered)",
        "kind": "encoder",
        "source": "same PCB as 4991",
        "pcb_mm": [25.4, 25.4, 1.6],
        "mount_holes": {
            "dia_mm": 2.5,
            "centers_mm": [[2.54, 2.54], [22.86, 2.54], [2.54, 22.86], [22.86, 22.86]],
            "origin": "board lower-left",
        },
        "cutouts": [
            {
                "type": "circle",
                "purpose": "PEC11 bushing (faceplate)",
                "dia_mm": 7.5,
                "centers_mm": [[12.7, 12.7]],
            }
        ],
        "notes": "Identical PCB to 4991 with PEC11 soldered. Shaft at center. Same 1.00 in footprint.",
    },
    "6310": {
        "name": "Adafruit ANO Rotary Navigation Encoder to I2C Adapter (encoder soldered)",
        "kind": "ano-encoder",
        "source": "eagle Adafruit-ANO-Rotary-Navigation-Encoder-to-I2C",
        "pcb_mm": [35.56, 40.64, 1.6],
        "mount_holes": {
            "dia_mm": 2.5,
            "centers_mm": [[15.24, 17.78], [-15.24, 17.78], [15.24, -17.78], [-15.24, -17.78]],
            "origin": "board center",
        },
        "encoder_posts_mm": {
            "dia_mm": 4.0,
            "centers_mm": [[0, 15.0], [0, -15.0], [15.0, 0], [-15.0, 0]],
            "purpose": "ANO encoder locating / posts, not panel screws",
        },
        "cutouts": [
            {
                "type": "circle",
                "purpose": "ANO click-wheel through a faceplate",
                "dia_mm": 22.0,
                "centers_mm": [[0, 0]],
            }
        ],
        "notes": "PCB 1.40 x 1.60 in. Needs a 2-wide strip. Same PCB as 5740 without the encoder.",
    },
}


def units_for(mm: float) -> int:
    if mm <= 0:
        return 1
    return max(1, int(math.ceil(mm / PITCH - 1e-9)))


def assign_grid(w_mm: float, h_mm: float) -> dict:
    uw, uh = units_for(w_mm), units_for(h_mm)
    # Prefer the shorter side as width so sliders run along the 4 in length.
    if uw > uh:
        uw, uh = uh, uw
        w_mm, h_mm = h_mm, w_mm
        rotated = True
    else:
        rotated = False
    overflow = uw > MAX_U or uh > MAX_U * STRIP_LEN_U
    strips_wide = min(uw, MAX_U)
    lengths = max(1, int(math.ceil(uh / STRIP_LEN_U)))
    return {
        "pcb_w_mm": round(w_mm, 2),
        "pcb_h_mm": round(h_mm, 2),
        "units_wide": uw,
        "units_long": uh,
        "strips_wide": strips_wide,
        "strip_length_units": STRIP_LEN_U,
        "strip_count_along": lengths,
        "rotated_to_fit": rotated,
        "fits_five_by_five": uw <= MAX_U and uh <= MAX_U * STRIP_LEN_U,
        "overflow": overflow,
        "panel_mm": [round(strips_wide * PITCH, 2), round(lengths * STRIP_LEN_U * PITCH, 2)],
    }


def _nums(s: str) -> list[float]:
    return [float(x) for x in re.findall(r"([0-9]+(?:\.[0-9]+)?)", s)]


def parse_html(raw: str) -> dict:
    text = htmlmod.unescape(raw)
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")
    out: dict = {}

    def grab(rx, key, n=2):
        m = re.search(rx, text, re.I)
        if m:
            out[key] = [float(m.group(i)) for i in range(1, n + 1)]

    grab(
        r"Product Dimensions:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
        "body_mm",
        3,
    )
    grab(
        r"Overall dimension:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
        "body_mm",
        3,
    )
    grab(r"(?:PCB|Board):\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm", "pcb_mm", 2)
    grab(
        r"PCB Dimension[^:<]{0,40}:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm(?:\s*x\s*([0-9.]+)\s*mm)?",
        "pcb_mm",
        2,
    )
    grab(
        r"Mounting Holes?(?: Distance| Dimensions)?:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
        "mount_span_mm",
        2,
    )
    grab(
        r"Mounting hole dimensions:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
        "mount_span_mm",
        2,
    )
    grab(
        r"Mounting hole distance:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm",
        "mount_span_mm",
        2,
    )
    grab(r"(?:Screen|Display area|LCD screen dimensions|TFT screen dimensions):\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm", "view_mm", 2)
    m = re.search(r"Mounting Hole Diameter:\s*([0-9.]+)\s*mm", text, re.I)
    if m:
        out["mount_dia_mm"] = float(m.group(1))
    m = re.search(r"Mounting holes?:\s*([0-9.]+)&quot;\s*x\s*([0-9.]+)&quot;", text, re.I)
    if m and "mount_span_mm" not in out:
        out["mount_span_mm"] = [round(float(m.group(1)) * 25.4, 2), round(float(m.group(2)) * 25.4, 2)]
    m = re.search(r"Mounting holes?:\s*([0-9.]+)\"\s*x\s*([0-9.]+)\"", text, re.I)
    if m and "mount_span_mm" not in out:
        out["mount_span_mm"] = [round(float(m.group(1)) * 25.4, 2), round(float(m.group(2)) * 25.4, 2)]
    m = re.search(r"Dimensions of Screen:\s*([0-9.]+)\s*mm\s*x\s*([0-9.]+)\s*mm(?:\s*x\s*([0-9.]+)\s*mm)?", text, re.I)
    if m and "body_mm" not in out:
        vals = [float(m.group(1)), float(m.group(2))]
        if m.group(3):
            vals.append(float(m.group(3)))
        out["body_mm"] = vals
    title = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S | re.I)
    if title:
        out["title"] = re.sub(r"<[^>]+>", "", title.group(1)).strip()
    return out


DISPLAY_NAME = re.compile(
    r"\b(oled|tft|lcd|eink|e-ink|e-paper|epaper|display)\b", re.I
)
SKIP_NAME = re.compile(
    r"(hdmi cable|plug adapter|socket adapter|extension cable|light valve|backpack driver|RA8875|TFP401|DVI Sock|ThinkInk for 24-pin|Breakout Friend|Feather Friend|wire stand|acrylic stand|mijia|picowbell|charlieplex|matrix portal|power meter|memory display breakout)",
    re.I,
)


def classify(name: str) -> str:
    n = name.lower()
    if "eink" in n or "e-ink" in n or "epaper" in n or "e-paper" in n:
        return "eink"
    if "oled" in n:
        return "oled"
    if "tft" in n:
        return "tft"
    if re.search(r"16x2|20x4|character lcd", n):
        return "character-lcd"
    if "lcd" in n or "display" in n:
        return "display"
    return "other"


def main() -> None:
    catalog = json.loads((ROOT / "data" / "adafruit-products.json").read_text(encoding="utf-8"))
    by_id = {str(p["product_id"]): p for p in catalog}
    pages = ROOT / "data" / "pages"
    devices = []

    for pid, feat in FEATURED.items():
        shop = by_id.get(pid, {})
        w, h = feat["pcb_mm"][0], feat["pcb_mm"][1]
        item = {
            "product_id": pid,
            "url": f"https://www.adafruit.com/product/{pid}",
            "featured": True,
            **feat,
            "price": shop.get("product_price"),
            "stock": shop.get("product_stock"),
            "grid": assign_grid(w, h),
        }
        devices.append(item)

    seen = set(FEATURED)
    for html_path in sorted(pages.glob("*.html")):
        pid = html_path.stem
        if pid in seen:
            continue
        shop = by_id.get(pid, {})
        name = shop.get("product_name") or ""
        if shop.get("discontinue_status") == "Discontinued":
            continue
        if SKIP_NAME.search(name):
            continue
        if not DISPLAY_NAME.search(name):
            continue
        kind_guess = classify(name)
        if kind_guess not in {"tft", "oled", "eink", "character-lcd"} and not re.search(
            r"hdmi.*backpack|backpack.*hdmi", name, re.I
        ):
            continue
        parsed = parse_html(html_path.read_text(encoding="utf-8", errors="replace"))
        body = parsed.get("body_mm") or parsed.get("pcb_mm")
        if not body or len(body) < 2:
            continue
        w, h = body[0], body[1]
        kind = classify(name)
        mount = None
        if parsed.get("mount_span_mm"):
            sx, sy = parsed["mount_span_mm"]
            mount = {
                "dia_mm": parsed.get("mount_dia_mm", 2.5),
                "span_mm": [sx, sy],
                "centers_mm": [
                    [round(-sx / 2, 2), round(-sy / 2, 2)],
                    [round(sx / 2, 2), round(-sy / 2, 2)],
                    [round(-sx / 2, 2), round(sy / 2, 2)],
                    [round(sx / 2, 2), round(sy / 2, 2)],
                ],
                "origin": "board center (span from shop page)",
            }
        cutouts = []
        view = parsed.get("view_mm")
        if view:
            cutouts.append(
                {
                    "type": "rect",
                    "purpose": "display window (faceplate)",
                    "w_mm": view[0],
                    "h_mm": view[1],
                    "center_mm": [0, 0],
                }
            )
        elif kind in {"tft", "oled", "eink", "display", "character-lcd"}:
            cutouts.append(
                {
                    "type": "rect",
                    "purpose": "display window, inferred 2 mm inset from PCB (not measured)",
                    "w_mm": round(max(8, w - 4), 1),
                    "h_mm": round(max(8, h - 4), 1),
                    "center_mm": [0, 0],
                    "inferred": True,
                }
            )
        devices.append(
            {
                "product_id": pid,
                "url": f"https://www.adafruit.com/product/{pid}",
                "featured": False,
                "name": parsed.get("title") or name,
                "kind": kind,
                "source": "adafruit shop technical details",
                "pcb_mm": [w, h] + ([body[2]] if len(body) > 2 else []),
                "shop_body_mm": parsed.get("body_mm"),
                "view_mm": view,
                "mount_holes": mount,
                "cutouts": cutouts,
                "price": shop.get("product_price"),
                "stock": shop.get("product_stock"),
                "grid": assign_grid(w, h),
            }
        )

    devices.sort(key=lambda d: (not d["featured"], d["kind"], d["grid"]["units_wide"], d["name"]))
    system = {
        "pitch_mm": PITCH,
        "pitch_in": 1.0,
        "strip_length_units": STRIP_LEN_U,
        "strip_length_mm": STRIP_LEN_U * PITCH,
        "max_strips_wide": MAX_U,
        "max_lengths": MAX_U,
        "assembled_max_mm": [MAX_U * PITCH, MAX_U * STRIP_LEN_U * PITCH],
        "hole_dia_mm": 3.3,
        "hole_for": "M3 clearance, screw from below into a female-female standoff",
        "countersink_mm": [6.5, 1.8],
        "panel_thick_mm": 4.0,
        "standoff": "M3 female-female 11-12 mm (STEMMA QT sits on the bottom of the QT boards)",
        "join": "butt edges; 1 in grid stays continuous; M3 join-bar under the seam, screws from below",
        "print": "PLA or PETG, 0.20 mm layer, 3 walls, 30 percent gyroid, no supports, bottom (countersink) on the bed",
    }
    payload = {"system": system, "devices": devices}
    out = ROOT / "data" / "devices.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    n_feat = sum(1 for d in devices if d["featured"])
    n_disp = len(devices) - n_feat
    overflow = [d["product_id"] for d in devices if d["grid"]["overflow"]]
    print(f"wrote {out} featured={n_feat} displays={n_disp} overflow={overflow}")


if __name__ == "__main__":
    main()
