#!/usr/bin/env python3
"""Promote the ClayCode release workspace only from a passing WP14 manifest.

This is bookkeeping, not evidence generation. It cannot turn proxy/hosted results into
release evidence: the WP14 manifest it consumes is itself fail-closed on the registered
Andreas Ubuntu strict target receipt, ten real application receipts, full FRANK handoff
and zero open P0/P1 defects.

Freshness law: the manifest's release repository commit must equal the checkout HEAD that
is attempting promotion. A fully coherent old target bundle is still stale evidence for a
newer source tree and must fail closed rather than replay into BASE PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json"
WORKSPACE = ROOT / "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
EXPECTED_WPS = [
    "CC-WP-01-SPEC-FREEZE",
    "CC-WP-02-PARSER-CANON",
    "CC-WP-03-IR-TYPES",
    "CC-WP-04-TYPE-EFFECT",
    "CC-WP-05-EVALUATOR",
    "CC-WP-06-COMPILER-LOWERING",
    "CC-WP-07-RUNTIME-ABI-FFI",
    "CC-WP-08-STDLIB-SDK",
    "CC-WP-09-CONCURRENCY-MEMORY",
    "CC-WP-10-GENERAL-APP-SUITE",
    "CC-WP-11-FUZZ-CONFORMANCE",
    "CC-WP-12-CORPUS-HELDOUT",
    "CC-WP-13-HARNESS-HANDOFF",
    "CC-WP-14-BASE-AUDIT",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--workspace", type=Path, default=WORKSPACE)
    args = ap.parse_args()

    if not args.manifest.exists() or not args.workspace.exists():
        print(json.dumps({"pass": False, "error": "MANIFEST_OR_WORKSPACE_MISSING"}))
        return 2

    manifest = load(args.manifest)
    workspace = load(args.workspace)
    failures: list[str] = []

    git_cp = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    git_head = git_cp.stdout.strip() if git_cp.returncode == 0 else ""
    manifest_repository_commit = str(manifest.get("repository_commit") or "").strip()
    if not git_head:
        failures.append("CURRENT_GIT_HEAD_UNAVAILABLE")
    if not manifest_repository_commit:
        failures.append("MANIFEST_REPOSITORY_COMMIT_MISSING")
    elif git_head and manifest_repository_commit != git_head:
        failures.append("MANIFEST_REPOSITORY_COMMIT_NOT_CURRENT")

    if manifest.get("manifest") != "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST":
        failures.append("WRONG_MANIFEST_KIND")
    if manifest.get("target_host") != TARGET:
        failures.append("WRONG_TARGET_HOST")
    for flag in ("general_purpose_gate_pass", "claycode_release_gate_pass", "promotion_allowed"):
        if manifest.get(flag) is not True:
            failures.append("MANIFEST_FLAG_NOT_TRUE:" + flag)
    if manifest.get("failed_work_packages") not in ([], None):
        failures.append("FAILED_WORK_PACKAGES_PRESENT")

    m_wps = manifest.get("work_packages") if isinstance(manifest.get("work_packages"), dict) else {}
    for wp in EXPECTED_WPS:
        row = m_wps.get(wp)
        if not isinstance(row, dict) or row.get("pass") is not True:
            failures.append("WORK_PACKAGE_NOT_PASS:" + wp)

    required_apps = list((workspace.get("application_acceptance") or {}).get("required") or [])
    if len(required_apps) != 10:
        failures.append("EXPECTED_TEN_APPLICATIONS")
    wp10 = m_wps.get("CC-WP-10-GENERAL-APP-SUITE") or {}
    app_rows = wp10.get("applications") if isinstance(wp10.get("applications"), list) else []
    app_pass = {str(x.get("app")): not x.get("reasons") for x in app_rows if isinstance(x, dict) and x.get("app")}
    for app in required_apps:
        if app_pass.get(app) is not True:
            failures.append("APPLICATION_NOT_ACCEPTED:" + app)

    if failures:
        print(json.dumps({
            "pass": False,
            "failures": failures,
            "manifest_repository_commit": manifest_repository_commit or None,
            "current_git_head": git_head or None,
        }, ensure_ascii=False))
        return 2

    manifest_hash = sha(args.manifest)
    promoted_at = datetime.now(timezone.utc).isoformat()

    for wp in EXPECTED_WPS:
        row = workspace.setdefault("work_packages", {}).setdefault(wp, {})
        row["status"] = "PASS"
        row["receipt"] = str(args.manifest.relative_to(ROOT)) if args.manifest.is_relative_to(ROOT) else str(args.manifest)
        row["promotion_basis"] = {
            "manifest_sha256": manifest_hash,
            "manifest_work_package_pass": True,
            "manifest_repository_commit": manifest_repository_commit,
            "current_git_head": git_head,
            "fresh_commit_match": True,
        }

    workspace["status"] = "BASE_PASS"
    workspace["gate_status"] = "PASS"
    workspace["general_purpose_gate_status"] = "PASS"
    if isinstance(workspace.get("blocker_burndown"), dict):
        workspace["blocker_burndown"]["status"] = "CLOSED_14_OF_14"
        workspace["blocker_burndown"]["closed_count"] = 14
        workspace["blocker_burndown"]["open_count"] = 0
    aa = workspace.setdefault("application_acceptance", {})
    aa["passed"] = required_apps
    aa["not_yet_passed"] = []
    aa["status"] = "PASS"

    completed = list(workspace.get("completed_receipts") or [])
    for receipt in (
        str(args.manifest.relative_to(ROOT)) if args.manifest.is_relative_to(ROOT) else str(args.manifest),
        "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_V2.json",
        "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json",
        "research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json",
        "research_entity/claycode/target_receipts/FULL_FRANK_HANDOFF_RECEIPT.json",
    ):
        if receipt not in completed:
            completed.append(receipt)
    workspace["completed_receipts"] = completed
    workspace["release_promotion"] = {
        "status": "PASS",
        "promoted_at": promoted_at,
        "target_host": TARGET,
        "manifest": str(args.manifest.relative_to(ROOT)) if args.manifest.is_relative_to(ROOT) else str(args.manifest),
        "manifest_sha256": manifest_hash,
        "strict_target_receipt": "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json",
        "manifest_repository_commit": manifest_repository_commit,
        "git_head_before_generated_evidence": git_head,
        "fresh_commit_match": True,
        "work_packages_passed": EXPECTED_WPS,
        "application_count": len(required_apps),
        "authority_invariant": "model output != execution authority",
    }
    workspace["last_updated"] = promoted_at

    atomic_json(args.workspace, workspace)
    reread = load(args.workspace)
    reread_ok = (
        reread.get("gate_status") == "PASS"
        and reread.get("general_purpose_gate_status") == "PASS"
        and all((reread.get("work_packages") or {}).get(wp, {}).get("status") == "PASS" for wp in EXPECTED_WPS)
    )
    print(json.dumps({
        "pass": reread_ok,
        "workspace": str(args.workspace.relative_to(ROOT)) if args.workspace.is_relative_to(ROOT) else str(args.workspace),
        "manifest_sha256": manifest_hash,
        "manifest_repository_commit": manifest_repository_commit,
        "current_git_head": git_head,
        "fresh_commit_match": manifest_repository_commit == git_head,
        "work_packages_pass": 14 if reread_ok else None,
        "applications_pass": len(required_apps) if reread_ok else None,
    }))
    return 0 if reread_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
