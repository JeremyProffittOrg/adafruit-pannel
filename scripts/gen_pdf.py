"""Build the control-panel PDF from devices.json."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Flowable,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "adafruit-control-panel.pdf"
PITCH = 25.4

NAVY = colors.HexColor("#0f172a")
BLUE = colors.HexColor("#1d4ed8")
PALE = colors.HexColor("#dbeafe")
GREY = colors.HexColor("#e5e7eb")
INK = colors.HexColor("#0b0f19")
MUTED = colors.HexColor("#4b5563")
WHITE = colors.HexColor("#ffffff")
AMBER = colors.HexColor("#fef3c7")


class GridDraw(Flowable):
    """Top-view of an NxM strip with 1 in holes, mm scale."""

    def __init__(self, nx, ny, width=6.8 * inch, label=""):
        super().__init__()
        self.nx = nx
        self.ny = ny
        self.label = label
        self.width = width
        panel_w = nx * PITCH
        panel_h = ny * PITCH
        self.scale = (width - 36) / max(panel_w, panel_h * 0.55)
        self.height = panel_h * self.scale + 28

    def draw(self):
        c = self.canv
        s = self.scale
        w = self.nx * PITCH * s
        h = self.ny * PITCH * s
        x0 = 18
        y0 = 14
        c.setFillColor(colors.HexColor("#f8fafc"))
        c.setStrokeColor(NAVY)
        c.setLineWidth(0.8)
        c.roundRect(x0, y0, w, h, 3, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor("#93c5fd"))
        c.setLineWidth(0.3)
        for i in range(self.nx + 1):
            x = x0 + i * PITCH * s
            c.line(x, y0, x, y0 + h)
        for j in range(self.ny + 1):
            y = y0 + j * PITCH * s
            c.line(x0, y, x0 + w, y)
        c.setFillColor(colors.HexColor("#1e3a8a"))
        c.setStrokeColor(NAVY)
        r = 1.65 * s
        for i in range(self.nx):
            for j in range(self.ny):
                cx = x0 + (i + 0.5) * PITCH * s
                cy = y0 + (j + 0.5) * PITCH * s
                c.setFillColor(WHITE)
                c.circle(cx, cy, r * 1.6, fill=1, stroke=1)
                c.setFillColor(NAVY)
                c.circle(cx, cy, r, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Helvetica", 8)
        c.drawString(x0, 2, f"{self.label}  {self.nx}x{self.ny} units  {self.nx*PITCH:.1f} x {self.ny*PITCH:.1f} mm")


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Cover", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK, spaceAfter=8))
    ss.add(ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=12, spaceAfter=6))
    ss.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK, spaceAfter=6))
    ss.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8, leading=11, textColor=INK))
    ss.add(ParagraphStyle("Muted", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED))
    ss.add(ParagraphStyle("Cell", fontName="Helvetica", fontSize=7.5, leading=10, textColor=INK))
    ss.add(ParagraphStyle("CellB", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=INK))
    ss.add(ParagraphStyle("HCell", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=WHITE))
    ss.add(ParagraphStyle("Mono", fontName="Courier", fontSize=8, leading=11, textColor=INK))
    return ss


def P(text, style):
    return Paragraph(str(text), style)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, doc.pagesize[1] - 22, doc.pagesize[0], 22, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(24, doc.pagesize[1] - 15, "Adafruit modular control panel  —  1.00 in grid, 3D printable")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, doc.pagesize[0], 18, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(24, 6, "C:\\dev\\adafruit-pannel")
    canvas.drawRightString(doc.pagesize[0] - 24, 6, f"page {doc.page}")
    canvas.restoreState()


def table(rows, col_widths, ss):
    styled = []
    for ri, row in enumerate(rows):
        out = []
        for cell in row:
            st = ss["HCell"] if ri == 0 else ss["Cell"]
            out.append(cell if isinstance(cell, Paragraph) else P(cell, st))
        styled.append(out)
    t = Table(styled, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f1f5f9")]),
    ]))
    return t


def hole_text(d):
    mh = d.get("mount_holes") or {}
    if not mh:
        return "not published on shop page"
    dia = mh.get("dia_mm", 2.5)
    if mh.get("centers_mm"):
        pts = "; ".join(f"({x:.2f}, {y:.2f})" for x, y in mh["centers_mm"])
        origin = mh.get("origin", "")
        return f"M{dia:g} / {dia} mm dia<br/>{pts}<br/>origin {origin}"
    if mh.get("span_mm"):
        return f"{dia} mm dia, span {mh['span_mm'][0]} x {mh['span_mm'][1]} mm"
    return "—"


def cut_text(d):
    cuts = d.get("cutouts") or []
    if not cuts:
        return "none (board sits above the grid)"
    bits = []
    for c in cuts:
        if c["type"] == "circle":
            n = len(c.get("centers_mm") or [0])
            bits.append(f"{n} x dia {c['dia_mm']} mm ({c['purpose']})")
        elif c["type"] == "slot":
            bits.append(f"slot {c['length_mm']} x {c['width_mm']} mm ({c['purpose']})")
        elif c["type"] == "rect":
            inf = " inferred" if c.get("inferred") else ""
            bits.append(f"window {c['w_mm']} x {c['h_mm']} mm{inf} ({c['purpose']})")
    return "<br/>".join(bits)


def main():
    data = json.loads((ROOT / "data" / "devices.json").read_text(encoding="utf-8"))
    sysd = data["system"]
    devices = data["devices"]
    featured = [d for d in devices if d.get("featured")]
    displays = [d for d in devices if not d.get("featured")]
    ss = styles()
    page = landscape(letter)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=page,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        title="Adafruit modular control panel",
        author="adafruit-pannel",
    )
    story = []
    usable = page[0] - 1.1 * inch

    story.append(P("Adafruit modular control panel", ss["Cover"]))
    story.append(P(
        "A 3D-printable 1.00 in (25.4 mm) grid. Print strips, screw them together from below, "
        "stand the boards off the grid with M3 standoffs, and build one solid control surface. "
        "Featured parts: NeoSlider 5295, quad rotary 5752, ANO 6310, rotary 5880 / 4991, plus Adafruit displays.",
        ss["Body"],
    ))
    story.append(P("Locked grid", ss["H"]))
    spec_rows = [
        ["Item", "Value", "Why"],
        ["Pitch", "1.00 in / 25.4 mm", "Matches the 1x1 hole request. Rotary 4991 is a 1.00 in square PCB."],
        ["Strip width", "1 to 5 units (25.4 to 127.0 mm)", "1-wide for sliders and single knobs. 2-wide for ANO. 3 to 5 wide for LCD/TFT."],
        ["Strip length", "4 units / 101.6 mm", "Fits a 3.00 in NeoSlider or quad rotary with margin. Tile length up to 5 strips = 508 mm."],
        ["Max assembly", "5 wide x 5 long = 127.0 x 508.0 mm", "Printable as separate 4 in strips. A 5x4 plate is 127 x 102 mm and fits a Bambu 256 mm bed."],
        ["Grid hole", "3.3 mm through, 6.5 mm x 1.8 mm countersink on the bottom", "M3 screw from below into a female-female standoff. Head sits flush under the panel."],
        ["Panel thickness", "4.0 mm", "Stiff enough as a 1-wide strip. Print countersink on the bed, no supports."],
        ["Board standoff", "M3 FF 11–12 mm", "STEMMA QT connectors are on the bottom of the QT boards. Cables run in the gap."],
        ["Board screws", "M2.5 into the Adafruit PCB holes", "Adafruit plated holes are 2.5 mm. Use the printed adapter so 2.5 mm and 1 in holes do not have to coincide."],
        ["Join", "Tongue + groove on +X/+Y and -X/-Y, plus a 2-hole join-bar under the seam", "Screws from below clamp two strips onto the same standoffs. The 1 in pitch stays continuous across the joint."],
    ]
    story.append(table(spec_rows, [1.3*inch, 2.6*inch, usable - 3.9*inch], ss))
    story.append(Spacer(1, 8))
    story.append(P(
        "The 1 in holes sit at the centre of each cell, not at the corners. A 1-wide strip is 25.4 mm and has one column of holes. "
        "Adafruit board holes are 2.5 mm and sit about 0.10 in in from the PCB corners, so they do not land on the 1 in grid. "
        "Print the adapter plate for that board: M3 holes on the grid, M2.5 holes on the PCB, standoffs in between.",
        ss["Body"],
    ))

    drawings = [P("Print these STLs", ss["H"])]
    gtable = Table(
        [[GridDraw(1, 4, width=2.0*inch, label="1x4"),
          GridDraw(2, 4, width=2.2*inch, label="2x4"),
          GridDraw(5, 4, width=3.4*inch, label="5x4 LCD")]],
        colWidths=[2.2*inch, 2.4*inch, 3.6*inch],
    )
    gtable.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    drawings.append(gtable)
    drawings.append(P(
        "Files in cad/stl/: strip_1x4, strip_2x4, strip_3x4, strip_4x4, strip_5x4, join_bar, "
        "adapter_4991 (also 5880), adapter_5295, adapter_5752, adapter_6310, and matching faceplates. "
        "Print PLA or PETG, 0.20 mm layer, 3 walls, 30% gyroid, no supports, countersink on the bed. "
        "Source: cad/grid-panel.scad.",
        ss["Body"],
    ))
    story.append(KeepTogether(drawings))

    story.append(PageBreak())
    story.append(P("Featured devices — measured from Adafruit Eagle PCB files", ss["H"]))
    story.append(P(
        "Hole coordinates are millimetres from the origin stated in the row. Cut-throughs are for an optional faceplate that sits above the knobs. The base grid itself is a solid 1 in hole plate with no device cutouts.",
        ss["Body"],
    ))
    frows = [["ID", "Device", "PCB mm", "Mounting holes", "Cut-through", "Grid"]]
    for d in featured:
        g = d["grid"]
        pcb = d.get("pcb_mm") or []
        pcb_s = " x ".join(f"{x:g}" for x in pcb[:2]) + " mm"
        grid_s = (
            f"{g['strips_wide']} wide x {g['units_long']} long "
            f"({g['panel_mm'][0]:g} x {g['pcb_h_mm'] if False else g['units_long']*PITCH:.1f} mm)<br/>"
            f"print {g['strips_wide']}x{sysd['strip_length_units']} strip"
        )
        frows.append([
            P(d["product_id"], ss["CellB"]),
            P(f"{d['name']}<br/><font color='#4b5563'>{d.get('notes','')}</font>", ss["Cell"]),
            P(pcb_s, ss["Cell"]),
            P(hole_text(d), ss["Cell"]),
            P(cut_text(d), ss["Cell"]),
            P(grid_s, ss["Cell"]),
        ])
    story.append(table(
        frows,
        [0.55*inch, 2.4*inch, 1.15*inch, 2.3*inch, 2.1*inch, usable - 8.5*inch],
        ss,
    ))

    story.append(P("How each featured board sits", ss["H"]))
    how = [
        ["Board", "Strip", "Adapter", "Above the board"],
        ["5295 NeoSlider", "1-wide x 4 long", "adapter_5295.stl — 4 M3 on the grid, 4 M2.5 at ±19.05 / ±8.255 mm (board rotated so 3 in runs along the strip)", "faceplate_5295.stl slot 75 x 4 mm, or leave open"],
        ["5752 Quad rotary", "1-wide x 4 long", "adapter_5752.stl — same PCB outline as the NeoSlider. Four PEC11 centres at x = ±9.525, ±28.575 mm", "faceplate_5752.stl four 7.5 mm holes. PEC11 bushing is ~7 mm; 7.5 mm is the panel hole."],
        ["4991 / 5880 rotary", "1-wide x 4 long (uses 2 cells)", "adapter_4991.stl is 1x2 so two M3 standoffs stop rotation. Four M2.5 at 2.54 mm from each corner of the 1.00 in PCB.", "faceplate_4991.stl one 7.5 mm hole over the shaft at board centre."],
        ["6310 ANO", "2-wide x 2 long (or a 2x4 strip)", "adapter_6310.stl — 4 M3, 4 M2.5 at ±15.24 / ±17.78 mm. 4.0 mm encoder posts are cleared, do not put screws in them.", "faceplate_6310.stl 22 mm hole for the click wheel."],
    ]
    story.append(table(how, [1.5*inch, 1.5*inch, 3.3*inch, usable - 6.3*inch], ss))

    story.append(PageBreak())
    story.append(P("Adafruit displays — shop-page sizes and strip count", ss["H"]))
    story.append(P(
        "Adafruit category LCDs &amp; Displays was searched (TFT, OLED, character LCD, eInk, HDMI backpacks). "
        "Rows below have a published millimetre size. Hole spans are used when the shop page lists them; otherwise mount with the 1 in grid and an adapter, or 2.5 mm holes 2.5 mm in from the PCB corners (Adafruit default, not verified per display). "
        "Window cut-throughs use the published viewing area, or the PCB minus 2 mm if the view size is not listed (marked inferred). "
        "A display that needs more than 5 strips wide or more than 5 lengths of 4 in does not fit the modular max; it is marked overflow.",
        ss["Body"],
    ))

    drows = [["ID", "Device", "Kind", "Size mm", "Mount", "Cut-through", "Strips W x L"]]
    for d in displays:
        g = d["grid"]
        pcb = d.get("pcb_mm") or d.get("shop_body_mm") or []
        size = " x ".join(f"{x:g}" for x in pcb[:2]) if pcb else "—"
        fit = f"{g['strips_wide']} x {g['units_long']}"
        if g["overflow"]:
            fit = f"<font color='#b45309'>overflow {g['units_wide']} x {g['units_long']}</font>"
        drows.append([
            P(d["product_id"], ss["Cell"]),
            P(d["name"], ss["Cell"]),
            P(d["kind"], ss["Cell"]),
            P(size, ss["Cell"]),
            P(hole_text(d), ss["Cell"]),
            P(cut_text(d), ss["Cell"]),
            P(fit, ss["Cell"]),
        ])
    story.append(table(
        drows,
        [0.5*inch, 2.5*inch, 0.85*inch, 1.1*inch, 1.7*inch, 2.2*inch, 0.85*inch],
        ss,
    ))

    story.append(PageBreak())
    story.append(P("Assembly", ss["H"]))
    steps = [
        "Print one strip per column. A mixer of knobs uses 1-wide strips. A 2.8 in TFT uses a 4-wide (101.6 mm) or a 5-wide (127 mm) plate. A 3.5 in TFT is 4-wide by 3 long — print a 4x4 and leave one row empty, or tile a second 4x4 on the length.",
        "Lay strips on a table, countersink down. Slide +X tongues into the next strip's -X grooves. Length joints use +Y into -Y. The 1 in holes line up across the seam.",
        "Put a join_bar under each seam so its two holes match one hole from each strip. From below, run an M3 screw through the join-bar, through both countersinks, into an 11–12 mm female-female standoff on top. That screw both joins the strips and starts a standoff.",
        "Fill the remaining 1 in holes the same way wherever you will put a board. Empty holes can stay open or take a short M3 screw and nut so the panel stays a solid sheet.",
        "Print the adapter for the board. Screw the adapter onto the standoffs with M3. Screw the Adafruit PCB onto the adapter with M2.5. STEMMA QT cables run in the 11–12 mm gap.",
        "Optional: print the faceplate, stand it off above the knobs, and let shafts / the slider / the display window come through the cut-outs.",
        "Hardware per cell you use: 1 x M3x8 to 12 mm pan or CSK from below, 1 x M3 FF standoff 11–12 mm, 1 x M3x6 into the adapter. Per board: 4 x M2.5x6 mm into the PCB.",
    ]
    for i, s in enumerate(steps, 1):
        story.append(P(f"{i}. {s}", ss["Body"]))

    story.append(P("Print settings that were used to generate the STLs", ss["H"]))
    story.append(P(
        "OpenSCAD nightly, cad/grid-panel.scad, PART= each name. Countersink is on the -Z face. "
        "Bambu / any FDM: 0.4 mm nozzle, 0.20 mm layer, 3 walls, 30% gyroid, 40 mm/s outer wall, no supports, no brim required on the 4x4 and 5x4, a 3 mm brim on the 1x4 strip so it does not peel. "
        "PETG if the panel will sit in a warm rack; PLA is fine for a desk. Do not heat-set inserts in the 4 mm plate — the through hole plus a metal standoff is the joint.",
        ss["Body"],
    ))

    story.append(P("Sources", ss["H"]))
    story.append(P(
        "PCB holes and outlines: Adafruit Eagle files "
        "Adafruit-NeoSlider-PCB, Adafruit-I2C-QT-Rotary-Encoder-PCB, "
        "Adafruit-I2C-Quad-Rotary-Encoder-Breakout-PCB, Adafruit-ANO-Rotary-Navigation-Encoder-to-I2C. "
        "Shop dimensions: https://www.adafruit.com/api/products plus each product technical-details block. "
        "PEC11 panel hole 7.5 mm is the common bushing clearance, not a dimension on the Adafruit PCB.",
        ss["Muted"],
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("wrote", OUT, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
