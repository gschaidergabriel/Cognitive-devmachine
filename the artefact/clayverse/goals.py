from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .effect_journal import EffectJournal
from .store import Lease, UnifiedDB


class GoalIntegrityError(RuntimeError):
    pass


class GoalPolicyError(PermissionError):
    pass


AUTO_CAPABILITIES = {"state.noop", "entityos.exec"}

_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS goals(
    goal_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(user_id),
    objective TEXT NOT NULL,
    success_contract TEXT NOT NULL,
    allowed_capabilities TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','PAUSED','BLOCKED','SUCCEEDED','CANCELLED')),
    priority INTEGER NOT NULL DEFAULT 0,
    max_steps INTEGER NOT NULL,
    max_retries_per_proposal INTEGER NOT NULL,
    steps_used INTEGER NOT NULL DEFAULT 0,
    created_generation INTEGER NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_goals_status_priority
    ON goals(status,priority DESC,created_at,goal_id);
CREATE TABLE IF NOT EXISTS goal_steps(
    step_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    proposal_hash TEXT NOT NULL,
    capability TEXT NOT NULL,
    target TEXT NOT NULL,
    argv TEXT,
    summary TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ADMITTED','VERIFIED','FAILED','UNKNOWN','CANCELLED')),
    effect_id TEXT REFERENCES effects(effect_id),
    admitted_at REAL NOT NULL,
    observed_at REAL,
    UNIQUE(goal_id,ordinal)
);
CREATE INDEX IF NOT EXISTS idx_goal_steps_goal ON goal_steps(goal_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_goal_steps_proposal ON goal_steps(goal_id,proposal_hash,status);
CREATE TABLE IF NOT EXISTS goal_events(
    event_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
    step_id TEXT REFERENCES goal_steps(step_id) ON DELETE SET NULL,
    seq INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    ts REAL NOT NULL,
    UNIQUE(goal_id,seq)
);
CREATE INDEX IF NOT EXISTS idx_goal_events_goal ON goal_events(goal_id,seq);
'''


def _json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("goal state must be canonical finite JSON") from exc


def _load(raw: str, expected: type) -> Any:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GoalIntegrityError("persisted goal JSON is invalid") from exc
    if not isinstance(value, expected):
        raise GoalIntegrityError("persisted goal JSON has wrong type")
    return value


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GoalClaim:
    goal_id: str
    lease: Lease


class GoalKernel:
    """Deterministic goal state inside UnifiedDB; never a second effect authority.

    Model output may propose one bounded action. It cannot create capability,
    execution evidence, or success. Execution must happen through the existing
    TurnLifecycle/EffectGate path. This kernel only admits proposals and binds an
    exact final EffectJournal receipt back to the admitted step.
    """

    FEATURE = "deterministic_goal_autonomy_v1"

    def __init__(self, db: UnifiedDB):
        self.db = db
        # sqlite3.executescript controls its own transaction boundary. Install the
        # additive schema first, then bind feature/hash state transactionally.
        self.db.db.executescript(_SCHEMA)
        with self.db.tx() as tx:
            tx.execute(
                "INSERT INTO meta(key,value) VALUES('goal_kernel_feature',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self.FEATURE,),
            )
            self._refresh_hash_tx(tx)

    def _refresh_hash_tx(self, tx) -> str:
        if not self.db.db.in_transaction:
            raise GoalIntegrityError("goal-state hash requires an active transaction")
        payload = []
        for table in ("goals", "goal_steps", "goal_events"):
            payload.append(
                (table, [dict(row) for row in tx.execute(f"SELECT * FROM {table} ORDER BY 1")])
            )
        digest = hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()
        tx.execute(
            "INSERT INTO meta(key,value) VALUES('goal_state_hash',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (digest,),
        )
        return digest

    def _event_tx(
        self,
        tx,
        goal_id: str,
        event_type: str,
        payload: dict[str, Any],
        step_id: str | None = None,
    ) -> None:
        seq = int(
            tx.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM goal_events WHERE goal_id=?",
                (goal_id,),
            ).fetchone()[0]
        )
        tx.execute(
            "INSERT INTO goal_events(event_id,goal_id,step_id,seq,generation,event_type,payload,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                goal_id,
                step_id,
                seq,
                self.db.entity_generation(),
                str(event_type)[:100],
                _json(payload),
                time.time(),
            ),
        )

    @staticmethod
    def _objective(value: str) -> str:
        value = str(value).strip()
        if not value or len(value) > 20_000 or "\x00" in value:
            raise ValueError("goal objective must be 1..20000 characters without NUL")
        return value

    @staticmethod
    def _capabilities(values) -> list[str]:
        if not isinstance(values, (list, tuple, set)):
            raise ValueError("allowed_capabilities must be a collection")
        values = sorted(set(values))
        if not values or any(not isinstance(item, str) for item in values):
            raise ValueError("goal requires at least one string capability")
        if "process.exec" in values or any(item not in AUTO_CAPABILITIES for item in values):
            raise GoalPolicyError("goal capability is not admitted by the autonomy kernel")
        return values

    @staticmethod
    def _contract(value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("success_contract must be an object")
        if value.get("type") == "manual":
            if set(value) != {"type"}:
                raise ValueError("manual success contract accepts only type")
            return {"type": "manual"}
        if value.get("type") != "verified_effects" or set(value) - {"type", "requirements"}:
            raise ValueError("unsupported success contract")
        requirements = value.get("requirements")
        if not isinstance(requirements, list) or not 1 <= len(requirements) <= 64:
            raise ValueError("verified_effects requires 1..64 requirements")
        normalized = []
        for item in requirements:
            if not isinstance(item, dict) or set(item) - {
                "capability",
                "target",
                "min_verified",
                "exit",
            }:
                raise ValueError("invalid verified_effects requirement")
            capability = item.get("capability")
            target = item.get("target")
            minimum = item.get("min_verified", 1)
            expected_exit = item.get("exit")
            if capability not in AUTO_CAPABILITIES:
                raise ValueError("success requirement capability is not admitted")
            if target is not None and (
                not isinstance(target, str)
                or not target
                or len(target) > 4096
                or "\x00" in target
            ):
                raise ValueError("invalid success requirement target")
            if isinstance(minimum, bool) or not isinstance(minimum, int) or not 1 <= minimum <= 1000:
                raise ValueError("min_verified must be 1..1000")
            if expected_exit is not None and (
                isinstance(expected_exit, bool) or not isinstance(expected_exit, int)
            ):
                raise ValueError("exit must be an integer")
            normalized.append(
                {
                    "capability": capability,
                    "target": target,
                    "min_verified": minimum,
                    "exit": expected_exit,
                }
            )
        return {"type": "verified_effects", "requirements": normalized}

    def create_goal(
        self,
        owner_user_id: str,
        objective: str,
        *,
        success_contract: dict[str, Any],
        allowed_capabilities,
        auto_start: bool = True,
        priority: int = 0,
        max_steps: int = 50,
        max_retries_per_proposal: int = 2,
    ) -> str:
        if owner_user_id not in {"gabriel", "andreas"}:
            raise GoalPolicyError("goal owner must be a canonical user")
        self.db.assert_session_owner(f"session:{owner_user_id}", owner_user_id)
        objective = self._objective(objective)
        contract = self._contract(success_contract)
        capabilities = self._capabilities(allowed_capabilities)
        if isinstance(priority, bool) or not isinstance(priority, int) or not -100 <= priority <= 100:
            raise ValueError("priority must be an integer from -100 to 100")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= 1000:
            raise ValueError("max_steps must be 1..1000")
        if (
            isinstance(max_retries_per_proposal, bool)
            or not isinstance(max_retries_per_proposal, int)
            or not 0 <= max_retries_per_proposal <= 20
        ):
            raise ValueError("max_retries_per_proposal must be 0..20")

        goal_id = str(uuid.uuid4())
        now = time.time()
        status = "ACTIVE" if auto_start else "PAUSED"
        with self.db.tx() as tx:
            tx.execute(
                "INSERT INTO goals(goal_id,owner_user_id,objective,success_contract,allowed_capabilities,status,priority,max_steps,max_retries_per_proposal,steps_used,created_generation,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,0,?,?,?)",
                (
                    goal_id,
                    owner_user_id,
                    objective,
                    _json(contract),
                    _json(capabilities),
                    status,
                    priority,
                    max_steps,
                    max_retries_per_proposal,
                    self.db.entity_generation(),
                    now,
                    now,
                ),
            )
            self._event_tx(
                tx,
                goal_id,
                "GOAL_CREATED",
                {
                    "auto_start": bool(auto_start),
                    "allowed_capabilities": capabilities,
                    "success_contract": contract,
                    "max_steps": max_steps,
                    "max_retries_per_proposal": max_retries_per_proposal,
                },
            )
            self._refresh_hash_tx(tx)
        return goal_id

    def get_goal(self, goal_id: str) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
        if row is None:
            raise KeyError(goal_id)
        result = dict(row)
        result["success_contract"] = _load(result["success_contract"], dict)
        result["allowed_capabilities"] = _load(result["allowed_capabilities"], list)
        return result

    def steps(self, goal_id: str) -> list[dict[str, Any]]:
        self.get_goal(goal_id)
        result = []
        rows = self.db.db.execute(
            "SELECT * FROM goal_steps WHERE goal_id=? ORDER BY ordinal", (goal_id,)
        ).fetchall()
        for row in rows:
            item = dict(row)
            item["argv"] = _load(item["argv"], list) if item["argv"] is not None else None
            result.append(item)
        return result

    def events(self, goal_id: str) -> list[dict[str, Any]]:
        self.get_goal(goal_id)
        result = []
        rows = self.db.db.execute(
            "SELECT * FROM goal_events WHERE goal_id=? ORDER BY seq", (goal_id,)
        ).fetchall()
        for row in rows:
            item = dict(row)
            item["payload"] = _load(item["payload"], dict)
            result.append(item)
        return result

    def claim_next(self, holder: str, *, ttl: float = 30.0) -> GoalClaim | None:
        if not isinstance(holder, str) or not holder or len(holder) > 256:
            raise ValueError("invalid goal holder")
        row = self.db.db.execute(
            "SELECT goal_id FROM goals WHERE status='ACTIVE' "
            "ORDER BY priority DESC,created_at,goal_id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        goal_id = row[0]
        return GoalClaim(goal_id, self.db.acquire_lease(f"goal:{goal_id}", holder, ttl=ttl))

    def capability_snapshot(self, goal_id: str, runtime_capabilities) -> dict[str, Any]:
        goal = self.get_goal(goal_id)
        runtime = sorted(set(runtime_capabilities))
        if any(not isinstance(item, str) for item in runtime):
            raise ValueError("runtime capabilities must be strings")
        effective = sorted(set(goal["allowed_capabilities"]) & set(runtime) & AUTO_CAPABILITIES)
        return {
            "schema": "ClayVerseGoalCapabilitySnapshot/v1",
            "goal_id": goal_id,
            "entity_generation": self.db.entity_generation(),
            "goal_status": goal["status"],
            "objective": goal["objective"],
            "success_contract": goal["success_contract"],
            "goal_allowed_capabilities": goal["allowed_capabilities"],
            "runtime_capabilities": runtime,
            "effective_capabilities": effective,
            "steps_used": int(goal["steps_used"]),
            "max_steps": int(goal["max_steps"]),
            "truth_rule": "MODEL_PROPOSAL_IS_NOT_EFFECT_OR_SUCCESS_EVIDENCE",
        }

    @staticmethod
    def _proposal(value: dict[str, Any]):
        if not isinstance(value, dict) or set(value) != {"capability", "target", "argv", "summary"}:
            raise ValueError("planner proposal must contain exactly capability,target,argv,summary")
        capability = value["capability"]
        target = value["target"]
        argv = value["argv"]
        summary = value["summary"]
        if capability not in AUTO_CAPABILITIES:
            raise GoalPolicyError("planner proposed non-admitted capability")
        if not isinstance(target, str) or not target or len(target) > 4096 or "\x00" in target:
            raise ValueError("invalid planner target")
        if argv is not None:
            if not isinstance(argv, list) or not argv or len(argv) > 256:
                raise ValueError("argv must be null or a bounded non-empty list")
            if any(
                not isinstance(item, str)
                or not item
                or len(item) > 4096
                or "\x00" in item
                for item in argv
            ):
                raise ValueError("invalid argv item")
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 2000 or "\x00" in summary:
            raise ValueError("proposal summary must be 1..2000 characters")
        normalized = {
            "capability": capability,
            "target": target,
            "argv": argv,
            "summary": summary.strip(),
        }
        return normalized, _sha(_json(normalized))

    def admit_proposal(
        self,
        goal_id: str,
        proposal: dict[str, Any],
        *,
        runtime_capabilities,
        lease: Lease,
    ) -> dict[str, Any]:
        self.db.assert_lease(lease)
        if lease.resource != f"goal:{goal_id}":
            raise GoalPolicyError("goal lease does not match goal")
        proposal, proposal_hash = self._proposal(proposal)
        runtime = set(runtime_capabilities)
        if any(not isinstance(item, str) for item in runtime):
            raise ValueError("runtime capabilities must be strings")

        error: Exception | None = None
        result: dict[str, Any] | None = None
        changed = False
        with self.db.tx() as tx:
            goal = tx.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if goal is None:
                error = KeyError(goal_id)
            elif goal["status"] != "ACTIVE":
                error = GoalPolicyError("goal is not active")
            elif tx.execute(
                "SELECT step_id FROM goal_steps WHERE goal_id=? AND status='ADMITTED' LIMIT 1",
                (goal_id,),
            ).fetchone() is not None:
                error = GoalPolicyError("goal already has an admitted step awaiting evidence")
            else:
                allowed = set(_load(goal["allowed_capabilities"], list))
                capability = proposal["capability"]
                if capability not in allowed:
                    error = GoalPolicyError("proposal exceeds goal capability envelope")
                elif capability not in runtime:
                    now = time.time()
                    tx.execute(
                        "UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                        (now, goal_id),
                    )
                    self._event_tx(
                        tx,
                        goal_id,
                        "GOAL_BLOCKED_CAPABILITY_UNAVAILABLE",
                        {"capability": capability, "proposal_hash": proposal_hash},
                    )
                    changed = True
                    error = GoalPolicyError("proposal capability is not currently available")
                elif int(goal["steps_used"]) >= int(goal["max_steps"]):
                    now = time.time()
                    tx.execute(
                        "UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                        (now, goal_id),
                    )
                    self._event_tx(
                        tx,
                        goal_id,
                        "GOAL_BLOCKED_STEP_BUDGET",
                        {"max_steps": int(goal["max_steps"])},
                    )
                    changed = True
                    error = GoalPolicyError("goal step budget exhausted")
                else:
                    failures = int(
                        tx.execute(
                            "SELECT COUNT(*) FROM goal_steps WHERE goal_id=? AND proposal_hash=? "
                            "AND status IN ('FAILED','UNKNOWN')",
                            (goal_id, proposal_hash),
                        ).fetchone()[0]
                    )
                    if failures > int(goal["max_retries_per_proposal"]):
                        now = time.time()
                        tx.execute(
                            "UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                            (now, goal_id),
                        )
                        self._event_tx(
                            tx,
                            goal_id,
                            "GOAL_BLOCKED_RETRY_BUDGET",
                            {
                                "proposal_hash": proposal_hash,
                                "failed_or_unknown_attempts": failures,
                            },
                        )
                        changed = True
                        error = GoalPolicyError("proposal retry budget exhausted")
                    else:
                        ordinal = int(goal["steps_used"]) + 1
                        step_id = str(uuid.uuid4())
                        now = time.time()
                        generation = self.db.entity_generation()
                        tx.execute(
                            "INSERT INTO goal_steps(step_id,goal_id,ordinal,generation,proposal_hash,capability,target,argv,summary,status,effect_id,admitted_at,observed_at) "
                            "VALUES(?,?,?,?,?,?,?,?,?,'ADMITTED',NULL,?,NULL)",
                            (
                                step_id,
                                goal_id,
                                ordinal,
                                generation,
                                proposal_hash,
                                capability,
                                proposal["target"],
                                _json(proposal["argv"]) if proposal["argv"] is not None else None,
                                proposal["summary"],
                                now,
                            ),
                        )
                        tx.execute(
                            "UPDATE goals SET steps_used=?,updated_at=? WHERE goal_id=?",
                            (ordinal, now, goal_id),
                        )
                        self._event_tx(
                            tx,
                            goal_id,
                            "STEP_ADMITTED",
                            {
                                "proposal_hash": proposal_hash,
                                "capability": capability,
                                "generation": generation,
                                "target_sha256": _sha(proposal["target"]),
                                "argv_sha256": (
                                    _sha(_json(proposal["argv"]))
                                    if proposal["argv"] is not None
                                    else None
                                ),
                            },
                            step_id,
                        )
                        changed = True
                        result = {
                            "step_id": step_id,
                            "goal_id": goal_id,
                            "ordinal": ordinal,
                            "generation": generation,
                            **proposal,
                            "proposal_hash": proposal_hash,
                            "execution_authority": "TURN_LIFECYCLE_EFFECTGATE_ONLY",
                        }
            if changed:
                self._refresh_hash_tx(tx)

        if error is not None:
            raise error
        if result is None:
            raise GoalIntegrityError("goal proposal admission produced no result")
        return result

    @staticmethod
    def _outcome(raw: str | None) -> dict[str, Any] | None:
        if raw is None:
            return None
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise GoalIntegrityError("effect outcome receipt is malformed") from exc
        if not isinstance(value, dict):
            raise GoalIntegrityError("effect outcome receipt is not an object")
        return value

    @staticmethod
    def _matches(step, effect) -> bool:
        expected_target = EffectJournal._payload(EffectJournal._target_receipt(step["target"]))
        argv = _load(step["argv"], list) if step["argv"] is not None else None
        argv_receipt = EffectJournal._argv_receipt(argv)
        expected_argv = _json(argv_receipt) if argv_receipt is not None else None
        return (
            effect["capability"] == step["capability"]
            and effect["target"] == expected_target
            and effect["argv"] == expected_argv
            and int(effect["requested_generation"]) == int(step["generation"])
        )

    def observe_effect(self, step_id: str, effect_id: str) -> dict[str, Any]:
        now = time.time()
        with self.db.tx() as tx:
            step = tx.execute("SELECT * FROM goal_steps WHERE step_id=?", (step_id,)).fetchone()
            if step is None:
                raise KeyError(step_id)
            goal = tx.execute("SELECT * FROM goals WHERE goal_id=?", (step["goal_id"],)).fetchone()
            if goal is None:
                raise GoalIntegrityError("goal missing for step")
            if step["status"] != "ADMITTED":
                if step["effect_id"] == effect_id:
                    return {
                        "step_id": step_id,
                        "goal_id": step["goal_id"],
                        "step_status": step["status"],
                        "goal_status": goal["status"],
                        "effect_id": effect_id,
                        "idempotent": True,
                    }
                raise GoalIntegrityError("step already terminalized with different effect")

            effect = tx.execute("SELECT * FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if effect is None:
                raise KeyError(effect_id)
            if effect["user_id"] != goal["owner_user_id"]:
                raise GoalPolicyError("effect owner does not match goal owner")
            if not self._matches(step, effect):
                raise GoalIntegrityError("effect receipt does not match admitted goal step")

            effect_status = effect["status"]
            outcome = self._outcome(effect["outcome"])
            if effect_status == "VERIFIED" and isinstance(outcome, dict) and outcome.get("ok") is True:
                step_status = "VERIFIED"
            elif effect_status in {"DENIED", "FAILED", "STALE_OUTCOME"}:
                step_status = "FAILED"
            elif effect_status == "UNKNOWN_AFTER_RESTART":
                step_status = "UNKNOWN"
            else:
                raise GoalPolicyError("non-final effect cannot terminalize goal step")

            tx.execute(
                "UPDATE goal_steps SET status=?,effect_id=?,observed_at=? WHERE step_id=?",
                (step_status, effect_id, now, step_id),
            )
            self._event_tx(
                tx,
                step["goal_id"],
                "STEP_EFFECT_OBSERVED",
                {
                    "effect_id": effect_id,
                    "effect_status": effect_status,
                    "step_status": step_status,
                    "outcome_sha256": outcome.get("sha256") if isinstance(outcome, dict) else None,
                    "safe_exit": outcome.get("exit") if isinstance(outcome, dict) else None,
                },
                step_id,
            )

            if step_status == "UNKNOWN":
                tx.execute(
                    "UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                    (now, step["goal_id"]),
                )
                self._event_tx(
                    tx,
                    step["goal_id"],
                    "GOAL_BLOCKED_UNKNOWN_EFFECT",
                    {"effect_id": effect_id},
                    step_id,
                )
            elif self._satisfied_tx(tx, goal):
                tx.execute(
                    "UPDATE goals SET status='SUCCEEDED',updated_at=? WHERE goal_id=?",
                    (now, step["goal_id"]),
                )
                self._event_tx(
                    tx,
                    step["goal_id"],
                    "GOAL_SUCCEEDED_VERIFIED",
                    {"effect_id": effect_id},
                    step_id,
                )
            self._refresh_hash_tx(tx)
            goal_status = tx.execute(
                "SELECT status FROM goals WHERE goal_id=?", (step["goal_id"],)
            ).fetchone()[0]

        return {
            "step_id": step_id,
            "goal_id": step["goal_id"],
            "step_status": step_status,
            "goal_status": goal_status,
            "effect_id": effect_id,
            "idempotent": False,
        }

    def _satisfied_tx(self, tx, goal) -> bool:
        contract = _load(goal["success_contract"], dict)
        if contract.get("type") == "manual":
            return False
        if contract.get("type") != "verified_effects":
            raise GoalIntegrityError("unsupported persisted success contract")
        rows = tx.execute(
            "SELECT s.*,e.status AS effect_status,e.outcome AS effect_outcome "
            "FROM goal_steps s JOIN effects e ON e.effect_id=s.effect_id "
            "WHERE s.goal_id=? AND s.status='VERIFIED' AND e.status='VERIFIED' ORDER BY s.ordinal",
            (goal["goal_id"],),
        ).fetchall()
        for requirement in contract["requirements"]:
            count = 0
            for row in rows:
                if row["capability"] != requirement["capability"]:
                    continue
                if requirement["target"] is not None and row["target"] != requirement["target"]:
                    continue
                outcome = self._outcome(row["effect_outcome"])
                if not isinstance(outcome, dict) or outcome.get("ok") is not True:
                    continue
                expected_exit = requirement.get("exit")
                if expected_exit is not None and outcome.get("exit") != expected_exit:
                    continue
                count += 1
            if count < int(requirement["min_verified"]):
                return False
        return True

    def success_satisfied(self, goal_id: str) -> bool:
        with self.db.tx() as tx:
            goal = tx.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if goal is None:
                raise KeyError(goal_id)
            return self._satisfied_tx(tx, goal)

    def set_status(self, goal_id: str, status: str, *, reason: str) -> None:
        if status not in {"ACTIVE", "PAUSED", "CANCELLED"}:
            raise ValueError("only ACTIVE, PAUSED or CANCELLED may be set explicitly")
        reason = str(reason).strip()
        if not reason or len(reason) > 2000:
            raise ValueError("bounded reason required")
        with self.db.tx() as tx:
            row = tx.execute("SELECT status FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if row is None:
                raise KeyError(goal_id)
            if row["status"] == "SUCCEEDED":
                raise GoalPolicyError("verified succeeded goal cannot be reopened")
            now = time.time()
            tx.execute("UPDATE goals SET status=?,updated_at=? WHERE goal_id=?", (status, now, goal_id))
            if status == "CANCELLED":
                tx.execute(
                    "UPDATE goal_steps SET status='CANCELLED',observed_at=? "
                    "WHERE goal_id=? AND status='ADMITTED'",
                    (now, goal_id),
                )
            self._event_tx(tx, goal_id, f"GOAL_{status}", {"reason": reason})
            self._refresh_hash_tx(tx)

    def recover_after_restart(self) -> dict[str, int]:
        """Fail closed on admitted-but-unbound work; never infer an effect occurred."""
        counts = {"admitted_steps_marked_unknown": 0, "goals_blocked": 0}
        with self.db.tx() as tx:
            rows = tx.execute(
                "SELECT step_id,goal_id FROM goal_steps WHERE status='ADMITTED' "
                "ORDER BY admitted_at,step_id"
            ).fetchall()
            affected = set()
            now = time.time()
            for row in rows:
                tx.execute(
                    "UPDATE goal_steps SET status='UNKNOWN',observed_at=? WHERE step_id=?",
                    (now, row["step_id"]),
                )
                self._event_tx(
                    tx,
                    row["goal_id"],
                    "STEP_UNKNOWN_AFTER_RESTART",
                    {"reason": "admitted_step_has_no_bound_effect_receipt"},
                    row["step_id"],
                )
                affected.add(row["goal_id"])
                counts["admitted_steps_marked_unknown"] += 1
            for goal_id in sorted(affected):
                current = tx.execute(
                    "SELECT status FROM goals WHERE goal_id=?", (goal_id,)
                ).fetchone()
                if current is not None and current["status"] == "ACTIVE":
                    tx.execute(
                        "UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                        (now, goal_id),
                    )
                    self._event_tx(
                        tx,
                        goal_id,
                        "GOAL_BLOCKED_RECOVERY_UNCERTAINTY",
                        {"reason": "unknown_autonomous_step"},
                    )
                    counts["goals_blocked"] += 1
            self._refresh_hash_tx(tx)
        return counts
