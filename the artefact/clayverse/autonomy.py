from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from .effects import EffectGate
from .store import Lease, UnifiedDB

AUTONOMY_SCHEMA_VERSION = 1
AUTONOMY_SCHEMA_KEY = "autonomy_schema_version"
AUTONOMY_DIGEST_KEY = "autonomy_state_digest"
SUPERVISOR_LEASE_RESOURCE = "autonomy:supervisor"
SUPERVISOR_LEASE_TTL = 3600.0

GOAL_STATES = frozenset(
    {"PENDING", "ACTIVE", "BLOCKED", "PAUSED", "SUCCEEDED", "FAILED", "CANCELLED"}
)
TERMINAL_GOAL_STATES = frozenset({"SUCCEEDED", "FAILED", "CANCELLED"})
STEP_STATES = frozenset({"OPEN", "COMPLETED", "FAILED", "BLOCKED", "UNKNOWN"})
MODEL_SELECTIONS = frozenset({"request_effect", "no_effect", "blocked"})
MODEL_KEYS = frozenset({"selection", "effect", "reason"})
NON_PROVING_EFFECTS = frozenset({"state.noop"})
MAX_OBJECTIVE_CHARS = 20_000
MAX_REASON_CHARS = 4_096
MAX_TARGET_CHARS = 4_096
MAX_ARG_CHARS = 4_096
MAX_ARGV = 64
MAX_ARGV_TOTAL_CHARS = 32_768

_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomy_goals(
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    objective TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING','ACTIVE','BLOCKED','PAUSED','SUCCEEDED','FAILED','CANCELLED')),
    priority INTEGER NOT NULL DEFAULT 0,
    allowed_capabilities TEXT NOT NULL,
    verifiers TEXT NOT NULL,
    limits TEXT NOT NULL,
    created_generation INTEGER NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    steps_used INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    effects_used INTEGER NOT NULL DEFAULT 0,
    same_failure_streak INTEGER NOT NULL DEFAULT 0,
    last_failure_fingerprint TEXT
);
CREATE INDEX IF NOT EXISTS idx_autonomy_goals_runnable
ON autonomy_goals(status,priority DESC,created_at,goal_id);

CREATE TABLE IF NOT EXISTS autonomy_steps(
    step_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES autonomy_goals(goal_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('OPEN','COMPLETED','FAILED','BLOCKED','UNKNOWN')),
    proposal_digest TEXT,
    selection TEXT,
    effect_id TEXT,
    causal_id TEXT,
    failure_class TEXT,
    created_at REAL NOT NULL,
    completed_at REAL,
    UNIQUE(goal_id,ordinal)
);
CREATE INDEX IF NOT EXISTS idx_autonomy_steps_goal ON autonomy_steps(goal_id,ordinal);

CREATE TABLE IF NOT EXISTS autonomy_goal_verifications(
    goal_id TEXT NOT NULL REFERENCES autonomy_goals(goal_id) ON DELETE CASCADE,
    verifier_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    ts REAL NOT NULL,
    PRIMARY KEY(goal_id,verifier_id)
);

