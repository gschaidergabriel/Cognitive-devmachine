from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from .grid_runtime_v2 import Runtime as RuntimeV2
from .unified_store import UnifiedStore, now


class Runtime(RuntimeV2):
    """OMEGA GRID v3: executable-task lifecycle + canonical evidence mirroring.

    The inherited runtime SQLite is an operational scheduler journal, not the project-
    wide authority. OMEGA UnifiedDB remains the convergence substrate. Effects are
    dispatched at most once per task: OPEN -> DISPATCHED, then relay receipts move the
    task to a terminal evidence state. UNKNOWN is never auto-replayed.
    """

    TERMINAL_TASK_STATES = {"COMPLETED", "EFFECT_FAILED", "EFFECT_UNKNOWN", "BLOCKED", "FAILED"}

    def __init__(self, root: Path, interval: float, router_config: Path, db_path: Path, repo_root: Path) -> None:
        super().__init__(root, interval, router_config)
        self.store = UnifiedStore(db_path, repo_root / "schema")
        sources = json.loads((repo_root / "config" / "sources.json").read_text(encoding="utf-8"))
        self.store.register_sources(sources.get("sources", ()))
        self.master_interval = float(os.getenv("OMEGA_MASTER_COGNITION_INTERVAL", "1800"))
        (self.root / "master_bridge").mkdir(parents=True, exist_ok=True)

    def _task_state(self, task_id: str, state: str) -> None:
        with self.connect() as con:
            con.execute("UPDATE task SET state=?,updated_at=? WHERE task_id=?", (state, now(), task_id))

    def _master_due(self) -> bool:
        marker = self.root / "master_bridge" / "LAST_GRID_MASTER_EMIT"
        try:
            age = time.time() - float(marker.read_text(encoding="utf-8").strip())
            return age >= self.master_interval
        except Exception:
            return True

    def _mark_master_emit(self) -> None:
        marker = self.root / "master_bridge" / "LAST_GRID_MASTER_EMIT"
        tmp = marker.with_suffix(".tmp")
        tmp.write_text(str(time.time()), encoding="utf-8")
        os.replace(tmp, marker)

    def reconcile_relay_results(self) -> int:
        changed = 0
        results_dir = self.root / "relay_results"
        for result_path in sorted(results_dir.glob("effect_*.json")):
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                effect_id = str(result["effect_id"])
                intent_path = self.root / "outbox" / f"{effect_id}.json"
                if not intent_path.exists():
                    continue
                intent = json.loads(intent_path.read_text(encoding="utf-8"))
                task = intent.get("task") if isinstance(intent.get("task"), dict) else {}
                task_id = str(task.get("task_id") or "")
                if not task_id:
                    continue
                state = str(result.get("state", "UNKNOWN"))
                effect_status = str(result.get("effect_status", "UNKNOWN"))
                if state == "COMPLETED" and effect_status == "PASS":
                    task_state = "COMPLETED"
                elif state == "COMPLETED":
                    task_state = "EFFECT_FAILED"
                elif state == "UNKNOWN":
                    task_state = "EFFECT_UNKNOWN"
                elif state == "BLOCKED":
                    task_state = "BLOCKED"
                else:
                    task_state = "FAILED"
                with self.connect() as con:
                    row = con.execute("SELECT state FROM task WHERE task_id=?", (task_id,)).fetchone()
                if row and str(row[0]) != task_state:
                    self._task_state(task_id, task_state)
                    changed += 1
            except Exception:
                continue
        return changed

    def reconcile_master_responses(self) -> int:
        changed = 0
        submitted = self.root / "master_bridge" / "submitted"
        responses = self.root / "master_bridge" / "responses"
        if not submitted.exists() or not responses.exists():
            return 0
        for response_path in sorted(responses.glob("omega_master_*.json")):
            request_path = submitted / response_path.name
            if not request_path.exists():
                continue
            try:
                req = json.loads(request_path.read_text(encoding="utf-8"))
                outer = req.get("payload") if isinstance(req.get("payload"), dict) else {}
                payload = outer.get("payload") if isinstance(outer.get("payload"), dict) else {}
                task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
                task_id = str(task.get("task_id") or "")
                if not task_id:
                    continue
                with self.connect() as con:
                    row = con.execute("SELECT state FROM task WHERE task_id=?", (task_id,)).fetchone()
                if row and str(row[0]) == "WAITING_MASTER":
                    self._task_state(task_id, "MASTER_RESPONDED")
                    changed += 1
            except Exception:
                continue
        return changed

    def cell_proposals(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        proposals = super().cell_proposals(context)
        tasks = context.get("tasks") or []
        task = tasks[0] if tasks and isinstance(tasks[0], dict) else None
        if task:
            executable = isinstance(task.get("effect"), dict) or isinstance(task.get("execution"), dict)
            needs_host = bool(task.get("required_capabilities")) or bool(task.get("preferred_data_domains")) or executable
            needs_master = bool(task.get("needs_master", False) or task.get("master_reasoning", False))
            for proposal in proposals:
                if needs_host and proposal["cell_id"] == "HOST_SCOUT":
                    proposal["score"] = max(float(proposal["score"]), 0.95 if executable else 0.72)
                    proposal["payload"] = {"kind": "organ_route", "task": task}
                if needs_master and proposal["cell_id"] == "MASTER_BRIDGE":
                    proposal["score"] = max(float(proposal["score"]), 0.90)
                    proposal["payload"] = {"kind": "master_bridge", "action": "publish_state_and_open_questions", "task": task}
        elif self._master_due():
            for proposal in proposals:
                if proposal["cell_id"] == "MASTER_BRIDGE":
                    proposal["score"] = max(float(proposal["score"]), 0.70)
                    proposal["payload"] = {"kind": "master_bridge", "action": "periodic_master_cognition"}
        return proposals

    def realize(self, selected: dict[str, Any], frame_id: str) -> dict[str, Any]:
        cell = selected["cell_id"]
        payload = selected["payload"]
        if cell == "HOST_SCOUT":
            result = super().realize(selected, frame_id)
            task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
            task_id = str(task.get("task_id") or "")
            if task_id and result.get("intent_files") and not result.get("error"):
                self._task_state(task_id, "DISPATCHED")
            return result
        if cell == "MASTER_BRIDGE":
            task = payload.get("task") if isinstance(payload.get("task"), dict) else None
            message_payload = {
                "frame_id": frame_id,
                "reason": payload.get("action"),
                "task": task,
                "state": self.snapshot_state(),
                "instruction": "Review current OMEGA state, resolve the highest-information next step, and return evidence-bound candidate actions. Do not self-promote effects.",
            }
            self.emit_outbox("MASTER_COGNITION_UPDATE", message_payload)
            self._mark_master_emit()
            if task and task.get("task_id"):
                self._task_state(str(task["task_id"]), "WAITING_MASTER")
            return {"broadcast": "master cognition request emitted", "outbox": True, "task_id": task.get("task_id") if task else None}
        return super().realize(selected, frame_id)

    def frame(self, epoch_id: str, trigger: str = "HEARTBEAT") -> str:
        self.reconcile_relay_results()
        self.reconcile_master_responses()
        frame_id = super().frame(epoch_id, trigger)
        status_path = self.root / "STATUS.json"
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"frame_id": frame_id}
        self.store.record_observation(
            source_id="runtime:omega-vps",
            subject_id="omega:grid",
            owner_id="omega",
            machine_id="omega-vps",
            runtime_epoch_id=epoch_id,
            payload=status,
            observed_at=str(status.get("updated_at") or now()),
            evidence_class="RUNTIME_RECEIPT",
            raw_locator=str(status_path),
            authority_rank=80,
            confidence=1.0,
        )
        for organ_id, telemetry in self.read_telemetry().items():
            if isinstance(telemetry, dict):
                self.store.record_telemetry(organ_id, telemetry)
        return frame_id


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_GRID_INTERVAL", "30")))
    ap.add_argument("--router-config", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/omega_runtime/current/config/organ_router.json"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/omega_runtime/current"))
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    rt = Runtime(Path(a.root), a.interval, Path(a.router_config), Path(a.db), Path(a.repo_root))
    if a.once:
        epoch = rt.start_epoch(); rt.frame(epoch, "MANUAL_ONCE"); return 0
    rt.run_forever(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
