#!/usr/bin/env python3
"""Synthetic regression for STRICT Andreas-target receipt commit coherence.

This is not target evidence and not an out-of-box experiment. It proves the helper used by
strict adjudication accepts an otherwise-green real application receipt only when its
`git_head` equals the clean collector commit, and rejects mixed/missing commit identity.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_SCRIPT = ROOT / "tools/claycode_andreas_ubuntu_acceptance_assembler.py"


def load_target():
    spec = importlib.util.spec_from_file_location("claycode_strict_adjudication_regression_target", TARGET_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("STRICT_ADJUDICATION_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def green_app(target, head: str | None) -> dict:
    row = {
        "schema_version": "1.2",
        "app": "CLI",
        "pass": True,
        "target_host": target.TARGET,
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


def main() -> int:
    target = load_target()
    expected = "a" * 40
    wrong = "b" * 40
    rows = []
    with tempfile.TemporaryDirectory(prefix="claycode-strict-commit-coherence-") as td:
        root = Path(td)
        target.ROOT = root
        target.APP_RECEIPT_DIR = root / "apps"
        target.APP_RECEIPT_DIR.mkdir(parents=True)
        path = target.APP_RECEIPT_DIR / "CLI.json"

        for case, head, want in (
            ("same_commit", expected, True),
            ("mixed_commit", wrong, False),
            ("missing_commit", None, False),
        ):
            path.write_text(json.dumps(green_app(target, head)), encoding="utf-8")
            observed, detail = target.real_app_receipt("CLI", expected)
            rows.append({
                "case": case,
                "expected": want,
                "observed": observed,
                "git_head_match": detail.get("git_head_match"),
                "reasons": detail.get("reasons"),
            })

        path.unlink()
        observed, detail = target.real_app_receipt("CLI", expected)
        rows.append({
            "case": "missing_receipt",
            "expected": False,
            "observed": observed,
            "git_head_match": detail.get("git_head_match"),
            "reasons": detail.get("reasons"),
        })

    passed = all(row["observed"] is row["expected"] for row in rows)
    payload = {
        "schema_version": "1.0",
        "test_id": "CLAYCODE_STRICT_ADJUDICATION_COMMIT_COHERENCE_REGRESSION",
        "pass": passed,
        "cases": rows,
        "scope_guard": "Synthetic release-gate regression only; never Andreas target acceptance evidence.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
