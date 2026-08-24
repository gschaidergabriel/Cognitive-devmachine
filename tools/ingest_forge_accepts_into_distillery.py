#!/usr/bin/env python3
"""Admit only evidence-qualified Forge ACCEPTED evaluations into Distillery.

Historical/nominal Forge acceptance remains append-only but is not sufficient for
current dataset credit. Admission delegates the acceptance boundary to
``forge_evidence_credit_871.evidence_reason`` so Distillery requires the same exact
source identities plus CLAY_FORGE_EXECUTION_ADMISSION/v1, isolated execution backend,
command admission and secret fences as current Forge evidence credit.

Only measured fields enter packet_text. Model-authored hypothesis/falsifier remain
candidate-only metadata. Distillery idempotence is bound to a replay-stable execution
evidence identity rather than the byte digest of the full evaluation envelope, so a
changed observation timestamp, candidate narration or evaluation ``delta_id`` cannot
mint a second dataset packet. If the same execution identity reappears with conflicting
measured evidence, admission fails closed instead of treating the mutation as a new
observation.

Replay identity v2 excludes ``delta_id`` because it names the evaluation/candidate
envelope, not the measured execution. Rows written under replay identity v1 are
backfilled to v2 from their already-persisted packet/metadata evidence. Rows too old or
incomplete to reconstruct v2 are treated as unresolved and fail closed on overlapping
execution coordinates until explicitly reconciled.

The destination is the existing Distillery SQLite database; this module performs no
provider/network I/O and creates no second truth/effect path.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any

from forge_evidence_credit_871 import evidence_reason

ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
DEFAULT_FORGE_EVAL = Path(os.getenv("CLAY_FORGE_EVAL_PATH", str(ARTIFACT_ROOT / "forge/architecture_delta_evaluations.jsonl")))
DEFAULT_DISTILLERY_DB = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DB", str(ARTIFACT_ROOT / "distillery/distillery.sqlite3")))


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4)) if text else 0


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def admission_reason(row: Any) -> tuple[bool, str]:
    """Use the single current Forge evidence-credit discriminator."""
    return evidence_reason(row)


def measured_packet(row: dict) -> dict:
    """Return dataset text containing measured evidence, never candidate narration."""
    execution_admission = row.get("execution_admission")
    return {
        "schema": "CLAY_DISTILLERY_FORGE_EXECUTION_PACKET/v2",
        "evidence_class": "FORGE_EVIDENCE_QUALIFIED_EXECUTION",
        "evidence_qualification": "EVIDENCE_QUALIFIED_ACCEPT",
        "canonical_truth": False,
        "training_scope": "EXECUTION_EVIDENCE_ONLY_NOT_JSPACE_CAUSAL_CREDIT",
        "delta_id": str(row.get("delta_id") or ""),
        "worker_sha": row["worker_sha"],
        "source_repo_head": row["source_repo_head"],
        "evaluation_repo_head": row["evaluation_repo_head"],
        "target_blob_identities": row["target_blob_identities"],
        "execution_admission_sha256": digest_json(execution_admission),
        "metric": str(row.get("metric") or ""),
        "relative_improvement_pct": float(row["relative_improvement_pct"]),
        "reproducible_runs": int(row["reproducible_runs"]),
        "tests_passed": int(row["tests_passed"]),
        "tests_failed": int(row["tests_failed"]),
        "negative_tests_passed": int(row.get("negative_tests_passed") or 0),
        "negative_tests_failed": int(row["negative_tests_failed"]),
        "static_checks_passed": int(row.get("static_checks_passed") or 0),
        "static_checks_failed": int(row["static_checks_failed"]),
        "benchmark_non_regression": True,
        "requires_rebase_to_evaluation_head": bool(row.get("requires_rebase_to_evaluation_head", False)),
        "evaluated_at": str(row.get("evaluated_at") or ""),
    }


def legacy_execution_replay_identity_v1(row: dict) -> dict:
    """Return the historical v1 replay key for migration/provenance only."""
    return {
        "schema": "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v1",
        "delta_id": str(row.get("delta_id") or ""),
        "source_class": str(row.get("source_class") or ""),
        "provider": str(row.get("provider") or ""),
        "model": str(row.get("model") or ""),
        "role": str(row.get("role") or ""),
        "worker_sha": row["worker_sha"],
        "source_repo_head": row["source_repo_head"],
        "evaluation_repo_head": row["evaluation_repo_head"],
        "target_blob_identities": row["target_blob_identities"],
        "execution_admission_sha256": digest_json(row.get("execution_admission")),
        "metric": str(row.get("metric") or ""),
        "requires_rebase_to_evaluation_head": bool(row.get("requires_rebase_to_evaluation_head", False)),
    }


def execution_replay_identity(row: dict) -> dict:
    """Bind one replay-stable measured execution family.

    Observation time, candidate narration and ``delta_id`` are evaluation-envelope
    metadata and are intentionally excluded. The identity binds source/provenance,
    target bytes, admitted execution surface and metric definition so envelope-only
    re-emission cannot become a new Distillery event while genuinely different
    execution evidence remains distinct.
    """
    return {
        "schema": "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2",
        "source_class": str(row.get("source_class") or ""),
        "provider": str(row.get("provider") or ""),
        "model": str(row.get("model") or ""),
        "role": str(row.get("role") or ""),
        "worker_sha": row["worker_sha"],
        "source_repo_head": row["source_repo_head"],
        "evaluation_repo_head": row["evaluation_repo_head"],
        "target_blob_identities": row["target_blob_identities"],
        "execution_admission_sha256": digest_json(row.get("execution_admission")),
        "metric": str(row.get("metric") or ""),
        "requires_rebase_to_evaluation_head": bool(row.get("requires_rebase_to_evaluation_head", False)),
    }


def persisted_execution_replay_identity_v2(packet: dict, metadata: dict) -> dict | None:
    """Reconstruct v2 identity from an already-persisted v1 knowledge packet."""
    required_packet = (
        "worker_sha",
        "source_repo_head",
        "evaluation_repo_head",
        "target_blob_identities",
        "execution_admission_sha256",
        "metric",
        "requires_rebase_to_evaluation_head",
    )
    required_metadata = ("source_class", "provider", "model", "role")
    if any(key not in packet for key in required_packet):
        return None
    if any(key not in metadata for key in required_metadata):
        return None
    if not isinstance(packet.get("target_blob_identities"), dict):
        return None
    if not str(packet.get("execution_admission_sha256") or ""):
        return None
    return {
        "schema": "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2",
        "source_class": str(metadata.get("source_class") or ""),
        "provider": str(metadata.get("provider") or ""),
        "model": str(metadata.get("model") or ""),
        "role": str(metadata.get("role") or ""),
        "worker_sha": packet["worker_sha"],
        "source_repo_head": packet["source_repo_head"],
        "evaluation_repo_head": packet["evaluation_repo_head"],
        "target_blob_identities": packet["target_blob_identities"],
        "execution_admission_sha256": str(packet["execution_admission_sha256"]),
        "metric": str(packet.get("metric") or ""),
        "requires_rebase_to_evaluation_head": bool(packet.get("requires_rebase_to_evaluation_head", False)),
    }


def measured_evidence_identity(row: dict) -> dict:
    """Return immutable measured evidence for conflict detection.

    ``evaluated_at`` and ``delta_id`` are observation/evaluation-envelope metadata, not
    measured execution evidence. Candidate hypothesis and falsifier are not part of
    ``measured_packet`` and therefore cannot change this digest either.
    """
    packet = measured_packet(row)
    packet.pop("evaluated_at", None)
    packet.pop("delta_id", None)
    return {
        "schema": "CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v1",
        "packet": packet,
    }


def _backfill_replay_identity_v2(con: sqlite3.Connection) -> None:
    """Backfill v1 rows from their durable packet evidence without rewriting history."""
    rows = con.execute(
        "SELECT f.evaluation_sha256,k.packet_text,k.metadata_json "
        "FROM forge_execution_ingest f "
        "LEFT JOIN knowledge_packets k ON k.id=f.packet_id "
        "WHERE f.execution_replay_identity_v2_sha256 IS NULL "
        "AND f.execution_replay_identity_sha256 IS NOT NULL"
    ).fetchall()
    for evaluation_sha256, packet_text, metadata_json in rows:
        if packet_text is None or metadata_json is None:
            continue
        try:
            packet = json.loads(packet_text)
            metadata = json.loads(metadata_json)
        except Exception:
            continue
        identity = persisted_execution_replay_identity_v2(packet, metadata)
        if identity is None:
            continue
        con.execute(
            "UPDATE forge_execution_ingest SET execution_replay_identity_v2_sha256=? "
            "WHERE evaluation_sha256=? AND execution_replay_identity_v2_sha256 IS NULL",
            (digest_json(identity), evaluation_sha256),
        )


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS knowledge_packets(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          root_problem TEXT NOT NULL,
          packet_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          intrinsic_score REAL NOT NULL,
          grf_score REAL NOT NULL,
          project_fit REAL NOT NULL,
          novelty_score REAL NOT NULL,
          approx_tokens INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS counters(
          key TEXT PRIMARY KEY,
          value INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS forge_execution_ingest(
          evaluation_sha256 TEXT PRIMARY KEY,
          execution_replay_identity_sha256 TEXT,
          execution_replay_identity_v2_sha256 TEXT,
          measured_evidence_sha256 TEXT,
          packet_id TEXT NOT NULL UNIQUE,
          delta_id TEXT,
          worker_sha TEXT NOT NULL,
          source_repo_head TEXT NOT NULL,
          evaluation_repo_head TEXT NOT NULL,
          admitted_at TEXT NOT NULL,
          approx_tokens INTEGER NOT NULL
        );
        """
    )
    columns = {str(row[1]) for row in con.execute("PRAGMA table_info(forge_execution_ingest)")}
    if "execution_replay_identity_sha256" not in columns:
        con.execute("ALTER TABLE forge_execution_ingest ADD COLUMN execution_replay_identity_sha256 TEXT")
    if "execution_replay_identity_v2_sha256" not in columns:
        con.execute("ALTER TABLE forge_execution_ingest ADD COLUMN execution_replay_identity_v2_sha256 TEXT")
    if "measured_evidence_sha256" not in columns:
        con.execute("ALTER TABLE forge_execution_ingest ADD COLUMN measured_evidence_sha256 TEXT")
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS forge_execution_ingest_replay_identity_uq "
        "ON forge_execution_ingest(execution_replay_identity_sha256) "
        "WHERE execution_replay_identity_sha256 IS NOT NULL"
    )
    _backfill_replay_identity_v2(con)
    duplicate_v2 = con.execute(
        "SELECT execution_replay_identity_v2_sha256,COUNT(*) "
        "FROM forge_execution_ingest "
        "WHERE execution_replay_identity_v2_sha256 IS NOT NULL "
        "GROUP BY execution_replay_identity_v2_sha256 HAVING COUNT(*)>1 LIMIT 1"
    ).fetchone()
    if duplicate_v2:
        raise RuntimeError("REPLAY_IDENTITY_V2_MIGRATION_CONFLICT")
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS forge_execution_ingest_replay_identity_v2_uq "
        "ON forge_execution_ingest(execution_replay_identity_v2_sha256) "
        "WHERE execution_replay_identity_v2_sha256 IS NOT NULL"
    )


