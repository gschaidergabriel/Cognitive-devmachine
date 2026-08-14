#!/usr/bin/env python3
"""Fail-closed ClayCode BASE preflight for the Andreas Ubuntu developer target.

This script deliberately does NOT turn proxy gates into release acceptance. It executes
all currently available compiler/runtime/conformance gates on the actual host, records
host identity and exposes which BASE requirements still lack target-grade receipts.

Target attestation must be explicitly supplied by the operator:
  CLAYCODE_TARGET_HOST_ATTEST=ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM \
    python tools/claycode_andreas_ubuntu_target_preflight.py
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_PREFLIGHT.json"
ATTEST = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"

GATES = [
    ("WP02_V7_FRONTEND_IDENTITY", "tools/claycode_v7_frontend_identity_regression.py"),
    ("WP03_06_PURE_COMPILER", "tools/claycode_base_compiler_validation.py"),
    ("WP04_EFFECT_AUTHORITY", "tools/claycode_base_effect_pipeline.py"),
    ("WP07_09_RUNTIME", "tools/claycode_base_runtime_validation.py"),
    ("WP10_TEN_APP_PROXY_V2", "tools/claycode_base_application_proxy_suite_v2.py"),
    ("WP11_FUZZ_CONFORMANCE", "tools/claycode_wp11_fuzz_conformance.py"),
    ("WP11_12_CORPUS", "tools/claycode_wp11_wp12_conformance_corpus.py"),
]


def sha(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def os_release() -> dict:
    path = Path("/etc/os-release")
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                out[k] = v.strip().strip('"')
    return out


def run_gate(name: str, relative: str) -> dict:
    path = ROOT / relative
    row = {"name": name, "path": relative, "sha256": sha(path), "exists": path.is_file()}
    if not path.is_file():
        row.update({"pass": False, "returncode": None, "error": "MISSING_GATE"})
        return row
    cp = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True, timeout=180
    )
    row.update(
        {
            "pass": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-4000:],
            "stderr_tail": cp.stderr[-4000:],
        }
    )
    return row


def main() -> int:
    osr = os_release()
    attested = os.environ.get("CLAYCODE_TARGET_HOST_ATTEST") == ATTEST
    ubuntu = osr.get("ID", "").lower() == "ubuntu"
    gcc = shutil.which("gcc") or shutil.which("cc")
    git = shutil.which("git")
    host_preconditions = {
        "explicit_operator_attestation": attested,
        "ubuntu_os_release": ubuntu,
        "python_available": bool(sys.executable),
        "native_c_compiler_available": bool(gcc),
        "git_available": bool(git),
    }
    gates = [run_gate(name, path) for name, path in GATES]
    technical_preflight_pass = all(host_preconditions.values()) and all(x["pass"] for x in gates)

    # These cannot be manufactured from the existing proxy suite. The target run must
    # replace them with release-grade receipts before WP10/WP13/WP14 can close.
    remaining_target_receipts = [
        "WP02 production parser/canonicalizer receipt bound to exact frozen sources",
        "WP03 production typed-IR identity receipt",
        "WP04 production type/effect diagnostic + authority-closure receipt",
        "WP05 full frozen-core evaluator receipt",
        "WP06 release lowering/native translation-validation receipt",
        "WP07 typed runtime ABI/FFI/resource-identity receipt",
        "WP08 target stdlib/SDK API+ABI receipt",
        "WP09 concurrency/memory/replay receipt",
        "WP10 ten release-grade application receipts (proxy labels are insufficient)",
        "WP11 target-linked full compiler/runtime/application conformance receipt",
        "WP12 frozen full-semantics held-out/leak audit receipt",
        "WP13 frozen H1 FRANK subsystem -> ClayCode H2 differential receipt",
        "WP14 general-purpose compiler manifest + final audit decision",
    ]

    receipt = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "ANDREAS_UBUNTU_TARGET_PREFLIGHT_NOT_RELEASE_PASS",
        "target_attestation_expected": ATTEST,
        "target_attestation_observed": os.environ.get("CLAYCODE_TARGET_HOST_ATTEST"),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
            "os_release": osr,
            "gcc_or_cc": gcc,
            "git": git,
        },
        "host_preconditions": host_preconditions,
        "gates": gates,
        "technical_preflight_pass": technical_preflight_pass,
        "counts_as_target_release_pass": False,
        "remaining_target_receipts": remaining_target_receipts,
        "fail_closed_rule": "A green preflight never promotes WP10/WP13/WP14 or GENERAL_PURPOSE_GATE. Promotion requires the package-specific target receipts and release manifest.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"technical_preflight_pass": technical_preflight_pass, "receipt": str(OUT.relative_to(ROOT)), "remaining_target_receipts": len(remaining_target_receipts)}))
    return 0 if technical_preflight_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
