#!/usr/bin/env python3
"""Install a typed worker->Forge ingestion boundary on the current Forge module.

New worker rows carrying ``delta_ingress`` must resolve to exactly one valid,
hash-bound sidecar. Missing/tampered/ambiguous typed evidence fails closed and can
never fall back to model-prose parsing. Historical rows without typed metadata keep
the prior compatibility path. The supplied Forge module retains all evaluator,
executor, isolation, state, and evidence authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from free_swarm_delta_ingress import SCHEMA as INGRESS_SCHEMA, validate_delta
from free_swarm_typed_delta_bridge import CANDIDATE_SCHEMA

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_INSTALLED = False


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def install(base) -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    def repo_head(value: Any) -> str:
        value = str(value or "").strip().lower()
        return value if base.COMMIT_RE.fullmatch(value) else ""

    def load_sidecars(active: Path, max_lines: int) -> dict[tuple[str, str], dict[str, Any] | None]:
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
            if base.sha(raw) != proposal_sha:
                continue
            if bool(proposal.get("ready_for_forge")) != bool(row.get("ready_for_forge")):
                continue
            key = (worker_sha, proposal_sha)
            existing = out.get(key)
            if key not in out:
                out[key] = row
            elif existing is None or _canonical(existing) != _canonical(row):
                out[key] = None
        return out

    def insert_candidate(con, worker: dict[str, Any], proposal: dict[str, Any], *, worker_sha: str, source_head: str) -> bool:
        raw = _canonical(proposal)
        candidate_hash = base.sha(worker_sha + raw)
        try:
            con.execute(
                "INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,repo_head,proposal_json,ready,state,ingested_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    candidate_hash,
                    str(proposal.get("delta_id") or candidate_hash[:16]),
                    str(worker.get("provider") or ""),
                    str(worker.get("model") or ""),
                    str(worker.get("role") or ""),
                    worker_sha,
                    source_head,
                    raw,
                    int(bool(proposal.get("ready_for_forge"))),
                    "NEW",
                    base.now(),
                ),
            )
            return True
        except base.sqlite3.IntegrityError:
            if source_head:
                con.execute(
                    "UPDATE candidates SET repo_head=? WHERE candidate_hash=? AND (repo_head IS NULL OR repo_head='')",
                    (source_head, candidate_hash),
                )
            return False

    def typed_candidate(worker: dict[str, Any], sidecars: dict[tuple[str, str], dict[str, Any] | None]):
        ingress = worker.get("delta_ingress")
        if not isinstance(ingress, dict):
            return None
        if ingress.get("schema") != INGRESS_SCHEMA or ingress.get("valid") is not True:
            return None
        proposal_sha = str(ingress.get("proposal_sha256") or "").strip().lower()
        text = str(worker.get("text") or "")
        worker_sha = str(worker.get("text_sha256") or "").strip().lower()
        if not SHA256_RE.fullmatch(worker_sha) or worker_sha != base.sha(text):
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
        worker_repo = repo_head(worker.get("repo_head_at_prompt") or worker.get("repo_head"))
        sidecar_repo = repo_head(sidecar.get("repo_head_at_prompt"))
        if worker_repo and sidecar_repo and worker_repo != sidecar_repo:
            return None
        return proposal, worker_sha, worker_repo or sidecar_repo

    def ingest_worker_candidates(con, max_lines_per_file: int = 1200) -> int:
        added = 0
        paths = sorted(
            base.ARTIFACT_ROOT.glob("active-*/workers.jsonl"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )[:8]
        for path in paths:
            sidecars = load_sidecars(path.parent, max_lines_per_file)
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
                    typed = typed_candidate(worker, sidecars)
                    if typed is None:
                        base.bump(con, "typed_candidates_rejected")
                        continue
                    proposal, worker_sha, source_head = typed
                    if insert_candidate(con, worker, proposal, worker_sha=worker_sha, source_head=source_head):
                        added += 1
                        base.bump(con, "typed_candidates_ingested")
                    continue

                text = str(worker.get("text") or "")
                proposal = base.balanced_json_after(text, "ARCHITECTURE_DELTA_JSON=")
                if not isinstance(proposal, dict):
                    continue
                worker_sha = str(worker.get("text_sha256") or base.sha(text)).strip().lower()
                source_head = repo_head(worker.get("repo_head_at_prompt"))
                if insert_candidate(con, worker, proposal, worker_sha=worker_sha, source_head=source_head):
                    added += 1
                    base.bump(con, "legacy_candidates_ingested")

        con.commit()
        base.bump(con, "candidates_ingested", added)
        con.commit()
        return added

    base.ingest_worker_candidates = ingest_worker_candidates
    _INSTALLED = True
