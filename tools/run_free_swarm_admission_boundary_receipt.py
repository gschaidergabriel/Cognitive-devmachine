#!/usr/bin/env python3
"""Emit an exact-source FREE Swarm admission-boundary execution receipt.

Executes the canonical admission-boundary unittest modules in a sanitized child
process. Provider credentials are not inherited. A Python socket tripwire blocks
and records any unmocked Python DNS or connection attempt. The canonical tests
retain their own per-case secret/network tripwire assertions.

The suite also binds malformed canonical admission, caller-forged FREE payloads,
and the shared ``rae_secret_loader`` primitive so direct/legacy callers cannot
inspect provider environment variables or repository secret stores before
canonical typed FREE admission.

Component evidence only: this runner does not admit or call any external provider
and cannot establish whole EntityOS/HCU, HCU, J-Space-model, or training credit.
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
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HARDENING_TEST_MODULE = "tests.test_free_swarm_receipt_runner_hardening_868"
HARDENING_TEST_PATH = ROOT / "tests/test_free_swarm_receipt_runner_hardening_868.py"
TEST_MODULES = (
    "tests.test_free_swarm_admission_boundary_867",
    "tests.test_free_swarm_admission_boundary_868_malformed",
    "tests.test_free_provider_admission_forgery_868",
    "tests.test_free_swarm_socket_tripwire_868",
    "tests.test_rae_secret_loader_provider_admission",
    HARDENING_TEST_MODULE,
)
TEST_PATHS = (
    ROOT / "tests/test_free_swarm_admission_boundary_867.py",
    ROOT / "tests/test_free_swarm_admission_boundary_868_malformed.py",
    ROOT / "tests/test_free_provider_admission_forgery_868.py",
    ROOT / "tests/test_free_swarm_socket_tripwire_868.py",
    ROOT / "tests/test_rae_secret_loader_provider_admission.py",
    HARDENING_TEST_PATH,
)
INBOX_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"

SOURCE_PATHS = (
    "tests/test_free_swarm_admission_boundary_867.py",
    "tests/test_free_swarm_admission_boundary_868_malformed.py",
    "tests/test_free_provider_admission_forgery_868.py",
    "tests/test_free_swarm_socket_tripwire_868.py",
    "tests/test_rae_secret_loader_provider_admission.py",
    "tests/test_free_swarm_receipt_runner_hardening_868.py",
    "tools/free_provider_admission.py",
    "tools/rae_secret_loader.py",
    "tools/run_free_go_swarm.py",
    "tools/run_24h_entityos_swarm.py",
    "tools/run_research_distillery_entry.py",
    "tools/run_24h_entityos_swarm_supervisor.sh",
    "tools/run_free_swarm_admission_boundary_receipt.py",
    "tools/run_free_swarm_admission_boundary_receipt_hardened_868.py",
    "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)

PROVIDER_SECRET_NAMES = (
    "GROQ_API_KEY", "GROQ_API_KEYS", "GROQ2_API_KEY", "GROQ3_API_KEY",
    "MISTRAL_API_KEY", "MISTRAL_API_KEYS", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY",
    "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_NIM_API_KEY", "NGC_API_KEY",
    "NVIDIA2_API_KEY", "NVIDIA3_API_KEY", "OPENROUTER_API_KEY",
)
SENTINEL = "CLAY_BOUNDARY_SENTINEL_NOT_A_REAL_SECRET"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


def _working_tree_dirty() -> bool:
    """Include untracked files because they can shadow imports on PYTHONPATH."""
    return bool(_git("status", "--porcelain", "--untracked-files=all"))


def _authority_snapshot() -> dict[str, Any]:
    inbox = _read_json(INBOX_PATH)
    steering_ref = str(inbox.get("steering") or "").strip()
    if not steering_ref:
        raise RuntimeError("SUPERVISOR_STEERING_REF_REQUIRED")
    steering = _read_json(ROOT / steering_ref)
    admission = _read_json(ADMISSION_PATH)
    inbox_epoch = str(inbox.get("schema_version") or "").strip()
    steering_epoch = str(steering.get("schema_version") or "").strip()
    admission_epoch = str(admission.get("authority_epoch") or "").strip()
    if not inbox_epoch or inbox_epoch != steering_epoch or inbox_epoch != admission_epoch:
        raise RuntimeError(
            f"AUTHORITY_EPOCH_MISMATCH:inbox={inbox_epoch}:steering={steering_epoch}:admission={admission_epoch}"
        )
    if steering.get("active_program") != "ENTITYOS_HCU":
        raise RuntimeError("ENTITYOS_HCU_SUPERVISOR_REQUIRED")
    if admission.get("mode") != "FREE_ONLY":
        raise RuntimeError("FREE_ONLY_REQUIRED")
    return {
        "epoch": inbox_epoch,
        "steering": steering_ref,
        "admission_schema": admission.get("schema"),
        "admission_mode": admission.get("mode"),
        "providers": {
            name: {
                "admitted": bool(record.get("admitted")),
                "cost_class": record.get("cost_class"),
            }
            for name, record in sorted((admission.get("providers") or {}).items())
            if isinstance(record, dict)
        },
    }


def _source_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in SOURCE_PATHS:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"SOURCE_REQUIRED:{rel}")
        rows.append({"path": rel, "sha256": _sha256_file(path), "bytes": path.stat().st_size})
    steering_ref = _authority_snapshot()["steering"]
    steering_path = ROOT / steering_ref
    rows.append({"path": steering_ref, "sha256": _sha256_file(steering_path), "bytes": steering_path.stat().st_size})
    return rows


def _manifest_digest(rows: list[dict[str, Any]]) -> str:
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(canonical)


def _bootstrap_text() -> str:
    return r'''import json
import os
from pathlib import Path
import socket
import sys
import unittest

log_path = Path(os.environ["CLAY_NETWORK_TRIPWIRE_LOG"])

def record(kind, target):
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": kind, "target": repr(target)}, separators=(",", ":")) + "\n")
    finally:
        raise RuntimeError("CLAY_BOUNDARY_NETWORK_TRIPWIRE")

def guarded_connect(self, address):
    return record("socket.connect", address)

def guarded_connect_ex(self, address):
    return record("socket.connect_ex", address)

def guarded_create_connection(address, *args, **kwargs):
    return record("socket.create_connection", address)

def guarded_getaddrinfo(host, port, *args, **kwargs):
    return record("socket.getaddrinfo", (host, port))

socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
socket.create_connection = guarded_create_connection
socket.getaddrinfo = guarded_getaddrinfo
suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def _safe_child_env(temp_home: Path, network_log: Path) -> dict[str, str]:
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(temp_home),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "CLAY_NETWORK_TRIPWIRE_LOG": str(network_log),
    }
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "tools")))
    for name in PROVIDER_SECRET_NAMES:
        env[name] = SENTINEL
    return env


def _network_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            value = {"raw": line}
        rows.append(value if isinstance(value, dict) else {"value": value})
    return rows


def _write_receipt(path: Path | None, receipt: dict[str, Any]) -> None:
    text = json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run exact-source FREE Swarm admission boundary and emit receipt")
    parser.add_argument("--output", type=Path, default=None, help="optional receipt JSON path; default stdout")
    parser.add_argument("--allow-dirty", action="store_true", help="diagnostic only; dirty execution is non-promotable")
    args = parser.parse_args(argv)

    head = _git("rev-parse", "HEAD")
    dirty = _working_tree_dirty()
    if dirty and not args.allow_dirty:
        raise SystemExit("REFUSING_DIRTY_TREE: rerun from an exact clean checkout")

    authority = _authority_snapshot()
    source_manifest = _source_manifest()
    source_manifest_sha256 = _manifest_digest(source_manifest)
    started = dt.datetime.now(dt.timezone.utc)

    with tempfile.TemporaryDirectory(prefix="clay-free-admission-") as td:
        temp = Path(td)
        bootstrap = temp / "boundary_bootstrap.py"
        network_log = temp / "network_tripwire.jsonl"
        bootstrap.write_text(_bootstrap_text(), encoding="utf-8")
        env = _safe_child_env(temp, network_log)
        command = [sys.executable, str(bootstrap), *TEST_MODULES]
        proc = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        attempts = _network_attempts(network_log)

    # Rebind exact source after execution. A concurrent checkout update, authority
    # change, tracked mutation, or untracked import shadow makes the receipt
    # non-promotable even if the child tests themselves were green.
    head_after = _git("rev-parse", "HEAD")
    dirty_after = _working_tree_dirty()
    source_manifest_after = _source_manifest()
    source_manifest_sha256_after = _manifest_digest(source_manifest_after)
    source_stable_during_execution = bool(
        head_after == head
        and not dirty_after
        and source_manifest_sha256_after == source_manifest_sha256
    )

    finished = dt.datetime.now(dt.timezone.utc)
    combined = proc.stdout + "\n" + proc.stderr
    match = re.search(r"Ran\s+(\d+)\s+tests?", combined)
    test_count = int(match.group(1)) if match else None
    unittest_ok = proc.returncode == 0 and re.search(r"(?:^|\n)OK(?:\s|\n|$)", combined) is not None
    sentinel_leaked = SENTINEL in combined
    pass_boundary = bool(
        unittest_ok
        and not attempts
        and not sentinel_leaked
        and not dirty
        and source_stable_during_execution
    )

    receipt = {
        "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "created_at": finished.isoformat(),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "mode": "FREE_ONLY",
        "authority": authority,
        "source": {
            "repository": "gschaidergabriel/clay-global-research-entity",
            "git_head": head,
            "git_head_after_execution": head_after,
            "clean_tracked_tree": not dirty,
            "clean_tree_after_execution": not dirty_after,
            "untracked_files_included_in_cleanliness_gate": True,
            "manifest": source_manifest,
            "manifest_sha256": source_manifest_sha256,
            "manifest_sha256_after_execution": source_manifest_sha256_after,
            "source_stable_during_execution": source_stable_during_execution,
            "test_modules": list(TEST_MODULES),
            "test_sha256": {path.relative_to(ROOT).as_posix(): _sha256_file(path) for path in TEST_PATHS},
        },
        "execution": {
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "duration_seconds": round((finished - started).total_seconds(), 6),
            "python": sys.version.split()[0],
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "command": [sys.executable, "<temp>/boundary_bootstrap.py", *TEST_MODULES],
            "bootstrap_sha256": _sha256_bytes(_bootstrap_text().encode("utf-8")),
            "exit_code": proc.returncode,
            "tests_reported": test_count,
            "stdout_sha256": _sha256_bytes(proc.stdout.encode("utf-8")),
            "stderr_sha256": _sha256_bytes(proc.stderr.encode("utf-8")),
        },
        "fences": {
            "real_provider_secrets_inherited": False,
            "provider_secret_sentinels_used": True,
            "secret_sentinel_leaked_to_output": sentinel_leaked,
            "python_socket_network_attempt_count": len(attempts),
            "python_socket_network_attempts": attempts,
            "python_socket_tripwire_covers": [
                "socket.getaddrinfo",
                "socket.create_connection",
                "socket.socket.connect",
                "socket.socket.connect_ex",
            ],
            "per_case_secret_and_network_zero_assertions": "ENFORCED_BY_CANONICAL_TEST_SUITE",
            "malformed_admission_zero_assertions": "ENFORCED_BY_TEST_FREE_SWARM_ADMISSION_BOUNDARY_868_MALFORMED",
            "caller_forgery_non_authority_assertions": "ENFORCED_BY_TEST_FREE_PROVIDER_ADMISSION_FORGERY_868",
            "shared_secret_loader_pretouch_assertions": "ENFORCED_BY_TEST_RAE_SECRET_LOADER_PROVIDER_ADMISSION",
            "source_toc_tou_guard": "HEAD_CLEAN_TREE_AND_MANIFEST_MUST_MATCH_BEFORE_AND_AFTER_EXECUTION",
            "canonical_runner_self_binding": "BASE_WRAPPER_AND_HARDENING_TEST_ARE_IN_SOURCE_MANIFEST_AND_TEST_SET",
        },
        "result": {
            "unittest_ok": unittest_ok,
            "boundary_pass": pass_boundary,
            "scope": "FREE_SWARM_PROVIDER_ADMISSION_BOUNDARY_COMPONENT_ONLY",
            "external_provider_runtime_credit": 0,
            "whole_entityos_hcu_runtime_credit": 0,
            "hcu_full_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
        },
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    _write_receipt(args.output, receipt)
    return 0 if pass_boundary else 1


if __name__ == "__main__":
    raise SystemExit(main())
