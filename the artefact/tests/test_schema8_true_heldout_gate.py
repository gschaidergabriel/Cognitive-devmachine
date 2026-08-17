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
from clayverse.store import UnifiedDB


def _sha256_json(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _candidate():
    return {
        "problem_signature": {"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        "abstraction_version": "v1",
        # Formation/provenance episodes are deliberately NOT held-out transfer evidence.
        "source_episode_ids": ["episode:source:a", "episode:source:b"],
    }


def _admit_validation(
    db: UnifiedDB,
    *,
    candidate_memory_id: str,
    episode_id: str,
    index: int,
    classification: str = "SUCCESS",
) -> str:
    candidate = _candidate()
    signature_sha = _sha256_json(candidate["problem_signature"])
    status = "VERIFIED" if classification == "SUCCESS" else "FAILED"
    credit = 1.0 if classification == "SUCCESS" else 0.0
    value = validate_candidate_validation_receipt(
        {
            "schema": CANDIDATE_VALIDATION_SCHEMA,
            "candidate_memory_id": candidate_memory_id,
            "candidate_use_receipt_id": f"use:{index}",
            "candidate_kind": "framework_candidate",
            "abstraction_version": "v1",
            "candidate_signature_sha256": signature_sha,
            "user_id": "gabriel",
            "session_id": "session:gabriel",
            "turn_id": f"turn:validation:{index}",
            "episode_id": episode_id,
            "causal_id": f"causal:validation:{index}",
            "generation": 1,
            "evidence_status": "UNKNOWN",
            "problem_signature_sha256": signature_sha,
            "evaluation_mode": "HELD_OUT",
            "falsifier_checked": True,
            "effect_id": f"effect:validation:{index}",
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
    return db.add_method_memory(
        "method_receipt",
        f"candidate_validation:{candidate_memory_id}:{value['causal_id']}",
        value,
        None,
        "gabriel",
        {
            "schema": CANDIDATE_VALIDATION_SCHEMA,
            "admission": "method_candidate_validation:v1",
            "candidate_memory_id": candidate_memory_id,
            "user_scope": "gabriel",
            "truth_authority": False,
            "effect_authority": False,
        },
    )


def test_schema8_promotion_stats_accept_two_true_heldout_successes(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_session("gabriel", "clayverse-gabriel")
    try:
        candidate_id = "candidate:true-heldout"
        first = _admit_validation(
            db,
            candidate_memory_id=candidate_id,
            episode_id="episode:heldout:a",
            index=1,
        )
        second = _admit_validation(
            db,
            candidate_memory_id=candidate_id,
            episode_id="episode:heldout:b",
            index=2,
        )

        stats = derive_promotion_stats(db.db, candidate_id, _candidate(), "gabriel")
        assert stats["support_count"] == 2
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 0
        assert stats["calibration"] == 1.0
        assert stats["validation_receipt_ids"] == [first, second]
    finally:
        db.close()


def test_schema8_one_success_plus_one_failure_cannot_promote_reusable_method(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_session("gabriel", "clayverse-gabriel")
    try:
        candidate_id = "candidate:anti-anecdote"
        _admit_validation(
            db,
            candidate_memory_id=candidate_id,
            episode_id="episode:heldout:a",
            index=1,
            classification="SUCCESS",
        )
        _admit_validation(
            db,
            candidate_memory_id=candidate_id,
            episode_id="episode:heldout:b",
            index=2,
            classification="FAILURE",
        )

        with pytest.raises(MethodValidationError, match="two validated successes"):
            derive_promotion_stats(db.db, candidate_id, _candidate(), "gabriel")
    finally:
        db.close()
