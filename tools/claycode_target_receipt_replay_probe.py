#!/usr/bin/env python3
"""Falsify stale Andreas-target release evidence replay at the workspace promoter boundary.

This is a bounded negative-control experiment. It builds a fully green synthetic WP14
manifest whose repository_commit is deliberately stale, then invokes the real production
promoter against an isolated temporary workspace. Safe behavior is rejection. If the
promoter accepts the stale manifest, the probe fails and records the replay vulnerability.

No real release workspace, target receipt, Frank runtime, or authority state is mutated.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTER = ROOT / "tools/claycode_promote_release_workspace.py"
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
APPS = [
    "CLI", "HTTP_WEBSITE", "DB_SERVICE", "CONCURRENT_SERVICE", "GUI_INTERACTIVE",
    "COMPILER_TOOL", "GPU_ML_NUMERICAL", "SYSTEM_EFFECT_SANDBOX", "FRANK_COMPONENT",
    "FULL_FRANK_HANDOFF",
]
STALE_COMMIT = "0" * 40


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="clay-target-replay-", dir=ROOT) as td:
        d = Path(td)
        manifest_path = d / "stale_manifest.json"
        workspace_path = d / "workspace.json"

        wps = {wp: {"pass": True} for wp in EXPECTED_WPS}
        wps["CC-WP-10-GENERAL-APP-SUITE"]["applications"] = [
            {"app": app, "reasons": []} for app in APPS
        ]
        manifest = {
            "schema_version": "replay-probe",
            "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST",
            "target_host": TARGET,
            "repository_commit": STALE_COMMIT,
            "general_purpose_gate_pass": True,
            "claycode_release_gate_pass": True,
            "promotion_allowed": True,
            "failed_work_packages": [],
            "work_packages": wps,
        }
        workspace = {
            "schema_version": "replay-probe",
            "status": "ACTIVE_BUILD",
            "gate_status": "NOT_PASS",
            "general_purpose_gate_status": "NOT_PASS",
            "work_packages": {wp: {"status": "OPEN"} for wp in EXPECTED_WPS},
            "application_acceptance": {"required": APPS, "passed": []},
            "completed_receipts": [],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        workspace_path.write_text(json.dumps(workspace, indent=2) + "\n", encoding="utf-8")

        cp = subprocess.run(
            [sys.executable, str(PROMOTER), "--manifest", str(manifest_path), "--workspace", str(workspace_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        after = json.loads(workspace_path.read_text(encoding="utf-8"))
        stale_accepted = (
            cp.returncode == 0
            and after.get("gate_status") == "PASS"
            and after.get("general_purpose_gate_status") == "PASS"
        )
        result = {
            "schema_version": "1.0",
            "experiment": "STALE_ANDREAS_TARGET_RECEIPT_REPLAY_NEGATIVE_CONTROL",
            "real_promoter": str(PROMOTER.relative_to(ROOT)),
            "stale_repository_commit": STALE_COMMIT,
            "expected": "REJECT_STALE_MANIFEST",
            "promoter_returncode": cp.returncode,
            "stale_manifest_accepted": stale_accepted,
            "probe_pass": not stale_accepted,
            "stdout_tail": cp.stdout[-2000:],
            "stderr_tail": cp.stderr[-2000:],
            "authority_invariant": "model output != execution authority",
            "scope_guard": "Synthetic isolated workspace only; no real target/release state mutated.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["probe_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
