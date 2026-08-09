#!/usr/bin/env python3
"""Canonical one-command ClayCode BASE14 closure on Andreas' Ubuntu target.

Fail-closed order:
1. verify the owner-registered target fingerprint;
2. run exactly one clean-checkout target component collector;
3. execute the real Ubuntu desktop window/event-loop/input/render proof;
4. prove the full frozen FRANK H1/H2/H3 handoff;
5. execute the hardened ten-application target suite;
6. materialize real per-application receipts, including typed-effect/runtime evidence;
7. assemble the strict Andreas-Ubuntu acceptance receipt;
8. run the independent strict WP14 auditor including mapped-window desktop evidence;
9. promote the release workspace to 14/14 PASS only from the passing WP14 manifest.

No hosted/proxy path can self-promote BASE. The desktop proof is deliberately executed
*after* the pristine collector so generated evidence cannot poison its clean-checkout
attestation, but *before* strict application/WP14 adjudication so GUI acceptance cannot
bypass the real target desktop requirement.
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
COLLECTOR = ROOT / "tools/claycode_base_andreas_target_runner_v2.py"
DESKTOP = ROOT / "tools/claycode_ubuntu_desktop_target_validation_runner.py"
FULL_FRANK = ROOT / "tools/claycode_full_frank_target_finalizer_runner.py"
APPS = ROOT / "tools/claycode_base_target_application_suite_v2_runner.py"
APP_RECEIPTS = ROOT / "tools/claycode_materialize_real_app_receipts.py"
ASSEMBLER = ROOT / "tools/claycode_andreas_ubuntu_acceptance_assembler_runner.py"
WP14 = ROOT / "tools/claycode_base_wp14_strict_audit_v2.py"
PROMOTER = ROOT / "tools/claycode_promote_release_workspace.py"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
DEFAULT_REGISTRATION = Path.home() / ".config/claycode/andreas_target_registration.json"
TARGET_MARKER = Path.home() / ".claycode/ANDREAS_TARGET_HOST"
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
        "schema_version": "1.3",
        "target_host": TARGET,
        "overall_pass": overall_pass,
        "steps": steps,
        "required_step_ids": [
            "CLEAN_TARGET_COMPONENT_COLLECTOR",
            "REAL_UBUNTU_DESKTOP_GUI",
            "FULL_FRANK_H1_H2_H3",
            "HARDENED_TEN_APPLICATION_SUITE",
            "REAL_PER_APPLICATION_RECEIPTS",
            "STRICT_TARGET_ACCEPTANCE_ASSEMBLY",
            "WP14_STRICT_INDEPENDENT_AUDIT",
            "RELEASE_WORKSPACE_PROMOTION",
        ],
        "authority_invariant": "model output != execution authority",
        "promotion_rule": "workspace promotion occurs only after desktop-aware strict WP14 PASS",
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

    TARGET_MARKER.parent.mkdir(parents=True, exist_ok=True)
    TARGET_MARKER.write_text(TARGET + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["CLAYCODE_TARGET_HOST_ID"] = TARGET
    steps: list[dict] = []

    sequence = [
        ("CLEAN_TARGET_COMPONENT_COLLECTOR", [sys.executable, str(COLLECTOR), "--marker", str(TARGET_MARKER)]),
        ("REAL_UBUNTU_DESKTOP_GUI", [sys.executable, str(DESKTOP), "--registration", str(args.registration)]),
        ("FULL_FRANK_H1_H2_H3", [sys.executable, str(FULL_FRANK), "--registration", str(args.registration)]),
        ("HARDENED_TEN_APPLICATION_SUITE", [sys.executable, str(APPS), "--registration", str(args.registration)]),
        ("REAL_PER_APPLICATION_RECEIPTS", [sys.executable, str(APP_RECEIPTS), "--registration", str(args.registration)]),
        ("STRICT_TARGET_ACCEPTANCE_ASSEMBLY", [sys.executable, str(ASSEMBLER), "--registration", str(args.registration)]),
        ("WP14_STRICT_INDEPENDENT_AUDIT", [sys.executable, str(WP14)]),
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
        "desktop_gui": "PASS",
        "workspace": "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
        "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json",
        "strict_target_receipt": "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json",
        "run_receipt": str(RUN_RECEIPT.relative_to(ROOT)),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
