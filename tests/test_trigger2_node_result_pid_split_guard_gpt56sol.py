from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_node_result_model_call_authority_envelope_v1.py"
spec = importlib.util.spec_from_file_location("gate_pid_split", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def h(ch: str) -> str:
    return ch * 64


def packet(*, payload_pid: int = 101, producer_pid: int | None = None) -> dict:
    value = {
        "schema": gate.NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "scope": "GLOBAL",
        "source_node_id": "x01",
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("a"),
        "payload": {"process_pid": payload_pid, "semantic": "same-payload"},
        "s1_write_intent": False,
    }
    if producer_pid is not None:
        value["producer_pid"] = producer_pid
    core = {k: value[k] for k in value if k not in ("packet_digest", "s1_write_intent")}
    value["packet_digest"] = gate.canonical_sha256(core)
    return value


def test_fused_style_matching_top_level_and_payload_pid_is_accepted():
    raw = gate.validate_raw_node_result(packet(payload_pid=101, producer_pid=101))
    assert raw["raw_process_pid"] == 101


def test_self_consistent_digest_cannot_hide_split_producer_and_payload_pid():
    p = packet(payload_pid=101, producer_pid=202)
    # The digest is deliberately recomputed after introducing the split, so rejection must
    # come from the identity invariant rather than from generic packet-integrity failure.
    try:
        gate.validate_raw_node_result(p)
    except gate.GateError as exc:
        assert str(exc) == "NODE_RESULT_PRODUCER_PID_PAYLOAD_MISMATCH"
    else:
        raise AssertionError("split producer/process PID identity was accepted")
