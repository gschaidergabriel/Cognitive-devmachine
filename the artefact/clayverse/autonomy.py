from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .store import UnifiedDB


class AutonomyError(RuntimeError):
    pass


class InvalidProposal(AutonomyError):
    pass


class GoalBlocked(AutonomyError):
    pass


@dataclass(frozen=True)
class AutonomyPolicy:
    default_step_max_attempts: int = 3
    max_repeated_identical_failures: int = 2
    max_goal_attempt_budget: int = 24
    max_objective_chars: int = 8_000
    max_step_chars: int = 4_000
    max_proposal_chars: int = 8_000


@dataclass(frozen=True)
class GroundedSnapshot:
    entity_generation: int
    identity_contract: Mapping[str, Any]
    goal: Mapping[str, Any]
    step: Mapping[str, Any]
    observed_capabilities: tuple[str, ...]
    verified_receipts: tuple[Mapping[str, Any], ...]
    epistemic_rules: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity_generation": self.entity_generation,
            "identity_contract": dict(self.identity_contract),
            "goal": dict(self.goal),
            "step": dict(self.step),
            "observed_capabilities": list(self.observed_capabilities),
            "verified_receipts": [dict(item) for item in self.verified_receipts],
            "epistemic_rules": list(self.epistemic_rules),
        }


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    reason: str
    evidence: Mapping[str, Any]
    source: str = "deterministic-verifier"
    kind: str = "VERIFICATION"


@dataclass(frozen=True)
class TickResult:
    tick_id: str
    state: str
    goal_id: str | None
    step_id: str | None
    reason: str
    receipt_id: str | None = None


