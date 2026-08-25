#!/usr/bin/env python3
"""Portable repository-bound GO acceptance runner.

Purpose: bypass a broken CI runner class without weakening evidence binding. This runner
executes the exact canonical S0 CAS component and the integrated Xeno self-organizing fabric
harness from the current checkout, binds HEAD/tree/source hashes/runtime, and emits one
machine-readable receipt.

It does not mint whole EntityOS/HCU/GRID10 credit. It only reports component execution facts.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
S0 = ROOT / "tools/zero_entityos_restart_resize_db_smoke_v1.py"
FABRIC = ROOT / "tools/xeno_self_organizing_fabric_acceptance_v1.py"
OUT = ROOT / "artifacts/go-repository-bound-acceptance"


def sh(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_json(path: Path) -> dict[str, Any]:
    p = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        return {
            "ok": False,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
        }
    try:
        payload = json.loads(p.stdout)
    except Exception as exc:
        return {
            "ok": False,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "parse_error": repr(exc),
        }
    return {"ok": True, "returncode": 0, "payload": payload, "stdout": p.stdout, "stderr": p.stderr}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    required = [S0, FABRIC]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("missing required source: " + ",".join(missing))

    head = sh("git", "rev-parse", "HEAD")
    tree = sh("git", "rev-parse", "HEAD^{tree}")
    dirty = bool(sh("git", "status", "--porcelain"))

    s0 = run_json(S0)
    fabric = run_json(FABRIC)

    s0_checks = s0.get("payload", {}).get("checks", {}) if s0.get("ok") else {}
    s0_required = [
        "DB_PROPOSAL_BINDS_EXPECTED_S0_EPOCH",
        "SAME_GENERATION_STALE_S0_EPOCH_WRITE_REJECTED",
        "FRESH_S0_EPOCH_REBASE_SUCCEEDS",
        "S0_ENGINE_LEVEL_READONLY_FROM_COGNITION",
    ]
    s0_pass = bool(s0.get("ok") and all(s0_checks.get(k) is True for k in s0_required))

    # Fabric harness owns its own detailed check set; this portable runner requires a clean
    # process exit plus a JSON payload whose top-level status/result does not declare failure.
    fp = fabric.get("payload", {}) if fabric.get("ok") else {}
    fabric_status = fp.get("status", fp.get("result", fp.get("verdict", "PASS" if fabric.get("ok") else "FAIL")))
    fabric_pass = bool(fabric.get("ok") and str(fabric_status).upper() not in {"FAIL", "FAILED", "ERROR", "BLOCKED"})

    receipt = {
        "schema": "GO_REPOSITORY_BOUND_ACCEPTANCE_BUNDLE/v1",
        "repository": "gschaidergabriel/clay-global-research-entity",
        "head": head,
        "tree": tree,
        "dirty": dirty,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "sources": {
            str(S0.relative_to(ROOT)): sha256(S0),
            str(FABRIC.relative_to(ROOT)): sha256(FABRIC),
            str(Path(__file__).resolve().relative_to(ROOT)): sha256(Path(__file__).resolve()),
        },
        "canonical_s0": {
            "executed": True,
            "pass": s0_pass,
            "required_checks": s0_required,
            "result": s0,
        },
        "xeno_self_organizing_fabric": {
            "executed": True,
            "pass": fabric_pass,
            "result": fabric,
        },
        "bundle_pass": bool(s0_pass and fabric_pass and not dirty),
        "evidence_boundary": {
            "repository_bound_component_execution": True,
            "physical_grid10_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "training_credit": 0,
        },
        "environment": {
            "CI": os.environ.get("CI"),
            "GITHUB_ACTIONS": os.environ.get("GITHUB_ACTIONS"),
        },
    }

    out = OUT / "receipt.json"
    out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["bundle_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
