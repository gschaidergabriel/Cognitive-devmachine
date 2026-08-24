#!/usr/bin/env python3
"""Typed-ingress front end for the legacy Clay FREE Evidence Forge.

Current runs are consumed from deterministic ``architecture_deltas.jsonl`` sidecars.
Rows that advertise typed ingress are never re-parsed from model prose if the sidecar is
missing or invalid. Historical worker logs without typed-ingress metadata retain the old
compatibility path. Candidate output remains noncanonical evidence.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from typing import Any

import run_free_evidence_forge_legacy as legacy
from free_swarm_delta_ingress import CANDIDATE_SCHEMA, canonical_json, validate_delta


def _insert_candidate(
    con: sqlite3.Connection,
    *,
    worker_sha: str,
    obj: dict[str, Any],
    provider: str,
    model: str,
    role: str,
) -> bool:
    raw = canonical_json(obj)
    ch = legacy.sha(worker_sha + raw)
    try:
        con.execute(
            "INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,"
            "proposal_json,ready,state,ingested_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                ch,
                str(obj.get("delta_id") or ch[:16]),
                provider,
                model,
                role,
                worker_sha,
                raw,
                int(bool(obj.get("ready_for_forge"))),
                "NEW",
                legacy.now(),
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def _typed_sidecars(con: sqlite3.Connection, max_lines_per_file: int) -> tuple[int, set[tuple[str, str]]]:
    added = 0
    seen: set[tuple[str, str]] = set()
    rejected = 0
    paths = sorted(
        legacy.ARTIFACT_ROOT.glob("active-*/architecture_deltas.jsonl"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )[:8]
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines_per_file:]
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except Exception:
                rejected += 1
                continue
            if not isinstance(row, dict) or row.get("schema") != CANDIDATE_SCHEMA:
                rejected += 1
                continue
            obj = row.get("proposal")
            worker_sha = str(row.get("worker_text_sha256") or "")
            claimed_sha = str(row.get("proposal_sha256") or "")
            if not isinstance(obj, dict) or len(worker_sha) != 64 or len(claimed_sha) != 64:
                rejected += 1
                continue
            valid, _ = validate_delta(obj)
            raw = canonical_json(obj)
            actual_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            key = (worker_sha, claimed_sha)
            seen.add(key)
            if (
                not valid
                or actual_sha != claimed_sha
                or bool(row.get("ready_for_forge")) != bool(obj.get("ready_for_forge"))
            ):
                rejected += 1
                continue
            if _insert_candidate(
                con,
                worker_sha=worker_sha,
                obj=obj,
                provider=str(row.get("provider") or ""),
                model=str(row.get("model") or ""),
                role=str(row.get("role") or ""),
            ):
                added += 1
    legacy.bump(con, "typed_candidates_rejected", rejected)
    legacy.bump(con, "typed_candidates_ingested", added)
    return added, seen


def _legacy_rows(
    con: sqlite3.Connection,
    max_lines_per_file: int,
    typed_seen: set[tuple[str, str]],
) -> tuple[int, int]:
    added = 0
    typed_orphans = 0
    paths = sorted(
        legacy.ARTIFACT_ROOT.glob("active-*/workers.jsonl"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )[:8]
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines_per_file:]
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except Exception:
                continue
            status = row.get("http_status")
            if not (isinstance(status, int) and 200 <= status < 300):
                continue

            ingress = row.get("delta_ingress")
            if isinstance(ingress, dict):
                worker_sha = str(row.get("text_sha256") or legacy.sha(str(row.get("text") or "")))
                proposal_sha = str(ingress.get("proposal_sha256") or "")
                if ingress.get("valid") and (worker_sha, proposal_sha) not in typed_seen:
                    typed_orphans += 1
                # Fail closed: current typed rows are never reinterpreted from prose.
                continue

            # Compatibility only for historical rows created before typed ingress.
            text = str(row.get("text") or "")
            obj = legacy.balanced_json_after(text, "ARCHITECTURE_DELTA_JSON=")
            if not isinstance(obj, dict):
                continue
            worker_sha = str(row.get("text_sha256") or legacy.sha(text))
            if _insert_candidate(
                con,
                worker_sha=worker_sha,
                obj=obj,
                provider=str(row.get("provider") or ""),
                model=str(row.get("model") or ""),
                role=str(row.get("role") or ""),
            ):
                added += 1
    legacy.bump(con, "legacy_candidates_ingested", added)
    legacy.bump(con, "typed_sidecar_orphans", typed_orphans)
    return added, typed_orphans


def ingest_worker_candidates(con: sqlite3.Connection, max_lines_per_file: int = 1200) -> int:
    typed_added, seen = _typed_sidecars(con, max_lines_per_file)
    legacy_added, _ = _legacy_rows(con, max_lines_per_file, seen)
    total = typed_added + legacy_added
    con.commit()
    legacy.bump(con, "candidates_ingested", total)
    con.commit()
    return total


# Keep the original Forge implementation and all of its evaluation/effect boundaries,
# replacing only candidate ingress.
legacy.ingest_worker_candidates = ingest_worker_candidates


if __name__ == "__main__":
    raise SystemExit(asyncio.run(legacy.main(legacy.parse_args())))
