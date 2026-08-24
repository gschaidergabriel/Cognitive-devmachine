#!/usr/bin/env python3
"""Typed-ingress front end for the current FREE Evidence Forge.

All evaluator/executor/discovery semantics stay in the exact current legacy backend.
Current worker rows that advertise ``delta_ingress`` are consumed only through their
hash-bound typed sidecar. Missing/tampered/ambiguous typed sidecars fail closed and
never fall back to model-prose reparsing. Historical rows without typed metadata keep
the pre-existing compatibility path.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import run_free_evidence_forge_legacy as legacy
from free_swarm_delta_ingress import SCHEMA as INGRESS_SCHEMA, validate_delta

CANDIDATE_SCHEMA = "CLAY_ARCHITECTURE_DELTA_CANDIDATE/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _repo_head(value: Any) -> str:
    value = str(value or "").strip().lower()
    return value if legacy.COMMIT_RE.fullmatch(value) else ""


def _load_sidecars(active: Path, max_lines: int) -> dict[tuple[str, str], dict[str, Any] | None]:
    path = active / "architecture_deltas.jsonl"
    if not path.exists():
        return {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except OSError:
        return {}
    out: dict[tuple[str, str], dict[str, Any] | None] = {}
    for line in lines:
        try:
            row = json.loads(line)
        except Exception:
            continue
        if not isinstance(row, dict) or row.get("schema") != CANDIDATE_SCHEMA:
            continue
        if row.get("ingress_schema") != INGRESS_SCHEMA:
            continue
        worker_sha = str(row.get("worker_text_sha256") or "").strip().lower()
        proposal_sha = str(row.get("proposal_sha256") or "").strip().lower()
        proposal = row.get("proposal")
        if not SHA256_RE.fullmatch(worker_sha) or not SHA256_RE.fullmatch(proposal_sha):
            continue
        if not isinstance(proposal, dict):
            continue
        valid, _ = validate_delta(proposal)
        if not valid:
            continue
        raw = _canonical(proposal)
        if legacy.sha(raw) != proposal_sha:
            continue
        if bool(proposal.get("ready_for_forge")) != bool(row.get("ready_for_forge")):
            continue
        key = (worker_sha, proposal_sha)
        existing = out.get(key)
        if key not in out:
            out[key] = row
        elif existing is None or _canonical(existing) != _canonical(row):
            # Same causal key with different envelope is ambiguous; never pick one.
            out[key] = None
    return out


def _insert_candidate(con, worker: dict[str, Any], proposal: dict[str, Any], *, worker_sha: str, repo_head: str) -> bool:
    raw = _canonical(proposal)
    ch = legacy.sha(worker_sha + raw)
    ready = bool(proposal.get("ready_for_forge"))
    try:
        con.execute(
            "INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,repo_head,proposal_json,ready,state,ingested_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                ch,
                str(proposal.get("delta_id") or ch[:16]),
                str(worker.get("provider") or ""),
                str(worker.get("model") or ""),
                str(worker.get("role") or ""),
                worker_sha,
                repo_head,
                raw,
                int(ready),
                "NEW",
                legacy.now(),
            ),
        )
        return True
    except legacy.sqlite3.IntegrityError:
        if repo_head:
            con.execute(
                "UPDATE candidates SET repo_head=? WHERE candidate_hash=? AND (repo_head IS NULL OR repo_head='')",
                (repo_head, ch),
            )
        return False


def _typed_candidate(worker: dict[str, Any], sidecars: dict[tuple[str, str], dict[str, Any] | None]) -> tuple[dict[str, Any], str, str] | None:
    ingress = worker.get("delta_ingress")
    if not isinstance(ingress, dict):
        return None
    if ingress.get("schema") != INGRESS_SCHEMA or ingress.get("valid") is not True:
        return None
    proposal_sha = str(ingress.get("proposal_sha256") or "").strip().lower()
    text = str(worker.get("text") or "")
    worker_sha = str(worker.get("text_sha256") or "").strip().lower()
    if not SHA256_RE.fullmatch(worker_sha) or worker_sha != legacy.sha(text):
        return None
    if not SHA256_RE.fullmatch(proposal_sha):
        return None
    sidecar = sidecars.get((worker_sha, proposal_sha))
    if not isinstance(sidecar, dict):
        return None
    proposal = sidecar.get("proposal")
    if not isinstance(proposal, dict):
        return None
    if bool(ingress.get("ready_for_forge")) != bool(sidecar.get("ready_for_forge")):
        return None
    for field in ("provider", "model", "role"):
        if str(worker.get(field) or "") != str(sidecar.get(field) or ""):
            return None
    worker_repo = _repo_head(worker.get("repo_head_at_prompt") or worker.get("repo_head"))
    sidecar_repo = _repo_head(sidecar.get("repo_head_at_prompt"))
    if worker_repo and sidecar_repo and worker_repo != sidecar_repo:
        return None
    repo_head = worker_repo or sidecar_repo
    return proposal, worker_sha, repo_head


def ingest_worker_candidates(con, max_lines_per_file: int = 1200) -> int:
    added = 0
    roots = sorted(
        legacy.ARTIFACT_ROOT.glob("active-*/workers.jsonl"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )[:8]
    for path in roots:
        sidecars = _load_sidecars(path.parent, max_lines_per_file)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines_per_file:]
        except OSError:
            continue
        for line in lines:
            try:
                worker = json.loads(line)
            except Exception:
                continue
            if not isinstance(worker, dict):
                continue
            status = worker.get("http_status")
            if not (isinstance(status, int) and 200 <= status < 300):
                continue

            if "delta_ingress" in worker:
                typed = _typed_candidate(worker, sidecars)
                if typed is None:
                    legacy.bump(con, "typed_candidates_rejected")
                    continue
                proposal, worker_sha, repo_head = typed
                if _insert_candidate(con, worker, proposal, worker_sha=worker_sha, repo_head=repo_head):
                    added += 1
                    legacy.bump(con, "typed_candidates_ingested")
                continue

            # Historical compatibility only: rows that predate typed metadata retain
            # the exact old prose extraction path. A typed row can never reach here.
            text = str(worker.get("text") or "")
            proposal = legacy.balanced_json_after(text, "ARCHITECTURE_DELTA_JSON=")
            if not isinstance(proposal, dict):
                continue
            worker_sha = str(worker.get("text_sha256") or legacy.sha(text)).strip().lower()
            repo_head = _repo_head(worker.get("repo_head_at_prompt"))
            if _insert_candidate(con, worker, proposal, worker_sha=worker_sha, repo_head=repo_head):
                added += 1
                legacy.bump(con, "legacy_candidates_ingested")

    con.commit()
    legacy.bump(con, "candidates_ingested", added)
    con.commit()
    return added


# The current backend remains the single evaluator/executor authority. Replace only
# its ingestion callback so every existing call site, including main(), sees the
# typed boundary without duplicating the rest of Forge.
legacy.ingest_worker_candidates = ingest_worker_candidates


def __getattr__(name: str):
    return getattr(legacy, name)


def main() -> int:
    return int(legacy.main())


if __name__ == "__main__":
    raise SystemExit(main())
