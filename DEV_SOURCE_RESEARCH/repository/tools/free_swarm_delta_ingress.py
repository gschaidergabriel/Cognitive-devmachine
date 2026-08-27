#!/usr/bin/env python3
"""Deterministic typed ingress for Free-Swarm architecture deltas.

Model output remains noncanonical candidate material. This parser performs
bounded, fail-closed admission before Evidence Forge so malformed/non-ready
proposals can be measured without spending a Forge clone/evaluation cycle.
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
HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@(?: .*)?$"
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
                    return json.loads(text[start:i + 1])
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


def _header_path(raw: str) -> str | None:
    value = raw.split("\t", 1)[0]
    if value == "/dev/null":
        return value
    if not value.startswith(("a/", "b/")):
        return None
    value = value[2:]
    return value if _safe_target(value) else None


def _diff_header_targets(patch: str) -> tuple[bool, set[str]]:
    """Validate unified-diff structure and return referenced repository paths.

    This is intentionally a syntax gate, not an applicability proof. Forge still
    owns exact-source ``git apply`` plus tests/benchmarks.
    """
    if not patch.strip() or len(patch.encode("utf-8", errors="replace")) > MAX_PATCH_BYTES:
        return False, set()

    lines = patch.splitlines()
    refs: set[str] = set()
    i = 0
    files = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].startswith("--- "):
            if lines[i].startswith("@@"):
                return False, set()
            i += 1
        if i >= len(lines):
            break

        old_path = _header_path(lines[i][4:])
        if old_path is None or i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
            return False, set()
        new_path = _header_path(lines[i + 1][4:])
        if new_path is None or (old_path == "/dev/null" and new_path == "/dev/null"):
            return False, set()

        for p in (old_path, new_path):
            if p != "/dev/null":
                refs.add(p)
        files += 1
        i += 2
        file_hunks = 0

        while i < len(lines) and not lines[i].startswith("--- "):
            if not lines[i].startswith("@@"):
                if file_hunks == 0 and (
                    not lines[i]
                    or lines[i].startswith(
                        ("diff --git ", "index ", "new file mode ", "deleted file mode ",
                         "old mode ", "new mode ", "similarity index ", "rename from ", "rename to ")
                    )
                ):
                    i += 1
                    continue
                return False, set()

            match = HUNK_RE.match(lines[i])
            if match is None:
                return False, set()
            old_expected = int(match.group("old_count") or "1")
            new_expected = int(match.group("new_count") or "1")
            old_seen = 0
            new_seen = 0
            file_hunks += 1
            i += 1

            while i < len(lines) and not lines[i].startswith(("@@ ", "--- ")):
                line = lines[i]
                if line.startswith("\\ No newline at end of file"):
                    i += 1
                    continue
                if not line or line[0] not in " +-":
                    return False, set()
                if line[0] in " -":
                    old_seen += 1
                if line[0] in " +":
                    new_seen += 1
                i += 1

            if old_seen != old_expected or new_seen != new_expected:
                return False, set()

        if file_hunks == 0:
            return False, set()

    return files > 0, refs


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
    targets = obj.get("target_files")
    tests = obj.get("test_commands")

    if not isinstance(patch, str):
        reasons.append("INVALID_PATCH")
        patch_ok, patch_targets = False, set()
    elif patch.strip():
        patch_ok, patch_targets = _diff_header_targets(patch)
        if not patch_ok:
            reasons.append("INVALID_PATCH")
    else:
        patch_ok, patch_targets = True, set()

    if not isinstance(targets, list) or len(targets) > MAX_TARGETS or any(
        not isinstance(x, str) or not _safe_target(x) for x in (targets or [])
    ):
        reasons.append("INVALID_TARGET_FILES")
        normalized_targets: set[str] = set()
    else:
        normalized_targets = {str(x) for x in targets}

    if patch_targets and normalized_targets and patch_targets != normalized_targets:
        reasons.append("PATCH_TARGET_MISMATCH")

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
        elif not patch_ok:
            reasons.append("READY_PATCH_NOT_UNIFIED_DIFF")
        if not isinstance(targets, list) or not targets:
            reasons.append("READY_MISSING_TARGETS")
        if not isinstance(tests, list) or not tests:
            reasons.append("READY_MISSING_TESTS")

    return not reasons, reasons


def parse_worker_delta(
    text: str,
    *,
    repo_head_at_prompt: str | None = None,
    worker_sha256: str | None = None,
) -> dict[str, Any]:
    if DELTA_MARKER not in text:
        return {
            "schema": SCHEMA, "status": "MISSING", "valid": False,
            "ready_for_forge": False, "reasons": ["DELTA_MARKER_MISSING"],
        }
    obj = _balanced_after(text, DELTA_MARKER, "{", "}")
    if obj is None:
        return {
            "schema": SCHEMA, "status": "MALFORMED", "valid": False,
            "ready_for_forge": False, "reasons": ["DELTA_JSON_MALFORMED"],
        }

    valid, reasons = validate_delta(obj)
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    out = {
        "schema": SCHEMA,
        "status": (
            "VALID_READY" if valid and obj.get("ready_for_forge") is True
            else ("VALID_NOT_READY" if valid else "SCHEMA_INVALID")
        ),
        "valid": valid,
        "ready_for_forge": bool(valid and obj.get("ready_for_forge") is True),
        "reasons": reasons,
        "proposal": obj if valid else None,
        "proposal_json": canonical if valid else None,
        "proposal_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest() if valid else None,
    }
    if repo_head_at_prompt:
        out["repo_head_at_prompt"] = str(repo_head_at_prompt).strip().lower()
    if worker_sha256:
        out["worker_sha256"] = str(worker_sha256).strip().lower()
    return out


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
