#!/usr/bin/env python3
"""Exact-source wrapper and strict runtime binder for the local Qwen3-0.6B J-Space path.

This tool does not run a second scientific intervention. When separately authorized to
execute the existing Trigger-1 local Qwen experiment, it launches that exact executor
from a clean Git worktree and seals source/runtime/model/endpoint identities into one
recomputable receipt. It never mints canonical, whole-EntityOS/HCU, J-Space-model, or
training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR_REL = Path("tools/trigger1_local_qwen06_activation_api_execute.py")
RESULT_NAME = "trigger1_local_activation_api_result.json"
CANDIDATE_NAME = "trigger1_direct_steering_candidate.json"
BINDING_NAME = "trigger1_local_runtime_binding.json"
BOUND_CANDIDATE_NAME = "trigger1_direct_steering_candidate_bound.json"
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_BOUND_RUNTIME/v1"
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
RESULT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex(value: Any, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git(repo_root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        timeout=15,
        check=False,
    )


def capture_source_attestation(repo_root: Path, launcher_path: Path, executor_path: Path) -> dict[str, Any]:
    head = _git(repo_root, "rev-parse", "HEAD")
    tree = _git(repo_root, "rev-parse", "HEAD^{tree}")
    status = _git(repo_root, "status", "--porcelain=v1", "-z", "--untracked-files=all", text=False)
    if head.returncode or tree.returncode or status.returncode:
        raise RuntimeError("GIT_SOURCE_ATTESTATION_UNAVAILABLE")
    head_value = str(head.stdout).strip()
    tree_value = str(tree.stdout).strip()
    status_bytes = bytes(status.stdout)
    if not is_hex(head_value, 40) or not is_hex(tree_value, 40):
        raise RuntimeError("GIT_SOURCE_IDENTITY_INVALID")
    if status_bytes:
        raise RuntimeError("SOURCE_WORKTREE_DIRTY_FAIL_CLOSED")
    exe = Path(sys.executable).resolve()
    if not launcher_path.is_file() or not executor_path.is_file() or not exe.is_file():
        raise RuntimeError("BOUND_EXECUTABLE_PATH_MISSING")
    return {
        "repo_head": head_value,
        "repo_tree": tree_value,
        "repo_dirty": False,
        "git_status_porcelain_v1_z_sha256": sha256_bytes(status_bytes),
        "launcher_relpath": str(launcher_path.relative_to(repo_root)),
        "launcher_sha256": sha256_file(launcher_path),
        "executor_relpath": str(executor_path.relative_to(repo_root)),
        "executor_sha256": sha256_file(executor_path),
        "python_executable": str(exe),
        "python_executable_sha256": sha256_file(exe),
    }


def _require_loopback(endpoint: Any) -> str:
    if not isinstance(endpoint, str) or not endpoint:
        raise RuntimeError("LOCAL_ENDPOINT_REQUIRED")
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("LOCAL_ENDPOINT_NOT_LOOPBACK")
    return endpoint


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _verify_result_digest(result: dict[str, Any]) -> str:
    got = result.get("result_sha256")
    if not is_hex(got, 64):
        raise RuntimeError("RESULT_SHA256_REQUIRED")
    payload = dict(result)
    payload.pop("result_sha256", None)
    expected = canonical_sha(payload)
    if got != expected:
        raise RuntimeError("RESULT_SHA256_MISMATCH")
    return expected


def _recompute_local_receipt(result: dict[str, Any], candidate: dict[str, Any]) -> str:
    source = result.get("source")
    runtime_build = result.get("runtime_build_sha256")
    checkpoint = result.get("checkpoint_sha256")
    tokenizer = result.get("tokenizer_sha256")
    endpoint = _require_loopback(result.get("api_endpoint"))
    calibration_rows = result.get("calibration_rows")
    holdout_rows = result.get("holdout_rows")
    if not isinstance(source, dict):
        raise RuntimeError("RESULT_SOURCE_REQUIRED")
    if not all(is_hex(v, 64) for v in (runtime_build, checkpoint, tokenizer)):
        raise RuntimeError("RESULT_RUNTIME_IDENTITY_REQUIRED")
    if not isinstance(calibration_rows, list) or not isinstance(holdout_rows, list):
        raise RuntimeError("RESULT_INVOCATION_ROWS_REQUIRED")
    invocations = len(calibration_rows) + len(holdout_rows)
    material = {
        "endpoint": endpoint,
        "runtime_build_sha256": runtime_build,
        "checkpoint_sha256": checkpoint,
        "tokenizer_sha256": tokenizer,
        "source": source,
        "api_invocations": invocations,
    }
    expected = canonical_sha(material)
    target = candidate.get("target")
    if not isinstance(target, dict) or target.get("local_runtime_execution_receipt_sha256") != expected:
        raise RuntimeError("LOCAL_RUNTIME_EXECUTION_RECEIPT_MISMATCH")
    return expected


def build_binding(
    pre: dict[str, Any],
    post: dict[str, Any],
    result: dict[str, Any],
    candidate: dict[str, Any],
    base_verdict: dict[str, Any],
) -> dict[str, Any]:
    if pre != post:
        raise RuntimeError("SOURCE_ATTESTATION_CHANGED_DURING_EXECUTION")
    if pre.get("repo_dirty") is not False:
        raise RuntimeError("SOURCE_WORKTREE_NOT_CLEAN")
    if result.get("schema") != RESULT_SCHEMA or result.get("status") != "PASS":
        raise RuntimeError("UPSTREAM_RUNTIME_RESULT_NOT_PASS")
    if result.get("promotion_candidate_written") is not True:
        raise RuntimeError("UPSTREAM_PROMOTION_CANDIDATE_NOT_WRITTEN")
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise RuntimeError("CANDIDATE_SCHEMA_INVALID")
    if base_verdict.get("owner_trigger1_goal_credit_candidate") is not True:
        raise RuntimeError("BASE_PROMOTION_GATE_NOT_POSITIVE")
    if base_verdict.get("canonical_credit_minted") is not False:
        raise RuntimeError("BASE_GATE_CANONICAL_CREDIT_BOUNDARY_VIOLATED")

    source = result.get("source")
    source_identity = candidate.get("source_identity")
    runtime = result.get("runtime_manifest")
    transport = candidate.get("transport")
    target = candidate.get("target")
    if not all(isinstance(v, dict) for v in (source, source_identity, runtime, transport, target)):
        raise RuntimeError("BOUND_OBJECTS_REQUIRED")
    assert isinstance(source, dict) and isinstance(source_identity, dict)
    assert isinstance(runtime, dict) and isinstance(transport, dict) and isinstance(target, dict)

    if source.get("repo_head") != pre.get("repo_head") or source.get("repo_tree") != pre.get("repo_tree"):
        raise RuntimeError("RESULT_SOURCE_DOES_NOT_MATCH_ATTESTED_TREE")
    if source_identity.get("repo_head") != pre.get("repo_head"):
        raise RuntimeError("CANDIDATE_SOURCE_HEAD_MISMATCH")
    if runtime.get("python_executable_sha256") != pre.get("python_executable_sha256"):
        raise RuntimeError("PYTHON_EXECUTABLE_IDENTITY_MISMATCH")
    for key in ("torch_version", "torch_module_sha256", "transformers_version", "transformers_module_sha256"):
        if runtime.get(key) in (None, ""):
            raise RuntimeError(f"RUNTIME_BINDING_FIELD_REQUIRED:{key}")
    for key in ("torch_module_sha256", "transformers_module_sha256"):
        if not is_hex(runtime.get(key), 64):
            raise RuntimeError(f"RUNTIME_BINDING_SHA256_REQUIRED:{key}")

    if result.get("model") != MODEL_ID or result.get("model_revision") != MODEL_REVISION:
        raise RuntimeError("PINNED_MODEL_IDENTITY_MISMATCH")
    checkpoint = result.get("checkpoint_sha256")
    tokenizer = result.get("tokenizer_sha256")
    runtime_build = result.get("runtime_build_sha256")
    if not all(is_hex(v, 64) for v in (checkpoint, tokenizer, runtime_build)):
        raise RuntimeError("MODEL_RUNTIME_DIGEST_REQUIRED")
    if source_identity.get("runtime_build_sha256") != runtime_build:
        raise RuntimeError("CANDIDATE_RUNTIME_BUILD_MISMATCH")
    if source_identity.get("checkpoint_sha256") != checkpoint:
        raise RuntimeError("CANDIDATE_CHECKPOINT_MISMATCH")
    if source_identity.get("tokenizer_sha256") != tokenizer:
        raise RuntimeError("CANDIDATE_TOKENIZER_MISMATCH")

    endpoint = _require_loopback(result.get("api_endpoint"))
    if transport.get("endpoint") != endpoint or transport.get("loopback_only") is not True or transport.get("api_served") is not True:
        raise RuntimeError("CANDIDATE_LOOPBACK_TRANSPORT_MISMATCH")
    if result.get("api_loopback_only") is not True:
        raise RuntimeError("RESULT_LOOPBACK_ONLY_REQUIRED")
    if result.get("zero_provider_billing") is not True or target.get("zero_provider_billing") is not True:
        raise RuntimeError("ZERO_PROVIDER_BILLING_REQUIRED")
    if result.get("external_provider_credentials_read") is not False:
        raise RuntimeError("EXTERNAL_PROVIDER_CREDENTIAL_FENCE_FAILED")
    if target.get("provider") != "local":
        raise RuntimeError("LOCAL_PROVIDER_REQUIRED")
    if target.get("model_or_route") != f"{MODEL_ID}@{MODEL_REVISION}":
        raise RuntimeError("TARGET_MODEL_ROUTE_MISMATCH")

    result_sha = _verify_result_digest(result)
    local_receipt = _recompute_local_receipt(result, candidate)
    candidate_sha = canonical_sha(candidate)
    runtime_manifest_sha = canonical_sha(runtime)
    if runtime_build != runtime_manifest_sha:
        raise RuntimeError("RUNTIME_BUILD_PREIMAGE_MISMATCH")

    binding_material = {
        "schema": SCHEMA,
        "source_attestation": pre,
        "executor_runtime": {
            "python_executable_sha256": pre["python_executable_sha256"],
            "torch_version": runtime["torch_version"],
            "torch_module_sha256": runtime["torch_module_sha256"],
            "transformers_version": runtime["transformers_version"],
            "transformers_module_sha256": runtime["transformers_module_sha256"],
            "runtime_build_sha256": runtime_build,
        },
        "model_runtime": {
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "checkpoint_sha256": checkpoint,
            "tokenizer_sha256": tokenizer,
        },
        "transport": {
            "endpoint": endpoint,
            "loopback_only": True,
            "zero_provider_billing": True,
            "external_provider_credentials_read": False,
        },
        "evidence": {
            "result_sha256": result_sha,
            "candidate_canonical_sha256": candidate_sha,
            "local_runtime_execution_receipt_sha256": local_receipt,
            "base_promotion_gate_schema": base_verdict.get("schema"),
            "base_owner_goal_candidate": True,
        },
        "credit_boundary": {
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        },
    }
    return {**binding_material, "runtime_binding_sha256": canonical_sha(binding_material)}


def _outside_repo(repo_root: Path, output_dir: Path) -> bool:
    try:
        output_dir.resolve().relative_to(repo_root.resolve())
        return False
    except ValueError:
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir", default=None)
    args = parser.parse_args()

    repo_root = ROOT.resolve()
    launcher = Path(__file__).resolve()
    executor = (repo_root / EXECUTOR_REL).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    binding_path = output_dir / BINDING_NAME

    try:
        if not _outside_repo(repo_root, output_dir):
            raise RuntimeError("OUTPUT_DIR_MUST_BE_OUTSIDE_REPO_FOR_CLEAN_ATTESTATION")
        pre = capture_source_attestation(repo_root, launcher, executor)
        command = [sys.executable, str(executor), "--output-dir", str(output_dir)]
        if args.cache_dir:
            command.extend(["--cache-dir", str(Path(args.cache_dir).resolve())])
        completed = subprocess.run(command, cwd=str(repo_root), check=False)
        post = capture_source_attestation(repo_root, launcher, executor)

        result_path = output_dir / RESULT_NAME
        candidate_path = output_dir / CANDIDATE_NAME
        if not result_path.is_file():
            raise RuntimeError(f"UPSTREAM_RESULT_MISSING:exit={completed.returncode}")
        result = _load_json(result_path)
        if completed.returncode != 0 or not candidate_path.is_file():
            blocked = {
                "schema": SCHEMA,
                "status": "UPSTREAM_NOT_PROMOTABLE",
                "upstream_exit_code": completed.returncode,
                "source_attestation_pre": pre,
                "source_attestation_post": post,
                "upstream_result_sha256": sha256_file(result_path),
                "credit_boundary": {
                    "canonical_credit_minted": False,
                    "whole_entityos_hcu_credit": False,
                    "jspace_model_runtime_credit": False,
                    "training_credit": False,
                },
            }
            blocked["runtime_binding_sha256"] = canonical_sha(blocked)
            binding_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return completed.returncode if completed.returncode else 2

        candidate = _load_json(candidate_path)
        tools_dir = str(repo_root / "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import trigger1_jspace_promotion_gate as promotion_gate

        base_verdict = promotion_gate.adjudicate(candidate)
        binding = build_binding(pre, post, result, candidate, base_verdict)
        binding["status"] = "BOUND_PROMOTION_CANDIDATE"
        binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        bound_candidate = dict(candidate)
        bound_candidate["runtime_binding"] = {
            "schema": SCHEMA,
            "runtime_binding_sha256": binding["runtime_binding_sha256"],
            "binding_receipt": BINDING_NAME,
        }
        (output_dir / BOUND_CANDIDATE_NAME).write_text(
            json.dumps(bound_candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        failed = {
            "schema": SCHEMA,
            "status": "BLOCKED_FAIL_CLOSED",
            "reason": f"{type(exc).__name__}:{str(exc)[:1200]}",
            "credit_boundary": {
                "canonical_credit_minted": False,
                "whole_entityos_hcu_credit": False,
                "jspace_model_runtime_credit": False,
                "training_credit": False,
            },
        }
        failed["runtime_binding_sha256"] = canonical_sha(failed)
        binding_path.write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
