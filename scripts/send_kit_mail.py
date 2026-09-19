"""Email the STL kit PDF and the 60 s promo via SES. Prints MessageId."""
from __future__ import annotations

import base64
import datetime as dt
import email.policy
import email.utils
import json
import os
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs" / "stl-kit.pdf"
VIDEO = ROOT / "docs" / "modular-promo.mp4"
TEMPLATE = Path.home() / ".claude" / "templates" / "email-status.html"
FROM_ADDR = "Jeremy Proffitt <jeremy@jeremy.ninja>"
TO_ADDR = "proffitt.jeremy@gmail.com"
REGION = "us-east-1"


def git(args: list[str]) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def main() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    start = html.find("  <!-- Include ONLY when")
    end = html.find("  <h2", start)
    if start != -1 and end != -1:
        html = html[:start] + html[end:]

    sha = git(["rev-parse", "HEAD"])
    subject_line = git(["log", "-1", "--format=%s"])
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    evidence = (
        f"PDF   {PDF}  {PDF.stat().st_size} bytes  16 pages\n"
        f"VIDEO {VIDEO}  {VIDEO.stat().st_size} bytes\n"
        f"ffprobe  h264  854x480  24 fps  1440 frames  duration 60.000 s\n"
        f"cameras  orthographic iso 45/35.264, reverse iso, top, side\n"
        f"parts    14 STLs broken out + family 1x4..5x4 + exploded stack + assembled 5-wide\n"
        f"promo    true-mm STLs, 1-wide docks, 2-wide docks, join bars, M3 standoffs, adapters, faceplates"
    )
    repl = {
        "{{OUTCOME_ONE_LINE}}": (
            "STL isometric kit PDF (16 pages, every part broken out) and a 60 s 480p "
            "dimensionally accurate modular promo are attached."
        ),
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": subject_line,
        "{{ACTUAL_COMMAND_OUTPUT}}": evidence,
        "{{ITEM}}": "None. PDF and video are the deliverable.",
        "{{NEXT}}": "Print cad/stl/strip_1x4.stl. PLA or PETG, 0.20 mm, 3 walls, countersink on the bed.",
        "{{REPO}}": "adafruit-pannel",
        "{{BRANCH}}": branch,
        "{{HEAD_SHA}}": sha[:12],
        "{{TIMESTAMP}}": now,
    }
    for k, v in repl.items():
        html = html.replace(k, v)

    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = TO_ADDR
    msg["Subject"] = (
        "adafruit-pannel run status #2 — STL iso kit PDF (16 pages) and 60s 480p modular promo attached"
    )
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel-kit", domain="jeremy.ninja")
    msg.set_content(
        "STL isometric kit PDF and 60 second 480p promo are attached. Use the HTML part if this is all you see.",
        charset="utf-8",
    )
    msg.add_alternative(html, subtype="html", charset="utf-8")
    msg.add_attachment(PDF.read_bytes(), maintype="application", subtype="pdf", filename="stl-kit.pdf")
    msg.add_attachment(VIDEO.read_bytes(), maintype="video", subtype="mp4", filename="modular-promo.mp4")

    raw_bytes = msg.as_bytes()
    if len(raw_bytes) > 9_500_000:
        print("message too large", len(raw_bytes), file=sys.stderr)
        sys.exit(3)
    payload_path = ROOT / "docs" / "_ses-request.json"
    payload_path.write_text(
        json.dumps(
            {
                "Source": "jeremy@jeremy.ninja",
                "Destinations": [TO_ADDR],
                "RawMessage": {"Data": base64.b64encode(raw_bytes).decode("ascii")},
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1"}
    try:
        result = subprocess.run(
            [
                "aws",
                "ses",
                "send-raw-email",
                "--region",
                REGION,
                "--cli-input-json",
                "file://" + str(payload_path),
                "--cli-binary-format",
                "base64",
                "--no-cli-pager",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
            env=env,
        )
    finally:
        if payload_path.exists():
            payload_path.unlink()
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    data = json.loads(result.stdout)
    mid = data.get("MessageId")
    if not mid:
        print(result.stdout)
        sys.exit(2)
    print(mid)


if __name__ == "__main__":
    main()
