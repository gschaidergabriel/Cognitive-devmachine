#!/usr/bin/env python3
"""Create the dedicated Architect UnifiedDB from its machine schema.

The Architect DB is intentionally separate from project-canonical stores.  It
contains Architect continuity and typed references back into canonical state.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "research_entity" / "architect" / "ARCHITECT_UNIFIEDDB_SCHEMA.json"
DEFAULT_DB = ROOT / "research_entity" / "architect" / "architect.sqlite"

INTEGER_FIELDS = {
    "generation", "architect_generation", "token_budget", "token_cost",
    "support_count", "counterexample_count"
}
REAL_FIELDS = {"confidence", "latency_ms", "external_action_cost"}


def sql_type(name: str) -> str:
    if name in INTEGER_FIELDS:
        return "INTEGER"
    if name in REAL_FIELDS:
        return "REAL"
    return "TEXT"


def quote_ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise ValueError(f"unsafe identifier: {name!r}")
    return '"' + name + '"'


def bootstrap(schema_path: Path, db_path: Path) -> None:
    spec = json.loads(schema_path.read_text(encoding="utf-8"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            "CREATE TABLE IF NOT EXISTS architect_meta ("
            "key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        for table_name, table_spec in spec["tables"].items():
            fields = list(table_spec["fields"])
            if not fields:
                raise ValueError(f"table without fields: {table_name}")
            cols = []
            for i, field in enumerate(fields):
                col = f"{quote_ident(field)} {sql_type(field)}"
                if i == 0:
                    col += " PRIMARY KEY"
                cols.append(col)
            ddl = f"CREATE TABLE IF NOT EXISTS {quote_ident(table_name)} ({', '.join(cols)})"
            con.execute(ddl)
        con.execute(
            "INSERT OR REPLACE INTO architect_meta(key,value,updated_at) "
            "VALUES('schema', ?, datetime('now'))",
            (spec["schema"],),
        )
        con.execute(
            "INSERT OR REPLACE INTO architect_meta(key,value,updated_at) "
            "VALUES('mode', ?, datetime('now'))",
            (spec["mode"],),
        )
        con.commit()
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    bootstrap(args.schema, args.db)
    print(json.dumps({
        "status": "OK",
        "schema": str(args.schema),
        "db": str(args.db),
        "federation_mode": "SEPARATE_STATE_SHARED_DIRECTION",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
