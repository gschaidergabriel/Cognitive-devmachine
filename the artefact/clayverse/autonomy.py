from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import Lease, LeaseConflict, StaleGeneration, UnifiedDB


class AutonomyError(RuntimeError):
    pass


class GoalContractError(ValueError):
    pass


AUTONOMY_SCHEMA_VERSION = 1
AUTONOMY_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS entity_profile(
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    entity_name TEXT NOT NULL,
    mission TEXT NOT NULL,
    operating_mode TEXT NOT NULL CHECK(operating_mode IN ('HIGH_AGENCY_GROUNDED')),
    identity_version INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS goals(
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    source_turn_id TEXT NOT NULL UNIQUE REFERENCES turns(turn_id),
    objective TEXT NOT NULL,
    success_contract TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','PAUSED','COMPLETED','BLOCKED','CANCELLED')),
    priority INTEGER NOT NULL CHECK(priority BETWEEN -1000 AND 1000),
    max_cycles INTEGER NOT NULL CHECK(max_cycles BETWEEN 1 AND 1000),
    max_failures INTEGER NOT NULL CHECK(max_failures BETWEEN 1 AND 1000),
    cycle_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    blocked_reason TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    completed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_goals_runnable
ON goals(status, priority DESC, created_at, goal_id);
CREATE TABLE IF NOT EXISTS goal_cycles(
    cycle_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
    generation INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('RUNNING','WAITING','EFFECT_RECORDED','FAILED','ABORTED','COMPLETED')),
    proposal_sha256 TEXT,
    proposal_summary TEXT,
    effect_id TEXT REFERENCES effects(effect_id),
    evidence TEXT NOT NULL DEFAULT '{}',
    started_at REAL NOT NULL,
    finished_at REAL,
    UNIQUE(goal_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_goal_cycles_goal
ON goal_cycles(goal_id, ordinal DESC);
CREATE TABLE IF NOT EXISTS goal_confirmations(
    goal_id TEXT PRIMARY KEY REFERENCES goals(goal_id) ON DELETE CASCADE,
    confirmation_turn_id TEXT NOT NULL UNIQUE REFERENCES turns(turn_id),
    confirmed_at REAL NOT NULL
);
'''


@dataclass(frozen=True)
class GoalClaim:
    goal_id: str
    lease: Lease


class AutonomousGoalKernel:
    """Deterministic goal-state and completion authority inside canonical UnifiedDB.

    The kernel deliberately does not infer goals, decide truth from model prose, or
    execute arbitrary actions.  A model/provider may propose a next action, but only
    canonical user turns create goals and only typed external evidence can complete
    them.  This keeps high-agency iteration separate from epistemic authority.
    """

    ENTITY_NAME = "ClayVerse"
    MISSION = (
        "Pursue explicitly admitted user goals proactively while preserving canonical "
        "state, evidence, authorization, bounded resource use, and recoverable causality."
    )
    OPERATING_MODE = "HIGH_AGENCY_GROUNDED"
    MAX_OBJECTIVE_CHARS = 100_000
    MAX_PROPOSAL_SUMMARY_CHARS = 2_000

    def __init__(self, db: UnifiedDB):
        self.db = db
        self._install_schema()

    def _install_schema(self) -> None:
        # Same SQLite connection / same state authority; this is a schema extension,
        # not a second database, agent identity, or lifecycle ledger.
        self.db.db.executescript(AUTONOMY_SCHEMA)
        now = time.time()
        with self.db.tx() as sql:
            sql.execute(
                "INSERT INTO entity_profile(singleton,entity_name,mission,operating_mode,identity_version,updated_at) "
                "VALUES(1,?,?,?,?,?) "
                "ON CONFLICT(singleton) DO UPDATE SET "
                "entity_name=excluded.entity_name,mission=excluded.mission,"
                "operating_mode=excluded.operating_mode,identity_version=excluded.identity_version,updated_at=excluded.updated_at",
                (self.ENTITY_NAME, self.MISSION, self.OPERATING_MODE, AUTONOMY_SCHEMA_VERSION, now),
            )
            sql.execute(
                "INSERT INTO meta(key,value) VALUES('autonomy_schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(AUTONOMY_SCHEMA_VERSION),),
            )
            self._refresh_state_hash_in_tx(sql)

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _clean_text(value: Any, name: str, max_chars: int) -> str:
        if not isinstance(value, str) or not value or len(value) > max_chars or "\x00" in value:
            raise ValueError(f"invalid {name}")
        return value

    @classmethod
    def _normalize_contract(cls, contract: Any) -> dict[str, Any]:
        if not isinstance(contract, dict):
            raise GoalContractError("goal success contract must be an object")
        kind = contract.get("type")
        if kind == "human_confirmation":
            if set(contract) != {"type"}:
                raise GoalContractError("human_confirmation contract has unexpected fields")
            return {"type": "human_confirmation"}
        if kind == "verified_effect":
            expected = {"type", "capability", "target_sha256"}
            if set(contract) != expected:
                raise GoalContractError("verified_effect contract must bind exact capability and target digest")
            capability = contract.get("capability")
            target_sha256 = contract.get("target_sha256")
            if capability != "entityos.exec":
                raise GoalContractError("automatic completion currently requires entityos.exec evidence")
            if (
                not isinstance(target_sha256, str)
                or len(target_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in target_sha256)
            ):
                raise GoalContractError("verified_effect target_sha256 must be lowercase SHA-256")
            return {
                "type": "verified_effect",
                "capability": capability,
                "target_sha256": target_sha256,
            }
        raise GoalContractError("unsupported goal success contract")

    def identity_snapshot(self) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM entity_profile WHERE singleton=1").fetchone()
        if row is None:
            raise AutonomyError("canonical entity profile missing")
        return {
            "entity_name": row["entity_name"],
            "mission": row["mission"],
            "operating_mode": row["operating_mode"],
            "identity_version": int(row["identity_version"]),
            "state_authority": "UnifiedDB",
            "epistemic_law": (
                "Capability, action, progress, and completion claims require canonical evidence; "
                "model statements are proposals, never receipts."
            ),
        }

    def create_goal_from_user_turn(
        self,
        source_turn_id: str,
        success_contract: dict[str, Any],
        *,
        priority: int = 0,
        max_cycles: int = 12,
        max_failures: int = 3,
    ) -> str:
        source_turn_id = self._clean_text(source_turn_id, "source turn id", 256)
        if isinstance(priority, bool) or not isinstance(priority, int) or not -1000 <= priority <= 1000:
            raise ValueError("invalid goal priority")
        if isinstance(max_cycles, bool) or not isinstance(max_cycles, int) or not 1 <= max_cycles <= 1000:
            raise ValueError("invalid max_cycles")
        if isinstance(max_failures, bool) or not isinstance(max_failures, int) or not 1 <= max_failures <= 1000:
            raise ValueError("invalid max_failures")
        contract = self._normalize_contract(success_contract)

        turn = self.db.db.execute(
            "SELECT turn_id,session_id,user_id,role,content FROM turns WHERE turn_id=?",
            (source_turn_id,),
        ).fetchone()
        if turn is None:
            raise KeyError(source_turn_id)
        if turn["role"] != "user":
            raise PermissionError("only a canonical human user turn may create a goal")
        objective = self._clean_text(turn["content"], "goal objective", self.MAX_OBJECTIVE_CHARS)
        self.db.assert_session_owner(turn["session_id"], turn["user_id"])
        self.db.assert_live_generation(turn["session_id"], self.db.session_generation(turn["session_id"]))

        goal_id = str(uuid.uuid4())
        now = time.time()
        with self.db.tx() as sql:
            sql.execute(
                "INSERT INTO goals(goal_id,user_id,session_id,source_turn_id,objective,success_contract,status,priority,max_cycles,max_failures,cycle_count,failure_count,blocked_reason,created_at,updated_at,completed_at) "
                "VALUES(?,?,?,?,?,?,'ACTIVE',?,?,?,0,0,NULL,?,?,NULL)",
                (
                    goal_id,
                    turn["user_id"],
                    turn["session_id"],
                    source_turn_id,
                    objective,
                    self._canonical_json(contract),
                    priority,
                    max_cycles,
                    max_failures,
                    now,
                    now,
                ),
            )
            self._refresh_state_hash_in_tx(sql)
        return goal_id

    def goal(self, goal_id: str) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
        if row is None:
            raise KeyError(goal_id)
        item = dict(row)
        item["success_contract"] = json.loads(item["success_contract"])
        return item

    def runnable_goals(self) -> list[dict[str, Any]]:
        rows = self.db.db.execute(
            "SELECT * FROM goals WHERE status='ACTIVE' "
            "AND cycle_count < max_cycles AND failure_count < max_failures "
            "ORDER BY priority DESC, created_at, goal_id"
        ).fetchall()
        return [dict(row) for row in rows]

    def claim_next(self, worker_id: str, *, ttl: float = 30.0) -> GoalClaim | None:
        worker_id = self._clean_text(worker_id, "worker id", 256)
        if not isinstance(ttl, (int, float)) or isinstance(ttl, bool) or ttl <= 0 or ttl > 300:
            raise ValueError("invalid goal lease ttl")
        self.enforce_budgets()
        for row in self.runnable_goals()[:32]:
            resource = f"goal:{row['goal_id']}"
            try:
                lease = self.db.acquire_lease(resource, worker_id, ttl=float(ttl))
            except LeaseConflict:
                continue
            return GoalClaim(row["goal_id"], lease)
        return None

    def release_claim(self, claim: GoalClaim) -> None:
        lease = claim.lease
        with self.db.tx() as sql:
            sql.execute(
                "DELETE FROM leases WHERE resource=? AND holder=? AND generation=? AND nonce=?",
                (lease.resource, lease.holder, lease.generation, lease.nonce),
            )

    def begin_cycle(self, claim: GoalClaim) -> dict[str, Any]:
        if claim.lease.resource != f"goal:{claim.goal_id}":
            raise AutonomyError("goal claim resource mismatch")
        self.db.assert_lease(claim.lease)
        goal = self.goal(claim.goal_id)
        if goal["status"] != "ACTIVE":
            raise AutonomyError("goal is not active")
        if int(goal["cycle_count"]) >= int(goal["max_cycles"]):
            self.enforce_budgets()
            raise AutonomyError("goal cycle budget exhausted")
        if int(goal["failure_count"]) >= int(goal["max_failures"]):
            self.enforce_budgets()
            raise AutonomyError("goal failure budget exhausted")

        generation = self.db.entity_generation()
        self.db.assert_live_generation(goal["session_id"], generation)
        cycle_id = str(uuid.uuid4())
        now = time.time()
        with self.db.tx() as sql:
            lease = sql.execute(
                "SELECT holder,generation,expires_at,nonce FROM leases WHERE resource=?",
                (claim.lease.resource,),
            ).fetchone()
            if (
                lease is None
                or lease["holder"] != claim.lease.holder
                or int(lease["generation"]) != claim.lease.generation
                or lease["nonce"] != claim.lease.nonce
                or float(lease["expires_at"]) <= now
            ):
                raise StaleGeneration(claim.lease.resource)
            current = sql.execute("SELECT * FROM goals WHERE goal_id=?", (claim.goal_id,)).fetchone()
            if current is None or current["status"] != "ACTIVE":
                raise AutonomyError("goal changed before cycle admission")
            ordinal = int(current["cycle_count"]) + 1
            if ordinal > int(current["max_cycles"]):
                raise AutonomyError("goal cycle budget exhausted")
            cur = sql.execute(
                "UPDATE goals SET cycle_count=?,updated_at=? WHERE goal_id=? AND status='ACTIVE' AND cycle_count=?",
                (ordinal, now, claim.goal_id, int(current["cycle_count"])),
            )
            if cur.rowcount != 1:
                raise AutonomyError("goal changed during cycle admission")
            sql.execute(
                "INSERT INTO goal_cycles(cycle_id,goal_id,generation,ordinal,status,proposal_sha256,proposal_summary,effect_id,evidence,started_at,finished_at) "
                "VALUES(?,?,?,?, 'RUNNING',NULL,NULL,NULL,'{}',?,NULL)",
                (cycle_id, claim.goal_id, generation, ordinal, now),
            )
            self._refresh_state_hash_in_tx(sql)
        return self.cycle_context(cycle_id)

    def cycle_context(self, cycle_id: str) -> dict[str, Any]:
        row = self.db.db.execute(
            "SELECT c.*,g.user_id,g.session_id,g.objective,g.success_contract,g.status AS goal_status,g.max_cycles,g.max_failures,g.cycle_count,g.failure_count "
            "FROM goal_cycles c JOIN goals g ON g.goal_id=c.goal_id WHERE c.cycle_id=?",
            (cycle_id,),
        ).fetchone()
        if row is None:
            raise KeyError(cycle_id)
        return {
            "identity": self.identity_snapshot(),
            "goal": {
                "goal_id": row["goal_id"],
                "user_id": row["user_id"],
                "session_id": row["session_id"],
                "objective": row["objective"],
                "success_contract": json.loads(row["success_contract"]),
                "status": row["goal_status"],
            },
            "cycle": {
                "cycle_id": row["cycle_id"],
                "generation": int(row["generation"]),
                "ordinal": int(row["ordinal"]),
                "status": row["status"],
            },
            "budget": {
                "cycles_used": int(row["cycle_count"]),
                "max_cycles": int(row["max_cycles"]),
                "failures_used": int(row["failure_count"]),
                "max_failures": int(row["max_failures"]),
            },
            "model_authority": "PROPOSAL_ONLY",
            "completion_authority": "DETERMINISTIC_GOAL_KERNEL",
        }

    def record_proposal(self, cycle_id: str, proposal: Any) -> str:
        # Proposals are auditable input to the controller, never evidence of success.
        payload = self._canonical_json(proposal)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if isinstance(proposal, dict):
            text = proposal.get("text", "")
            summary = text if isinstance(text, str) else ""
        else:
            summary = ""
        summary = summary[: self.MAX_PROPOSAL_SUMMARY_CHARS]
        with self.db.tx() as sql:
            row = sql.execute("SELECT status FROM goal_cycles WHERE cycle_id=?", (cycle_id,)).fetchone()
            if row is None:
                raise KeyError(cycle_id)
            if row["status"] != "RUNNING":
                raise AutonomyError("proposal may only be recorded for a running cycle")
            sql.execute(
                "UPDATE goal_cycles SET proposal_sha256=?,proposal_summary=?,status='WAITING' WHERE cycle_id=?",
                (digest, summary, cycle_id),
            )
            self._refresh_state_hash_in_tx(sql)
        return digest

    @staticmethod
    def _effect_target_sha(effect_row: Any) -> str | None:
        try:
            receipt = json.loads(effect_row["target"])
        except (TypeError, json.JSONDecodeError):
            return None
        digest = receipt.get("sha256") if isinstance(receipt, dict) else None
        return digest if isinstance(digest, str) else None

    def record_verified_effect(self, cycle_id: str, effect_id: str) -> bool:
        effect_id = self._clean_text(effect_id, "effect id", 256)
        row = self.db.db.execute(
            "SELECT c.goal_id,c.generation,c.started_at,g.user_id,g.session_id,g.success_contract,e.effect_id,e.user_id AS effect_user,e.capability,e.target,e.requested_generation,e.status,e.outcome,e.ts,ce.causal_id,ce.reentered "
            "FROM goal_cycles c "
            "JOIN goals g ON g.goal_id=c.goal_id "
            "JOIN effects e ON e.effect_id=? "
            "LEFT JOIN causal_episodes ce ON ce.effect_id=e.effect_id "
            "WHERE c.cycle_id=?",
            (effect_id, cycle_id),
        ).fetchone()
        if row is None:
            raise KeyError(cycle_id)
        contract = json.loads(row["success_contract"])
        if contract.get("type") != "verified_effect":
            raise GoalContractError("goal does not accept effect evidence")
        if row["effect_user"] != row["user_id"]:
            raise PermissionError("effect user does not match goal owner")
        if int(row["requested_generation"]) != int(row["generation"]):
            raise StaleGeneration("goal_effect_generation")
        self.db.assert_live_generation(row["session_id"], int(row["generation"]))
        if float(row["ts"]) < float(row["started_at"]):
            raise AutonomyError("effect predates goal cycle")
        if row["status"] != "VERIFIED" or not row["causal_id"] or int(row["reentered"] or 0) != 1:
            raise AutonomyError("effect is not verified and causally re-entered")
        if row["capability"] != contract["capability"]:
            raise AutonomyError("effect capability does not satisfy goal contract")
        if self._effect_target_sha(row) != contract["target_sha256"]:
            raise AutonomyError("effect target does not satisfy goal contract")
        try:
            outcome = json.loads(row["outcome"]) if row["outcome"] else None
        except json.JSONDecodeError as exc:
            raise AutonomyError("verified effect outcome receipt is malformed") from exc
        if not isinstance(outcome, dict) or outcome.get("ok") is not True:
            raise AutonomyError("verified effect lacks positive receipt")

        evidence = {
            "kind": "verified_effect",
            "effect_id": effect_id,
            "causal_id": row["causal_id"],
            "capability": row["capability"],
            "target_sha256": contract["target_sha256"],
            "generation": int(row["generation"]),
        }
        now = time.time()
        with self.db.tx() as sql:
            cycle = sql.execute("SELECT status FROM goal_cycles WHERE cycle_id=?", (cycle_id,)).fetchone()
            if cycle is None:
                raise KeyError(cycle_id)
            if cycle["status"] not in {"RUNNING", "WAITING"}:
                raise AutonomyError("goal cycle is already terminal or has effect evidence")
            sql.execute(
                "UPDATE goal_cycles SET effect_id=?,evidence=?,status='COMPLETED',finished_at=? WHERE cycle_id=?",
                (effect_id, self._canonical_json(evidence), now, cycle_id),
            )
            cur = sql.execute(
                "UPDATE goals SET status='COMPLETED',completed_at=?,updated_at=?,blocked_reason=NULL "
                "WHERE goal_id=? AND status='ACTIVE'",
                (now, now, row["goal_id"]),
            )
            if cur.rowcount != 1:
                raise AutonomyError("goal changed before verified completion")
            self._refresh_state_hash_in_tx(sql)
        return True

    def confirm_goal(self, goal_id: str, confirmation_turn_id: str) -> bool:
        goal = self.goal(goal_id)
        contract = goal["success_contract"]
        if contract.get("type") != "human_confirmation":
            raise GoalContractError("goal does not use human confirmation")
        turn = self.db.db.execute(
            "SELECT session_id,user_id,role,ts FROM turns WHERE turn_id=?",
            (confirmation_turn_id,),
        ).fetchone()
        if turn is None:
            raise KeyError(confirmation_turn_id)
        if turn["role"] != "user" or turn["user_id"] != goal["user_id"] or turn["session_id"] != goal["session_id"]:
            raise PermissionError("confirmation must be a later canonical turn from the goal owner")
        if float(turn["ts"]) < float(goal["created_at"]):
            raise PermissionError("confirmation predates goal")
        now = time.time()
        with self.db.tx() as sql:
            sql.execute(
                "INSERT INTO goal_confirmations(goal_id,confirmation_turn_id,confirmed_at) VALUES(?,?,?)",
                (goal_id, confirmation_turn_id, now),
            )
            cur = sql.execute(
                "UPDATE goals SET status='COMPLETED',completed_at=?,updated_at=?,blocked_reason=NULL "
                "WHERE goal_id=? AND status='ACTIVE'",
                (now, now, goal_id),
            )
            if cur.rowcount != 1:
                raise AutonomyError("goal is not active at confirmation")
            self._refresh_state_hash_in_tx(sql)
        return True

    def fail_cycle(self, cycle_id: str, reason: str) -> dict[str, Any]:
        reason = self._clean_text(reason, "cycle failure reason", 2000)
        now = time.time()
        with self.db.tx() as sql:
            row = sql.execute(
                "SELECT c.goal_id,c.status,g.failure_count,g.max_failures,g.cycle_count,g.max_cycles,g.status AS goal_status "
                "FROM goal_cycles c JOIN goals g ON g.goal_id=c.goal_id WHERE c.cycle_id=?",
                (cycle_id,),
            ).fetchone()
            if row is None:
                raise KeyError(cycle_id)
            if row["status"] not in {"RUNNING", "WAITING"}:
                raise AutonomyError("goal cycle is already terminal")
            failures = int(row["failure_count"]) + 1
            sql.execute(
                "UPDATE goal_cycles SET status='FAILED',evidence=?,finished_at=? WHERE cycle_id=?",
                (self._canonical_json({"kind": "failure", "reason": reason}), now, cycle_id),
            )
            blocked = failures >= int(row["max_failures"]) or int(row["cycle_count"]) >= int(row["max_cycles"])
            status = "BLOCKED" if blocked else row["goal_status"]
            blocked_reason = (
                "failure_budget_exhausted" if failures >= int(row["max_failures"]) else
                "cycle_budget_exhausted" if blocked else None
            )
            sql.execute(
                "UPDATE goals SET failure_count=?,status=?,blocked_reason=?,updated_at=? WHERE goal_id=?",
                (failures, status, blocked_reason, now, row["goal_id"]),
            )
            self._refresh_state_hash_in_tx(sql)
        return self.goal(row["goal_id"])

    def enforce_budgets(self) -> int:
        now = time.time()
        with self.db.tx() as sql:
            cur = sql.execute(
                "UPDATE goals SET status='BLOCKED',blocked_reason=CASE "
                "WHEN failure_count>=max_failures THEN 'failure_budget_exhausted' "
                "ELSE 'cycle_budget_exhausted' END,updated_at=? "
                "WHERE status='ACTIVE' AND (failure_count>=max_failures OR cycle_count>=max_cycles)",
                (now,),
            )
            changed = cur.rowcount
            if changed:
                self._refresh_state_hash_in_tx(sql)
        return int(changed)

    def set_status(self, goal_id: str, status: str, *, reason: str | None = None) -> None:
        if status not in {"ACTIVE", "PAUSED", "BLOCKED", "CANCELLED"}:
            raise ValueError("invalid externally settable goal status")
        if reason is not None:
            reason = self._clean_text(reason, "goal status reason", 2000)
        now = time.time()
        with self.db.tx() as sql:
            row = sql.execute("SELECT status FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if row is None:
                raise KeyError(goal_id)
            if row["status"] in {"COMPLETED", "CANCELLED"}:
                raise AutonomyError("terminal goal cannot be reopened through generic status mutation")
            sql.execute(
                "UPDATE goals SET status=?,blocked_reason=?,updated_at=? WHERE goal_id=?",
                (status, reason, now, goal_id),
            )
            self._refresh_state_hash_in_tx(sql)

    def _refresh_state_hash_in_tx(self, sql: Any) -> str:
        payload = {
            "profile": [dict(row) for row in sql.execute("SELECT * FROM entity_profile ORDER BY singleton")],
            "goals": [dict(row) for row in sql.execute("SELECT * FROM goals ORDER BY goal_id")],
            "cycles": [dict(row) for row in sql.execute("SELECT * FROM goal_cycles ORDER BY goal_id,ordinal")],
            "confirmations": [dict(row) for row in sql.execute("SELECT * FROM goal_confirmations ORDER BY goal_id")],
        }
        digest = hashlib.sha256(self._canonical_json(payload).encode("utf-8")).hexdigest()
        sql.execute(
            "INSERT INTO meta(key,value) VALUES('autonomy_state_hash',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (digest,),
        )
        return digest
