from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .bridge_transport import BridgeTarget, command_from_effect
from .receipt_reconciler import ReceiptReconciler, effect_command_id, validate_host_receipt
from .unified_store import UnifiedStore, now


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _sha(payload: Any) -> str:
    return hashlib.sha256(_json_bytes(payload)).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class SpoolReceiptReconciler(ReceiptReconciler):
    """Reconcile UNKNOWN effects from the credential-free outer spool."""

    def __init__(
        self,
        *,
        runtime_root: Path,
        repo_root: Path,
        db_path: Path,
        router_path: Path,
        spool_root: Path,
    ) -> None:
        self.runtime_root = runtime_root
        self.store = UnifiedStore(db_path, repo_root / "schema")
        self.spool_root = spool_root
        self.outbox = spool_root / "outbox"
        self.inbox = spool_root / "inbox"
        router = json.loads(router_path.read_text(encoding="utf-8"))
        self.organs = {str(o["organ_id"]): o for o in router.get("organs", ())}
        (runtime_root / "relay_results").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_identity(
        payload: dict[str, Any],
        *,
        target: BridgeTarget,
        command_id: str,
        prefix: str,
    ) -> None:
        expected = {
            "command_id": command_id,
            "organ_id": target.organ_id,
            "machine_id": target.machine_id,
            "owner": target.owner_id,
            "control_branch": target.control_branch,
            "results_branch": target.results_branch,
        }
        for key, value in expected.items():
            if str(payload.get(key)) != str(value):
                raise ValueError(f"{prefix}_{key.upper()}_MISMATCH")

    @staticmethod
    def _request_from_row(row: dict[str, Any]) -> dict[str, Any]:
        intent = json.loads(str(row["payload_json"]))
        task = intent.get("task") if isinstance(intent.get("task"), dict) else {}
        request = task.get("effect") or task.get("execution")
        if not isinstance(request, dict):
            raise ValueError("EFFECT_INTENT_EXECUTION_DESCRIPTOR_MISSING")
        return request

    def _read_spool_late_receipt(
        self,
        row: dict[str, Any],
        target: BridgeTarget,
        command_id: str,
    ) -> tuple[dict[str, Any], str, str] | None:
        effect_id = str(row["effect_id"])
        if row.get("owner_id") is not None and str(row["owner_id"]) != target.owner_id:
            raise ValueError("EFFECT_INTENT_OWNER_ID_MISMATCH")
        if row.get("machine_id") is not None and str(row["machine_id"]) != target.machine_id:
            raise ValueError("EFFECT_INTENT_MACHINE_ID_MISMATCH")

        request = self._request_from_row(row)
        expected_command = command_from_effect(effect_id, target, request)
        if str(expected_command.get("command_id") or "") != command_id:
            raise ValueError("RECONSTRUCTED_COMMAND_ID_MISMATCH")
        expected_command_sha = _sha(expected_command)
        stored_command_sha = str(row.get("command_digest") or "")
        if stored_command_sha and stored_command_sha != expected_command_sha:
            raise ValueError("LEDGER_COMMAND_DIGEST_CONFLICT")

        receipt_path = self.inbox / f"{command_id}.json"
        if not receipt_path.exists():
            return None
        outer = json.loads(receipt_path.read_text(encoding="utf-8"))
        if outer.get("schema") != "OMEGA_OUTER_BRIDGE_RECEIPT/v1":
            raise ValueError("OUTER_RECEIPT_SCHEMA_MISMATCH")
        self._validate_identity(outer, target=target, command_id=command_id, prefix="OUTER_RECEIPT")

        if str(outer.get("state", "")).upper() != "COMPLETED":
            return None
        if outer.get("automatic_replay") is not False:
            raise ValueError("OUTER_RECEIPT_REPLAY_ATTESTATION_MISSING")

        command_path = self.outbox / f"{command_id}.json"
        if not command_path.exists():
            raise ValueError("OUTER_COMMAND_ENVELOPE_MISSING")
        envelope = json.loads(command_path.read_text(encoding="utf-8"))
        if envelope.get("schema") != "OMEGA_OUTER_BRIDGE_COMMAND/v1":
            raise ValueError("OUTER_COMMAND_SCHEMA_MISMATCH")
        self._validate_identity(envelope, target=target, command_id=command_id, prefix="OUTER_COMMAND")

        command = envelope.get("command")
        if not isinstance(command, dict):
            raise ValueError("OUTER_COMMAND_PAYLOAD_MISSING")
        if command != expected_command:
            raise ValueError("OUTER_COMMAND_DOES_NOT_MATCH_IMMUTABLE_EFFECT_INTENT")
        command_sha = _sha(command)
        if command_sha != expected_command_sha:
            raise ValueError("OUTER_COMMAND_RECONSTRUCTION_DIGEST_MISMATCH")
        if str(envelope.get("command_sha256") or "") != command_sha:
            raise ValueError("OUTER_COMMAND_CANONICAL_DIGEST_MISMATCH")
        if str(outer.get("command_sha256") or "") != command_sha:
            raise ValueError("OUTER_RECEIPT_COMMAND_DIGEST_MISMATCH")

        host_receipt = outer.get("host_receipt")
        if not isinstance(host_receipt, dict):
            raise ValueError("OUTER_RECEIPT_HOST_RECEIPT_MISSING")
        canonical_raw = _json_bytes(host_receipt).decode("utf-8")
        receipt, canonical_digest = validate_host_receipt(target, command_id, canonical_raw)
        claimed_canonical = str(outer.get("host_receipt_canonical_sha256") or "")
        if claimed_canonical and claimed_canonical != canonical_digest:
            raise ValueError("OUTER_RECEIPT_HOST_CANONICAL_DIGEST_MISMATCH")

        receipt_digest = str(outer.get("host_receipt_file_sha256") or canonical_digest)
        return receipt, receipt_digest, command_sha

    def _backfill_command_binding(self, row: dict[str, Any], command_id: str, command_sha: str) -> None:
        effect_id = str(row["effect_id"])
        with self.store.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            current = con.execute(
                "SELECT state,command_id,command_digest FROM relay_ledger WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if current is None or str(current["state"]) != "UNKNOWN":
                raise ValueError("RECONCILE_LEDGER_NO_LONGER_UNKNOWN")
            existing_id = str(current["command_id"] or "")
            existing_sha = str(current["command_digest"] or "")
            if existing_id and existing_id != command_id:
                raise ValueError("RECONCILE_LEDGER_COMMAND_ID_CONFLICT")
            if existing_sha and existing_sha != command_sha:
                raise ValueError("RECONCILE_LEDGER_COMMAND_DIGEST_CONFLICT")
            con.execute(
                "UPDATE relay_ledger SET command_id=?,command_digest=?,updated_at=? WHERE effect_id=? AND state='UNKNOWN'",
                (command_id, command_sha, now(), effect_id),
            )
            con.commit()

    def _persisted_relay_state(self, effect_id: str) -> str:
        with self.store.connect() as con:
            row = con.execute("SELECT state FROM relay_ledger WHERE effect_id=?", (effect_id,)).fetchone()
        return str(row[0]) if row is not None else "MISSING"

    def run_once(self) -> list[dict[str, Any]]:
        self._publish_pending_results()
        results: list[dict[str, Any]] = []
        for row in self._unknown_rows():
            effect_id = str(row["effect_id"])
            target = self._target(str(row["organ_id"]))
            if target is None:
                continue
            command_id = effect_command_id(effect_id)
            try:
                found = self._read_spool_late_receipt(row, target, command_id)
                if found is None:
                    continue
                receipt, receipt_digest, command_sha = found
                self._backfill_command_binding(row, command_id, command_sha)
                results.append(self._apply(row, target, receipt, receipt_digest))
            except Exception as exc:
                persisted_state = self._persisted_relay_state(effect_id)
                _atomic_json(
                    self.runtime_root / "relay_results" / f"RECONCILE_ERROR_{effect_id}.json",
                    {
                        "at": now(),
                        "effect_id": effect_id,
                        "organ_id": str(row["organ_id"]),
                        "error": f"{type(exc).__name__}:{exc}",
                        "persisted_relay_state": persisted_state,
                        "automatic_replay": False,
                    },
                )
        return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/omega_runtime/current"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--router", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/omega_runtime/current/config/organ_router.json"))
    ap.add_argument("--spool-root", default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_RECEIPT_RECONCILE_INTERVAL", "15")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    reconciler = SpoolReceiptReconciler(
        runtime_root=Path(args.runtime_root),
        repo_root=Path(args.repo_root),
        db_path=Path(args.db),
        router_path=Path(args.router),
        spool_root=Path(args.spool_root),
    )
    if args.once:
        print(json.dumps(reconciler.run_once(), ensure_ascii=False, indent=2))
        return 0
    reconciler.run_forever(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())