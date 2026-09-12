from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .bridge_transport import BridgeTarget, GitBranchTransport
from .unified_store import UnifiedStore, now


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def effect_command_id(effect_id: str) -> str:
    return "omega-" + effect_id.replace("effect_", "")[:48]


def validate_host_receipt(target: BridgeTarget, command_id: str, raw: str) -> tuple[dict[str, Any], str]:
    receipt = json.loads(raw)
    if str(receipt.get("command_id")) != command_id:
        raise ValueError("RECEIPT_COMMAND_ID_MISMATCH")
    if str(receipt.get("machine_id")) != target.machine_id:
        raise ValueError("RECEIPT_MACHINE_ID_MISMATCH")
    if str(receipt.get("owner")) != target.owner_id:
        raise ValueError("RECEIPT_OWNER_ID_MISMATCH")
    return receipt, hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ReceiptReconciler:
    """Resolve UNKNOWN host effects from late receipts without ever republishing them.

    UNKNOWN is a no-replay state, not an evidence black hole. A bridge receipt may
    arrive after a timeout, watchdog termination, or relay-process crash. This daemon
    only reads the host results branch. If an exact command/owner/machine receipt is
    found, it upgrades the existing effect evidence to COMPLETED and rewrites the
    relay-result file consumed by GRID. It never writes a control-branch command.
    """

    def __init__(
        self,
        *,
        runtime_root: Path,
        repo_root: Path,
        db_path: Path,
        carrier_repo: Path,
        router_path: Path,
    ) -> None:
        self.runtime_root = runtime_root
        self.store = UnifiedStore(db_path, repo_root / "schema")
        router = json.loads(router_path.read_text(encoding="utf-8"))
        self.organs = {str(o["organ_id"]): o for o in router.get("organs", ())}
        # Use a separate checkout root from the active dispatcher. Read-side receipt
        # reconciliation must never race the relay's control/results worktrees.
        self.transport = GitBranchTransport(
            carrier_repo=carrier_repo,
            work_root=runtime_root / "reconcile_git",
            poll_seconds=0.5,
        )
        (runtime_root / "relay_results").mkdir(parents=True, exist_ok=True)

    def _target(self, organ_id: str) -> BridgeTarget | None:
        cfg = self.organs.get(organ_id)
        if not cfg or cfg.get("kind") != "host_frankenstein":
            return None
        try:
            return BridgeTarget(
                organ_id=organ_id,
                owner_id=str(cfg["owner_id"]),
                machine_id=str(cfg["machine_id"]),
                control_branch=str(cfg["control_branch"]),
                results_branch=str(cfg["results_branch"]),
            )
        except KeyError:
            return None

    def _unknown_rows(self, limit: int = 32) -> list[dict[str, Any]]:
        with self.store.connect() as con:
            rows = con.execute(
                """
                SELECT r.effect_id,r.organ_id,r.command_digest,r.created_at,
                       e.request_digest,e.payload_json,e.owner_id,e.machine_id
                  FROM relay_ledger r
                  JOIN effect_intent e ON e.effect_id=r.effect_id
                 WHERE r.state='UNKNOWN' AND r.organ_id LIKE 'host:%'
                 ORDER BY r.updated_at ASC,r.effect_id ASC
                 LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def _read_late_receipt(self, target: BridgeTarget, command_id: str) -> tuple[dict[str, Any], str] | None:
        repo = self.transport._checkout(target.results_branch)
        self.transport._refresh(repo, target.results_branch)
        path = repo / "local_bridge" / "results" / "receipts" / f"{command_id}.json"
        if not path.exists():
            return None
        return validate_host_receipt(target, command_id, path.read_text(encoding="utf-8"))

    def _apply(self, row: dict[str, Any], target: BridgeTarget, receipt: dict[str, Any], receipt_digest: str) -> dict[str, Any]:
        effect_id = str(row["effect_id"])
        command_id = effect_command_id(effect_id)
        intent = json.loads(str(row["payload_json"]))
        task = intent.get("task") if isinstance(intent.get("task"), dict) else {}
        request = task.get("effect") or task.get("execution") or {}
        status = str(receipt.get("status", "UNKNOWN"))
        promoted_at = now()

        # Atomic compare-and-set. A stale UNKNOWN observation may not overwrite a
        # terminal state established concurrently by another evidence path.
        with self.store.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            current = con.execute(
                "SELECT state FROM relay_ledger WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if current is None or str(current[0]) != "UNKNOWN":
                con.rollback()
                return {"state": "SKIPPED", "effect_id": effect_id, "reason": "NO_LONGER_UNKNOWN"}
            changed = con.execute(
                """
                UPDATE relay_ledger
                   SET command_id=?,state='COMPLETED',receipt_digest=?,last_error=NULL,updated_at=?
                 WHERE effect_id=? AND state='UNKNOWN'
                """,
                (command_id, receipt_digest, promoted_at, effect_id),
            ).rowcount
            if changed != 1:
                con.rollback()
                return {"state": "SKIPPED", "effect_id": effect_id, "reason": "UNKNOWN_CAS_LOST"}
            con.execute(
                "UPDATE effect_intent SET dispatch_state='COMPLETED',updated_at=? WHERE effect_id=?",
                (promoted_at, effect_id),
            )
            con.commit()

        self.store.record_effect_receipt(
            effect_id=effect_id,
            subject_id=str(row["organ_id"]),
            owner_id=target.owner_id,
            machine_id=target.machine_id,
            runtime_epoch_id=str(intent.get("runtime_epoch_id")) if intent.get("runtime_epoch_id") else None,
            action_kind=str(request.get("op", "UNKNOWN")),
            request_digest=str(row["request_digest"]),
            result_digest=receipt_digest,
            status=status,
            requested_at=str(row["created_at"]),
            completed_at=promoted_at,
            receipt_locator=command_id,
            metadata={**receipt, "reconciled_from_unknown": True, "automatic_replay": False},
        )
        self.store.bridge_message(
            direction="IN",
            sender=str(row["organ_id"]),
            recipient="omega",
            kind="LATE_EFFECT_RECEIPT",
            payload=receipt,
            correlation_id=effect_id,
        )
        result = {
            "state": "COMPLETED",
            "effect_id": effect_id,
            "organ_id": str(row["organ_id"]),
            "effect_status": status,
            "receipt_digest": receipt_digest,
            "host_receipt": receipt,
            "reconciled_from_unknown": True,
            "automatic_replay": False,
        }
        _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
        return result

    def run_once(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for row in self._unknown_rows():
            effect_id = str(row["effect_id"])
            target = self._target(str(row["organ_id"]))
            if target is None:
                continue
            command_id = effect_command_id(effect_id)
            try:
                found = self._read_late_receipt(target, command_id)
                if found is None:
                    continue
                receipt, receipt_digest = found
                results.append(self._apply(row, target, receipt, receipt_digest))
            except Exception as exc:
                _atomic_json(
                    self.runtime_root / "relay_results" / f"RECONCILE_ERROR_{effect_id}.json",
                    {
                        "at": now(),
                        "effect_id": effect_id,
                        "organ_id": str(row["organ_id"]),
                        "error": f"{type(exc).__name__}:{exc}",
                        "state_preserved": "UNKNOWN",
                        "automatic_replay": False,
                    },
                )
        return results

    def run_forever(self, interval: float) -> None:
        while True:
            self.run_once()
            time.sleep(max(2.0, interval))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/oMEGA"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--carrier-repo", default=os.getenv("OMEGA_CARRIER_REPO", "/workspace/clay-global-research-entity"))
    ap.add_argument("--router", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/oMEGA/config/organ_router.json"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_RECEIPT_RECONCILE_INTERVAL", "15")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    reconciler = ReceiptReconciler(
        runtime_root=Path(args.runtime_root),
        repo_root=Path(args.repo_root),
        db_path=Path(args.db),
        carrier_repo=Path(args.carrier_repo),
        router_path=Path(args.router),
    )
    if args.once:
        print(json.dumps(reconciler.run_once(), ensure_ascii=False, indent=2))
        return 0
    reconciler.run_forever(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
