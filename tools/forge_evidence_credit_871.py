#!/usr/bin/env python3
"""Supervisor-8.71 fail-closed Evidence Forge acceptance credit audit.

Historical Forge rows remain append-only. This module distinguishes nominal historical
`accepted` labels from evidence-qualified acceptance under current 8.71 invariants.
It performs no network access and grants no canonical/runtime/model/training credit.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import re
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40_64 = re.compile(r"^[0-9a-f]{40,64}$")


def _int(obj: dict[str, Any], key: str, minimum: int = 0) -> int | None:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        return None
    return value


def nominal_accept(row: Any) -> bool:
    if not isinstance(row, dict) or row.get("record_type") == "schema_marker":
        return False
    if str(row.get("status", "")).lower() not in {"accepted", "pass", "integrated", "verified"}:
        return False
    try:
        improvement = float(row.get("relative_improvement_pct"))
        runs = int(row.get("reproducible_runs", 0))
        failed = int(row.get("tests_failed", 0)) + int(row.get("negative_tests_failed", 0)) + int(row.get("static_checks_failed", 0))
    except Exception:
        return False
    return improvement > 0 and runs >= 2 and failed == 0 and row.get("benchmark_non_regression") is True and not bool(row.get("reverted", False))


def _safe_targets(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    for name, blob in value.items():
        if not isinstance(name, str) or not name.strip():
            return False
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or str(p).startswith(".git"):
            return False
        if blob != "NEW_OR_MISSING_AT_SOURCE" and not (isinstance(blob, str) and HEX40_64.fullmatch(blob)):
            return False
    return True


def evidence_reason(row: Any) -> tuple[bool, str]:
    if not nominal_accept(row):
        return False, "NOT_NOMINAL_ACCEPT"
    if row.get("schema") != "CLAY_FORGE_DELTA_EVALUATION/v1":
        return False, "WRONG_SCHEMA"
    if row.get("source_scope") != "EXACT_WORKER_PROMPT_HEAD":
        return False, "SOURCE_SCOPE_NOT_EXACT"

    source_head = row.get("source_repo_head")
    evaluation_head = row.get("evaluation_repo_head")
    worker_sha = row.get("worker_sha")
    if not (isinstance(source_head, str) and HEX40.fullmatch(source_head)):
        return False, "SOURCE_HEAD_UNBOUND"
    if not (isinstance(evaluation_head, str) and HEX40.fullmatch(evaluation_head)):
        return False, "EVALUATION_HEAD_UNBOUND"
    if not (isinstance(worker_sha, str) and HEX64.fullmatch(worker_sha)):
        return False, "WORKER_SHA_UNBOUND"
    if not _safe_targets(row.get("target_blob_identities")):
        return False, "TARGET_BLOBS_UNBOUND"

    admission = row.get("execution_admission")
    if not isinstance(admission, dict) or admission.get("schema") != "CLAY_FORGE_EXECUTION_ADMISSION/v1":
        return False, "EXECUTION_ADMISSION_MISSING"
    if admission.get("source_scope") != "EXACT_WORKER_PROMPT_HEAD":
        return False, "EXECUTION_SOURCE_SCOPE_NOT_EXACT"
    if admission.get("source_identity_admitted") is not True:
        return False, "EXECUTION_SOURCE_IDENTITY_NOT_ADMITTED"
    if admission.get("source_head") != source_head:
        return False, "EXECUTION_SOURCE_HEAD_MISMATCH"

    evaluation_checkout_head = admission.get("evaluation_checkout_head")
    if not (isinstance(evaluation_checkout_head, str) and HEX40.fullmatch(evaluation_checkout_head)):
        return False, "EXECUTION_EVALUATION_HEAD_UNBOUND"
    if evaluation_checkout_head != evaluation_head:
        return False, "EXECUTION_EVALUATION_HEAD_MISMATCH"

    decisions = admission.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        return False, "EXECUTION_COMMAND_DECISIONS_MISSING"
    if any(not isinstance(decision, dict) or decision.get("admitted") is not True for decision in decisions):
        return False, "EXECUTION_COMMAND_DECISION_REJECTED"
    if admission.get("all_commands_admitted") is not True:
        return False, "MODEL_COMMAND_SET_NOT_ADMITTED"
    if admission.get("candidate_is_canonical_truth") is not False:
        return False, "CANDIDATE_TRUTH_FENCE_MISSING"

    backend = admission.get("backend")
    if not isinstance(backend, dict) or backend.get("admitted") is not True:
        return False, "ISOLATED_BACKEND_NOT_ADMITTED"
    if backend.get("backend") != "bubblewrap_unshare_all" or backend.get("network_namespace") != "ISOLATED":
        return False, "ISOLATION_NOT_PROVEN"
    if backend.get("secret_environment_inherited") is not False or backend.get("host_secret_paths_exposed") is not False:
        return False, "SECRET_FENCE_NOT_PROVEN"

    if _int(row, "reproducible_runs", 2) is None or _int(row, "tests_passed", 1) is None:
        return False, "MEASUREMENT_COUNTS_INVALID"
    for key in ("tests_failed", "negative_tests_failed", "static_checks_failed"):
        if _int(row, key, 0) != 0:
            return False, key.upper() + "_NONZERO_OR_INVALID"

    return True, "EVIDENCE_QUALIFIED_ACCEPT"


def audit(path: Path) -> dict[str, Any]:
    reasons: collections.Counter[str] = collections.Counter()
    nominal = qualified = seen = invalid_json = 0
    if not path.exists():
        return {"schema": "CLAY_FORGE_EVIDENCE_CREDIT_AUDIT/v1", "path": str(path), "missing": True, "seen": 0, "nominal_accepted": 0, "evidence_qualified_accepted": 0, "reasons": {}}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        seen += 1
        try:
            row = json.loads(line)
        except Exception:
            invalid_json += 1
            reasons["INVALID_JSON"] += 1
            continue
        if nominal_accept(row):
            nominal += 1
            ok, reason = evidence_reason(row)
            reasons[reason] += 1
            if ok:
                qualified += 1
    return {
        "schema": "CLAY_FORGE_EVIDENCE_CREDIT_AUDIT/v1",
        "path": str(path),
        "missing": False,
        "seen": seen,
        "invalid_json": invalid_json,
        "nominal_accepted": nominal,
        "evidence_qualified_accepted": qualified,
        "legacy_or_unqualified_accepted": nominal - qualified,
        "reasons": dict(sorted(reasons.items())),
        "credit_scope": "FORGE_ACCEPTANCE_METRIC_ONLY",
        "whole_entityos_hcu_runtime_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger", type=Path)
    args = ap.parse_args()
    print(json.dumps(audit(args.ledger), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())