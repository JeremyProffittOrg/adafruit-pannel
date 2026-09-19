"""Email application shortcuts as a second message. Prints MessageId."""
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
FILES = [
    ROOT / "docs" / "panel-shortcuts.zip",
    ROOT / "shortcuts" / "README.txt",
]


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
    evidence = "\n".join(f"{p.name:28} {p.stat().st_size} bytes" for p in FILES)
    evidence += (
        "\n\nstart-panelweb.cmd  ->  builds if needed, starts :8787, opens the browser\n"
        "Panel-case-builder.url  ->  http://127.0.0.1:8787/\n"
        "open-case-in-bambu.cmd  ->  sliders-quads-case.3mf in Bambu Studio"
    )
    repl = {
        "{{OUTCOME_ONE_LINE}}": (
            "Application shortcuts attached: start the Go case builder, open the site, open the kit in Bambu."
        ),
        "{{SHA}}": sha[:12],
        "{{COMMIT_SUBJECT}}": git(["log", "-1", "--format=%s"]),
        "{{ACTUAL_COMMAND_OUTPUT}}": evidence,
        "{{ITEM}}": "None.",
        "{{NEXT}}": "Double-click start-panelweb.cmd then use the site to emit STLs.",
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
    msg["Subject"] = "adafruit-pannel run status #4 — application shortcuts attached"
    msg["Date"] = email.utils.format_datetime(dt.datetime.now().astimezone())
    msg["Message-ID"] = email.utils.make_msgid(idstring="adafruit-pannel-shortcuts", domain="jeremy.ninja")
    msg.set_content("Application shortcuts are attached: start-panelweb.cmd, URL, Bambu opener, README.", charset="utf-8")
    msg.add_alternative(html, subtype="html", charset="utf-8")
    msg.add_attachment(
        (ROOT / "docs" / "panel-shortcuts.zip").read_bytes(),
        maintype="application", subtype="zip", filename="panel-shortcuts.zip",
    )
    msg.add_attachment(
        (ROOT / "shortcuts" / "README.txt").read_bytes(),
        maintype="text", subtype="plain", filename="shortcuts-readme.txt",
    )
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
