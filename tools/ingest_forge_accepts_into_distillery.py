#!/usr/bin/env python3
"""Deterministically admit measured Forge ACCEPTED evaluations into Distillery.

This bridge closes the executable-delta -> Forge -> Distillery conversion edge without
promoting model-authored hypotheses to fact. Only measured fields from an exact-source
Forge evaluation are admitted into packet_text. Proposal text remains metadata-only.

The destination remains the existing Distillery SQLite database; this module does not
create a second truth/effect authority and performs no network or external effect.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from forge_evidence_credit_871 import evidence_reason as evidence_credit_reason  # noqa: E402

ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
DEFAULT_FORGE_EVAL = Path(os.getenv("CLAY_FORGE_EVAL_PATH", str(ARTIFACT_ROOT / "forge/architecture_delta_evaluations.jsonl")))
DEFAULT_DISTILLERY_DB = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DB", str(ARTIFACT_ROOT / "distillery/distillery.sqlite3")))
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40_64 = re.compile(r"^[0-9a-f]{40,64}$")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4)) if text else 0


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _int_at_least(obj: dict, key: str, minimum: int) -> bool:
    value = obj.get(key)
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _int_eq_zero(obj: dict, key: str) -> bool:
    value = obj.get(key)
    return isinstance(value, int) and not isinstance(value, bool) and value == 0


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) > 0.0


def _safe_target_blobs(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    for path, blob in value.items():
        if not isinstance(path, str) or not path.strip():
            return False
        p = Path(path)
        if p.is_absolute() or ".." in p.parts or str(p).startswith(".git"):
            return False
        if blob != "NEW_OR_MISSING_AT_SOURCE" and not (isinstance(blob, str) and HEX40_64.fullmatch(blob)):
            return False
    return True


def admission_reason(row: Any) -> tuple[bool, str]:
    if not isinstance(row, dict):
        return False, "NOT_OBJECT"
    if row.get("schema") != "CLAY_FORGE_DELTA_EVALUATION/v1":
        return False, "WRONG_SCHEMA"
    if row.get("status") != "accepted":
        return False, "NOT_ACCEPTED"
    if row.get("source_scope") != "EXACT_WORKER_PROMPT_HEAD":
        return False, "SOURCE_SCOPE_NOT_EXACT"
    source_head = row.get("source_repo_head")
    eval_head = row.get("evaluation_repo_head")
    worker_sha = row.get("worker_sha")
    if not (isinstance(source_head, str) and HEX40.fullmatch(source_head)):
        return False, "SOURCE_HEAD_INVALID"
    if not (isinstance(eval_head, str) and HEX40.fullmatch(eval_head)):
        return False, "EVALUATION_HEAD_INVALID"
    if not (isinstance(worker_sha, str) and HEX64.fullmatch(worker_sha)):
        return False, "WORKER_SHA_INVALID"
    if not _safe_target_blobs(row.get("target_blob_identities")):
        return False, "TARGET_BLOBS_INVALID"
    if not _int_at_least(row, "reproducible_runs", 2):
        return False, "REPRODUCIBILITY_TOO_LOW"
    for key in ("tests_failed", "negative_tests_failed", "static_checks_failed"):
        if not _int_eq_zero(row, key):
            return False, key.upper() + "_NONZERO_OR_INVALID"
    if row.get("benchmark_non_regression") is not True:
        return False, "BENCHMARK_REGRESSION_OR_UNKNOWN"
    if not _positive_number(row.get("relative_improvement_pct")):
        return False, "NO_POSITIVE_IMPROVEMENT"
    if not _int_at_least(row, "tests_passed", 1):
        return False, "NO_PASSING_TESTS"

    # Supervisor 8.71 now distinguishes historical/nominal ACCEPTED rows from
    # evidence-qualified acceptance. Distillery must never be a weaker promotion
    # boundary than the current Forge evidence-credit audit. Preserve the detailed
    # bridge diagnostics above, then require the centralized current qualification
    # immediately before packet admission.
    qualified, reason = evidence_credit_reason(row)
    if not qualified:
        return False, "EVIDENCE_" + reason
    return True, "ACCEPTED_EXACT_EXECUTION_EVIDENCE"


def measured_packet(row: dict) -> dict:
    """Return training text fields containing only measured Forge evidence.

    proposal_hypothesis/falsifier are deliberately excluded. They remain candidate
    narration and cannot be upgraded by being adjacent to an accepted evaluation.
    """
    return {
        "schema": "CLAY_DISTILLERY_FORGE_EXECUTION_PACKET/v1",
        "evidence_class": "FORGE_MEASURED_EXECUTION",
        "canonical_truth": False,
        "training_scope": "EXECUTION_EVIDENCE_ONLY_NOT_JSPACE_CAUSAL_CREDIT",
        "delta_id": str(row.get("delta_id") or ""),
        "worker_sha": row["worker_sha"],
        "source_repo_head": row["source_repo_head"],
        "evaluation_repo_head": row["evaluation_repo_head"],
        "target_blob_identities": row["target_blob_identities"],
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


def bump(con: sqlite3.Connection, key: str, delta: int) -> None:
    con.execute(
        "INSERT INTO counters(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
        (key, int(delta)),
    )


def admit_one(con: sqlite3.Connection, row: dict) -> tuple[bool, str, str | None]:
    ok, reason = admission_reason(row)
    if not ok:
        return False, reason, None
    eval_sha = digest_json(row)
    if con.execute("SELECT 1 FROM forge_execution_ingest WHERE evaluation_sha256=?", (eval_sha,)).fetchone():
        return False, "DUPLICATE", None

    packet = measured_packet(row)
    text = canonical_json(packet)
    tok = approx_tokens(text)
    packet_id = "kf-" + eval_sha[:18]
    question_id = "forge-" + eval_sha[:16]
    metadata = {
        "packet_class": "FORGE_EXECUTION_EVIDENCE",
        "forge_evaluation_sha256": eval_sha,
        "source_class": row.get("source_class"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "role": row.get("role"),
        "proposal_hypothesis_candidate_only": row.get("proposal_hypothesis"),
        "proposal_falsifier_candidate_only": row.get("falsifier"),
        "score_semantics": {
            "intrinsic_score": "1.0 = exact accepted measured execution packet passed deterministic admission",
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
            "Measured executable delta evidence from Evidence Forge",
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
        "INSERT INTO forge_execution_ingest(evaluation_sha256,packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            eval_sha,
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
    return True, reason, packet_id


def ingest(forge_eval_path: Path, distillery_db: Path, *, limit: int = 0) -> dict:
    summary = {
        "schema": "CLAY_FORGE_TO_DISTILLERY_INGEST_RESULT/v1",
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
