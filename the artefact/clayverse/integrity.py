from __future__ import annotations

import hashlib
import json
import time
import uuid

CANONICAL_TABLES = (
    "meta",
    "users",
    "sessions",
    "turns",
    "durable_memory",
    "workspace_episodes",
    "effects",
    "causal_episodes",
    "leases",
)
SEAL_PREFIX = "integrity:v1:"


class IntegrityViolation(RuntimeError):
    pass


def state_digest(db) -> str:
    """Digest canonical state only; ClayGraph/checkpoints are derived evidence."""
    payload = []
    for table in CANONICAL_TABLES:
        rows = [dict(r) for r in db.db.execute(f"SELECT * FROM {table} ORDER BY 1")]
        payload.append((table, rows))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal(db, note: str) -> tuple[str, str]:
    digest = state_digest(db)
    checkpoint_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO checkpoints(checkpoint_id,ts,state_hash,note) VALUES(?,?,?,?)",
        (checkpoint_id, time.time(), digest, SEAL_PREFIX + note),
    )
    return checkpoint_id, digest


def verify_latest(db) -> dict | None:
    """Fail closed if canonical state drifted since the last v1 integrity seal.

    Legacy checkpoints are deliberately ignored because they used a weaker table set.
    """
    row = db.db.execute(
        "SELECT checkpoint_id,state_hash,note FROM checkpoints WHERE note LIKE ? ORDER BY ts DESC,rowid DESC LIMIT 1",
        (SEAL_PREFIX + "%",),
    ).fetchone()
    if row is None:
        return None
    actual = state_digest(db)
    if actual != row["state_hash"]:
        raise IntegrityViolation(
            f"canonical UnifiedDB state diverges from integrity seal {row['checkpoint_id']}"
        )
    return {"checkpoint_id": row["checkpoint_id"], "state_hash": actual, "note": row["note"]}
