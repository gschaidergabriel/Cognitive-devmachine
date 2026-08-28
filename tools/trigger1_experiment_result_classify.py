#!/usr/bin/env python3
"""Fail-closed classification for a leased Trigger-1 experiment result.

The atomic-lease result schema has only PASS/FAIL/BLOCKED. PASS therefore means the
named Trigger-1 experiment objective reached the current owner-goal promotion gate;
a lower-level mechanism candidate is preserved separately but cannot be relabeled as
full experiment success.
"""
from __future__ import annotations

from typing import Any

PROMOTION_GATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4"


def classify(result: dict[str, Any] | None, gate: dict[str, Any] | None, rc: int | None) -> str:
    result = result if isinstance(result, dict) else {}
    gate = gate if isinstance(gate, dict) else {}
    status = str(result.get("status") or "")

    if not result or status.startswith("BLOCKED") or rc is None:
        return "BLOCKED"
    if rc != 0:
        return "FAIL"
    if status != "PASS":
        return "FAIL"

    required_gate_truths = (
        gate.get("mechanism_runtime_vector_credit_candidate") is True,
        gate.get("scientifically_independent_vector_candidate") is True,
        gate.get("owner_trigger1_goal_credit_candidate") is True,
    )
    if gate.get("schema") == PROMOTION_GATE_SCHEMA and all(required_gate_truths):
        return "PASS"
    return "FAIL"


def evidence_summary(gate: dict[str, Any] | None) -> dict[str, bool]:
    gate = gate if isinstance(gate, dict) else {}
    return {
        "mechanism_runtime_vector_credit_candidate": gate.get("mechanism_runtime_vector_credit_candidate") is True,
        "scientifically_independent_vector_candidate": gate.get("scientifically_independent_vector_candidate") is True,
        "owner_trigger1_goal_credit_candidate": gate.get("owner_trigger1_goal_credit_candidate") is True,
    }
