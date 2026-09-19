"""60 s / 24 fps / 854x480 promo of the 1.00 in modular grid, from the STLs."""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glview import COLORS, Renderer, ensure_standoff, iso_eye, translate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "modular-promo.mp4"
PITCH = 25.4
W, H = 854, 480
FPS = 24
SECONDS = 60
NFRAMES = FPS * SECONDS
FFMPEG = r"C:\Users\Jeremy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"


def lerp(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def scene_t(t, t0, t1):
    if t1 <= t0:
        return 1.0
    return (t - t0) / (t1 - t0)


def hud(img: Image.Image, title: str, lines: list[str]) -> Image.Image:
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
    d.text((W - 210, 10), "1.00 in / 25.4 mm grid", fill=(147, 197, 253), font=tiny)
    return img


def frame_state(t):
    """t in [0,1] over 60 seconds. Returns dict of poses."""
    yaw = 38 + 22 * math.sin(t * math.pi * 2)
    pitch = 28 + 6 * math.sin(t * math.pi * 2 + 0.4)
    dist = 210
    # strip B slides in 6-14s
    sB = lerp(90.0, PITCH / 2, scene_t(t, 0.10, 0.23))
    # strip C (a 2-wide) slides in 14-24s to sit at +1.5 pitch
    sC = lerp(130.0, 1.5 * PITCH, scene_t(t, 0.23, 0.38))
    show_c = t >= 0.22
    # join bars rise 24-32s
    z_join = lerp(-24.0, -3.5, scene_t(t, 0.38, 0.48))
    # standoffs grow 32-42s
    stand_s = lerp(0.02, 1.0, scene_t(t, 0.48, 0.60))
    # adapters drop 42-50s
    z_adp = lerp(36.0, 14.0, scene_t(t, 0.60, 0.72))
    # faceplates drop 50-58s
    z_face = lerp(52.0, 16.6, scene_t(t, 0.72, 0.88))
    show_adp = t >= 0.58
    show_face = t >= 0.70
    # camera pulls back as the panel grows
    dist = lerp(170, 250, t)
    if t < 0.10:
        title = "One strip. 1 x 4 units."
        notes = ["25.4 x 101.6 x 4.0 mm body", "M3 holes on 25.4 mm centres, countersink below"]
    elif t < 0.23:
        title = "Second 1-wide slides on. Tongue into groove."
        notes = ["Assembled pitch stays 25.4 mm", "Join screws come from below"]
    elif t < 0.38:
        title = "A 2-wide plate docks. Now 5 units across."
        notes = ["1-wide + 1-wide + 2-wide = 127.0 mm", "LCD plates print 3, 4 or 5 wide"]
    elif t < 0.48:
        title = "Join bars clamp the seams from below."
        notes = ["40 x 12 x 3 mm bar, two M3 at 25.4 mm", "Same holes take the standoffs"]
    elif t < 0.60:
        title = "M3 standoffs rise from every cell."
        notes = ["11-12 mm female-female", "STEMMA QT cables run in the gap"]
    elif t < 0.72:
        title = "Board adapters drop onto the grid."
        notes = ["M3 on the 1 in grid, M2.5 on the Adafruit PCB", "4991 rotary 1x2   5295 NeoSlider 1x4"]
    elif t < 0.88:
        title = "Faceplates drop. Shafts and slider slots cut through."
        notes = ["7.5 mm PEC11   75 x 4 mm slider   22 mm ANO wheel", "Optional. The base grid has no device cutouts."]
    else:
        title = "One solid control panel."
        notes = ["Print more strips. Tile width 1-5, length x1 to x5.", "cad/stl   1.00 in grid   screws from below"]
        yaw = 42 + 50 * (t - 0.88) / 0.12
        pitch = 26
        dist = 260
    return {
        "yaw": yaw,
        "pitch": pitch,
        "dist": dist,
        "sB": sB,
        "sC": sC,
        "show_c": show_c,
        "z_join": z_join,
        "stand_s": stand_s,
        "z_adp": z_adp,
        "z_face": z_face,
        "show_adp": show_adp,
        "show_face": show_face,
        "title": title,
        "notes": notes,
    }


def draw_scene(rnd: Renderer, s):
    target = np.array([0.5 * PITCH, 0.0, 8.0])
    eye = iso_eye(target, s["dist"], s["yaw"], s["pitch"])
    rnd.begin(eye, target, ortho_span=None, fovy=32, near=5, far=900)
    rnd.ctx.clear(0.09, 0.11, 0.14, 1.0)
    rnd.draw_grid(nx=10, ny=8, pitch=PITCH, z=-4.0)
    # 1-wide left
    rnd.draw("strip_1x4", translate(-PITCH / 2, 0, 0))
    # 1-wide sliding
    rnd.draw("strip_1x4", translate(s["sB"], 0, 0))
    if s["show_c"]:
        rnd.draw("strip_2x4", translate(s["sC"], 0, 0))
    # join bars under seams at x=0 (between first two 1-wides) and x=PITCH (1-wide to 2-wide)
    if s["z_join"] > -23.5:
        for xseam in (0.0, PITCH):
            for y in (-38.1, -12.7, 12.7, 38.1):
                rnd.draw("join_bar", translate(xseam, y, s["z_join"]))
    if s["stand_s"] > 0.05:
        ensure_standoff(rnd)
        for ix in range(5):
            for iy in range(4):
                x = -2 * PITCH + ix * PITCH
                y = -1.5 * PITCH + iy * PITCH
                m = translate(x, y, 4.0)
                m[2, 2] = s["stand_s"]
                rnd.draw("standoff", m, color=COLORS["standoff"])
    if s["show_adp"]:
        rnd.draw("adapter_4991", translate(-PITCH / 2, -PITCH / 2, s["z_adp"]))
        rnd.draw("adapter_5295", translate(PITCH / 2, 0, s["z_adp"]))
        rnd.draw("adapter_6310", translate(2.0 * PITCH, 0, s["z_adp"]))
    if s["show_face"]:
        rnd.draw("faceplate_4991", translate(-PITCH / 2, -PITCH / 2, s["z_face"]))
        rnd.draw("faceplate_5295", translate(PITCH / 2, 0, s["z_face"]))
        rnd.draw("faceplate_6310", translate(2.0 * PITCH, 0, s["z_face"]))


def main():
    rnd = Renderer(W, H, bg=(0.09, 0.11, 0.14))
    rnd.load_all_stls()
    ensure_standoff(rnd)
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
            s = frame_state(t)
            draw_scene(rnd, s)
            img = hud(rnd.image(), s["title"], s["notes"])
            proc.stdin.write(img.tobytes())
            if i % 48 == 0:
                print(f"frame {i}/{NFRAMES} t={t:.2f}", flush=True)
    finally:
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=120)
    if proc.returncode:
        sys.stderr.write(stderr.decode("utf-8", "replace")[-2000:])
        sys.exit(proc.returncode)
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
