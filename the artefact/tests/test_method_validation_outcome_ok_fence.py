import json

import pytest

from clayverse.method_validation import (
    CANDIDATE_USE_SCHEMA,
    CandidateValidation,
    MethodValidationError,
    _sha256_json,
)


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _SQL:
    def __init__(self, use_row, outcome_row):
        self.rows = [use_row, outcome_row]
        self.queries = []

    def execute(self, query, params=()):
        self.queries.append((query, params))
        if "ORDER BY ts LIMIT 1" in query:
            return _Result(None)
        return _Result(self.rows.pop(0))


class _DB:
    def __init__(self, use_row, outcome_row):
        self.db = _SQL(use_row, outcome_row)
        self.added = []

    def add_method_memory(self, *args):
        self.added.append(args)
        return "validation-receipt"


def _use_row():
    signature = {"goal": ["diagnose"], "mechanism": ["causal_boundary"]}
    value = {
        "schema": CANDIDATE_USE_SCHEMA,
        "candidate_memory_id": "candidate-1",
        "candidate_kind": "framework_candidate",
        "abstraction_version": "1",
        "candidate_signature_sha256": "a" * 64,
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn-1",
        "episode_id": "episode-heldout-1",
        "causal_id": "causal-heldout-1",
        "generation": 7,
        "evidence_status": "UNKNOWN",
        "problem_signature": signature,
        "problem_signature_sha256": _sha256_json(signature),
        "evaluation_mode": "HELD_OUT",
        "falsifier_checked": True,
        "truth_authority": False,
        "effect_authority": False,
        "ts": 1.0,
    }
    return {"memory_id": "candidate-use-1", "user_id": "gabriel", "value": json.dumps(value)}


def _outcome_row(*, ok):
    return {
        "session_id": "session:gabriel",
        "state": "COMPLETED",
        "observation_turn_id": "turn-1",
        "session_user": "gabriel",
        "turn_user": "gabriel",
        "causal_id": "causal-heldout-1",
        "causal_episode_id": "episode-heldout-1",
        "effect_id": "effect-1",
        "outcome_hash": "outcome-hash-1",
        "credit": 1.0,
        "reentered": 1,
        "effect_user": "gabriel",
        "capability": "entityos.exec",
        "status": "VERIFIED",
        "requested_generation": 7,
        "verified_at": 2.0,
        "outcome": json.dumps({"ok": ok}),
    }


def test_verified_positive_credit_with_ok_false_cannot_mint_success_receipt():
    db = _DB(_use_row(), _outcome_row(ok=False))
    with pytest.raises(MethodValidationError, match="verified outcome ok=true"):
        CandidateValidation(db).finalize(candidate_use_receipt_id="candidate-use-1")
    assert db.added == []
    assert "e.outcome" in db.db.queries[1][0]


def test_verified_positive_credit_with_ok_true_mints_success_receipt():
    db = _DB(_use_row(), _outcome_row(ok=True))
    receipt_id = CandidateValidation(db).finalize(candidate_use_receipt_id="candidate-use-1")
    assert receipt_id == "validation-receipt"
    assert len(db.added) == 1
    kind, subject, value, turn_id, user_id, provenance = db.added[0]
    assert kind == "method_receipt"
    assert subject == "candidate_validation:candidate-1:causal-heldout-1"
    assert value["classification"] == "SUCCESS"
    assert value["effect_status"] == "VERIFIED"
    assert value["causal_credit"] == 1.0
    assert turn_id == "turn-1" and user_id == "gabriel"
    assert provenance["truth_authority"] is False
    assert provenance["effect_authority"] is False
