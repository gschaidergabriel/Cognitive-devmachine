#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import socket
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SCHEMA = ROOT / "research_entity/runtime/RAE_UNIFIEDDB_SCHEMA.sql"
U11_SQL = ROOT / "research_entity/trigger_runs/unifieddb/unifieddb-20260810T2335p0700-chatgpt-secondary-u11-pcamf/U11_PROOF_CARRYING_RECEIPT_LATTICE_CANDIDATE.sql"
KINDS = ["GWT_USE", "EFFECT_ATTEMPT", "VERIFIED_OUTCOME", "CAUSAL_CREDIT", "ADMITTED_DELTA", "REENTRY", "TERMINAL_DONE"]
EDGE_KINDS = ["ATTEMPTS", "VERIFIES", "CREDITS", "ADMITS", "REENTERS", "CLOSES"]
EXECUTION_ID = "u11-target-exec"
LEASE_EPOCH = 91
START_EPOCH = 1000


def digest(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def quantiles_us(samples_ns: list[int]) -> dict:
    values = sorted(v / 1000.0 for v in samples_ns)
    if not values:
        return {"n": 0}
    def pick(p: float) -> float:
        i = min(len(values) - 1, max(0, int(round((len(values) - 1) * p))))
        return values[i]
    return {
        "n": len(values),
        "p50": pick(0.50),
        "p95": pick(0.95),
        "p99": pick(0.99),
        "min": values[0],
        "max": values[-1],
        "mean": statistics.fmean(values),
    }


def setup_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.executescript(BASE_SCHEMA.read_text(encoding="utf-8"))
    con.executescript(U11_SQL.read_text(encoding="utf-8"))
    con.execute("CREATE TABLE IF NOT EXISTS u11_probe_current_execution(singleton INTEGER PRIMARY KEY CHECK(singleton=1), execution_id TEXT NOT NULL, lease_epoch INTEGER NOT NULL, state TEXT NOT NULL)")
    con.execute("INSERT OR REPLACE INTO u11_probe_current_execution VALUES(1,?,?,?)", (EXECUTION_ID, LEASE_EPOCH, "ACTIVE"))
    parent = None
    for i in range(len(KINDS)):
        epoch = START_EPOCH + i
        con.execute(
            "INSERT INTO state_epochs(epoch,parent_epoch,tx_id,root_hash,committed_at,writer_node) VALUES(?,?,?,?,?,?)",
            (epoch, parent, None, digest("epoch", str(epoch)), "2026-08-10T17:00:00Z", "u11-target-probe"),
        )
        parent = epoch
    con.commit()
    return con


def seed_valid_chain(con: sqlite3.Connection) -> list[str]:
    ids = []
    for i, kind in enumerate(KINDS):
        rid = f"u11-r{i}-{kind.lower()}"
        ids.append(rid)
        con.execute(
            "INSERT INTO u11_receipt_registry(receipt_id,receipt_kind,state_epoch,execution_id,lease_epoch,payload_hash,source_ref,verified,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (rid, kind, START_EPOCH + i, EXECUTION_ID, LEASE_EPOCH, digest(rid, kind, "payload"), "target-vps-probe", 1, "2026-08-10T17:00:00Z"),
        )
    for i, edge_kind in enumerate(EDGE_KINDS, start=1):
        con.execute(
            "INSERT INTO u11_receipt_edges(child_receipt_id,parent_receipt_id,edge_kind) VALUES(?,?,?)",
            (ids[i], ids[i - 1], edge_kind),
        )
    terminal = ids[-1]
    con.execute(
        "INSERT INTO u11_terminal_receipts(terminal_receipt_id,execution_id,lease_epoch,state_epoch,chain_root_hash,terminal_class,closure_validator_version,closed_at) VALUES(?,?,?,?,?,?,?,?)",
        (terminal, EXECUTION_ID, LEASE_EPOCH, START_EPOCH + len(KINDS) - 1, digest(*ids), "DONE", "u11-target-v1", "2026-08-10T17:00:00Z"),
    )
    con.commit()
    return ids


def validate_chain(con: sqlite3.Connection, ids: list[str], execution_id: str = EXECUTION_ID, lease_epoch: int = LEASE_EPOCH) -> bool:
    active = con.execute("SELECT execution_id,lease_epoch,state FROM u11_probe_current_execution WHERE singleton=1").fetchone()
    if active != (execution_id, lease_epoch, "ACTIVE"):
        return False
    if len(ids) != len(KINDS):
        return False
    for rid, expected_kind in zip(ids, KINDS):
        row = con.execute(
            "SELECT receipt_kind,execution_id,lease_epoch,verified FROM u11_receipt_registry WHERE receipt_id=?",
            (rid,),
        ).fetchone()
        if row != (expected_kind, execution_id, lease_epoch, 1):
            return False
    for i, edge_kind in enumerate(EDGE_KINDS, start=1):
        if con.execute(
            "SELECT 1 FROM u11_receipt_edges WHERE child_receipt_id=? AND parent_receipt_id=? AND edge_kind=?",
            (ids[i], ids[i - 1], edge_kind),
        ).fetchone() is None:
            return False
    terminal = con.execute(
        "SELECT execution_id,lease_epoch,state_epoch,terminal_class,closure_validator_version FROM u11_terminal_receipts WHERE terminal_receipt_id=?",
        (ids[-1],),
    ).fetchone()
    return terminal == (execution_id, lease_epoch, START_EPOCH + len(KINDS) - 1, "DONE", "u11-target-v1")


def mutation_falsifier(con: sqlite3.Connection, ids: list[str], n: int = 10000) -> dict:
    mutation_types = ["fabricated_ref", "stale_lease", "wrong_execution", "cross_kind", "missing_ref", "unverified_outcome", "missing_edge"]
    false_accepts = 0
    counts = {k: 0 for k in mutation_types}
    for j in range(n):
        kind = mutation_types[j % len(mutation_types)]
        counts[kind] += 1
        refs = list(ids)
        ex = EXECUTION_ID
        lease = LEASE_EPOCH
        restore = None
        if kind == "fabricated_ref":
            refs[j % len(refs)] = f"fake-{j}"
        elif kind == "stale_lease":
            lease = LEASE_EPOCH - 1
        elif kind == "wrong_execution":
            ex = "other-execution"
        elif kind == "cross_kind":
            refs[0], refs[1] = refs[1], refs[0]
        elif kind == "missing_ref":
            refs[j % len(refs)] = ""
        elif kind == "unverified_outcome":
            con.execute("UPDATE u11_receipt_registry SET verified=0 WHERE receipt_kind='VERIFIED_OUTCOME'")
            restore = lambda: con.execute("UPDATE u11_receipt_registry SET verified=1 WHERE receipt_kind='VERIFIED_OUTCOME'")
        elif kind == "missing_edge":
            child = ids[3]
            parent = ids[2]
            edge = EDGE_KINDS[2]
            con.execute("DELETE FROM u11_receipt_edges WHERE child_receipt_id=? AND parent_receipt_id=? AND edge_kind=?", (child, parent, edge))
            restore = lambda: con.execute("INSERT INTO u11_receipt_edges VALUES(?,?,?)", (child, parent, edge))
        if validate_chain(con, refs, ex, lease):
            false_accepts += 1
        if restore:
            restore()
    con.commit()
    return {"mutations": n, "counts": counts, "false_accepts": false_accepts, "false_accept_rate": false_accepts / n}


def latency_probe(con: sqlite3.Connection, ids: list[str], n: int = 20000) -> dict:
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        ok = validate_chain(con, ids)
        samples.append(time.perf_counter_ns() - t0)
        if not ok:
            raise AssertionError("valid receipt chain rejected")
    return quantiles_us(samples)


def recovery_probe(db_path: Path, ids: list[str]) -> dict:
    # Close/reopen durable state.
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    restart_ok = validate_chain(con, ids)
    integrity_before = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_before = con.execute("PRAGMA foreign_key_check").fetchall()

    # Uncommitted write must disappear on close/reopen.
    con.execute("BEGIN IMMEDIATE")
    con.execute(
        "INSERT INTO u11_associative_fields(field_id,field_kind,source_state_epoch,build_hash,model_or_index_hash,admissibility_clay,calibration_clay,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
        ("uncommitted-field", "OTHER", START_EPOCH, "b", "m", "{}", "{}", "SHADOW", "2026-08-10T17:00:00Z"),
    )
    con.close()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    uncommitted_present = con.execute("SELECT COUNT(*) FROM u11_associative_fields WHERE field_id='uncommitted-field'").fetchone()[0]

    # Online backup API and restore equivalence.
    with tempfile.TemporaryDirectory() as td:
        backup_path = Path(td) / "backup.sqlite"
        dst = sqlite3.connect(backup_path)
        con.backup(dst)
        dst.close()
        restored = sqlite3.connect(backup_path)
        restored.execute("PRAGMA foreign_keys=ON")
        restore_chain_ok = validate_chain(restored, ids)
        integrity_after = restored.execute("PRAGMA integrity_check").fetchone()[0]
        fk_after = restored.execute("PRAGMA foreign_key_check").fetchall()
        restored.close()
    con.close()
    return {
        "restart_chain_ok": restart_ok,
        "integrity_before": integrity_before,
        "foreign_key_violations_before": len(fk_before),
        "uncommitted_write_present_after_reopen": int(uncommitted_present),
        "backup_restore_chain_ok": restore_chain_ok,
        "integrity_after_restore": integrity_after,
        "foreign_key_violations_after_restore": len(fk_after),
    }


def environment() -> dict:
    cpu_model = "UNKNOWN"
    mem_total_kb = "UNKNOWN"
    try:
        for line in Path("/proc/cpuinfo").read_text(errors="ignore").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except Exception:
        pass
    try:
        for line in Path("/proc/meminfo").read_text(errors="ignore").splitlines():
            if line.startswith("MemTotal:"):
                mem_total_kb = line.split(":", 1)[1].strip()
                break
    except Exception:
        pass
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "cpu_model": cpu_model,
        "memory_total": mem_total_kb,
        "pid": os.getpid(),
    }


