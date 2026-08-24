#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for the FREE Evidence Forge.

Installs deterministic model-command execution admission before the base Forge can
evaluate worker-authored candidates. Candidate output remains noncanonical. No
model-authored command is executed without exact worker-source identity, an
allowlisted argv form, a secret-free child environment, and a functional isolated
bubblewrap backend.

The only writable host bind exposed to model-authored commands is the disposable
Forge worktree itself. This is required for ordinary test/build artifacts such as
``__pycache__`` while preserving network isolation and keeping host /home, /run and
other /artifacts paths outside the namespace.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import forge_execution_admission_871 as admission
import run_free_evidence_forge as base

_ORIGINAL_VALIDATE = base.validate_candidate
_ORIGINAL_BWRAP_PREFIX = admission._bubblewrap_prefix
_ORIGINAL_ADMISSION_RUN_CMD = admission.run_cmd


def _is_disposable_forge_workdir(cwd: Path) -> bool:
    try:
        cwd.resolve().relative_to(Path(base.FORGE_ROOT).resolve())
        return cwd.resolve() != Path(base.FORGE_ROOT).resolve()
    except (OSError, ValueError):
        return False


def _writable_disposable_bwrap_prefix(cwd: Path) -> list[str] | None:
    prefix = _ORIGINAL_BWRAP_PREFIX(cwd)
    if prefix is None or not _is_disposable_forge_workdir(cwd):
        return prefix
    host = str(cwd.resolve())
    for i in range(len(prefix) - 2):
        if prefix[i:i + 3] == ["--ro-bind", host, "/work"]:
            prefix[i] = "--bind"
            return prefix
    # The writable-worktree invariant is explicit. If the donor prefix changes and
    # the exact bind cannot be identified, fail closed rather than guessing.
    return None


admission._bubblewrap_prefix = _writable_disposable_bwrap_prefix


def run_cmd(cwd: Path, command: str, timeout: int = 120) -> dict[str, Any]:
    if not _is_disposable_forge_workdir(cwd):
        return {
            "rc": 126,
            "elapsed_s": 0.0,
            "stdout": "",
            "stderr": "FORGE_EXECUTION_BLOCKED:WORKDIR_OUTSIDE_DISPOSABLE_FORGE_ROOT",
            "execution_admission": admission.admit_command(command).to_dict(),
        }
    return _ORIGINAL_ADMISSION_RUN_CMD(cwd, command, timeout)


base.safe_command = admission.safe_command
base.run_cmd = run_cmd


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

    # Manifest construction runs only the isolated-backend probe against the repo
    # root. Untrusted candidate commands are not invoked here; those are separately
    # confined by run_cmd() to a child of FORGE_ROOT.
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
    manifest["candidate_execution_workdir_scope"] = "DISPOSABLE_FORGE_ROOT_CHILD_ONLY"
    manifest["candidate_worktree_writable"] = True
    manifest["host_home_run_other_artifacts_exposed"] = False

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
