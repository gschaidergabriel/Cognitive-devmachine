import hashlib
import json
from pathlib import Path

from omega.bridge_transport import BridgeOutcomeUnknown, BridgeTarget
from omega.outer_bridge_worker import OuterBridgeWorker


def _json_bytes(payload):
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _sha(payload):
    return hashlib.sha256(_json_bytes(payload)).hexdigest()


def _envelope(command_id="omega-test-1"):
    command = {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": command_id,
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "op": "status",
    }
    return {
        "schema": "OMEGA_OUTER_BRIDGE_COMMAND/v1",
        "command_id": command_id,
        "organ_id": "host:ai-core-node",
        "machine_id": "ai-core-node",
        "owner": "gabriel",
        "control_branch": "chatgpt-local-ai-core-node-control",
        "results_branch": "chatgpt-local-ai-core-node-results",
        "command_sha256": _sha(command),
        "command": command,
    }


class FakeTransport:
    def __init__(self, *, outcome="completed"):
        self.outcome = outcome
        self.calls = 0

    def dispatch(self, target: BridgeTarget, command, *, receipt_timeout=180.0):
        self.calls += 1
        if self.outcome == "unknown":
            raise BridgeOutcomeUnknown("simulated ambiguous push")
        receipt = {
            "command_id": command["command_id"],
            "machine_id": target.machine_id,
            "owner": target.owner_id,
            "status": "PASS",
        }
        return receipt, _sha(command), hashlib.sha256(b"host-file").hexdigest()


def _stage(root: Path, envelope):
    outbox = root / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{envelope['command_id']}.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return path


def test_completed_dispatch_writes_bound_terminal_receipt(tmp_path):
    envelope = _envelope()
    path = _stage(tmp_path, envelope)
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    result = worker.process_path(path)

    assert result["state"] == "COMPLETED"
    assert transport.calls == 1
    receipt_path = tmp_path / "inbox" / f"{envelope['command_id']}.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["machine_id"] == "ai-core-node"
    assert receipt["owner"] == "gabriel"
    assert receipt["command_sha256"] == envelope["command_sha256"]
    assert receipt["host_receipt"]["status"] == "PASS"
    assert receipt["host_receipt_canonical_sha256"] == _sha(receipt["host_receipt"])


def test_existing_terminal_receipt_is_never_redispatched(tmp_path):
    envelope = _envelope()
    path = _stage(tmp_path, envelope)
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)
    worker.process_path(path)
    assert transport.calls == 1

    second = worker.process_path(path)

    assert second["state"] == "ALREADY_TERMINAL"
    assert transport.calls == 1


def test_recovered_dispatching_journal_becomes_unknown_without_replay(tmp_path):
    envelope = _envelope()
    path = _stage(tmp_path, envelope)
    journal = tmp_path / "journal"
    journal.mkdir(parents=True, exist_ok=True)
    (journal / f"{envelope['command_id']}.json").write_text(
        json.dumps(
            {
                "schema": "OMEGA_OUTER_BRIDGE_JOURNAL/v1",
                "state": "DISPATCHING",
                "command_id": envelope["command_id"],
                "command_sha256": envelope["command_sha256"],
            }
        ),
        encoding="utf-8",
    )
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    result = worker.process_path(path)

    assert result["state"] == "UNKNOWN"
    assert result["automatic_replay"] is False
    assert transport.calls == 0


def test_terminal_journal_without_inbox_is_recovered_to_unknown_without_replay(tmp_path):
    envelope = _envelope()
    path = _stage(tmp_path, envelope)
    journal = tmp_path / "journal"
    journal.mkdir(parents=True, exist_ok=True)
    (journal / f"{envelope['command_id']}.json").write_text(
        json.dumps(
            {
                "schema": "OMEGA_OUTER_BRIDGE_JOURNAL/v1",
                "state": "COMPLETED",
                "command_id": envelope["command_id"],
                "command_sha256": envelope["command_sha256"],
            }
        ),
        encoding="utf-8",
    )
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    result = worker.process_path(path)

    assert result["state"] == "UNKNOWN"
    assert "without terminal inbox receipt" in result["reason"]
    assert transport.calls == 0
    assert (tmp_path / "inbox" / f"{envelope['command_id']}.json").exists()


def test_transport_unknown_is_terminal_and_not_replayed(tmp_path):
    envelope = _envelope()
    path = _stage(tmp_path, envelope)
    transport = FakeTransport(outcome="unknown")
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    first = worker.process_path(path)
    second = worker.process_path(path)

    assert first["state"] == "UNKNOWN"
    assert first["automatic_replay"] is False
    assert second["state"] == "ALREADY_TERMINAL"
    assert transport.calls == 1


def test_digest_mismatch_fails_before_transport(tmp_path):
    envelope = _envelope()
    envelope["command"]["op"] = "exec"
    path = _stage(tmp_path, envelope)
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    result = worker.process_path(path)

    assert result["state"] == "FAILED"
    assert "PRE_DISPATCH_VALIDATION" in result["reason"]
    assert transport.calls == 0


def test_owner_mismatch_fails_before_transport(tmp_path):
    envelope = _envelope()
    envelope["command"]["owner"] = "andreas"
    envelope["command_sha256"] = _sha(envelope["command"])
    path = _stage(tmp_path, envelope)
    transport = FakeTransport()
    worker = OuterBridgeWorker(spool_root=tmp_path, transport=transport)

    result = worker.process_path(path)

    assert result["state"] == "FAILED"
    assert transport.calls == 0
