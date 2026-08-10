#!/usr/bin/env python3
"""Parse GNU /usr/bin/time -v output into stable Clay resource metadata.

GNU time indents its human-readable labels. Receipt collectors must therefore tolerate
leading horizontal whitespace rather than treating those measurements as UNKNOWN.
Unknown or missing fields remain literal UNKNOWN; this tool never converts absence to zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
FIELDS: dict[str, tuple[str, str]] = {
    "user_seconds": ("User time (seconds)", "float"),
    "system_seconds": ("System time (seconds)", "float"),
    "max_rss_kb": ("Maximum resident set size (kbytes)", "int"),
    "major_page_faults": ("Major (requiring I/O) page faults", "int"),
    "minor_page_faults": ("Minor (reclaiming a frame) page faults", "int"),
    "voluntary_context_switches": ("Voluntary context switches", "int"),
    "involuntary_context_switches": ("Involuntary context switches", "int"),
}


def _grab(text: str, label: str) -> str | None:
    # GNU time -v normally prefixes labels with a tab. Keep this deliberately narrow:
    # horizontal/vertical leading whitespace is trivia, the exact label remains fixed.
    match = re.search(rf"^\s*{re.escape(label)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _typed(raw: str | None, kind: str) -> int | float | str:
    if raw is None or raw == "":
        return "UNKNOWN"
    try:
        if kind == "int":
            return int(raw)
        if kind == "float":
            return float(raw)
    except ValueError:
        return "UNKNOWN"
    return raw


def parse_time_v(text: str) -> dict[str, int | float | str]:
    return {key: _typed(_grab(text, label), kind) for key, (label, kind) in FIELDS.items()}


def build_receipt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    metrics = parse_time_v(text)
    known = sum(value != "UNKNOWN" for value in metrics.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "source": str(path),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "parser": "GNU_TIME_V_WHITESPACE_SAFE_V1",
        "metrics": metrics,
        "known_metric_count": known,
        "expected_metric_count": len(FIELDS),
        "complete_expected_subset": known == len(FIELDS),
        "unknown_policy": "PRESERVE_LITERAL_UNKNOWN_NEVER_ZERO_FILL",
    }


def self_test() -> dict[str, Any]:
    fixture = """\tCommand being timed: \"true\"\n\tUser time (seconds): 0.01\n\tSystem time (seconds): 0.02\n\tMaximum resident set size (kbytes): 1234\n\tMajor (requiring I/O) page faults: 1\n\tMinor (reclaiming a frame) page faults: 22\n\tVoluntary context switches: 3\n\tInvoluntary context switches: 4\n"""
    expected = {
        "user_seconds": 0.01,
        "system_seconds": 0.02,
        "max_rss_kb": 1234,
        "major_page_faults": 1,
        "minor_page_faults": 22,
        "voluntary_context_switches": 3,
        "involuntary_context_switches": 4,
    }
    observed = parse_time_v(fixture)
    missing = parse_time_v("\tUser time (seconds): 0.50\n")
    passed = observed == expected and missing["user_seconds"] == 0.5 and all(
        missing[key] == "UNKNOWN" for key in FIELDS if key != "user_seconds"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": "GNU_TIME_V_WHITESPACE_SAFE_PARSER_SELF_TEST",
        "observed": observed,
        "expected": expected,
        "unknown_preservation": missing,
        "pass": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        payload = self_test()
    else:
        if args.input is None:
            parser.error("--input is required unless --self-test is used")
        payload = build_receipt(args.input)

    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if payload.get("pass", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
