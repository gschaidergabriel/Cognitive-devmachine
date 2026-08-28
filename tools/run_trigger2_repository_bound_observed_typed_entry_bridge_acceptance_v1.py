#!/usr/bin/env python3
"""Repository-bound acceptance runner for Trigger-2 OBSERVED Typed Entry bridge v1.

Scope is deliberately narrow: exact checkout/source binding, gate regressions, retained
Typed Entry replay/generation regression, and real fail-closed execution against the
current intentionally-empty admission-witness authority. A green result proves only
bounded source/component behavior. It does not prove a positive witness path and mints
zero dataset/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

SCHEMA = "CLAY_TRIGGER2_REPOSITORY_BOUND_OBSERVED_TYPED_ENTRY_BRIDGE_ACCEPTANCE/v1"
EXPECTED_REPOSITORY = "gschaidergabriel/clay-global-research-entity"
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_REL = Path("research_entity/global/j-space/research/TRIGGER2_OBSERVED_TYPED_ENTRY_BRIDGE_AUTHORITY_V1.json")
GATE_REL = Path("tools/trigger2_observed_evidence_typed_entry_bridge_gate_v1.py")
TEST_REL = Path("tests/test_trigger2_observed_evidence_typed_entry_bridge_gate_v1.py")
ENTRY_REL = Path("the artefact/MicroEntity/hcu/xeno_entry_fabric_v1.py")
ENTRY_REPLAY_TEST_REL = Path("the artefact/MicroEntity/hcu/test_entry_generation_replay_identity_v1.py")
RUNNER_REL = Path("tools/run_trigger2_repository_bound_observed_typed_entry_bridge_acceptance_v1.py")
RELEVANT = [AUTHORITY_REL, GATE_REL, TEST_REL, ENTRY_REL, ENTRY_REPLAY_TEST_REL, RUNNER_REL]


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=ROOT, check=check, capture_output=True, text=True)


def _git(*args: str) -> str:
    return _run("git", *args).stdout.strip()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_remote(url: str) -> str | None:
    value = url.strip().rstrip("/")
    accepted = {
        "https://github.com/gschaidergabriel/clay-global-research-entity",
        "https://github.com/gschaidergabriel/clay-global-research-entity.git",
        "git@github.com:gschaidergabriel/clay-global-research-entity",
        "git@github.com:gschaidergabriel/clay-global-research-entity.git",
        "ssh://git@github.com/gschaidergabriel/clay-global-research-entity",
        "ssh://git@github.com/gschaidergabriel/clay-global-research-entity.git",
    }
    return EXPECTED_REPOSITORY if value in accepted else None


def _head_binding(rel: Path) -> dict[str, Any]:
    path = ROOT / rel
    out: dict[str, Any] = {"path": rel.as_posix(), "exists": path.is_file(), "pass": False}
    if not path.is_file():
        return out
    out["worktree_sha256"] = _sha256_file(path)
    try:
        blob_oid = _git("rev-parse", f"HEAD:{rel.as_posix()}")
        head_bytes = subprocess.check_output(["git", "show", f"HEAD:{rel.as_posix()}"], cwd=ROOT)
    except Exception as exc:
        out["error"] = type(exc).__name__
        return out
    out["head_blob_oid"] = blob_oid
    out["head_sha256"] = hashlib.sha256(head_bytes).hexdigest()
    out["pass"] = out["head_sha256"] == out["worktree_sha256"]
    return out


def _producer_lineage(authority: dict[str, Any], head: str) -> dict[str, Any]:
    producer = authority.get("entry_fabric_producer")
    lineage = producer.get("source_lineage") if isinstance(producer, dict) else None
    if not isinstance(producer, dict) or not isinstance(lineage, dict):
        return {"pass": False, "failure": "ENTRY_PRODUCER_LINEAGE_REQUIRED"}
    commit = lineage.get("source_commit_sha")
    path = lineage.get("source_path")
    expected_blob = producer.get("source_git_blob_sha")
    if not all(isinstance(x, str) and x for x in (commit, path, expected_blob)):
        return {"pass": False, "failure": "ENTRY_PRODUCER_LINEAGE_FIELDS_REQUIRED"}
    commit_exists = _run("git", "cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode == 0
    ancestor = False
    commit_blob = None
    head_blob = None
    if commit_exists:
        ancestor = _run("git", "merge-base", "--is-ancestor", commit, head, check=False).returncode == 0
        try:
            commit_blob = _git("rev-parse", f"{commit}:{path}")
            head_blob = _git("rev-parse", f"HEAD:{path}")
        except Exception:
            pass
    passed = bool(
        commit_exists and ancestor and commit_blob == expected_blob and head_blob == expected_blob
        and lineage.get("repository") == EXPECTED_REPOSITORY
        and lineage.get("branch") == "main"
        and producer.get("repo_path") == path
    )
    return {
        "pass": passed,
        "source_commit_sha": commit,
        "source_path": path,
        "source_commit_exists": commit_exists,
        "source_commit_is_ancestor": ancestor,
        "source_commit_blob_oid": commit_blob,
        "executed_head_blob_oid": head_blob,
        "authority_expected_blob_oid": expected_blob,
    }


def _load_gate():
    path = ROOT / GATE_REL
    spec = importlib.util.spec_from_file_location("trigger2_observed_bridge_acceptance_gate", path)
    if spec is None or spec.loader is None:
        raise ImportError("GATE_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _negative_runtime_checks() -> dict[str, Any]:
    gate = _load_gate()
    forged_receipt = {
        "schema": gate.OBSERVATION_RECEIPT_SCHEMA,
        "event_id": "forged-observed-event",
        "admission_witness_id": "caller-invented-witness",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    forged_envelope = {
        "schema": gate.ENVELOPE_SCHEMA,
        "event_id": "forged-observed-event",
        "admission_witness_id": "caller-invented-witness",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    row = {
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": {
            "event_id": "forged-observed-event",
            "epistemic_type": "OBSERVED",
        },
        "typed_observation_evidence_receipts_evaluator_only": [forged_receipt],
        "typed_observation_admission_envelopes_evaluator_only": [forged_envelope],
    }
    result = gate.adjudicate(row)
    result_failures = result.get("failures", []) if isinstance(result, dict) else []
    unlisted_rejected = (
        isinstance(result, dict)
        and result.get("pass") is False
        and any("OBS_ENTRY_WITNESS_NOT_ADMITTED" in str(item) for item in result_failures)
    )

    legacy_only = dict(row)
    legacy_only["typed_observation_admission_envelopes_evaluator_only"] = []
    legacy_result = gate.adjudicate(legacy_only)
    legacy_failures = legacy_result.get("failures", []) if isinstance(legacy_result, dict) else []
    legacy_rejected = (
        isinstance(legacy_result, dict)
        and legacy_result.get("pass") is False
        and any("OBS_ENTRY_ENVELOPE_REQUIRED" in str(item) for item in legacy_failures)
    )
    return {
        "pass": unlisted_rejected and legacy_rejected,
        "forged_coherent_unlisted_witness_rejected": unlisted_rejected,
        "legacy_receipt_without_independent_envelope_rejected": legacy_rejected,
        "forged_result": result,
        "legacy_only_result": legacy_result,
    }


def _pytest() -> dict[str, Any]:
    tests = [TEST_REL, ENTRY_REPLAY_TEST_REL]
    cmd = [sys.executable, "-m", "pytest", "-q", *(p.as_posix() for p in tests)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "pass": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    failures: list[str] = []
    try:
        head = _git("rev-parse", "HEAD")
        tree = _git("rev-parse", "HEAD^{tree}")
        raw_remote = _git("remote", "get-url", "origin")
    except Exception as exc:
        print(json.dumps({
            "schema": SCHEMA,
            "pass": False,
            "failure": "GIT_CHECKOUT_REQUIRED",
            "error": type(exc).__name__,
        }, sort_keys=True))
        return 2

    normalized_repo = _normalize_remote(raw_remote)
    if normalized_repo != EXPECTED_REPOSITORY:
        failures.append("REPOSITORY_REMOTE_IDENTITY_MISMATCH")
    dirty_before = bool(_git("status", "--porcelain"))
    if dirty_before:
        failures.append("WORKTREE_DIRTY_BEFORE_EXECUTION")

    try:
        authority = json.loads((ROOT / AUTHORITY_REL).read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({
            "schema": SCHEMA,
            "pass": False,
            "failure": "AUTHORITY_LOAD_FAILED",
            "error": type(exc).__name__,
        }, sort_keys=True))
        return 2

    source_bindings = {path.as_posix(): _head_binding(path) for path in RELEVANT}
    if any(not item.get("pass") for item in source_bindings.values()):
        failures.append("WORKTREE_SOURCE_NOT_EXACT_HEAD")

    lineage = _producer_lineage(authority, head)
    if lineage.get("pass") is not True:
        failures.append("ENTRY_PRODUCER_GIT_OBJECT_LINEAGE_FAILED")

    witness_count = len(authority.get("admission_witnesses", {})) if isinstance(authority.get("admission_witnesses"), dict) else -1
    if witness_count != 0:
        failures.append("SOURCE_INTRODUCTION_EXPECTS_EMPTY_WITNESS_AUTHORITY")

    tests = _pytest() if not failures else {
        "pass": False,
        "executed": False,
        "reason": "PREEXECUTION_BINDING_FAILED",
    }
    if tests.get("pass") is not True:
        failures.append("OBSERVED_BRIDGE_REGRESSION_SUITE_FAILED_OR_NOT_EXECUTED")

    negatives = _negative_runtime_checks() if not failures else {
        "pass": False,
        "executed": False,
        "reason": "PREEXECUTION_OR_TEST_FAILURE",
    }
    if negatives.get("pass") is not True:
        failures.append("OBSERVED_BRIDGE_FAIL_CLOSED_RUNTIME_CHECK_FAILED_OR_NOT_EXECUTED")

    dirty_after = bool(_git("status", "--porcelain"))
    if dirty_after:
        failures.append("WORKTREE_DIRTY_AFTER_EXECUTION")

    failures = sorted(set(failures))
    receipt = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_component_acceptance_pass": not failures,
        "scope": "EMPTY_WITNESS_FAIL_CLOSED_SOURCE_COMPONENT_ONLY",
        "positive_witness_path_executed": False,
        "positive_witness_path_reason": "AUTHORITY_INTENTIONALLY_HAS_ZERO_ADMISSION_WITNESSES",
        "failures": failures,
        "repository": EXPECTED_REPOSITORY,
        "origin_repository_normalized": normalized_repo,
        "origin_remote_secret_fence": "RAW_REMOTE_URL_NOT_PERSISTED",
        "executed_head": head,
        "executed_tree": tree,
        "dirty_before": dirty_before,
        "dirty_after": dirty_after,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "source_bindings": source_bindings,
        "entry_producer_lineage": lineage,
        "authority": {
            "path": AUTHORITY_REL.as_posix(),
            "sha256": _sha256_file(ROOT / AUTHORITY_REL),
            "admission_witness_count": witness_count,
        },
        "tests": tests,
        "negative_runtime_checks": negatives,
        "evidence_boundary": {
            "source_or_runner_presence_is_runtime_credit": False,
            "positive_observed_instance_authentication_credit": 0,
            "canonical_dataset_admission": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "jspace_runtime_credit_minted": 0,
            "hcu_runtime_credit_minted": 0,
            "entityos_runtime_credit_minted": 0,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "next_required_gate": "independently produced real admission witness + exact positive/negative repository-bound execution",
        },
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