def bump(con: sqlite3.Connection, key: str, delta: int) -> None:
    con.execute(
        "INSERT INTO counters(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
        (key, int(delta)),
    )


def _unresolved_replay_collision(con: sqlite3.Connection, row: dict) -> bool:
    """Conservatively fence rows whose replay-v2 identity cannot be reconstructed.

    Such rows do not retain enough evidence to prove whether a new envelope represents
    a genuinely new execution. ``delta_id`` is deliberately ignored here because using
    it as an escape hatch would recreate the v1 bug.
    """
    return con.execute(
        "SELECT 1 FROM forge_execution_ingest "
        "WHERE execution_replay_identity_v2_sha256 IS NULL "
        "AND worker_sha=? AND source_repo_head=? AND evaluation_repo_head=? LIMIT 1",
        (
            row["worker_sha"],
            row["source_repo_head"],
            row["evaluation_repo_head"],
        ),
    ).fetchone() is not None


def admit_one(con: sqlite3.Connection, row: dict) -> tuple[bool, str, str | None]:
    ok, reason = admission_reason(row)
    if not ok:
        return False, reason, None

    eval_sha = digest_json(row)
    replay_v1_sha = digest_json(legacy_execution_replay_identity_v1(row))
    replay_v2_sha = digest_json(execution_replay_identity(row))
    measured_sha = digest_json(measured_evidence_identity(row))
    existing = con.execute(
        "SELECT evaluation_sha256, measured_evidence_sha256 "
        "FROM forge_execution_ingest "
        "WHERE evaluation_sha256=? OR execution_replay_identity_v2_sha256=? LIMIT 1",
        (eval_sha, replay_v2_sha),
    ).fetchone()
    if existing:
        existing_eval_sha = str(existing[0] or "")
        existing_measured_sha = str(existing[1] or "")
        if existing_eval_sha == eval_sha or not existing_measured_sha or existing_measured_sha == measured_sha:
            return False, "DUPLICATE", None
        return False, "REPLAY_IDENTITY_CONFLICT", None

    if _unresolved_replay_collision(con, row):
        return False, "LEGACY_REPLAY_IDENTITY_UNRESOLVED", None

    packet = measured_packet(row)
    text = canonical_json(packet)
    tok = approx_tokens(text)
    # Durable packet identity follows replay-v2 stable execution identity, not volatile
    # full-evaluation bytes or candidate/evaluation delta_id.
    packet_id = "kf-" + replay_v2_sha[:18]
    question_id = "forge-" + replay_v2_sha[:16]
    metadata = {
        "packet_class": "FORGE_EVIDENCE_QUALIFIED_EXECUTION",
        "forge_evaluation_sha256": eval_sha,
        "forge_execution_replay_identity_sha256": replay_v1_sha,
        "forge_execution_replay_identity_v2_sha256": replay_v2_sha,
        "forge_measured_evidence_sha256": measured_sha,
        "execution_admission_sha256": packet["execution_admission_sha256"],
        "evidence_qualification": reason,
        "source_class": row.get("source_class"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "role": row.get("role"),
        "proposal_hypothesis_candidate_only": row.get("proposal_hypothesis"),
        "proposal_falsifier_candidate_only": row.get("falsifier"),
        "score_semantics": {
            "intrinsic_score": "1.0 = evidence-qualified isolated measured execution passed deterministic admission",
            "grf_score": "0.0 = not measured by Forge; unknown rather than promoted",
            "project_fit": "1.0 = executable EntityOS/HCU delta evidence",
            "novelty_score": "0.0 = not measured by Forge; unknown rather than promoted",
        },
        "canonical_truth": False,
        "jspace_causal_credit": 0,
        "training_credit": 0,
    }
    con.execute(
        "INSERT INTO knowledge_packets(id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            packet_id,
            question_id,
            "Evidence-qualified executable delta evidence from Evidence Forge",
            text,
            canonical_json(metadata),
            1.0,
            0.0,
            1.0,
            0.0,
            tok,
            now_iso(),
        ),
    )
    con.execute(
        "INSERT INTO forge_execution_ingest("
        "evaluation_sha256,execution_replay_identity_sha256,execution_replay_identity_v2_sha256,measured_evidence_sha256,"
        "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            eval_sha,
            replay_v1_sha,
            replay_v2_sha,
            measured_sha,
            packet_id,
            str(row.get("delta_id") or ""),
            row["worker_sha"],
            row["source_repo_head"],
            row["evaluation_repo_head"],
            now_iso(),
            tok,
        ),
    )
    bump(con, "accepted_dataset_tokens", tok)
    bump(con, "accepted_packets", 1)
    bump(con, "forge_execution_packets", 1)
    bump(con, "forge_evidence_qualified_packets", 1)
    return True, reason, packet_id


