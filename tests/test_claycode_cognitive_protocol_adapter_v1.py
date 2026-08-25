from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import pytest

from tools.claycode_cognitive_protocol_adapter_v1 import (
    ClayCodeProtocolError,
    claude_bridge_request,
    claude_bridge_stub_result,
    classify_state,
    execute_on_grid,
    make_work_packet,
    parse_work,
    serialize_work,
    workspace_reentry,
)
from tools.zero_entityos_restart_resize_db_smoke_v1 import CanonicalStateAuthority, CognitiveGridRuntime, GridConfig

EVENT = "11" * 32
ADMISSION = "22" * 32


def make_packet(snapshot: str, *, generation: int = 3, process_id: str = "ZECP03"):
    return make_work_packet(
        causal_event_id="event-fixture-001",
        admission_id="admission-fixture-001",
        entry_event_sha256=EVENT,
        entry_admission_sha256=ADMISSION,
        generation=generation,
        workspace_epoch=7,
        process_id=process_id,
        state_snapshot_ref="sha256:" + snapshot,
        payload={"goal_ref": "goal", "evidence_ref": "evidence/ref"},
        capability_scope_ref="capability:read-propose-only",
        resource_budget={"max_model_calls": 0, "max_tokens": 0, "max_wall_ms": 1000},
        epistemic_inputs=[{"ref": "evidence/ref", "status": "OBSERVED"}],
    )


def test_wire_roundtrip_preserves_semantic_hash():
    packet = make_packet("aa" * 32)
    wire = serialize_work(packet)
    parsed = parse_work(wire)
    assert parsed == packet
    assert wire.startswith(b"CLAYCODE-CP/1\n")


def test_wire_tamper_fails_closed():
    packet = make_packet("aa" * 32)
    wire = bytearray(serialize_work(packet))
    wire[-3] = ord("x")
    with pytest.raises(ClayCodeProtocolError):
        parse_work(bytes(wire))


def test_semantic_identity_excludes_grid_n_and_executor():
    packet = make_packet("aa" * 32)
    assert "requested_N" not in packet
    assert "executor_id" not in packet
    assert "lease_id" not in packet


def test_state_placement_separates_durable_and_transient():
    durable = classify_state(
        entry_event_sha256=EVENT, generation=3, datum_ref="goal", durable=True,
        exact=True, queryable=True, restart_surviving=True, epistemic_status="OBSERVED",
    )
    transient = classify_state(
        entry_event_sha256=EVENT, generation=3, datum_ref="hypothesis", durable=False,
        exact=False, queryable=False, restart_surviving=False, epistemic_status="HYPOTHESIS",
    )
    assert durable["selected_plane"] == "DATABASE_S0"
    assert durable["canonical_write"] is False
    assert durable["requires_deterministic_admission"] is True
    assert transient["selected_plane"] == "WORKSPACE_S1"
    assert transient["canonical_fact"] is False


def test_stale_generation_rejected_before_grid_execution():
    class NeverCalled:
        def enqueue(self, *_args, **_kwargs):
            raise AssertionError("must not route stale work")

    packet = make_packet("aa" * 32, generation=2)
    with pytest.raises(ClayCodeProtocolError, match="STALE_GENERATION"):
        execute_on_grid(NeverCalled(), packet, current_generation=3)


def test_claude_stub_roundtrip_has_zero_execution_and_jspace_credit():
    packet = make_packet("aa" * 32)
    req = claude_bridge_request(packet, interface_class="TEXT", payload={"task": "fixture-only"})
    ret = claude_bridge_stub_result(req, payload={"candidate": "no-model-call"})
    assert req["activation_access_claimed"] is False
    assert req["claude_execution_observed"] is False
    assert ret["global_jspace_causal_credit"] is False
    assert ret["authority"] == "CANDIDATE_ONLY"


def test_reentry_rejects_mismatched_typed_entry_identity():
    packet = make_packet("aa" * 32)
    fake_result = {
        "entry_event_sha256": EVENT,
        "entry_admission_sha256": ADMISSION,
        "generation": 3,
        "workspace_epoch": 7,
        "runtime_result": {"result_id": "r1"},
    }
    req = claude_bridge_request(packet, interface_class="TEXT", payload={"task": "fixture"})
    ret = claude_bridge_stub_result(req, payload={"candidate": "x"})
    ret["entry_event_sha256"] = "33" * 32
    with pytest.raises(ClayCodeProtocolError, match="REENTRY_BINDING_MISMATCH:entry_event_sha256"):
        workspace_reentry(fake_result, ret)


def test_protocol_executes_across_real_fixture_restart_and_n_change():
    with tempfile.TemporaryDirectory(prefix="claycode-cog-proto-") as td:
        db_path = Path(td) / "canonical.sqlite3"
        authority = CanonicalStateAuthority(db_path)
        try:
            generation = 3
            authority.seed("goal", {"goal": "claycode-protocol"}, provenance="fixture:admitted", generation=generation, epoch=1)
            authority.seed("evidence/ref", "ev-001", provenance="fixture:observed", generation=generation, epoch=1)
            snapshot = authority.snapshot_digest()
            packet = make_packet(snapshot)
            reparsed = parse_work(serialize_work(packet))

            grid1 = CognitiveGridRuntime(db_path, GridConfig(n=1, generation=generation))
            try:
                result1 = execute_on_grid(grid1, reparsed, current_generation=generation)
                request = claude_bridge_request(reparsed, interface_class="TEXT", payload={"task": "stub"})
                bridge_result = claude_bridge_stub_result(request, payload={"candidate": "stub-only"})
                reentry = workspace_reentry(result1, bridge_result)
                assert reentry["global_jspace_causal_credit"] is False
            finally:
                grid1.close()

            assert authority.snapshot_digest() == snapshot

            grid20 = CognitiveGridRuntime(db_path, GridConfig(n=20, generation=generation))
            try:
                result20 = execute_on_grid(grid20, reparsed, current_generation=generation)
                assert result20["clay_semantic_hash"] == result1["clay_semantic_hash"]
                assert result20["state_snapshot_ref"] == result1["state_snapshot_ref"]
                assert result20["entry_event_sha256"] == EVENT
                assert result20["entry_admission_sha256"] == ADMISSION
                assert result20["runtime_result"]["process_id"] == "ZECP03"
                assert result20["canonical_db_write"] is False
                assert result20["real_effect_authority"] is False
            finally:
                grid20.close()

            assert authority.snapshot_digest() == snapshot
        finally:
            authority.close()
