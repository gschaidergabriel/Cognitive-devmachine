from __future__ import annotations

import hashlib
import json
import time

import pytest

from clayverse.method_validation import (
    CANDIDATE_VALIDATION_SCHEMA,
    MethodValidationError,
    derive_promotion_stats,
    validate_candidate_validation_receipt,
)


def _sha256_json(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


class _ReceiptDB:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *_args, **_kwargs):
        return _Rows(self._rows)


def _candidate():
    return {
        "problem_signature": {
            "goal": ["verify"],
            "mechanism": ["causal", "provenance"],
        },
        "abstraction_version": "v1",
        "source_episode_ids": ["episode:formation:a", "episode:formation:b"],
    }


def _validation_row(index: int, classification: str):
    candidate = _candidate()
    signature_sha = _sha256_json(candidate["problem_signature"])
    status = "VERIFIED" if classification == "SUCCESS" else "FAILED"
    credit = 1.0 if classification == "SUCCESS" else 0.0
    value = validate_candidate_validation_receipt(
        {
            "schema": CANDIDATE_VALIDATION_SCHEMA,
            "candidate_memory_id": "candidate:threshold",
            "candidate_use_receipt_id": f"use:{index}",
            "candidate_kind": "framework_candidate",
            "abstraction_version": "v1",
            "candidate_signature_sha256": signature_sha,
            "user_id": "gabriel",
            "session_id": "session:gabriel",
            "turn_id": f"turn:heldout:{index}",
            "episode_id": f"episode:heldout:{index}",
            "causal_id": f"causal:heldout:{index}",
            "generation": 1,
            "evidence_status": "UNKNOWN",
            "problem_signature_sha256": signature_sha,
            "evaluation_mode": "HELD_OUT",
            "falsifier_checked": index == 1,
            "effect_id": f"effect:heldout:{index}",
            "effect_capability": "entityos.exec",
            "effect_status": status,
            "outcome_hash": hashlib.sha256(f"outcome:{index}:{status}".encode()).hexdigest(),
            "causal_credit": credit,
            "causal_receipt_id": hashlib.sha256(f"causal-receipt:{index}".encode()).hexdigest(),
            "signal_class": f"effect_outcome:{status}",
            "classification": classification,
            "truth_authority": False,
            "effect_authority": False,
            "ts": time.time() + index,
        }
    )
    return {
        "memory_id": f"validation:{index}",
        "value": json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False),
    }


def test_one_success_plus_one_failure_remains_candidate_evidence_only():
    db = _ReceiptDB([
        _validation_row(1, "SUCCESS"),
        _validation_row(2, "FAILURE"),
    ])
    with pytest.raises(MethodValidationError, match="two validated successes"):
        derive_promotion_stats(db, "candidate:threshold", _candidate(), "gabriel")


def test_two_distinct_heldout_successes_can_satisfy_the_transfer_count_gate():
    db = _ReceiptDB([
        _validation_row(1, "SUCCESS"),
        _validation_row(2, "SUCCESS"),
    ])
    stats = derive_promotion_stats(db, "candidate:threshold", _candidate(), "gabriel")
    assert stats["support_count"] == 2
    assert stats["success_count"] == 2
    assert stats["failure_count"] == 0
    assert stats["calibration"] == 1.0
