from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from .cortex import CortexCore, CortexEvent, stable_digest
from .grid_runtime_v2 import Runtime as RuntimeV2
from .unified_store import UnifiedStore, now


class Runtime(RuntimeV2):
    """OMEGA GRID v3: canonical GRID plus native Cortex projection.

    The inherited runtime SQLite is an operational scheduler journal, not the project-
    wide authority. OMEGA UnifiedDB remains the convergence substrate. Effects are
    dispatched at most once per task: OPEN -> DISPATCHED, then relay receipts move the
    task to a terminal evidence state. UNKNOWN is never auto-replayed.

    Cortex is integrated *inside this same GRID runtime*. It is not a second daemon,
    watcher or workspace. Typed Cortex events are projected into StateAtoms and can add
    CORTEX proposals to the existing GRID competition. Retina feedback is emitted as a
    typed inference directive only; camera/device effects still require normal effect
    authority.

    Pure cognition/planning tasks are not emitted as fake host effects. They are handed
    once to the ChatGPT master organ, which may return evidence-bound candidate actions;
    any real effect still has to re-enter the normal GRID -> alignment -> relay path.
    """

    TERMINAL_TASK_STATES = {"COMPLETED", "EFFECT_FAILED", "EFFECT_UNKNOWN", "BLOCKED", "FAILED"}

    def __init__(self, root: Path, interval: float, router_config: Path, db_path: Path, repo_root: Path) -> None:
        super().__init__(root, interval, router_config)
        self.store = UnifiedStore(db_path, repo_root / "schema")
        sources = json.loads((repo_root / "config" / "sources.json").read_text(encoding="utf-8"))
        self.store.register_sources(sources.get("sources", ()))
        self.master_interval = float(os.getenv("OMEGA_MASTER_COGNITION_INTERVAL", "1800"))
        (self.root / "master_bridge").mkdir(parents=True, exist_ok=True)

        # Native Cortex integration uses the existing GRID cadence. No second loop.
        self.cortex = CortexCore()
        for name in (
            "cortex_inbox",
            "cortex_candidates",
            "cortex_feedback",
            "cortex_projections",
            "cortex_rejected",
            "cortex_state",
        ):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self._last_cortex_state_digest: str | None = None

    @staticmethod
    def _atomic_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)

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

    @staticmethod
    def _is_executable_task(task: dict[str, Any]) -> bool:
        return isinstance(task.get("effect"), dict) or isinstance(task.get("execution"), dict)

    def ingest_cortex_inbox(self) -> int:
        """Consume typed Cortex events exactly once into the native Cortex.

        The inbox is a transport boundary, not a second cognition loop. Producers such
        as Retina/WorldModel can drop an OMEGA_CORTEX_EVENT/v1 packet here; this method
        is called synchronously at the beginning of the existing GRID frame.
        """
        count = 0
        for path in sorted((self.root / "cortex_inbox").glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if raw.get("schema") != "OMEGA_CORTEX_EVENT/v1":
                    raise ValueError("unsupported_cortex_event_schema")
                payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
                provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
                event = CortexEvent(
                    event_id=str(raw.get("event_id") or ""),
                    kind=str(raw.get("kind") or ""),
                    causal_id=str(raw.get("causal_id") or ""),
                    meta_order=int(raw.get("meta_order", -1)),
                    evidence_class=str(raw.get("evidence_class") or "UNKNOWN"),
                    source=str(raw.get("source") or ""),
                    payload=payload,
                    provenance=provenance,
                )
                projection = self.cortex.ingest(event)
                projection_dict = projection.as_dict()
                self._atomic_json(
                    self.root / "cortex_projections" / f"{event.event_id}.json",
                    projection_dict,
                )

                if projection.retina_feedback is not None:
                    feedback = projection.retina_feedback.as_dict()
                    self._atomic_json(
                        self.root / "cortex_feedback" / f"{projection.retina_feedback.feedback_id}.json",
                        {
                            "schema": "OMEGA_RETINA_FEEDBACK/v1",
                            "created_at": now(),
                            "effect_authority": False,
                            **feedback,
                        },
                    )

                for proposal in projection.grid_proposals:
                    candidate_id = "cortex_" + stable_digest(
                        {
                            "event_id": event.event_id,
                            "proposal": proposal,
                        }
                    )[:24]
                    self._atomic_json(
                        self.root / "cortex_candidates" / f"{candidate_id}.json",
                        {
                            "schema": "OMEGA_CORTEX_GRID_CANDIDATE/v1",
                            "candidate_id": candidate_id,
                            "source_event_id": event.event_id,
                            "causal_id": event.causal_id,
                            "meta_order": event.meta_order,
                            "state": "OPEN",
                            "proposal": dict(proposal),
                            "effect_authority": False,
                            "created_at": now(),
                        },
                    )

                path.rename(path.with_suffix(".consumed"))
                count += 1
            except Exception as exc:
                reject = {
                    "schema": "OMEGA_CORTEX_REJECTION/v1",
                    "source_path": str(path),
                    "error": f"{type(exc).__name__}:{exc}",
                    "rejected_at": now(),
                }
                reject_id = stable_digest(reject)[:24]
                self._atomic_json(self.root / "cortex_rejected" / f"{reject_id}.json", reject)
                try:
                    path.rename(path.with_suffix(".rejected"))
                except OSError:
                    pass
        return count

    def open_cortex_candidates(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for path in sorted((self.root / "cortex_candidates").glob("*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                if item.get("schema") != "OMEGA_CORTEX_GRID_CANDIDATE/v1":
                    continue
                if item.get("state") != "OPEN":
                    continue
                proposal = item.get("proposal") if isinstance(item.get("proposal"), dict) else {}
                if proposal.get("effect_authority") is not False:
                    continue
                row = dict(item)
                row["_path"] = str(path)
                out.append(row)
            except Exception:
                continue
        return out

    def _consume_cortex_candidate(self, candidate_id: str) -> None:
        path = self.root / "cortex_candidates" / f"{candidate_id}.json"
        if not path.exists():
            return
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            item["state"] = "SELECTED"
            item["selected_at"] = now()
            selected_path = path.with_suffix(".selected")
            self._atomic_json(selected_path, item)
            path.unlink(missing_ok=True)
        except Exception:
            return

    def _persist_cortex_state(self, epoch_id: str) -> None:
        snapshot = self.cortex.snapshot()
        digest_value = str(snapshot.get("state_digest") or "")
        state_path = self.root / "cortex_state" / "STATE.json"
        self._atomic_json(state_path, snapshot)
        if digest_value and digest_value != self._last_cortex_state_digest:
            self.store.record_observation(
                source_id="runtime:omega-vps",
                subject_id="omega:cortex",
                owner_id="omega",
                machine_id="omega-vps",
                runtime_epoch_id=epoch_id,
                payload=snapshot,
                observed_at=now(),
                evidence_class="RUNTIME_RECEIPT",
                raw_locator=str(state_path),
                authority_rank=75,
                confidence=1.0,
            )
            self._last_cortex_state_digest = digest_value

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
        master_due = self._master_due()

        if task:
            executable = self._is_executable_task(task)
            explicit_master = bool(task.get("needs_master", False) or task.get("master_reasoning", False))

            for proposal in proposals:
                if executable and proposal["cell_id"] == "HOST_SCOUT":
                    proposal["score"] = max(float(proposal["score"]), 0.95)
                    proposal["payload"] = {"kind": "organ_route", "task": task}

                if (explicit_master or not executable) and proposal["cell_id"] == "MASTER_BRIDGE":
                    proposal["score"] = max(float(proposal["score"]), 0.92)
                    proposal["payload"] = {
                        "kind": "master_bridge",
                        "action": "resolve_open_task_to_evidence_bound_actions",
                        "task": task,
                    }

                if master_due and proposal["cell_id"] == "MASTER_BRIDGE" and not (explicit_master or not executable):
                    proposal["score"] = max(float(proposal["score"]), 0.70)
                    proposal["payload"] = {"kind": "master_bridge", "action": "periodic_master_cognition"}
        elif master_due:
            for proposal in proposals:
                if proposal["cell_id"] == "MASTER_BRIDGE":
                    proposal["score"] = max(float(proposal["score"]), 0.70)
                    proposal["payload"] = {"kind": "master_bridge", "action": "periodic_master_cognition"}

        # Cortex contributes to the *existing* competition. It does not own a loop or
        # bypass executable-task priority. A visual/cognitive candidate must earn its
        # score, while host effects remain at 0.95 and planning/master tasks at 0.92.
        for candidate in self.open_cortex_candidates()[:8]:
            source = candidate.get("proposal") if isinstance(candidate.get("proposal"), dict) else {}
            utility = max(0.0, min(0.91, float(source.get("utility", 0.0) or 0.0)))
            proposals.append(
                {
                    "proposal_id": "prop_cortex_" + uuid.uuid4().hex,
                    "cell_id": "CORTEX",
                    "score": round(utility, 6),
                    "payload": {
                        "kind": "cortex_projection",
                        "candidate_id": candidate.get("candidate_id"),
                        "source_event_id": candidate.get("source_event_id"),
                        "causal_id": candidate.get("causal_id"),
                        "meta_order": candidate.get("meta_order"),
                        "proposal": source,
                        "effect_authority": False,
                    },
                }
            )
        return proposals

    def realize(self, selected: dict[str, Any], frame_id: str) -> dict[str, Any]:
        cell = selected["cell_id"]
        payload = selected["payload"]
        if cell == "CORTEX":
            if payload.get("effect_authority") is not False:
                return {"broadcast": "cortex proposal blocked", "error": "cortex_effect_authority_forbidden"}
            candidate_id = str(payload.get("candidate_id") or "")
            proposal = payload.get("proposal") if isinstance(payload.get("proposal"), dict) else {}
            if candidate_id:
                self._consume_cortex_candidate(candidate_id)
            return {
                "broadcast": "cortex proposal selected by canonical GRID",
                "frame_id": frame_id,
                "candidate_id": candidate_id,
                "cortex": proposal,
                "effect_authority": False,
            }

        if cell == "HOST_SCOUT":
            task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
            task_id = str(task.get("task_id") or "")
            if task_id and not self._is_executable_task(task):
                self._task_state(task_id, "WAITING_MASTER")
                message_payload = {
                    "frame_id": frame_id,
                    "reason": "defensive_non_executable_host_route_redirect",
                    "task": task,
                    "state": self.snapshot_state(),
                    "instruction": "Resolve this planning-only task into evidence-bound candidate actions. Do not self-promote effects.",
                }
                self.emit_outbox("MASTER_COGNITION_UPDATE", message_payload)
                self._mark_master_emit()
                return {"broadcast": "non-executable host route redirected to master cognition", "outbox": True, "task_id": task_id}

            result = super().realize(selected, frame_id)
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
        self.ingest_cortex_inbox()
        self.reconcile_relay_results()
        self.reconcile_master_responses()
        frame_id = super().frame(epoch_id, trigger)
        self._persist_cortex_state(epoch_id)
        status_path = self.root / "STATUS.json"
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"frame_id": frame_id}
        status["cortex"] = {
            "state_digest": self.cortex.snapshot().get("state_digest"),
            "open_candidates": len(self.open_cortex_candidates()),
            "feedback_files": len(list((self.root / "cortex_feedback").glob("*.json"))),
        }
        self._atomic_json(status_path, status)
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