CREATE TABLE IF NOT EXISTS autonomy_goal_events(
    event_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES autonomy_goals(goal_id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    generation INTEGER NOT NULL,
    step_id TEXT,
    payload TEXT NOT NULL,
    ts REAL NOT NULL,
    UNIQUE(goal_id,seq)
);
CREATE INDEX IF NOT EXISTS idx_autonomy_goal_events_goal
ON autonomy_goal_events(goal_id,seq);
"""


class AutonomyError(RuntimeError):
    pass


class AutonomyIntegrityError(AutonomyError):
    pass


class GoalStateError(AutonomyError):
    pass


class GoalBusy(AutonomyError):
    pass


class ModelDecisionError(AutonomyError):
    pass


class PreEffectAdmissionError(AutonomyError):
    """Executor may raise this only when it can prove no effect started."""


@dataclass(frozen=True)
class GoalLimits:
    max_steps: int = 12
    max_failures: int = 4
    max_effects: int = 6
    max_same_failure: int = 2

    def as_dict(self) -> dict[str, int]:
        return {
            "max_steps": int(self.max_steps),
            "max_failures": int(self.max_failures),
            "max_effects": int(self.max_effects),
            "max_same_failure": int(self.max_same_failure),
        }


@dataclass(frozen=True)
class GoalSnapshot:
    goal_id: str
    user_id: str
    session_id: str
    objective: str
    status: str
    priority: int
    allowed_capabilities: tuple[str, ...]
    verifiers: tuple[dict[str, Any], ...]
    limits: GoalLimits
    created_generation: int
    created_at: float
    updated_at: float
    steps_used: int
    failures: int
    effects_used: int
    same_failure_streak: int
    last_failure_fingerprint: str | None
    verified_ids: tuple[str, ...]


@dataclass(frozen=True)
class GoalStep:
    goal_id: str
    step_id: str
    ordinal: int
    user_id: str
    session_id: str
    generation: int
    goal_resource: str
    step_resource: str


class AutonomyStore:
    """Deterministic goal state machine inside the one canonical UnifiedDB."""

    def __init__(self, db: UnifiedDB):
        self.db = db
        self._ensure_schema()
        self.verify_integrity()

    @staticmethod
    def canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @staticmethod
    def parse_json(raw: str, what: str) -> Any:
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise AutonomyIntegrityError(f"invalid {what}") from exc

    def _ensure_schema(self) -> None:
        # executescript may manage its own transaction. All statements are idempotent;
        # component version/digest admission is then committed under BEGIN IMMEDIATE.
        self.db.db.executescript(_SCHEMA)
        with self.db.tx() as db:
            row = db.execute(
                "SELECT value FROM meta WHERE key=?", (AUTONOMY_SCHEMA_KEY,)
            ).fetchone()
            if row is not None and int(row[0]) != AUTONOMY_SCHEMA_VERSION:
                raise AutonomyIntegrityError("unsupported autonomy schema version")
            db.execute(
                "INSERT INTO meta(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (AUTONOMY_SCHEMA_KEY, str(AUTONOMY_SCHEMA_VERSION)),
            )
            if (
                db.execute(
                    "SELECT 1 FROM meta WHERE key=?", (AUTONOMY_DIGEST_KEY,)
                ).fetchone()
                is None
            ):
                self._refresh_digest_in_tx(db)

    def _state_payload_in_tx(self, db) -> list[Any]:
        specs = (
            ("autonomy_goals", "goal_id"),
            ("autonomy_steps", "goal_id,ordinal,step_id"),
            ("autonomy_goal_verifications", "goal_id,verifier_id"),
            ("autonomy_goal_events", "goal_id,seq,event_id"),
        )
        payload: list[Any] = []
        for table, order in specs:
            payload.append(
                (
                    table,
                    [
                        dict(row)
                        for row in db.execute(
                            f"SELECT * FROM {table} ORDER BY {order}"
                        ).fetchall()
                    ],
                )
            )
        return payload

    def _computed_digest_in_tx(self, db) -> str:
        raw = self.canonical_json(self._state_payload_in_tx(db)).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _refresh_digest_in_tx(self, db) -> str:
        digest = self._computed_digest_in_tx(db)
        db.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (AUTONOMY_DIGEST_KEY, digest),
        )
        return digest

    def verify_integrity(self) -> str:
        with self.db.tx() as db:
            row = db.execute(
                "SELECT value FROM meta WHERE key=?", (AUTONOMY_DIGEST_KEY,)
            ).fetchone()
            if row is None:
                raise AutonomyIntegrityError("autonomy digest missing")
            actual = self._computed_digest_in_tx(db)
            if str(row[0]) != actual:
                raise AutonomyIntegrityError("autonomy state digest mismatch")
            return actual

    @staticmethod
    def _validate_limits(limits: GoalLimits) -> None:
        values = limits.as_dict()
        if not 1 <= values["max_steps"] <= 100:
            raise ValueError("max_steps out of bounds")
        if not 1 <= values["max_failures"] <= 50:
            raise ValueError("max_failures out of bounds")
        if not 0 <= values["max_effects"] <= 50:
            raise ValueError("max_effects out of bounds")
        if not 1 <= values["max_same_failure"] <= 10:
            raise ValueError("max_same_failure out of bounds")

    @staticmethod
    def _normalize_capabilities(values: list[str] | tuple[str, ...]) -> list[str]:
        if not isinstance(values, (list, tuple)):
            raise ValueError("allowed_capabilities must be a list")
        result = sorted(set(values))
        if len(result) > 16:
            raise ValueError("too many capabilities")
        for capability in result:
            if (
                not isinstance(capability, str)
                or capability not in EffectGate.ALLOWED
                or capability == "process.exec"
            ):
                raise ValueError(f"capability not admitted: {capability!r}")
        return result

    @staticmethod
    def _normalize_verifiers(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(values, list) or not values or len(values) > 32:
            raise ValueError("at least one bounded verifier is required")
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("verifier must be an object")
            verifier_id = value.get("id")
            kind = value.get("kind")
            if (
                not isinstance(verifier_id, str)
                or not verifier_id
                or len(verifier_id) > 128
                or verifier_id in seen
            ):
                raise ValueError("invalid or duplicate verifier id")
            seen.add(verifier_id)
            if kind == "effect_verified":
                capability = value.get("capability")
                if (
                    capability not in EffectGate.ALLOWED
                    or capability in NON_PROVING_EFFECTS
                    or capability == "process.exec"
                ):
                    raise ValueError("effect verifier requires a proving capability")
                result.append(
                    {"id": verifier_id, "kind": kind, "capability": capability}
                )
            elif kind == "checkpoint":
                prefix = value.get("note_prefix", "")
                if not isinstance(prefix, str) or len(prefix) > 512:
                    raise ValueError("invalid checkpoint note_prefix")
                result.append(
                    {"id": verifier_id, "kind": kind, "note_prefix": prefix}
                )
            elif kind == "user_ack":
                result.append({"id": verifier_id, "kind": kind})
            else:
                raise ValueError("unsupported verifier kind")
        return result

    def _append_event_in_tx(
        self,
        db,
        goal_id: str,
        event_type: str,
        generation: int,
        payload: dict[str, Any] | None = None,
        *,
        step_id: str | None = None,
    ) -> None:
        seq = int(
            db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM autonomy_goal_events WHERE goal_id=?",
                (goal_id,),
            ).fetchone()[0]
        )
        db.execute(
            "INSERT INTO autonomy_goal_events(event_id,goal_id,seq,event_type,generation,step_id,payload,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                goal_id,
                seq,
                event_type,
                int(generation),
                step_id,
                self.canonical_json(payload or {}),
                time.time(),
            ),
        )

    def _row_to_snapshot(self, row) -> GoalSnapshot:
        allowed = self.parse_json(row["allowed_capabilities"], "allowed_capabilities")
        verifiers = self.parse_json(row["verifiers"], "verifiers")
        limits_raw = self.parse_json(row["limits"], "limits")
        if (
            not isinstance(allowed, list)
            or not isinstance(verifiers, list)
            or not isinstance(limits_raw, dict)
        ):
            raise AutonomyIntegrityError("invalid goal envelope")
        limits = GoalLimits(
            max_steps=int(limits_raw["max_steps"]),
            max_failures=int(limits_raw["max_failures"]),
            max_effects=int(limits_raw["max_effects"]),
            max_same_failure=int(limits_raw["max_same_failure"]),
        )
        self._validate_limits(limits)
        status = str(row["status"])
        if status not in GOAL_STATES:
            raise AutonomyIntegrityError("invalid goal status")
        verified_ids = tuple(
            r["verifier_id"]
            for r in self.db.db.execute(
                "SELECT verifier_id FROM autonomy_goal_verifications "
                "WHERE goal_id=? ORDER BY verifier_id",
                (row["goal_id"],),
            ).fetchall()
        )
        return GoalSnapshot(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            objective=row["objective"],
            status=status,
            priority=int(row["priority"]),
            allowed_capabilities=tuple(allowed),
            verifiers=tuple(verifiers),
            limits=limits,
            created_generation=int(row["created_generation"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            steps_used=int(row["steps_used"]),
            failures=int(row["failures"]),
            effects_used=int(row["effects_used"]),
            same_failure_streak=int(row["same_failure_streak"]),
            last_failure_fingerprint=row["last_failure_fingerprint"],
            verified_ids=verified_ids,
        )

    def get(self, goal_id: str) -> GoalSnapshot:
        self.verify_integrity()
        row = self.db.db.execute(
            "SELECT * FROM autonomy_goals WHERE goal_id=?", (goal_id,)
        ).fetchone()
        if row is None:
            raise KeyError(goal_id)
        return self._row_to_snapshot(row)

    def list(self) -> list[GoalSnapshot]:
        self.verify_integrity()
        rows = self.db.db.execute(
            "SELECT * FROM autonomy_goals "
            "ORDER BY priority DESC,created_at,goal_id"
        ).fetchall()
        return [self._row_to_snapshot(row) for row in rows]

    def create_goal(
        self,
        user_id: str,
        objective: str,
        *,
        verifiers: list[dict[str, Any]],
        allowed_capabilities: list[str] | tuple[str, ...] = (),
        limits: GoalLimits | None = None,
        priority: int = 0,
    ) -> str:
        objective = str(objective).strip()
        if not objective or len(objective) > MAX_OBJECTIVE_CHARS:
            raise ValueError("invalid objective")
        if not -1000 <= int(priority) <= 1000:
            raise ValueError("priority out of bounds")
        session_id = f"session:{user_id}"
        self.db.assert_session_owner(session_id, user_id)
        generation = self.db.entity_generation()
        self.db.assert_live_generation(session_id, generation)
        capabilities = self._normalize_capabilities(allowed_capabilities)
        normalized_verifiers = self._normalize_verifiers(verifiers)
        limits = limits or GoalLimits()
        self._validate_limits(limits)
        goal_id = str(uuid.uuid4())
        now = time.time()
        with self.db.tx() as db:
            db.execute(
                "INSERT INTO autonomy_goals("
                "goal_id,user_id,session_id,objective,status,priority,allowed_capabilities,"
                "verifiers,limits,created_generation,created_at,updated_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    goal_id,
                    user_id,
                    session_id,
                    objective,
                    "PENDING",
                    int(priority),
                    self.canonical_json(capabilities),
                    self.canonical_json(normalized_verifiers),
                    self.canonical_json(limits.as_dict()),
                    generation,
                    now,
                    now,
                ),
            )
            self._append_event_in_tx(
                db,
                goal_id,
                "GOAL_CREATED",
                generation,
                {
                    "verifier_ids": [item["id"] for item in normalized_verifiers],
                    "allowed_capabilities": capabilities,
                    "limits": limits.as_dict(),
                },
            )
            self._refresh_digest_in_tx(db)
        return goal_id

    def _transition(
        self,
        goal_id: str,
        user_id: str,
        from_states: set[str],
        to_state: str,
        event_type: str,
        reason: str,
    ) -> GoalSnapshot:
        if to_state not in GOAL_STATES:
            raise ValueError(to_state)
        with self.db.tx() as db:
            row = db.execute(
                "SELECT * FROM autonomy_goals WHERE goal_id=?", (goal_id,)
            ).fetchone()
            if row is None:
                raise KeyError(goal_id)
            if row["user_id"] != user_id:
                raise PermissionError("goal owner mismatch")
            if row["status"] not in from_states:
                raise GoalStateError(
                    f"cannot transition {row['status']} -> {to_state}"
                )
            if db.execute(
                "SELECT 1 FROM autonomy_steps WHERE goal_id=? AND status='OPEN'",
                (goal_id,),
            ).fetchone():
                raise GoalBusy("goal has an open step")
            generation = self.db.entity_generation()
            self.db.assert_live_generation(row["session_id"], generation)
            db.execute(
                "UPDATE autonomy_goals SET status=?,updated_at=? WHERE goal_id=?",
                (to_state, time.time(), goal_id),
            )
            self._append_event_in_tx(
                db,
                goal_id,
                event_type,
                generation,
                {"reason": str(reason)[:512], "by": user_id},
            )
            self._refresh_digest_in_tx(db)
        return self.get(goal_id)

    def activate(self, goal_id: str, user_id: str) -> GoalSnapshot:
        return self._transition(
            goal_id,
            user_id,
            {"PENDING", "PAUSED", "BLOCKED"},
            "ACTIVE",
            "GOAL_ACTIVATED",
            "user_or_program_activation",
        )

    def pause(self, goal_id: str, user_id: str) -> GoalSnapshot:
        return self._transition(
            goal_id, user_id, {"PENDING", "ACTIVE", "BLOCKED"}, "PAUSED", "GOAL_PAUSED", "user_pause"
        )

    def cancel(self, goal_id: str, user_id: str) -> GoalSnapshot:
        return self._transition(
            goal_id,
            user_id,
            {"PENDING", "ACTIVE", "BLOCKED", "PAUSED"},
            "CANCELLED",
            "GOAL_CANCELLED",
            "user_cancel",
        )

    def _verifier(self, snapshot: GoalSnapshot, verifier_id: str) -> dict[str, Any]:
        for verifier in snapshot.verifiers:
            if verifier.get("id") == verifier_id:
                return verifier
        raise KeyError(verifier_id)

    def _record_verification(
        self,
        snapshot: GoalSnapshot,
        verifier_id: str,
        evidence_type: str,
        evidence_id: str,
    ) -> bool:
        if snapshot.status in TERMINAL_GOAL_STATES:
            raise GoalStateError("terminal goal cannot accept evidence")
        generation = self.db.entity_generation()
        self.db.assert_live_generation(snapshot.session_id, generation)
        with self.db.tx() as db:
            existing = db.execute(
                "SELECT evidence_type,evidence_id FROM autonomy_goal_verifications "
                "WHERE goal_id=? AND verifier_id=?",
                (snapshot.goal_id, verifier_id),
            ).fetchone()
            if existing is not None:
                if (
                    existing["evidence_type"] == evidence_type
                    and existing["evidence_id"] == evidence_id
                ):
                    return False
                raise GoalStateError("verifier already bound to different evidence")
            db.execute(
                "INSERT INTO autonomy_goal_verifications("
                "goal_id,verifier_id,evidence_type,evidence_id,generation,ts"
                ") VALUES(?,?,?,?,?,?)",
                (
                    snapshot.goal_id,
                    verifier_id,
                    evidence_type,
                    evidence_id,
                    generation,
                    time.time(),
                ),
            )
            self._append_event_in_tx(
                db,
                snapshot.goal_id,
                "VERIFICATION_RECORDED",
                generation,
                {
                    "verifier_id": verifier_id,
                    "evidence_type": evidence_type,
                    "evidence_id": evidence_id,
                },
            )
            self._maybe_succeed_in_tx(db, snapshot.goal_id, generation)
            self._refresh_digest_in_tx(db)
        return True

    def record_checkpoint(
        self, goal_id: str, verifier_id: str, checkpoint_id: str
    ) -> bool:
        snapshot = self.get(goal_id)
        verifier = self._verifier(snapshot, verifier_id)
        if verifier.get("kind") != "checkpoint":
            raise ValueError("wrong verifier kind")
        row = self.db.db.execute(
            "SELECT checkpoint_id,ts,note FROM checkpoints WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        if row is None:
            raise KeyError(checkpoint_id)
        if float(row["ts"]) < snapshot.created_at:
            raise GoalStateError("checkpoint predates goal")
        prefix = verifier.get("note_prefix", "")
        if prefix and not str(row["note"]).startswith(prefix):
            raise GoalStateError("checkpoint does not match verifier")
        return self._record_verification(
            snapshot, verifier_id, "checkpoint", checkpoint_id
        )

    def record_user_ack(self, goal_id: str, verifier_id: str, user_id: str) -> bool:
        snapshot = self.get(goal_id)
        if snapshot.user_id != user_id:
            raise PermissionError("goal owner mismatch")
        verifier = self._verifier(snapshot, verifier_id)
        if verifier.get("kind") != "user_ack":
            raise ValueError("wrong verifier kind")
        return self._record_verification(
            snapshot, verifier_id, "user_ack", f"user:{user_id}"
        )

    def _all_verified_in_tx(self, db, goal_id: str) -> bool:
        row = db.execute(
            "SELECT verifiers FROM autonomy_goals WHERE goal_id=?", (goal_id,)
        ).fetchone()
        required = {
            item["id"]
            for item in self.parse_json(row["verifiers"], "verifiers")
        }
        found = {
            item["verifier_id"]
            for item in db.execute(
                "SELECT verifier_id FROM autonomy_goal_verifications WHERE goal_id=?",
                (goal_id,),
            ).fetchall()
        }
        return bool(required) and required == found

    def _maybe_succeed_in_tx(self, db, goal_id: str, generation: int) -> bool:
        row = db.execute(
            "SELECT status FROM autonomy_goals WHERE goal_id=?", (goal_id,)
        ).fetchone()
        if row is None:
            raise KeyError(goal_id)
        if row["status"] in TERMINAL_GOAL_STATES:
            return row["status"] == "SUCCEEDED"
        if db.execute(
            "SELECT 1 FROM autonomy_steps WHERE goal_id=? AND status='OPEN'",
            (goal_id,),
        ).fetchone():
            return False
        if not self._all_verified_in_tx(db, goal_id):
            return False
        db.execute(
            "UPDATE autonomy_goals SET status='SUCCEEDED',updated_at=? WHERE goal_id=?",
            (time.time(), goal_id),
        )
        self._append_event_in_tx(
            db,
            goal_id,
            "GOAL_SUCCEEDED",
            generation,
            {"basis": "all_typed_verifiers_satisfied"},
        )
        return True

    @staticmethod
    def _fingerprint(failure_class: str) -> str:
        return hashlib.sha256(failure_class.encode("utf-8")).hexdigest()

    def begin_step(self, snapshot: GoalSnapshot) -> GoalStep | None:
        if snapshot.status != "ACTIVE":
            raise GoalStateError("goal is not active")
        generation = self.db.entity_generation()
        self.db.assert_live_generation(snapshot.session_id, generation)
        with self.db.tx() as db:
            row = db.execute(
                "SELECT * FROM autonomy_goals WHERE goal_id=?", (snapshot.goal_id,)
            ).fetchone()
            if row is None or row["status"] != "ACTIVE":
                raise GoalStateError("goal changed before step admission")
            if db.execute(
                "SELECT 1 FROM autonomy_steps WHERE goal_id=? AND status='OPEN'",
                (snapshot.goal_id,),
            ).fetchone():
                raise GoalBusy("goal already has an open step")
            limits = self.parse_json(row["limits"], "limits")
            budget_reason = None
            if int(row["steps_used"]) >= int(limits["max_steps"]):
                budget_reason = "max_steps"
            elif int(row["failures"]) >= int(limits["max_failures"]):
                budget_reason = "max_failures"
            elif int(row["same_failure_streak"]) >= int(limits["max_same_failure"]):
                budget_reason = "repeated_failure"
            if budget_reason:
                state = "BLOCKED" if budget_reason == "repeated_failure" else "FAILED"
                event = "GOAL_BLOCKED" if state == "BLOCKED" else "GOAL_FAILED"
                db.execute(
                    "UPDATE autonomy_goals SET status=?,updated_at=? WHERE goal_id=?",
                    (state, time.time(), snapshot.goal_id),
                )
                self._append_event_in_tx(
                    db,
                    snapshot.goal_id,
                    event,
                    generation,
                    {"reason": budget_reason},
                )
                self._refresh_digest_in_tx(db)
                return None
            ordinal = int(row["steps_used"]) + 1
            step_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO autonomy_steps("
                "step_id,goal_id,ordinal,generation,status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                (
                    step_id,
                    snapshot.goal_id,
                    ordinal,
                    generation,
                    "OPEN",
                    time.time(),
                ),
            )
            db.execute(
                "UPDATE autonomy_goals SET steps_used=steps_used+1,updated_at=? WHERE goal_id=?",
                (time.time(), snapshot.goal_id),
            )
            self._append_event_in_tx(
                db,
                snapshot.goal_id,
                "STEP_STARTED",
                generation,
                {"ordinal": ordinal},
                step_id=step_id,
            )
            self._refresh_digest_in_tx(db)
        return GoalStep(
            goal_id=snapshot.goal_id,
            step_id=step_id,
            ordinal=ordinal,
            user_id=snapshot.user_id,
            session_id=snapshot.session_id,
            generation=generation,
            goal_resource=f"goal:{snapshot.goal_id}",
            step_resource=f"goal-step:{step_id}",
        )

    def record_proposal(self, step: GoalStep, proposal: dict[str, Any]) -> None:
        canonical = self.canonical_json(proposal)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.db.tx() as db:
            row = db.execute(
                "SELECT status,generation FROM autonomy_steps WHERE step_id=? AND goal_id=?",
                (step.step_id, step.goal_id),
            ).fetchone()
            if row is None or row["status"] != "OPEN":
                raise GoalStateError("step is not open")
            if int(row["generation"]) != step.generation:
                raise GoalStateError("step generation mismatch")
            cur = db.execute(
                "UPDATE autonomy_steps SET proposal_digest=?,selection=? "
                "WHERE step_id=? AND proposal_digest IS NULL",
                (digest, proposal["selection"], step.step_id),
            )
            if cur.rowcount != 1:
                raise GoalStateError("step already has a proposal")
            self._append_event_in_tx(
                db,
                step.goal_id,
                "MODEL_PROPOSAL_RECORDED",
                step.generation,
                {
                    "selection": proposal["selection"],
                    "proposal_sha256": digest,
                    "model_output_is_authority": False,
                },
                step_id=step.step_id,
            )
            self._refresh_digest_in_tx(db)

    def _close_step_in_tx(
        self,
        db,
        step: GoalStep,
        status: str,
        *,
        effect_id: str | None = None,
        causal_id: str | None = None,
        failure_class: str | None = None,
    ) -> None:
        if status not in STEP_STATES or status == "OPEN":
            raise ValueError(status)
        cur = db.execute(
            "UPDATE autonomy_steps SET status=?,effect_id=?,causal_id=?,failure_class=?,completed_at=? "
            "WHERE step_id=? AND goal_id=? AND status='OPEN'",
            (
                status,
                effect_id,
                causal_id,
                failure_class,
                time.time(),
                step.step_id,
                step.goal_id,
            ),
        )
        if cur.rowcount != 1:
            raise GoalStateError("step is no longer open")

    def complete_no_effect(self, step: GoalStep) -> GoalSnapshot:
        with self.db.tx() as db:
            self._close_step_in_tx(db, step, "COMPLETED")
            db.execute(
                "UPDATE autonomy_goals SET same_failure_streak=0,last_failure_fingerprint=NULL,updated_at=? "
                "WHERE goal_id=?",
                (time.time(), step.goal_id),
            )
            self._append_event_in_tx(
                db,
                step.goal_id,
                "STEP_COMPLETED",
                step.generation,
                {"effect": False},
                step_id=step.step_id,
            )
            self._maybe_succeed_in_tx(db, step.goal_id, step.generation)
            self._refresh_digest_in_tx(db)
        return self.get(step.goal_id)

    def fail_step(self, step: GoalStep, failure_class: str) -> GoalSnapshot:
        failure_class = str(failure_class)[:128]
        fingerprint = self._fingerprint(failure_class)
        with self.db.tx() as db:
            row = db.execute(
                "SELECT failures,same_failure_streak,last_failure_fingerprint FROM autonomy_goals "
                "WHERE goal_id=?",
                (step.goal_id,),
            ).fetchone()
            if row is None:
                raise KeyError(step.goal_id)
            streak = (
                int(row["same_failure_streak"]) + 1
                if row["last_failure_fingerprint"] == fingerprint
                else 1
            )
            self._close_step_in_tx(
                db, step, "FAILED", failure_class=failure_class
            )
            db.execute(
                "UPDATE autonomy_goals SET failures=failures+1,same_failure_streak=?,"
                "last_failure_fingerprint=?,updated_at=? WHERE goal_id=?",
                (streak, fingerprint, time.time(), step.goal_id),
            )
            self._append_event_in_tx(
                db,
                step.goal_id,
                "STEP_FAILED",
                step.generation,
                {"failure_class": failure_class},
                step_id=step.step_id,
            )
            self._refresh_digest_in_tx(db)
        return self.get(step.goal_id)

    def block_step(self, step: GoalStep, reason: str, *, unknown: bool = False) -> GoalSnapshot:
        event_generation = self.db.entity_generation()
        with self.db.tx() as db:
            self._close_step_in_tx(
                db,
                step,
                "UNKNOWN" if unknown else "BLOCKED",
                failure_class=str(reason)[:128],
            )
            db.execute(
                "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                (time.time(), step.goal_id),
            )
            self._append_event_in_tx(
                db,
                step.goal_id,
                "GOAL_BLOCKED",
                event_generation,
                {"reason": str(reason)[:512], "unknown_outcome": bool(unknown)},
                step_id=step.step_id,
            )
            self._refresh_digest_in_tx(db)
        return self.get(step.goal_id)

    def record_effect(self, step: GoalStep, effect_id: str) -> GoalSnapshot:
        """Bind only an actually persisted effect on this goal-step resource path."""
        effect = self.db.db.execute(
            "SELECT * FROM effects WHERE effect_id=?", (effect_id,)
        ).fetchone()
        if effect is None:
            raise AutonomyIntegrityError("effect receipt missing")
        if effect["user_id"] != step.user_id:
            raise AutonomyIntegrityError("effect user mismatch")
        if int(effect["requested_generation"]) != step.generation:
            raise AutonomyIntegrityError("effect generation mismatch")
        status = str(effect["status"])
        if status == "PENDING":
            raise GoalBusy("effect is still pending")
        causal = self.db.db.execute(
            "SELECT causal_id,episode_id,observation_turn_id FROM causal_episodes "
            "WHERE effect_id=? ORDER BY ts DESC LIMIT 1",
            (effect_id,),
        ).fetchone()
        if causal is None:
            raise AutonomyIntegrityError("effect has no causal re-entry")
        turn = self.db.db.execute(
            "SELECT session_id,user_id,resource_refs FROM turns WHERE turn_id=?",
            (causal["observation_turn_id"],),
        ).fetchone()
        if turn is None:
            raise AutonomyIntegrityError("effect observation turn missing")
        if turn["session_id"] != step.session_id or turn["user_id"] != step.user_id:
            raise AutonomyIntegrityError("effect turn identity mismatch")
        resources = self.parse_json(turn["resource_refs"], "effect resource refs")
        if (
            not isinstance(resources, list)
            or step.goal_resource not in resources
            or step.step_resource not in resources
        ):
            raise AutonomyIntegrityError("effect is not bound to this goal step")
        snapshot = self.get(step.goal_id)
        if effect["capability"] not in snapshot.allowed_capabilities:
            raise AutonomyIntegrityError("effect capability outside goal contract")

        with self.db.tx() as db:
            step_state = (
                "COMPLETED"
                if status == "VERIFIED"
                else "UNKNOWN"
                if status == "UNKNOWN_AFTER_RESTART"
                else "FAILED"
            )
            self._close_step_in_tx(
                db,
                step,
                step_state,
                effect_id=effect_id,
                causal_id=causal["causal_id"],
                failure_class=None if status == "VERIFIED" else f"effect_{status.lower()}",
            )
            db.execute(
                "UPDATE autonomy_goals SET effects_used=effects_used+1,updated_at=? WHERE goal_id=?",
                (time.time(), step.goal_id),
            )
            self._append_event_in_tx(
                db,
                step.goal_id,
                "EFFECT_RECEIPT_BOUND",
                step.generation,
                {
                    "effect_id": effect_id,
                    "causal_id": causal["causal_id"],
                    "status": status,
                    "capability": effect["capability"],
                },
                step_id=step.step_id,
            )
            if status == "UNKNOWN_AFTER_RESTART":
                db.execute(
                    "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=?",
                    (time.time(), step.goal_id),
                )
                self._append_event_in_tx(
                    db,
                    step.goal_id,
                    "GOAL_BLOCKED",
                    step.generation,
                    {"reason": "effect_outcome_unknown_after_restart", "unknown_outcome": True},
                    step_id=step.step_id,
                )
            elif status == "VERIFIED":
                db.execute(
                    "UPDATE autonomy_goals SET same_failure_streak=0,last_failure_fingerprint=NULL "
                    "WHERE goal_id=?",
                    (step.goal_id,),
                )
                self._append_event_in_tx(
                    db,
                    step.goal_id,
                    "STEP_COMPLETED",
                    step.generation,
                    {"effect": True, "effect_id": effect_id},
                    step_id=step.step_id,
                )
                receipt = self.parse_json(effect["outcome"], "effect outcome")
                if isinstance(receipt, dict) and receipt.get("ok") is True:
                    verifiers = self.parse_json(
                        db.execute(
                            "SELECT verifiers FROM autonomy_goals WHERE goal_id=?",
                            (step.goal_id,),
                        ).fetchone()[0],
                        "goal verifiers",
                    )
                    for verifier in verifiers:
                        if (
                            verifier.get("kind") == "effect_verified"
                            and verifier.get("capability") == effect["capability"]
                            and effect["capability"] not in NON_PROVING_EFFECTS
                        ):
                            exists = db.execute(
                                "SELECT 1 FROM autonomy_goal_verifications "
                                "WHERE goal_id=? AND verifier_id=?",
                                (step.goal_id, verifier["id"]),
                            ).fetchone()
                            if exists:
                                continue
                            db.execute(
                                "INSERT INTO autonomy_goal_verifications("
                                "goal_id,verifier_id,evidence_type,evidence_id,generation,ts"
                                ") VALUES(?,?,?,?,?,?)",
                                (
                                    step.goal_id,
                                    verifier["id"],
                                    "effect",
                                    effect_id,
                                    step.generation,
                                    time.time(),
                                ),
                            )
                            self._append_event_in_tx(
                                db,
                                step.goal_id,
                                "VERIFICATION_RECORDED",
                                step.generation,
                                {
                                    "verifier_id": verifier["id"],
                                    "evidence_type": "effect",
                                    "evidence_id": effect_id,
                                },
                                step_id=step.step_id,
                            )
                self._maybe_succeed_in_tx(db, step.goal_id, step.generation)
            else:
                failure_class = f"effect_{status.lower()}"
                self._append_event_in_tx(
                    db,
                    step.goal_id,
                    "STEP_FAILED",
                    step.generation,
                    {"failure_class": failure_class, "effect_id": effect_id},
                    step_id=step.step_id,
                )
                fingerprint = self._fingerprint(failure_class)
                goal_row = db.execute(
                    "SELECT same_failure_streak,last_failure_fingerprint FROM autonomy_goals "
                    "WHERE goal_id=?",
                    (step.goal_id,),
                ).fetchone()
                streak = (
                    int(goal_row["same_failure_streak"]) + 1
                    if goal_row["last_failure_fingerprint"] == fingerprint
                    else 1
                )
                db.execute(
                    "UPDATE autonomy_goals SET failures=failures+1,same_failure_streak=?,"
                    "last_failure_fingerprint=? WHERE goal_id=?",
                    (streak, fingerprint, step.goal_id),
                )
            self._refresh_digest_in_tx(db)
        return self.get(step.goal_id)

    def event_log(self, goal_id: str) -> list[dict[str, Any]]:
        self.verify_integrity()
        rows = self.db.db.execute(
            "SELECT * FROM autonomy_goal_events WHERE goal_id=? ORDER BY seq",
            (goal_id,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        expected = 1
        for row in rows:
            if int(row["seq"]) != expected:
                raise AutonomyIntegrityError("goal event sequence gap")
            expected += 1
            item = dict(row)
            item["payload"] = self.parse_json(item["payload"], "event payload")
            out.append(item)
        return out


class AutonomySupervisor:
    """Bounded autonomous goal loop; cognition proposes, code decides state."""

    def __init__(self, db: UnifiedDB, *, entityos_bridge=None):
        self.db = db
        self.store = AutonomyStore(db)
        self.effect_gate = EffectGate(
            db, allow_process=False, entityos_bridge=entityos_bridge
        )

    def _lease(self) -> Lease:
        return self.db.acquire_lease(
            SUPERVISOR_LEASE_RESOURCE,
            f"autonomy:{uuid.uuid4().hex}",
            ttl=SUPERVISOR_LEASE_TTL,
        )

    def _release(self, lease: Lease) -> None:
        with self.db.tx() as db:
            db.execute(
                "DELETE FROM leases WHERE resource=? AND holder=? AND generation=? AND nonce=?",
                (
                    lease.resource,
                    lease.holder,
                    lease.generation,
                    lease.nonce,
                ),
            )

    def _has_open_step(self, goal_id: str) -> bool:
        return (
            self.db.db.execute(
                "SELECT 1 FROM autonomy_steps WHERE goal_id=? AND status='OPEN'",
                (goal_id,),
            ).fetchone()
            is not None
        )

    def _select_runnable(self) -> GoalSnapshot | None:
        for snapshot in self.store.list():
            if snapshot.status != "ACTIVE":
                continue
            # Human/canonical interactive turns have priority. Autonomy never aborts one.
            if self.db.db.execute(
                "SELECT 1 FROM active_turns WHERE session_id=?",
                (snapshot.session_id,),
            ).fetchone():
                continue
            if self._has_open_step(snapshot.goal_id):
                # After lease loss/crash we cannot assume whether an executor acted.
                # Close ambiguity by blocking, never by automatic retry.
                open_row = self.db.db.execute(
                    "SELECT * FROM autonomy_steps WHERE goal_id=? AND status='OPEN' "
                    "ORDER BY ordinal LIMIT 1",
                    (snapshot.goal_id,),
                ).fetchone()
                step = GoalStep(
                    goal_id=snapshot.goal_id,
                    step_id=open_row["step_id"],
                    ordinal=int(open_row["ordinal"]),
                    user_id=snapshot.user_id,
                    session_id=snapshot.session_id,
                    generation=int(open_row["generation"]),
                    goal_resource=f"goal:{snapshot.goal_id}",
                    step_resource=f"goal-step:{open_row['step_id']}",
                )
                self.store.block_step(
                    step, "open_step_after_supervisor_lease_loss", unknown=True
                )
                continue
            return snapshot
        return None

    def context_for(self, step: GoalStep) -> dict[str, Any]:
        snapshot = self.store.get(step.goal_id)
        available = set(self.effect_gate.available_capabilities())
        allowed = sorted(set(snapshot.allowed_capabilities).intersection(available))
        return {
            "schema": "clayverse.autonomy_step/v1",
            "operational_identity": {
                "persistent_state_authority": "UnifiedDB",
                "mode": "autonomous_goal_execution",
                "entity_generation": step.generation,
                "user_id": step.user_id,
                "session_id": step.session_id,
                "model_role": "planner_cognition_not_authority",
            },
            "goal": {
                "goal_id": snapshot.goal_id,
                "objective": snapshot.objective,
                "status": snapshot.status,
                "step_id": step.step_id,
                "step_ordinal": step.ordinal,
                "verifiers": list(snapshot.verifiers),
                "verified_ids": list(snapshot.verified_ids),
            },
            "budgets": {
                "remaining_steps": max(
                    0, snapshot.limits.max_steps - snapshot.steps_used
                ),
                "remaining_failures": max(
                    0, snapshot.limits.max_failures - snapshot.failures
                ),
                "remaining_effects": max(
                    0, snapshot.limits.max_effects - snapshot.effects_used
                ),
            },
            "capabilities": allowed,
            "required_resource_refs_for_executor": [
                step.goal_resource,
                step.step_resource,
            ],
            "laws": {
                "model_output_is_proposal_only": True,
                "model_cannot_create_or_rewrite_goals": True,
                "model_cannot_mark_goal_succeeded": True,
                "success_requires_all_typed_verifiers": True,
                "effect_execution_requires_canonical_effectgate_receipt": True,
                "unknown_effect_outcome_is_not_success": True,
                "capabilities_not_listed_here_do_not_exist_for_this_step": True,
            },
        }

    def validate_proposal(
        self, step: GoalStep, raw: Any
    ) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ModelDecisionError("proposal must be an object")
        if set(raw) - MODEL_KEYS:
            raise ModelDecisionError("proposal contains non-authoritative fields")
        selection = raw.get("selection")
        if selection not in MODEL_SELECTIONS:
            raise ModelDecisionError("unsupported proposal selection")
        reason = raw.get("reason", "")
        if not isinstance(reason, str) or len(reason) > MAX_REASON_CHARS:
            raise ModelDecisionError("invalid proposal reason")
        effect = raw.get("effect")
        snapshot = self.store.get(step.goal_id)
        if selection == "request_effect":
            if snapshot.effects_used >= snapshot.limits.max_effects:
                raise ModelDecisionError("goal effect budget exhausted")
            if not isinstance(effect, dict) or set(effect) - {
                "capability",
                "target",
                "argv",
            }:
                raise ModelDecisionError("invalid effect proposal")
            capability = effect.get("capability")
            target = effect.get("target")
            argv = effect.get("argv")
            if capability not in snapshot.allowed_capabilities:
                raise ModelDecisionError("capability outside goal contract")
            if capability not in self.effect_gate.available_capabilities():
                raise ModelDecisionError("capability unavailable at runtime")
            if capability == "process.exec":
                raise ModelDecisionError("generic process execution is forbidden")
            if (
                not isinstance(target, str)
                or not target
                or len(target) > MAX_TARGET_CHARS
            ):
                raise ModelDecisionError("invalid target")
            if argv is not None:
                if not isinstance(argv, list) or len(argv) > MAX_ARGV:
                    raise ModelDecisionError("invalid argv")
                total = 0
                for item in argv:
                    if not isinstance(item, str) or len(item) > MAX_ARG_CHARS:
                        raise ModelDecisionError("invalid argv item")
                    total += len(item)
                if total > MAX_ARGV_TOTAL_CHARS:
                    raise ModelDecisionError("argv too large")
        elif effect is not None:
            raise ModelDecisionError("effect supplied without request_effect")
        proposal = {"selection": selection, "effect": effect, "reason": reason}
        self.store.record_proposal(step, proposal)
        return proposal

    def commit_executor_receipt(
        self, step: GoalStep, proposal: dict[str, Any], receipt: Any
    ) -> GoalSnapshot:
        if proposal["selection"] == "blocked":
            return self.store.block_step(step, proposal["reason"] or "model_blocked")
        if proposal["selection"] == "no_effect":
            if receipt != {"kind": "no_effect"}:
                # Executor contract is uncertain; do not retry an ambiguous step.
                return self.store.block_step(
                    step, "malformed_no_effect_executor_receipt", unknown=True
                )
            return self.store.complete_no_effect(step)
        if not isinstance(receipt, dict) or set(receipt) != {"kind", "effect_id"}:
            return self.store.block_step(
                step, "malformed_effect_executor_receipt", unknown=True
            )
        if receipt.get("kind") != "effect" or not isinstance(
            receipt.get("effect_id"), str
        ):
            return self.store.block_step(
                step, "malformed_effect_executor_receipt", unknown=True
            )
        try:
            return self.store.record_effect(step, receipt["effect_id"])
        except GoalBusy:
            raise
        except AutonomyIntegrityError:
            return self.store.block_step(
                step, "unverifiable_effect_executor_receipt", unknown=True
            )

    def tick(
        self,
        planner: Callable[[dict[str, Any]], Any],
        executor: Callable[[GoalStep, dict[str, Any], dict[str, Any]], Any],
    ) -> dict[str, Any]:
        lease = self._lease()
        try:
            snapshot = self._select_runnable()
            if snapshot is None:
                return {"status": "IDLE", "reason": "no_runnable_goal"}
            step = self.store.begin_step(snapshot)
            if step is None:
                return {
                    "status": "LIMIT_REACHED",
                    "goal": self.store.get(snapshot.goal_id),
                }
            context = self.context_for(step)
            try:
                proposal = self.validate_proposal(step, planner(context))
            except ModelDecisionError:
                goal = self.store.fail_step(step, "model_decision_invalid")
                return {"status": "STEP_FAILED", "goal": goal, "step": step}
            except Exception:
                goal = self.store.fail_step(step, "planner_error")
                return {"status": "STEP_FAILED", "goal": goal, "step": step}

            if proposal["selection"] == "blocked":
                goal = self.store.block_step(
                    step, proposal["reason"] or "planner_blocked"
                )
                return {"status": "BLOCKED", "goal": goal, "step": step}

            try:
                receipt = executor(step, proposal, context)
            except PreEffectAdmissionError:
                goal = self.store.fail_step(step, "pre_effect_admission_error")
                return {"status": "STEP_FAILED", "goal": goal, "step": step}
            except Exception:
                # The executor may have crossed the effect boundary before failing.
                # Never infer "nothing happened"; block with explicit uncertainty.
                goal = self.store.block_step(
                    step, "executor_outcome_unknown", unknown=True
                )
                return {"status": "UNKNOWN_BLOCKED", "goal": goal, "step": step}

            goal = self.commit_executor_receipt(step, proposal, receipt)
            status = (
                "SUCCEEDED"
                if goal.status == "SUCCEEDED"
                else "BLOCKED"
                if goal.status == "BLOCKED"
                else "STEP_COMMITTED"
            )
            return {
                "status": status,
                "goal": goal,
                "step": step,
                "receipt": receipt,
            }
        finally:
            self._release(lease)

    def run_bounded(
        self,
        planner: Callable[[dict[str, Any]], Any],
        executor: Callable[[GoalStep, dict[str, Any], dict[str, Any]], Any],
        *,
        max_ticks: int = 4,
    ) -> list[dict[str, Any]]:
        if not isinstance(max_ticks, int) or not 1 <= max_ticks <= 8:
            raise ValueError("max_ticks must be between 1 and 8")
        results: list[dict[str, Any]] = []
        for _ in range(max_ticks):
            result = self.tick(planner, executor)
            results.append(result)
            goal = result.get("goal")
            if result["status"] in {"IDLE", "LIMIT_REACHED", "UNKNOWN_BLOCKED"}:
                break
            if isinstance(goal, GoalSnapshot) and goal.status in (
                TERMINAL_GOAL_STATES | {"BLOCKED", "PAUSED"}
            ):
                break
        return results
