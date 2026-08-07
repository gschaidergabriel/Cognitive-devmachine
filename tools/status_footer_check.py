#!/usr/bin/env python3
"""Validate the visible RAE status footer structure from stdin or a file."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REQUIRED = [
    "RAE STATUS",
    "Entity:",
    "GitHub:",
    "Canonical:",
    "Actor:",
    "Trigger:",
    "Research write:",
    "LAST PROMPT",
    "Completion:",
    "Done:",
    "Open:",
]


def validate(text: str) -> list[str]:
    errors = []
    stripped = text.rstrip()
    if not stripped.endswith("```"):
        errors.append("footer_not_final_fenced_block")
    tail = stripped[stripped.rfind("```text"):] if "```text" in stripped else ""
    for label in REQUIRED:
        if label not in tail:
            errors.append(f"missing:{label}")
    m = re.search(r"Completion:\s*(\d{1,3})%", tail)
    if not m or not 0 <= int(m.group(1)) <= 100:
        errors.append("invalid_completion")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    args = ap.parse_args()
    text = Path(args.file).read_text(encoding="utf-8") if args.file else __import__("sys").stdin.read()
    errors = validate(text)
    if errors:
        print("INVALID", *errors, sep="\n")
        raise SystemExit(2)
    print("VALID")


if __name__ == "__main__":
    main()
