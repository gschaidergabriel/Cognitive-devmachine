#!/usr/bin/env python3
"""Fail-closed integrity gate for Trigger-2 authority-masked transition rows.

This gate is deliberately *not* another semantic authority.  The retained semantics
remain:

- ``trigger2_executable_transition_pilot_v1`` for the executable transition donor;
- ``trigger2_executable_transition_authority_mask_v1`` for authority masking.

The missing property closed here is transport/materialization integrity.  A row that
was valid when produced must not remain apparently valid after its evaluator-bound
oracle envelope, learned body, source identity, state, or credit fences are mutated.

The gate therefore wraps each retained authority-masked candidate with an exact source
snapshot and checks the candidate against deterministic recomputation from the current
retained donor.  It mints no corpus, runtime, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from tools import trigger2_executable_transition_authority_mask_v1 as masked
from tools import trigger2_executable_transition_pilot_v1 as pilot

ROOT = Path(__file__).resolve().parents[1]
PILOT_PATH = ROOT / "tools/trigger2_executable_transition_pilot_v1.py"
MASK_PATH = ROOT / "tools/trigger2_executable_transition_authority_mask_v1.py"
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
CENSUS_PATH = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
COURSE_PATH = ROOT / "research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md"

SCHEMA = "TRIGGER2_EXECUTABLE_TRANSITION_AUTHORITY_MASK_INTEGRITY_ENVELOPE/v1"
AUDIT_SCHEMA = "TRIGGER2_EXECUTABLE_TRANSITION_AUTHORITY_MASK_INTEGRITY_AUDIT/v1"


def cj(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def dg(value: Any) -> str:
    return hashlib.sha256(cj(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_snapshot() -> dict[str, Any]:
    files = {
        "transition_donor": PILOT_PATH,
        "authority_mask": MASK_PATH,
        "cognitive_process_abi": ABI_PATH,
        "cognitive_process_census": CENSUS_PATH,
        "trigger2_course": COURSE_PATH,
    }
    return {
        "schema": "TRIGGER2_EXECUTABLE_TRANSITION_SOURCE_SNAPSHOT/v1",
        "files": {
            name: {
                "repo_path": str(path.relative_to(ROOT)),
                "sha256": file_sha256(path),
            }
            for name, path in files.items()
        },
        "issue": 2022,
    }


def _source_rows() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in pilot.rows():
        cid = row.get("case_id")
        if not isinstance(cid, str) or not cid:
            raise ValueError("SOURCE_CASE_ID_REQUIRED")
        if cid in out:
            raise ValueError("SOURCE_CASE_ID_DUPLICATE:" + cid)
        out[cid] = row
    return out


def bind_row(candidate: Mapping[str, Any]) -> dict[str, Any]:
    copied = copy.deepcopy(dict(candidate))
    return {
        "schema": SCHEMA,
        "status": "CANDIDATE_EVAL_ONLY_NOT_TRAINING_ELIGIBLE",
        "candidate": copied,
        "candidate_digest_evaluator_only": dg(copied),
        "source_snapshot_evaluator_only": source_snapshot(),
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


def rows() -> list[dict[str, Any]]:
    return [bind_row(row) for row in masked.rows()]


def adjudicate(envelope: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(envelope, Mapping):
        failures.append("ENVELOPE_OBJECT_REQUIRED")
        envelope = {}
    if envelope.get("schema") != SCHEMA:
        failures.append("ENVELOPE_SCHEMA_MISMATCH")
    if envelope.get("training_eligible") is not False:
        failures.append("TRAINING_ELIGIBILITY_MUST_REMAIN_FALSE")
    if envelope.get("accepted_dataset_tokens_minted") != 0:
        failures.append("ACCEPTED_DATASET_TOKENS_MUST_REMAIN_ZERO")
    if envelope.get("training_credit_minted") != 0:
        failures.append("TRAINING_CREDIT_MUST_REMAIN_ZERO")

    snapshot = envelope.get("source_snapshot_evaluator_only")
    expected_snapshot = source_snapshot()
    if not isinstance(snapshot, Mapping) or dict(snapshot) != expected_snapshot:
        failures.append("SOURCE_SNAPSHOT_MISMATCH")

    candidate = envelope.get("candidate")
    if not isinstance(candidate, Mapping):
        failures.append("CANDIDATE_OBJECT_REQUIRED")
        candidate = {}
    if dg(candidate) != envelope.get("candidate_digest_evaluator_only"):
        failures.append("CANDIDATE_DIGEST_MISMATCH")

    base = masked.audit_row(copy.deepcopy(dict(candidate))) if candidate else {
        "pass": False,
        "failures": ["CANDIDATE_MISSING"],
    }
    if not base.get("pass"):
        for failure in base.get("failures") or ["MASKED_BASE_AUDIT_REJECTED"]:
            failures.append("MASKED_BASE:" + str(failure))

    cid = candidate.get("case_id") if isinstance(candidate, Mapping) else None
    try:
        source_rows = _source_rows()
    except Exception as exc:
        failures.append("SOURCE_RECOMPUTE_EXCEPTION:" + type(exc).__name__)
        source_rows = {}

    source = source_rows.get(cid) if isinstance(cid, str) else None
    if source is None:
        failures.append("SOURCE_CASE_NOT_FOUND:" + str(cid))
    else:
        try:
            expected_candidate = masked.adapt_row(source)
        except Exception as exc:
            failures.append("EXPECTED_CANDIDATE_RECOMPUTE_EXCEPTION:" + type(exc).__name__)
        else:
            if dict(candidate) != expected_candidate:
                failures.append("CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION")
            if candidate.get("source_transition_semantic_digest") != source.get("transition_semantic_digest"):
                failures.append("SOURCE_TRANSITION_DIGEST_MISMATCH")
            if candidate.get("process_id_evaluator_only") != source.get("process_id_evaluator_only"):
                failures.append("PROCESS_ID_EVALUATOR_BINDING_MISMATCH")

    failures = sorted(set(failures))
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "retained_semantic_authority": "tools/trigger2_executable_transition_authority_mask_v1.py",
        "second_semantic_authority_created": False,
        "source_snapshot_bound": "SOURCE_SNAPSHOT_MISMATCH" not in failures,
        "candidate_recomputed_from_retained_donor": "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" not in failures,
        "training_eligible": False,
        "positive_rows_admitted": 0,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "model_runtime_credit_minted": 0,
        "jspace_credit_minted": 0,
        "hcu_credit_minted": 0,
        "entityos_credit_minted": 0,
        "evidence_boundary": "authority-masked candidate transport/source integrity only",
    }


def audit_all() -> dict[str, Any]:
    bound = rows()
    results = [adjudicate(row) for row in bound]
    failures = [
        {"index": idx, "case_id": row.get("candidate", {}).get("case_id"), "failures": result["failures"]}
        for idx, (row, result) in enumerate(zip(bound, results))
        if not result["pass"]
    ]
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "row_count": len(bound),
        "failures": failures,
        "training_eligible": False,
        "positive_rows_admitted": 0,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


if __name__ == "__main__":
    print(json.dumps(audit_all(), indent=2, sort_keys=True))