def ingest(forge_eval_path: Path, distillery_db: Path, *, limit: int = 0) -> dict:
    summary = {
        "schema": "CLAY_FORGE_TO_DISTILLERY_INGEST_RESULT/v2",
        "acceptance_semantics": "EVIDENCE_QUALIFIED_ONLY",
        "replay_semantics": "STABLE_EXECUTION_IDENTITY_V2_EXCLUDES_DELTA_ID_WITH_MEASURED_CONFLICT_AND_LEGACY_UNKNOWN_REJECTION",
        "forge_eval_path": str(forge_eval_path),
        "distillery_db": str(distillery_db),
        "seen": 0,
        "admitted": 0,
        "duplicates": 0,
        "rejected": {},
        "packet_ids": [],
    }
    if not forge_eval_path.exists():
        summary["rejected"]["FORGE_EVAL_MISSING"] = 1
        return summary
    distillery_db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(distillery_db, timeout=30)
    try:
        ensure_schema(con)
        for line in forge_eval_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if limit and summary["seen"] >= limit:
                break
            if not line.strip():
                continue
            summary["seen"] += 1
            try:
                row = json.loads(line)
            except Exception:
                summary["rejected"]["INVALID_JSON"] = summary["rejected"].get("INVALID_JSON", 0) + 1
                continue
            admitted, reason, packet_id = admit_one(con, row)
            if admitted:
                summary["admitted"] += 1
                summary["packet_ids"].append(packet_id)
            elif reason == "DUPLICATE":
                summary["duplicates"] += 1
            else:
                summary["rejected"][reason] = summary["rejected"].get(reason, 0) + 1
        con.commit()
        row = con.execute("SELECT COALESCE(SUM(approx_tokens),0),COUNT(*) FROM knowledge_packets").fetchone()
        summary["knowledge_packet_tokens_total"] = int(row[0] or 0)
        summary["knowledge_packets_total"] = int(row[1] or 0)
        c = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
        summary["accepted_dataset_tokens_counter"] = int(c[0]) if c else 0
        f = con.execute("SELECT COUNT(*) FROM forge_execution_ingest").fetchone()
        summary["forge_execution_packets_total"] = int(f[0] or 0)
        q = con.execute("SELECT value FROM counters WHERE key='forge_evidence_qualified_packets'").fetchone()
        summary["forge_evidence_qualified_packets_counter"] = int(q[0]) if q else 0
    finally:
        con.close()
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-evaluations", type=Path, default=DEFAULT_FORGE_EVAL)
    ap.add_argument("--distillery-db", type=Path, default=DEFAULT_DISTILLERY_DB)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    result = ingest(args.forge_evaluations, args.distillery_db, limit=max(0, args.limit))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not result["rejected"].get("FORGE_EVAL_MISSING") else 2


if __name__ == "__main__":
    raise SystemExit(main())
