from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import Lease, LeaseConflict, StaleGeneration, UnifiedDB

STATE_KEY = "autonomy_state_v2"
STATE_SCHEMA = "ClayVerseAutonomyState/v2"
IDENTITY_STATE = {
    "entity_name": "ClayVerse",
    "operating_mode": "HIGH_AGENCY_GROUNDED",
    "mission": "Pursue explicitly admitted user goals proactively while preserving canonical state, evidence, authorization, bounded resource use, and recoverable causality.",
    "model_authority": "PROPOSAL_ONLY",
    "completion_authority": "EXTERNAL_EVIDENCE_OR_OWNER_ACK",
}
GOAL_STATUSES = {"ACTIVE", "WAITING", "VERIFYING", "BLOCKED", "COMPLETED", "CANCELLED"}
STEP_KINDS = {"reason", "effect", "wait", "complete_candidate"}
EFFECT_CAPABILITIES = {"state.noop", "entityos.exec"}
COMPLETION_MODES = {"verified_effect", "user_ack"}
MAX_GOALS, MAX_STEPS, MAX_RETRIES, MAX_EFFECTS = 512, 256, 16, 64
MAX_OBJECTIVE_CHARS, MAX_STEP_CHARS = 20_000, 8_000


class AutonomyStateError(RuntimeError):
    pass


class AutonomyBudgetExceeded(AutonomyStateError):
    pass


class CompletionNotVerified(AutonomyStateError):
    pass


@dataclass(frozen=True)
class GoalBudget:
    max_steps: int = 32
    max_retries_per_step: int = 3
    max_effects: int = 8

    def validate(self) -> "GoalBudget":
        if not 1 <= int(self.max_steps) <= MAX_STEPS:
            raise ValueError("max_steps out of range")
        if not 0 <= int(self.max_retries_per_step) <= MAX_RETRIES:
            raise ValueError("max_retries_per_step out of range")
        if not 0 <= int(self.max_effects) <= MAX_EFFECTS:
            raise ValueError("max_effects out of range")
        return self


@dataclass(frozen=True)
class GoalClaim:
    goal_id: str
    lease: Lease


