"""Generate walkthrough narration with edge-tts and mux onto the mp4s."""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
VOICE = "en-US-AndrewNeural"
FFMPEG = r"C:\Users\Jeremy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"

SITE_SCRIPT = """This is the panel case builder at ap.jeremy.ninja.

You are looking at a one inch grid case. A closed four-wall tray, and a shoebox lid. Boards screw to the underside of the lid. Sign in with Amazon to keep projects.

The bottom tray has four walls. M3 screws come from below, into pegs in the lid.

The lid prints face-down. The visible face sits on the bed. Skirt and bosses point up.

Together, the lid drops onto the tray. Drag the three-D view. Magenta marks every cutout.

Every part has a manufacturer page. Pick a device, then open the Adafruit, LilyGO, or M5Stack listing.

Rows can tilt. Three rows flat, two at plus thirty degrees, one at minus thirty. Side walls stay full height at every kink. The skirt hangs straight down, so the lid still drops on.

The bill of materials updates as you place parts. Screw counts and store links are in the table. Then download a zip with the BOM and OpenSCAD files.

Sign in to save folders, cases, and notes. Search your library. List every case that uses a part.

Build the case. Print the lid face-down. ap.jeremy.ninja.
"""

CASE_SCRIPT = """This is a two-piece one inch case. A closed tray, and a shoebox lid. Five by four cells, twenty-five millimetres inside, eight millimetre walls. Boards screw to the underside of the lid.

The lid lifts off. An eight millimetre skirt hangs over the outside of the tray. Short two-and-a-half millimetre pegs locate the lid at the end of the drop.

Print the lid face-down. The visible face is on the bed. No supports. Flip it after print, then drop it on the tray.

The lid flips one hundred eighty degrees, then drops. Pegs are vertical in world Z. M3 from below, through the floor, into the lid. Four walls stay closed.

A ghost lid. Pegs sit in the wall tops. The cavity stays clear. Pegs live in the eight millimetre rim, never in a board cell.

Rows can tilt. Three flat, two at plus thirty degrees, one at minus thirty. Side walls stay full height at every kink. The skirt hangs straight down so the lid still drops on.

Build it at ap.jeremy.ninja. Sign in with Amazon. Save folders, cases, and notes. Download a zip with the BOM and OpenSCAD. The lid prints face-down.
"""


async def speak(text: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(text, VOICE, rate="-5%")
    await comm.save(str(dest))
    print("wrote", dest, dest.stat().st_size, flush=True)


def mux(video: Path, audio: Path, out: Path) -> None:
    cmd = [
        FFMPEG, "-y",
        "-i", str(video),
        "-i", str(audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
        sys.stderr.write(r.stderr[-2500:])
        sys.exit(1)
    print("muxed", out, out.stat().st_size, flush=True)


async def main() -> None:
    site_wav = DOCS / "preview" / "site-intro.mp3"
    case_wav = DOCS / "preview" / "case-anim.mp3"
    await speak(SITE_SCRIPT, site_wav)
    await speak(CASE_SCRIPT, case_wav)
    site_in = DOCS / "site-intro.mp4"
    case_in = DOCS / "case-anim.mp4"
    if not site_in.exists() or not case_in.exists():
        print("video files missing; mux later")
        return
    mux(site_in, site_wav, DOCS / "site-intro-vo.mp4")
    mux(case_in, case_wav, DOCS / "case-anim-vo.mp4")


if __name__ == "__main__":
    asyncio.run(main())
