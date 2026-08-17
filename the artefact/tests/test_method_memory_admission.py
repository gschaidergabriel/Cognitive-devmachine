import json
import math
import sqlite3
import time

import pytest

from clayverse.method_memory import (
    METHOD_SCHEMA_VERSION,
    MethodMemoryManager,
    MethodMemoryValidationError,
    canonical_method_value,
    signature_facets,
    validate_method_record,
)


class FakeDB:
    def __init__(self):
        self.rows = []

    def add_memory(self, kind, subject, value, source_turn_id, user_id, provenance):
        memory_id = f"m{len(self.rows) + 1}"
        self.rows.append(
            {
                "memory_id": memory_id,
                "kind": kind,
                "subject": subject,
                "value": value,
                "source_turn_id": source_turn_id,
                "user_id": user_id,
                "ts": time.time(),
                "provenance": json.dumps(provenance, sort_keys=True),
            }
        )
        return memory_id


def candidate_record(**overrides):
    value = {
        "problem_signature": {
            "goal": ["identify causal fault"],
            "constraint_shape": ["partial observability"],
            "evidence_shape": ["competing explanations"],
        },
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": "separate competing causal mechanisms",
        "method_steps": ["generate alternatives", "derive discriminating predictions", "run cheapest falsifier"],
        "invariants": ["unknown facts remain unknown"],
        "expected_observations": ["one intervention separates predictions"],
        "falsifiers": ["candidate predictions remain indistinguishable"],
        "failure_modes": ["proxy metric is not causally diagnostic"],
        "scope_limits": ["not for settled factual lookup"],
        "source_episode_ids": ["episode:a"],
        "supporting_memory_ids": ["evidence:a"],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        "support_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "calibration": 0.5,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }
    value.update(overrides)
    return value


def promoted_record(**overrides):
    value = candidate_record(
        source_episode_ids=["episode:a", "episode:b"],
        support_count=2,
        success_count=2,
        calibration=0.7,
        last_validated_at=time.time(),
        status="PROMOTED",
    )
    value.update(overrides)
    return value


def test_candidate_admission_is_canonical_and_schema_bound():
    db = FakeDB()
    manager = MethodMemoryManager(db)
    mid = manager.admit(
        "framework_candidate",
        "causal discrimination",
        candidate_record(),
        "turn:1",
        "gabriel",
        {"source": "episode_abstraction", "extractor": "test"},
    )
    assert mid == "m1"
    row = db.rows[0]
    assert json.loads(row["provenance"])["method_schema_version"] == METHOD_SCHEMA_VERSION
    assert json.loads(row["value"])["status"] == "CANDIDATE"
    decoded = manager.decode_row(row)
    assert decoded["kind"] == "framework_candidate"
    assert decoded["value"]["problem_signature"]["goal"] == ["identify causal fault"]


def test_candidate_cannot_self_promote_by_status_flip():
    with pytest.raises(MethodMemoryValidationError, match="candidate kind must remain CANDIDATE"):
        validate_method_record(
            "framework_candidate",
            candidate_record(status="PROMOTED", last_validated_at=time.time()),
            {"source": "episode_abstraction", "promotion_receipt_id": "forged"},
        )


def test_promoted_method_requires_cross_episode_support_and_receipt():
    with pytest.raises(MethodMemoryValidationError, match="single success cannot promote"):
        validate_method_record(
            "framework",
            promoted_record(source_episode_ids=["episode:a"], support_count=1, success_count=1),
            {"source": "promotion", "promotion_receipt_id": "r1"},
        )
    with pytest.raises(MethodMemoryValidationError, match="promotion_receipt_id"):
        validate_method_record(
            "framework",
            promoted_record(),
            {"source": "promotion"},
        )
    validated = validate_method_record(
        "framework",
        promoted_record(),
        {"source": "promotion", "promotion_receipt_id": "r1"},
    )
    assert validated["status"] == "PROMOTED"


def test_counts_and_calibration_fail_closed():
    with pytest.raises(MethodMemoryValidationError, match="support_count"):
        validate_method_record(
            "framework_candidate",
            candidate_record(support_count=0, success_count=1),
            {"source": "episode_abstraction"},
        )
    with pytest.raises(MethodMemoryValidationError, match="canonical JSON"):
        validate_method_record(
            "framework_candidate",
            candidate_record(calibration=float("nan")),
            {"source": "episode_abstraction"},
        )


def test_signature_facets_are_structural_and_deterministic():
    record = candidate_record(
        problem_signature={
            "constraint_shape": ["Partial Observability", "bounded intervention"],
            "goal": "Identify Causal Fault",
        }
    )
    assert signature_facets(record) == (
        "constraint_shape=bounded intervention",
        "constraint_shape=partial observability",
        "goal=identify causal fault",
    )


def test_decode_rejects_unknown_schema_or_malformed_stored_record():
    db = FakeDB()
    manager = MethodMemoryManager(db)
    row = {
        "memory_id": "m1",
        "kind": "framework_candidate",
        "subject": "bad",
        "value": json.dumps(candidate_record()),
        "source_turn_id": "turn:1",
        "user_id": "gabriel",
        "ts": time.time(),
        "provenance": json.dumps({"source": "legacy", "method_schema_version": 999}),
    }
    with pytest.raises(MethodMemoryValidationError, match="unknown schema version"):
        manager.decode_row(row)

    row["provenance"] = json.dumps({"source": "legacy", "method_schema_version": METHOD_SCHEMA_VERSION})
    value = candidate_record()
    del value["falsifiers"]
    row["value"] = json.dumps(value)
    with pytest.raises(MethodMemoryValidationError, match="missing method fields"):
        manager.decode_row(row)


def test_method_receipt_requires_bounded_known_fields():
    receipt = {
        "method_memory_id": "m1",
        "action": "PROMOTE",
        "source_episode_ids": ["episode:a", "episode:b"],
        "supporting_memory_ids": ["evidence:a"],
        "counterexample_memory_ids": [],
        "evaluation": "held-out structural transfer improved without factual contamination",
        "ts": time.time(),
    }
    encoded = canonical_method_value("method_receipt", receipt, {"source": "held_out_eval"})
    assert json.loads(encoded)["action"] == "PROMOTE"
    receipt["authority_grant"] = "effect:*"
    with pytest.raises(MethodMemoryValidationError, match="unknown method receipt fields"):
        canonical_method_value("method_receipt", receipt, {"source": "held_out_eval"})


# GO unusual experiment: METHOD_RECORD_TRUTH_SMUGGLE.
# One method candidate tries to carry factual/authority claims through undeclared fields.
# The admission boundary must reject the whole record rather than silently drop them.
def test_unusual_method_record_truth_smuggle_rejected():
    attack = candidate_record()
    attack["facts"] = ["invented fact may be treated as true"]
    attack["truth_confidence"] = 1.0
    attack["effect_authority"] = "*"
    with pytest.raises(MethodMemoryValidationError, match="unknown method fields"):
        validate_method_record(
            "framework_candidate",
            attack,
            {"source": "adversarial_experiment"},
        )
