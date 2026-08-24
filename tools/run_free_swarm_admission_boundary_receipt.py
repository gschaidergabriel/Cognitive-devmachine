#!/usr/bin/env python3
"""Emit a source-bound FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1.

This runner is intentionally provider-network blind. It executes only the deterministic
admission-boundary unittest suite, records exact source/control-plane identities, and emits
bounded component evidence. A PASS does not admit any provider as FREE and does not create
whole EntityOS/HCU, J-Space, training, or provider-runtime credit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEST_GLOB = "test_free_swarm_*.py"
SCHEMA = "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1"
SOURCE_PATHS = (
    "tools/free_provider_admission.py",
    "tools/run_free_go_swarm.py",
    "tools/run_24h_entityos_swarm.py",
    "tools/run_research_distillery_entry.py",
    "tools/run_24h_entityos_swarm_supervisor.sh",
    "tests/test_free_swarm_admission_boundary_867.py",
    "tests/test_free_swarm_socket_tripwire_868.py",
    "tests/test_free_swarm_admission_boundary_receipt_v1.py",
    "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)
REQUIRED_BLOCKED_CASES = (
    "MISSING_GLOBAL_COMPATIBILITY_ASSERTION",
    "MISSING_PROVIDER_ADMISSION",
    "MALFORMED_PROVIDER_ADMISSION",
    "UNKNOWN",
    "PAID",
    "SUBSCRIPTION",
    "AUTHORITY_MISMATCH",
    "UNLISTED_PROVIDER",
    "OPENROUTER_UNADMITTED_DISTILLERY",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"OBJECT_REQUIRED:{path}")
    return value


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{proc.stderr.strip()}")
    return proc.stdout.strip()


def _source_manifest(extra_paths: tuple[str, ...] = ()) -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for rel in (*SOURCE_PATHS, *extra_paths):
        path = ROOT / rel
        data = path.read_bytes()
        manifest[rel] = {"sha256": _sha256_bytes(data), "bytes": len(data)}
    return manifest


def _safe_child_env() -> dict[str, str]:
    """Do not expose real provider credentials to the boundary-test child process."""
    env = dict(os.environ)
    secret_markers = ("API_KEY", "API_KEYS", "TOKEN", "SECRET", "PASSWORD")
    for key in tuple(env):
        upper = key.upper()
        if any(marker in upper for marker in secret_markers):
            env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_suite() -> tuple[subprocess.CompletedProcess[str], int]:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(ROOT / "tests"),
        "-p",
        TEST_GLOB,
        "-v",
    ]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        env=_safe_child_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )
    combined = proc.stdout + "\n" + proc.stderr
    match = re.search(r"Ran\s+(\d+)\s+tests?", combined)
    return proc, int(match.group(1)) if match else 0


def build_receipt() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")

    inbox_path = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = _read_json(inbox_path)
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel:
        raise RuntimeError("SUPERVISOR_STEERING_REF_REQUIRED")
    steering_path = ROOT / steering_rel
    steering = _read_json(steering_path)
    epoch = str(inbox.get("schema_version") or "")
    if not epoch or str(steering.get("schema_version") or "") != epoch:
        raise RuntimeError("SUPERVISOR_EPOCH_MISMATCH")
    if steering.get("active_program") != "ENTITYOS_HCU" or steering.get("product") != "EntityOS":
        raise RuntimeError("SUPERVISOR_PRODUCT_MISMATCH")

    admission_path = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
    admission = _read_json(admission_path)
    if admission.get("authority_epoch") != epoch or admission.get("mode") != "FREE_ONLY":
        raise RuntimeError("PROVIDER_ADMISSION_AUTHORITY_MISMATCH")

    source_manifest = _source_manifest((steering_rel, "tools/run_free_swarm_admission_boundary_receipt.py"))
    proc, tests_run = _run_suite()
    combined = proc.stdout + "\n" + proc.stderr
    passed = proc.returncode == 0 and tests_run >= 18 and re.search(r"\bOK\b", combined) is not None

    providers = admission.get("providers") if isinstance(admission.get("providers"), dict) else {}
    provider_state = {
        name: {
            "admitted": bool(record.get("admitted")) if isinstance(record, dict) else False,
            "cost_class": record.get("cost_class") if isinstance(record, dict) else "INVALID",
        }
        for name, record in sorted(providers.items())
    }

    core: dict[str, Any] = {
        "schema": SCHEMA,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "mode": "FREE_ONLY",
        "scope": "EXTERNAL_LLM_PROVIDER_ADMISSION_BOUNDARY_COMPONENT_ONLY",
        "source_identity": {
            "git_head": head,
            "git_tree": tree,
            "branch": branch,
            "clean_tree_before_execution": status == "",
            "source_manifest": source_manifest,
        },
        "authority": {
            "epoch": epoch,
            "supervisor_inbox": "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            "steering": steering_rel,
            "provider_admission": "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
            "provider_admission_sha256": _sha256_bytes(admission_path.read_bytes()),
            "provider_state_observed": provider_state,
        },
        "environment": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "execution": {
            "command": [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-p", TEST_GLOB, "-v"],
            "exit_code": proc.returncode,
            "tests_run": tests_run,
            "stdout_sha256": _sha256_bytes(proc.stdout.encode("utf-8")),
            "stderr_sha256": _sha256_bytes(proc.stderr.encode("utf-8")),
        },
        "tripwire_acceptance": {
            "blocked_cases": list(REQUIRED_BLOCKED_CASES),
            "required_secret_lookup_count_per_blocked_case": 0,
            "required_network_attempt_count_per_blocked_case": 0,
            "proof_method": "PASSING_EXACT_SOURCE_UNIT_ASSERTIONS_WITH_SECRET_AND_NETWORK_TRIPWIRES",
            "tests_required_minimum": 18,
        },
        "result": "PASS" if passed and status == "" else "FAIL",
        "credits": {
            "provider_runtime": 0,
            "whole_entityos_hcu": 0,
            "hcu_full": 0,
            "jspace_model": 0,
            "training": 0,
        },
        "non_promotion": "PASS_DOES_NOT_ADMIT_ANY_PROVIDER_OR_AUTHORIZE_PROVIDER_NETWORK_EXECUTION",
    }
    core["receipt_core_sha256"] = _sha256_bytes(_canonical_bytes(core))
    return core


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source FREE swarm admission boundary receipt")
    parser.add_argument("--output", type=Path, help="optional output JSON path; stdout is always emitted")
    args = parser.parse_args()
    try:
        receipt = build_receipt()
    except Exception as exc:
        failure = {
            "schema": SCHEMA,
            "result": "FAIL",
            "error": f"{exc.__class__.__name__}:{exc}",
            "credits": {"provider_runtime": 0, "whole_entityos_hcu": 0, "hcu_full": 0, "jspace_model": 0, "training": 0},
        }
        text = json.dumps(failure, sort_keys=True, separators=(",", ":"))
        print(text)
        return 2

    text = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if receipt.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
