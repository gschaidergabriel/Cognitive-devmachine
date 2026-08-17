from __future__ import annotations

import pytest

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import BridgeStateError, ClayVerseEffectBridge
from clayverse.method_stageb import (
    QUERY_ADMISSION_VERSION,
    QUERY_SCHEMA,
    MethodRetrievalIdentityError,
    ProblemSignatureAdmissionError,
    admit_problem_query,
)
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _runtime(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    life = TurnLifecycle(db, "gabriel", "session:gabriel")
    return db, life, ClayVerseEffectBridge(life)


def _signature():
    return {"goal": ["diagnose"], "mechanism": ["causal_boundary"]}


def test_raw_turn_remains_signature_required_until_explicit_mcp_ingress(tmp_path):
    db, life, bridge = _runtime(tmp_path)
    try:
        turn = life.begin("novel diagnostic problem with no factual memory")
        assert turn["context"]["method_context"] == []
        assert turn["context"]["method_receipt"]["status"] == "METHOD_NOT_SERVED_SIGNATURE_ADMISSION_REQUIRED"
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 0

        result = bridge.method_context(_signature(), "diagnose")
        receipt = result["method_receipt"]
        signature_receipt = result["signature_receipt"]

        assert receipt["status"] == "METHOD_UNKNOWN"
        assert receipt["served"] is False
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
        assert result["truth_authority"] is False
        assert result["effect_authority"] is False
        assert result["served_automatically"] is False
        assert result["unknowns"] == [{
            "status": "FACT_UNKNOWN",
            "query_sha256": result["retrieval_receipt"]["query_sha256"],
            "method_present": False,
            "fact_status_unchanged": True,
        }]

        assert signature_receipt["source"] == ClayVerseEffectBridge.METHOD_SIGNATURE_SOURCE
        assert signature_receipt["truth_authority"] is False
        assert signature_receipt["effect_authority"] is False
        assert receipt["signature_sha256"] == signature_receipt["signature_sha256"]

        active = life.active()
        durable = db.db.execute("SELECT * FROM method_use_receipts WHERE causal_id=?", (turn["causal_id"],)).fetchone()
        assert durable is not None
        assert str(durable["turn_id"]) == str(active["turn_id"]) == turn["turn_id"]
        assert str(durable["episode_id"]) == str(active["episode_id"]) == turn["episode_id"]
        assert str(durable["session_id"]) == "session:gabriel"
        assert str(durable["user_id"]) == "gabriel"
        assert int(durable["generation"]) == int(active["generation"]) == turn["generation"]
        assert str(durable["query_schema"]) == QUERY_SCHEMA
        assert int(durable["admission_version"]) == QUERY_ADMISSION_VERSION
        assert str(durable["problem_signature_hash"]) == signature_receipt["signature_sha256"]

        forged_source = admit_problem_query({
            "schema": QUERY_SCHEMA,
            "problem_signature": _signature(),
            "goal_shape": "diagnose",
            "provenance": {
                "source": "caller_chosen_source",
                "turn_id": turn["turn_id"],
                "episode_id": turn["episode_id"],
                "causal_id": turn["causal_id"],
                "generation": turn["generation"],
                "admission_version": QUERY_ADMISSION_VERSION,
            },
        }).receipt()
        assert forged_source["signature_sha256"] != str(durable["problem_signature_hash"])

        replay = bridge.method_context(_signature(), "diagnose")
        assert replay["method_receipt"]["replayed"] is True
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 1
    finally:
        if life.active() is not None:
            life.abort("test-end")
        db.close()


def test_mcp_signature_ingress_does_not_accept_caller_identity_or_source(tmp_path):
    db, life, bridge = _runtime(tmp_path)
    try:
        life.begin("another novel problem")
        with pytest.raises(TypeError):
            bridge.method_context(_signature(), "diagnose", source="raw_prompt")
        with pytest.raises(TypeError):
            bridge.method_context(_signature(), "diagnose", turn_id="attacker-turn")
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 0
    finally:
        if life.active() is not None:
            life.abort("test-end")
        db.close()


def test_malformed_or_same_causal_signature_drift_fails_closed(tmp_path):
    db, life, bridge = _runtime(tmp_path)
    try:
        life.begin("bounded unknown problem")
        with pytest.raises(ProblemSignatureAdmissionError):
            bridge.method_context({"goal": ["diagnose"]}, "diagnose")
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 0

        bridge.method_context(_signature(), "diagnose")
        with pytest.raises(MethodRetrievalIdentityError, match="method_retrieval_identity"):
            bridge.method_context(
                {"goal": ["diagnose"], "mechanism": ["different_boundary"]},
                "diagnose",
            )
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 1
    finally:
        if life.active() is not None:
            life.abort("test-end")
        db.close()


def test_method_context_requires_active_canonical_turn(tmp_path):
    db, life, bridge = _runtime(tmp_path)
    try:
        with pytest.raises(BridgeStateError, match="active canonical turn"):
            bridge.method_context(_signature(), "diagnose")
        assert db.db.execute("SELECT COUNT(*) FROM method_use_receipts").fetchone()[0] == 0
    finally:
        db.close()
