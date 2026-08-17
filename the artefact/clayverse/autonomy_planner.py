from __future__ import annotations

import json
from typing import Any

from .autonomy import (
    AutonomyController,
    AutonomyStateError,
    CompletionNotVerified,
)
from .store import UnifiedDB

DECISION_SCHEMA = "ClayVerseAutonomyDecision/v1"
PLANNER_STEP_PREFIX = "AUTONOMY_PLANNER_DECISION:"
DECISION_KINDS = {"reason", "effect", "complete_candidate"}
MAX_DECISION_CHARS = 20_000


class AutonomyDecisionError(RuntimeError):
    pass


class AutonomyPlanner:
    """Compile model planning output into the existing deterministic goal state machine.

    The planner grants no new authority. It creates/adopts only controller-valid steps;
    effects still execute exclusively through request_autonomy_effect/EffectGate.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.controller = AutonomyController(db)

    @staticmethod
    def _decision_object(raw: str) -> dict[str, Any]:
        if not isinstance(raw, str) or not raw or len(raw) > MAX_DECISION_CHARS:
            raise AutonomyDecisionError("invalid planner decision size")
        try:
            value = AutonomyController._loads(raw)
        except Exception as exc:
            raise AutonomyDecisionError("planner decision is not canonical JSON") from exc
        if set(value) != {"schema", "kind", "description", "effect"}:
            raise AutonomyDecisionError("planner decision has unexpected fields")
        if value.get("schema") != DECISION_SCHEMA:
            raise AutonomyDecisionError("planner decision schema mismatch")
        kind = value.get("kind")
        if kind not in DECISION_KINDS:
            raise AutonomyDecisionError("planner decision kind not admitted")
        description = value.get("description")
        if not isinstance(description, str) or not description.strip():
            raise AutonomyDecisionError("planner decision description missing")
        if kind == "effect":
            try:
                value["effect"] = AutonomyController._validated_effect(value.get("effect"))
            except Exception as exc:
                raise AutonomyDecisionError("planner effect proposal invalid") from exc
        elif value.get("effect") is not None:
            raise AutonomyDecisionError("non-effect planner decision contains effect")
        value["description"] = description.strip()
        return value

    @staticmethod
    def _is_planner_step(step: dict[str, Any]) -> bool:
        return bool(
            isinstance(step, dict)
            and step.get("kind") == "reason"
            and isinstance(step.get("description"), str)
            and step["description"].startswith(PLANNER_STEP_PREFIX)
        )

    def _live_goal(self, user_id: str) -> dict[str, Any] | None:
        live = self.db.entity_generation()
        for goal in self.controller.snapshot(user_id=user_id)["goals"]:
            if int(goal.get("generation", -1)) != live or goal.get("status") != "ACTIVE":
                continue
            return goal
        return None

    def prepare_next(self, user_id: str) -> dict[str, Any] | None:
        """Return exactly one admitted step ready for autonomous cognition/execution.

        Existing PROPOSED/FAILED steps are admitted/re-admitted by code. A goal with no
        unfinished step receives one deterministic reasoning/planner step. ADMITTED steps
        are returned unchanged so caller-side dispatch can resume without consuming a new
        retry/step budget entry.
        """
        goal = self._live_goal(user_id)
        if goal is None:
            return None
        goal_id = goal["goal_id"]
        step = goal.get("current_step")

        if isinstance(step, dict) and step.get("status") == "ADMITTED":
            admitted = dict(step)
        elif isinstance(step, dict) and step.get("status") in {"PROPOSED", "FAILED"}:
            admitted = self.controller.admit_step(goal_id, step["step_id"])
        else:
            planning = self.controller.propose_step(
                goal_id,
                "reason",
                f"{PLANNER_STEP_PREFIX} determine the next bounded state-machine step from canonical goal/evidence state",
            )
            admitted = self.controller.admit_step(goal_id, planning["step_id"])

        kind = admitted["kind"]
        if kind == "effect":
            prompt = (
                "ClayVerse autonomous EFFECT execution event. The exact effect intent is already admitted in UnifiedDB. "
                f"Goal={goal_id} Step={admitted['step_id']}. "
                "Call mcp__clayverse__request_autonomy_effect with exactly this goal_id and step_id. "
                "Do not resupply or alter capability, target, or argv. Then report only the observed result."
            )
            mode = "effect"
        elif kind == "reason":
            prompt = (
                "ClayVerse autonomous reasoning/planning event. Work only on the canonical goal and admitted step in injected UnifiedDB context. "
                f"Goal={goal_id} Step={admitted['step_id']}. Step description={admitted['description']!r}. "
                "Your final response MUST be exactly one JSON object and no markdown: "
                '{"schema":"ClayVerseAutonomyDecision/v1","kind":"reason|effect|complete_candidate",'
                '"description":"bounded next step","effect":null}.'
                " For kind=effect, effect MUST instead be exactly "
                '{"capability":"state.noop|entityos.exec","target":"...","argv":null_or_string_array}. '
                "Never use complete_candidate as proof; it only asks the controller to verify independent evidence."
            )
            mode = "reason"
        else:
            raise AutonomyStateError("runnable autonomous dispatch supports admitted reason/effect steps only")

        return {
            "goal_id": goal_id,
            "step_id": admitted["step_id"],
            "kind": kind,
            "mode": mode,
            "prompt": prompt,
            "generation": int(goal["generation"]),
        }

    def ingest_reason_response(
        self,
        goal_id: str,
        step_id: str,
        response: str,
        *,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        """Compile one autonomous reason response into the next controller step.

        Invalid model output makes the admitted reason step fail. The raw response is not
        copied into controller state or a failure reason. A valid decision first proves the
        reason step terminal, then creates the next controller proposal. Effect/reason
        proposals are deterministically admitted immediately; completion remains separately
        verified by AutonomyController.
        """
        try:
            decision = self._decision_object(response)
        except AutonomyDecisionError:
            self.controller.record_step_failure(
                goal_id,
                step_id,
                "invalid_autonomy_planner_decision",
                expected_generation=expected_generation,
            )
            raise

        snapshot = self.controller.snapshot()
        goal = next((item for item in snapshot["goals"] if item["goal_id"] == goal_id), None)
        if goal is None:
            raise KeyError(goal_id)
        current = goal.get("current_step")
        if (
            not self._is_planner_step(current)
            or current.get("step_id") != step_id
            or current.get("status") != "ADMITTED"
        ):
            raise AutonomyStateError("reason response does not belong to an admitted planner step")

        self.controller.record_reason_success(
            goal_id,
            step_id,
            expected_generation=expected_generation,
        )
        next_step = self.controller.propose_step(
            goal_id,
            decision["kind"],
            decision["description"],
            effect=decision["effect"],
            expected_generation=expected_generation,
        )

        admitted = None
        completion = None
        if decision["kind"] in {"reason", "effect"}:
            admitted = self.controller.admit_step(
                goal_id,
                next_step["step_id"],
                expected_generation=expected_generation,
            )
        else:
            try:
                completion = self.controller.verify_completion(
                    goal_id,
                    expected_generation=expected_generation,
                )
            except CompletionNotVerified:
                completion = None

        return {
            "goal_id": goal_id,
            "planning_step_id": step_id,
            "decision": decision,
            "next_step": admitted or next_step,
            "completion": completion,
        }
