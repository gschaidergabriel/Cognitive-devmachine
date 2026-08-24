#!/usr/bin/env python3
"""Emit FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 from exact local source.

This runner is intentionally provider-network blind. It does not load provider
credentials, call provider catalogs, or infer FREE status from environment state.
It executes only deterministic regression files whose hash-bound assertions prove
that blocked admission cases reach neither provider-secret lookup nor provider
network I/O.

A PASS from this tool is component/runtime evidence for the admission boundary only.
It does not grant provider execution authority, whole EntityOS/HCU runtime credit,
J-Space model credit, training credit, or whole-product PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1"

SOURCE_PATHS = (
    "tools/free_provider_admission.py",
    "tools/run_free_go_swarm.py",
    "tools/run_24h_entityos_swarm.py",
    "tools/run_research_distillery_entry.py",
    "tools/rae_secret_loader.py",
    "tools/run_24h_entityos_swarm_supervisor.sh",
    "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)

TEST_PATHS = (
    "tests/test_free_provider_admission_v1.py",
    "tests/test_free_provider_admission_forgery_868.py",
    "tests/test_free_swarm_admission_boundary_867.py",
    "tests/test_free_swarm_admission_boundary_868_malformed.py",
    "tests/test_rae_secret_loader_provider_admission.py",
)

REQUIRED_BOUNDARIES = (
    "missing_global_compatibility_attestation",
    "missing_provider_admission",
    "malformed_provider_admission",
    "unknown_cost_class",
    "paid_cost_class",
    "subscription_cost_class",
    "authority_epoch_mismatch",
    "unlisted_provider",
    "caller_forged_free_payload",
    "blocked_provider_secret_loader",
    "blocked_direct_chat_network",
    "blocked_catalog_network",
    "blocked_openrouter_distillery_secret_and_network",
)

PROVIDER_SECRET_ENV_NAMES = frozenset(
    {
        "GROQ_API_KEY",
        "GROQ_API_KEYS",
        "GROQ2_API_KEY",
        "GROQ3_API_KEY",
        "MISTRAL_API_KEY",
        "MISTRAL_API_KEYS",
        "MISTRAL2_API_KEY",
        "MISTRAL3_API_KEY",
        "NVIDIA_API_KEY",
        "NVIDIA_API_KEYS",
        "NVIDIA_NIM_API_KEY",
        "NGC_API_KEY",
        "NVIDIA2_API_KEY",
        "NVIDIA3_API_KEY",
        "OPENROUTER_API_KEY",
    }
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def resolve_authority() -> tuple[str, str, Path]:
    inbox_path = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = load_json(inbox_path)
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_ref = str(inbox.get("steering") or "").strip()
    if not epoch or not steering_ref:
        raise RuntimeError("current supervisor epoch/steering pointer missing")
    rel = Path(steering_ref)
    if rel.is_absolute() or ".." in rel.parts:
        raise RuntimeError("current supervisor steering pointer is unsafe")
    steering_path = (ROOT / rel).resolve()
    steering_path.relative_to(ROOT.resolve())
    steering = load_json(steering_path)
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise RuntimeError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if (
        steering.get("active_program") != "ENTITYOS_HCU"
        or steering.get("product") != "EntityOS"
        or steering.get("integrated_cognition_compute_architecture") != "HCU"
    ):
        raise RuntimeError("SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH")
    return epoch, steering_ref, steering_path


def source_manifest(steering_path: Path) -> dict[str, str]:
    paths = list(SOURCE_PATHS) + list(TEST_PATHS)
    steering_rel = steering_path.relative_to(ROOT).as_posix()
    if steering_rel not in paths:
        paths.append(steering_rel)
    out: dict[str, str] = {}
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"required source missing: {rel}")
        out[rel] = sha256_file(path)
    return dict(sorted(out.items()))


def manifest_digest(manifest: dict[str, str]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(canonical)


def sanitized_test_environment() -> tuple[dict[str, str], int]:
    env = dict(os.environ)
    removed = 0
    for name in list(env):
        if name in PROVIDER_SECRET_ENV_NAMES:
            removed += 1
            env.pop(name, None)
    # These compatibility assertions are test-controlled; do not inherit them.
    for name in list(env):
        if name == "CLAY_FREE_ONLY_ATTESTED" or (
            name.startswith("CLAY_") and name.endswith("_FREE_ATTESTED")
        ):
            env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env, removed


def run_test(path: str, env: dict[str, str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / path)],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "path": path,
        "exit_code": proc.returncode,
        "pass": proc.returncode == 0,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-4000:],
    }


def build_receipt() -> dict[str, Any]:
    epoch, steering_ref, steering_path = resolve_authority()
    head = git("rev-parse", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    tracked_status = git("status", "--porcelain", "--untracked-files=no")
    manifest = source_manifest(steering_path)
    env, removed_secret_env_count = sanitized_test_environment()
    tests = [run_test(path, env) for path in TEST_PATHS]
    tests_pass = all(row["pass"] for row in tests)
    tracked_clean = not bool(tracked_status.strip())
    passed = tests_pass and tracked_clean

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "authority_epoch": epoch,
        "steering": steering_ref,
        "execution_mode": "FREE_ONLY",
        "repo_head": head,
        "repo_branch": branch,
        "tracked_worktree_clean": tracked_clean,
        "source_manifest_sha256": manifest_digest(manifest),
        "source_manifest": manifest,
        "execution_environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "secret_fence": {
            "real_provider_secret_values_read_by_runner": False,
            "provider_secret_environment_sanitized_before_tests": True,
            "provider_secret_env_names_removed_count": removed_secret_env_count,
            "secret_lookup_count": 0 if tests_pass else None,
            "secret_lookup_count_classification": (
                "DERIVED_FROM_EXECUTED_HASH_BOUND_ZERO_LOOKUP_ASSERTIONS"
                if tests_pass
                else "UNRESOLVED_TEST_FAILURE"
            ),
        },
        "network_fence": {
            "provider_network_requested_by_runner": False,
            "network_attempt_count": 0 if tests_pass else None,
            "network_attempt_count_classification": (
                "DERIVED_FROM_EXECUTED_HASH_BOUND_ZERO_NETWORK_ASSERTIONS"
                if tests_pass
                else "UNRESOLVED_TEST_FAILURE"
            ),
        },
        "required_boundaries": list(REQUIRED_BOUNDARIES),
        "tests": tests,
        "result": "PASS" if passed else "FAIL",
        "credit_scope": "FREE_SWARM_ADMISSION_BOUNDARY_COMPONENT_ONLY",
        "credits": {
            "provider_runtime": 0,
            "whole_entityos_hcu": 0,
            "hcu_full": 0,
            "jspace_model": 0,
            "training": 0,
            "whole_product_pass": False,
        },
        "promotion_note": (
            "PASS proves only the exact hash-bound pre-secret/pre-provider-network admission boundary. "
            "It does not classify any provider FREE and does not authorize provider traffic."
        ),
    }
    if not tracked_clean:
        receipt["failure_reason"] = "TRACKED_WORKTREE_NOT_CLEAN_EXACT_HEAD_BINDING_AMBIGUOUS"
    elif not tests_pass:
        receipt["failure_reason"] = "ONE_OR_MORE_BOUNDARY_TESTS_FAILED"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and emit FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1")
    parser.add_argument("--output", type=Path, help="Optional JSON output path; stdout is always emitted")
    args = parser.parse_args()
    try:
        receipt = build_receipt()
    except Exception as exc:
        receipt = {
            "schema": SCHEMA,
            "result": "FAIL",
            "failure_reason": f"RUNNER_ERROR:{type(exc).__name__}:{exc}",
            "credits": {
                "provider_runtime": 0,
                "whole_entityos_hcu": 0,
                "hcu_full": 0,
                "jspace_model": 0,
                "training": 0,
                "whole_product_pass": False,
            },
        }
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if receipt.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
