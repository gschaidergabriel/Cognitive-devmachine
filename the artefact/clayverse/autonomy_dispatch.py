from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass

from .autonomy import AutonomyController, AutonomyStateError
from .store import LeaseConflict, StaleGeneration, UnifiedDB

DISPATCH_SCHEMA = "ClayVerseAutonomyDispatch/v1"
DISPATCH_PREFIX = "__CLAY_AUTONOMY_DISPATCH__:"
DISPATCH_TTL_SECONDS = 30.0
DISPATCH_INSTRUCTION_MAX_CHARS = 12_000
_NONCE = re.compile(r"^[0-9a-f]{32}$")


class AutonomyDispatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class AutonomyDispatch:
    user_id: str
    session_id: str
    goal_id: str
    step_id: str
    generation: int
    instruction: str
    nonce: str
    expires_at: float

    @property
    def terminal_prompt(self) -> str:
        return f"{DISPATCH_PREFIX}{self.nonce}"


def _resource(session_id: str) -> str:
    return f"autonomy-dispatch:{session_id}"


def _holder(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _payload(raw: str) -> dict:
    try:
        value = AutonomyController._loads(raw)
    except Exception as exc:
        raise AutonomyDispatchError("dispatch lease payload malformed") from exc
    if set(value) != {"schema", "user_id", "session_id", "goal_id", "step_id", "generation", "instruction"}:
        raise AutonomyDispatchError("dispatch lease payload fields invalid")
    if value.get("schema") != DISPATCH_SCHEMA:
        raise AutonomyDispatchError("dispatch lease schema mismatch")
    instruction = value.get("instruction")
    if not isinstance(instruction, str) or not instruction or len(instruction) > DISPATCH_INSTRUCTION_MAX_CHARS:
        raise AutonomyDispatchError("dispatch instruction invalid")
    return value


def reserve_dispatch(
    db: UnifiedDB,
    *,
    user_id: str,
    goal_id: str,
    step_id: str,
    instruction: str,
    ttl: float = DISPATCH_TTL_SECONDS,
) -> AutonomyDispatch:
    """Reserve exactly one live terminal dispatch for an already-admitted goal step."""
    if user_id not in {"gabriel", "andreas"}:
        raise PermissionError("dispatch requires canonical user")
    session_id = f"session:{user_id}"
    db.assert_session_owner(session_id, user_id)
    generation = db.entity_generation()
    db.assert_live_generation(session_id, generation)
    if not isinstance(ttl, (int, float)) or not 1.0 <= float(ttl) <= 300.0:
        raise ValueError("dispatch ttl out of range")
    if not isinstance(instruction, str) or not instruction or len(instruction) > DISPATCH_INSTRUCTION_MAX_CHARS:
        raise ValueError("dispatch instruction invalid")

    controller = AutonomyController(db)
    snapshot = controller.snapshot(user_id=user_id)
    goal = next((item for item in snapshot["goals"] if item.get("goal_id") == goal_id), None)
    if goal is None:
        raise KeyError(goal_id)
    step = goal.get("current_step")
    if (
        int(goal.get("generation", -1)) != generation
        or goal.get("status") != "ACTIVE"
        or not isinstance(step, dict)
        or step.get("step_id") != step_id
        or step.get("status") != "ADMITTED"
        or step.get("kind") not in {"reason", "effect"}
    ):
        raise AutonomyDispatchError("dispatch target is not one live admitted runnable step")

    payload = {
        "schema": DISPATCH_SCHEMA,
        "user_id": user_id,
        "session_id": session_id,
        "goal_id": goal_id,
        "step_id": step_id,
        "generation": generation,
        "instruction": instruction,
    }
    resource = _resource(session_id)
    now = time.time()
    nonce = uuid.uuid4().hex
    expires_at = now + float(ttl)
    with db.tx() as tx:
        existing = tx.execute("SELECT expires_at FROM leases WHERE resource=?", (resource,)).fetchone()
        if existing is not None and float(existing["expires_at"]) > now:
            raise LeaseConflict(resource)
        previous = tx.execute("SELECT generation FROM leases WHERE resource=?", (resource,)).fetchone()
        lease_generation = int(previous["generation"]) + 1 if previous else 1
        tx.execute(
            "INSERT INTO leases(resource,holder,generation,expires_at,nonce) VALUES(?,?,?,?,?) "
            "ON CONFLICT(resource) DO UPDATE SET holder=excluded.holder,generation=excluded.generation,expires_at=excluded.expires_at,nonce=excluded.nonce",
            (resource, _holder(payload), lease_generation, expires_at, nonce),
        )
    return AutonomyDispatch(
        user_id=user_id,
        session_id=session_id,
        goal_id=goal_id,
        step_id=step_id,
        generation=generation,
        instruction=instruction,
        nonce=nonce,
        expires_at=expires_at,
    )


def consume_dispatch_prompt(
    db: UnifiedDB,
    *,
    user_id: str,
    session_id: str,
    prompt: str,
) -> AutonomyDispatch | None:
    """Consume one live reserved dispatch; reserved-prefix failures never become human input."""
    if not isinstance(prompt, str) or not prompt.startswith(DISPATCH_PREFIX):
        return None
    nonce = prompt[len(DISPATCH_PREFIX) :]
    if not _NONCE.fullmatch(nonce):
        raise AutonomyDispatchError("reserved dispatch prompt malformed")
    if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
        raise PermissionError("dispatch identity mismatch")

    resource = _resource(session_id)
    now = time.time()
    with db.tx() as tx:
        row = tx.execute(
            "SELECT holder,generation,expires_at,nonce FROM leases WHERE resource=?",
            (resource,),
        ).fetchone()
        if row is None:
            raise AutonomyDispatchError("reserved dispatch lease missing")
        if row["nonce"] != nonce:
            raise AutonomyDispatchError("reserved dispatch nonce mismatch")
        if float(row["expires_at"]) <= now:
            raise AutonomyDispatchError("reserved dispatch lease expired")
        payload = _payload(row["holder"])
        live = db.entity_generation()
        if (
            payload["user_id"] != user_id
            or payload["session_id"] != session_id
            or int(payload["generation"]) != live
        ):
            raise StaleGeneration("autonomy-dispatch")
        db.assert_live_generation(session_id, live)
        controller = AutonomyController(db)
        state = controller._load(tx)
        goal = state["goals"].get(payload["goal_id"])
        step = goal.get("current_step") if isinstance(goal, dict) else None
        if (
            goal is None
            or goal.get("user_id") != user_id
            or goal.get("session_id") != session_id
            or int(goal.get("generation", -1)) != live
            or goal.get("status") != "ACTIVE"
            or not isinstance(step, dict)
            or step.get("step_id") != payload["step_id"]
            or step.get("status") != "ADMITTED"
            or step.get("kind") not in {"reason", "effect"}
        ):
            raise AutonomyDispatchError("dispatch lease no longer matches admitted goal step")
        deleted = tx.execute(
            "DELETE FROM leases WHERE resource=? AND nonce=? AND generation=?",
            (resource, nonce, int(row["generation"])),
        )
        if deleted.rowcount != 1:
            raise AutonomyDispatchError("dispatch lease changed during consume")

    return AutonomyDispatch(
        user_id=user_id,
        session_id=session_id,
        goal_id=payload["goal_id"],
        step_id=payload["step_id"],
        generation=int(payload["generation"]),
        instruction=payload["instruction"],
        nonce=nonce,
        expires_at=float(row["expires_at"]),
    )
