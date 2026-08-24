#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for the FREE Evidence Forge.

Installs deterministic model-command execution admission before the base Forge can
evaluate worker-authored candidates. Candidate output remains noncanonical. No
model-authored command is executed without exact worker-source identity, an
allowlisted argv form, a secret-free child environment, and a functional isolated
bubblewrap backend.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import forge_execution_admission_871 as admission
import run_free_evidence_forge as base

_ORIGINAL_VALIDATE = base.validate_candidate
base.safe_command = admission.safe_command
base.run_cmd = admission.run_cmd


def validate_candidate(con: Any, row: Any) -> dict[str, Any]:
    try:
        proposal = json.loads(row["proposal_json"])
    except Exception:
        proposal = None
    if not isinstance(proposal, dict):
        return {
            "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
            "delta_id": row["delta_id"],
            "status": "execution_not_admitted",
            "reason": "PROPOSAL_JSON_INVALID",
            "evaluated_at": base.now(),
        }

    manifest = admission.candidate_execution_manifest(row, proposal, Path(base.ROOT))
    source_head = str(manifest.get("worker_source_head") or "")
    source_tree = str(manifest.get("worker_source_tree") or "")
    source_admitted = bool(
        manifest.get("source_identity_bound")
        and base.COMMIT_RE.fullmatch(source_head)
        and source_tree
    )
    manifest["source_identity_admitted"] = source_admitted
    manifest["source_scope"] = "EXACT_WORKER_PROMPT_HEAD"

    record = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": row["delta_id"],
        "source_class": "free_swarm",
        "provider": row["provider"],
        "model": row["model"],
        "role": row["role"],
        "worker_sha": row["worker_sha"],
        "source_repo_head": source_head or None,
        "source_repo_tree": source_tree or None,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": base.now(),
        "execution_admission": manifest,
    }
    if not source_admitted:
        return {
            **record,
            "status": "source_identity_unavailable" if source_head else "source_identity_unbound",
            "reason": "EXACT_WORKER_SOURCE_COMMIT_AND_TREE_REQUIRED",
        }
    if not manifest.get("all_commands_admitted"):
        return {**record, "status": "execution_not_admitted", "reason": "MODEL_COMMAND_POLICY_REJECTED"}
    if not (manifest.get("backend") or {}).get("admitted"):
        return {
            **record,
            "status": "execution_blocked_no_isolated_executor",
            "reason": "BUBBLEWRAP_UNSHARE_ALL_REQUIRED",
        }

    # Canonical Forge independently checks out row.repo_head before patch
    # application. Its command globals are replaced above, so all candidate tests,
    # negatives and benchmarks pass through the same no-shell isolated executor.
    result = _ORIGINAL_VALIDATE(con, row)
    result["execution_admission"] = manifest
    return result


base.validate_candidate = validate_candidate


def main() -> int:
    return asyncio.run(base.main(base.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
