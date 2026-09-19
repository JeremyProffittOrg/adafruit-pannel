"""60 s / 24 fps / 854x480 promo v2 of the two-piece case."""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glview import COLORS, Renderer, iso_eye, translate

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "print-kits" / "sliders-quads-case"
OUT = ROOT / "docs" / "modular-promo-v2.mp4"
W, H, FPS, SECONDS = 854, 480, 24, 60
NFRAMES = FPS * SECONDS
FFMPEG = r"C:\Users\Jeremy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"


def lerp(a, b, t):
    t = 0 if t < 0 else 1 if t > 1 else t
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def st(t, a, b):
    return (t - a) / (b - a) if b > a else 1.0


def hud(img, title, lines):
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
        small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)
        tiny = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
        small = font
        tiny = font
    d.rectangle([0, 0, W, 36], fill=(15, 23, 42))
    d.text((12, 8), title, fill=(226, 232, 240), font=font)
    d.rectangle([0, H - 52, W, H], fill=(15, 23, 42))
    y = H - 48
    for line in lines:
        d.text((12, y), line, fill=(226, 232, 240), font=small)
        y += 18
    d.text((W - 168, 10), "promo v2", fill=(147, 197, 253), font=tiny)
    return img


def main():
    rnd = Renderer(W, H, bg=(0.09, 0.11, 0.14))
    rnd.load_stl("bottom", KIT / "bottom.stl")
    rnd.load_stl("top", KIT / "top.stl")
    rnd.load_stl("tilt_b", KIT / "tilt-bottom.stl")
    rnd.load_stl("tilt_t", KIT / "tilt-top.stl")
    bb = rnd._bounds["bottom"]
    tb = rnd._bounds["top"]
    tbb = rnd._bounds["tilt_b"]
    bc = (bb[0] + bb[1]) * 0.5
    tc = (tb[0] + tb[1]) * 0.5
    tbc = (tbb[0] + tbb[1]) * 0.5

    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "pipe:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
        "-movflags", "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i in range(NFRAMES):
            t = i / (NFRAMES - 1)
            if t < 0.22:
                title = "Bottom tray. Walls hold the posts."
                notes = ["8 mm rim  -  M3 from below", "No posts in the board grid"]
                c = bc
                dist = lerp(220, 200, st(t, 0, 0.22))
                yaw = 40 + 50 * t / 0.22
                pitch = 28
                rnd.begin(iso_eye(c, dist, yaw, pitch), c, fovy=32, near=5, far=1200)
                rnd.ctx.clear(0.09, 0.11, 0.14, 1.0)
                rnd.draw("bottom", color=COLORS["strip"])
            elif t < 0.42:
                title = "Top lid. Posts hang from the back, in the rim."
                notes = ["Print flipped: visible face on the bed", "Board bosses sit under the cutouts, inside the cells"]
                c = tc
                dist = 210
                yaw = 50 + 40 * st(t, 0.22, 0.42)
                rnd.begin(iso_eye(c, dist, yaw, 26), c, fovy=32, near=5, far=1200)
                rnd.ctx.clear(0.09, 0.11, 0.14, 1.0)
                rnd.draw("top", color=COLORS["faceplate"])
            elif t < 0.62:
                title = "Lid posts drop into the wall sockets."
                notes = ["Boards screw to the lid from below", "Posts never cross a NeoSlider or quad rotary"]
                lift = lerp(55.0, 4.0, st(t, 0.42, 0.62))
                # shift top so its XY aligns with bottom: move top min to bottom min, then lift
                dx = bb[0][0] - tb[0][0]
                dy = bb[0][1] - tb[0][1]
                dz = bb[1][2] - tb[0][2] + lift
                c = bc + np.array([0, 0, lift / 2])
                yaw = 38 + 25 * st(t, 0.42, 0.62)
                rnd.begin(iso_eye(c, 240, yaw, 22), c, fovy=32, near=5, far=1200)
                rnd.ctx.clear(0.09, 0.11, 0.14, 1.0)
                rnd.draw("bottom", color=COLORS["strip"])
                rnd.draw("top", translate(dx, dy, dz), color=COLORS["faceplate"])
            else:
                title = "Angled rows. Sides go all the way up."
                notes = ["3 flat, 2 at +30 deg, 1 at -30 deg", "Hull fills every kink in the left and right walls"]
                c = tbc
                yaw = 30 + 70 * st(t, 0.62, 1.0)
                dist = lerp(280, 260, st(t, 0.62, 1.0))
                rnd.begin(iso_eye(c, dist, yaw, 18), c, fovy=32, near=5, far=1600)
                rnd.ctx.clear(0.09, 0.11, 0.14, 1.0)
                rnd.draw("tilt_b", color=COLORS["strip"])
                # park the tilted lid slightly above
                ttb = rnd._bounds["tilt_t"]
                dx = tbb[0][0] - ttb[0][0]
                dy = tbb[0][1] - ttb[0][1]
                dz = tbb[1][2] - ttb[0][2] + 8
                rnd.draw("tilt_t", translate(dx, dy, dz), color=COLORS["faceplate"], alpha=0.92)
            img = hud(rnd.image(), title, notes)
            proc.stdin.write(img.tobytes())
            if i % 48 == 0:
                print(f"frame {i}/{NFRAMES}", flush=True)
    finally:
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=120)
    if proc.returncode:
        sys.stderr.write(stderr.decode("utf-8", "replace")[-2000:])
        sys.exit(proc.returncode)
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