class AutonomyState:
    """Goal state inside the one canonical UnifiedDB authority.

    Schema ownership stays in ``store.SCHEMA``. This class verifies that the canonical
    autonomy extension is present; it does not create a second schema/state path.
    """

    REQUIRED_TABLES = (
        "autonomy_goals",
        "autonomy_steps",
        "autonomy_receipts",
        "autonomy_ticks",
    )

    def __init__(self, db: UnifiedDB, policy: AutonomyPolicy | None = None):
        self.db = db
        self.policy = policy or AutonomyPolicy()
        version = self.db.db.execute(
            "SELECT value FROM meta WHERE key='autonomy_schema_version'"
        ).fetchone()
        if not version or version[0] != "1":
            raise AutonomyError("canonical autonomy schema version is unavailable")
        tables = {
            row[0]
            for row in self.db.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'autonomy_%'"
            ).fetchall()
        }
        if not set(self.REQUIRED_TABLES).issubset(tables):
            raise AutonomyError("canonical autonomy tables are incomplete")

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _hash_payload(cls, value: Any) -> str:
        return hashlib.sha256(cls._json(value).encode("utf-8")).hexdigest()

    def admit_goal(
        self,
        creator_user_id: str,
        objective: str,
        *,
        success_contract: Mapping[str, Any],
        priority: int = 100,
        autonomous: bool = True,
        attempt_budget: int | None = None,
    ) -> str:
        objective = str(objective).strip()
        if not objective or len(objective) > self.policy.max_objective_chars:
            raise ValueError("goal objective is empty or oversized")
        if not isinstance(success_contract, Mapping) or not success_contract:
            raise ValueError("success_contract must be a non-empty mapping")
        if not self.db.db.execute(
            "SELECT 1 FROM users WHERE user_id=?", (creator_user_id,)
        ).fetchone():
            raise PermissionError("goal creator is not a canonical user")
        budget = int(attempt_budget or self.policy.max_goal_attempt_budget)
        if budget < 1 or budget > self.policy.max_goal_attempt_budget:
            raise ValueError("attempt_budget outside admitted bounds")
        now = time.time()
        goal_id = str(uuid.uuid4())
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO autonomy_goals(goal_id,creator_user_id,objective,success_contract,priority,status,autonomous,attempt_budget,attempts_used,created_generation,created_at,updated_at) VALUES(?,?,?,?,?,'ACTIVE',?,?,?,?,?,?)",
                (
                    goal_id,
                    creator_user_id,
                    objective,
                    self._json(dict(success_contract)),
                    int(priority),
                    1 if autonomous else 0,
                    budget,
                    0,
                    self.db.entity_generation(),
                    now,
                    now,
                ),
            )
        return goal_id

    def add_step(
        self,
        goal_id: str,
        description: str,
        *,
        verification_contract: Mapping[str, Any],
        max_attempts: int | None = None,
    ) -> str:
        description = str(description).strip()
        if not description or len(description) > self.policy.max_step_chars:
            raise ValueError("step description is empty or oversized")
        if not isinstance(verification_contract, Mapping) or not verification_contract:
            raise ValueError("verification_contract must be a non-empty mapping")
        attempts = int(max_attempts or self.policy.default_step_max_attempts)
        if attempts < 1 or attempts > self.policy.default_step_max_attempts:
            raise ValueError("step max_attempts outside admitted bounds")
        now = time.time()
        step_id = str(uuid.uuid4())
        with self.db.tx() as conn:
            goal = conn.execute(
                "SELECT status FROM autonomy_goals WHERE goal_id=?", (goal_id,)
            ).fetchone()
            if not goal:
                raise KeyError(goal_id)
            if goal["status"] not in {"ACTIVE", "PAUSED"}:
                raise GoalBlocked("cannot add a step to a terminal/blocked goal")
            ordinal = int(
                conn.execute(
                    "SELECT COALESCE(MAX(ordinal),0)+1 FROM autonomy_steps WHERE goal_id=?",
                    (goal_id,),
                ).fetchone()[0]
            )
            conn.execute(
                "INSERT INTO autonomy_steps(step_id,goal_id,ordinal,description,verification_contract,status,max_attempts,created_at,updated_at) VALUES(?,?,?,?,?,'PENDING',?,?,?)",
                (
                    step_id,
                    goal_id,
                    ordinal,
                    description,
                    self._json(dict(verification_contract)),
                    attempts,
                    now,
                    now,
                ),
            )
            conn.execute(
                "UPDATE autonomy_goals SET updated_at=? WHERE goal_id=?", (now, goal_id)
            )
        return step_id

    def goal(self, goal_id: str) -> dict[str, Any]:
        row = self.db.db.execute(
            "SELECT * FROM autonomy_goals WHERE goal_id=?", (goal_id,)
        ).fetchone()
        if not row:
            raise KeyError(goal_id)
        item = dict(row)
        item["success_contract"] = json.loads(item["success_contract"])
        item["autonomous"] = bool(item["autonomous"])
        return item

    def step(self, step_id: str) -> dict[str, Any]:
        row = self.db.db.execute(
            "SELECT * FROM autonomy_steps WHERE step_id=?", (step_id,)
        ).fetchone()
        if not row:
            raise KeyError(step_id)
        item = dict(row)
        item["verification_contract"] = json.loads(item["verification_contract"])
        return item

    def next_frontier(self) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Return only an executable PENDING frontier.

        WAITING_VERIFICATION and BLOCKED are intentionally quiescent and therefore do
        not consume repeated planner calls on timer wakes.
        """
        rows = self.db.db.execute(
            "SELECT * FROM autonomy_goals WHERE status='ACTIVE' AND autonomous=1 AND attempts_used<attempt_budget ORDER BY priority ASC,created_at ASC"
        ).fetchall()
        for goal_row in rows:
            step_row = self.db.db.execute(
                "SELECT * FROM autonomy_steps WHERE goal_id=? AND status='PENDING' ORDER BY ordinal ASC LIMIT 1",
                (goal_row["goal_id"],),
            ).fetchone()
            if step_row:
                return self.goal(goal_row["goal_id"]), self.step(step_row["step_id"])
        return None

    def verified_receipts(self, step_id: str, limit: int = 12) -> tuple[dict[str, Any], ...]:
        rows = self.db.db.execute(
            "SELECT * FROM autonomy_receipts WHERE step_id=? AND verified=1 ORDER BY ts DESC LIMIT ?",
            (step_id, int(limit)),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item["payload"])
            out.append(item)
        return tuple(reversed(out))

    def grounded_snapshot(
        self,
        goal: Mapping[str, Any],
        step: Mapping[str, Any],
        observed_capabilities: Sequence[str],
    ) -> GroundedSnapshot:
        return GroundedSnapshot(
            entity_generation=self.db.entity_generation(),
            identity_contract={
                "entity": "ClayVerse",
                "persistent_state_authority": "UnifiedDB",
                "operating_mode": "goal-directed-proactive",
                "model_role": "cognition/proposal organ, not durable truth or effect authority",
            },
            goal=goal,
            step=step,
            observed_capabilities=tuple(sorted(set(str(x) for x in observed_capabilities))),
            verified_receipts=self.verified_receipts(str(step["step_id"])),
            epistemic_rules=(
                "Never infer a capability from identity text; only observed_capabilities are available.",
                "Never claim an action succeeded without a verified execution/effect receipt.",
                "Never mark a step or goal complete from model text; completion requires a trusted verifier receipt.",
                "Unknown state remains UNKNOWN/BLOCKED rather than being filled by a plausible story.",
            ),
        )

    def record_receipt(
        self,
        goal_id: str,
        step_id: str,
        *,
        kind: str,
        source: str,
        verified: bool,
        payload: Mapping[str, Any],
        generation: int,
    ) -> str:
        kind = str(kind).upper()
        if kind not in {
            "OBSERVATION",
            "EFFECT",
            "VERIFICATION",
            "USER_CONFIRMATION",
            "ARTIFACT",
            "TEST",
        }:
            raise ValueError("unsupported autonomy receipt kind")
        if int(generation) != self.db.entity_generation():
            raise GoalBlocked("stale autonomy receipt generation")
        receipt_id = str(uuid.uuid4())
        serial = dict(payload)
        with self.db.tx() as conn:
            goal = conn.execute(
                "SELECT created_generation FROM autonomy_goals WHERE goal_id=?", (goal_id,)
            ).fetchone()
            step = conn.execute(
                "SELECT 1 FROM autonomy_steps WHERE step_id=? AND goal_id=?",
                (step_id, goal_id),
            ).fetchone()
            if not goal or not step:
                raise KeyError("goal/step")
            if int(goal["created_generation"]) > int(generation):
                raise GoalBlocked("receipt generation predates goal")
            conn.execute(
                "INSERT INTO autonomy_receipts(receipt_id,goal_id,step_id,generation,kind,source,verified,payload,payload_hash,ts) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    receipt_id,
                    goal_id,
                    step_id,
                    int(generation),
                    kind,
                    str(source)[:200],
                    1 if verified else 0,
                    self._json(serial),
                    self._hash_payload(serial),
                    time.time(),
                ),
            )
            conn.execute(
                "UPDATE autonomy_steps SET last_receipt_id=?,updated_at=? WHERE step_id=?",
                (receipt_id, time.time(), step_id),
            )
        return receipt_id

    def _tick(
        self,
        *,
        goal_id: str | None,
        step_id: str | None,
        generation: int,
        trigger: str,
        proposal: Mapping[str, Any] | None,
        action_state: str,
        receipt_id: str | None,
        reason: str,
    ) -> str:
        tick_id = str(uuid.uuid4())
        self.db.db.execute(
            "INSERT INTO autonomy_ticks(tick_id,goal_id,step_id,generation,trigger,proposal,action_state,receipt_id,reason,ts) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                tick_id,
                goal_id,
                step_id,
                int(generation),
                str(trigger)[:80],
                self._json(dict(proposal)) if proposal is not None else None,
                action_state,
                receipt_id,
                str(reason)[:1000],
                time.time(),
            ),
        )
        return tick_id

    def start_attempt(self, goal_id: str, step_id: str) -> None:
        """Spend one bounded attempt before any planner/provider call."""
        now = time.time()
        with self.db.tx() as conn:
            goal = conn.execute(
                "SELECT * FROM autonomy_goals WHERE goal_id=?", (goal_id,)
            ).fetchone()
            step = conn.execute(
                "SELECT * FROM autonomy_steps WHERE step_id=? AND goal_id=?",
                (step_id, goal_id),
            ).fetchone()
            if not goal or not step:
                raise KeyError("goal/step")
            if goal["status"] != "ACTIVE" or not int(goal["autonomous"]):
                raise GoalBlocked("goal is not autonomous-active")
            if step["status"] != "PENDING":
                raise GoalBlocked("step is not executable")
            if int(goal["attempts_used"]) >= int(goal["attempt_budget"]):
                conn.execute(
                    "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                    (now, goal_id),
                )
                raise GoalBlocked("goal attempt budget exhausted")
            if int(step["attempts_used"]) >= int(step["max_attempts"]):
                conn.execute(
                    "UPDATE autonomy_steps SET status='BLOCKED',last_error='step attempt budget exhausted',updated_at=? WHERE step_id=?",
                    (now, step_id),
                )
                conn.execute(
                    "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                    (now, goal_id),
                )
                raise GoalBlocked("step attempt budget exhausted")
            conn.execute(
                "UPDATE autonomy_goals SET attempts_used=attempts_used+1,updated_at=? WHERE goal_id=?",
                (now, goal_id),
            )
            conn.execute(
                "UPDATE autonomy_steps SET attempts_used=attempts_used+1,status='RUNNING',updated_at=? WHERE step_id=?",
                (now, step_id),
            )

    def record_failure(self, goal_id: str, step_id: str, reason: str) -> bool:
        fingerprint = hashlib.sha256(str(reason).encode("utf-8")).hexdigest()
        now = time.time()
        with self.db.tx() as conn:
            row = conn.execute(
                "SELECT last_failure_fingerprint,repeated_failures,attempts_used,max_attempts FROM autonomy_steps WHERE step_id=? AND goal_id=?",
                (step_id, goal_id),
            ).fetchone()
            if not row:
                raise KeyError(step_id)
            repeated = (
                int(row["repeated_failures"]) + 1
                if row["last_failure_fingerprint"] == fingerprint
                else 1
            )
            blocked = (
                repeated >= self.policy.max_repeated_identical_failures
                or int(row["attempts_used"]) >= int(row["max_attempts"])
            )
            conn.execute(
                "UPDATE autonomy_steps SET status=?,repeated_failures=?,last_failure_fingerprint=?,last_error=?,updated_at=? WHERE step_id=?",
                (
                    "BLOCKED" if blocked else "PENDING",
                    repeated,
                    fingerprint,
                    str(reason)[:1000],
                    now,
                    step_id,
                ),
            )
            if blocked:
                conn.execute(
                    "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                    (now, goal_id),
                )
        return blocked

    def block(self, goal_id: str, step_id: str, reason: str) -> None:
        now = time.time()
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE autonomy_steps SET status='BLOCKED',last_error=?,updated_at=? WHERE step_id=? AND goal_id=? AND status!='VERIFIED'",
                (str(reason)[:1000], now, step_id, goal_id),
            )
            conn.execute(
                "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=? AND status NOT IN ('DONE','CANCELLED')",
                (now, goal_id),
            )

    def mark_waiting_verification(self, goal_id: str, step_id: str, reason: str = "") -> None:
        """Pause after an executed/observed action so timer wakes cannot replay it."""
        now = time.time()
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE autonomy_steps SET status='WAITING_VERIFICATION',last_error=?,updated_at=? WHERE step_id=? AND goal_id=?",
                (str(reason)[:1000] or None, now, step_id, goal_id),
            )
            conn.execute(
                "UPDATE autonomy_goals SET status='PAUSED',updated_at=? WHERE goal_id=? AND status='ACTIVE'",
                (now, goal_id),
            )

    def verify_step(self, goal_id: str, step_id: str, receipt_id: str) -> None:
        now = time.time()
        with self.db.tx() as conn:
            receipt = conn.execute(
                "SELECT verified,kind,generation FROM autonomy_receipts WHERE receipt_id=? AND goal_id=? AND step_id=?",
                (receipt_id, goal_id, step_id),
            ).fetchone()
            if not receipt or not int(receipt["verified"]):
                raise GoalBlocked("step verification requires a verified receipt")
            if int(receipt["generation"]) != self.db.entity_generation():
                raise GoalBlocked("step verification receipt is stale")
            if receipt["kind"] not in {
                "VERIFICATION",
                "USER_CONFIRMATION",
                "ARTIFACT",
                "TEST",
            }:
                raise GoalBlocked("execution/observation receipt alone cannot complete a step")
            conn.execute(
                "UPDATE autonomy_steps SET status='VERIFIED',last_receipt_id=?,last_error=NULL,updated_at=? WHERE step_id=?",
                (receipt_id, now, step_id),
            )
            conn.execute(
                "UPDATE autonomy_goals SET status='ACTIVE',updated_at=? WHERE goal_id=? AND status='PAUSED'",
                (now, goal_id),
            )

    def complete_goal_if_verified(
        self,
        goal_id: str,
        verifier: Callable[[Mapping[str, Any], Sequence[Mapping[str, Any]]], VerificationResult],
    ) -> str | None:
        goal = self.goal(goal_id)
        rows = self.db.db.execute(
            "SELECT * FROM autonomy_steps WHERE goal_id=? ORDER BY ordinal", (goal_id,)
        ).fetchall()
        if not rows or any(row["status"] != "VERIFIED" for row in rows):
            return None
        receipts = [
            dict(row)
            for row in self.db.db.execute(
                "SELECT * FROM autonomy_receipts WHERE goal_id=? AND verified=1 ORDER BY ts",
                (goal_id,),
            ).fetchall()
        ]
        result = verifier(goal, receipts)
        if not isinstance(result, VerificationResult):
            raise TypeError("goal verifier must return VerificationResult")
        if not result.verified:
            self.db.db.execute(
                "UPDATE autonomy_goals SET status='PAUSED',updated_at=? WHERE goal_id=?",
                (time.time(), goal_id),
            )
            return None
        generation = self.db.entity_generation()
        final_step = str(rows[-1]["step_id"])
        receipt_id = self.record_receipt(
            goal_id,
            final_step,
            kind=result.kind,
            source=result.source,
            verified=True,
            payload={"scope": "goal", "reason": result.reason, "evidence": dict(result.evidence)},
            generation=generation,
        )
        now = time.time()
        self.db.db.execute(
            "UPDATE autonomy_goals SET status='DONE',completed_at=?,updated_at=? WHERE goal_id=?",
            (now, now, goal_id),
        )
        return receipt_id

    def context_summary(self, limit: int = 4) -> dict[str, Any]:
        rows = self.db.db.execute(
            "SELECT goal_id,creator_user_id,objective,priority,status,autonomous,attempt_budget,attempts_used FROM autonomy_goals WHERE status IN ('ACTIVE','PAUSED','BLOCKED') ORDER BY priority,created_at LIMIT ?",
            (int(limit),),
        ).fetchall()
        return {
            "entity_generation": self.db.entity_generation(),
            "identity_contract": {
                "entity": "ClayVerse",
                "state_authority": "UnifiedDB",
                "mode": "goal-directed-proactive",
            },
            "active_goals": [dict(row) for row in rows],
            "truth_boundary": {
                "capability_claims": "must come from observed runtime capability state, never identity prose",
                "effect_success": "verified effect outcome only",
                "step_success": "trusted verification receipt only",
                "unknown": "remain UNKNOWN/BLOCKED",
            },
        }


class AutonomyController:
    """One bounded deterministic autonomy work unit.

    The planner may be an LLM, but only state-machine transitions and trusted receipts
    can change goal truth. Planner calls themselves consume attempt budget.
    """

    def __init__(
        self,
        state: AutonomyState,
        *,
        capability_provider: Callable[[], Sequence[str]],
        planner: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        effect_executor: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
        observer: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
        step_verifier: Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], VerificationResult],
        goal_verifier: Callable[[Mapping[str, Any], Sequence[Mapping[str, Any]]], VerificationResult],
    ):
        self.state = state
        self.capability_provider = capability_provider
        self.planner = planner
        self.effect_executor = effect_executor
        self.observer = observer
        self.step_verifier = step_verifier
        self.goal_verifier = goal_verifier

    def _proposal(self, snapshot: GroundedSnapshot) -> dict[str, Any]:
        raw = self.planner(snapshot.as_dict())
        if not isinstance(raw, Mapping):
            raise InvalidProposal("planner output must be a mapping")
        proposal = dict(raw)
        if len(json.dumps(proposal, ensure_ascii=False)) > self.state.policy.max_proposal_chars:
            raise InvalidProposal("planner proposal is oversized")
        kind = proposal.get("kind")
        if kind not in {"observe", "effect", "blocked"}:
            raise InvalidProposal("proposal kind must be observe/effect/blocked")
        if kind == "effect":
            capability = proposal.get("capability")
            if not isinstance(capability, str) or capability not in snapshot.observed_capabilities:
                raise InvalidProposal("proposal requested an unobserved capability")
            if not isinstance(proposal.get("target"), str) or not proposal["target"].strip():
                raise InvalidProposal("effect proposal requires a target")
        return proposal

    def _result(
        self,
        state_name: str,
        goal_id: str | None,
        step_id: str | None,
        generation: int,
        trigger: str,
        reason: str,
        *,
        proposal: Mapping[str, Any] | None = None,
        receipt_id: str | None = None,
    ) -> TickResult:
        tick_id = self.state._tick(
            goal_id=goal_id,
            step_id=step_id,
            generation=generation,
            trigger=trigger,
            proposal=proposal,
            action_state=state_name,
            receipt_id=receipt_id,
            reason=reason,
        )
        return TickResult(tick_id, state_name, goal_id, step_id, reason, receipt_id)

    def tick(self, *, trigger: str = "timer") -> TickResult:
        frontier = self.state.next_frontier()
        generation = self.state.db.entity_generation()
        if frontier is None:
            return self._result(
                "IDLE", None, None, generation, trigger, "no autonomous executable frontier"
            )

        goal, step = frontier
        goal_id = str(goal["goal_id"])
        step_id = str(step["step_id"])

        try:
            # Spend budget before capability/provider/planner calls so varying malformed
            # plans cannot evade the retry budget.
            self.state.start_attempt(goal_id, step_id)
            capabilities = tuple(self.capability_provider())
            snapshot = self.state.grounded_snapshot(goal, self.state.step(step_id), capabilities)
            proposal = self._proposal(snapshot)
        except Exception as exc:
            blocked = self.state.record_failure(
                goal_id, step_id, f"proposal:{type(exc).__name__}:{exc}"
            )
            return self._result(
                "BLOCKED" if blocked else "FAILED",
                goal_id,
                step_id,
                generation,
                trigger,
                str(exc),
            )

        if proposal["kind"] == "blocked":
            reason = str(proposal.get("reason", "planner reported a missing prerequisite"))
            self.state.block(goal_id, step_id, reason)
            return self._result(
                "BLOCKED",
                goal_id,
                step_id,
                generation,
                trigger,
                reason,
                proposal=proposal,
            )

        if proposal["kind"] == "effect":
            try:
                execution = self.effect_executor(snapshot.as_dict(), proposal)
            except Exception as exc:
                # Once an external effect executor was entered, absence of a verified
                # receipt is epistemically ambiguous. Never auto-replay it.
                reason = f"effect_outcome_unknown:{type(exc).__name__}:{exc}"
                self.state.block(goal_id, step_id, reason)
                return self._result(
                    "BLOCKED",
                    goal_id,
                    step_id,
                    generation,
                    trigger,
                    reason,
                    proposal=proposal,
                )
            receipt_kind = "EFFECT"
            receipt_source = "effect-boundary"
        else:
            try:
                execution = self.observer(snapshot.as_dict(), proposal)
            except Exception as exc:
                blocked = self.state.record_failure(
                    goal_id, step_id, f"observation:{type(exc).__name__}:{exc}"
                )
                return self._result(
                    "BLOCKED" if blocked else "FAILED",
                    goal_id,
                    step_id,
                    generation,
                    trigger,
                    str(exc),
                    proposal=proposal,
                )
            receipt_kind = "OBSERVATION"
            receipt_source = "observation-boundary"

        if not isinstance(execution, Mapping):
            if proposal["kind"] == "effect":
                reason = "effect outcome is not a receipt mapping"
                self.state.block(goal_id, step_id, reason)
                return self._result(
                    "BLOCKED", goal_id, step_id, generation, trigger, reason, proposal=proposal
                )
            blocked = self.state.record_failure(
                goal_id, step_id, "observation boundary returned a non-mapping receipt"
            )
            return self._result(
                "BLOCKED" if blocked else "FAILED",
                goal_id,
                step_id,
                generation,
                trigger,
                "observation boundary returned a non-mapping receipt",
                proposal=proposal,
            )

        execution = dict(execution)
        receipt_id = self.state.record_receipt(
            goal_id,
            step_id,
            kind=receipt_kind,
            source=receipt_source,
            verified=bool(execution.get("verified") is True),
            payload=execution,
            generation=generation,
        )

        if execution.get("verified") is not True:
            if proposal["kind"] == "effect":
                reason = "effect outcome was not independently verified; replay denied"
                self.state.block(goal_id, step_id, reason)
                return self._result(
                    "BLOCKED",
                    goal_id,
                    step_id,
                    generation,
                    trigger,
                    reason,
                    proposal=proposal,
                    receipt_id=receipt_id,
                )
            blocked = self.state.record_failure(
                goal_id, step_id, "observation was not verified"
            )
            return self._result(
                "BLOCKED" if blocked else "FAILED",
                goal_id,
                step_id,
                generation,
                trigger,
                "observation was not verified",
                proposal=proposal,
                receipt_id=receipt_id,
            )

        # From this point an action/observation has a receipt. Pause before semantic
        # verification so no timer wake can repeat it if verification crashes/stalls.
        self.state.mark_waiting_verification(
            goal_id, step_id, "awaiting trusted semantic verification"
        )
        try:
            verification = self.step_verifier(snapshot.as_dict(), proposal, execution)
        except Exception as exc:
            return self._result(
                "WAITING_VERIFICATION",
                goal_id,
                step_id,
                generation,
                trigger,
                f"verifier_unavailable:{type(exc).__name__}:{exc}",
                proposal=proposal,
                receipt_id=receipt_id,
            )
        if not isinstance(verification, VerificationResult):
            return self._result(
                "WAITING_VERIFICATION",
                goal_id,
                step_id,
                generation,
                trigger,
                "step verifier returned an invalid result type",
                proposal=proposal,
                receipt_id=receipt_id,
            )
        if not verification.verified:
            return self._result(
                "WAITING_VERIFICATION",
                goal_id,
                step_id,
                generation,
                trigger,
                verification.reason,
                proposal=proposal,
                receipt_id=receipt_id,
            )

        verification_receipt = self.state.record_receipt(
            goal_id,
            step_id,
            kind=verification.kind,
            source=verification.source,
            verified=True,
            payload={"reason": verification.reason, "evidence": dict(verification.evidence)},
            generation=generation,
        )
        self.state.verify_step(goal_id, step_id, verification_receipt)
        self.state.complete_goal_if_verified(goal_id, self.goal_verifier)
        return self._result(
            "VERIFIED",
            goal_id,
            step_id,
            generation,
            trigger,
            verification.reason,
            proposal=proposal,
            receipt_id=verification_receipt,
        )


class AutonomyLoop:
    """Timer-driven worker inside the ClayVerse supervisor process, not a second daemon."""

    def __init__(self, controller: AutonomyController, *, interval_seconds: float = 30.0):
        if interval_seconds < 1.0:
            raise ValueError("autonomy interval must be at least one second")
        self.controller = controller
        self.interval_seconds = float(interval_seconds)

    def run_forever(self, stop_event: Any) -> None:
        while not stop_event.is_set():
            self.controller.tick(trigger="timer")
            stop_event.wait(self.interval_seconds)
