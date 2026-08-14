#!/usr/bin/env python3
"""Regression for WP14 cross-receipt commit coherence.

This is a synthetic, execution-only release-gate falsifier. It never produces target
acceptance evidence. It proves that otherwise-green application/full-FRANK receipts are
accepted only when their git_head matches the strict release commit and fail closed for a
mismatch or missing commit identity.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/claycode_base_wp14_strict_audit.py"


def load_audit():
    spec = importlib.util.spec_from_file_location("claycode_wp14_audit_regression_target", AUDIT)
    if spec is None or spec.loader is None:
        raise RuntimeError("WP14_AUDIT_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def app_receipt(audit, head: str | None) -> dict:
    row = {
        "schema_version": "1.2",
        "app": "CLI",
        "pass": True,
        "target_host": audit.TARGET,
        "evidence_class": "ANDREAS_UBUNTU_REAL_APPLICATION",
        "model_output_is_execution_authority": False,
        "source_sha256": "1" * 64,
        "artifact_sha256": "2" * 64,
        "expected": 42,
        "observed": 42,
        "positive_test": {"pass": True},
        "negative_test": {"pass": True},
    }
    if head is not None:
        row["git_head"] = head
    return row


def full_frank_receipt(audit, head: str | None) -> dict:
    row = {
        "schema_version": "1.1",
        "pass": True,
        "target_host": audit.TARGET,
        "evidence_class": "ANDREAS_UBUNTU_FULL_FRANK_HANDOFF",
        "semantic_escape_hatch_used": False,
        "model_output_is_execution_authority": False,
        "h2_h3_handoff_ready": True,
        "frank_input_sha256": "3" * 64,
        "clay_source_sha256": "4" * 64,
        "artifact_sha256": "5" * 64,
        "expected": {},
        "observed": {},
        "production_chain_receipts": {},
    }
    if head is not None:
        row["git_head"] = head
    return row


def main() -> int:
    audit = load_audit()
    expected = "a" * 40
    wrong = "b" * 40
    rows = []

    with tempfile.TemporaryDirectory(prefix="claycode-wp14-coherence-") as td:
        root = Path(td)
        app_dir = root / "apps"
        app_dir.mkdir(parents=True)
        full_frank = root / "FULL_FRANK_HANDOFF_RECEIPT.json"
        audit.ROOT = root
        audit.APP_DIR = app_dir
        audit.FULL_FRANK = full_frank

        app_path = app_dir / "CLI.json"
        app_path.write_text(json.dumps(app_receipt(audit, expected)), encoding="utf-8")
        ok, detail = audit.real_app("CLI", expected)
        rows.append({"case": "app_same_commit", "expected": True, "observed": ok, "detail": detail})

        app_path.write_text(json.dumps(app_receipt(audit, wrong)), encoding="utf-8")
        ok, detail = audit.real_app("CLI", expected)
        rows.append({"case": "app_mixed_commit", "expected": False, "observed": ok, "detail": detail})

        app_path.write_text(json.dumps(app_receipt(audit, None)), encoding="utf-8")
        ok, detail = audit.real_app("CLI", expected)
        rows.append({"case": "app_missing_commit", "expected": False, "observed": ok, "detail": detail})

        full_frank.write_text(json.dumps(full_frank_receipt(audit, expected)), encoding="utf-8")
        ok, detail = audit.full_frank(expected)
        rows.append({"case": "full_frank_same_commit", "expected": True, "observed": ok, "detail": detail})

        full_frank.write_text(json.dumps(full_frank_receipt(audit, wrong)), encoding="utf-8")
        ok, detail = audit.full_frank(expected)
        rows.append({"case": "full_frank_mixed_commit", "expected": False, "observed": ok, "detail": detail})

        full_frank.write_text(json.dumps(full_frank_receipt(audit, None)), encoding="utf-8")
        ok, detail = audit.full_frank(expected)
        rows.append({"case": "full_frank_missing_commit", "expected": False, "observed": ok, "detail": detail})

    passed = all(row["observed"] is row["expected"] for row in rows)
    payload = {
        "schema_version": "1.0",
        "test_id": "CLAYCODE_WP14_CROSS_RECEIPT_COMMIT_COHERENCE_REGRESSION",
        "pass": passed,
        "cases": rows,
        "scope_guard": "Synthetic release-gate regression only; never target acceptance evidence.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
