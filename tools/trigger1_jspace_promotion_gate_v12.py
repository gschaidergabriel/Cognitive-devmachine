#!/usr/bin/env python3
"""Exact-source audited successor to Trigger-1 J-Space promotion gate v11.

v11 correctly requires nuisance residualization and direct native ALL_PROMPT_TOKENS evidence,
but several deconfound properties arrive as attestations/receipt digests. v12 adds an exact,
deterministic source audit: the basis design and both producer case-plan objects must match a
frozen label-free abstract relation protocol whose model-facing payload lexicons are pairwise
disjoint across BASIS/CALIBRATION/HOLDOUT and whose calibration/holdout mapping is a full 3x3
semantic-metadata x arbitrary A/B/C code factorial.

The old LAST_TOKEN_ONLY witness remains ineligible as a native-causal identity premise through
v11. A separate scope-matched all-token witness may be used for backend replication, but v12
does not require cross-backend numerical identity to support a direct-native candidate.

Execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools import trigger1_abstract_state_protocol_v1 as exact_protocol
from tools import trigger1_jspace_promotion_gate_v11 as v11

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v12"
BASIS_BINDING_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_BASIS_CAPTURE_BINDING/v1"


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def exact_source_audit(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    expected = exact_protocol.validate_design()
    if expected.get("pass") is not True:
        failures.append("FROZEN_EXACT_PROTOCOL_INTERNAL_VALIDATION_FAILED")

    declared = candidate.get("abstract_state_exact_protocol")
    if not isinstance(declared, dict):
        failures.append("ABSTRACT_STATE_EXACT_PROTOCOL_ATTESTATION_REQUIRED")
        declared = {}
    for field in (
        "protocol_sha256",
        "basis_design_sha256",
        "case_plan_sha256",
        "payload_lexicon_sha256",
        "payload_lexicon_pairwise_disjoint",
        "canonical_status_words_model_facing_absent",
        "semantic_x_output_code_counterbalanced",
        "generic_instruction_scaffold_common_mode",
        "explicit_yes_no_approval_compliance_vocabulary_absent",
    ):
        if declared.get(field) != expected.get(field):
            failures.append(f"ABSTRACT_STATE_EXACT_PROTOCOL_FIELD_MISMATCH:{field}")

    expected_plans = exact_protocol.expected_case_plans()
    prereg = candidate.get("preregistration_evidence")
    source_plans = prereg.get("case_plans") if isinstance(prereg, dict) else None
    if not isinstance(source_plans, dict):
        failures.append("EXACT_AUDIT_BOUND_SOURCE_CASE_PLANS_REQUIRED")
        source_plans = {}
    for split in ("CALIBRATION", "HOLDOUT"):
        got = source_plans.get(split)
        want = expected_plans[split]
        if not isinstance(got, dict):
            failures.append(f"EXACT_AUDIT_{split}_SOURCE_PLAN_REQUIRED")
            continue
        if got.get("plan_sha256") != want.get("plan_sha256"):
            failures.append(f"EXACT_AUDIT_{split}_PLAN_SHA256_MISMATCH")
        if got != want:
            failures.append(f"EXACT_AUDIT_{split}_PLAN_OBJECT_MISMATCH")

    basis_binding = candidate.get("abstract_state_basis_capture_binding")
    if not isinstance(basis_binding, dict):
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_BINDING_REQUIRED")
        basis_binding = {}
    if basis_binding.get("schema") != BASIS_BINDING_SCHEMA:
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_BINDING_SCHEMA_INVALID")
    if basis_binding.get("basis_design_sha256") != expected.get("basis_design_sha256"):
        failures.append("ABSTRACT_STATE_BASIS_DESIGN_SHA256_MISMATCH")
    expected_basis_rows = exact_protocol.basis_rows()
    expected_prompt_hashes = sorted(row["prompt_sha256"] for row in expected_basis_rows)
    observed_prompt_hashes = basis_binding.get("captured_prompt_sha256")
    if not isinstance(observed_prompt_hashes, list) or sorted(observed_prompt_hashes) != expected_prompt_hashes:
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_PROMPT_UNIVERSE_MISMATCH")
    if basis_binding.get("family_count") != 6:
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_EXACT_SIX_FAMILIES_REQUIRED")
    if basis_binding.get("capture_frozen_before_holdout") is not True:
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_MUST_PRECEDE_HOLDOUT")
    if not _sha256(basis_binding.get("basis_capture_receipt_sha256")):
        failures.append("ABSTRACT_STATE_BASIS_CAPTURE_RECEIPT_REQUIRED")
    if not _sha256(basis_binding.get("projected_basis_receipt_sha256")):
        failures.append("ABSTRACT_STATE_PROJECTED_BASIS_RECEIPT_REQUIRED")

    deconfound = candidate.get("abstract_state_deconfound")
    if not isinstance(deconfound, dict):
        failures.append("ABSTRACT_STATE_DECONFOUND_REQUIRED_FOR_EXACT_AUDIT")
        deconfound = {}
    if basis_binding.get("projected_basis_receipt_sha256") != deconfound.get("projected_basis_receipt_sha256"):
        failures.append("ABSTRACT_STATE_PROJECTED_BASIS_RECEIPT_CROSS_BINDING_MISMATCH")
    if deconfound.get("basis_holdout_lexically_disjoint") is not True:
        failures.append("V11_BASIS_HOLDOUT_LEXICAL_DISJOINTNESS_ATTESTATION_MUST_REMAIN_TRUE")
    if deconfound.get("semantic_synonym_lexicon_disjoint") is not True:
        failures.append("V11_SEMANTIC_SYNONYM_DISJOINTNESS_ATTESTATION_MUST_REMAIN_TRUE")

    return {
        "pass": not failures,
        "failures": sorted(set(failures)),
        "protocol_sha256": expected.get("protocol_sha256"),
        "basis_design_sha256": expected.get("basis_design_sha256"),
        "case_plan_sha256": expected.get("case_plan_sha256"),
        "payload_lexicon_sha256": expected.get("payload_lexicon_sha256"),
        "basis_prompt_count": len(expected_basis_rows),
        "calibration_case_count": 9,
        "holdout_case_count": 9,
        "model_executed": False,
        "canonical_credit_minted": False,
    }


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v11.adjudicate(candidate)
    exact = exact_source_audit(candidate)
    base_native = base.get("abstract_native_semantic_jspace_candidate") is True
    promoted_candidate = bool(base_native and exact.get("pass") is True)
    failures = sorted(set(list(base.get("v11_failures", [])) + list(exact.get("failures", []))))
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v11_abstract_native_semantic_jspace_candidate": bool(base_native),
        "exact_abstract_source_audit_pass": exact.get("pass") is True,
        "exact_abstract_source_audit_failures": exact.get("failures", []),
        "exact_abstract_protocol_sha256": exact.get("protocol_sha256"),
        "exact_abstract_basis_design_sha256": exact.get("basis_design_sha256"),
        "exact_abstract_case_plan_sha256": exact.get("case_plan_sha256"),
        "abstract_native_semantic_jspace_candidate": promoted_candidate,
        "abstract_state_control_candidate": promoted_candidate,
        "strict_micro_mechanistic_identity_candidate": False,
        "v12_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v12 requires all v11 nuisance-residualized direct-native ALL_PROMPT_TOKENS evidence plus an "
            "exact deterministic binding to the frozen label-free abstract-state basis and exact CALIBRATION/"
            "HOLDOUT producer plans. Prompt payload lexicons are recomputed from source and pairwise disjoint; "
            "the 3x3 semantic-metadata x arbitrary-code mapping is recomputed, not trusted as a boolean. The "
            "basis capture prompt universe is hash-bound to the exact 18-row six-family design and cross-bound "
            "to v11's projected-basis receipt. The historical last-token witness remains non-identifying. This "
            "gate is adjudication only and mints no canonical semantics/runtime/J-Space/HCU/EntityOS/training credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "abstract_state_control_candidate": False,
            "canonical_credit_minted": False,
            "v12_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(obj, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "abstract_state_control_candidate": False,
            "canonical_credit_minted": False,
            "v12_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(obj)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "abstract_native_semantic_jspace_candidate": any(
            row.get("abstract_native_semantic_jspace_candidate") is True for row in verdicts
        ),
        "abstract_state_control_candidate": any(
            row.get("abstract_state_control_candidate") is True for row in verdicts
        ),
        "strict_micro_mechanistic_identity_candidate": False,
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = ap.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
