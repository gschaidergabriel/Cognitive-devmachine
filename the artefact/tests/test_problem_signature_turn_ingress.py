from __future__ import annotations

import hashlib

import pytest

from clayverse.method_memory import MethodRecordError
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _runtime(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db, TurnLifecycle(db, "gabriel", session_id)


def _signature():
    return {
        "goal": ["recover"],
        "mechanism": ["stateful", "provenance"],
    }


def _provenance(source="VALIDATED_ABSTRACTION"):
    producer = "microclay-structural-abstraction-v1"
    return {
        "source": source,
        "producer": producer,
        "abstraction_version": "problem-signature-v1",
        "producer_sha256": hashlib.sha256(producer.encode("utf-8")).hexdigest(),
    }


def test_turn_ingress_persists_typed_signature_before_stage_b_context(tmp_path):
    db, lifecycle = _runtime(tmp_path)
    resources = ["repo:clay-global-research-entity", "db:unified"]

    with lifecycle.begin_admission(
        "recover state provenance without inventing facts",
        resources,
        problem_signature=_signature(),
        problem_signature_provenance=_provenance(),
    ) as admission:
        context = admission["context"]
        method_receipt = context["method_retrieval_receipt"]
        evidence_receipt = context["retrieval_receipt"]

        assert admission["problem_signature_receipt_id"]
        assert method_receipt["signature_receipt_id"] == admission["problem_signature_receipt_id"]
        assert method_receipt["signature_source"] == "VALIDATED_ABSTRACTION"
        assert method_receipt["signature_abstraction_version"] == "problem-signature-v1"
        assert method_receipt["signature_identity_sha256"]
        assert method_receipt["signature_provenance_sha256"]
        assert method_receipt["problem_signature_sha256"]
        assert method_receipt["resource_ref_count"] == 2
        assert method_receipt["status"] in {"METHOD_UNKNOWN", "METHOD_PRESENT"}
        assert method_receipt["factual_status_unchanged"] == evidence_receipt["status"]
        assert method_receipt["truth_authority"] is False
        assert method_receipt["effect_authority"] is False

        row = db.db.execute(
            "SELECT kind,source_turn_id,user_id,value FROM durable_memory WHERE memory_id=?",
            (admission["problem_signature_receipt_id"],),
        ).fetchone()
        assert row is not None
        assert row["kind"] == "method_receipt"
        assert row["source_turn_id"] == admission["turn_id"]
        assert row["user_id"] == "gabriel"


def test_turn_ingress_unknown_signature_provenance_rolls_back_entire_new_turn(tmp_path):
    db, lifecycle = _runtime(tmp_path)

    with pytest.raises(MethodRecordError, match="provenance source is not admitted"):
        with lifecycle.begin_admission(
            "recover state provenance",
            [],
            problem_signature=_signature(),
            problem_signature_provenance=_provenance("UNTRUSTED_PROMPT_INFERENCE"),
        ):
            raise AssertionError("invalid signature provenance reached Stage-B")

    assert lifecycle.active() is None
    assert db.db.execute("SELECT COUNT(*) FROM turns WHERE session_id='session:gabriel'").fetchone()[0] == 0
    assert db.db.execute("SELECT COUNT(*) FROM workspace_episodes WHERE session_id='session:gabriel'").fetchone()[0] == 0
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'").fetchone()[0] == 0


def test_turn_ingress_requires_signature_and_provenance_as_one_typed_packet(tmp_path):
    _, lifecycle = _runtime(tmp_path)

    with pytest.raises(ValueError, match="must be supplied together"):
        with lifecycle.begin_admission(
            "recover state provenance",
            [],
            problem_signature=_signature(),
            problem_signature_provenance=None,
        ):
            raise AssertionError("partial signature packet admitted")


def test_turn_without_signature_remains_signature_required(tmp_path):
    _, lifecycle = _runtime(tmp_path)

    with lifecycle.begin_admission("recover state provenance", []) as admission:
        receipt = admission["context"]["method_retrieval_receipt"]
        assert admission["problem_signature_receipt_id"] is None
        assert receipt["status"] == "SIGNATURE_REQUIRED"
        assert receipt["signature_source"] == "NONE"
        assert receipt["signature_receipt_id"] is None
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
