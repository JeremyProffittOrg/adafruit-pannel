"""60 s user-introduction video of https://ap.jeremy.ninja  1280x720 24 fps."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "site-intro.mp4"
POSTER = ROOT / "docs" / "preview" / "site-intro-poster.png"
W, H, FPS, SECONDS = 1280, 720, 24, 60
NFRAMES = FPS * SECONDS
FFMPEG = r"C:\Users\Jeremy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
URL = "https://ap.jeremy.ninja/"


def hud(img, title, line):
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
        small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
        tiny = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = font
        tiny = font
    d.rectangle([0, 0, W, 44], fill=(11, 15, 25))
    d.text((16, 8), title, fill=(226, 232, 240), font=font)
    d.rectangle([0, H - 40, W, H], fill=(11, 15, 25))
    d.text((16, H - 32), line, fill=(226, 232, 240), font=small)
    d.text((W - 220, 12), "ap.jeremy.ninja", fill=(147, 197, 253), font=tiny)
    return img


def grab(page, title, line):
    raw = page.screenshot(type="png")
    img = Image.open(__import__("io").BytesIO(raw)).convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H), Image.Resampling.LANCZOS)
    return hud(img, title, line)


def hold(proc, img, seconds):
    n = max(1, int(seconds * FPS))
    buf = img.tobytes()
    for _ in range(n):
        proc.stdin.write(buf)


def main():
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
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-gl=angle", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#view3d canvas", timeout=30000)
        time.sleep(2.5)
        shots = []

        shots.append((grab(page, "Panel case builder on the web", "1.00 in grid. Closed tray. Shoebox lid. Sign in with Amazon to keep projects."), 6.0))
        page.click("button[data-view='bottom']")
        time.sleep(1.2)
        shots.append((grab(page, "Bottom tray", "Four walls. M3 from below. Peg sockets in the wall tops."), 5.0))
        page.click("button[data-view='top']")
        time.sleep(1.2)
        shots.append((grab(page, "Lid", "Print this face-down. Skirt and bosses point up off the bed."), 5.0))
        page.click("button[data-view='assembly']")
        time.sleep(1.2)
        shots.append((grab(page, "Together", "Drag the 3D view. Magenta marks every cutout."), 6.0))

        page.fill("#devfilter", "neoslider")
        time.sleep(0.4)
        page.select_option("#device", "neoslider")
        time.sleep(0.6)
        shots.append((grab(page, "Parts have manufacturer pages", "Pick a device. Open the Adafruit / LilyGO / M5Stack listing."), 6.0))

        page.click("#preset-tilt")
        time.sleep(1.6)
        shots.append((grab(page, "Row tilt", "3 rows flat, 2 at +30 deg, 1 at -30 deg. Side walls stay full height."), 6.0))

        page.click("#preset-sq")
        time.sleep(1.4)
        page.evaluate("document.getElementById('bom')?.scrollIntoView({block:'center'})")
        time.sleep(0.4)
        shots.append((grab(page, "Bill of materials", "Counts, screws, and links update as you place parts. Then download a zip."), 8.0))

        page.evaluate("window.scrollTo(0,0)")
        time.sleep(0.3)
        shots.append((grab(page, "Save projects after you sign in", "Folders, cases, notes, search, and cases-by-part. Zip = BOM + OpenSCAD."), 8.0))
        shots.append((grab(page, "ap.jeremy.ninja", "Sign in with Amazon. Build the case. Print the lid face-down."), 10.0))

        poster = shots[0][0].copy()
        total = 0.0
        try:
            for img, dur in shots:
                hold(proc, img, dur)
                total += dur
            # pad/trim to exactly SECONDS
            if total < SECONDS:
                hold(proc, shots[-1][0], SECONDS - total)
        finally:
            proc.stdin.close()
            stdout, stderr = proc.communicate(timeout=120)
            browser.close()
    if proc.returncode:
        sys.stderr.write(stderr.decode("utf-8", "replace")[-2500:])
        sys.exit(proc.returncode)
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    poster.save(POSTER, "PNG")
    print("wrote", OUT, OUT.stat().st_size, "held", total)


if __name__ == "__main__":
    main()
