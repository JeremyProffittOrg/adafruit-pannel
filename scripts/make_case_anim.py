"""Extensive case animation: skirt drop, print flip, explode, tilt. 1280x720 24 fps 75 s."""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glview import COLORS, Renderer, iso_eye, lid_flip_animate, lid_print_to_use, translate

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "print-kits" / "sliders-quads-case"
GEN = ROOT / "cad" / "generated"
OUT = ROOT / "docs" / "case-anim.mp4"
POSTER = ROOT / "docs" / "preview" / "case-anim-poster.png"
W, H, FPS, SECONDS = 1280, 720, 24, 75
NFRAMES = FPS * SECONDS
FFMPEG = r"C:\Users\Jeremy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"


def lerp(a, b, t):
    t = 0 if t < 0 else 1 if t > 1 else t
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def st(t, a, b):
    return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)


def hud(img, title, lines):
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
        small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
        tiny = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = font
        tiny = font
    d.rectangle([0, 0, W, 44], fill=(11, 15, 25))
    d.text((16, 8), title, fill=(226, 232, 240), font=font)
    d.rectangle([0, H - 58, W, H], fill=(11, 15, 25))
    y = H - 54
    for line in lines:
        d.text((16, y), line, fill=(226, 232, 240), font=small)
        y += 22
    d.text((W - 220, 12), "ap.jeremy.ninja", fill=(147, 197, 253), font=tiny)
    return img


