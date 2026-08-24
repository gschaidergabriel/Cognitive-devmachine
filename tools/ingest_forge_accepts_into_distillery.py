#!/usr/bin/env python3
"""Admit only evidence-qualified Forge ACCEPTED evaluations into Distillery.

Historical/nominal Forge acceptance remains append-only but is not sufficient for
current dataset credit. Admission delegates the acceptance boundary to
``forge_evidence_credit_871.evidence_reason`` so Distillery requires the same exact
source identities plus CLAY_FORGE_EXECUTION_ADMISSION/v1, isolated execution backend,
command admission and secret fences as current Forge evidence credit.

Only measured fields enter packet_text. Model-authored hypothesis/falsifier, volatile
observation time, and ``delta_id`` remain envelope/metadata only. Distillery idempotence
is bound to a replay-stable execution evidence identity rather than the byte digest of
the full evaluation envelope, so changed envelope narration, timestamp, or identifier
cannot mint a second dataset packet or alter training-bearing packet bytes for the same
measured evidence. If the same execution identity reappears with conflicting measured
evidence, admission fails closed instead of treating the mutation as a new observation.

Legacy ingest rows predate the replay-identity columns. They cannot be safely backfilled
from the reduced legacy table, so a new evaluation colliding on the available legacy
execution coordinates fails closed until the historical row is explicitly reconciled.

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
    """Return replay-stable dataset text containing measured evidence only.

    ``evaluated_at`` and ``delta_id`` are intentionally excluded from the training
    preimage. Two fresh Distillery rebuilds that first encounter different observation
    envelopes for the same measured execution must produce identical packet bytes and
    token counts.
    """
    execution_admission = row.get("execution_admission")
    return {
        "schema": "CLAY_DISTILLERY_FORGE_EXECUTION_PACKET/v2",
        "evidence_class": "FORGE_EVIDENCE_QUALIFIED_EXECUTION",
        "evidence_qualification": "EVIDENCE_QUALIFIED_ACCEPT",
        "canonical_truth": False,
        "training_scope": "EXECUTION_EVIDENCE_ONLY_NOT_JSPACE_CAUSAL_CREDIT",
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
    }


def execution_replay_identity(row: dict) -> dict:
    """Bind one replay-stable measured Forge execution/evaluation family.

    Volatile observation time, model-authored narration and ``delta_id`` are
    intentionally excluded. ``delta_id`` names a candidate/evaluation envelope; it is
    not proof of a new measured execution. The identity keeps source/provenance,
    target bytes, admitted execution surface and metric definition, so envelope-only
    replay cannot become a new Distillery event while genuinely different execution
    evidence remains distinct.
    """
    return {
        "schema": "CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v1",
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


def measured_evidence_identity(row: dict) -> dict:
    """Return immutable measured evidence for conflict detection.

    Observation time, ``delta_id``, and candidate narration are absent from
    ``measured_packet`` itself, so conflict identity and training-bearing packet share
    one stable measured-evidence preimage.
    """
    return {
        "schema": "CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v1",
        "packet": measured_packet(row),
    }


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
    if "measured_evidence_sha256" not in columns:
        con.execute("ALTER TABLE forge_execution_ingest ADD COLUMN measured_evidence_sha256 TEXT")
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS forge_execution_ingest_replay_identity_uq "
        "ON forge_execution_ingest(execution_replay_identity_sha256) "
        "WHERE execution_replay_identity_sha256 IS NOT NULL"
    )


def bump(con: sqlite3.Connection, key: str, delta: int) -> None:
    con.execute(
        "INSERT INTO counters(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
        (key, int(delta)),
    )


def _legacy_replay_collision(con: sqlite3.Connection, row: dict) -> bool:
    """Conservatively fence a possible replay against a pre-v1 ingest row.

    Legacy rows retain only coarse execution coordinates. They do not retain enough
    evidence to derive the new replay/measured digests without guessing. ``delta_id``
    is deliberately not used as a legacy discriminator because it is envelope identity,
    not proof of a distinct measured execution. Ambiguous legacy overlap is therefore
    UNKNOWN rather than admissible.
    """
    return con.execute(
        "SELECT 1 FROM forge_execution_ingest "
        "WHERE execution_replay_identity_sha256 IS NULL "
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
    replay_sha = digest_json(execution_replay_identity(row))
    measured_sha = digest_json(measured_evidence_identity(row))
    existing = con.execute(
        "SELECT evaluation_sha256, measured_evidence_sha256 "
        "FROM forge_execution_ingest "
        "WHERE evaluation_sha256=? OR execution_replay_identity_sha256=? LIMIT 1",
        (eval_sha, replay_sha),
    ).fetchone()
    if existing:
        existing_eval_sha = str(existing[0] or "")
        existing_measured_sha = str(existing[1] or "")
        if existing_eval_sha == eval_sha or not existing_measured_sha or existing_measured_sha == measured_sha:
            return False, "DUPLICATE", None
        return False, "REPLAY_IDENTITY_CONFLICT", None

    if _legacy_replay_collision(con, row):
        return False, "LEGACY_REPLAY_IDENTITY_UNRESOLVED", None

    packet = measured_packet(row)
    text = canonical_json(packet)
    tok = approx_tokens(text)
    # Durable packet identity follows the stable execution identity, not volatile
    # full-evaluation bytes. Full envelope identity is retained as metadata only.
    packet_id = "kf-" + replay_sha[:18]
    question_id = "forge-" + replay_sha[:16]
    metadata = {
        "packet_class": "FORGE_EVIDENCE_QUALIFIED_EXECUTION",
        "forge_evaluation_sha256": eval_sha,
        "forge_execution_replay_identity_sha256": replay_sha,
        "forge_measured_evidence_sha256": measured_sha,
        "execution_admission_sha256": packet["execution_admission_sha256"],
        "evidence_qualification": reason,
        "source_class": row.get("source_class"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "role": row.get("role"),
        "forge_delta_id_observation_only": row.get("delta_id"),
        "forge_evaluated_at_observation_only": row.get("evaluated_at"),
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
        "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
        "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
        ") VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            eval_sha,
            replay_sha,
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
        "replay_semantics": "STABLE_EXECUTION_IDENTITY_WITH_MEASURED_CONFLICT_AND_LEGACY_UNKNOWN_REJECTION",
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
