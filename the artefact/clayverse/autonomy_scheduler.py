from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable

from .adapters import ClaudeCodeInference
from .agency import AgencyView
from .autonomy import AutonomyBudgetExceeded, AutonomyController, CompletionNotVerified
from .effects import EffectGate, EffectRequest
from .entityos_bridge import EntityOSBridge
from .identity import CANONICAL_TERMINAL_NAMES, IdentityRouter
from .retrieval import WorldAssembler
from .store import UnifiedDB
from .workspace import Workspace

STEP_PREFIX = {
    "STEP:REASON": "reason",
    "STEP:WAIT": "wait",
    "STEP:COMPLETE_CANDIDATE": "complete_candidate",
    "STEP:EFFECT": "effect",
}
MAX_STEPS_PER_WAKE = 8


class UserHomeClaudeCodeInference(ClaudeCodeInference):
    """Headless cognition using the canonical goal owner's terminal HOME."""

    def __init__(self, home: str | Path, **kwargs):
        self.user_home = str(Path(home))
        super().__init__(**kwargs)

    def _subprocess_env(self) -> dict[str, str]:
        env = super()._subprocess_env()
        env["HOME"] = self.user_home
        return env


class UserHomeClaudeInferenceRouter:
    def __init__(self, state_root: str | Path):
        self.state_root = Path(state_root)
        self._adapters: dict[str, UserHomeClaudeCodeInference] = {}

    def adapter(self, user_id: str) -> UserHomeClaudeCodeInference:
        if user_id not in CANONICAL_TERMINAL_NAMES:
            raise PermissionError("unknown autonomous goal owner")
        if user_id not in self._adapters:
            home = self.state_root / "users" / user_id / "home"
            self._adapters[user_id] = UserHomeClaudeCodeInference(home)
        return self._adapters[user_id]


