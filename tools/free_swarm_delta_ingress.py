#!/usr/bin/env python3
"""Deterministic candidate-admission parser for Free-Swarm architecture deltas.

Model text stays noncanonical. This module only turns an explicitly marked JSON
object into a bounded, schema-checked candidate record. It deliberately mirrors
the existing Evidence Forge path/command fences so ``VALID_READY`` means the
proposal can actually cross that next boundary without semantic relabeling.
Malformed or incomplete proposals remain rejected with a machine-readable reason;
nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

DELTA_MARKER = "ARCHITECTURE_DELTA_JSON="
QUESTIONS_MARKER = "OPEN_RESEARCH_QUESTIONS_JSON="
SCHEMA = "CLAY_ARCHITECTURE_DELTA_INGRESS/v1"
MAX_PATCH_BYTES = 250_000
MAX_TEXT = 16_000
MAX_TARGETS = 32
MAX_COMMANDS = 8
EXPECTED_DIRECTIONS = {"higher", "lower", "boolean"}
FORBIDDEN_COMMAND_FRAGMENTS = (
    "sudo ", "systemctl ", "shutdown", "reboot", "mkfs", "dd if=",
    "> /dev/", "rm -rf /", "podman ", "docker ",
)


def _balanced_after(text: str, marker: str, opener: str, closer: str) -> Any | None:
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.find(opener, pos + len(marker))
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _safe_target(value: str) -> bool:
    if not value or len(value) > 500 or any(ord(ch) < 32 for ch in value):
        return False
    p = Path(value)
    return not p.is_absolute() and ".." not in p.parts and not str(p).startswith(".git")


def _safe_command(value: str) -> bool:
    low = value.lower()
    return bool(value.strip()) and len(value) < 2000 and not any(
        fragment in low for fragment in FORBIDDEN_COMMAND_FRAGMENTS
    )


def _patch_paths_safe(patch: str) -> bool:
    if len(patch.encode("utf-8", errors="replace")) > MAX_PATCH_BYTES:
        return False
    for line in patch.splitlines():
        if not line.startswith(("+++ ", "--- ")):
            continue
        value = line[4:].split("\t", 1)[0]
        if value == "/dev/null":
            continue
        value = re.sub(r"^[ab]/", "", value)
        if not _safe_target(value):
            return False
    return True


def _bounded_string(obj: dict[str, Any], key: str, *, required: bool = True) -> str | None:
    value = obj.get(key)
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if required and not value:
        return None
    if len(value) > MAX_TEXT:
        return None
    return value


def validate_delta(obj: Any) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not isinstance(obj, dict):
        return False, ["DELTA_NOT_OBJECT"]

    for key in ("delta_id", "hypothesis", "mechanism", "metric", "falsifier", "risk"):
        if _bounded_string(obj, key) is None:
            reasons.append(f"INVALID_{key.upper()}")

    patch = obj.get("patch_unified_diff")
    if not isinstance(patch, str) or not _patch_paths_safe(patch):
        reasons.append("INVALID_PATCH")

    targets = obj.get("target_files")
    if not isinstance(targets, list) or len(targets) > MAX_TARGETS or any(
        not isinstance(x, str) or not _safe_target(x) for x in (targets or [])
    ):
        reasons.append("INVALID_TARGET_FILES")

    tests = obj.get("test_commands")
    if not isinstance(tests, list) or len(tests) > MAX_COMMANDS or any(
        not isinstance(x, str) or not _safe_command(x) for x in (tests or [])
    ):
        reasons.append("INVALID_TEST_COMMANDS")

    negatives = obj.get("negative_test_commands", [])
    if not isinstance(negatives, list) or len(negatives) > MAX_COMMANDS or any(
        not isinstance(x, str) or not _safe_command(x) for x in (negatives or [])
    ):
        reasons.append("INVALID_NEGATIVE_TEST_COMMANDS")

    bench = obj.get("benchmark_command", "")
    if not isinstance(bench, str) or (bench and not _safe_command(bench)):
        reasons.append("INVALID_BENCHMARK_COMMAND")

    if obj.get("expected_direction") not in EXPECTED_DIRECTIONS:
        reasons.append("INVALID_EXPECTED_DIRECTION")
    if not isinstance(obj.get("baseline_needed"), bool):
        reasons.append("INVALID_BASELINE_NEEDED")
    if not isinstance(obj.get("ready_for_forge"), bool):
        reasons.append("INVALID_READY_FOR_FORGE")

    if obj.get("ready_for_forge") is True:
        if not isinstance(patch, str) or not patch.strip():
            reasons.append("READY_MISSING_PATCH")
        if not isinstance(targets, list) or not targets:
            reasons.append("READY_MISSING_TARGETS")
        if not isinstance(tests, list) or not tests:
            reasons.append("READY_MISSING_TESTS")

    return not reasons, reasons


def parse_worker_delta(text: str) -> dict[str, Any]:
    if DELTA_MARKER not in text:
        return {"schema": SCHEMA, "status": "MISSING", "valid": False, "ready_for_forge": False, "reasons": ["DELTA_MARKER_MISSING"]}
    obj = _balanced_after(text, DELTA_MARKER, "{", "}")
    if obj is None:
        return {"schema": SCHEMA, "status": "MALFORMED", "valid": False, "ready_for_forge": False, "reasons": ["DELTA_JSON_MALFORMED"]}
    valid, reasons = validate_delta(obj)
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "schema": SCHEMA,
        "status": "VALID_READY" if valid and obj.get("ready_for_forge") is True else ("VALID_NOT_READY" if valid else "SCHEMA_INVALID"),
        "valid": valid,
        "ready_for_forge": bool(valid and obj.get("ready_for_forge") is True),
        "reasons": reasons,
        "proposal": obj if valid else None,
        "proposal_json": canonical if valid else None,
        "proposal_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest() if valid else None,
    }


def parse_questions(text: str) -> list[str]:
    obj = _balanced_after(text, QUESTIONS_MARKER, "[", "]")
    if not isinstance(obj, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in obj[:32]:
        if not isinstance(value, str):
            continue
        value = value.strip()
        if not value or len(value) > 1000 or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
