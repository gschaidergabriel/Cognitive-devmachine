#!/usr/bin/env python3
"""Supervisor-8.71/8.72 safe entrypoint for the FREE Evidence Forge.

Installs deterministic model-command execution admission before the base Forge
cycle can evaluate a worker-authored candidate. The execution manifest binds both
the exact ``repo_head_at_prompt`` worker source and the observed evaluation checkout;
post-admission evaluation-head drift is downgraded instead of receiving evidence
credit. Candidate output remains noncanonical and no execution is admitted without
the isolated backend.

Model-authored commands may write only inside the disposable Forge worktree. The
rest of the host remains hidden by bubblewrap; this narrow writable bind is required
for ordinary test/build artifacts such as ``__pycache__`` and compiler outputs.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import forge_execution_admission_871 as admission
import run_free_evidence_forge as base
import free_swarm_typed_forge_ingress_872 as typed_ingress

# Install only the candidate-ingestion callback on the real current Forge module.
# This preserves module-global monkeypatch semantics used by all safe-executor gates.
typed_ingress.install(base)

_ORIGINAL_VALIDATE = base.validate_candidate
_ORIGINAL_MANIFEST = admission.candidate_execution_manifest
_ORIGINAL_BWRAP_PREFIX = admission._bubblewrap_prefix
_ORIGINAL_ADMISSION_RUN_CMD = admission.run_cmd
base.safe_command = admission.safe_command


def _is_disposable_forge_workdir(cwd: Path) -> bool:
    """Admit writes only beneath, never at, the canonical Forge scratch root."""
    try:
        forge_root = Path(base.FORGE_ROOT).resolve()
        resolved = cwd.resolve()
        resolved.relative_to(forge_root)
        return resolved != forge_root
    except (OSError, ValueError):
        return False


def _writable_disposable_bwrap_prefix(cwd: Path) -> list[str] | None:
    """Make only the exact disposable candidate checkout writable in bwrap."""
    prefix = _ORIGINAL_BWRAP_PREFIX(cwd)
    if prefix is None or not _is_disposable_forge_workdir(cwd):
        return prefix
    host = str(cwd.resolve())
    for i in range(len(prefix) - 2):
        if prefix[i:i + 3] == ["--ro-bind", host, "/work"]:
            prefix[i] = "--bind"
            return prefix
    # Donor namespace shape changed: fail closed instead of guessing which host
    # path should become writable.
    return None


# The admission module resolves this helper at execution time. Repo-root backend
# probes remain read-only because the root itself is not a disposable child.
admission._bubblewrap_prefix = _writable_disposable_bwrap_prefix


def _run_cmd_disposable_only(cwd: Path, command: str, timeout: int = 120) -> dict[str, Any]:
    if not _is_disposable_forge_workdir(cwd):
        return {
            "rc": 126,
            "elapsed_s": 0.0,
            "stdout": "",
            "stderr": "FORGE_EXECUTION_BLOCKED:WORKDIR_OUTSIDE_DISPOSABLE_FORGE_ROOT",
            "execution_admission": admission.admit_command(command).to_dict(),
        }
    return _ORIGINAL_ADMISSION_RUN_CMD(cwd, command, timeout)


base.run_cmd = _run_cmd_disposable_only


def _source_bound_manifest(row: Any, proposal: dict[str, Any], cwd: Path) -> dict[str, Any]:
    manifest = _ORIGINAL_MANIFEST(row, proposal, cwd)
    evaluation_head = str(manifest.get("evaluation_head") or "").strip().lower()
    try:
        source_head = str(row["repo_head"] or "").strip().lower()
    except Exception:
        source_head = ""

    manifest["evaluation_checkout_head"] = evaluation_head or None
    manifest["evaluation_checkout_tree"] = None
    manifest["source_scope"] = "EXACT_WORKER_PROMPT_HEAD"
    manifest["source_head"] = source_head or None
    manifest["source_tree"] = None
    manifest["source_identity_admitted"] = False
    manifest["source_identity_reason"] = "VALID_REPO_HEAD_AT_PROMPT_REQUIRED"
    manifest["candidate_execution_workdir_scope"] = "DISPOSABLE_FORGE_ROOT_CHILD_ONLY"
    manifest["candidate_worktree_writable"] = True

    if not base.COMMIT_RE.fullmatch(source_head):
        return manifest
    if not base.COMMIT_RE.fullmatch(evaluation_head):
        manifest["source_identity_reason"] = "VALID_EVALUATION_HEAD_REQUIRED"
        return manifest

    rc, _, err = base._git_text(base.ROOT, "cat-file", "-e", source_head + "^{commit}")
    if rc != 0:
        manifest["source_identity_reason"] = "SOURCE_COMMIT_NOT_PRESENT:" + err[-500:]
        return manifest
    rc, tree, err = base._git_text(base.ROOT, "rev-parse", source_head + "^{tree}")
    if rc != 0 or not tree:
        manifest["source_identity_reason"] = "SOURCE_TREE_UNRESOLVED:" + err[-500:]
        return manifest
    rc, evaluation_tree, err = base._git_text(base.ROOT, "rev-parse", evaluation_head + "^{tree}")
    if rc != 0 or not evaluation_tree:
        manifest["source_identity_reason"] = "EVALUATION_TREE_UNRESOLVED:" + err[-500:]
        return manifest

    manifest["source_tree"] = tree
    manifest["evaluation_checkout_tree"] = evaluation_tree
    manifest["source_identity_admitted"] = True
    manifest["source_identity_reason"] = "EXACT_WORKER_AND_EVALUATION_SOURCE_BOUND"
    return manifest


# validate_candidate_with_admission resolves this global at call time, so the
# successor-current manifest reuses the admission mechanism while taking source
# identity from the canonical Forge row rather than inventing a second authority.
admission.candidate_execution_manifest = _source_bound_manifest


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
        "evaluation_repo_head": manifest.get("evaluation_checkout_head"),
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": base.now(),
        "execution_admission": manifest,
    }
    if not manifest.get("source_identity_admitted"):
        return {
            **record,
            "status": "source_identity_unbound"
            if not base.COMMIT_RE.fullmatch(str(manifest.get("source_head") or ""))
            else "source_identity_unavailable",
            "reason": manifest.get("source_identity_reason"),
        }
    if not manifest.get("all_commands_admitted"):
        return {**record, "status": "execution_not_admitted", "reason": "MODEL_COMMAND_POLICY_REJECTED"}
    if not (manifest.get("backend") or {}).get("admitted"):
        return {**record, "status": "execution_blocked_no_isolated_executor", "reason": "BUBBLEWRAP_REQUIRED"}

    # Canonical Forge checks out exactly row.repo_head before patch/application
    # validation. Its run_cmd/safe_command globals are narrowed to the isolated,
    # no-shell admission implementation with a writable disposable worktree only.
    # If the base validator observes a different evaluation checkout after admission,
    # preserve the measurement but fail closed for evidence-qualified ACCEPT credit.
    result = _ORIGINAL_VALIDATE(con, row)
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
