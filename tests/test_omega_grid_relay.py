from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import omega_grid_relay as relay  # noqa: E402


def _effect(*, organ_id: str = "host:ai-core-node", command: str = "printf hello") -> dict:
    base = {
        "effect_id": "test-effect-1",
        "organ_id": organ_id,
        "task": {"bridge_op": "exec", "bridge_args": {"command": command, "timeout_seconds": 30}},
        "route": {"selected": organ_id},
        "authority": "NOT_YET_GRANTED",
    }
    return {**base, "request_sha256": relay.digest(base)}


def _command_and_bytes(effect: dict | None = None):
    effect = effect or _effect()
    _cid, command, _op = relay.build_local_command(effect)
    return command, relay.serialized_local_command(command)


def _receipt(target: dict, command: dict, command_bytes: bytes, **overrides):
    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "machine_id": target["machine_id"],
        "owner": target["owner"],
        "command_id": command["command_id"],
        "op": command["op"],
        "command_sha256": relay.command_sha256(command_bytes),
        "status": "PASS",
        "exit_code": 0,
        "errors": [],
        "execution_boundary": "REAL_LOCAL_HOST_TEST",
    }
    receipt.update(overrides)
    return receipt


def test_local_command_is_bound_to_exact_host_and_owner():
    command, _ = _command_and_bytes(_effect(organ_id="host:ai-core-node"))
    assert command["machine_id"] == "ai-core-node"
    assert command["owner"] == "gabriel"

    command, _ = _command_and_bytes(_effect(organ_id="host:andreas-maco"))
    assert command["machine_id"] == "andreas-maco"
    assert command["owner"] == "andreas"


def test_exact_correlated_receipt_is_accepted():
    target = relay.ORGAN["host:ai-core-node"]
    command, command_bytes = _command_and_bytes()
    receipt = _receipt(target, command, command_bytes)
    assert relay.verify_local_receipt(target, command, command_bytes, receipt) is receipt


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("machine_id", "andreas-maco", "RECEIPT_IDENTITY_MISMATCH"),
        ("owner", "andreas", "RECEIPT_IDENTITY_MISMATCH"),
        ("command_id", "omega-effect-other", "RECEIPT_COMMAND_MISMATCH"),
        ("op", "status", "RECEIPT_OP_MISMATCH"),
        ("command_sha256", "0" * 64, "RECEIPT_COMMAND_DIGEST_MISMATCH"),
        ("exit_code", 7, "RECEIPT_EXIT_CODE_MISMATCH"),
    ],
)
def test_receipt_correlation_mismatch_is_never_pass(field: str, value, code: str):
    target = relay.ORGAN["host:ai-core-node"]
    command, command_bytes = _command_and_bytes()
    receipt = _receipt(target, command, command_bytes, **{field: value})
    with pytest.raises(relay.ReceiptVerificationError) as exc:
        relay.verify_local_receipt(target, command, command_bytes, receipt)
    assert exc.value.code == code


def test_receipt_schema_and_pass_status_are_fail_closed():
    target = relay.ORGAN["host:ai-core-node"]
    command, command_bytes = _command_and_bytes()

    bad_schema = _receipt(target, command, command_bytes, schema="OTHER/v1")
    with pytest.raises(relay.ReceiptVerificationError) as exc:
        relay.verify_local_receipt(target, command, command_bytes, bad_schema)
    assert exc.value.code == "RECEIPT_SCHEMA_MISMATCH"

    failed = _receipt(target, command, command_bytes, status="FAIL", exit_code=1)
    with pytest.raises(relay.ReceiptVerificationError) as exc:
        relay.verify_local_receipt(target, command, command_bytes, failed)
    assert exc.value.code == "RECEIPT_NOT_PASS"


def test_delete_format_and_alignment_self_mutation_are_denied():
    assert relay.dangerous_exec("rm -rf /tmp/omega-nope") == "DELETE_REMOVAL_DENIED"
    assert relay.dangerous_exec("mkfs.ext4 /dev/sdb") == "STORAGE_FORMAT_DENIED"
    assert relay.dangerous_exec("printf x > tools/omega_grid_relay.py") == "ALIGNMENT_SELF_MUTATION_DENIED"


def test_timeout_becomes_unknown_and_does_not_mint_pass(monkeypatch):
    effect = _effect()
    returned = []
    queued = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        queued.append((branch, path, content, message))
        return True

    monkeypatch.setattr(relay, "put_new", put_new)
    monkeypatch.setattr(relay, "wait_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(relay, "return_to_omega", lambda e, state, gate, receipt: returned.append((e, state, gate, receipt)))

    relay.process({"payload": effect})

    assert len(queued) == 1
    assert len(returned) == 1
    _effect_returned, state, gate, evidence = returned[0]
    assert state == "UNKNOWN"
    assert gate["receipt_state"] == "RECEIPT_TIMEOUT_NO_REPLAY"
    assert gate["machine_id"] == "ai-core-node"
    assert gate["owner"] == "gabriel"
    assert evidence["reason"] == "RECEIPT_TIMEOUT_NO_REPLAY"


def test_cross_host_pass_receipt_is_downgraded_to_unknown(monkeypatch):
    effect = _effect()
    returned = []
    queued: list[bytes] = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        queued.append(content)
        return True

    def wait_file(branch: str, path: str, timeout_s: float = 75.0):
        command_bytes = queued[-1]
        command = json.loads(command_bytes)
        wrong_target = relay.ORGAN["host:andreas-maco"]
        wrong = _receipt(wrong_target, command, command_bytes)
        return json.dumps(wrong).encode()

    monkeypatch.setattr(relay, "put_new", put_new)
    monkeypatch.setattr(relay, "wait_file", wait_file)
    monkeypatch.setattr(relay, "return_to_omega", lambda e, state, gate, receipt: returned.append((state, gate, receipt)))

    relay.process({"payload": effect})

    assert returned[0][0] == "UNKNOWN"
    assert returned[0][1]["receipt_state"] == "RECEIPT_IDENTITY_MISMATCH"
    assert returned[0][2]["reason"] == "RECEIPT_IDENTITY_MISMATCH"
