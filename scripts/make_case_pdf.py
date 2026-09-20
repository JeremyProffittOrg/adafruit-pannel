"""PDF of the two-piece case: bottom tray and print-flipped top lid."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glview import COLORS, Renderer, caption, iso_eye, lid_print_to_use, translate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "docs" / "case-views"
PDF = ROOT / "docs" / "case-parts.pdf"
NAVY = colors.HexColor("#0f172a")
INK = colors.HexColor("#0b0f19")
WHITE = colors.HexColor("#ffffff")

PARTS = [
    ("bottom", ROOT / "print-kits" / "sliders-quads-case" / "bottom.stl", COLORS["strip"],
     "Bottom tray  5 x 4 cells  25 mm inside  M3 from below, blind peg sockets"),
    ("top", ROOT / "print-kits" / "sliders-quads-case" / "top.stl", COLORS["faceplate"],
     "Top lid  print this way (visible face on the bed, skirt and bosses up)"),
    ("face_tilt_bottom", ROOT / "print-kits" / "sliders-quads-case" / "face-tilt-bottom.stl", COLORS["join"],
     "Face-tilt tray  5 x 4  sitting 30 deg, floor fill to 3 mm above the table"),
    ("face_tilt_top", ROOT / "print-kits" / "sliders-quads-case" / "face-tilt-top.stl", COLORS["adapter"],
     "Face-tilt lid  print face-down, short rim pegs"),
]


def span_for(bounds, pad=1.25):
    ext = bounds[1] - bounds[0]
    return float(max(ext) * pad) * 0.52


def shots(name, rnd, color, label):
    bounds = rnd._bounds[name]
    c = (bounds[0] + bounds[1]) * 0.5
    ext = bounds[1] - bounds[0]
    dist = float(np.linalg.norm(ext)) * 1.7 + 50
    sp = span_for(bounds)
    out = {}
    cams = {
        "iso": (iso_eye(c, dist, 48, 32), sp),
        "iso_back": (iso_eye(c, dist, 220, 24), sp),
        "top": (c + np.array([0.3, 0.0, dist]), sp * 0.95),
        "side": (c + np.array([dist, 0.2, ext[2] * 0.4]), sp),
    }
    for key, (eye, s) in cams.items():
        rnd.begin(eye, c, ortho_span=s, near=0.5, far=2500)
        rnd.draw(name, color=color)
        img = caption(
            rnd.image(),
            [label, key.replace("_", " ").upper()],
            footer=f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm   1.00 in grid",
        )
        path = VIEWS / f"{name}_{key}.png"
        img.save(path, "PNG", optimize=True)
        out[key] = path
    return out


def exploded(rnd):
    bb = rnd._bounds["bottom"]
    tb = rnd._bounds["top"]
    bc = (bb[0] + bb[1]) * 0.5
    gap = 40.0
    # place top to the right of bottom, both on z=0
    dx = (bb[1][0] - bb[0][0]) / 2 + (tb[1][0] - tb[0][0]) / 2 + gap
    center = np.array([bc[0] + dx / 2, bc[1], 20.0])
    rnd.begin(iso_eye(center, 280, 42, 28), center, ortho_span=95, near=1, far=3000)
    rnd.draw("bottom", color=COLORS["strip"])
    rnd.draw("top", translate(dx, 0, 0), color=COLORS["faceplate"])
    img = caption(
        rnd.image(),
        ["Print pair  3 NeoSlider + 2 quad rotary", "Left: tray. Right: lid already flipped for the bed."],
        footer="M3 from below through tray posts into lid bosses   M2.5 into boards from below",
    )
    path = VIEWS / "print_pair.png"
    img.save(path, "PNG", optimize=True)
    return path


def fit_test(rnd):
    bb = rnd._bounds["bottom"]
    bc = (bb[0] + bb[1]) * 0.5
    center = bc + np.array([0.0, 0.0, 16.0])
    rnd.begin(iso_eye(center, 240, 44, 22), center, ortho_span=85, near=1, far=3000)
    rnd.draw("bottom", color=COLORS["strip"])
    rnd.draw("top", lid_print_to_use(4, 0.0), color=COLORS["faceplate"])
    img = caption(
        rnd.image(),
        ["Fit test  lid flipped off the bed, posts down", "Two side walls only. Front and back stay open."],
        footer="Print the lid upside down, flip it over, drop into the left and right walls",
    )
    path = VIEWS / "assembly_fit.png"
    img.save(path, "PNG", optimize=True)
    return path


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, doc.pagesize[1] - 22, doc.pagesize[0], 22, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(24, doc.pagesize[1] - 15, "Adafruit modular case  -  two-piece print kit")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, doc.pagesize[0], 18, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(24, 6, "bottom tray + top lid   5 x 4 x 25 mm inside")
    canvas.drawRightString(doc.pagesize[0] - 24, 6, f"page {doc.page}")
    canvas.restoreState()


def P(text, ss):
    return Paragraph(str(text), ss)


def img_flow(path, w, h):
    im = RLImage(str(path), width=w, height=h)
    im.hAlign = "CENTER"
    return im


def main():
    VIEWS.mkdir(parents=True, exist_ok=True)
    rnd = Renderer(1280, 900, bg=(0.93, 0.94, 0.96))
    views = {}
    for name, path, color, label in PARTS:
        print("load", name, flush=True)
        rnd.load_stl(name, path)
        views[name] = shots(name, rnd, color, label)
    pair = exploded(rnd)
    fit = fit_test(rnd)

    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Cover", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=8))
    ss.add(ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=8, spaceAfter=6))
    ss.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK, spaceAfter=6))
    ss.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8, leading=11, textColor=INK))
    page = landscape(letter)
    doc = SimpleDocTemplate(
        str(PDF), pagesize=page,
        leftMargin=0.45 * inch, rightMargin=0.45 * inch,
        topMargin=0.42 * inch, bottomMargin=0.36 * inch,
        title="Two-piece case print kit", author="adafruit-pannel",
    )
    usable_w = page[0] - 0.9 * inch
    story = []
    story.append(P("Two-piece case print kit", ss["Cover"]))
    story.append(P(
        "Bottom tray and top lid for 3 NeoSliders beside 2 quad rotaries. "
        "5 x 4 cells, 25 mm inside. Top is already flipped: put the STL on the bed as exported. "
        "Boards screw into bosses under the lid. M3 screws come from below through the tray into the lid posts.",
        ss["Body"],
    ))
    story.append(P("Print pair", ss["H"]))
    story.append(img_flow(pair, usable_w, 4.4 * inch))
    story.append(P("Fit test — flip the lid over", ss["H"]))
    story.append(P(
        "The lid STL is already upside down for the bed. Flip it 180 deg so the posts point down, then drop it onto the two side walls. Front and back of the tray are open.",
        ss["Body"],
    ))
    story.append(img_flow(fit, usable_w, 4.4 * inch))
    labels = {
        "bottom": "Bottom tray",
        "top": "Top lid (print orientation)",
        "tilt_bottom": "Tilted tray demo",
        "tilt_top": "Tilted lid demo",
    }
    for name, _, _, _ in PARTS:
        story.append(PageBreak())
        story.append(P(labels[name], ss["H"]))
        pv = views[name]
        cell_w, cell_h = 4.8 * inch, 2.55 * inch
        grid = Table(
            [
                [img_flow(pv["iso"], cell_w, cell_h), img_flow(pv["iso_back"], cell_w, cell_h)],
                [img_flow(pv["top"], cell_w, cell_h), img_flow(pv["side"], cell_w, cell_h)],
            ],
            colWidths=[usable_w / 2, usable_w / 2],
        )
        grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(grid)
        story.append(P("Iso, reverse iso, top ortho, side ortho. Millimetres from the STL.", ss["Small"]))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("wrote", PDF, PDF.stat().st_size)


if __name__ == "__main__":
    main()
