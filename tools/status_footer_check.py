#!/usr/bin/env python3
"""Validate the visible RAE status footer structure from stdin or a file.

The footer rendering contract is intentionally strict because some ChatGPT clients
mis-render code fences when attributes such as `id=...` are appended or when Unicode
box-drawing layouts are mixed with Markdown. The only accepted opener is exactly
` ```text ` on its own line, and the closing fence must be the final visible content.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND_REGISTRY = ROOT / "research_entity" / "global" / "PROJECT_COMMAND_REGISTRY.json"

REQUIRED = [
    "RAE STATUS",
    "Entity:",
    "GitHub:",
    "Canonical:",
    "Actor:",
    "Trigger:",
    "Research write:",
    "Short commands:",
    "LAST PROMPT",
    "Completion:",
    "Done:",
    "Open:",
]

FORBIDDEN_BOX_CHARS = set("╔═║╚╗╝┌─│└┐┘├┤┬┴┼")
OPEN_FENCE = "```text\n"
CLOSE_FENCE = "\n```"


def _required_commands() -> list[str]:
    data = json.loads(COMMAND_REGISTRY.read_text(encoding="utf-8"))
    commands = data.get("commands") or {}
    if not isinstance(commands, dict) or not commands:
        raise RuntimeError("PROJECT_COMMAND_REGISTRY.json has no commands")
    return list(commands)


def _tail_block(text: str) -> tuple[str, list[str]]:
    errors: list[str] = []
    stripped = text.rstrip()

    if not stripped.endswith("```"):
        errors.append("footer_not_final_fenced_block")
        return "", errors

    start = stripped.rfind("```text\n")
    if start < 0:
        # Catch attribute-bearing variants such as ```text id="..." explicitly.
        if re.search(r"(?m)^```text\S|^```text\s+.+$", stripped):
            errors.append("invalid_fence_opener_attributes")
        else:
            errors.append("missing_exact_text_fence")
        return "", errors

    tail = stripped[start:]
    if not tail.startswith(OPEN_FENCE):
        errors.append("invalid_fence_opener")
    if not tail.endswith(CLOSE_FENCE):
        errors.append("invalid_fence_closer")

    # No additional code fence is allowed inside the final footer block.
    inner = tail[len(OPEN_FENCE):-len(CLOSE_FENCE)]
    if "```" in inner:
        errors.append("nested_fence_in_footer")

    return tail, errors


def validate(text: str) -> list[str]:
    tail, errors = _tail_block(text)
    if not tail:
        return errors

    # The opener must be exactly ```text. Any attribute-bearing opener anywhere in
    # the final block is a rendering bug.
    opener_line = tail.splitlines()[0] if tail.splitlines() else ""
    if opener_line != "```text":
        errors.append("invalid_fence_opener_attributes")

    if any(ch in FORBIDDEN_BOX_CHARS for ch in tail):
        errors.append("forbidden_box_drawing_character")

    for label in REQUIRED:
        if label not in tail:
            errors.append(f"missing:{label}")

    m = re.search(r"Completion:\s*(\d{1,3})%", tail)
    if not m or not 0 <= int(m.group(1)) <= 100:
        errors.append("invalid_completion")

    cmd_match = re.search(r"Short commands:\s*(.+)", tail)
    if cmd_match:
        line = cmd_match.group(1).lower()
        for command in _required_commands():
            if not re.search(rf"(?<![a-z0-9_-]){re.escape(command)}(?![a-z0-9_-])", line):
                errors.append(f"missing_command:{command}")

    return errors


def _self_test() -> list[str]:
    commands = " · ".join(_required_commands())
    good = (
        "answer\n\n```text\n"
        "RAE STATUS\n"
        "Entity: JOINED\n"
        "GitHub: VERIFIED_RW\n"
        "Canonical: r2 · 04234efdb86c\n"
        "Actor: chatgpt-secondary\n"
        "Trigger: none\n"
        "Research write: NO_RESEARCH_DELTA\n"
        f"Short commands: {commands}\n\n"
        "LAST PROMPT\n"
        "Completion: 100%\n"
        "Done: rendering contract test\n"
        "Open: none\n"
        "```"
    )
    bad_attr = good.replace("```text\n", "```text id=\"broken\"\n", 1)
    bad_box = good.replace("RAE STATUS", "╔ RAE STATUS ═╗")
    bad_after = good + "\nvisible trailing prose"

    failures: list[str] = []
    if validate(good):
        failures.append("selftest_good_rejected")
    if "invalid_fence_opener_attributes" not in validate(bad_attr):
        failures.append("selftest_attribute_fence_not_rejected")
    if "forbidden_box_drawing_character" not in validate(bad_box):
        failures.append("selftest_box_chars_not_rejected")
    if "footer_not_final_fenced_block" not in validate(bad_after):
        failures.append("selftest_trailing_prose_not_rejected")
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        failures = _self_test()
        if failures:
            print("SELF_TEST_INVALID", *failures, sep="\n")
            raise SystemExit(2)
        print("SELF_TEST_VALID")
        return

    text = Path(args.file).read_text(encoding="utf-8") if args.file else __import__("sys").stdin.read()
    errors = validate(text)
    if errors:
        print("INVALID", *errors, sep="\n")
        raise SystemExit(2)
    print("VALID")


if __name__ == "__main__":
    main()
