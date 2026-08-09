#!/usr/bin/env python3
"""Canonical entry point for ClayCode BASE execution on Andreas' Ubuntu target.

Order is fail-closed:
1. verify the owner-registered target fingerprint;
2. prove the full frozen FRANK H1/H2/H3 handoff and materialize target-only receipts;
3. execute the hardened ten-application suite;
4. execute the full ClayCode convergence gate.

No hosted/proxy path can self-promote BASE.
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
FULL_FRANK = ROOT / "tools/claycode_full_frank_target_finalizer_runner.py"
APPS = ROOT / "tools/claycode_base_target_application_suite_v2_runner.py"
GATE = ROOT / "tools/claycode_andreas_ubuntu_target_gate.py"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
DEFAULT_REGISTRATION = Path.home() / ".config/claycode/andreas_target_registration.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    ap.add_argument("--output", type=Path)
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

    full_frank = subprocess.run(
        [sys.executable, str(FULL_FRANK), "--registration", str(args.registration)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if full_frank.returncode != 0:
        # Do not allow the ten-app suite to reinterpret a missing/failed FULL_FRANK
        # receipt as a partial success. Component receipts already preserve the failure.
        return full_frank.returncode

    apps = subprocess.run(
        [sys.executable, str(APPS), "--registration", str(args.registration)],
        cwd=ROOT,
        env=env,
        check=False,
    )

    argv = [sys.executable, str(GATE)]
    if args.output:
        argv += ["--output", str(args.output)]
    gate = subprocess.run(argv, cwd=ROOT, env=env, check=False)

    if apps.returncode != 0:
        return apps.returncode
    return gate.returncode


if __name__ == "__main__":
    raise SystemExit(main())
