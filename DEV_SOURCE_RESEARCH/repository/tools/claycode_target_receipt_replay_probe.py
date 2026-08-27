#!/usr/bin/env python3
"""Falsify stale Andreas-target release evidence replay at the workspace promoter boundary.

This is one bounded matched-control experiment over the real production promoter:
- stale arm: an otherwise green manifest bound to an old/different repository commit MUST fail;
- fresh arm: the same synthetic shape bound to the exact current checkout HEAD MUST pass.

Both arms use isolated temporary workspaces. No real release workspace, target receipt,
Frank runtime, or authority state is mutated. Passing this probe validates only promoter
freshness discrimination; it does not fabricate Andreas target evidence.
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


def current_head() -> str:
    cp = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return cp.stdout.strip() if cp.returncode == 0 else ""


def manifest_for(repository_commit: str) -> dict:
    wps = {wp: {"pass": True} for wp in EXPECTED_WPS}
    wps["CC-WP-10-GENERAL-APP-SUITE"]["applications"] = [
        {"app": app, "reasons": []} for app in APPS
    ]
    return {
        "schema_version": "replay-probe",
        "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST",
        "target_host": TARGET,
        "repository_commit": repository_commit,
        "general_purpose_gate_pass": True,
        "claycode_release_gate_pass": True,
        "promotion_allowed": True,
        "failed_work_packages": [],
        "work_packages": wps,
    }


def fresh_workspace() -> dict:
    return {
        "schema_version": "replay-probe",
        "status": "ACTIVE_BUILD",
        "gate_status": "NOT_PASS",
        "general_purpose_gate_status": "NOT_PASS",
        "work_packages": {wp: {"status": "OPEN"} for wp in EXPECTED_WPS},
        "application_acceptance": {"required": APPS, "passed": []},
        "completed_receipts": [],
    }


def arm(root: Path, name: str, repository_commit: str) -> dict:
    manifest_path = root / f"{name}_manifest.json"
    workspace_path = root / f"{name}_workspace.json"
    manifest_path.write_text(json.dumps(manifest_for(repository_commit), indent=2) + "\n", encoding="utf-8")
    workspace_path.write_text(json.dumps(fresh_workspace(), indent=2) + "\n", encoding="utf-8")
    cp = subprocess.run(
        [sys.executable, str(PROMOTER), "--manifest", str(manifest_path), "--workspace", str(workspace_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    after = json.loads(workspace_path.read_text(encoding="utf-8"))
    promoted = (
        cp.returncode == 0
        and after.get("gate_status") == "PASS"
        and after.get("general_purpose_gate_status") == "PASS"
    )
    return {
        "name": name,
        "repository_commit": repository_commit,
        "promoter_returncode": cp.returncode,
        "promoted": promoted,
        "stdout_tail": cp.stdout[-2000:],
        "stderr_tail": cp.stderr[-2000:],
    }


def main() -> int:
    head = current_head()
    with tempfile.TemporaryDirectory(prefix="clay-target-replay-", dir=ROOT) as td:
        d = Path(td)
        stale = arm(d, "stale", STALE_COMMIT)
        fresh = arm(d, "fresh", head)
        stale_rejected = not stale["promoted"]
        fresh_accepted = bool(head) and fresh["promoted"]
        result = {
            "schema_version": "1.1",
            "experiment": "STALE_ANDREAS_TARGET_RECEIPT_REPLAY_NEGATIVE_CONTROL",
            "design": "MATCHED_STALE_VS_EXACT_CURRENT_HEAD",
            "real_promoter": str(PROMOTER.relative_to(ROOT)),
            "current_git_head": head or None,
            "stale_arm": stale,
            "fresh_arm": fresh,
            "stale_rejected": stale_rejected,
            "fresh_accepted": fresh_accepted,
            "probe_pass": stale_rejected and fresh_accepted,
            "authority_invariant": "model output != execution authority",
            "scope_guard": (
                "Synthetic isolated workspaces only; this tests promoter freshness discrimination and does not count as target acceptance."
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["probe_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
