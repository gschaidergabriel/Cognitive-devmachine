#!/usr/bin/env python3
"""Materialize contract-shaped ClayCode BASE application receipts on Andreas' target.

This is the canonical per-application receipt writer consumed by WP14. It delegates
actual execution to the hardened target suite (APP-02 real routing/HTML/assets/query
state, APP-04 cancellation/error, APP-05 kernel-FD event loop, etc.) and converts its
rows into the exact target_receipts/apps schema.

FULL_FRANK_HANDOFF is never fabricated here. The full-FRANK finalizer must have created
its independent application receipt first; this tool verifies that receipt and leaves it
unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_target_application_suite_v2 as suite  # noqa: E402
from claycode_target_host_identity import DEFAULT_REGISTRATION, TARGET_HOST, verify  # noqa: E402

TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
AGGREGATE = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json"
OUTDIR = ROOT / "research_entity/claycode/target_receipts/apps"
FULL_FRANK = OUTDIR / "FULL_FRANK_HANDOFF.json"
APPS = [
    "CLI", "HTTP_WEBSITE", "DB_SERVICE", "CONCURRENT_SERVICE", "GUI_INTERACTIVE",
    "COMPILER_TOOL", "GPU_ML_NUMERICAL", "SYSTEM_EFFECT_SANDBOX", "FRANK_COMPONENT",
    "FULL_FRANK_HANDOFF",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def negative_pass(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("pass"), bool):
            return bool(value["pass"])
        bools = [v for v in value.values() if isinstance(v, bool)]
        return bool(bools) and all(bools)
    if isinstance(value, list):
        bools = [v for v in value if isinstance(v, bool)]
        return bool(bools) and all(bools)
    return False


def convert(app: str, row: dict[str, Any], head: str) -> dict[str, Any]:
    negative = row.get("negative_or_failure_path")
    authority = row.get("authority_boundary_preserved") is True
    positive_ok = row.get("pass") is True
    neg_ok = negative_pass(negative)
    return {
        "schema_version": "1.2",
        "app": app,
        "pass": bool(positive_ok and neg_ok and authority),
        "target_host": TARGET,
        "evidence_class": "ANDREAS_UBUNTU_REAL_APPLICATION",
        "model_output_is_execution_authority": False,
        "git_head": head,
        "source_sha256": row.get("source_or_program_hash"),
        "semantic_or_ir_hash": row.get("semantic_or_ir_hash"),
        "artifact_sha256": row.get("target_artifact_hash"),
        "compiler_runtime_version": row.get("compiler_runtime_version"),
        "execution_command_or_test_id": row.get("execution_command_or_test_id"),
        "expected": row.get("expected"),
        "observed": row.get("observed"),
        "positive_test": {
            "pass": positive_ok,
            "execution_command_or_test_id": row.get("execution_command_or_test_id"),
            "semantic_or_ir_hash": row.get("semantic_or_ir_hash"),
        },
        "negative_test": {
            "pass": neg_ok,
            "observed": negative,
        },
        "authority_boundary_preserved": authority,
        "aggregate_receipt_sha256": sha(AGGREGATE.read_bytes()),
    }


def valid_full_frank() -> tuple[bool, list[str]]:
    if not FULL_FRANK.exists():
        return False, ["MISSING"]
    try:
        row = read_json(FULL_FRANK)
    except Exception as exc:
        return False, [f"INVALID:{type(exc).__name__}"]
    reasons = []
    if row.get("pass") is not True: reasons.append("PASS_NOT_TRUE")
    if row.get("target_host") != TARGET: reasons.append("WRONG_TARGET")
    if row.get("evidence_class") != "ANDREAS_UBUNTU_REAL_APPLICATION": reasons.append("WRONG_EVIDENCE_CLASS")
    if row.get("model_output_is_execution_authority") is not False: reasons.append("AUTHORITY_INVARIANT")
    for key in ("source_sha256", "artifact_sha256", "expected", "observed", "positive_test", "negative_test"):
        if key not in row: reasons.append("MISSING_FIELD:" + key)
    return not reasons, reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    host_ok, host = verify(args.registration)
    if not host_ok or host.get("target_host") != TARGET_HOST:
        print(json.dumps({"error": "TARGET_HOST_IDENTITY_NOT_VERIFIED", "host": host}, ensure_ascii=False, indent=2))
        return 3

    # Reuse the hardened target suite and ensure it verifies the same trust anchor.
    suite.DEFAULT_REGISTRATION = args.registration
    suite_rc = suite.main()
    if not AGGREGATE.exists():
        print(json.dumps({"error": "HARDENED_APPLICATION_AGGREGATE_MISSING", "suite_returncode": suite_rc}))
        return 2
    aggregate = read_json(AGGREGATE)
    rows = aggregate.get("applications") or {}
    if not isinstance(rows, dict):
        print(json.dumps({"error": "HARDENED_APPLICATION_ROWS_INVALID"}))
        return 2

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    emitted = []
    failed = []
    # FULL_FRANK is created only by the independent target finalizer. Never overwrite it
    # from the suite's summary row.
    for app in APPS:
        if app == "FULL_FRANK_HANDOFF":
            continue
        row = rows.get(app)
        if not isinstance(row, dict):
            failed.append(app + ":MISSING_ROW")
            continue
        receipt = convert(app, row, head)
        (OUTDIR / f"{app}.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        emitted.append(app)
        if not receipt["pass"]:
            failed.append(app + ":NOT_PASS")

    ff_ok, ff_reasons = valid_full_frank()
    if not ff_ok:
        failed.append("FULL_FRANK_HANDOFF:" + ",".join(ff_reasons))
    else:
        emitted.append("FULL_FRANK_HANDOFF")

    expected_set = set(APPS)
    complete = set(emitted) == expected_set and not failed and aggregate.get("pass") is True and suite_rc == 0
    summary = {
        "schema_version": "1.0",
        "target_host": TARGET,
        "target_host_verified": True,
        "host_fingerprint": host.get("host_fingerprint", {}),
        "git_head": head,
        "emitted_apps": sorted(emitted),
        "required_apps": APPS,
        "failed": failed,
        "hardened_suite_returncode": suite_rc,
        "hardened_suite_pass": aggregate.get("pass") is True,
        "pass": complete,
        "wp10_complete": complete,
        "full_frank_source": "tools/claycode_full_frank_target_finalizer.py",
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
