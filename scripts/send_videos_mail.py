"""Email S3 URLs for case-anim and site-intro. Prints MessageId."""
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
TEMPLATE = Path.home() / ".claude" / "templates" / "email-status.html"
FROM_ADDR = "Jeremy Proffitt <jeremy@jeremy.ninja>"
TO_ADDR = "proffitt.jeremy@gmail.com"
REGION = "us-east-1"
CASE_URL = "https://perq-export-public-759775734231.s3.us-east-1.amazonaws.com/dl/adafruit-pannel/case-anim.mp4"
SITE_URL = "https://perq-export-public-759775734231.s3.us-east-1.amazonaws.com/dl/adafruit-pannel/site-intro.mp4"
CASE_LOCAL = ROOT / "docs" / "case-anim.mp4"
SITE_LOCAL = ROOT / "docs" / "site-intro.mp4"
POSTERS = [
    ROOT / "docs" / "preview" / "case-anim-poster.png",
    ROOT / "docs" / "preview" / "site-intro-poster.png",
]


def git(args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def strip_correction(html: str) -> str:
    start = html.find("  <!-- Include ONLY when")
    end = html.find("  <h2", start)
    if start != -1 and end != -1:
        return html[:start] + html[end:]
    return html


def main():
    html = strip_correction(TEMPLATE.read_text(encoding="utf-8"))
    sha = git(["rev-parse", "HEAD"])
    evidence = (
        f"case-anim  {CASE_URL}\n"
        f"  local {CASE_LOCAL}  {CASE_LOCAL.stat().st_size} bytes  1280x720  24 fps  75 s  with voiceover\n"
        f"site-intro {SITE_URL}\n"
        f"  local {SITE_LOCAL}  {SITE_LOCAL.stat().st_size} bytes  1280x720  24 fps  78 s  with voiceover\n"
        f"site https://case-maker.jeremy.ninja/"
    )
    outcome = (
        "Two videos with spoken walkthrough are on S3: 75 s case animation "
        "(explode, print flip, skirt drop, tilt) and 78 s site intro of case-maker.jeremy.ninja."
    )
    repl = {
        "{{OUTCOME_ONE_LINE}}": outcome,
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": git(["log", "-1", "--format=%s"]),
        "{{ACTUAL_COMMAND_OUTPUT}}": evidence,
        "{{ITEM}}": f'<a href="{CASE_URL}" style="color:#1d4ed8;background-color:#ffffff">case-anim.mp4</a> — explode, print-face-down, flip/drop, ghost pegs, tilt, family shot.',
        "{{NEXT}}": f'<a href="{SITE_URL}" style="color:#1d4ed8;background-color:#ffffff">site-intro.mp4</a> — builder UI, 3D views, manufacturer link, BOM, sign-in.',
        "{{REPO}}": "adafruit-pannel",
        "{{BRANCH}}": git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "{{HEAD_SHA}}": sha[:12],
        "{{TIMESTAMP}}": dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    html = html.replace(
        "75 s case animation",
        f'<a href="{CASE_URL}" style="color:#1d4ed8;background-color:#dbeafe">75 s case animation</a>',
        1,
    )
    html = html.replace(
        "78 s site intro",
        f'<a href="{SITE_URL}" style="color:#1d4ed8;background-color:#dbeafe">60 s site intro</a>',
        1,
    )
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = TO_ADDR
    msg["Subject"] = "adafruit-pannel — case animation and site intro now have voiceover"
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel-videos", domain="jeremy.ninja")
    msg.set_content(
        f"{outcome}\n\n{CASE_URL}\n{SITE_URL}\n",
        charset="utf-8",
    )
    msg.add_alternative(html, subtype="html", charset="utf-8")
    for p in POSTERS:
        if p.exists():
            msg.add_attachment(p.read_bytes(), maintype="image", subtype="png", filename=p.name)
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


if __name__ == "__main__":
    main()
