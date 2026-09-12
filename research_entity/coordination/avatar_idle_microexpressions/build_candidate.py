#!/usr/bin/env python3
"""Build a fail-closed buehne.html candidate with silent idle microexpressions.

This tool does NOT touch the production avatar. It transforms an exact captured
live source into a candidate file and syntax-checks every inline script with Node.
Production deployment is intentionally a separate, host-admitted step.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import subprocess
import tempfile

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
VERSION_MARKER = 'version:"2026-09-12/state-hazard-v1"'

MOUTH_FUNCTION_NEEDLE = '''function mundAnimation(text){
  const grobeSilben = Math.max(3, Math.round((text || "").length / 2.6));
  const dauerMs = Math.min(9000, grobeSilben * 220);
'''
MOUTH_FUNCTION_REPLACEMENT = MOUTH_FUNCTION_NEEDLE + '''  // Idle-Mimik besitzt den Mund nie waehrend Sprache: harte Arbitration.
  mundSprechBis = Math.max(mundSprechBis, Date.now() + dauerMs + 650);
  mikroMimikAbbrechen("sprache", false);
  mikroMimikPlanen(dauerMs + 900 + Math.random()*1300);
'''

CONTROLLER_INSERT_MARKER = '// Beim ersten Durchlauf steht cursor auf ""'
START_NEEDLE = 'chatHolen(); statusHolen();'
START_REPLACEMENT = START_NEEDLE + '\nmikroMimikStarten();'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, needle: str, replacement: str, label: str) -> str:
    count = text.count(needle)
    if count != 1:
        raise SystemExit(f"FAIL_CLOSED {label}: expected exactly 1 marker, found {count}")
    return text.replace(needle, replacement, 1)


def extract_and_check_inline_js(html: str) -> None:
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
    if not scripts:
        raise SystemExit("FAIL_CLOSED JS_CHECK: no inline <script> blocks found")
    with tempfile.TemporaryDirectory(prefix="frank-idlemimik-") as td:
        p = pathlib.Path(td) / "inline.js"
        p.write_text("\n\n".join(scripts), encoding="utf-8")
        proc = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
        if proc.returncode:
            raise SystemExit("FAIL_CLOSED JS_CHECK:\n" + proc.stdout + proc.stderr)


def build(live_path: pathlib.Path, controller_path: pathlib.Path, out_path: pathlib.Path) -> None:
    raw = live_path.read_bytes()
    got_sha = sha256_bytes(raw)
    if got_sha != EXPECTED_LIVE_SHA256:
        raise SystemExit(f"FAIL_CLOSED LIVE_SHA expected={EXPECTED_LIVE_SHA256} got={got_sha}")
    html = raw.decode("utf-8")
    controller = controller_path.read_text(encoding="utf-8").strip()
    if VERSION_MARKER not in controller:
        raise SystemExit("FAIL_CLOSED CONTROLLER_VERSION marker missing")
    if VERSION_MARKER in html:
        raise SystemExit("FAIL_CLOSED ALREADY_PATCHED")

    html = replace_once(html, MOUTH_FUNCTION_NEEDLE, MOUTH_FUNCTION_REPLACEMENT, "MOUTH_FUNCTION")
    insert = (
        "\n// ⭐⭐⭐ 2026-09-12 STATE-DRIVEN IDLE-MIKRO-MIMIK\n"
        "// Aperiodisch; state-abgeleitet; Sprache/Sonderausdruck/FPS haben Vorrang.\n"
        + controller + "\n\n"
        + CONTROLLER_INSERT_MARKER
    )
    html = replace_once(html, CONTROLLER_INSERT_MARKER, insert, "CONTROLLER_INSERT")
    html = replace_once(html, START_NEEDLE, START_REPLACEMENT, "START_HOOK")

    extract_and_check_inline_js(html)
    out_path.write_text(html, encoding="utf-8")
    print("CANDIDATE_BUILD_PASS")
    print("INPUT_SHA256=" + got_sha)
    print("OUTPUT_SHA256=" + sha256_bytes(out_path.read_bytes()))
    print("OUTPUT=" + str(out_path))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-html", required=True, type=pathlib.Path)
    ap.add_argument("--controller", default=pathlib.Path(__file__).with_name("idle_microexpressions.js"), type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()
    build(args.live_html, args.controller, args.out)


if __name__ == "__main__":
    main()