class AutonomySchedulerRunner:
    """One bounded wake of the canonical AutonomyController.

    This object owns no durable mind/state. It reloads canonical goals each step,
    asks cognition for one schema-constrained proposal, persists the proposal as an
    AutonomyController step, routes operational effects through EffectGate, re-ingests
    the observed outcome, and stops at controller/budget/verification boundaries.
    """

    def __init__(
        self,
        db: UnifiedDB,
        inference_router: UserHomeClaudeInferenceRouter,
        *,
        entityos_bridge: EntityOSBridge | None = None,
    ):
        self.db = db
        self.controller = AutonomyController(db)
        self.agency = AgencyView(db)
        self.world = WorldAssembler(db)
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process=False, entityos_bridge=entityos_bridge)
        self.inference_router = inference_router

    @staticmethod
    def _parse_step(decision: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
        text = str(decision.get("text", ""))
        first, _, rest = text.partition("\n")
        kind = STEP_PREFIX.get(first.strip())
        effect = decision.get("effect")
        if effect is not None:
            if kind != "effect":
                raise RuntimeError("effect proposal must use STEP:EFFECT marker")
        elif kind == "effect":
            raise RuntimeError("STEP:EFFECT requires an effect proposal")
        if kind is None:
            raise RuntimeError("autonomy step marker missing")
        description = rest.strip() or first.strip()
        return kind, description, effect

    @staticmethod
    def _observation(goal: dict[str, Any]) -> str:
        return (
            "AUTONOMOUS_GOAL_WAKE\n"
            f"goal_id={goal['goal_id']}\n"
            f"objective={goal['objective']}\n"
            f"status={goal['status']}\n"
            f"budget={json.dumps(goal['budget'], sort_keys=True)}\n"
            f"counters={json.dumps(goal['counters'], sort_keys=True)}\n\n"
            "Choose exactly one next bounded step from canonical state. The first line of text MUST be exactly one of: "
            "STEP:REASON, STEP:EFFECT, STEP:WAIT, STEP:COMPLETE_CANDIDATE. "
            "Use STEP:EFFECT only with one admitted EffectGate intent. Use STEP:COMPLETE_CANDIDATE only when current evidence "
            "justifies testing the independent completion contract. A proposal is never evidence and must not claim execution."
        )

    def run_wake(self) -> dict[str, Any]:
        executed = 0
        effects = 0
        while executed < MAX_STEPS_PER_WAKE:
            goal = self.controller.next_runnable()
            if goal is None:
                return {"status": "idle" if executed == 0 else "closed", "steps": executed, "effects": effects}

            user_id = goal["user_id"]
            session_id = goal["session_id"]
            generation = int(goal["generation"])
            self.db.assert_live_generation(session_id, generation)
            observation = self._observation(goal)
            observation_turn_id = self.db.append_turn(
                session_id,
                user_id,
                "system",
                observation,
                provenance={
                    "source": "autonomy-scheduler",
                    "phase": "proposal-observation",
                    "goal_id": goal["goal_id"],
                    "generation": generation,
                },
            )
            ws = self.workspace.open(session_id, observation_turn_id, observation, [])
            world = self.world.assemble(session_id, [])
            world["agency"] = self.agency.snapshot(user_id=user_id)
            world["autonomous_goal"] = goal
            world["runtime_capabilities"] = list(self.effects.available_capabilities())
            world["autonomy_protocol"] = {
                "markers": list(STEP_PREFIX),
                "effect_truth": "Only persisted verified EffectGate outcome is operational truth.",
                "completion_truth": "Only AutonomyController completion contract evidence can complete the goal.",
            }

            inference = self.inference_router.adapter(user_id)
            try:
                decision = inference.reason(world, observation)
                kind, description, effect = self._parse_step(decision)
            except Exception as exc:
                self.db.append_turn(
                    session_id,
                    user_id,
                    "system",
                    json.dumps({"goal_id": goal["goal_id"], "scheduler_blocked": type(exc).__name__}, sort_keys=True),
                    provenance={"source": "autonomy-scheduler", "phase": "proposal-blocked"},
                )
                return {"status": "blocked", "steps": executed, "effects": effects, "reason": type(exc).__name__}

            self.db.append_turn(
                session_id,
                user_id,
                "assistant",
                decision.get("text", ""),
                provenance={
                    "source": "autonomy-scheduler",
                    "phase": "proposal",
                    "goal_id": goal["goal_id"],
                    "workspace_episode_id": ws["episode_id"],
                },
            )

            try:
                step = self.controller.propose_step(
                    goal["goal_id"],
                    kind,
                    description,
                    effect=effect,
                    expected_generation=generation,
                )
            except (AutonomyBudgetExceeded, Exception) as exc:
                return {"status": "blocked", "steps": executed, "effects": effects, "reason": type(exc).__name__}

            if kind == "complete_candidate":
                try:
                    completed = self.controller.verify_completion(goal["goal_id"], expected_generation=generation)
                    self.db.append_turn(
                        session_id,
                        user_id,
                        "system",
                        json.dumps(completed, sort_keys=True),
                        provenance={"source": "autonomy-scheduler", "phase": "completion-verified"},
                    )
                    executed += 1
                    continue
                except CompletionNotVerified:
                    return {"status": "waiting_for_evidence", "steps": executed + 1, "effects": effects, "goal_id": goal["goal_id"]}

            admitted = self.controller.admit_step(
                goal["goal_id"], step["step_id"], expected_generation=generation
            )
            self.workspace.select(
                ws["episode_id"],
                "request_effect" if kind == "effect" else "respond",
            )

            if kind == "effect":
                try:
                    effect_id, outcome = self.effects.execute(
                        EffectRequest(
                            user_id,
                            session_id,
                            admitted["effect"]["capability"],
                            admitted["effect"]["target"],
                            admitted["effect"].get("argv"),
                            generation,
                        ),
                        ws["episode_id"],
                    )
                    result = self.controller.record_effect_result(
                        goal["goal_id"], step["step_id"], effect_id, expected_generation=generation
                    )
                except Exception as exc:
                    try:
                        self.controller.record_step_failure(
                            goal["goal_id"], step["step_id"], type(exc).__name__, expected_generation=generation
                        )
                    except Exception:
                        pass
                    return {"status": "blocked", "steps": executed + 1, "effects": effects, "reason": type(exc).__name__}
                effects += 1
                executed += 1
                self.db.append_turn(
                    session_id,
                    user_id,
                    "system",
                    json.dumps({"effect_id": effect_id, "outcome": outcome, "autonomy": result}, ensure_ascii=False, sort_keys=True),
                    causal_refs=[effect_id],
                    provenance={"source": "autonomy-scheduler", "phase": "effect-observed", "goal_id": goal["goal_id"]},
                )
                try:
                    self.controller.verify_completion(goal["goal_id"], expected_generation=generation)
                except CompletionNotVerified:
                    pass
                continue

            self.controller.record_reason_success(
                goal["goal_id"], step["step_id"], expected_generation=generation
            )
            executed += 1
            if kind == "wait":
                return {"status": "waiting", "steps": executed, "effects": effects, "goal_id": goal["goal_id"]}

        return {"status": "wake_limit", "steps": executed, "effects": effects}


class AutonomyScheduler:
    """Process-local timer trigger for the canonical controller; no durable mind."""

    def __init__(
        self,
        state_root: str,
        *,
        entityos_bridge: EntityOSBridge | None = None,
        interval_seconds: float = 60.0,
    ):
        self.state_root = state_root
        self.entityos_bridge = entityos_bridge
        self.interval_seconds = max(1.0, float(interval_seconds))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="clayverse-autonomy-scheduler", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        db_path = os.path.join(self.state_root, "unified.db")
        router = UserHomeClaudeInferenceRouter(self.state_root)
        while not self._stop.is_set():
            db = None
            try:
                db = UnifiedDB(db_path)
                IdentityRouter(db, {})
                controller = AutonomyController(db)
                if controller.next_runnable() is not None:
                    result = AutonomySchedulerRunner(
                        db,
                        router,
                        entityos_bridge=self.entityos_bridge,
                    ).run_wake()
                    if result["status"] != "idle":
                        db.checkpoint("autonomy-scheduler-wake")
            except Exception as exc:
                print(json.dumps({"service": "clayverse-autonomy", "status": "wake_error", "error": type(exc).__name__}), flush=True)
            finally:
                if db is not None:
                    db.close()
            self._stop.wait(self.interval_seconds)