class AutonomyController:
    """Canonical bounded goal controller; model proposals are never evidence."""

    def __init__(self, db: UnifiedDB):
        self.db = db
        self._ensure_initialized()

    @staticmethod
    def _loads(raw: str) -> dict[str, Any]:
        def reject_constant(value: str):
            raise AutonomyStateError(f"non-finite JSON constant: {value}")

        def unique_pairs(pairs):
            out = {}
            for key, value in pairs:
                if key in out:
                    raise AutonomyStateError(f"duplicate state key: {key}")
                out[key] = value
            return out

        try:
            value = json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_pairs)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise AutonomyStateError("invalid autonomy state JSON") from exc
        if not isinstance(value, dict):
            raise AutonomyStateError("autonomy state must be an object")
        return value

    @staticmethod
    def _dumps(value: dict[str, Any]) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise AutonomyStateError("autonomy state is not canonical JSON") from exc

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "schema": STATE_SCHEMA,
            "revision": 0,
            "identity": dict(IDENTITY_STATE),
            "goals": {},
            "queue": [],
        }

    def _ensure_initialized(self) -> None:
        with self.db.tx() as db:
            row = db.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()
            if row is None:
                state = self._empty()
                self._validate(state)
                db.execute("INSERT INTO meta(key,value) VALUES(?,?)", (STATE_KEY, self._dumps(state)))
            else:
                self._validate(self._loads(row[0]))

    @classmethod
    def _validate(cls, state: dict[str, Any]) -> None:
        if set(state) != {"schema", "revision", "identity", "goals", "queue"} or state["schema"] != STATE_SCHEMA:
            raise AutonomyStateError("unsupported autonomy state")
        if state["identity"] != IDENTITY_STATE:
            raise AutonomyStateError("persisted autonomy identity contract mismatch")
        if not isinstance(state["revision"], int) or state["revision"] < 0:
            raise AutonomyStateError("invalid autonomy revision")
        if not isinstance(state["goals"], dict) or len(state["goals"]) > MAX_GOALS:
            raise AutonomyStateError("invalid autonomy goals")
        if not isinstance(state["queue"], list) or len(state["queue"]) != len(set(state["queue"])):
            raise AutonomyStateError("invalid autonomy queue")
        if any(goal_id not in state["goals"] for goal_id in state["queue"]):
            raise AutonomyStateError("queue references unknown goal")
        for goal_id, goal in state["goals"].items():
            cls._validate_goal(goal_id, goal)

    @staticmethod
    def _validate_goal(goal_id: str, goal: dict[str, Any]) -> None:
        required = {
            "goal_id", "user_id", "session_id", "generation", "source_turn_id", "objective",
            "priority", "status", "completion_contract", "budget", "counters", "current_step",
            "evidence_effect_ids", "user_ack_turn_id", "created_at", "updated_at", "blocked_reason",
        }
        if not isinstance(goal, dict) or set(goal) != required or goal.get("goal_id") != goal_id:
            raise AutonomyStateError("invalid goal fields")
        uid = goal["user_id"]
        if uid not in {"gabriel", "andreas"} or goal["session_id"] != f"session:{uid}":
            raise AutonomyStateError("invalid goal identity")
        if not isinstance(goal["generation"], int) or goal["generation"] < 1:
            raise AutonomyStateError("invalid goal generation")
        if not isinstance(goal["source_turn_id"], str) or not goal["source_turn_id"]:
            raise AutonomyStateError("invalid goal source")
        objective = goal["objective"]
        if not isinstance(objective, str) or not objective.strip() or len(objective) > MAX_OBJECTIVE_CHARS:
            raise AutonomyStateError("invalid goal objective")
        if not isinstance(goal["priority"], int) or not 0 <= goal["priority"] <= 100 or goal["status"] not in GOAL_STATUSES:
            raise AutonomyStateError("invalid goal scheduling state")
        contract = goal["completion_contract"]
        if (
            not isinstance(contract, dict)
            or set(contract) != {"mode", "required_capability", "required_target_sha256"}
            or contract["mode"] not in COMPLETION_MODES
        ):
            raise AutonomyStateError("invalid completion contract")
        if contract["mode"] == "verified_effect":
            if contract["required_capability"] != "entityos.exec":
                raise AutonomyStateError("automatic completion requires non-noop EntityOS evidence")
            digest = contract["required_target_sha256"]
            if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise AutonomyStateError("invalid completion target digest")
        elif contract["required_capability"] is not None or contract["required_target_sha256"] is not None:
            raise AutonomyStateError("user_ack cannot require an effect")
        budget = goal["budget"]
        if not isinstance(budget, dict) or set(budget) != {"max_steps", "max_retries_per_step", "max_effects"}:
            raise AutonomyStateError("invalid goal budget")
        GoalBudget(**budget).validate()
        counters = goal["counters"]
        if not isinstance(counters, dict) or set(counters) != {"steps", "effects", "consecutive_failures"}:
            raise AutonomyStateError("invalid goal counters")
        if any(not isinstance(v, int) or v < 0 for v in counters.values()):
            raise AutonomyStateError("invalid goal counters")
        if counters["steps"] > budget["max_steps"] or counters["effects"] > budget["max_effects"]:
            raise AutonomyStateError("goal counters exceed budget")
        step = goal["current_step"]
        if step is not None:
            fields = {"step_id", "kind", "description", "effect", "attempts", "status", "created_at"}
            if not isinstance(step, dict) or set(step) != fields or step["kind"] not in STEP_KINDS:
                raise AutonomyStateError("invalid current step")
            if not isinstance(step["description"], str) or not step["description"] or len(step["description"]) > MAX_STEP_CHARS:
                raise AutonomyStateError("invalid step description")
            if not isinstance(step["attempts"], int) or step["attempts"] < 0 or step["status"] not in {"PROPOSED", "ADMITTED", "SUCCEEDED", "FAILED"}:
                raise AutonomyStateError("invalid step state")
            if step["kind"] == "effect":
                effect = step["effect"]
                if not isinstance(effect, dict) or set(effect) != {"capability", "target", "argv"} or effect["capability"] not in EFFECT_CAPABILITIES:
                    raise AutonomyStateError("invalid effect proposal")
            elif step["effect"] is not None:
                raise AutonomyStateError("non-effect step contains effect")
        evidence = goal["evidence_effect_ids"]
        if not isinstance(evidence, list) or len(evidence) != len(set(evidence)) or any(not isinstance(x, str) or not x for x in evidence):
            raise AutonomyStateError("invalid effect evidence")
        if goal["user_ack_turn_id"] is not None and not isinstance(goal["user_ack_turn_id"], str):
            raise AutonomyStateError("invalid user acknowledgement")
        if any(not isinstance(goal[k], (int, float)) or not math.isfinite(float(goal[k])) for k in ("created_at", "updated_at")):
            raise AutonomyStateError("invalid goal timestamp")
        if goal["blocked_reason"] is not None and not isinstance(goal["blocked_reason"], str):
            raise AutonomyStateError("invalid blocked reason")

    def _load(self, db) -> dict[str, Any]:
        row = db.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()
        state = self._empty() if row is None else self._loads(row[0])
        self._validate(state)
        return state

    def _save(self, db, state: dict[str, Any]) -> None:
        self._validate(state)
        state["revision"] += 1
        db.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (STATE_KEY, self._dumps(state)),
        )

    def snapshot(self, *, user_id: str | None = None) -> dict[str, Any]:
        with self.db.tx() as db:
            state = self._load(db)
        goals = [
            state["goals"][gid]
            for gid in state["queue"]
            if user_id is None or state["goals"][gid]["user_id"] == user_id
        ]
        return {
            "schema": STATE_SCHEMA,
            "revision": state["revision"],
            "identity": dict(state["identity"]),
            "goals": goals,
        }

    @staticmethod
    def _target_digest(target: str) -> str:
        return hashlib.sha256(target.encode("utf-8")).hexdigest()

    def create_goal_from_turn(
        self,
        user_id: str,
        session_id: str,
        source_turn_id: str,
        *,
        completion_mode: str,
        required_capability: str | None = None,
        required_target: str | None = None,
        priority: int = 50,
        budget: GoalBudget | None = None,
    ) -> dict[str, Any]:
        self.db.assert_session_owner(session_id, user_id)
        generation = self.db.session_generation(session_id)
        self.db.assert_live_generation(session_id, generation)
        if completion_mode not in COMPLETION_MODES:
            raise ValueError("invalid completion mode")
        if completion_mode == "verified_effect":
            if required_capability != "entityos.exec":
                raise ValueError("automatic completion requires entityos.exec, never state.noop")
            if not isinstance(required_target, str) or not required_target or len(required_target) > 2048 or "\x00" in required_target:
                raise ValueError("verified_effect requires exact bounded target")
            required_target_sha256 = self._target_digest(required_target)
        else:
            if required_capability is not None or required_target is not None:
                raise ValueError("user_ack does not accept effect completion fields")
            required_target_sha256 = None
        if not isinstance(priority, int) or not 0 <= priority <= 100:
            raise ValueError("priority out of range")
        budget = (budget or GoalBudget()).validate()
        now, goal_id = time.time(), str(uuid.uuid4())
        with self.db.tx() as db:
            self.db.assert_live_generation(session_id, generation)
            row = db.execute(
                "SELECT session_id,user_id,role,content FROM turns WHERE turn_id=?",
                (source_turn_id,),
            ).fetchone()
            if row is None:
                raise AutonomyStateError("goal source turn missing")
            if row["session_id"] != session_id or row["user_id"] != user_id or row["role"] != "user":
                raise PermissionError("goal source must be a canonical owner user turn")
            objective = row["content"]
            if not isinstance(objective, str) or not objective.strip() or len(objective) > MAX_OBJECTIVE_CHARS:
                raise AutonomyStateError("invalid canonical goal objective")
            state = self._load(db)
            if len(state["goals"]) >= MAX_GOALS:
                raise AutonomyStateError("goal capacity reached")
            goal = {
                "goal_id": goal_id,
                "user_id": user_id,
                "session_id": session_id,
                "generation": int(generation),
                "source_turn_id": source_turn_id,
                "objective": objective,
                "priority": priority,
                "status": "ACTIVE",
                "completion_contract": {
                    "mode": completion_mode,
                    "required_capability": required_capability,
                    "required_target_sha256": required_target_sha256,
                },
                "budget": {
                    "max_steps": int(budget.max_steps),
                    "max_retries_per_step": int(budget.max_retries_per_step),
                    "max_effects": int(budget.max_effects),
                },
                "counters": {"steps": 0, "effects": 0, "consecutive_failures": 0},
                "current_step": None,
                "evidence_effect_ids": [],
                "user_ack_turn_id": None,
                "created_at": now,
                "updated_at": now,
                "blocked_reason": None,
            }
            state["goals"][goal_id] = goal
            state["queue"].append(goal_id)
            state["queue"].sort(
                key=lambda gid: (-state["goals"][gid]["priority"], state["goals"][gid]["created_at"], gid)
            )
            self._save(db, state)
        return dict(goal)

    def _goal(self, db, goal_id: str, expected_generation: int | None = None):
        state = self._load(db)
        goal = state["goals"].get(goal_id)
        if goal is None:
            raise KeyError(goal_id)
        live = self.db.entity_generation()
        if goal["generation"] != live or (expected_generation is not None and int(expected_generation) != live):
            raise StaleGeneration(goal_id)
        self.db.assert_live_generation(goal["session_id"], live)
        return state, goal

    @staticmethod
    def _budget(goal: dict[str, Any], *, needs_effect: bool = False) -> None:
        if goal["counters"]["steps"] >= goal["budget"]["max_steps"]:
            raise AutonomyBudgetExceeded("step budget exhausted")
        if needs_effect and goal["counters"]["effects"] >= goal["budget"]["max_effects"]:
            raise AutonomyBudgetExceeded("effect budget exhausted")

    @staticmethod
    def _validated_effect(effect: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(effect, dict):
            raise ValueError("effect step requires effect object")
        capability, target, argv = effect.get("capability"), effect.get("target"), effect.get("argv")
        if capability not in EFFECT_CAPABILITIES:
            raise PermissionError("effect capability denied")
        if not isinstance(target, str) or not target or len(target) > 2048 or "\x00" in target:
            raise ValueError("invalid effect target")
        if capability == "entityos.exec":
            if (
                not isinstance(argv, list)
                or not argv
                or len(argv) > 128
                or any(not isinstance(x, str) or not x or len(x) > 8192 or "\x00" in x for x in argv)
            ):
                raise ValueError("invalid effect argv")
        elif argv not in (None, []):
            raise ValueError("state.noop does not accept argv")
        else:
            argv = None
        return {"capability": capability, "target": target, "argv": argv}

    def propose_step(
        self,
        goal_id: str,
        kind: str,
        description: str,
        *,
        effect=None,
        expected_generation=None,
    ) -> dict[str, Any]:
        if kind not in STEP_KINDS:
            raise ValueError("invalid step kind")
        description = str(description).strip()
        if not description or len(description) > MAX_STEP_CHARS:
            raise ValueError("invalid step description")
        if kind == "effect":
            effect = self._validated_effect(effect)
        elif effect is not None:
            raise ValueError("effect only allowed for effect step")
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            if goal["status"] not in {"ACTIVE", "WAITING"}:
                raise AutonomyStateError("goal is not runnable")
            if goal["current_step"] and goal["current_step"]["status"] in {"PROPOSED", "ADMITTED"}:
                raise AutonomyStateError("goal already has an unfinished step")
            self._budget(goal, needs_effect=kind == "effect")
            step = {
                "step_id": str(uuid.uuid4()),
                "kind": kind,
                "description": description,
                "effect": effect,
                "attempts": 0,
                "status": "PROPOSED",
                "created_at": time.time(),
            }
            goal["current_step"] = step
            goal["status"] = "VERIFYING" if kind == "complete_candidate" else ("WAITING" if kind == "wait" else "ACTIVE")
            goal["updated_at"] = time.time()
            self._save(db, state)
            return dict(step)

    def admit_step(self, goal_id: str, step_id: str, *, expected_generation=None) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            step = goal["current_step"]
            if not step or step["step_id"] != step_id or step["status"] not in {"PROPOSED", "FAILED"}:
                raise AutonomyStateError("step not admissible")
            if step["attempts"] > goal["budget"]["max_retries_per_step"]:
                raise AutonomyBudgetExceeded("retry budget exhausted")
            self._budget(goal, needs_effect=step["kind"] == "effect")
            step["attempts"] += 1
            step["status"] = "ADMITTED"
            goal["counters"]["steps"] += 1
            goal["counters"]["effects"] += int(step["kind"] == "effect")
            goal["updated_at"] = time.time()
            self._save(db, state)
            return dict(step)

    def record_step_failure(
        self,
        goal_id: str,
        step_id: str,
        reason: str,
        *,
        expected_generation=None,
    ) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            step = goal["current_step"]
            if not step or step["step_id"] != step_id or step["status"] != "ADMITTED":
                raise AutonomyStateError("step is not active")
            step["status"] = "FAILED"
            goal["counters"]["consecutive_failures"] += 1
            exhausted = step["attempts"] > goal["budget"]["max_retries_per_step"]
            goal["status"] = "BLOCKED" if exhausted else "ACTIVE"
            goal["blocked_reason"] = "retry_budget_exhausted" if exhausted else (str(reason).strip()[:2000] or "step_failed")
            goal["updated_at"] = time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "status": goal["status"], "reason": goal["blocked_reason"]}

    def record_reason_success(self, goal_id: str, step_id: str, *, expected_generation=None) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            step = goal["current_step"]
            if not step or step["step_id"] != step_id or step["status"] != "ADMITTED" or step["kind"] not in {"reason", "wait"}:
                raise AutonomyStateError("reason/wait step is not active")
            step["status"], goal["status"], goal["blocked_reason"] = "SUCCEEDED", "ACTIVE", None
            goal["counters"]["consecutive_failures"] = 0
            goal["updated_at"] = time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "status": "ACTIVE", "step_id": step_id}

    @staticmethod
    def _effect_target_sha(raw: str) -> str | None:
        try:
            value = AutonomyController._loads(raw)
        except AutonomyStateError:
            return None
        digest = value.get("sha256")
        return digest if isinstance(digest, str) else None

    def _effect_context(self, db, goal: dict[str, Any], effect_id: str) -> dict[str, Any]:
        row = db.execute(
            "SELECT e.effect_id,e.episode_id,e.user_id,e.capability,e.target,e.requested_generation,e.status,e.outcome,e.ts,"
            "w.session_id AS effect_session,ce.causal_id,ce.reentered "
            "FROM effects e "
            "LEFT JOIN workspace_episodes w ON w.episode_id=e.episode_id "
            "LEFT JOIN causal_episodes ce ON ce.effect_id=e.effect_id "
            "WHERE e.effect_id=?",
            (effect_id,),
        ).fetchone()
        if row is None:
            raise AutonomyStateError("effect receipt missing")
        if row["user_id"] != goal["user_id"] or row["effect_session"] != goal["session_id"]:
            raise PermissionError("effect receipt owner/session mismatch")
        if int(row["requested_generation"]) != int(goal["generation"]):
            raise StaleGeneration(effect_id)
        if float(row["ts"]) < float(goal["created_at"]):
            raise AutonomyStateError("effect predates goal")
        return dict(row)

    def _verified_effect_matches(
        self,
        db,
        goal: dict[str, Any],
        effect_id: str,
        *,
        step: dict[str, Any] | None = None,
        require_completion_contract: bool = False,
    ) -> bool:
        row = self._effect_context(db, goal, effect_id)
        if row["status"] != "VERIFIED" or not row["causal_id"] or int(row["reentered"] or 0) != 1:
            return False
        try:
            outcome = self._loads(row["outcome"] or "{}")
        except AutonomyStateError:
            return False
        if outcome.get("ok") is not True:
            return False
        if step is not None:
            if step["kind"] != "effect" or row["capability"] != step["effect"]["capability"]:
                return False
            if self._effect_target_sha(row["target"]) != self._target_digest(step["effect"]["target"]):
                return False
        if require_completion_contract:
            contract = goal["completion_contract"]
            if contract["mode"] != "verified_effect" or row["capability"] != contract["required_capability"]:
                return False
            if self._effect_target_sha(row["target"]) != contract["required_target_sha256"]:
                return False
        return True

    def record_effect_result(
        self,
        goal_id: str,
        step_id: str,
        effect_id: str,
        *,
        expected_generation=None,
    ) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            step = goal["current_step"]
            if not step or step["step_id"] != step_id or step["status"] != "ADMITTED" or step["kind"] != "effect":
                raise AutonomyStateError("effect step is not active")
            row = self._effect_context(db, goal, effect_id)
            if row["capability"] != step["effect"]["capability"]:
                raise PermissionError("effect receipt capability mismatch")
            if self._effect_target_sha(row["target"]) != self._target_digest(step["effect"]["target"]):
                raise PermissionError("effect receipt target mismatch")
            if row["status"] == "PENDING":
                raise AutonomyStateError("effect outcome is pending")
            verified = self._verified_effect_matches(db, goal, effect_id, step=step)
            completion_evidence = verified and self._verified_effect_matches(
                db, goal, effect_id, require_completion_contract=True
            )
            step["status"] = "SUCCEEDED" if verified else "FAILED"
            if completion_evidence and effect_id not in goal["evidence_effect_ids"]:
                goal["evidence_effect_ids"].append(effect_id)
            goal["counters"]["consecutive_failures"] = 0 if verified else goal["counters"]["consecutive_failures"] + 1
            goal["status"] = "ACTIVE" if verified else "BLOCKED"
            goal["blocked_reason"] = None if verified else f"effect_{str(row['status']).lower()}"
            goal["updated_at"] = time.time()
            self._save(db, state)
            return {
                "goal_id": goal_id,
                "effect_id": effect_id,
                "verified": verified,
                "completion_evidence": completion_evidence,
                "status": goal["status"],
            }

    def acknowledge_by_user(self, goal_id: str, turn_id: str, *, expected_generation=None) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            row = db.execute(
                "SELECT session_id,user_id,role,ts FROM turns WHERE turn_id=?",
                (turn_id,),
            ).fetchone()
            if row is None:
                raise AutonomyStateError("acknowledgement turn missing")
            if row["session_id"] != goal["session_id"] or row["user_id"] != goal["user_id"] or row["role"] != "user":
                raise PermissionError("acknowledgement must come from goal owner")
            if turn_id == goal["source_turn_id"] or float(row["ts"]) <= float(goal["created_at"]):
                raise PermissionError("acknowledgement must be an explicit later owner turn")
            goal["user_ack_turn_id"], goal["updated_at"] = turn_id, time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "user_ack_turn_id": turn_id}

    def verify_completion(self, goal_id: str, *, expected_generation=None) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id, expected_generation)
            contract, evidence = goal["completion_contract"], None
            if contract["mode"] == "user_ack":
                turn_id = goal["user_ack_turn_id"]
                if turn_id:
                    row = db.execute(
                        "SELECT session_id,user_id,role,ts FROM turns WHERE turn_id=?",
                        (turn_id,),
                    ).fetchone()
                    if (
                        row
                        and row["session_id"] == goal["session_id"]
                        and row["user_id"] == goal["user_id"]
                        and row["role"] == "user"
                        and turn_id != goal["source_turn_id"]
                        and float(row["ts"]) > float(goal["created_at"])
                    ):
                        evidence = turn_id
            else:
                for effect_id in goal["evidence_effect_ids"]:
                    try:
                        if self._verified_effect_matches(
                            db,
                            goal,
                            effect_id,
                            require_completion_contract=True,
                        ):
                            evidence = effect_id
                            break
                    except (AutonomyStateError, PermissionError, StaleGeneration):
                        continue
            if not evidence:
                raise CompletionNotVerified(goal_id)
            goal["status"], goal["blocked_reason"], goal["updated_at"] = "COMPLETED", None, time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "status": "COMPLETED", "evidence": evidence}

    def block_goal(self, goal_id: str, reason: str) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id)
            if goal["status"] in {"COMPLETED", "CANCELLED"}:
                raise AutonomyStateError("terminal goal cannot be blocked")
            goal["status"] = "BLOCKED"
            goal["blocked_reason"] = str(reason).strip()[:2000] or "blocked"
            goal["updated_at"] = time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "status": "BLOCKED", "reason": goal["blocked_reason"]}

    def cancel_goal(self, goal_id: str) -> dict[str, Any]:
        with self.db.tx() as db:
            state, goal = self._goal(db, goal_id)
            if goal["status"] == "COMPLETED":
                raise AutonomyStateError("completed goal cannot be cancelled")
            goal["status"], goal["blocked_reason"], goal["updated_at"] = "CANCELLED", None, time.time()
            self._save(db, state)
            return {"goal_id": goal_id, "status": "CANCELLED"}

    def next_runnable(self, *, user_id: str | None = None) -> dict[str, Any] | None:
        with self.db.tx() as db:
            state, live = self._load(db), self.db.entity_generation()
            for goal_id in state["queue"]:
                goal = state["goals"][goal_id]
                if user_id is not None and goal["user_id"] != user_id:
                    continue
                if goal["generation"] != live or goal["status"] != "ACTIVE":
                    continue
                if goal["counters"]["steps"] >= goal["budget"]["max_steps"]:
                    continue
                step = goal["current_step"]
                if step and step["status"] in {"PROPOSED", "ADMITTED"}:
                    continue
                return dict(goal)
        return None

    def claim_next(
        self,
        worker_id: str,
        *,
        user_id: str | None = None,
        ttl: float = 60.0,
    ) -> GoalClaim | None:
        worker_id = str(worker_id).strip()
        if not worker_id or len(worker_id) > 256:
            raise ValueError("invalid worker id")
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not 0 < float(ttl) <= 300:
            raise ValueError("invalid goal lease ttl")
        with self.db.tx() as db:
            state, live = self._load(db), self.db.entity_generation()
            candidates = []
            for goal_id in state["queue"]:
                goal = state["goals"][goal_id]
                if user_id is not None and goal["user_id"] != user_id:
                    continue
                if goal["generation"] != live or goal["status"] != "ACTIVE":
                    continue
                if goal["counters"]["steps"] >= goal["budget"]["max_steps"]:
                    continue
                step = goal["current_step"]
                if step and step["status"] in {"PROPOSED", "ADMITTED"}:
                    continue
                candidates.append(goal_id)
        for goal_id in candidates:
            try:
                lease = self.db.acquire_lease(f"autonomy-goal:{goal_id}", worker_id, ttl=float(ttl))
            except LeaseConflict:
                continue
            return GoalClaim(goal_id=goal_id, lease=lease)
        return None

    def assert_claim(self, claim: GoalClaim) -> None:
        if claim.lease.resource != f"autonomy-goal:{claim.goal_id}":
            raise AutonomyStateError("goal lease resource mismatch")
        self.db.assert_lease(claim.lease)

    def release_claim(self, claim: GoalClaim) -> None:
        self.assert_claim(claim)
        lease = claim.lease
        with self.db.tx() as db:
            db.execute(
                "DELETE FROM leases WHERE resource=? AND holder=? AND generation=? AND nonce=?",
                (lease.resource, lease.holder, lease.generation, lease.nonce),
            )
