#!/usr/bin/env python3
"""Executable exact-source FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 harness.

This harness performs only local deterministic control-boundary tests. It does not
read real provider credentials and does not open provider network connections.
Canonical credit remains component-only until the receipt is run on an authorized
exact-source local or clay-direct-dev surface and admitted by current project rules.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_TEST_FILE = ROOT / "tests/test_free_swarm_admission_boundary_867.py"
UNIT_PATTERN = "test_free_swarm_admission_boundary_*.py"

SOURCE_PATHS = (
    "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
    "tools/free_provider_admission.py",
    "tools/run_free_go_swarm.py",
    "tools/run_24h_entityos_swarm.py",
    "tools/run_research_distillery_entry.py",
    "tools/run_24h_entityos_swarm_supervisor.sh",
    "tests/test_free_swarm_admission_boundary_867.py",
    "tests/test_free_swarm_admission_boundary_868_malformed.py",
    "tools/free_swarm_admission_boundary_receipt_v1.py",
)

NEGATIVE_COST_CLASSES = ("UNKNOWN", "PAID", "SUBSCRIPTION")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(argv: list[str], timeout: float = 90.0) -> dict[str, Any]:
    proc = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
    }


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0:
        return "UNAVAILABLE"
    return proc.stdout.strip()


def _load_test_module():
    spec = importlib.util.spec_from_file_location("clay_free_boundary_tests", PRIMARY_TEST_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("boundary_test_module_unloadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _structured_tripwire_matrix() -> list[dict[str, Any]]:
    """Re-use the production-path test helper and retain observed counters."""
    t = _load_test_module()
    case_runner = t.FreeProviderAdmissionBoundaryTests(
        methodName="test_global_attestation_missing_has_zero_secret_and_network_access"
    )
    rows: list[dict[str, Any]] = []

    def record(
        name: str,
        admission_path: Path,
        root: Path,
        inbox: Path,
        *,
        global_attested: bool,
        expected_nonzero: bool = True,
    ) -> None:
        code, secret_reads, network_attempts = case_runner._run_with_tripwires(
            admission_path,
            root,
            inbox,
            global_attested=global_attested,
        )
        passed = (
            (code != 0 if expected_nonzero else code == 0)
            and secret_reads == 0
            and network_attempts == 0
        )
        rows.append(
            {
                "case": name,
                "exit_code": code,
                "secret_lookup_count": secret_reads,
                "network_attempt_count": network_attempts,
                "pass": passed,
            }
        )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inbox = t._authority(root)
        adm = t._admission(root, "FREE", True)
        record(
            "GLOBAL_ATTESTATION_MISSING",
            adm,
            root,
            inbox,
            global_attested=False,
        )

    for cost_class in NEGATIVE_COST_CLASSES:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inbox = t._authority(root)
            adm = t._admission(root, cost_class, False)
            record(
                f"PROVIDER_COST_{cost_class}",
                adm,
                root,
                inbox,
                global_attested=True,
            )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inbox = t._authority(root)
        # Production resolves the canonical repository-relative path. Deliberately
        # leave that path absent; the compatibility argument is non-authoritative.
        record(
            "ADMISSION_FILE_MISSING",
            root / "compatibility-nonauthority-missing.json",
            root,
            inbox,
            global_attested=True,
        )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inbox = t._authority(root)
        # Write malformed JSON at the exact path production resolves. This avoids
        # the historical root/admission.json fixture drift repaired on 8.68 main.
        malformed = t._canonical_admission_path(root)
        malformed.write_text("{not-json", encoding="utf-8")
        record(
            "ADMISSION_MALFORMED_CANONICAL_PATH",
            malformed,
            root,
            inbox,
            global_attested=True,
        )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inbox = t._authority(root, epoch="8.68")
        stale = t._admission(root, "FREE", True, epoch="8.67")
        record(
            "AUTHORITY_EPOCH_MISMATCH",
            stale,
            root,
            inbox,
            global_attested=True,
        )

    # Direct control-plane checks for providers that cannot be selected through the
    # base swarm provider tuple. The admission functions themselves do not read
    # provider secrets or perform provider network I/O.
    direct_secret_reads = 0
    direct_network_attempts = 0

    def secret_tripwire(name: str, default=None):
        nonlocal direct_secret_reads
        direct_secret_reads += 1
        raise AssertionError(f"secret lookup in direct admission check:{name}")

    def network_tripwire(*_args, **_kwargs):
        nonlocal direct_network_attempts
        direct_network_attempts += 1
        raise AssertionError("network attempt in direct admission check")

    with mock.patch.object(
        t.admission_mod.os if hasattr(t.admission_mod, "os") else os,
        "getenv",
        side_effect=secret_tripwire,
        create=True,
    ), mock.patch.object(t.base.urllib.request, "urlopen", side_effect=network_tripwire):
        unlisted_allowed = t.admission_mod.provider_is_admitted_free("unlisted-provider")
        openrouter_allowed = t.admission_mod.provider_is_admitted_free("openrouter")

    rows.append(
        {
            "case": "UNLISTED_PROVIDER",
            "observed_allowed": bool(unlisted_allowed),
            "secret_lookup_count": direct_secret_reads,
            "network_attempt_count": direct_network_attempts,
            "pass": (
                unlisted_allowed is False
                and direct_secret_reads == 0
                and direct_network_attempts == 0
            ),
        }
    )
    rows.append(
        {
            "case": "OPENROUTER_CURRENT_CANONICAL_BLOCK",
            "observed_allowed": bool(openrouter_allowed),
            "secret_lookup_count": direct_secret_reads,
            "network_attempt_count": direct_network_attempts,
            "pass": (
                openrouter_allowed is False
                and direct_secret_reads == 0
                and direct_network_attempts == 0
            ),
        }
    )
    return rows


def main() -> int:
    source_hashes: dict[str, str] = {}
    missing_sources: list[str] = []
    for rel in SOURCE_PATHS:
        path = ROOT / rel
        if not path.is_file():
            missing_sources.append(rel)
            continue
        source_hashes[rel] = _sha256_file(path)

    git_head = _git("rev-parse", "HEAD")
    git_tree = _git("rev-parse", "HEAD^{tree}")
    git_status = _git("status", "--porcelain=v1")

    unit = _run(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            UNIT_PATTERN,
            "-v",
        ]
    )
    syntax = _run(["bash", "-n", str(ROOT / "tools/run_24h_entityos_swarm_supervisor.sh")])

    python_compile_errors: list[str] = []
    for rel in (
        "tools/free_provider_admission.py",
        "tools/run_free_go_swarm.py",
        "tools/run_24h_entityos_swarm.py",
        "tools/run_research_distillery_entry.py",
        "tests/test_free_swarm_admission_boundary_867.py",
        "tests/test_free_swarm_admission_boundary_868_malformed.py",
    ):
        path = ROOT / rel
        try:
            compile(path.read_text(encoding="utf-8"), rel, "exec")
        except Exception as exc:
            python_compile_errors.append(f"{rel}:{type(exc).__name__}:{exc}")

    admission_snapshot = _run(
        [sys.executable, "-B", str(ROOT / "tools/free_provider_admission.py"), "--json"]
    )

    tripwire_error = None
    try:
        tripwire_rows = _structured_tripwire_matrix()
    except Exception as exc:
        tripwire_rows = []
        tripwire_error = f"{type(exc).__name__}:{exc}"

    combined_test_text = unit["stdout"] + "\n" + unit["stderr"]
    match = re.search(r"Ran\s+(\d+)\s+tests?", combined_test_text)
    test_count = int(match.group(1)) if match else None

    admission_payload: dict[str, Any] | None = None
    if admission_snapshot["exit_code"] == 0:
        try:
            admission_payload = json.loads(admission_snapshot["stdout"])
        except json.JSONDecodeError:
            admission_payload = None

    all_tripwires_pass = bool(tripwire_rows) and all(
        row.get("pass") is True for row in tripwire_rows
    )
    status = "PASS"
    reasons: list[str] = []
    checks = {
        "source_manifest_complete": not missing_sources,
        "git_head_observed": git_head != "UNAVAILABLE",
        "git_tree_observed": git_tree != "UNAVAILABLE",
        "git_tree_clean": git_status == "",
        "unit_boundary_suite_pass": (
            unit["exit_code"] == 0 and test_count is not None and test_count >= 13
        ),
        "shell_syntax_pass": syntax["exit_code"] == 0,
        "python_compile_pass": not python_compile_errors,
        "canonical_admission_snapshot_pass": (
            admission_payload is not None
            and admission_payload.get("ok") is True
            and "openrouter" in admission_payload.get("providers", {})
        ),
        "structured_tripwire_matrix_pass": (
            all_tripwires_pass and tripwire_error is None
        ),
    }
    for name, passed in checks.items():
        if not passed:
            status = "FAIL"
            reasons.append(name)

    receipt = {
        "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "status": status,
        "failure_reasons": reasons,
        "exact_source": {
            "git_head": git_head,
            "git_tree": git_tree,
            "git_status_porcelain": git_status,
            "source_sha256": source_hashes,
            "missing_sources": missing_sources,
        },
        "environment": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
        },
        "authority_snapshot": admission_payload,
        "checks": checks,
        "unit_suite": {
            "pattern": UNIT_PATTERN,
            "test_count": test_count,
            "exit_code": unit["exit_code"],
            "stdout_sha256": unit["stdout_sha256"],
            "stderr_sha256": unit["stderr_sha256"],
        },
        "structured_tripwire_matrix": tripwire_rows,
        "structured_tripwire_error": tripwire_error,
        "syntax_check": {
            "exit_code": syntax["exit_code"],
            "stdout_sha256": syntax["stdout_sha256"],
            "stderr_sha256": syntax["stderr_sha256"],
        },
        "python_compile_errors": python_compile_errors,
        "real_provider_credentials_read": 0,
        "real_provider_network_attempts": 0,
        "external_provider_execution_performed": False,
        "provider_runtime_credit": 0,
        "whole_entityos_hcu_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
        "scope": "FREE_ONLY_PROVIDER_ADMISSION_BOUNDARY_COMPONENT_ONLY",
        "evidence_note": (
            "PASS is executable component evidence at the exact reported source/environment only; "
            "it does not classify any real provider as FREE and does not authorize provider traffic."
        ),
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
