#!/usr/bin/env python3
"""Supervisor-8.72 source-identity guard for Trigger-1 local runtime promotion.

This wrapper makes the local Qwen Trigger-1 path fail closed unless the exact repo
HEAD/tree is clean and stable across the runtime experiment.  It then chains the
existing scientific promotion verdict to the observed local runtime receipt and to
pre/post source snapshots, without minting canonical EntityOS/HCU/J-Space credit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PRE = "CLAY_TRIGGER1_SOURCE_PRE_SNAPSHOT/v1"
SCHEMA_VERDICT = "CLAY_TRIGGER1_SOURCE_BOUND_PROMOTION/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{proc.stderr.decode('utf-8', 'replace')[:300]}")
    return proc.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8", "strict").strip()


def source_snapshot() -> dict[str, Any]:
    status = git_bytes("status", "--porcelain=v1", "-z", "--untracked-files=all")
    files = {
        "executor_sha256": sha256_file(ROOT / "tools" / "trigger1_local_qwen06_activation_api_execute.py"),
        "launcher_sha256": sha256_file(ROOT / "tools" / "trigger1_jspace_research.sh"),
        "base_promotion_gate_sha256": sha256_file(ROOT / "tools" / "trigger1_jspace_promotion_gate.py"),
        "source_bound_gate_sha256": sha256_file(Path(__file__).resolve()),
    }
    return {
        "repo_head": git_text("rev-parse", "HEAD"),
        "repo_tree": git_text("rev-parse", "HEAD^{tree}"),
        "worktree_clean": status == b"",
        "worktree_status_sha256": hashlib.sha256(status).hexdigest(),
        "bound_files": files,
    }


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"OBJECT_REQUIRED:{path}")
    return obj


def is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def write_pre(path: Path) -> int:
    snap = source_snapshot()
    payload = {
        "schema": SCHEMA_PRE,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        **snap,
    }
    payload["snapshot_sha256"] = canonical_sha(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["worktree_clean"] else 4


def call_base_gate(gate: Path, candidate: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(gate), "--candidate", str(candidate)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"BASE_GATE_FAILED:{proc.returncode}:{proc.stderr[:500]}")
    obj = json.loads(proc.stdout)
    if not isinstance(obj, dict):
        raise ValueError("BASE_GATE_OBJECT_REQUIRED")
    return obj


def verify(candidate_path: Path, result_path: Path, pre_path: Path, gate_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    candidate = load_json(candidate_path)
    result = load_json(result_path)
    pre = load_json(pre_path)
    post = source_snapshot()

    if pre.get("schema") != SCHEMA_PRE:
        failures.append("PRE_SOURCE_SCHEMA_INVALID")
    if pre.get("worktree_clean") is not True:
        failures.append("PRE_RUNTIME_WORKTREE_NOT_CLEAN")
    if post.get("worktree_clean") is not True:
        failures.append("POST_RUNTIME_WORKTREE_NOT_CLEAN")

    for key in ("repo_head", "repo_tree"):
        if not isinstance(pre.get(key), str) or len(str(pre.get(key))) != 40:
            failures.append(f"PRE_{key.upper()}_INVALID")
        if post.get(key) != pre.get(key):
            failures.append(f"SOURCE_{key.upper()}_CHANGED_DURING_RUNTIME")

    result_source = result.get("source") if isinstance(result.get("source"), dict) else {}
    candidate_source = candidate.get("source_identity") if isinstance(candidate.get("source_identity"), dict) else {}
    if result_source.get("repo_head") != pre.get("repo_head"):
        failures.append("RESULT_HEAD_NOT_BOUND_TO_PRE_SOURCE")
    if result_source.get("repo_tree") != pre.get("repo_tree"):
        failures.append("RESULT_TREE_NOT_BOUND_TO_PRE_SOURCE")
    if candidate_source.get("repo_head") != pre.get("repo_head"):
        failures.append("CANDIDATE_HEAD_NOT_BOUND_TO_PRE_SOURCE")

    pre_files = pre.get("bound_files") if isinstance(pre.get("bound_files"), dict) else {}
    post_files = post.get("bound_files") if isinstance(post.get("bound_files"), dict) else {}
    for key in ("executor_sha256", "launcher_sha256", "base_promotion_gate_sha256", "source_bound_gate_sha256"):
        if not is_sha256(pre_files.get(key)):
            failures.append(f"PRE_BOUND_FILE_SHA_REQUIRED:{key}")
        if post_files.get(key) != pre_files.get(key):
            failures.append(f"BOUND_FILE_CHANGED_DURING_RUNTIME:{key}")

    if result.get("status") != "PASS":
        failures.append("LOCAL_RUNTIME_RESULT_PASS_REQUIRED")
    if result.get("zero_provider_billing") is not True:
        failures.append("ZERO_PROVIDER_BILLING_REQUIRED")
    if result.get("external_provider_credentials_read") is not False:
        failures.append("EXTERNAL_PROVIDER_CREDENTIAL_READ_MUST_BE_FALSE")

    target = candidate.get("target") if isinstance(candidate.get("target"), dict) else {}
    local_runtime_receipt = target.get("local_runtime_execution_receipt_sha256")
    if not is_sha256(local_runtime_receipt):
        failures.append("LOCAL_RUNTIME_EXECUTION_RECEIPT_REQUIRED")

    try:
        base = call_base_gate(gate_path, candidate_path)
    except Exception as exc:
        base = {"owner_trigger1_goal_credit_candidate": False, "failures": [f"{type(exc).__name__}:{str(exc)[:400]}"]}
        failures.append("BASE_PROMOTION_GATE_UNAVAILABLE")

    base_pass = base.get("owner_trigger1_goal_credit_candidate") is True
    if not base_pass:
        failures.append("BASE_SCIENTIFIC_PROMOTION_GATE_NOT_PASS")

    candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    result_sha = hashlib.sha256(result_path.read_bytes()).hexdigest()
    receipt_material = {
        "candidate_sha256": candidate_sha,
        "result_file_sha256": result_sha,
        "local_runtime_execution_receipt_sha256": local_runtime_receipt,
        "pre_source_snapshot_sha256": pre.get("snapshot_sha256"),
        "pre_source": {k: pre.get(k) for k in ("repo_head", "repo_tree", "worktree_clean", "worktree_status_sha256", "bound_files")},
        "post_source": post,
        "base_gate_candidate_sha256": base.get("candidate_sha256"),
        "base_gate_schema": base.get("schema"),
    }
    source_execution_receipt_sha256 = canonical_sha(receipt_material)
    source_bound = not failures

    return {
        "schema": SCHEMA_VERDICT,
        "owner_trigger1_goal_credit_candidate": bool(base_pass and source_bound),
        "mechanism_runtime_vector_credit_candidate": bool(
            base.get("mechanism_runtime_vector_credit_candidate") is True and source_bound
        ),
        "source_bound_runtime_evidence": bool(source_bound),
        "source_execution_receipt_sha256": source_execution_receipt_sha256,
        "local_runtime_execution_receipt_sha256": local_runtime_receipt,
        "pre_source": pre,
        "post_source": post,
        "base_verdict": base,
        "failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS is a Trigger-1 promotion candidate only. It proves the base scientific gate was satisfied "
            "while the exact repo HEAD/tree and bound executor/gate bytes remained clean and stable across "
            "the local runtime. It does not mint canonical EntityOS/HCU/J-Space/training credit."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-pre")
    ap.add_argument("--candidate")
    ap.add_argument("--result")
    ap.add_argument("--pre-source")
    ap.add_argument("--gate", default=str(ROOT / "tools" / "trigger1_jspace_promotion_gate.py"))
    args = ap.parse_args()

    if args.write_pre:
        return write_pre(Path(args.write_pre))

    required = (args.candidate, args.result, args.pre_source)
    if not all(required):
        ap.error("verification requires --candidate, --result, and --pre-source")
    try:
        verdict = verify(Path(args.candidate), Path(args.result), Path(args.pre_source), Path(args.gate))
    except Exception as exc:
        verdict = {
            "schema": SCHEMA_VERDICT,
            "owner_trigger1_goal_credit_candidate": False,
            "mechanism_runtime_vector_credit_candidate": False,
            "source_bound_runtime_evidence": False,
            "failures": [f"SOURCE_BOUND_GATE_ERROR:{type(exc).__name__}:{str(exc)[:500]}"],
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
    print(json.dumps(verdict, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
