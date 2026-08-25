import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xeno_shell_packets_v1 as pk


def _work_kwargs(**overrides):
    base = dict(
        causal_event_id="ce1", admission_id="adm1", generation=1, work_id="w1",
        process_id="ZECP11", parent_work_id=None, workspace_epoch=7,
        db_snapshot_refs=["s0:ref1"], input_evidence_refs=["ev1"],
        epistemic_classes=["OBSERVED"], capability_scope_ref="cap:scope1",
        resource_budget={"max_tokens": 32}, runtime_grid_facts={"n": 10},
        route_policy_ref="policy:v1", completion_contract={"kind": "single_atom"},
    )
    base.update(overrides)
    return base


def test_build_and_validate_work_packet_roundtrip():
    p = pk.build_work_packet(**_work_kwargs())
    pk.validate_work_packet(p)
    assert p["schema"] == "COGNITIVE_WORK_PACKET/v1"


def test_work_packet_missing_field_rejected():
    kwargs = _work_kwargs()
    del kwargs["generation"]
    try:
        pk.build_work_packet(**kwargs)
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "MISSING_FIELDS" in str(e)


def test_work_packet_unknown_field_rejected():
    kwargs = _work_kwargs()
    kwargs["extra_field_not_in_spec"] = 1
    try:
        pk.build_work_packet(**kwargs)
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "UNKNOWN_FIELDS" in str(e)


def test_work_packet_tampered_digest_rejected():
    p = pk.build_work_packet(**_work_kwargs())
    p["body"]["generation"] = 999
    try:
        pk.validate_work_packet(p)
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "DIGEST_MISMATCH" in str(e)


def test_result_packet_candidate_from_model_ok():
    r = pk.build_result_packet(
        result_class="CANDIDATE", producer="MODEL",
        source_work_digest="abc", payload={"atom": "A"},
        unresolved_alternatives=[{"atom": "B"}],
    )
    pk.validate_result_packet(r)
    assert r["body"]["unresolved_alternatives"] == [{"atom": "B"}]


def test_result_packet_effect_receipt_from_model_forbidden():
    try:
        pk.build_result_packet(
            result_class="EFFECT_RECEIPT", producer="MODEL",
            source_work_digest="abc", payload={},
        )
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "RESULT_CLASS_PRODUCER_FORBIDDEN" in str(e)


def test_result_packet_deterministic_control_result_from_model_forbidden():
    try:
        pk.build_result_packet(
            result_class="DETERMINISTIC_CONTROL_RESULT", producer="CLAUDE_CODE",
            source_work_digest="abc", payload={},
        )
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "RESULT_CLASS_PRODUCER_FORBIDDEN" in str(e)


def test_result_packet_effect_receipt_from_zecp17_allowed():
    r = pk.build_result_packet(
        result_class="EFFECT_RECEIPT", producer="ZECP17",
        source_work_digest="abc", payload={"effect": "noop"},
    )
    pk.validate_result_packet(r)


def test_result_packet_unknown_class_rejected():
    try:
        pk.build_result_packet(
            result_class="TRUTH", producer="ZECP17",
            source_work_digest="abc", payload={},
        )
        assert False, "expected PacketError"
    except pk.PacketError as e:
        assert "UNKNOWN_CLASS" in str(e)
