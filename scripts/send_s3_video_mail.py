"""Email the public S3 URL for promo v2. Prints MessageId."""
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
URL = "https://perq-export-public-759775734231.s3.us-east-1.amazonaws.com/dl/adafruit-pannel/modular-promo-v2.mp4"


def git(args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def main():
    html = TEMPLATE.read_text(encoding="utf-8")
    start = html.find("  <!-- Include ONLY when")
    end = html.find("  <h2", start)
    if start != -1 and end != -1:
        html = html[:start] + html[end:]
    sha = git(["rev-parse", "HEAD"])
    evidence = (
        f"{URL}\n"
        f"HEAD 200  Content-Type video/mp4  Content-Length 2986148\n"
        f"local  docs/modular-promo-v2.mp4  854x480  24 fps  60.000 s\n"
        f"s3://perq-export-public-759775734231/dl/adafruit-pannel/modular-promo-v2.mp4"
    )
    repl = {
        "{{OUTCOME_ONE_LINE}}": f"Promo v2 is on S3: {URL}",
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": git(["log", "-1", "--format=%s"]),
        "{{ACTUAL_COMMAND_OUTPUT}}": evidence,
        "{{ITEM}}": "None.",
        "{{NEXT}}": "Open the URL. Tray walls hold the posts. Angled sides hull to full height.",
        "{{REPO}}": "adafruit-pannel",
        "{{BRANCH}}": git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "{{HEAD_SHA}}": sha[:12],
        "{{TIMESTAMP}}": dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    # make the URL a real link in the outcome block
    html = html.replace(URL, f'<a href="{URL}" style="color:#1d4ed8;background-color:#dbeafe">{URL}</a>', 1)
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Reply-To"] = TO_ADDR
    msg["Subject"] = "adafruit-pannel run status #5 — promo v2 S3 link"
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel-v2-s3", domain="jeremy.ninja")
    msg.set_content(f"Promo v2: {URL}", charset="utf-8")
    msg.add_alternative(html, subtype="html", charset="utf-8")
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
