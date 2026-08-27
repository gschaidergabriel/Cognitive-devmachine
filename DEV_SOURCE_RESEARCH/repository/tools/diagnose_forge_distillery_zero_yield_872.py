#!/usr/bin/env python3
"""Read-only diagnosis of Forge -> Distillery zero-yield under Supervisor 8.72.

This tool deliberately reuses the canonical Forge evidence audit and never mutates the
Forge ledger or Distillery database. It separates nominal Forge acceptance from current
evidence-qualified acceptance and binds that distinction to the existing Distillery
packet/token ledgers. Global Distillery packet/token baselines may include non-Forge data,
so Forge provenance is inferred only from Forge-specific ingest rows/counters.
Diagnostic success is not runtime/J-Space/training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
from typing import Any

from forge_evidence_credit_871 import audit as forge_audit

SCHEMA = "CLAY_FORGE_DISTILLERY_ZERO_YIELD_DIAGNOSTIC/v2"


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _counter(con: sqlite3.Connection, key: str) -> int:
    if not _table_exists(con, "counters"):
        return 0
    row = con.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def inspect_distillery(db: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(db),
        "missing": not db.exists(),
        "accepted_dataset_tokens_counter": 0,
        "accepted_packets_counter": 0,
        "forge_execution_packets_counter": 0,
        "forge_evidence_qualified_packets_counter": 0,
        "knowledge_packets_total": 0,
        "knowledge_packet_tokens_total": 0,
        "forge_execution_ingest_rows": 0,
        "forge_execution_ingest_tokens_sum": 0,
    }
    if result["missing"]:
        return result
    uri = f"file:{db.resolve()}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        result["accepted_dataset_tokens_counter"] = _counter(con, "accepted_dataset_tokens")
        result["accepted_packets_counter"] = _counter(con, "accepted_packets")
        result["forge_execution_packets_counter"] = _counter(con, "forge_execution_packets")
        result["forge_evidence_qualified_packets_counter"] = _counter(
            con, "forge_evidence_qualified_packets"
        )
        if _table_exists(con, "knowledge_packets"):
            row = con.execute(
                "SELECT COUNT(*),COALESCE(SUM(approx_tokens),0) FROM knowledge_packets"
            ).fetchone()
            result["knowledge_packets_total"] = int(row[0] or 0)
            result["knowledge_packet_tokens_total"] = int(row[1] or 0)
        if _table_exists(con, "forge_execution_ingest"):
            row = con.execute(
                "SELECT COUNT(*),COALESCE(SUM(approx_tokens),0) FROM forge_execution_ingest"
            ).fetchone()
            result["forge_execution_ingest_rows"] = int(row[0] or 0)
            result["forge_execution_ingest_tokens_sum"] = int(row[1] or 0)
    finally:
        con.close()
    return result


def diagnose(forge_ledger: Path, distillery_db: Path) -> dict[str, Any]:
    forge = forge_audit(forge_ledger)
    dist = inspect_distillery(distillery_db)
    nominal = int(forge.get("nominal_accepted", 0) or 0)
    qualified = int(forge.get("evidence_qualified_accepted", 0) or 0)
    ingest_rows = int(dist.get("forge_execution_ingest_rows", 0) or 0)
    ingest_tokens = int(dist.get("forge_execution_ingest_tokens_sum", 0) or 0)
    accepted_tokens = int(dist.get("accepted_dataset_tokens_counter", 0) or 0)
    accepted_packets = int(dist.get("accepted_packets_counter", 0) or 0)
    knowledge_packets = int(dist.get("knowledge_packets_total", 0) or 0)
    knowledge_tokens = int(dist.get("knowledge_packet_tokens_total", 0) or 0)
    forge_packet_counter = int(dist.get("forge_execution_packets_counter", 0) or 0)
    qualified_packet_counter = int(
        dist.get("forge_evidence_qualified_packets_counter", 0) or 0
    )

    forge_specific_db_evidence = bool(
        ingest_rows or forge_packet_counter or qualified_packet_counter
    )
    gate_open = False

    if forge.get("missing"):
        classification = "FORGE_LEDGER_MISSING"
    elif nominal == 0:
        classification = (
            "FORGE_LEDGER_DB_PROVENANCE_UNBOUND"
            if forge_specific_db_evidence
            else "NO_NOMINAL_ACCEPT"
        )
    elif qualified == 0:
        classification = (
            "FORGE_LEDGER_DB_PROVENANCE_UNBOUND"
            if forge_specific_db_evidence
            else "NOMINAL_ACCEPT_NOT_EVIDENCE_QUALIFIED"
        )
    elif dist.get("missing"):
        classification = "QUALIFIED_ACCEPT_DB_MISSING"
    elif ingest_rows == 0:
        classification = "EVIDENCE_QUALIFIED_ACCEPT_NOT_INGESTED"
    elif ingest_rows > qualified:
        classification = "FORGE_LEDGER_DB_PROVENANCE_UNBOUND"
    elif ingest_rows < qualified:
        classification = "EVIDENCE_QUALIFIED_ACCEPT_PARTIALLY_INGESTED"
    elif ingest_tokens <= 0:
        classification = "TOKEN_LEDGER_INCONSISTENT"
    elif accepted_tokens < ingest_tokens or knowledge_tokens < ingest_tokens:
        classification = "TOKEN_LEDGER_INCONSISTENT"
    elif (
        accepted_packets < ingest_rows
        or knowledge_packets < ingest_rows
        or forge_packet_counter != ingest_rows
        or qualified_packet_counter != ingest_rows
    ):
        classification = "FORGE_PACKET_LEDGER_INCONSISTENT"
    else:
        classification = "FORGE_TO_DISTILLERY_DATASET_GATE_OPEN"
        gate_open = True

    return {
        "schema": SCHEMA,
        "gate_open": gate_open,
        "classification": classification,
        "forge": forge,
        "distillery": dist,
        "baseline_semantics": (
            "GLOBAL_DISTILLERY_PACKET_AND_TOKEN_COUNTERS_MAY_INCLUDE_NON_FORGE_DATA;"
            " FORGE_PROVENANCE_REQUIRES_FORGE_SPECIFIC_INGEST_ROWS_OR_COUNTERS"
        ),
        "diagnostic_scope": "READ_ONLY_FORGE_TO_DISTILLERY_LEDGER_CONSISTENCY_ONLY",
        "canonical_truth_credit": 0,
        "whole_entityos_hcu_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-evaluations", type=Path, required=True)
    ap.add_argument("--distillery-db", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(diagnose(args.forge_evaluations, args.distillery_db), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
