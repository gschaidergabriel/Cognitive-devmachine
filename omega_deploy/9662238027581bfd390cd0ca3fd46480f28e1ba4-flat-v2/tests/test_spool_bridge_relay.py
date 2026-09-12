import hashlib
import json
import threading
import time

import pytest

from omega.bridge_transport import BridgeError, BridgeOutcomeUnknown, BridgeTarget
from omega.spool_bridge_relay import SpoolTransport


TARGET = BridgeTarget(
    organ_id="host:ai-core-node",
    owner_id="gabriel",
    machine_id="ai-core-node",
    control_branch="chatgpt-local-ai-core-node-control",
    results_branch="chatgpt-local-ai-core-node-results",
)


def _command():
    return {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": "omega-test-1",
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "op": "status",
    }


def _canonical_sha(payload):
    raw = (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def test_rejects_owner_mismatch_before_staging(tmp_path):
    tr = SpoolTransport(tmp_path, poll_seconds=0.01)
    command = _command()
    command["owner"] = "andreas"
    with pytest.raises(BridgeError):
        tr.dispatch(TARGET, command, receipt_timeout=0.05)
    assert list((tmp_path / "outbox").glob("*.json")) == []


def test_completed_receipt_roundtrip(tmp_path):
    tr = SpoolTransport(tmp_path, poll_seconds=0.01)
    command = _command()
    command_sha = _canonical_sha(command)
    host_receipt = {
        "command_id": command["command_id"],
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "status": "PASS",
    }

    def writer():
        outbox = tmp_path / "outbox" / f"{command['command_id']}.json"
        deadline = time.monotonic() + 1
        while not outbox.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        payload = {
            "schema": "OMEGA_OUTER_BRIDGE_RECEIPT/v1",
            "state": "COMPLETED",
            "command_id": command["command_id"],
            "organ_id": TARGET.organ_id,
            "machine_id": TARGET.machine_id,
            "owner": TARGET.owner_id,
            "control_branch": TARGET.control_branch,
            "results_branch": TARGET.results_branch,
            "command_sha256": command_sha,
            "host_receipt": host_receipt,
            "host_receipt_canonical_sha256": _canonical_sha(host_receipt),
        }
        inbox = tmp_path / "inbox" / f"{command['command_id']}.json"
        inbox.write_text(json.dumps(payload), encoding="utf-8")

    thread = threading.Thread(target=writer)
    thread.start()
    receipt, got_command_sha, receipt_sha = tr.dispatch(TARGET, command, receipt_timeout=1)
    thread.join(timeout=1)
    assert receipt == host_receipt
    assert got_command_sha == command_sha
    assert receipt_sha == _canonical_sha(host_receipt)


def test_unknown_is_terminal_no_replay(tmp_path):
    tr = SpoolTransport(tmp_path, poll_seconds=0.01)
    command = _command()
    command_sha = _canonical_sha(command)
    staged = {
        "schema": "OMEGA_OUTER_BRIDGE_COMMAND/v1",
        "command_id": command["command_id"],
        "organ_id": TARGET.organ_id,
        "machine_id": TARGET.machine_id,
        "owner": TARGET.owner_id,
        "control_branch": TARGET.control_branch,
        "results_branch": TARGET.results_branch,
        "command_sha256": command_sha,
        "command": command,
    }
    (tmp_path / "outbox" / f"{command['command_id']}.json").write_text(json.dumps(staged), encoding="utf-8")
    unknown = {
        "schema": "OMEGA_OUTER_BRIDGE_RECEIPT/v1",
        "state": "UNKNOWN",
        "reason": "push outcome unresolved; no automatic replay",
        "command_id": command["command_id"],
        "organ_id": TARGET.organ_id,
        "machine_id": TARGET.machine_id,
        "owner": TARGET.owner_id,
        "control_branch": TARGET.control_branch,
        "results_branch": TARGET.results_branch,
        "command_sha256": command_sha,
    }
    (tmp_path / "inbox" / f"{command['command_id']}.json").write_text(json.dumps(unknown), encoding="utf-8")
    with pytest.raises(BridgeOutcomeUnknown):
        tr.dispatch(TARGET, command, receipt_timeout=0.1)
