#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for Evidence Forge.

The base Forge remains the single candidate/evaluation implementation. This wrapper
narrows model-authored command execution before validation and binds exact worker-source
identity. The canonical supervisor owns the existing idempotent Forge->Distillery poll,
so this entrypoint does not create a second conversion loop.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import forge_execution_admission_871 as execution
import run_free_evidence_forge as base

_ORIGINAL_VALIDATE = base.validate_candidate
base.safe_command = execution.safe_command
base.run_cmd = execution.run_cmd


def _source_bound_manifest(row: Any, proposal: dict[str, Any]) -> dict[str, Any]:
    manifest = execution.candidate_execution_manifest(row, proposal)
    source_head = str(manifest.get("source_head") or "")
    if not base.COMMIT_RE.fullmatch(source_head):
        return manifest

    rc, _, err = base._git_text(base.ROOT, "cat-file", "-e", source_head + "^{commit}")
    if rc != 0:
        manifest["source_identity_reason"] = "SOURCE_COMMIT_NOT_PRESENT:" + err[-500:]
        return manifest
    rc, tree, err = base._git_text(base.ROOT, "rev-parse", source_head + "^{tree}")
    if rc != 0 or not tree:
        manifest["source_identity_reason"] = "SOURCE_TREE_UNRESOLVED:" + err[-500:]
        return manifest
    rc, eval_head, err = base._git_text(base.ROOT, "rev-parse", "HEAD")
    if rc != 0 or not base.COMMIT_RE.fullmatch(eval_head):
        manifest["source_identity_reason"] = "EVALUATION_HEAD_UNRESOLVED:" + err[-500:]
        return manifest

    manifest["source_tree"] = tree
    manifest["evaluation_checkout_head"] = eval_head
    manifest["source_identity_admitted"] = True
    manifest["source_identity_reason"] = "EXACT_WORKER_SOURCE_BOUND"
    return manifest


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

    manifest = _source_bound_manifest(row, proposal)
    record = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": row["delta_id"],
        "source_class": "free_swarm",
        "provider": row["provider"],
        "model": row["model"],
        "role": row["role"],
        "worker_sha": row["worker_sha"],
        "source_repo_head": manifest.get("source_head"),
        "evaluation_repo_head": manifest.get("evaluation_checkout_head"),
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": base.now(),
        "execution_admission": manifest,
    }
    if not manifest.get("source_identity_admitted"):
        status = "source_identity_unbound" if not base.COMMIT_RE.fullmatch(str(manifest.get("source_head") or "")) else "source_identity_unavailable"
        return {**record, "status": status, "reason": manifest.get("source_identity_reason")}
    if not manifest.get("all_commands_admitted"):
        return {**record, "status": "execution_not_admitted", "reason": "MODEL_COMMAND_POLICY_REJECTED"}
    if not (manifest.get("backend") or {}).get("admitted"):
        return {**record, "status": "execution_blocked_no_isolated_executor", "reason": "BUBBLEWRAP_REQUIRED"}

    result = _ORIGINAL_VALIDATE(con, row)
    # The canonical base evaluator resolves evaluation_repo_head independently. If it
    # changed after admission, downgrade rather than preserving a nominal ACCEPTED.
    if result.get("evaluation_repo_head") != manifest.get("evaluation_checkout_head"):
        return {
            **result,
            "status": "evaluation_identity_drift",
            "reason": "EVALUATION_HEAD_CHANGED_AFTER_EXECUTION_ADMISSION",
            "execution_admission": manifest,
        }
    result["execution_admission"] = manifest
    return result


base.validate_candidate = validate_candidate


def main() -> int:
    return asyncio.run(base.main(base.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
