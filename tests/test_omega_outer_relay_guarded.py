from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import omega_outer_relay as base
import omega_outer_relay_guarded as guarded


class FakeRuntime:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.writes: dict[str, bytes] = {}

    def read_bytes(self, path: str) -> bytes:
        return self.files[path]

    def write_bytes_atomic(self, path: str, raw: bytes) -> None:
        self.writes[path] = raw


class FakeMailbox:
    def __init__(self, *, host_receipt: dict | None = None, publish_exc: Exception | None = None) -> None:
        self.host_receipt = host_receipt
        self.publish_exc = publish_exc
        self.published: list[tuple[str, str, bytes]] = []
        self.waited: list[tuple[str, str, float]] = []

    def publish_exact(self, branch: str, rel: str, raw: bytes) -> None:
        self.published.append((branch, rel, raw))
        if self.publish_exc is not None:
            raise self.publish_exc

    def wait_receipt(self, branch: str, rel: str, timeout_seconds: float) -> bytes:
        self.waited.append((branch, rel, timeout_seconds))
        if self.host_receipt is None:
            raise AssertionError("wait_receipt must not be called")
        return base.json_bytes(self.host_receipt)


def command(command_id: str, *, op: str = "status") -> dict:
    return {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": command_id,
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "op": op,
    }


def envelope(command_id: str, *, op: str = "status") -> dict:
    cmd = command(command_id, op=op)
    return {
        "schema": "OMEGA_OUTER_BRIDGE_COMMAND/v1",
        "command_id": command_id,
        "organ_id": "host:ai-core-node",
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "control_branch": "chatgpt-local-ai-core-node-control",
        "results_branch": "chatgpt-local-ai-core-node-results",
        "command_sha256": base.sha(base.json_bytes(cmd)),
        "command": cmd,
    }


def make_relay(tmp_path: Path, runtime: FakeRuntime, mailbox: FakeMailbox) -> guarded.GuardedOuterRelay:
    return guarded.GuardedOuterRelay(
        runtime=runtime,
        mailbox=mailbox,
        spool_root="/spool",
        ledger_root=tmp_path / "ledger",
        receipt_timeout=0.1,
    )


def put(runtime: FakeRuntime, command_id: str, payload: dict | bytes) -> str:
    path = f"/spool/outbox/{command_id}.json"
    runtime.files[path] = payload if isinstance(payload, bytes) else base.json_bytes(payload)
    return f"{command_id}.json"


def read_write(runtime: FakeRuntime, path: str) -> dict:
    return json.loads(runtime.writes[path].decode("utf-8"))


def test_pre_dispatch_validation_rejection_is_immediate_terminal_receipt(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    mailbox = FakeMailbox()
    relay = make_relay(tmp_path, runtime, mailbox)
    command_id = "omega-reject-unsupported-op"
    filename = put(runtime, command_id, envelope(command_id, op="definitely_not_allowed"))

    result = relay.process_name(filename)

    assert result["state"] == "REJECTED"
    assert result["dispatch_crossed"] is False
    assert result["effect_may_have_occurred"] is False
    assert result["automatic_replay"] is False
    assert mailbox.published == []
    assert mailbox.waited == []

    inbox = read_write(runtime, f"/spool/inbox/{command_id}.json")
    assert inbox["state"] == "REJECTED"
    assert inbox["command_id"] == command_id
    assert inbox["machine_id"] == "ai-core-node"
    assert inbox["owner"] == "gabriel"
    assert inbox["organ_id"] == "host:ai-core-node"
    assert inbox["dispatch_crossed"] is False
    assert inbox["automatic_replay"] is False

    ledger = json.loads((tmp_path / "ledger" / f"{command_id}.json").read_text(encoding="utf-8"))
    assert ledger == inbox


def test_filename_command_id_mismatch_returns_bound_rejection_without_dispatch(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    mailbox = FakeMailbox()
    relay = make_relay(tmp_path, runtime, mailbox)
    filename_id = "omega-filename-id"
    env = envelope("omega-nested-id")
    filename = put(runtime, filename_id, env)

    result = relay.process_name(filename)

    # validate_envelope succeeds for the embedded command, then the filename binding
    # is rejected before any publication.  The receipt is keyed by the observed spool
    # filename so the waiting side can terminate deterministically.
    assert result["state"] == "REJECTED"
    assert result["command_id"] == filename_id
    assert result["reason"] == "FILENAME_COMMAND_ID_MISMATCH"
    assert mailbox.published == []
    inbox = read_write(runtime, f"/spool/inbox/{filename_id}.json")
    assert inbox["state"] == "REJECTED"
    assert inbox["dispatch_crossed"] is False


def test_malformed_unbindable_input_does_not_fabricate_identity(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    mailbox = FakeMailbox()
    relay = make_relay(tmp_path, runtime, mailbox)
    command_id = "omega-malformed-json"
    filename = put(runtime, command_id, b"{ definitely not json")

    result = relay.process_name(filename)

    assert result["state"] == "REJECTED_UNBOUND"
    assert result["dispatch_crossed"] is False
    assert result["automatic_replay"] is False
    assert runtime.writes == {}
    assert mailbox.published == []
    assert mailbox.waited == []


def test_valid_success_path_is_unchanged_and_completed(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    command_id = "omega-valid-roundtrip"
    host_receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": command_id,
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "status": "PASS",
    }
    mailbox = FakeMailbox(host_receipt=host_receipt)
    relay = make_relay(tmp_path, runtime, mailbox)
    filename = put(runtime, command_id, envelope(command_id))

    result = relay.process_name(filename)

    assert result["state"] == "COMPLETED"
    assert result["host_receipt"] == host_receipt
    assert len(mailbox.published) == 1
    assert len(mailbox.waited) == 1
    inbox = read_write(runtime, f"/spool/inbox/{command_id}.json")
    assert inbox["state"] == "COMPLETED"
    assert inbox["host_receipt"] == host_receipt


def test_ambiguous_publish_outcome_stays_unknown_and_is_never_downgraded_to_rejected(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    command_id = "omega-publish-unknown"
    mailbox = FakeMailbox(publish_exc=base.OutcomeUnknown("push outcome unresolved; no automatic replay"))
    relay = make_relay(tmp_path, runtime, mailbox)
    filename = put(runtime, command_id, envelope(command_id))

    result = relay.process_name(filename)

    assert result["state"] == "UNKNOWN"
    assert result["automatic_replay"] is False
    assert len(mailbox.published) == 1
    assert mailbox.waited == []
    inbox = read_write(runtime, f"/spool/inbox/{command_id}.json")
    assert inbox["state"] == "UNKNOWN"
    assert inbox["automatic_replay"] is False
