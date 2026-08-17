from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .adapters import ClaudeCodeInference
from .agency import AgencyState
from .effects import EffectGate, EffectRequest
from .entityos_bridge import EntityOSBridge
from .identity import CANONICAL_TERMINAL_NAMES, IdentityRouter
from .retrieval import WorldAssembler
from .store import UnifiedDB


class UserHomeClaudeCodeInference(ClaudeCodeInference):
    """Headless Claude cognition using the same canonical per-user HOME as its terminal.

    This lets background goal work reuse the authenticated Claude subscription/OAuth
    identity already owned by that user's permanent ClayVerse terminal without
    attaching to tmux or inheriting the service account's unrelated HOME.
    """

    def __init__(self, home: str | Path, **kwargs):
        self.user_home = str(Path(home))
        super().__init__(**kwargs)

    def _subprocess_env(self) -> dict[str, str]:
        env = super()._subprocess_env()
        env["HOME"] = self.user_home
        return env


class UserHomeClaudeInferenceRouter:
    """Select one headless cognition adapter from canonical goal ownership."""

    def __init__(self, state_root: str | Path):
        self.state_root = Path(state_root)
        self._adapters: dict[str, UserHomeClaudeCodeInference] = {}

    def _adapter(self, user_id: str) -> UserHomeClaudeCodeInference:
        if user_id not in CANONICAL_TERMINAL_NAMES:
            raise PermissionError("unknown autonomous goal owner")
        if user_id not in self._adapters:
            home = self.state_root / "users" / user_id / "home"
            self._adapters[user_id] = UserHomeClaudeCodeInference(home)
        return self._adapters[user_id]

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        if not isinstance(world, dict):
            raise RuntimeError("autonomous world must be an object")
        work = world.get("autonomous_work_item")
        if not isinstance(work, dict):
            raise RuntimeError("autonomous work item missing")
        user_id = work.get("user_id")
        if not isinstance(user_id, str):
            raise RuntimeError("autonomous goal owner missing")
        return self._adapter(user_id).reason(world, observation)