def run(output: Path) -> dict:
    t_start = time.perf_counter_ns()
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "u11_target.sqlite"
        con = setup_db(db_path)
        journal = con.execute("PRAGMA journal_mode").fetchone()[0]
        synchronous = con.execute("PRAGMA synchronous").fetchone()[0]
        ids = seed_valid_chain(con)
        valid = validate_chain(con, ids)
        mutations = mutation_falsifier(con, ids)
        latency = latency_probe(con, ids)
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        con.close()
        recovery = recovery_probe(db_path, ids)
    elapsed_ms = (time.perf_counter_ns() - t_start) / 1e6
    checks = {
        "valid_chain": valid,
        "mutation_false_accepts_zero": mutations["false_accepts"] == 0,
        "integrity_ok": integrity == "ok",
        "foreign_keys_ok": len(fk) == 0,
        "restart_chain_ok": recovery["restart_chain_ok"],
        "uncommitted_rollback_ok": recovery["uncommitted_write_present_after_reopen"] == 0,
        "backup_restore_chain_ok": recovery["backup_restore_chain_ok"],
        "restore_integrity_ok": recovery["integrity_after_restore"] == "ok",
        "restore_foreign_keys_ok": recovery["foreign_key_violations_after_restore"] == 0,
    }
    passed = all(checks.values())
    result = {
        "schema_version": "1.0",
        "receipt_id": "UNIFIEDDB-U11-PCAMF-TARGET-VPS-PROOF-GATE",
        "evidence_class": "EXECUTED_ENVIRONMENT_SUBSYSTEM_EVIDENCE",
        "scope": "U11 receipt-lattice/schema/restart/backup proof gate; NOT whole Frank v0.1 acceptance",
        "source": {
            "base_schema": str(BASE_SCHEMA.relative_to(ROOT)),
            "u11_sql": str(U11_SQL.relative_to(ROOT)),
            "base_schema_sha256": hashlib.sha256(BASE_SCHEMA.read_bytes()).hexdigest(),
            "u11_sql_sha256": hashlib.sha256(U11_SQL.read_bytes()).hexdigest(),
        },
        "environment": environment(),
        "sqlite_runtime": {"journal_mode": journal, "synchronous_numeric": synchronous},
        "checks": checks,
        "mutation_falsifier": mutations,
        "validation_latency_us": latency,
        "recovery": recovery,
        "resource_shadow": {
            "elapsed_ms": elapsed_ms,
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "status": "PASS" if passed else "FAIL",
        "promotion": "TARGET_SUBSYSTEM_EVIDENCE_ONLY; U11/Frank promotion remains separately gated",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = run(Path(args.output))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
