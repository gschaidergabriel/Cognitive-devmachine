#!/usr/bin/env python3
"""Repository-bound Trigger-2 A02/Hyperposition acceptance runner v1.

This is an execution/evidence wrapper, not a semantic authority. It verifies that the
checkout, the authority-declared producer lineage, and every relevant current source are
bound to real Git objects before it executes the exact A02 adversarial mutation suite and
retained Hyperposition v4 composition tests.

A PASS from this runner is still bounded component evidence. It does not admit training
rows, mint canonical truth/effects, or grant J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

SCHEMA = "CLAY_TRIGGER2_REPOSITORY_BOUND_A02_ACCEPTANCE/v1"
EXPECTED_REPOSITORY = "gschaidergabriel/clay-global-research-entity"
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_REL = Path(
    "research_entity/global/j-space/research/"
    "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)
GENERATION_AUTHORITY_REL = Path(
    "research_entity/global/j-space/research/"
    "TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY_V1.json"
)
TESTS = [
    Path("tests/test_trigger2_a02_discriminator_producer_auth_gate_v1.py"),
    Path("tests/test_trigger2_hyperposition_state_history_generation_bound_gate_v4.py"),
]
RELEVANT_SOURCES = [
    Path("tools/trigger2_a02_discriminator_producer_v1.py"),
    Path("tools/trigger2_a02_discriminator_producer_auth_gate_v1.py"),
    Path("tools/trigger2_hyperposition_state_history_generation_bound_gate_v4.py"),
    Path("tools/trigger2_generation_provenance_gate_v1.py"),
    Path("tools/trigger2_hyperposition_epistemic_preupdate_guard_v1.py"),
    Path("tools/trigger2_hyperposition_reference_labelers_v3.py"),
    Path("tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"),
    Path("the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"),
    AUTHORITY_REL,
    GENERATION_AUTHORITY_REL,
    *TESTS,
    Path("tools/run_trigger2_repository_bound_a02_acceptance_v1.py"),
]


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def _git(*args: str) -> str:
    return _run("git", *args).stdout.strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git_blob_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", spec], cwd=ROOT)


def _normalize_remote(url: str) -> str | None:
    """Return only a canonical repo id; never persist the input URL.

    Exact accepted forms deliberately exclude credential-bearing HTTPS URLs and arbitrary
    suffix matches so the receipt cannot leak a token or accept an attacker-controlled host.
    """
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
    out: dict[str, Any] = {"path": rel.as_posix(), "exists": path.is_file()}
    if not path.is_file():
        out["pass"] = False
        return out
    worktree_sha = _sha256_file(path)
    out["worktree_sha256"] = worktree_sha
    try:
        blob_oid = _git("rev-parse", f"HEAD:{rel.as_posix()}")
        head_bytes = _git_blob_bytes(f"HEAD:{rel.as_posix()}")
    except Exception as exc:
        out["pass"] = False
        out["error"] = type(exc).__name__
        return out
    out["head_blob_oid"] = blob_oid
    out["head_blob_sha256"] = _sha256_bytes(head_bytes)
    out["pass"] = worktree_sha == out["head_blob_sha256"]
    return out


def _lineage_binding(authority: dict[str, Any], head: str) -> dict[str, Any]:
    producer = authority.get("producer")
    lineage = producer.get("source_lineage") if isinstance(producer, dict) else None
    if not isinstance(producer, dict) or not isinstance(lineage, dict):
        return {"pass": False, "failure": "A02_PRODUCER_LINEAGE_AUTHORITY_REQUIRED"}

    commit = lineage.get("source_commit_sha")
    source_path = lineage.get("source_path")
    expected_sha = producer.get("source_sha256")
    if not all(isinstance(x, str) and x for x in (commit, source_path, expected_sha)):
        return {"pass": False, "failure": "A02_PRODUCER_LINEAGE_FIELDS_REQUIRED"}

    commit_exists = _run("git", "cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode == 0
    ancestry = False
    commit_blob_oid = None
    commit_blob_sha256 = None
    head_blob_oid = None
    head_blob_sha256 = None
    if commit_exists:
        ancestry = _run("git", "merge-base", "--is-ancestor", commit, head, check=False).returncode == 0
        try:
            commit_blob_oid = _git("rev-parse", f"{commit}:{source_path}")
            commit_blob_sha256 = _sha256_bytes(_git_blob_bytes(f"{commit}:{source_path}"))
            head_blob_oid = _git("rev-parse", f"HEAD:{source_path}")
            head_blob_sha256 = _sha256_bytes(_git_blob_bytes(f"HEAD:{source_path}"))
        except Exception:
            pass

    current_path = ROOT / source_path
    current_sha = _sha256_file(current_path) if current_path.is_file() else None
    exact_bytes = (
        commit_blob_sha256 is not None
        and commit_blob_sha256 == expected_sha
        and head_blob_sha256 == expected_sha
        and current_sha == expected_sha
    )
    repository_declared = lineage.get("repository") == EXPECTED_REPOSITORY
    branch_declared = lineage.get("branch") == "main"
    path_declared = producer.get("repo_path") == source_path
    passed = bool(
        commit_exists
        and ancestry
        and exact_bytes
        and repository_declared
        and branch_declared
        and path_declared
    )
    return {
        "pass": passed,
        "source_commit_sha": commit,
        "source_path": source_path,
        "commit_exists": commit_exists,
        "commit_is_ancestor_of_executed_head": ancestry,
        "commit_blob_oid": commit_blob_oid,
        "commit_blob_sha256": commit_blob_sha256,
        "executed_head_blob_oid": head_blob_oid,
        "executed_head_blob_sha256": head_blob_sha256,
        "worktree_sha256": current_sha,
        "authority_source_sha256": expected_sha,
        "repository_declared_exact": repository_declared,
        "branch_declared_main": branch_declared,
        "path_declared_exact": path_declared,
        "all_three_byte_identities_match": exact_bytes,
    }


def _pytest() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "-q", *(p.as_posix() for p in TESTS)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": p.returncode,
        "pass": p.returncode == 0,
        "stdout": p.stdout,
        "stderr": p.stderr,
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

    normalized_repository = _normalize_remote(raw_remote)
    repository_ok = normalized_repository == EXPECTED_REPOSITORY
    if not repository_ok:
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
            "failure": "A02_AUTHORITY_LOAD_FAILED",
            "error": type(exc).__name__,
        }, sort_keys=True))
        return 2

    source_bindings = {p.as_posix(): _head_binding(p) for p in RELEVANT_SOURCES}
    bad_sources = sorted(k for k, v in source_bindings.items() if not v.get("pass"))
    if bad_sources:
        failures.append("WORKTREE_SOURCE_NOT_EXACT_HEAD:" + ",".join(bad_sources))

    lineage = _lineage_binding(authority, head)
    if not lineage.get("pass"):
        failures.append("A02_GIT_OBJECT_LINEAGE_BINDING_FAILED")

    test_result = _pytest() if not failures else {
        "pass": False,
        "executed": False,
        "reason": "PREEXECUTION_REPOSITORY_BINDING_FAILED",
    }
    if test_result.get("pass") is not True:
        failures.append("A02_OR_RETAINED_V4_TEST_SUITE_FAILED_OR_NOT_EXECUTED")

    dirty_after = bool(_git("status", "--porcelain"))
    if dirty_after:
        failures.append("WORKTREE_DIRTY_AFTER_EXECUTION")

    authority_sha256 = _sha256_file(ROOT / AUTHORITY_REL)
    generation_authority_sha256 = _sha256_file(ROOT / GENERATION_AUTHORITY_REL)
    policy_jcs_sha256 = authority.get("policy_jcs_sha256")
    failures = sorted(set(failures))
    receipt = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_component_acceptance_pass": not failures,
        "failures": failures,
        "repository": EXPECTED_REPOSITORY,
        "origin_repository_normalized": normalized_repository,
        "origin_remote_secret_fence": "RAW_REMOTE_URL_NOT_PERSISTED",
        "repository_remote_identity_verified": repository_ok,
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
        "a02_producer_git_object_lineage": lineage,
        "a02_authority": {
            "path": AUTHORITY_REL.as_posix(),
            "sha256": authority_sha256,
            "policy_jcs_sha256": policy_jcs_sha256,
        },
        "generation_authority": {
            "path": GENERATION_AUTHORITY_REL.as_posix(),
            "sha256": generation_authority_sha256,
        },
        "tests": test_result,
        "evidence_boundary": {
            "source_or_runner_presence_is_runtime_credit": False,
            "canonical_dataset_admission": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "jspace_runtime_credit_minted": 0,
            "hcu_runtime_credit_minted": 0,
            "entityos_runtime_credit_minted": 0,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "supervisor_or_admission_review_required_for_credit": True,
        },
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