class AutonomyRunner:
    """Bounded Plan -> Act -> Observe -> Adjust loop over persisted goals.

    The LLM chooses the next proposal. UnifiedDB chooses runnable work and limits;
    EffectGate alone can turn an effect intent into an observed action. The runner
    never infers success from fluent text and never marks milestones PASSED.
    """

    def __init__(self, db: UnifiedDB, inference, *, entityos_bridge: EntityOSBridge | None = None):
        self.db = db
        self.inference = inference
        self.agency = AgencyState(db)
        self.world = WorldAssembler(db)
        self.effects = EffectGate(db, allow_process=False, entityos_bridge=entityos_bridge)

    @staticmethod
    def _observation(work) -> str:
        return (
            "AUTONOMOUS_GOAL_CYCLE\n"
            f"goal_id={work.goal_id}\n"
            f"milestone_id={work.milestone_id}\n"
            f"phase={work.phase}\n"
            f"goal={work.goal_title}\n"
            f"objective={work.objective}\n"
            f"goal_success_criteria={work.success_criteria}\n"
            f"milestone={work.milestone_title}\n"
            f"milestone_acceptance_criteria={work.acceptance_criteria}\n"
            f"attempt={work.attempt_ordinal}\n\n"
            "Choose exactly one next bounded move toward this milestone from the supplied canonical state. "
            "Use only capabilities listed in runtime_capabilities. If a real action is needed, propose one EffectGate intent. "
            "If no further executable move is justified from current evidence, return effect=null and explain what is ready "
            "for review or what is missing. Never claim an action happened merely because you proposed it."
        )

    def run_cycle(self) -> dict[str, Any]:
        cycle_id = self.agency.begin_cycle()
        if cycle_id is None:
            return {"status":"idle","cycle_id":None,"steps":0,"effects":0}

        completed = 0
        effects = 0
        try:
            while True:
                work = self.agency.claim_next(cycle_id)
                if work is None:
                    break
                session_id = self.db.ensure_session(work.user_id, CANONICAL_TERMINAL_NAMES[work.user_id])
                generation = self.db.session_generation(session_id)
                self.db.assert_live_generation(session_id,generation)

                observation = self._observation(work)
                observation_turn_id = self.db.append_turn(
                    session_id,
                    work.user_id,
                    "system",
                    observation,
                    provenance={
                        "source":"agency-daemon",
                        "phase":"autonomous-observation",
                        "goal_id":work.goal_id,
                        "milestone_id":work.milestone_id,
                        "attempt_id":work.attempt_id,
                        "cycle_id":cycle_id,
                    },
                )
                world = self.world.assemble(session_id, [])
                world["agency"] = self.agency.snapshot(
                    user_id=work.user_id,
                    max_goals=8,
                    max_attempts_per_milestone=5,
                )
                world["autonomous_work_item"] = asdict(work)
                world["runtime_capabilities"] = list(self.effects.available_capabilities())
                world["grounding"] = {
                    "observation_turn_id":observation_turn_id,
                    "generation":generation,
                    "effect_truth":"Only EffectGate verified outcome is operational truth.",
                }

                try:
                    decision = self.inference.reason(world, observation)
                except Exception as exc:
                    self.agency.abort_attempt(work.attempt_id, f"inference:{type(exc).__name__}")
                    self.agency.close_cycle(cycle_id, f"inference_failure:{type(exc).__name__}")
                    return {
                        "status":"blocked",
                        "cycle_id":cycle_id,
                        "steps":completed,
                        "effects":effects,
                        "reason":f"inference_failure:{type(exc).__name__}",
                    }

                assistant_turn_id = self.db.append_turn(
                    session_id,
                    work.user_id,
                    "assistant",
                    str(decision.get("text", "")),
                    provenance={
                        "source":"agency-daemon",
                        "phase":"autonomous-proposal",
                        "goal_id":work.goal_id,
                        "milestone_id":work.milestone_id,
                        "attempt_id":work.attempt_id,
                        "cycle_id":cycle_id,
                        "inference_receipt":decision.get("inference_receipt"),
                    },
                )

                effect_id = None
                outcome = None
                effect_exception = None
                effect = decision.get("effect")
                if effect is not None:
                    _, current_effects = self.agency.cycle_counts(cycle_id)
                    limit = int(self.agency.policy()["max_effects_per_cycle"])
                    if current_effects >= limit:
                        self.agency.abort_attempt(work.attempt_id,"effect_limit")
                        self.agency.close_cycle(cycle_id,"effect_limit")
                        break
                    try:
                        effect_id,outcome = self.effects.execute(
                            EffectRequest(
                                work.user_id,
                                session_id,
                                effect["capability"],
                                effect["target"],
                                effect.get("argv"),
                                generation,
                            ),
                            episode_id=None,
                        )
                    except Exception as exc:
                        effect_exception = type(exc).__name__
                        outcome = {"ok":False,"error":effect_exception,"boundary":"EffectGate"}

                status = self.agency.complete_attempt(work.attempt_id, decision, effect_id, outcome)
                completed += 1
                if effect_id is not None:
                    effects += 1
                self.db.append_turn(
                    session_id,
                    work.user_id,
                    "system",
                    json.dumps(
                        {
                            "agency_attempt_id":work.attempt_id,
                            "assistant_turn_id":assistant_turn_id,
                            "effect_id":effect_id,
                            "outcome":outcome,
                            "attempt_status":status,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",",":"),
                    ),
                    causal_refs=[effect_id] if effect_id else [],
                    provenance={
                        "source":"agency-daemon",
                        "phase":"autonomous-observe",
                        "goal_id":work.goal_id,
                        "milestone_id":work.milestone_id,
                        "attempt_id":work.attempt_id,
                        "cycle_id":cycle_id,
                    },
                )
                if effect_exception is not None:
                    # EffectGate/runtime exceptions are not a reason to retry in a tight
                    # inner loop. Persist the failed observation and defer to next cycle.
                    self.agency.close_cycle(cycle_id, f"effect_exception:{effect_exception}")
                    break

            self.agency.close_cycle(cycle_id,"cycle_complete")
            steps,effect_count = self.agency.cycle_counts(cycle_id)
            return {"status":"closed","cycle_id":cycle_id,"steps":steps,"effects":effect_count}
        except Exception:
            self.agency.close_cycle(cycle_id,"runner_exception")
            raise


class AutonomyDaemon:
    """Periodic server-side driver for the bounded goal runner.

    It owns a separate UnifiedDB connection, sleeps between cycles, performs no model
    call when there is no runnable work, and can be stopped synchronously at shutdown.
    """

    def __init__(
        self,
        state_root: str,
        inference_factory: Callable[[], Any],
        *,
        entityos_bridge: EntityOSBridge | None = None,
    ):
        self.state_root = state_root
        self.inference_factory = inference_factory
        self.entityos_bridge = entityos_bridge
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="clayverse-autonomy", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        db_path = os.path.join(self.state_root,"unified.db")
        while not self._stop.is_set():
            interval = 60.0
            db = None
            try:
                db = UnifiedDB(db_path)
                IdentityRouter(db,{})
                agency = AgencyState(db)
                interval = float(agency.policy()["cycle_interval_seconds"])
                if agency.has_runnable_work():
                    runner = AutonomyRunner(db,self.inference_factory(),entityos_bridge=self.entityos_bridge)
                    result = runner.run_cycle()
                    if result.get("status") != "idle":
                        db.checkpoint("autonomy-cycle")
            except Exception as exc:
                print(
                    json.dumps({"service":"clayverse-autonomy","status":"cycle_error","error":type(exc).__name__}),
                    flush=True,
                )
            finally:
                if db is not None:
                    db.close()
            self._stop.wait(max(1.0,interval))
