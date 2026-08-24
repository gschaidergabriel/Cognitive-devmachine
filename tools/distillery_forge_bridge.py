#!/usr/bin/env python3
"""Deterministic Forge -> Distillery evidence admission bridge.

Only exact-source Forge evaluations that already passed the Forge acceptance gate are
admitted. The resulting Distillery packet remains noncanonical component evidence:
``fact_credit`` is always zero and no product/model/training credit is implied.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Callable

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
FORGE_EVAL_SCHEMA = "CLAY_FORGE_DELTA_EVALUATION/v1"
DISTILLERY_EVIDENCE_SCHEMA = "CLAY_DISTILLERY_FORGE_EVIDENCE/v1"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS forge_distillery_ingest(
          evaluation_sha256 TEXT PRIMARY KEY,
          delta_id TEXT NOT NULL,
          source_repo_head TEXT NOT NULL,
          knowledge_packet_id TEXT NOT NULL,
          approx_tokens INTEGER NOT NULL,
          ingested_at TEXT NOT NULL
        )
        """
    )
    con.commit()


def _int(row: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(row.get(key, default) or 0)
    except Exception:
        return default


def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or 0.0)
    except Exception:
        return default


def accepted_evaluation_is_admissible(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("schema") != FORGE_EVAL_SCHEMA:
        return False, "WRONG_SCHEMA"
    if str(row.get("status") or "").lower() != "accepted":
        return False, "NOT_ACCEPTED"
    source_head = str(row.get("source_repo_head") or "").strip().lower()
    eval_head = str(row.get("evaluation_repo_head") or "").strip().lower()
    if not COMMIT_RE.fullmatch(source_head):
        return False, "SOURCE_IDENTITY_UNBOUND"
    if not COMMIT_RE.fullmatch(eval_head):
        return False, "EVALUATION_IDENTITY_UNBOUND"
    if _int(row, "reproducible_runs") < 2:
        return False, "INSUFFICIENT_REPRODUCIBILITY"
    if _int(row, "tests_failed") != 0:
        return False, "TEST_FAILURE_PRESENT"
    if _int(row, "negative_tests_failed") != 0:
        return False, "NEGATIVE_TEST_FAILURE_PRESENT"
    if _int(row, "static_checks_failed") != 0:
        return False, "STATIC_CHECK_FAILURE_PRESENT"
    if row.get("benchmark_non_regression") is not True:
        return False, "BENCHMARK_NON_REGRESSION_UNPROVEN"
    if _float(row, "relative_improvement_pct") <= 0.0:
        return False, "NO_POSITIVE_DELTA"
    blobs = row.get("target_blob_identities")
    if not isinstance(blobs, dict) or not blobs:
        return False, "TARGET_BLOB_IDENTITIES_MISSING"
    for path, blob in blobs.items():
        if not isinstance(path, str) or not path.strip():
            return False, "TARGET_PATH_INVALID"
        if blob == "NEW_OR_MISSING_AT_SOURCE":
            continue
        if not isinstance(blob, str) or not re.fullmatch(r"[0-9a-f]{40,64}", blob):
            return False, "TARGET_BLOB_IDENTITY_INVALID"
    if not str(row.get("delta_id") or "").strip():
        return False, "DELTA_ID_MISSING"
    return True, "ADMISSIBLE"


def _packet_from_eval(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "epistemic_class": "EXECUTABLE_DELTA_COMPONENT_EVIDENCE",
        "fact_credit": 0,
        "delta_id": str(row.get("delta_id") or ""),
        "source_repo_head": str(row.get("source_repo_head") or ""),
        "evaluation_repo_head": str(row.get("evaluation_repo_head") or ""),
        "target_blob_identities": row.get("target_blob_identities") or {},
        "metric": row.get("metric"),
        "relative_improvement_pct": _float(row, "relative_improvement_pct"),
        "reproducible_runs": _int(row, "reproducible_runs"),
        "tests_passed": _int(row, "tests_passed"),
        "tests_failed": _int(row, "tests_failed"),
        "negative_tests_passed": _int(row, "negative_tests_passed"),
        "negative_tests_failed": _int(row, "negative_tests_failed"),
        "static_checks_passed": _int(row, "static_checks_passed"),
        "static_checks_failed": _int(row, "static_checks_failed"),
        "benchmark_non_regression": bool(row.get("benchmark_non_regression")),
        "requires_rebase_to_evaluation_head": bool(row.get("requires_rebase_to_evaluation_head")),
        "scope": "FORGE_DISPOSABLE_CLONE_COMPONENT_ONLY",
    }


def ingest_forge_acceptances(
    con: sqlite3.Connection,
    eval_path: Path,
    *,
    now_iso: Callable[[], str],
    approx_tokens: Callable[[str], int],
    bump: Callable[[sqlite3.Connection, str, int], None],
    emit: Callable[..., None] | None = None,
) -> dict[str, int]:
    """Admit new exact-source Forge accepts into Distillery exactly once.

    This is a local deterministic conversion path. It performs no provider/network
    calls and never promotes the evidence to canonical fact/product/model credit.
    """
    ensure_schema(con)
    result = {"admitted_packets": 0, "admitted_tokens": 0, "skipped_invalid": 0}
    if not eval_path.exists():
        return result
    try:
        lines = eval_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return result

    for line in lines:
        try:
            row = json.loads(line)
        except Exception:
            result["skipped_invalid"] += 1
            continue
        if not isinstance(row, dict):
            result["skipped_invalid"] += 1
            continue
        if str(row.get("status") or "").lower() != "accepted":
            continue
        ok, reason = accepted_evaluation_is_admissible(row)
        if not ok:
            result["skipped_invalid"] += 1
            if emit is not None:
                emit("forge_distillery_skip", delta_id=str(row.get("delta_id") or ""), reason=reason)
            continue

        evaluation_sha = _digest(row)
        if con.execute(
            "SELECT 1 FROM forge_distillery_ingest WHERE evaluation_sha256=?",
            (evaluation_sha,),
        ).fetchone():
            continue

        packet = _packet_from_eval(row)
        packet_text = _canonical(packet)
        tokens = int(approx_tokens(packet_text))
        delta_id = str(row.get("delta_id") or "")[:240]
        source_head = str(row.get("source_repo_head") or "").lower()
        qid = "q-forge-" + evaluation_sha[:16]
        kid = "k-forge-" + evaluation_sha[:18]
        ts = now_iso()
        question = f"Executable Forge evidence for delta {delta_id}"

        con.execute(
            "INSERT OR IGNORE INTO questions(id,parent_id,root_problem,question,depth,priority,status,attempts,created_at,last_touched,source_worker_sha) VALUES(?,?,?,?,?,?,?,0,?,?,?)",
            (
                qid,
                None,
                question,
                question,
                0,
                0.0,
                "EVIDENCE_ADMITTED",
                ts,
                ts,
                str(row.get("worker_sha") or "")[:128] or None,
            ),
        )
        metadata = {
            "schema": DISTILLERY_EVIDENCE_SCHEMA,
            "epistemic_class": "EXECUTABLE_DELTA_COMPONENT_EVIDENCE",
            "fact_credit": 0,
            "canonical_truth": False,
            "whole_product_credit": 0,
            "model_runtime_credit": 0,
            "training_credit": 0,
            "source_class": "evidence_forge",
            "forge_evaluation_sha256": evaluation_sha,
            "source_repo_head": source_head,
            "evaluation_repo_head": str(row.get("evaluation_repo_head") or "").lower(),
            "requires_rebase_to_evaluation_head": bool(row.get("requires_rebase_to_evaluation_head")),
            "admission_rule": "EXACT_SOURCE_FORGE_ACCEPTED_COMPONENT_EVIDENCE_ONLY",
        }
        con.execute(
            "INSERT INTO knowledge_packets(id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (kid, qid, question, packet_text, _canonical(metadata), 0.0, 0.0, 0.0, 0.0, tokens, ts),
        )
        con.execute(
            "INSERT INTO forge_distillery_ingest(evaluation_sha256,delta_id,source_repo_head,knowledge_packet_id,approx_tokens,ingested_at) VALUES(?,?,?,?,?,?)",
            (evaluation_sha, delta_id, source_head, kid, tokens, ts),
        )
        bump(con, "accepted_dataset_tokens", tokens)
        bump(con, "accepted_packets", 1)
        bump(con, "forge_evidence_tokens", tokens)
        bump(con, "forge_evidence_packets", 1)
        con.commit()
        result["admitted_packets"] += 1
        result["admitted_tokens"] += tokens
        if emit is not None:
            emit(
                "forge_evidence_admitted",
                delta_id=delta_id,
                knowledge_packet=kid,
                source_repo_head=source_head,
                approx_tokens=tokens,
                fact_credit=0,
            )
    return result
