#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for the FREE Evidence Forge.

Installs deterministic model-command execution admission before the base Forge can
evaluate a worker-authored candidate. Source identity remains the canonical Forge
row's exact repo_head_at_prompt. Candidate output is noncanonical; no execution is
admitted without the isolated backend.
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


def _source_bound_manifest(row: Any, proposal: dict[str, Any], cwd: Path) -> dict[str, Any]:
    manifest = admission.candidate_execution_manifest(row, proposal, cwd)
    manifest["evaluation_checkout_head"] = manifest.get("evaluation_head")
    manifest["evaluation_checkout_tree"] = None
    try:
        source_head = str(row["repo_head"] or "").strip().lower()
    except Exception:
        source_head = ""

    manifest["source_scope"] = "EXACT_WORKER_PROMPT_HEAD"
    manifest["source_head"] = source_head or None
    manifest["source_tree"] = None
    manifest["source_identity_admitted"] = False
    manifest["source_identity_reason"] = "VALID_REPO_HEAD_AT_PROMPT_REQUIRED"

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

    manifest["source_tree"] = tree
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

    manifest = _source_bound_manifest(row, proposal, Path(base.ROOT))
    record = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": row["delta_id"],
        "source_class": "free_swarm",
        "provider": row["provider"],
        "model": row["model"],
        "role": row["role"],
        "worker_sha": row["worker_sha"],
        "source_repo_head": manifest.get("source_head"),
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
    result["execution_admission"] = manifest
    return result


base.validate_candidate = validate_candidate


def main() -> int:
    return asyncio.run(base.main(base.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
