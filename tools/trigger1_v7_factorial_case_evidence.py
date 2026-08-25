#!/usr/bin/env python3
"""Deterministic Trigger-1 semantic-factorial case/evidence producer.

This module is deliberately execution-free. It never invents model-facing semantic
prompts. Instead it accepts an externally frozen set of label-free matched scenario
cases, verifies an exact 3x3 requested-semantic-state x output-code factorial, expands
those exact cases across the six evidence controls, and later binds observed per-control
runtime receipt digests into the evidence envelope consumed by
trigger1_semantic_factorial_evidence_gate_v1.

The separation is intentional: semantic_target is evaluator metadata, not model-facing
text. A producer that writes "Requested semantic state: AFFIRMATIVE" into the prompt
would reintroduce the target-label shortcut that the current preregistration forbids.
Runtime rows must echo the exact deterministic case identity; case_id alone is not a
sufficient binding between an observed receipt and its planned semantic-factorial cell.

This tool does not run a model, open holdout, synthesize runtime receipts, or mint any
runtime/J-Space/HCU/EntityOS/training/canonical-semantics credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_semantic_factorial_evidence_gate_v1 as evidence_gate

PLAN_SCHEMA = "CLAY_TRIGGER1_V7_SEMANTIC_FACTORIAL_CASE_PLAN/v2"
BOUND_SPLIT_SCHEMA = "CLAY_TRIGGER1_V7_BOUND_SEMANTIC_FACTORIAL_SPLIT/v2"
CASE_SPEC_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v1"
TARGETS = evidence_gate.TARGETS
CODES = evidence_gate.CODES
CONTROLS = evidence_gate.REQUIRED_CONTROLS
SPLITS = ("CALIBRATION", "HOLDOUT")
FORBIDDEN_MODEL_FACING_LABELS = tuple(x.lower() for x in TARGETS)
CASE_IDENTITY_FIELDS = (
    "case_id",
    "seed",
    "prompt_sha256",
    "semantic_target",
    "output_code_identity",
    "split_family_id",
    "scenario_family_sha256",
    "lexical_family_sha256",
    "codebook_family_sha256",
)


class EvidenceBuildError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return evidence_gate.canonical_sha(value)


def _prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _case_identity(row: dict[str, Any]) -> str:
    return canonical_sha({key: row.get(key) for key in CASE_IDENTITY_FIELDS})


def _normalize_case_spec(raw: Any, *, split: str, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise EvidenceBuildError(f"CASE_SPEC_{index}_OBJECT_REQUIRED")
    if raw.get("schema") not in (None, CASE_SPEC_SCHEMA):
        raise EvidenceBuildError(f"CASE_SPEC_{index}_SCHEMA_INVALID")

    case_id = raw.get("case_id")
    semantic_target = str(raw.get("semantic_target") or "").strip().upper()
    output_code = str(raw.get("output_code_identity") or "").strip().upper()
    seed = raw.get("seed")
    prompt = raw.get("prompt")
    scenario_sha = raw.get("scenario_family_sha256")
    lexical_sha = raw.get("lexical_family_sha256")
    codebook_sha = raw.get("codebook_family_sha256")

    if not isinstance(case_id, str) or not case_id.strip():
        raise EvidenceBuildError(f"CASE_SPEC_{index}_CASE_ID_REQUIRED")
    if semantic_target not in TARGETS:
        raise EvidenceBuildError(f"CASE_SPEC_{index}_SEMANTIC_TARGET_INVALID")
    if output_code not in CODES:
        raise EvidenceBuildError(f"CASE_SPEC_{index}_OUTPUT_CODE_INVALID")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise EvidenceBuildError(f"CASE_SPEC_{index}_INTEGER_SEED_REQUIRED")
    if not isinstance(prompt, str) or not prompt.strip():
        raise EvidenceBuildError(f"CASE_SPEC_{index}_PROMPT_REQUIRED")
    if raw.get("model_facing_target_identity_exposed") is not False:
        raise EvidenceBuildError(f"CASE_SPEC_{index}_MODEL_FACING_TARGET_IDENTITY_MUST_BE_FALSE")
    if raw.get("model_facing_explicit_semantic_labels") is not False:
        raise EvidenceBuildError(f"CASE_SPEC_{index}_MODEL_FACING_EXPLICIT_SEMANTIC_LABELS_MUST_BE_FALSE")

    lowered = prompt.lower()
    exposed = [label for label in FORBIDDEN_MODEL_FACING_LABELS if label in lowered]
    if exposed:
        raise EvidenceBuildError(
            f"CASE_SPEC_{index}_CANONICAL_SEMANTIC_LABEL_PRESENT_IN_PROMPT:{','.join(exposed)}"
        )

    for name, value in (
        ("scenario_family_sha256", scenario_sha),
        ("lexical_family_sha256", lexical_sha),
        ("codebook_family_sha256", codebook_sha),
    ):
        if not _sha256(value):
            raise EvidenceBuildError(f"CASE_SPEC_{index}_{name.upper()}_REQUIRED")

    declared_prompt_sha = raw.get("prompt_sha256")
    actual_prompt_sha = _prompt_sha(prompt)
    if declared_prompt_sha is not None and declared_prompt_sha != actual_prompt_sha:
        raise EvidenceBuildError(f"CASE_SPEC_{index}_PROMPT_SHA256_MISMATCH")

    return {
        "case_id": case_id.strip(),
        "seed": seed,
        "semantic_target": semantic_target,
        "output_code_identity": output_code,
        "prompt": prompt,
        "prompt_sha256": actual_prompt_sha,
        "scenario_family_sha256": scenario_sha,
        "lexical_family_sha256": lexical_sha,
        "codebook_family_sha256": codebook_sha,
        "model_facing_target_identity_exposed": False,
        "model_facing_explicit_semantic_labels": False,
        "split": split,
    }


def build_plan(split: str, case_specs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Freeze externally authored label-free cases; no internal prompt synthesis is allowed."""
    split = str(split).strip().upper()
    if split not in SPLITS:
        raise EvidenceBuildError(f"SPLIT_INVALID:{split}")
    if not isinstance(case_specs, list):
        raise EvidenceBuildError("EXTERNAL_LABEL_FREE_CASE_SPECS_REQUIRED")
    if len(case_specs) != 9:
        raise EvidenceBuildError("EXACTLY_NINE_EXTERNAL_CASE_SPECS_REQUIRED")

    normalized = [_normalize_case_spec(row, split=split, index=i) for i, row in enumerate(case_specs)]
    case_ids = [row["case_id"] for row in normalized]
    if len(set(case_ids)) != len(case_ids):
        raise EvidenceBuildError("EXTERNAL_CASE_IDS_MUST_BE_UNIQUE")
    prompt_hashes = [row["prompt_sha256"] for row in normalized]
    if len(set(prompt_hashes)) != len(prompt_hashes):
        raise EvidenceBuildError("EXTERNAL_PROMPTS_MUST_BE_UNIQUE")

    expected_factorial = {(target, code) for target in TARGETS for code in CODES}
    observed_factorial = {
        (row["semantic_target"], row["output_code_identity"]) for row in normalized
    }
    if observed_factorial != expected_factorial:
        raise EvidenceBuildError("EXTERNAL_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")

    scenario_ids = sorted({row["scenario_family_sha256"] for row in normalized})
    lexical_ids = sorted({row["lexical_family_sha256"] for row in normalized})
    codebook_ids = sorted({row["codebook_family_sha256"] for row in normalized})
    if len(scenario_ids) < 3:
        raise EvidenceBuildError("AT_LEAST_THREE_SCENARIO_FAMILIES_REQUIRED")
    if len(lexical_ids) < 3:
        raise EvidenceBuildError("AT_LEAST_THREE_LEXICAL_FAMILIES_REQUIRED")
    if len(codebook_ids) < 2:
        raise EvidenceBuildError("AT_LEAST_TWO_CODEBOOK_FAMILIES_REQUIRED")

    # Stronger than the global 3x3 requirement: every scenario family must contain all
    # semantic targets and all output codes, preventing domain/scenario identity from
    # becoming a proxy for the semantic class or code identity.
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in normalized:
        by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
    for scenario_sha, rows in by_scenario.items():
        if {row["semantic_target"] for row in rows} != set(TARGETS):
            raise EvidenceBuildError(f"SCENARIO_MISSING_SEMANTIC_TARGETS:{scenario_sha}")
        if {row["output_code_identity"] for row in rows} != set(CODES):
            raise EvidenceBuildError(f"SCENARIO_MISSING_OUTPUT_CODE_ROTATION:{scenario_sha}")
        if len({row["lexical_family_sha256"] for row in rows}) != 1:
            raise EvidenceBuildError(f"SCENARIO_MUST_USE_ONE_MATCHED_LEXICAL_FAMILY:{scenario_sha}")

    split_family_id = canonical_sha(
        {
            "schema": PLAN_SCHEMA,
            "split": split,
            "case_specs": [
                {key: row[key] for key in (
                    "case_id",
                    "seed",
                    "prompt_sha256",
                    "semantic_target",
                    "output_code_identity",
                    "scenario_family_sha256",
                    "lexical_family_sha256",
                    "codebook_family_sha256",
                )}
                for row in sorted(normalized, key=lambda x: x["case_id"])
            ],
        }
    )

    cases: list[dict[str, Any]] = []
    for row in normalized:
        case = {
            **row,
            "split_family_id": split_family_id,
        }
        case["case_identity_sha256"] = _case_identity(case)
        cases.append(case)

    plan_core = {
        "schema": PLAN_SCHEMA,
        "split": split,
        "split_family_id": split_family_id,
        "semantic_targets": list(TARGETS),
        "output_codes": list(CODES),
        "required_controls": list(CONTROLS),
        "case_identity_fields": list(CASE_IDENTITY_FIELDS),
        "case_count": len(cases),
        "scenario_family_sha256": scenario_ids,
        "lexical_family_sha256": lexical_ids,
        "codebook_family_sha256": codebook_ids,
        "external_case_specs_sha256": canonical_sha(case_specs),
        "model_facing_target_identity_exposed": False,
        "model_facing_explicit_semantic_labels": False,
        "cases": cases,
        "model_executed": False,
        "runtime_receipts_present": False,
    }
    return {**plan_core, "plan_sha256": canonical_sha(plan_core)}


