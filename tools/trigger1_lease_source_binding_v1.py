#!/usr/bin/env python3
"""Bind a canonical Trigger-1 atomic claim to the exact execution source.

This is not a second lease authority. It reuses trigger1_atomic_lease_gate.validate_claim,
then proves that the clean source measured immediately before intervention is a permitted
successor of the claim's observed main. The provided pre-intervention identity is also
remeasured against the repository at binding time. When workflow-captured source HEAD/tree
or claim SHA are supplied, they must match the same source and canonical claim.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "tools" / "trigger1_atomic_lease_gate.py"
SOURCE_IDENTITY_PATH = ROOT / "tools" / "git_source_identity_v1.py"
SCHEMA = "CLAY_TRIGGER1_LEASE_SOURCE_BINDING/v1"
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_IMPORT_UNAVAILABLE:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_ok(repo: Path, *args: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0


def validate_binding(
    *,
    repo: Path,
    source_identity: dict[str, Any],
    claims_root: Path,
    trigger_key: str,
    expected_claim_sha256: str | None = None,
    expected_source_head: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    gate = load_module(GATE_PATH, "trigger1_atomic_lease_gate")
    source_mod = load_module(SOURCE_IDENTITY_PATH, "git_source_identity_v1")

    lease = gate.validate_claim(
        issue_body=f"trigger_key: {trigger_key}\n",
        claims_root=claims_root,
        expected_experiment=gate.EXPECTED_EXPERIMENT,
    )
    if lease.get("pass") is not True:
        return {
            "schema": SCHEMA,
            "pass": False,
            "reason": f"ATOMIC_LEASE_REVALIDATION_FAILED:{lease.get('reason')}",
            "trigger_key": trigger_key,
            "lease_revalidation": lease,
        }

    measured_now = source_mod.source_identity(repo)
    head = str(source_identity.get("repo_head") or "")
    tree = str(source_identity.get("repo_tree") or "")
    dirty_state = source_identity.get("dirty_state") if isinstance(source_identity.get("dirty_state"), dict) else {}
    checks: dict[str, bool] = {
        "source_schema": source_identity.get("schema") == "CLAY_GIT_SOURCE_IDENTITY/v1",
        "source_head_valid": bool(HEAD_RE.fullmatch(head)),
        "source_tree_valid": bool(HEAD_RE.fullmatch(tree)),
        "source_clean": dirty_state.get("dirty") is False,
        "source_identity_matches_current_repo": (
            source_identity.get("source_identity_sha256") == measured_now.get("source_identity_sha256")
        ),
        "claim_sha_valid": bool(SHA256_RE.fullmatch(str(lease.get("claim_sha256") or ""))),
    }

    claim_sha = str(lease.get("claim_sha256") or "")
    claim_main = str(lease.get("observed_canonical_main") or "")
    checks["claim_main_valid"] = bool(HEAD_RE.fullmatch(claim_main))

    if expected_claim_sha256 is not None:
        checks["workflow_claim_sha_matches"] = expected_claim_sha256 == claim_sha
    if expected_source_head is not None:
        checks["workflow_source_head_matches"] = expected_source_head == head
    if expected_source_tree is not None:
        checks["workflow_source_tree_matches"] = expected_source_tree == tree

    if checks["source_head_valid"] and checks["claim_main_valid"]:
        checks["claim_main_exists"] = git_ok(repo, "cat-file", "-e", f"{claim_main}^{{commit}}")
        checks["claim_main_is_ancestor_of_execution_head"] = bool(
            checks["claim_main_exists"] and git_ok(repo, "merge-base", "--is-ancestor", claim_main, head)
        )
    else:
        checks["claim_main_exists"] = False
        checks["claim_main_is_ancestor_of_execution_head"] = False

    passed = all(checks.values())
    payload = {
        "schema": SCHEMA,
        "pass": passed,
        "reason": "LEASE_SOURCE_BINDING_PASS" if passed else "LEASE_SOURCE_BINDING_FAILED",
        "trigger_key": trigger_key,
        "claim_path": lease.get("claim_path"),
        "claim_sha256": claim_sha,
        "claim_observed_main": claim_main,
        "execution_source_head": head,
        "execution_source_tree": tree,
        "execution_source_identity_sha256": source_identity.get("source_identity_sha256"),
        "remeasured_source_identity_sha256": measured_now.get("source_identity_sha256"),
        "checks": checks,
    }
    payload["binding_sha256"] = canonical_sha(payload)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--source-identity", type=Path, required=True)
    ap.add_argument("--claims-root", type=Path, default=ROOT / "research_entity/continuity/go_experiment_claims")
    ap.add_argument("--trigger-key", required=True)
    ap.add_argument("--expected-claim-sha256")
    ap.add_argument("--expected-source-head")
    ap.add_argument("--expected-source-tree")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    try:
        source = json.loads(args.source_identity.read_text(encoding="utf-8"))
        if not isinstance(source, dict):
            raise ValueError("SOURCE_IDENTITY_NOT_OBJECT")
        result = validate_binding(
            repo=args.repo.resolve(),
            source_identity=source,
            claims_root=args.claims_root.resolve(),
            trigger_key=args.trigger_key,
            expected_claim_sha256=args.expected_claim_sha256,
            expected_source_head=args.expected_source_head,
            expected_source_tree=args.expected_source_tree,
        )
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "pass": False,
            "reason": f"LEASE_SOURCE_BINDING_EXCEPTION:{type(exc).__name__}:{str(exc)[:700]}",
            "trigger_key": args.trigger_key,
        }
        result["binding_sha256"] = canonical_sha(result)

    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
