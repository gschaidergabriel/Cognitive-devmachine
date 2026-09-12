import json
from pathlib import Path
import tempfile

from omega.bridge_transport import BridgeTarget
from omega.receipt_reconciler import ReceiptReconciler, effect_command_id, validate_host_receipt
from omega.unified_store import UnifiedStore, now


ROOT = Path(__file__).resolve().parents[1]


def _target() -> BridgeTarget:
    return BridgeTarget(
        organ_id="host:ai-core-node",
        owner_id="gabriel",
        machine_id="ai-core-node",
        control_branch="control",
        results_branch="results",
    )


def test_exact_late_receipt_promotes_unknown_without_new_attempt():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "state"
        db = Path(td) / "omega.db"
        store = UnifiedStore(db, ROOT / "schema")
        effect_id = "effect_late_receipt"
        command_id = effect_command_id(effect_id)
        created = now()
        intent = {
            "schema": "OMEGA_GRID_EFFECT_INTENT/v1",
            "effect_id": effect_id,
            "organ_id": "host:ai-core-node",
            "runtime_epoch_id": "epoch-test",
            "task": {"task_id": "task-late", "effect": {"op": "status"}},
        }
        with store.connect() as con:
            con.execute(
                """
                INSERT INTO effect_intent(
                  effect_id,frame_id,organ_id,owner_id,machine_id,request_digest,payload_json,
                  authority_state,dispatch_state,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    effect_id, "frame-test", "host:ai-core-node", "gabriel", "ai-core-node",
                    "request-digest", json.dumps(intent), "ALLOW", "UNKNOWN", created, created,
                ),
            )
            con.execute(
                """
                INSERT INTO relay_ledger(
                  effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,
                  last_error,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    effect_id, "host:ai-core-node", command_id, "UNKNOWN", 1,
                    "command-digest", None, "timeout", created, created,
                ),
            )

        target = _target()
        raw = json.dumps(
            {
                "command_id": command_id,
                "machine_id": "ai-core-node",
                "owner": "gabriel",
                "status": "PASS",
            },
            sort_keys=True,
        )
        receipt, receipt_digest = validate_host_receipt(target, command_id, raw)

        reconciler = ReceiptReconciler.__new__(ReceiptReconciler)
        reconciler.runtime_root = runtime
        reconciler.store = store
        result = reconciler._apply(
            {
                "effect_id": effect_id,
                "organ_id": "host:ai-core-node",
                "command_digest": "command-digest",
                "created_at": created,
                "request_digest": "request-digest",
                "payload_json": json.dumps(intent),
            },
            target,
            receipt,
            receipt_digest,
        )

        assert result["state"] == "COMPLETED"
        assert result["reconciled_from_unknown"] is True
        assert result["automatic_replay"] is False
        with store.connect() as con:
            relay = con.execute(
                "SELECT state,attempt_count,receipt_digest FROM relay_ledger WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            effect = con.execute(
                "SELECT dispatch_state FROM effect_intent WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            evidence = con.execute(
                "SELECT status,result_digest FROM effect_receipt WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
        assert tuple(relay) == ("COMPLETED", 1, receipt_digest)
        assert effect[0] == "COMPLETED"
        assert tuple(evidence) == ("PASS", receipt_digest)
        persisted = json.loads((runtime / "relay_results" / f"{effect_id}.json").read_text())
        assert persisted["state"] == "COMPLETED"
        assert persisted["automatic_replay"] is False


def test_late_receipt_rejects_wrong_host_attribution():
    target = _target()
    command_id = effect_command_id("effect_wrong_host")
    raw = json.dumps(
        {
            "command_id": command_id,
            "machine_id": "andreas-maco",
            "owner": "gabriel",
            "status": "PASS",
        }
    )
    try:
        validate_host_receipt(target, command_id, raw)
    except ValueError as exc:
        assert str(exc) == "RECEIPT_MACHINE_ID_MISMATCH"
    else:
        raise AssertionError("wrong-host receipt was accepted")
