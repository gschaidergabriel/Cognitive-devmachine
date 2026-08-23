#!/usr/bin/env python3
"""Static fail-closed guard for the missing UCF causal turn lookup boundary.

It does not certify runtime behavior. It prevents source convergence credit when the
canonical Cognitive Fabric call must invent causal_turn_id/task_text from prompt,
profile, packet hash, generation, clock, randomness, or literals.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

PHASE_NAMES = ("pipeline_cognitive_fabric_prepare", "pipeline_cognitive_fabric_admit")


def _value_for(source: str, map_name: str, key: str) -> str | None:
    pattern = re.compile(
        rf'map_set\(\s*{re.escape(map_name)}\s*,\s*"{re.escape(key)}"\s*,\s*([^\)\n]+)\)'
    )
    match = pattern.search(source)
    return match.group(1).strip() if match else None


def evaluate(source: str) -> dict[str, Any]:
    phase_match = None
    for phase_name in PHASE_NAMES:
        match = re.search(
            rf'phase\(\s*"{phase_name}"\s*,\s*entity_db\s*,\s*source_db\s*,\s*profile\s*,\s*previous\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)',
            source,
        )
        if match:
            phase_match = (phase_name, match.group(1))
            break

    if phase_match is None:
        return {
            "schema": "UCF_TURN_REF_SOURCE_GUARD/v1",
            "pass": False,
            "errors": ["COGNITIVE_FABRIC_PHASE_NOT_FOUND"],
        }

    phase_name, map_name = phase_match
    causal = _value_for(source, map_name, "causal_turn_id")
    task = _value_for(source, map_name, "task_text")
    turn_ref = _value_for(source, map_name, "turn_ref")

    unsafe_causal_patterns = (
        r"compiled\.packet_hash",
        r"compiled\.canonical_state_hash",
        r"previous\.generation",
        r"profile\.",
        r"prompt\.",
        r"time|clock|now|random|rand|uuid|token_hex",
        r'^"[^\"]*"$',
    )
    unsafe_task_patterns = (
        r"prompt\.(?:system|user)",
        r"profile\.",
        r"compiled\.",
        r"time|clock|now|random|rand|uuid|token_hex",
        r'^"[^\"]*"$',
    )

    errors: list[str] = []
    if turn_ref is None and causal is None:
        errors.append("MISSING_CAUSAL_TURN_LOOKUP_KEY")
    if turn_ref is None and task is None:
        errors.append("MISSING_TASK_LOOKUP_KEY")
    if causal is not None and any(re.search(p, causal, re.I) for p in unsafe_causal_patterns):
        errors.append("UNSAFE_CAUSAL_TURN_DERIVATION")
    if task is not None and any(re.search(p, task, re.I) for p in unsafe_task_patterns):
        errors.append("UNSAFE_TASK_DERIVATION")

    return {
        "schema": "UCF_TURN_REF_SOURCE_GUARD/v1",
        "phase": phase_name,
        "data_map": map_name,
        "turn_ref_expression": turn_ref,
        "causal_turn_expression": causal,
        "task_text_expression": task,
        "errors": sorted(set(errors)),
        "pass": not errors,
        "policy": "TURN_REF is lookup-only; MiniUnifiedDB resolver is authority. No causal/task identity may be invented from prompt/profile/hash/time/random/literals.",
    }


def main() -> int:
    source = sys.stdin.read()
    report = evaluate(source)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
