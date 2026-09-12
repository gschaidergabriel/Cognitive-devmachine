from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .unified_store import now


RECOVERY_REASON = "RELAY_PROCESS_RESTART_DURING_DISPATCH_NO_AUTOMATIC_REPLAY"
ALLOWED_RELAY_MODULES = frozenset({
    "omega.bridge_relay",
    "omega.spool_bridge_relay",
    "omega.spool_bridge_relay_parallel",
})


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _has_table(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def selected_relay_module(value: str | None = None) -> str:
    """Resolve the effect-capable relay through a hard allow-list.

    The recovery entrypoint runs immediately before a process that can cross an effect
    boundary. Environment configuration therefore selects only named audited OMEGA
    relay modules and can never become an arbitrary Python-module trampoline.
    """

    module = (value if value is not None else os.getenv("OMEGA_RELAY_MODULE", "omega.bridge_relay")).strip()
    if module not in ALLOWED_RELAY_MODULES:
        raise ValueError(f"unsupported relay module: {module!r}")
    return module


def quarantine_inflight(db_path: str | Path) -> list[str]:
    """Fail closed across relay-process death.

    A relay row left in DISPATCHING means the previous process may have crossed the
    external effect boundary before dying. Replaying that effect would violate the
    architecture's no-automatic-replay rule. On every supervised relay start we
    therefore atomically convert abandoned DISPATCHING rows to UNKNOWN and mirror the
    state into effect_intent.

    This deliberately prefers a recoverable unknown outcome over duplicate real-world
    effects. Later reconciliation may attach a matching receipt, but this function
    never republishes the command.
    """

    db = Path(db_path)
    if not db.exists():
        return []

    con = sqlite3.connect(db, timeout=30)
    try:
        con.execute("PRAGMA busy_timeout=30000")
        if not _has_table(con, "relay_ledger") or not _has_table(con, "effect_intent"):
            return []
        con.execute("BEGIN IMMEDIATE")
        rows = con.execute(
            "SELECT effect_id FROM relay_ledger WHERE state='DISPATCHING' ORDER BY created_at,effect_id"
        ).fetchall()
        effect_ids = [str(row[0]) for row in rows]
        if effect_ids:
            t = now()
            con.executemany(
                """
                UPDATE relay_ledger
                   SET state='UNKNOWN', last_error=?, updated_at=?
                 WHERE effect_id=? AND state='DISPATCHING'
                """,
                [(RECOVERY_REASON, t, effect_id) for effect_id in effect_ids],
            )
            con.executemany(
                """
                UPDATE effect_intent
                   SET dispatch_state='UNKNOWN', updated_at=?
                 WHERE effect_id=?
                """,
                [(t, effect_id) for effect_id in effect_ids],
            )
        con.commit()
        return effect_ids
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main() -> int:
    runtime_root = Path(os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    db_path = Path(os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    module = selected_relay_module()

    quarantined = quarantine_inflight(db_path)
    _atomic_json(
        runtime_root / "RELAY_RECOVERY_STATUS.json",
        {
            "schema": "OMEGA_RELAY_RECOVERY_STATUS/v2",
            "at": now(),
            "pid": os.getpid(),
            "relay_module": module,
            "quarantined_effect_ids": quarantined,
            "quarantined_count": len(quarantined),
            "reason": RECOVERY_REASON if quarantined else None,
            "automatic_replay": False,
        },
    )

    os.execv(sys.executable, [sys.executable, "-m", module])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
