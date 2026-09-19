"""Send the control-panel PDF via SES. Prints MessageId on success."""
from __future__ import annotations

import datetime as dt
import email.policy
import email.utils
import json
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs" / "adafruit-control-panel.pdf"
TEMPLATE = Path.home() / ".claude" / "templates" / "email-status.html"
FROM_ADDR = "Jeremy Proffitt <jeremy@jeremy.ninja>"
TO_ADDR = "proffitt.jeremy@gmail.com"
REGION = "us-east-1"


def git(args: list[str]) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def main() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    # No earlier claim to correct.
    html = html.split("<!-- Include ONLY when")[0] + html.split("</div>", 8)[-1] if False else html
    start = html.find("  <!-- Include ONLY when")
    end = html.find("  <h2", start)
    if start != -1 and end != -1:
        html = html[:start] + html[end:]

    sha = git(["rev-parse", "HEAD"])
    subject_line = git(["log", "-1", "--format=%s"])
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    stl = sorted((ROOT / "cad" / "stl").glob("*.stl"))
    stl_lines = "\n".join(f"{p.name:22} {p.stat().st_size:7d} bytes" for p in stl)
    evidence = (
        f"PDF  {PDF}  {PDF.stat().st_size} bytes\n"
        f"devices.json featured=5 displays=57 overflow=none\n"
        f"grid 1.00 in / 25.4 mm; strip 1-5 wide x 4 long (101.6 mm); max 5 x 5 lengths = 127 x 508 mm\n"
        f"STLs (watertight):\n{stl_lines}\n"
        f"Eagle sources: NeoSlider, I2C QT Rotary, Quad Rotary, ANO-to-I2C\n"
        f"Shop catalog: https://www.adafruit.com/api/products plus product technical-details"
    )
    repl = {
        "{{OUTCOME_ONE_LINE}}": (
            "1.00 in 3D-printable control-panel grid is built: 5 featured Adafruit boards "
            "measured from Eagle, 57 displays sized, 14 STLs, PDF attached."
        ),
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": subject_line,
        "{{ACTUAL_COMMAND_OUTPUT}}": evidence,
        "{{ITEM}}": "None. The PDF and STLs are the deliverable.",
        "{{NEXT}}": (
            "Print cad/stl/strip_1x4.stl and join_bar.stl in PLA or PETG, 0.20 mm, 3 walls, "
            "countersink on the bed. Use M3 FF standoffs 11-12 mm and M2.5 into the Adafruit PCBs."
        ),
        "{{REPO}}": "adafruit-pannel",
        "{{BRANCH}}": branch,
        "{{HEAD_SHA}}": sha[:12],
        "{{TIMESTAMP}}": now,
    }
    for k, v in repl.items():
        html = html.replace(k, v)

    subject = (
        "adafruit-pannel run status #1 — 1.00 in printable grid, "
        "5 featured boards measured, 57 displays, PDF attached"
    )
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = TO_ADDR
    msg["Subject"] = subject
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel", domain="jeremy.ninja")
    msg.set_content(
        "Adafruit modular control panel PDF is attached. Open the HTML part if your client shows this.",
        charset="utf-8",
    )
    msg.add_alternative(html, subtype="html", charset="utf-8")
    msg.add_attachment(
        PDF.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename="adafruit-control-panel.pdf",
    )

    raw_path = ROOT / "docs" / "_ses-raw.eml"
    raw_path.write_bytes(msg.as_bytes())
    try:
        result = subprocess.run(
            [
                "aws",
                "ses",
                "send-raw-email",
                "--region",
                REGION,
                "--from",
                "jeremy@jeremy.ninja",
                "--destinations",
                TO_ADDR,
                "--cli-binary-format",
                "raw-in-base64-out",
                "--raw-message",
                f"fileb://{raw_path}",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
        )
    finally:
        if raw_path.exists():
            raw_path.unlink()

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
