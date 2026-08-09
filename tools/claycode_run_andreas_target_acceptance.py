#!/usr/bin/env python3
"""Canonical one-command ClayCode BASE14 closure on Andreas' Ubuntu target.

Fail-closed order:
1. verify the owner-registered target fingerprint;
2. run the clean-checkout target component gate before generating any evidence;
3. prove the full frozen FRANK H1/H2/H3 handoff;
4. execute the hardened ten-application target suite;
5. materialize real per-application receipts, including typed-effect/runtime evidence;
6. assemble the canonical Andreas-Ubuntu acceptance receipt;
7. run the independent WP14 auditor;
8. promote the release workspace to 14/14 PASS only from the passing WP14 manifest.

No hosted/proxy path can self-promote BASE. The command may create evidence/workspace
files locally; persistence to GitHub remains an explicit repository operation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "tools/claycode_target_host_identity.py"
GATE = ROOT / "tools/claycode_andreas_ubuntu_target_gate.py"
FULL_FRANK = ROOT / "tools/claycode_full_frank_target_finalizer_runner.py"
APPS = ROOT / "tools/claycode_base_target_application_suite_v2_runner.py"
APP_RECEIPTS = ROOT / "tools/claycode_materialize_real_app_receipts.py"
ASSEMBLER = ROOT / "tools/claycode_andreas_ubuntu_acceptance_assembler.py"
WP14 = ROOT / "tools/claycode_base_wp14_audit.py"
PROMOTER = ROOT / "tools/claycode_promote_release_workspace.py"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
DEFAULT_REGISTRATION = Path.home() / ".config/claycode/andreas_target_registration.json"
RUN_RECEIPT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_BASE14_CLOSURE_RUN.json"


def execute(step_id: str, argv: list[str], env: dict[str, str]) -> dict:
    cp = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    row = {
        "step_id": step_id,
        "argv": argv,
        "returncode": cp.returncode,
        "pass": cp.returncode == 0,
        "stdout_tail": cp.stdout[-8000:],
        "stderr_tail": cp.stderr[-8000:],
    }
    print(json.dumps({"step_id": step_id, "pass": row["pass"], "returncode": cp.returncode}, ensure_ascii=False))
    return row


def write_run_receipt(steps: list[dict], overall_pass: bool) -> None:
    payload = {
        "schema_version": "1.0",
        "target_host": TARGET,
        "overall_pass": overall_pass,
        "steps": steps,
        "authority_invariant": "model output != execution authority",
        "promotion_rule": "workspace promotion occurs only after independent WP14 PASS",
    }
    RUN_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RUN_RECEIPT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    verify = subprocess.run(
        [sys.executable, str(IDENTITY), "verify", "--registration", str(args.registration), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if verify.returncode != 0:
        print(json.dumps({
            "error": "ANDREAS_TARGET_IDENTITY_NOT_VERIFIED",
            "registration": str(args.registration),
            "identity_stdout": verify.stdout[-4000:],
            "identity_stderr": verify.stderr[-4000:],
            "next_required": (
                "Run the explicit owner registration once on the actual target host: "
                f"python tools/claycode_target_host_identity.py register --acknowledge {TARGET}"
            ),
        }, ensure_ascii=False, indent=2))
        return 3

    env = dict(os.environ)
    env["CLAYCODE_TARGET_HOST_ID"] = TARGET
    steps: list[dict] = []

    sequence = [
        ("CLEAN_TARGET_COMPONENT_GATE", [sys.executable, str(GATE)]),
        ("FULL_FRANK_H1_H2_H3", [sys.executable, str(FULL_FRANK), "--registration", str(args.registration)]),
        ("HARDENED_TEN_APPLICATION_SUITE", [sys.executable, str(APPS), "--registration", str(args.registration)]),
        ("REAL_PER_APPLICATION_RECEIPTS", [sys.executable, str(APP_RECEIPTS), "--registration", str(args.registration)]),
        ("STRICT_TARGET_ACCEPTANCE_ASSEMBLY", [sys.executable, str(ASSEMBLER)]),
        ("WP14_INDEPENDENT_AUDIT", [sys.executable, str(WP14)]),
        ("RELEASE_WORKSPACE_PROMOTION", [sys.executable, str(PROMOTER)]),
    ]

    for step_id, argv in sequence:
        row = execute(step_id, argv, env)
        steps.append(row)
        if not row["pass"]:
            write_run_receipt(steps, False)
            return int(row["returncode"] or 2)

    write_run_receipt(steps, True)
    print(json.dumps({
        "pass": True,
        "target_host": TARGET,
        "work_packages": "14/14",
        "applications": "10/10",
        "workspace": "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
        "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json",
        "run_receipt": str(RUN_RECEIPT.relative_to(ROOT)),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
