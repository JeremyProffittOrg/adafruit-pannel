"""Render sliders-quads and tilt-demo case STLs from cad/case.scad."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSC = Path(r"C:\Users\Jeremy\tools\openscad-nightly\openscad.exe")
GEN = ROOT / "cad" / "generated"
KIT = ROOT / "print-kits" / "sliders-quads-case"

SQ = """PART = "{part}";
COLS = 5; ROWS = 4; INNER_H = 25;
EDGE_STYLE = "round"; EDGE_MM = 2;
TILTS = [0, 0, 0, 0];
NDEV = 5;
DEV_ID = ["neoslider", "neoslider", "neoslider", "quad_rotary", "quad_rotary"];
DEV_C = [0, 1, 2, 3, 4];
DEV_R = [0, 0, 0, 0, 0];
NWALL = 0;
include <../case.scad>
"""

TILT = """PART = "{part}";
COLS = 4; ROWS = 6; INNER_H = 25;
EDGE_STYLE = "round"; EDGE_MM = 2;
TILTS = [0, 0, 0, 30, 30, -30];
NDEV = 0; NWALL = 0;
include <../case.scad>
"""

JOBS = [
    ("sq", "bottom", GEN / "sq-bottom.stl", KIT / "bottom.stl"),
    ("sq", "top", GEN / "sq-top.stl", KIT / "top.stl"),
    ("sq", "top_use", GEN / "sq-top-use.stl", None),
    ("tilt", "bottom", GEN / "tilt-bottom.stl", KIT / "tilt-bottom.stl"),
    ("tilt", "top", GEN / "tilt-top.stl", KIT / "tilt-top.stl"),
    ("tilt", "top_use", GEN / "tilt-top-use.stl", None),
]


def main() -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    KIT.mkdir(parents=True, exist_ok=True)
    for kind, part, dest, kit in JOBS:
        src = GEN / f"job-{kind}-{part}.scad"
        src.write_text((SQ if kind == "sq" else TILT).format(part=part), encoding="utf-8")
        print("render", kind, part, flush=True)
        r = subprocess.run(
            [str(OSC), "-o", str(dest), "--export-format=binstl", str(src)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
            print("FAIL", dest)
            print(r.stdout[-800:] if r.stdout else "")
            print(r.stderr[-2000:] if r.stderr else "")
            sys.exit(1)
        print(" ", dest.name, dest.stat().st_size, flush=True)
        if kit is not None:
            shutil.copy2(dest, kit)
            print("  copied", kit.name, flush=True)
    print("OK")


if __name__ == "__main__":
    main()
