"""Render every STL from iso/top/side plus exploded and base-plate family views, then build a PDF."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from glview import (
    COLORS,
    Renderer,
    caption,
    ensure_standoff,
    iso_eye,
    part_kind,
    translate,
)

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "docs" / "views"
PDF = ROOT / "docs" / "stl-kit.pdf"
PITCH = 25.4

PARTS = [
    "strip_1x4",
    "strip_2x4",
    "strip_3x4",
    "strip_4x4",
    "strip_5x4",
    "join_bar",
    "adapter_4991",
    "adapter_5295",
    "adapter_5752",
    "adapter_6310",
    "faceplate_4991",
    "faceplate_5295",
    "faceplate_5752",
    "faceplate_6310",
]

LABELS = {
    "strip_1x4": "Base strip 1 x 4  (25.4 x 101.6 mm body)",
    "strip_2x4": "Base strip 2 x 4  (50.8 x 101.6 mm body)",
    "strip_3x4": "Base strip 3 x 4  (76.2 x 101.6 mm body)",
    "strip_4x4": "Base strip 4 x 4  (101.6 x 101.6 mm body)",
    "strip_5x4": "Base strip 5 x 4  (127.0 x 101.6 mm body, LCD)",
    "join_bar": "Join bar  (40 x 12 x 3 mm, two M3 at 25.4 mm)",
    "adapter_4991": "Adapter 4991 / 5880 rotary  (1 x 2 cells)",
    "adapter_5295": "Adapter 5295 NeoSlider  (1 x 4 cells)",
    "adapter_5752": "Adapter 5752 quad rotary  (1 x 4 cells)",
    "adapter_6310": "Adapter 6310 ANO  (2 x 2 cells)",
    "faceplate_4991": "Faceplate 4991 / 5880  (7.5 mm shaft hole)",
    "faceplate_5295": "Faceplate 5295  (75 x 4 mm slider slot)",
    "faceplate_5752": "Faceplate 5752  (four 7.5 mm shaft holes)",
    "faceplate_6310": "Faceplate 6310  (22 mm click-wheel hole)",
}

NAVY = colors.HexColor("#0f172a")
INK = colors.HexColor("#0b0f19")
WHITE = colors.HexColor("#ffffff")


def span_for(bounds, pad=1.35):
    ext = bounds[1] - bounds[0]
    return float(max(ext) * pad) * 0.55


def render_part_views(rnd: Renderer, name: str) -> dict[str, Path]:
    bounds = rnd._bounds[name]
    c = (bounds[0] + bounds[1]) * 0.5
    ext = bounds[1] - bounds[0]
    dist = float(np.linalg.norm(ext)) * 1.8 + 40
    span = span_for(bounds)
    out = {}
    shots = {
        "iso": (iso_eye(c, dist, 45, 35.264), span),
        "iso_back": (iso_eye(c, dist, 225, 28), span),
        "top": (c + np.array([0.3, 0.0, dist]), span * 0.95),
        "side": (c + np.array([dist, 0.0, ext[2] * 0.5 + 8]), span),
    }
    for key, (eye, sp) in shots.items():
        rnd.begin(eye, c, ortho_span=sp, near=0.5, far=2000)
        rnd.draw(name)
        img = caption(
            rnd.image(),
            [LABELS[name], key.replace("_", " ").upper()],
            footer=f"body {ext[0]:.2f} x {ext[1]:.2f} x {ext[2]:.2f} mm   1.00 in grid   M3 from below",
        )
        path = VIEWS / f"{name}_{key}.png"
        img.save(path, "PNG", optimize=True)
        out[key] = path
    return out


def render_family(rnd: Renderer) -> Path:
    # 1x4 through 5x4 in a row, true 25.4 mm pitch between strip centres.
    # Each strip is centered on origin, so place at x = (n-1)*PITCH/2 offset from a shared baseline.
    # Put them on a line along X with 8 mm gaps between bodies.
    xs = []
    x = 0.0
    gap = 8.0
    widths = [1, 2, 3, 4, 5]
    for n in widths:
        w = n * PITCH
        xs.append(x + w / 2)
        x += w + gap
    total_w = x - gap
    center = np.array([total_w / 2, 0.0, 2.0])
    dist = 280
    rnd.begin(iso_eye(center, dist, 40, 32), center, ortho_span=155, near=1, far=2000)
    rnd.draw_grid(nx=12, ny=6, pitch=PITCH, z=-2.0)
    for n, cx in zip(widths, xs):
        rnd.draw(f"strip_{n}x4", translate(cx, 0, 0))
    img = caption(
        rnd.image(),
        ["Base plates  1x4 through 5x4", "Bodies 25.4 mm * N wide, 101.6 mm long, 4.0 mm thick"],
        footer="gap 8 mm in this family view only   assembled pitch is 25.4 mm with zero gap",
    )
    path = VIEWS / "base_plates_family.png"
    img.save(path, "PNG", optimize=True)
    return path


def render_family_top(rnd: Renderer) -> Path:
    xs = []
    x = 0.0
    gap = 8.0
    widths = [1, 2, 3, 4, 5]
    for n in widths:
        w = n * PITCH
        xs.append(x + w / 2)
        x += w + gap
    total_w = x - gap
    center = np.array([total_w / 2, 0.0, 0.0])
    rnd.begin(center + np.array([0.2, 0.0, 320]), center, ortho_span=155, near=1, far=2000)
    rnd.draw_grid(nx=14, ny=6, pitch=PITCH, z=-2.0)
    for n, cx in zip(widths, xs):
        rnd.draw(f"strip_{n}x4", translate(cx, 0, 0))
    img = caption(
        rnd.image(),
        ["Base plates  top orthographic", "Hole centres on a 25.4 mm grid"],
        footer="1-wide = one hole column   5-wide = five hole columns for LCD",
    )
    path = VIEWS / "base_plates_top.png"
    img.save(path, "PNG", optimize=True)
    return path


def render_exploded(rnd: Renderer) -> Path:
    ensure_standoff(rnd)
    # One 2x4 strip with join bars, standoffs, 4991 adapter+faceplate and 5295 adapter+faceplate.
    # Explode along Z.
    z_join, z_strip, z_stand, z_adp, z_face = -18.0, 0.0, 22.0, 42.0, 64.0
    center = np.array([0.0, 0.0, 30.0])
    rnd.begin(iso_eye(center, 210, 48, 28), center, ortho_span=78, near=1, far=2000)
    rnd.draw_grid(nx=6, ny=6, pitch=PITCH, z=-22)
    # two 1x4 strips side by side = 2 wide, exploded in X as well
    gap = 14.0
    rnd.draw("strip_1x4", translate(-PITCH / 2 - gap / 2, 0, z_strip))
    rnd.draw("strip_1x4", translate(PITCH / 2 + gap / 2, 0, z_strip))
    # join bars under the seam (two along Y)
    for iy, y in enumerate((-38.1, -12.7, 12.7, 38.1)):
        rnd.draw("join_bar", translate(0, y, z_join), color=COLORS["join"])
    # standoffs on a 2x4 grid
    for ix in (-0.5, 0.5):
        for iy in range(4):
            x = ix * PITCH
            y = -PITCH * 1.5 + iy * PITCH
            rnd.draw("standoff", translate(x, y, z_stand), color=COLORS["standoff"])
    rnd.draw("adapter_4991", translate(-PITCH / 2, -PITCH / 2, z_adp))
    rnd.draw("faceplate_4991", translate(-PITCH / 2, -PITCH / 2, z_face))
    rnd.draw("adapter_5295", translate(PITCH / 2, 0, z_adp))
    rnd.draw("faceplate_5295", translate(PITCH / 2, 0, z_face))
    img = caption(
        rnd.image(),
        ["Exploded modular stack", "join bar  ->  1x4 strips  ->  M3 standoffs  ->  adapter  ->  faceplate"],
        footer="true millimetres   strips pulled 14 mm apart in X, layers 18-22 mm in Z for the breakout",
    )
    path = VIEWS / "exploded_stack.png"
    img.save(path, "PNG", optimize=True)
    return path


def render_assembled_base(rnd: Renderer) -> Path:
    # 5-wide panel made of 1+2+2 strips, true pitch, no extra gap.
    center = np.array([0.0, 0.0, 2.0])
    rnd.begin(iso_eye(center, 240, 42, 30), center, ortho_span=88, near=1, far=2000)
    rnd.draw_grid(nx=8, ny=6, pitch=PITCH, z=-2)
    # 1-wide at left, 2-wide, 2-wide
    rnd.draw("strip_1x4", translate(-2 * PITCH, 0, 0))
    rnd.draw("strip_2x4", translate(-0.5 * PITCH, 0, 0))
    rnd.draw("strip_2x4", translate(1.5 * PITCH, 0, 0))
    img = caption(
        rnd.image(),
        ["Assembled base  5 units wide", "1-wide + 2-wide + 2-wide   pitch 25.4 mm   length 101.6 mm"],
        footer="screws from below through join bars into standoffs on top",
    )
    path = VIEWS / "assembled_base.png"
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
    canvas.drawString(24, doc.pagesize[1] - 15, "Adafruit modular panel  -  STL isometric kit")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, doc.pagesize[0], 18, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(24, 6, "cad/stl   1.00 in / 25.4 mm grid   M3 from below")
    canvas.drawRightString(doc.pagesize[0] - 24, 6, f"page {doc.page}")
    canvas.restoreState()


def P(text, style):
    return Paragraph(str(text), style)


def img_flow(path: Path, w, h):
    im = RLImage(str(path), width=w, height=h)
    im.hAlign = "CENTER"
    return im


def build_pdf(part_views: dict, family, family_top, exploded, assembled):
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Cover", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=8))
    ss.add(ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=8, spaceAfter=6))
    ss.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK, spaceAfter=6))
    ss.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8, leading=11, textColor=INK))
    page = landscape(letter)
    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=page,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.42 * inch,
        bottomMargin=0.36 * inch,
        title="Adafruit modular panel STL kit",
        author="adafruit-pannel",
    )
    usable_w = page[0] - 0.9 * inch
    usable_h = page[1] - 0.9 * inch
    story = []
    story.append(P("STL isometric kit", ss["Cover"]))
    story.append(P(
        "Every printable part in cad/stl, drawn from the STL in millimetres. "
        "Orthographic cameras. Isometric is yaw 45 deg, pitch 35.264 deg. "
        "Hole pitch 25.4 mm. Strip body 25.4 * N by 101.6 mm, 4.0 mm thick. "
        "M3 screws from below into female-female standoffs.",
        ss["Body"],
    ))
    story.append(P("Base plates", ss["H"]))
    story.append(img_flow(family, usable_w, usable_h * 0.42))
    story.append(Spacer(1, 6))
    story.append(img_flow(family_top, usable_w, usable_h * 0.38))
    story.append(PageBreak())
    story.append(P("Assembled 5-wide base and exploded stack", ss["H"]))
    story.append(img_flow(assembled, usable_w, usable_h * 0.44))
    story.append(Spacer(1, 6))
    story.append(img_flow(exploded, usable_w, usable_h * 0.44))
    story.append(P(
        "Exploded Z offsets are 18-22 mm so you can see each layer. "
        "X gap 14 mm between the two 1x4 strips is for the breakout only; "
        "the assembled pitch is 25.4 mm with tongues in grooves.",
        ss["Small"],
    ))
    for name in PARTS:
        story.append(PageBreak())
        story.append(P(LABELS[name], ss["H"]))
        pv = part_views[name]
        cell_w = 4.8 * inch
        cell_h = 2.55 * inch
        grid = Table(
            [
                [img_flow(pv["iso"], cell_w, cell_h), img_flow(pv["iso_back"], cell_w, cell_h)],
                [img_flow(pv["top"], cell_w, cell_h), img_flow(pv["side"], cell_w, cell_h)],
            ],
            colWidths=[usable_w / 2, usable_w / 2],
        )
        grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(grid)
        story.append(P("Top-left isometric. Top-right reverse isometric. Bottom-left top ortho. Bottom-right side ortho.", ss["Small"]))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("wrote", PDF, PDF.stat().st_size)


def main():
    VIEWS.mkdir(parents=True, exist_ok=True)
    rnd = Renderer(1280, 900, bg=(0.93, 0.94, 0.96))
    rnd.load_all_stls()
    part_views = {}
    for name in PARTS:
        print("view", name, flush=True)
        part_views[name] = render_part_views(rnd, name)
    print("family", flush=True)
    family = render_family(rnd)
    family_top = render_family_top(rnd)
    exploded = render_exploded(rnd)
    assembled = render_assembled_base(rnd)
    build_pdf(part_views, family, family_top, exploded, assembled)


if __name__ == "__main__":
    main()
