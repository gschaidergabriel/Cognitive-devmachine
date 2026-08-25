#!/usr/bin/env python3
"""Typed/exact architecture hardening over Trigger-2 Qwen3.5 gate v4.

Gate v4 binds receipt blobs and recovers nested ``config.text_config`` fields, but its
integer predicate uses ``isinstance(value, int)`` and only requires ``value > 0``.
Therefore Python ``True`` is accepted as an integer and an unexpected positive model
shape can remain source-valid. The three measured arms are pinned immutable members of
one Qwen3.5-0.8B family, so their normalized architecture is an exact source-integrity
contract, not merely a positive-number schema.

This successor changes source integrity only. Loader-probe v1 still does not attest the
exact consumed weight set or model-visible input identity. Selection remains closed and
no runtime/J-Space/HCU/EntityOS/training credit is minted.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from tools import trigger2_qwen35_checkpoint_candidates_gate_v4 as v4

GATE_SCHEMA = "CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v5"
EXPECTED_ARCHITECTURE = {
    "model_type": "qwen3_5_text",
    "num_hidden_layers": 24,
    "hidden_size": 1024,
    "num_attention_heads": 8,
    "num_key_value_heads": 2,
    "vocab_size": 248320,
    "max_position_embeddings": 262144,
}


def architecture_typed_exact(arch: Any) -> bool:
    if type(arch) is not dict:
        return False
    if arch.get("model_type") != EXPECTED_ARCHITECTURE["model_type"]:
        return False
    for field in v4.ARCH_FIELDS:
        value = arch.get(field)
        # bool is an int subclass; exact type is required for numeric architecture fields.
        if type(value) is not int:
            return False
        if value != EXPECTED_ARCHITECTURE[field]:
            return False
    return True


def adjudicate(registry: Any) -> dict[str, Any]:
    result = copy.deepcopy(v4.adjudicate(registry))
    failures = set(result.get("failures", []))

    normalized = result.get("normalized_measured_candidates")
    if not isinstance(normalized, list):
        failures.add("NORMALIZED_MEASURED_CANDIDATES_REQUIRED")
        normalized = []

    by_id = {
        row.get("candidate_id"): row
        for row in normalized
        if isinstance(row, dict) and isinstance(row.get("candidate_id"), str)
    }
    for cid in v4.REQUIRED_MEASURED:
        row = by_id.get(cid)
        if not isinstance(row, dict) or not architecture_typed_exact(row.get("architecture")):
            failures.add("BOUND_ARCHITECTURE_TYPED_EXACT_MISMATCH:" + cid)

    failures = sorted(failures)
    result["schema"] = GATE_SCHEMA
    result["failures"] = failures
    result["pass"] = not failures
    result["registry_valid"] = not failures
    result["selection_ready"] = False
    result["checkpoint_winner"] = None
    result["credit"] = {
        "checkpoint_selection": 0,
        "jspace": 0,
        "training": 0,
        "whole_hcu_runtime": 0,
        "whole_entityos_runtime": 0,
    }
    result["bound_architecture_contract"] = EXPECTED_ARCHITECTURE
    result["evidence_boundary"] = (
        "PASS adds exact typed Qwen3.5-0.8B architecture integrity to gate-v4 receipt "
        "binding. Loader-probe v1 remains load-smoke evidence only: exact consumed bytes, "
        "resolved template/render/input_ids/attention/generation identity, matched-pilot "
        "execution, winner selection, J-Space and training credit remain unresolved/zero."
    )
    return result


def self_test(registry: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    current = adjudicate(registry)
    checks["CURRENT_REGISTRY_PASSES_TYPED_EXACT_GATE"] = current["pass"]

    expected = copy.deepcopy(EXPECTED_ARCHITECTURE)
    checks["EXPECTED_ARCHITECTURE_ACCEPTED"] = architecture_typed_exact(expected)

    m = copy.deepcopy(expected)
    m["hidden_size"] = True
    checks["BOOL_INT_ALIAS_REJECTED"] = not architecture_typed_exact(m)

    m = copy.deepcopy(expected)
    m["hidden_size"] = 2048
    checks["UNEXPECTED_POSITIVE_SHAPE_REJECTED"] = not architecture_typed_exact(m)

    m = copy.deepcopy(expected)
    m["model_type"] = "qwen3_5"
    checks["WRONG_TEXT_MODEL_TYPE_REJECTED"] = not architecture_typed_exact(m)

    stale = copy.deepcopy(registry)
    stale["schema"] = "STALE"
    checks["V4_SOURCE_FAILURE_PROPAGATES"] = not adjudicate(stale)["pass"]

    return {"pass": all(checks.values()), "checks": checks}


def main() -> int:
    registry = json.loads(v4.REGISTRY_PATH.read_text(encoding="utf-8"))
    result = adjudicate(registry)
    result["self_test"] = self_test(registry)
    result["pass"] = bool(result["pass"] and result["self_test"]["pass"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