def expand_runtime_cases(plan: dict[str, Any], candidate_key: str) -> list[dict[str, Any]]:
    _validate_plan(plan)
    if not isinstance(candidate_key, str) or not candidate_key.strip():
        raise EvidenceBuildError("CANDIDATE_KEY_REQUIRED")
    expanded: list[dict[str, Any]] = []
    for case in plan["cases"]:
        for control in CONTROLS:
            expanded.append({
                "case_id": case["case_id"],
                "case_identity_sha256": case["case_identity_sha256"],
                "seed": case["seed"],
                "semantic_target": case["semantic_target"],
                "target_label": case["output_code_identity"],
                "output_code_identity": case["output_code_identity"],
                "prompt": case["prompt"],
                "prompt_sha256": case["prompt_sha256"],
                "prompt_family": case["case_id"],
                "split_family_id": case["split_family_id"],
                "scenario_family_sha256": case["scenario_family_sha256"],
                "lexical_family_sha256": case["lexical_family_sha256"],
                "codebook_family_sha256": case["codebook_family_sha256"],
                "control": control,
                "candidate_key": candidate_key,
            })
    return expanded


def _validate_plan(plan: Any) -> None:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise EvidenceBuildError("PLAN_SCHEMA_INVALID")
    split = plan.get("split")
    if split not in SPLITS:
        raise EvidenceBuildError("PLAN_SPLIT_INVALID")
    cases = plan.get("cases")
    if not isinstance(cases, list) or len(cases) != 9:
        raise EvidenceBuildError("PLAN_EXACTLY_NINE_CASES_REQUIRED")
    if plan.get("runtime_receipts_present") is not False:
        raise EvidenceBuildError("PLAN_MUST_NOT_PRETEND_RUNTIME_RECEIPTS")
    if plan.get("model_executed") is not False:
        raise EvidenceBuildError("PLAN_MUST_BE_EXECUTION_FREE")
    if plan.get("model_facing_target_identity_exposed") is not False:
        raise EvidenceBuildError("PLAN_MODEL_FACING_TARGET_IDENTITY_MUST_BE_FALSE")
    if plan.get("model_facing_explicit_semantic_labels") is not False:
        raise EvidenceBuildError("PLAN_MODEL_FACING_EXPLICIT_SEMANTIC_LABELS_MUST_BE_FALSE")
    if plan.get("case_identity_fields") != list(CASE_IDENTITY_FIELDS):
        raise EvidenceBuildError("PLAN_CASE_IDENTITY_FIELDS_MISMATCH")

    observed = {(row.get("semantic_target"), row.get("output_code_identity")) for row in cases}
    expected = {(target, code) for target in TARGETS for code in CODES}
    if observed != expected:
        raise EvidenceBuildError("PLAN_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")
    family_ids = {row.get("split_family_id") for row in cases}
    if len(family_ids) != 1 or None in family_ids:
        raise EvidenceBuildError("PLAN_SINGLE_SPLIT_FAMILY_REQUIRED")
    case_ids = [row.get("case_id") for row in cases]
    if any(not isinstance(x, str) or not x for x in case_ids) or len(set(case_ids)) != len(case_ids):
        raise EvidenceBuildError("PLAN_UNIQUE_CASE_IDS_REQUIRED")
    prompt_hashes = [row.get("prompt_sha256") for row in cases]
    if any(not _sha256(x) for x in prompt_hashes) or len(set(prompt_hashes)) != len(prompt_hashes):
        raise EvidenceBuildError("PLAN_UNIQUE_PROMPT_SHA256_REQUIRED")

    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in cases:
        prompt = row.get("prompt")
        if not isinstance(prompt, str) or _prompt_sha(prompt) != row.get("prompt_sha256"):
            raise EvidenceBuildError(f"PLAN_PROMPT_SHA256_MISMATCH:{row.get('case_id')}")
        lowered = prompt.lower()
        if any(label in lowered for label in FORBIDDEN_MODEL_FACING_LABELS):
            raise EvidenceBuildError(f"PLAN_CANONICAL_SEMANTIC_LABEL_PRESENT:{row.get('case_id')}")
        if row.get("model_facing_target_identity_exposed") is not False:
            raise EvidenceBuildError(f"PLAN_TARGET_IDENTITY_EXPOSURE_ATTESTATION_FAIL:{row.get('case_id')}")
        if row.get("model_facing_explicit_semantic_labels") is not False:
            raise EvidenceBuildError(f"PLAN_EXPLICIT_SEMANTIC_LABEL_ATTESTATION_FAIL:{row.get('case_id')}")
        for field in ("scenario_family_sha256", "lexical_family_sha256", "codebook_family_sha256"):
            if not _sha256(row.get(field)):
                raise EvidenceBuildError(f"PLAN_{field.upper()}_INVALID:{row.get('case_id')}")
        if row.get("case_identity_sha256") != _case_identity(row):
            raise EvidenceBuildError(f"PLAN_CASE_IDENTITY_MISMATCH:{row.get('case_id')}")
        by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)

    if len(by_scenario) < 3:
        raise EvidenceBuildError("PLAN_AT_LEAST_THREE_SCENARIO_FAMILIES_REQUIRED")
    for scenario_sha, rows in by_scenario.items():
        if {row["semantic_target"] for row in rows} != set(TARGETS):
            raise EvidenceBuildError(f"PLAN_SCENARIO_MISSING_SEMANTIC_TARGETS:{scenario_sha}")
        if {row["output_code_identity"] for row in rows} != set(CODES):
            raise EvidenceBuildError(f"PLAN_SCENARIO_MISSING_OUTPUT_CODE_ROTATION:{scenario_sha}")
        if len({row["lexical_family_sha256"] for row in rows}) != 1:
            raise EvidenceBuildError(f"PLAN_SCENARIO_LEXICAL_FAMILY_MISMATCH:{scenario_sha}")


