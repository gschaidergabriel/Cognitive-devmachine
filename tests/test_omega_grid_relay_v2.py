from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import omega_grid_relay as relay  # noqa: E402


def _effect(organ_id: str = "host:ai-core-node", task: dict | None = None) -> dict:
    effect = {
        "effect_id": "e-test-1",
        "organ_id": organ_id,
        "task": task or {"bridge_op": "status", "bridge_args": {}},
        "route": {"source": "test"},
        "authority": "NOT_YET_GRANTED",
    }
    effect["request_sha256"] = relay.digest(effect)
    return effect


def test_build_local_command_binds_exact_gabriel_subject():
    cid, command, op = relay.build_local_command(_effect())
    assert cid == "omega-effect-e-test-1"
    assert op == "status"
    assert command["machine_id"] == "ai-core-node"
    assert command["owner"] == "gabriel"


def test_build_local_command_binds_exact_andreas_subject():
    cid, command, op = relay.build_local_command(_effect("host:andreas-maco"))
    assert cid == "omega-effect-e-test-1"
    assert op == "status"
    assert command["machine_id"] == "andreas-maco"
    assert command["owner"] == "andreas"


def test_alignment_guard_denies_delete_format_and_self_mutation():
    assert relay.dangerous_exec("rm -rf /tmp/x") == "DELETE_REMOVAL_DENIED"
    assert relay.dangerous_exec("mkfs.ext4 /dev/sda") == "STORAGE_FORMAT_DENIED"
    assert relay.dangerous_exec("printf x > voice_action_guard.py") == "ALIGNMENT_SELF_MUTATION_DENIED"


def test_validate_receipt_requires_command_machine_owner_and_op():
    target = relay.ORGAN["host:ai-core-node"]
    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": "c1",
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "op": "status",
    }
    assert relay.validate_local_receipt(receipt, "c1", target, "status") is None
    assert relay.validate_local_receipt(dict(receipt, owner="andreas"), "c1", target, "status") == "RECEIPT_OWNER_MISMATCH"
    assert relay.validate_local_receipt(dict(receipt, machine_id="andreas-maco"), "c1", target, "status") == "RECEIPT_MACHINE_ID_MISMATCH"
    assert relay.validate_local_receipt(dict(receipt, command_id="c2"), "c1", target, "status") == "RECEIPT_COMMAND_ID_MISMATCH"
    assert relay.validate_local_receipt(dict(receipt, op="exec"), "c1", target, "status") == "RECEIPT_OP_MISMATCH"


def test_put_new_accepts_only_byte_identical_existing_command(monkeypatch):
    monkeypatch.setattr(relay, "_request", lambda *a, **k: (422, {"message": "exists"}))
    monkeypatch.setattr(relay, "get_file", lambda *a, **k: b"same")
    assert relay.put_new("branch", "p", b"same", "m") is False


def test_put_new_rejects_same_id_with_changed_bytes(monkeypatch):
    monkeypatch.setattr(relay, "_request", lambda *a, **k: (422, {"message": "exists"}))
    monkeypatch.setattr(relay, "get_file", lambda *a, **k: b"old")
    try:
        relay.put_new("branch", "p", b"new", "m")
    except RuntimeError as exc:
        assert str(exc) == "COMMAND_ID_CONFLICT"
    else:
        raise AssertionError("changed bytes under one command id must conflict")


def test_process_dispatches_once_and_returns_pending_without_block(monkeypatch):
    effect = _effect()
    writes = []
    returns = []
    monkeypatch.setattr(relay, "get_file", lambda *a, **k: None)
    monkeypatch.setattr(relay, "put_new", lambda branch, path, content, message: writes.append((branch, path, content)) or True)
    monkeypatch.setattr(relay, "wait_file", lambda *a, **k: None)
    monkeypatch.setattr(relay, "return_to_omega", lambda *a, **k: returns.append((a, k)))
    outcome = relay.process({"payload": effect}, receipt_wait_s=0)
    assert outcome == "PENDING"
    assert len(writes) == 1
    assert returns[0][1]["consume_intent"] is False


def test_process_finalizes_existing_exact_receipt_without_dispatch(monkeypatch):
    effect = _effect()
    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": "omega-effect-e-test-1",
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "op": "status",
        "status": "PASS",
        "finished_at": "2026-09-12T13:00:00+00:00",
    }
    returns = []
    monkeypatch.setattr(relay, "get_file", lambda *a, **k: relay.json.dumps(receipt).encode())
    monkeypatch.setattr(relay, "put_new", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not redispatch")))
    monkeypatch.setattr(relay, "return_to_omega", lambda *a, **k: returns.append((a, k)))
    assert relay.process({"payload": effect}) == "PASS"
    assert returns[0][1]["consume_intent"] is True


def test_process_mismatched_receipt_is_unknown_and_terminal(monkeypatch):
    effect = _effect()
    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": "omega-effect-e-test-1",
        "machine_id": "ai-core-node",
        "owner": "andreas",
        "op": "status",
        "status": "PASS",
    }
    returns = []
    monkeypatch.setattr(relay, "get_file", lambda *a, **k: relay.json.dumps(receipt).encode())
    monkeypatch.setattr(relay, "return_to_omega", lambda *a, **k: returns.append((a, k)))
    outcome = relay.process({"payload": effect})
    assert outcome == "UNKNOWN:RECEIPT_OWNER_MISMATCH"
    assert returns[0][1]["consume_intent"] is True


def test_unknown_organ_is_explicit_denial_not_silent_return(monkeypatch):
    effect = _effect("host:not-real")
    returns = []
    monkeypatch.setattr(relay, "return_to_omega", lambda *a, **k: returns.append((a, k)))
    outcome = relay.process({"payload": effect})
    assert outcome == "DENIED:UNKNOWN_ORGAN"
    assert returns[0][1]["consume_intent"] is True


def test_digest_mismatch_is_explicit_denial(monkeypatch):
    effect = _effect()
    effect["route"] = {"tampered": True}
    returns = []
    monkeypatch.setattr(relay, "return_to_omega", lambda *a, **k: returns.append((a, k)))
    outcome = relay.process({"payload": effect})
    assert outcome == "DENIED:REQUEST_DIGEST_MISMATCH"
    assert returns[0][1]["consume_intent"] is True
