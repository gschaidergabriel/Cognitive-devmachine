#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "research_entity" / "architect" / "architect.sqlite"
DEFAULT_STATE = ROOT / "research_entity" / "architect" / "ARCHITECT_STATE.json"


def _rows(con: sqlite3.Connection, sql: str, params=()):
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    except sqlite3.OperationalError:
        return []


def compile_context(db_path: Path, state_path: Path, max_items: int, heads: dict) -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    capsule = {
        "schema": "ARCHITECT_CONTEXT_CAPSULE/v1",
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "architect_id": state.get("architect_id"),
        "generation": state.get("generation"),
        "federation_mode": state.get("federation_mode"),
        "current_focus": state.get("current_focus"),
        "active_goal_ids": state.get("active_goal_ids", []),
        "active_workpackage_ids": state.get("active_workpackage_ids", []),
        "active_hypothesis_ids": state.get("active_hypothesis_ids", []),
        "unresolved_contradictions_from_state": state.get("unresolved_contradictions", []),
        "worker_frontier": state.get("worker_frontier", {}),
        "test_frontier": state.get("test_frontier", {}),
        "next_exact_actions": state.get("next_exact_actions", []),
        "external_heads": heads,
        "episodes": [],
        "decisions": [],
        "hypotheses": [],
        "method_rules": [],
        "contradictions": [],
        "direction_bindings": []
    }
    if db_path.exists():
        con = sqlite3.connect(db_path)
        try:
            capsule["episodes"] = _rows(con, "SELECT * FROM architect_episode ORDER BY generation DESC LIMIT ?", (max_items,))
            capsule["decisions"] = _rows(con, "SELECT * FROM architect_decision WHERE status IN ('ACTIVE','CANDIDATE') ORDER BY generation DESC LIMIT ?", (max_items,))
            capsule["hypotheses"] = _rows(con, "SELECT * FROM architect_hypothesis WHERE status IN ('OPEN','TESTING','UNRESOLVED') ORDER BY generation DESC LIMIT ?", (max_items,))
            capsule["method_rules"] = _rows(con, "SELECT * FROM architect_method_rule WHERE status IN ('PROMOTED','TRIAL','SHADOW') ORDER BY updated_at DESC LIMIT ?", (max_items,))
            capsule["contradictions"] = _rows(con, "SELECT * FROM architect_contradiction WHERE status IN ('OPEN','TESTING','UNRESOLVED') ORDER BY updated_at DESC LIMIT ?", (max_items,))
            capsule["direction_bindings"] = _rows(con, "SELECT * FROM direction_binding WHERE reconciliation_status IN ('CURRENT','CONFLICT','STALE') ORDER BY observed_at DESC LIMIT ?", (max_items * 2,))
        finally:
            con.close()
    digest_source = json.dumps(capsule, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    capsule["context_sha256"] = hashlib.sha256(digest_source).hexdigest()
    return capsule


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--max-items", type=int, default=12)
    parser.add_argument("--heads-json", default="{}")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    capsule = compile_context(args.db, args.state, max(1, args.max_items), json.loads(args.heads_json))
    text = json.dumps(capsule, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
