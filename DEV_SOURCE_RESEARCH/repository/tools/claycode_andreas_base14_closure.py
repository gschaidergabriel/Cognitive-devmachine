#!/usr/bin/env python3
"""One-command fail-closed ClayCode BASE14 closeout on Andreas' Ubuntu target.

Canonical order:
1. verify the owner-local machine fingerprint from a pristine checkout;
2. run the component target gate while the release input is still pristine;
3. prove FULL_FRANK through two independent H2 realizations + H3 + native subsystem
   paths and materialize its target-only receipts;
4. run resource/concurrency lifetime evidence;
5. execute the hardened ten-application suite and materialize WP14-shaped app receipts;
6. run the final WP14 auditor/manifest.

The target-id environment is set internally only after fingerprint verification. A
caller-supplied target string is therefore not sufficient evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE14_CLOSURE.json"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
DEFAULT_REGISTRATION = Path.home() / ".config/claycode/andreas_target_registration.json"
MANIFEST = ROOT / "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_initial_checkout() -> tuple[bool, list[str]]:
    cp = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False)
    return cp.returncode == 0 and not cp.stdout.strip(), cp.stdout.splitlines()[:50]


def run(name: str, argv: list[str], env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    try:
        cp = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=timeout)
        return {
            "step": name,
            "argv": argv,
            "returncode": cp.returncode,
            "pass": cp.returncode == 0,
            "stdout_tail": cp.stdout[-12000:],
            "stderr_tail": cp.stderr[-12000:],
        }
    except Exception as exc:
        return {
            "step": name,
            "argv": argv,
            "returncode": None,
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    clean, dirty = clean_initial_checkout()
    if not clean:
        print(json.dumps({"error": "INITIAL_CHECKOUT_NOT_CLEAN", "entries": dirty}, ensure_ascii=False))
        return 3

    identity = subprocess.run(
        [sys.executable, "tools/claycode_target_host_identity.py", "verify", "--registration", str(args.registration), "--json"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        identity_payload = json.loads(identity.stdout) if identity.stdout.strip() else {}
    except Exception:
        identity_payload = {"raw_stdout": identity.stdout[-8000:]}
    if identity.returncode != 0 or identity_payload.get("verified") is not True or identity_payload.get("target_host") != TARGET:
        print(json.dumps({
            "error": "ANDREAS_TARGET_FINGERPRINT_NOT_VERIFIED",
            "registration": str(args.registration),
            "identity_returncode": identity.returncode,
            "identity": identity_payload,
            "stderr": identity.stderr[-4000:],
            "register_once_on_actual_target": f"python tools/claycode_target_host_identity.py register --acknowledge {TARGET}",
        }, ensure_ascii=False, indent=2))
        return 3

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    env = dict(os.environ)
    # Set only after the stronger local fingerprint verification above.
    env["CLAYCODE_TARGET_HOST_ID"] = TARGET

    steps = [
        (
            "target_components_pristine_input",
            [sys.executable, "tools/claycode_andreas_ubuntu_target_gate.py"],
        ),
        (
            "full_frank_two_h2_plus_h3",
            [sys.executable, "tools/claycode_full_frank_target_finalizer_runner.py", "--registration", str(args.registration)],
        ),
        (
            "resource_lifetime",
            [sys.executable, "tools/claycode_base_resource_lifetime_validation.py"],
        ),
        (
            "real_apps_10_of_10_hardened",
            [sys.executable, "tools/claycode_andreas_application_acceptance.py", "--registration", str(args.registration)],
        ),
        (
            "wp14_audit",
            [sys.executable, "tools/claycode_base_wp14_audit.py"],
        ),
    ]

    rows: list[dict[str, Any]] = []
    for name, argv in steps:
        row = run(name, argv, env)
        rows.append(row)
        if row["returncode"] != 0:
            # Preserve a fail-closed short circuit. Later steps must not reinterpret an
            # upstream failure as partial release evidence.
            break

    manifest: dict[str, Any] = {}
    if MANIFEST.exists():
        try:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                manifest = value
        except Exception:
            pass

    all_steps_pass = len(rows) == len(steps) and all(x["pass"] for x in rows)
    report = {
        "schema_version": "2.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_host": TARGET,
        "target_host_verified": True,
        "target_host_identity": identity_payload,
        "input_git_head": head,
        "steps": rows,
        "all_closeout_steps_pass": all_steps_pass,
        "general_purpose_gate_pass": manifest.get("general_purpose_gate_pass") is True,
        "claycode_release_gate_pass": manifest.get("claycode_release_gate_pass") is True,
        "failed_work_packages": manifest.get("failed_work_packages", []),
        "manifest_sha256": sha(MANIFEST.read_bytes()) if MANIFEST.exists() else None,
        "pass": bool(all_steps_pass and manifest.get("general_purpose_gate_pass") is True and manifest.get("claycode_release_gate_pass") is True),
        "authority_invariant": "model_output != execution_authority",
        "note": "A nonzero result is an evidence-preserving blocker verdict, never partial-success promotion.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "pass": report["pass"],
        "executed_steps": [x["step"] for x in rows],
        "failed_step": next((x["step"] for x in rows if not x["pass"]), None),
        "failed_work_packages": report["failed_work_packages"],
        "output": str(OUT.relative_to(ROOT)),
    }, ensure_ascii=False))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
