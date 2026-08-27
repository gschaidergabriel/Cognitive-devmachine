#!/usr/bin/env python3
"""Bind v11 abstract-native J-Space claims to the exact derived challenge bytes.

v11 closes the scientific nuisance/scope logic.  v12 adds one authenticity property:
the lexical-disjointness / target-blindness claim must be reconstructible from the actual
model-facing challenge strings, and the runtime attestation must bind to those exact rows.
Caller-supplied lexical-family booleans or hashes alone cannot satisfy this successor.

This module is deterministic adjudication only and mints no canonical/model/product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v11 as v11
import trigger1_abstract_state_challenge_v1 as challenge_gate

SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v12"
REQUIRED_CONTROLS = {
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
}


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _expected_rows(challenge: dict[str, Any], split: str) -> dict[tuple[str, str], dict[str, Any]]:
    source = challenge["calibration_rows"] if split == "CALIBRATION" else challenge["holdout_rows"]
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in source:
        key = (str(row["family_id"]), str(row["semantic_target"]))
        material = {
            "family_id": row["family_id"],
            "family_sha256": row["family_sha256"],
            "semantic_target": row["semantic_target"],
            "seed": row["seed"],
            "prompt_sha256": row["prompt_sha256"],
        }
        if split == "HOLDOUT":
            material["output_code_identity"] = row["output_code_identity"]
        out[key] = material
    return out


def _bind_rows(
    expected: dict[tuple[str, str], dict[str, Any]],
    observed: Any,
    split: str,
    failures: list[str],
) -> None:
    if not isinstance(observed, list):
        failures.append(f"{split}_EXECUTED_CHALLENGE_ROWS_REQUIRED")
        return
    got: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw in enumerate(observed):
        prefix = f"{split}_EXECUTED_ROW_{index}"
        if not isinstance(raw, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        key = (str(raw.get("family_id") or ""), str(raw.get("semantic_target") or ""))
        if key in got:
            failures.append(f"{prefix}_DUPLICATE_FAMILY_TARGET")
            continue
        receipt = raw.get("runtime_receipt_sha256")
        if not _sha256(receipt):
            failures.append(f"{prefix}_RUNTIME_RECEIPT_REQUIRED")
        controls = raw.get("control_runtime_receipts")
        if not isinstance(controls, dict) or set(controls) != REQUIRED_CONTROLS:
            failures.append(f"{prefix}_EXACT_SIX_CONTROL_RECEIPTS_REQUIRED")
        elif any(not _sha256(controls[name]) for name in REQUIRED_CONTROLS):
            failures.append(f"{prefix}_CONTROL_RECEIPT_SHA256_INVALID")
        got[key] = raw

    if set(got) != set(expected):
        failures.append(f"{split}_EXECUTED_CHALLENGE_CASE_UNIVERSE_MISMATCH")
    for key in sorted(set(got) & set(expected)):
        raw = got[key]
        for field, value in expected[key].items():
            if raw.get(field) != value:
                failures.append(f"{split}_EXECUTED_CHALLENGE_FIELD_MISMATCH:{key[0]}:{key[1]}:{field}")


def _challenge_binding(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    challenge = candidate.get("abstract_state_challenge")
    design = challenge_gate.validate(challenge)
    if design.get("pass") is not True:
        failures.extend(f"CHALLENGE_DESIGN:{item}" for item in design.get("failures", []))
        return False, sorted(set(failures)), design
    if not isinstance(challenge, dict):
        return False, ["ABSTRACT_STATE_CHALLENGE_REQUIRED"], design

    binding = candidate.get("abstract_state_challenge_runtime_binding")
    if not isinstance(binding, dict):
        return False, ["ABSTRACT_STATE_CHALLENGE_RUNTIME_BINDING_REQUIRED"], design
    if binding.get("challenge_sha256") != design.get("challenge_sha256"):
        failures.append("EXECUTED_CHALLENGE_SHA256_MISMATCH")
    if binding.get("runtime_intervention_scope") != "ALL_PROMPT_TOKENS":
        failures.append("V11_DIRECT_NATIVE_CHALLENGE_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
    if binding.get("model_facing_target_identity_exposed") is not False:
        failures.append("EXECUTED_CHALLENGE_TARGET_IDENTITY_MUST_REMAIN_HIDDEN")
    if binding.get("prompt_bytes_revalidated_from_runtime_rows") is not True:
        failures.append("EXECUTED_PROMPT_BYTES_MUST_BE_REVALIDATED")
    if binding.get("generic_compliance_axis_fails_to_reproduce_target_matrix") is not True:
        failures.append("EXECUTED_GENERIC_COMPLIANCE_COUNTERHYPOTHESIS_MUST_FAIL")
    if not _sha256(binding.get("generic_compliance_control_receipt_sha256")):
        failures.append("GENERIC_COMPLIANCE_CONTROL_RECEIPT_REQUIRED")
    if not _sha256(binding.get("binding_receipt_sha256")):
        failures.append("CHALLENGE_RUNTIME_BINDING_RECEIPT_REQUIRED")

    _bind_rows(
        _expected_rows(challenge, "CALIBRATION"),
        binding.get("calibration_rows"),
        "CALIBRATION",
        failures,
    )
    _bind_rows(
        _expected_rows(challenge, "HOLDOUT"),
        binding.get("holdout_rows"),
        "HOLDOUT",
        failures,
    )
    return not failures, sorted(set(failures)), design


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v11.adjudicate(candidate)
    binding_ok, binding_failures, design = _challenge_binding(candidate)
    abstract = bool(base.get("abstract_native_semantic_jspace_candidate") is True and binding_ok)
    failures = sorted(set(list(base.get("v11_failures", [])) + binding_failures))
    return {
        **base,
        "schema": SCHEMA,
        "derived_abstract_challenge_design_pass": design.get("pass") is True,
        "exact_abstract_challenge_runtime_binding_pass": binding_ok,
        "abstract_state_challenge_sha256": design.get("challenge_sha256"),
        "abstract_native_semantic_jspace_candidate": abstract,
        "strict_micro_mechanistic_identity_candidate": False,
        "v12_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v12 requires v11 plus reconstruction of label/lexical/target-blind challenge properties from actual "
            "model-facing strings and exact binding of the executed six-family calibration + six-family holdout "
            "rows to those bytes and six control receipts. It remains non-minting adjudication; external runtime "
            "receipt authenticity and the actual causal measurements remain separate evidence boundaries."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": SCHEMA, "abstract_native_semantic_jspace_candidate": False, "v12_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"], "canonical_credit_minted": False}
    if not isinstance(candidate, dict):
        return {"schema": SCHEMA, "abstract_native_semantic_jspace_candidate": False, "v12_failures": ["CANDIDATE_OBJECT_REQUIRED"], "canonical_credit_minted": False}
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "abstract_native_semantic_jspace_candidate": any(x.get("abstract_native_semantic_jspace_candidate") is True for x in verdicts),
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = ap.parse_args()
    out = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
