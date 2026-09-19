"""Email the two-piece case parts PDF. Prints MessageId."""
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
PDF = ROOT / "docs" / "case-parts.pdf"
TEMPLATE = Path.home() / ".claude" / "templates" / "email-status.html"
FROM_ADDR = "Jeremy Proffitt <jeremy@jeremy.ninja>"
TO_ADDR = "proffitt.jeremy@gmail.com"
REGION = "us-east-1"


def git(args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def strip_correction(html: str) -> str:
    start = html.find("  <!-- Include ONLY when")
    end = html.find("  <h2", start)
    if start != -1 and end != -1:
        return html[:start] + html[end:]
    return html


def ses_send(msg: EmailMessage) -> str:
    payload_path = ROOT / "docs" / "_ses-request.json"
    payload_path.write_text(
        json.dumps(
            {
                "Source": "jeremy@jeremy.ninja",
                "Destinations": [TO_ADDR],
                "RawMessage": {"Data": base64.b64encode(msg.as_bytes()).decode("ascii")},
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1"}
    try:
        result = subprocess.run(
            [
                "aws", "ses", "send-raw-email",
                "--region", REGION,
                "--cli-input-json", "file://" + str(payload_path),
                "--cli-binary-format", "base64",
                "--no-cli-pager", "--output", "json",
            ],
            capture_output=True, text=True, encoding="utf-8", timeout=90, env=env,
        )
    finally:
        if payload_path.exists():
            payload_path.unlink()
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    mid = json.loads(result.stdout).get("MessageId")
    if not mid:
        print(result.stdout)
        sys.exit(2)
    print(mid)
    return mid


def main():
    html = strip_correction(TEMPLATE.read_text(encoding="utf-8"))
    # keep Correction: previous PDF was the old strip kit
    corr = """
  <div style="border-left:4px solid #b45309;background-color:#fef3c7;color:#0b0f19;padding:12px 16px;border-radius:0 6px 6px 0;margin:22px 0">
    <div style="font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#78350f;background-color:#fef3c7">Correction</div>
    <div style="margin-top:4px;color:#0b0f19;background-color:#fef3c7">{{WHAT_I_SAID_THEN_WHAT_IS_TRUE_AND_HOW_IT_WAS_CAUGHT}}</div>
  </div>
"""
    html = html.replace(
        "  <h2 style=\"font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#1f2937;background-color:#ffffff;border-bottom:2px solid #9ca3af;padding-bottom:5px;margin:22px 0 10px\">Next</h2>",
        corr + "  <h2 style=\"font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#1f2937;background-color:#ffffff;border-bottom:2px solid #9ca3af;padding-bottom:5px;margin:22px 0 10px\">Next</h2>",
    )
    sha = git(["rev-parse", "HEAD"])
    repl = {
        "{{OUTCOME_ONE_LINE}}": (
            "Two-piece case parts PDF is attached: bottom tray and print-flipped top lid "
            "for 3 NeoSliders + 2 quad rotaries, plus the tilted-tray demo."
        ),
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": git(["log", "-1", "--format=%s"]),
        "{{ACTUAL_COMMAND_OUTPUT}}": (
            f"PDF  {PDF}  {PDF.stat().st_size} bytes\n"
            f"bottom.stl  135.0 x 109.6 x 29.6 mm\n"
            f"top.stl     134.6 x 109.2 x 28.0 mm  (already flipped)\n"
            f"3mf         print-kits/sliders-quads-case/sliders-quads-case.3mf"
        ),
        "{{ITEM}}": "Second mail: application shortcuts.",
        "{{WHAT_I_SAID_THEN_WHAT_IS_TRUE_AND_HOW_IT_WAS_CAUGHT}}": (
            "The earlier stl-kit.pdf showed the old strip / adapter / join-bar stack. "
            "That stack is retired. This PDF is the two-piece tray + lid."
        ),
        "{{NEXT}}": "Print top.stl as exported (visible face on the bed). M3 from below into lid posts.",
        "{{REPO}}": "adafruit-pannel",
        "{{BRANCH}}": git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "{{HEAD_SHA}}": sha[:12],
        "{{TIMESTAMP}}": dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = TO_ADDR
    msg["Subject"] = "adafruit-pannel run status #3 — two-piece case parts PDF attached"
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel-case-pdf", domain="jeremy.ninja")
    msg.set_content("Two-piece case parts PDF is attached.", charset="utf-8")
    msg.add_alternative(html, subtype="html", charset="utf-8")
    msg.add_attachment(PDF.read_bytes(), maintype="application", subtype="pdf", filename="case-parts.pdf")
    ses_send(msg)


if __name__ == "__main__":
    main()
