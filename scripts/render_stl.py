"""Render each PART in cad/grid-panel.scad to a binary STL."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / "cad" / "grid-panel.scad"
OUT = ROOT / "cad" / "stl"
OPENSCAD = Path(r"C:\Users\Jeremy\tools\openscad-nightly\openscad.exe")
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for part in PARTS:
        dest = OUT / f"{part}.stl"
        cmd = [
            str(OPENSCAD),
            "-o",
            str(dest),
            "-D",
            f'PART="{part}"',
            "--export-format=binstl",
            str(SCAD),
        ]
        print("render", part, flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
            failed.append(part)
            print(r.stdout[-500:] if r.stdout else "")
            print(r.stderr[-800:] if r.stderr else "")
        else:
            print(" ", dest.name, dest.stat().st_size, "bytes")
    if failed:
        print("FAILED", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