def main():
    rnd = Renderer(W, H, bg=(0.07, 0.09, 0.12))
    rnd.load_stl("tray", KIT / "bottom.stl")
    rnd.load_stl("lid_print", KIT / "top.stl")
    lid_use = GEN / "sq-top-use.stl"
    if not lid_use.exists():
        lid_use = KIT / "top.stl"
    rnd.load_stl("lid_use", lid_use)
    rnd.load_stl("tilt_tray", KIT / "face-tilt-bottom.stl")
    tilt_use = GEN / "face-tilt-top-use.stl"
    if not tilt_use.exists():
        tilt_use = KIT / "face-tilt-top.stl"
    rnd.load_stl("tilt_lid", tilt_use)
    rnd.load_stl("tilt_print", KIT / "face-tilt-top.stl")

    tray_b = rnd._bounds["tray"]
    print_b = rnd._bounds["lid_print"]
    use_b = rnd._bounds["lid_use"]
    tilt_b = rnd._bounds["tilt_tray"]
    tray_c = (tray_b[0] + tray_b[1]) * 0.5
    print_c = (print_b[0] + print_b[1]) * 0.5
    use_c = (use_b[0] + use_b[1]) * 0.5
    tilt_c = (tilt_b[0] + tilt_b[1]) * 0.5
    assy_c = tray_c + np.array([0.0, 0.0, 16.0])

    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "pipe:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium",
        "-movflags", "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    poster = None
    try:
        for i in range(NFRAMES):
            t = i / (NFRAMES - 1)
            if t < 0.12:
                title = "Two-piece 1.00 in case. Closed tray. Shoebox lid."
                notes = ["5 x 4 cells  -  25 mm inside  -  8 mm walls", "Boards screw to the underside of the lid"]
                u = st(t, 0.00, 0.12)
                yaw = 28 + 70 * u
                dist = lerp(240, 210, u)
                rnd.begin(iso_eye(assy_c, dist, yaw, 24), assy_c, fovy=30, near=4, far=1600)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw_grid(8, 6, 25.4, z=-1.0)
                rnd.draw("tray", color=COLORS["strip"])
                rnd.draw("lid_use", color=COLORS["faceplate"])
            elif t < 0.24:
                title = "Explode. Lid lifts off the tray. Skirt clears the walls."
                notes = ["8 mm skirt hangs over the outside of the tray", "Short 2.5 mm pegs locate the lid at the end of the drop"]
                u = st(t, 0.12, 0.24)
                lift = lerp(0.0, 48.0, u)
                yaw = 40 + 50 * u
                rnd.begin(iso_eye(assy_c + np.array([0, 0, lift * 0.3]), 230, yaw, 22), assy_c, fovy=30, near=4, far=1600)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw("tray", color=COLORS["strip"])
                rnd.draw("lid_use", translate(0, 0, lift), color=COLORS["faceplate"])
            elif t < 0.38:
                title = "Print the lid face-down. Skirt and bosses point up."
                notes = ["Visible face on the bed. No supports.", "Flip it after print, then drop it on the tray."]
                u = st(t, 0.24, 0.38)
                yaw = 20 + 80 * u
                pitch = lerp(55, 22, u)
                rnd.begin(iso_eye(print_c, 200, yaw, pitch), print_c, fovy=30, near=4, far=1400)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw_grid(6, 5, 25.4, z=-0.4)
                rnd.draw("lid_print", color=COLORS["faceplate"])
            elif t < 0.56:
                title = "Flip 180 deg, then drop. Skirt finds the tray."
                notes = ["World-Z pegs. M3 from below through the floor into the lid.", "Four walls stay closed. No through-wall sockets."]
                u = st(t, 0.38, 0.56)
                angle = lerp(0.0, 180.0, min(1.0, u / 0.55))
                drop = lerp(0.0, 1.0, st(u, 0.50, 1.0))
                model = lid_flip_animate(print_b, tray_b, 4, angle, drop)
                c = assy_c + np.array([0.0, 0.0, 20.0])
                yaw = 38 + 24 * u
                rnd.begin(iso_eye(c, 260, yaw, 18), c, fovy=30, near=4, far=1600)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw("tray", color=COLORS["strip"])
                rnd.draw("lid_print", model, color=COLORS["faceplate"])
            elif t < 0.66:
                title = "Ghost lid. Pegs sit in the wall tops. Cavity stays clear."
                notes = ["Pegs live in the 8 mm rim, never in a board cell", "PCBs hang from the lid on M2.5 bosses"]
                u = st(t, 0.56, 0.66)
                yaw = 50 + 40 * u
                rnd.begin(iso_eye(assy_c, 200, yaw, 16), assy_c, fovy=28, near=4, far=1400)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw("tray", color=COLORS["strip"])
                rnd.draw("lid_use", color=COLORS["faceplate"], alpha=0.42)
            elif t < 0.82:
                title = "Tilted rows. Side walls stay full height at every kink."
                notes = ["3 flat, 2 at +30 deg, 1 at -30 deg", "World-Z fasteners on flat rows. Skirt follows the lid."]
                u = st(t, 0.66, 0.82)
                yaw = 25 + 85 * u
                dist = lerp(300, 270, u)
                c = tilt_c + np.array([0, 0, 18])
                rnd.begin(iso_eye(c, dist, yaw, 18), c, fovy=30, near=5, far=1800)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw("tilt_tray", color=COLORS["strip"])
                seated = lid_print_to_use(6, lift=0.0)
                # tilt-top-use is already in use pose; identity if file is use STL
                if tilt_use.name.endswith("use.stl"):
                    rnd.draw("tilt_lid", color=COLORS["adapter"], alpha=0.94)
                else:
                    rnd.draw("tilt_print", seated, color=COLORS["adapter"], alpha=0.94)
            else:
                title = "Build it at ap.jeremy.ninja"
                notes = ["Sign in with Amazon. Save folders, cases, notes.", "Download zip: BOM + OpenSCAD. Lid prints face-down."]
                u = st(t, 0.82, 1.0)
                yaw = 35 + 50 * u
                left = translate(-95, 0, 0)
                right = translate(110, -20, 0)
                c = assy_c
                rnd.begin(iso_eye(c, 340, yaw, 20), c, fovy=32, near=6, far=2000)
                rnd.ctx.clear(0.07, 0.09, 0.12, 1.0)
                rnd.draw("tray", left, color=COLORS["strip"])
                rnd.draw("lid_use", left, color=COLORS["faceplate"])
                rnd.draw("tilt_tray", right, color=COLORS["join"])
                if tilt_use.name.endswith("use.stl"):
                    rnd.draw("tilt_lid", right, color=COLORS["adapter"], alpha=0.94)
                else:
                    rnd.draw("tilt_print", right @ lid_print_to_use(6, 0.0), color=COLORS["adapter"], alpha=0.94)
            img = hud(rnd.image(), title, notes)
            if i == int(0.08 * (NFRAMES - 1)):
                poster = img.copy()
            proc.stdin.write(img.tobytes())
            if i % 48 == 0:
                print(f"case-anim frame {i}/{NFRAMES}", flush=True)
    finally:
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=180)
    if proc.returncode:
        sys.stderr.write(stderr.decode("utf-8", "replace")[-2500:])
        sys.exit(proc.returncode)
    if poster:
        POSTER.parent.mkdir(parents=True, exist_ok=True)
        poster.save(POSTER, "PNG")
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