def bind_runtime_receipts(plan: dict[str, Any], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind observed per-control receipts only after exact planned-case identity replay."""
    _validate_plan(plan)
    if not isinstance(runtime_rows, list):
        raise EvidenceBuildError("RUNTIME_ROWS_LIST_REQUIRED")
    expected_by_case = {row["case_id"]: row for row in plan["cases"]}
    grouped: dict[str, dict[str, str]] = {case_id: {} for case_id in expected_by_case}
    for index, row in enumerate(runtime_rows):
        if not isinstance(row, dict):
            raise EvidenceBuildError(f"RUNTIME_ROW_{index}_OBJECT_REQUIRED")
        case_id = row.get("case_id")
        control = row.get("control")
        receipt = row.get("runtime_receipt_sha256")
        if case_id not in expected_by_case:
            raise EvidenceBuildError(f"RUNTIME_ROW_UNKNOWN_CASE:{case_id}")
        expected_case = expected_by_case[case_id]
        if row.get("case_identity_sha256") != expected_case["case_identity_sha256"]:
            raise EvidenceBuildError(f"RUNTIME_ROW_CASE_IDENTITY_MISMATCH:{case_id}")
        for field in CASE_IDENTITY_FIELDS:
            if row.get(field) != expected_case.get(field):
                raise EvidenceBuildError(f"RUNTIME_ROW_CASE_FIELD_MISMATCH:{case_id}:{field}")
        if row.get("prompt") != expected_case.get("prompt"):
            raise EvidenceBuildError(f"RUNTIME_ROW_PROMPT_MISMATCH:{case_id}")
        if _prompt_sha(str(row.get("prompt"))) != expected_case["prompt_sha256"]:
            raise EvidenceBuildError(f"RUNTIME_ROW_PROMPT_HASH_MISMATCH:{case_id}")
        if control not in CONTROLS:
            raise EvidenceBuildError(f"RUNTIME_ROW_UNKNOWN_CONTROL:{control}")
        if not _sha256(receipt):
            raise EvidenceBuildError(f"RUNTIME_ROW_RECEIPT_INVALID:{case_id}:{control}")
        if control in grouped[case_id]:
            raise EvidenceBuildError(f"RUNTIME_ROW_DUPLICATE_CONTROL:{case_id}:{control}")
        grouped[case_id][control] = receipt

    evidence_case_rows: list[dict[str, Any]] = []
    preregistration_case_rows: list[dict[str, Any]] = []
    for case_id in sorted(expected_by_case):
        case = expected_by_case[case_id]
        receipts = grouped[case_id]
        missing = [control for control in CONTROLS if control not in receipts]
        if missing:
            raise EvidenceBuildError(f"RUNTIME_CONTROLS_MISSING:{case_id}:{','.join(missing)}")
        evidence_row = {
            "case_id": case_id,
            "seed": case["seed"],
            "prompt_sha256": case["prompt_sha256"],
            "semantic_target": case["semantic_target"],
            "output_code_identity": case["output_code_identity"],
            "split_family_id": case["split_family_id"],
            "control_runtime_receipts": {control: receipts[control] for control in CONTROLS},
        }
        evidence_case_rows.append(evidence_row)
        preregistration_case_rows.append({
            "split": plan["split"],
            "case_id": case_id,
            "scenario_family_sha256": case["scenario_family_sha256"],
            "lexical_family_sha256": case["lexical_family_sha256"],
            "codebook_family_sha256": case["codebook_family_sha256"],
            "seed": case["seed"],
            "prompt_sha256": case["prompt_sha256"],
            "semantic_target": case["semantic_target"],
            "output_code_identity": case["output_code_identity"],
            "split_family_id": case["split_family_id"],
            "case_identity_sha256": case["case_identity_sha256"],
            "control_runtime_receipts": {control: receipts[control] for control in CONTROLS},
        })

    counts = {target: {code: 0 for code in CODES} for target in TARGETS}
    for row in evidence_case_rows:
        counts[row["semantic_target"]][row["output_code_identity"]] += 1
    split_name = str(plan["split"])
    material = {
        "schema": evidence_gate.FACTORIAL_RECEIPT_SCHEMA,
        "split_name": split_name,
        "split_family_id": plan["split_family_id"],
        "semantic_targets": list(TARGETS),
        "output_codes": list(CODES),
        "required_controls": list(CONTROLS),
        "factorial_counts": counts,
        "case_rows": sorted(
            evidence_case_rows,
            key=lambda row: (
                row["semantic_target"], row["output_code_identity"], row["case_id"], row["seed"]
            ),
        ),
    }
    receipt = canonical_sha(material)
    split = {
        "schema": BOUND_SPLIT_SCHEMA,
        "family_id": plan["split_family_id"],
        "semantic_targets": list(TARGETS),
        "semantic_target_counterbalanced": True,
        "label_mapping_counterbalanced": True,
        "semantic_target_x_output_code_factorial": True,
        "semantic_target_x_output_code_counts": counts,
        "case_rows": evidence_case_rows,
        "preregistration_case_rows": preregistration_case_rows,
        "semantic_factorial_receipt_sha256": receipt,
        "source_plan_sha256": plan["plan_sha256"],
        "runtime_case_identity_binding": True,
        "model_facing_target_identity_exposed": False,
        "model_facing_explicit_semantic_labels": False,
    }
    derived, failures = evidence_gate.derive_split_receipt(split, split_name)
    if failures or derived is None or derived["receipt_sha256"] != receipt:
        raise EvidenceBuildError("EVIDENCE_GATE_SELF_CHECK_FAILED:" + ",".join(failures))
    return split


def build_interaction_binding(
    holdout_factorial_receipt_sha256: str,
    metric_definition_sha256: str,
    analysis_implementation_sha256: str,
    analysis_result_receipt_sha256: str,
) -> dict[str, Any]:
    analysis = {
        "factorial_receipt_sha256": holdout_factorial_receipt_sha256,
        "metric_definition_sha256": metric_definition_sha256,
        "analysis_implementation_sha256": analysis_implementation_sha256,
        "analysis_result_receipt_sha256": analysis_result_receipt_sha256,
        "treatment_control_identities": list(CONTROLS),
    }
    material = {
        "schema": evidence_gate.INTERACTION_BINDING_SCHEMA,
        "holdout_factorial_receipt_sha256": holdout_factorial_receipt_sha256,
        "metric_definition_sha256": metric_definition_sha256.lower(),
        "analysis_implementation_sha256": analysis_implementation_sha256.lower(),
        "analysis_result_receipt_sha256": analysis_result_receipt_sha256.lower(),
        "treatment_control_identities": list(CONTROLS),
    }
    analysis["analysis_binding_sha256"] = canonical_sha(material)
    bound, failures = evidence_gate.derive_interaction_binding(analysis, holdout_factorial_receipt_sha256)
    if failures or bound is None:
        raise EvidenceBuildError("INTERACTION_BINDING_SELF_CHECK_FAILED:" + ",".join(failures))
    return analysis


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", required=True, choices=SPLITS)
    ap.add_argument("--cases-json", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    raw = json.loads(Path(args.cases_json).read_text(encoding="utf-8"))
    case_specs = raw.get("cases") if isinstance(raw, dict) else raw
    plan = build_plan(args.split, case_specs)
    text = json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
