#!/usr/bin/env python3
"""Reconstruct target-specific internal-state control from per-case heldout measurements.

This companion is deliberately narrower than the existing v11/v12 deconfound/scope gates.
It closes one remaining evidence-authenticity gap: a caller cannot satisfy an abstract-state
claim merely by asserting that a dual-readout or causal-matrix check passed. The gate binds
an independent downstream probe and reconstructs target-specific internal-state and behavioral
margins from the exact nine counterbalanced heldout cases, baseline plus all three commands.

For every heldout case, all three applied commands are scored against the SAME requested
semantic target. This same-case competition is essential: scoring each command against its
own target would not falsify a generic multi-direction actuator.

It runs no model and mints no semantic/runtime/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any

SCHEMA = "CLAY_TRIGGER1_INTERNAL_STATE_SPECIFICITY_ATTESTATION/v2"
VERDICT_SCHEMA = "CLAY_TRIGGER1_INTERNAL_STATE_SPECIFICITY_GATE/v2"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _margin(scores: dict[str, float], target: str) -> float:
    others = [name for name in TARGETS if name != target]
    return float(scores[target]) - 0.5 * (float(scores[others[0]]) + float(scores[others[1]]))


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    root = candidate if isinstance(candidate, dict) else {}
    att = root.get("internal_state_specificity_attestation")
    if not isinstance(att, dict):
        att = {}
        failures.append("INTERNAL_STATE_SPECIFICITY_ATTESTATION_REQUIRED")
    if att.get("schema") != SCHEMA:
        failures.append("ATTESTATION_SCHEMA_INVALID")

    for field in ("abstract_state_challenge_sha256", "v12_candidate_sha256", "protocol_sha256"):
        if not _sha(att.get(field)):
            failures.append(f"{field.upper()}_REQUIRED")
    if att.get("frozen_before_holdout") is not True:
        failures.append("PROTOCOL_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if att.get("thresholds_selected_on") != "CALIBRATION_ONLY":
        failures.append("THRESHOLDS_MUST_BE_CALIBRATION_ONLY")

    probe = att.get("independent_probe") if isinstance(att.get("independent_probe"), dict) else {}
    if probe.get("uses_output_tokens") is not False:
        failures.append("PROBE_MUST_NOT_USE_OUTPUT_TOKENS")
    if probe.get("uses_steering_basis_families") is not False:
        failures.append("PROBE_MUST_NOT_USE_STEERING_BASIS_FAMILIES")
    if probe.get("fit_split") != "CALIBRATION_ONLY":
        failures.append("PROBE_MUST_BE_FIT_ON_CALIBRATION_ONLY")
    if not isinstance(probe.get("steering_layer"), int) or not isinstance(probe.get("probe_layer"), int) or probe.get("probe_layer", 0) <= probe.get("steering_layer", 0):
        failures.append("INDEPENDENT_DOWNSTREAM_PROBE_LAYER_REQUIRED")
    if not _sha(probe.get("probe_definition_sha256")):
        failures.append("PROBE_DEFINITION_SHA256_REQUIRED")

    commands = att.get("commands") if isinstance(att.get("commands"), dict) else {}
    if set(commands) != set(TARGETS):
        failures.append("EXACT_THREE_COMMANDS_REQUIRED")
    command_ids: dict[str, str] = {}
    vector_ids: dict[str, str] = {}
    for semantic in TARGETS:
        command = commands.get(semantic) if isinstance(commands.get(semantic), dict) else {}
        cid = command.get("command_id_sha256")
        vid = command.get("semantic_vector_sha256")
        if not _sha(cid):
            failures.append(f"COMMAND_ID_REQUIRED:{semantic}")
        else:
            command_ids[semantic] = cid
        if not _sha(vid):
            failures.append(f"SEMANTIC_VECTOR_ID_REQUIRED:{semantic}")
        else:
            vector_ids[semantic] = vid
        if command.get("nuisance_residualized") is not True:
            failures.append(f"NUISANCE_RESIDUALIZATION_REQUIRED:{semantic}")
    if len(command_ids) == 3 and len(set(command_ids.values())) != 3:
        failures.append("COMMAND_IDS_MUST_BE_DISTINCT")
    if len(vector_ids) == 3 and len(set(vector_ids.values())) != 3:
        failures.append("VECTOR_IDS_MUST_BE_DISTINCT")

    thresholds = att.get("thresholds") if isinstance(att.get("thresholds"), dict) else {}
    specs = {
        "min_internal_match_vs_baseline": lambda x: x > 0,
        "min_internal_match_vs_best_nonmatching": lambda x: x > 0,
        "min_behavior_match_vs_best_nonmatching": lambda x: x > 0,
        "max_nonmatching_behavior_uplift_vs_baseline": lambda x: x >= 0,
        "max_off_target_internal_drift": lambda x: x >= 0,
    }
    for key, predicate in specs.items():
        value = thresholds.get(key)
        if not _finite(value) or not predicate(float(value)):
            failures.append(f"THRESHOLD_INVALID:{key}")

    rows = att.get("holdout_rows") if isinstance(att.get("holdout_rows"), list) else []
    if len(rows) != 9:
        failures.append("EXACTLY_NINE_HELDOUT_CASES_REQUIRED")
    pair_counts: Counter[tuple[str, str]] = Counter()
    seen: set[str] = set()
    metrics = {target: [] for target in TARGETS}

    for index, row in enumerate(rows):
        prefix = f"CASE_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        case_id = row.get("case_id")
        target = str(row.get("semantic_target") or "").upper()
        code = str(row.get("output_code_identity") or "").upper()
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            failures.append(f"{prefix}_UNIQUE_CASE_ID_REQUIRED")
        else:
            seen.add(case_id)
        if target not in TARGETS or code not in CODES:
            failures.append(f"{prefix}_TARGET_CODE_INVALID")
        else:
            pair_counts[(target, code)] += 1
        for field in ("case_identity_sha256", "prompt_sha256"):
            if not _sha(row.get(field)):
                failures.append(f"{prefix}_{field.upper()}_REQUIRED")

        baseline = row.get("baseline") if isinstance(row.get("baseline"), dict) else {}
        base_scores = baseline.get("internal_scores") if isinstance(baseline.get("internal_scores"), dict) else {}
        if set(base_scores) != set(TARGETS) or not all(_finite(base_scores.get(t)) for t in TARGETS):
            failures.append(f"{prefix}_BASELINE_INTERNAL_SCORES_REQUIRED")
            continue
        if not _finite(baseline.get("target_output_score")):
            failures.append(f"{prefix}_BASELINE_OUTPUT_SCORE_REQUIRED")
            continue
        for field in ("runtime_receipt_sha256", "probe_receipt_sha256", "output_metric_receipt_sha256"):
            if not _sha(baseline.get(field)):
                failures.append(f"{prefix}_BASELINE_{field.upper()}_REQUIRED")

        apps = row.get("applications") if isinstance(row.get("applications"), dict) else {}
        if set(apps) != set(TARGETS):
            failures.append(f"{prefix}_EXACT_THREE_APPLICATIONS_REQUIRED")
            continue
        valid = True
        by_command: dict[str, dict[str, float]] = {}
        for applied in TARGETS:
            app = apps.get(applied) if isinstance(apps.get(applied), dict) else {}
            if app.get("command_id_sha256") != command_ids.get(applied):
                failures.append(f"{prefix}_COMMAND_ID_MISMATCH:{applied}")
                valid = False
            if app.get("semantic_vector_sha256") != vector_ids.get(applied):
                failures.append(f"{prefix}_VECTOR_ID_MISMATCH:{applied}")
                valid = False
            scores = app.get("internal_scores") if isinstance(app.get("internal_scores"), dict) else {}
            if set(scores) != set(TARGETS) or not all(_finite(scores.get(t)) for t in TARGETS):
                failures.append(f"{prefix}_INTERNAL_SCORES_REQUIRED:{applied}")
                valid = False
                continue
            if not _finite(app.get("target_output_score")) or not _finite(app.get("off_target_internal_drift")):
                failures.append(f"{prefix}_FINITE_EFFECT_METRICS_REQUIRED:{applied}")
                valid = False
                continue
            for field in ("runtime_receipt_sha256", "probe_receipt_sha256", "output_metric_receipt_sha256"):
                if not _sha(app.get(field)):
                    failures.append(f"{prefix}_{field.upper()}_REQUIRED:{applied}")
            # Crucially score every applied command toward THIS CASE'S requested target.
            by_command[applied] = {
                "internal_shift_toward_case_target": _margin(scores, target) - _margin(base_scores, target) if target in TARGETS else float("nan"),
                "output": float(app["target_output_score"]),
                "off_target": float(app["off_target_internal_drift"]),
            }
        if not valid or target not in TARGETS or len(by_command) != 3:
            continue

        base_output = float(baseline["target_output_score"])
        match = by_command[target]
        nonmatching = [by_command[name] for name in TARGETS if name != target]
        metrics[target].append({
            "internal_match_vs_baseline": match["internal_shift_toward_case_target"],
            "internal_match_vs_best_nonmatching": match["internal_shift_toward_case_target"] - max(x["internal_shift_toward_case_target"] for x in nonmatching),
            "behavior_match_vs_best_nonmatching": match["output"] - max(x["output"] for x in nonmatching),
            "max_nonmatching_behavior_uplift_vs_baseline": max(x["output"] - base_output for x in nonmatching),
            "max_off_target_internal_drift": max(x["off_target"] for x in by_command.values()),
        })

    expected = {(target, code) for target in TARGETS for code in CODES}
    if set(pair_counts) != expected or any(pair_counts[pair] != 1 for pair in expected):
        failures.append("HOLDOUT_TARGET_X_CODE_MUST_BE_EXACT_ONE_EACH")

    summary: dict[str, Any] = {}
    threshold_ready = all(_finite(thresholds.get(key)) for key in specs)
    for target in TARGETS:
        records = metrics[target]
        if len(records) != 3:
            failures.append(f"EXACT_THREE_VALID_CASES_PER_TARGET_REQUIRED:{target}")
            continue
        values = {
            "min_internal_match_vs_baseline": min(x["internal_match_vs_baseline"] for x in records),
            "min_internal_match_vs_best_nonmatching": min(x["internal_match_vs_best_nonmatching"] for x in records),
            "min_behavior_match_vs_best_nonmatching": min(x["behavior_match_vs_best_nonmatching"] for x in records),
            "max_nonmatching_behavior_uplift_vs_baseline": max(x["max_nonmatching_behavior_uplift_vs_baseline"] for x in records),
            "max_off_target_internal_drift": max(x["max_off_target_internal_drift"] for x in records),
            "case_count": len(records),
        }
        passed = bool(
            threshold_ready
            and values["min_internal_match_vs_baseline"] >= float(thresholds["min_internal_match_vs_baseline"])
            and values["min_internal_match_vs_best_nonmatching"] >= float(thresholds["min_internal_match_vs_best_nonmatching"])
            and values["min_behavior_match_vs_best_nonmatching"] >= float(thresholds["min_behavior_match_vs_best_nonmatching"])
            and values["max_nonmatching_behavior_uplift_vs_baseline"] <= float(thresholds["max_nonmatching_behavior_uplift_vs_baseline"])
            and values["max_off_target_internal_drift"] <= float(thresholds["max_off_target_internal_drift"])
        )
        values["pass"] = passed
        summary[target] = values
        if not passed:
            failures.append(f"TARGET_SPECIFIC_INTERNAL_STATE_THRESHOLD_FAILED:{target}")

    material = {
        "schema": SCHEMA,
        "abstract_state_challenge_sha256": att.get("abstract_state_challenge_sha256"),
        "v12_candidate_sha256": att.get("v12_candidate_sha256"),
        "protocol_sha256": att.get("protocol_sha256"),
        "independent_probe": probe,
        "commands": commands,
        "thresholds": thresholds,
        "holdout_rows": sorted(rows, key=lambda x: str(x.get("case_id")) if isinstance(x, dict) else ""),
        "summary": summary,
    }
    passed = not failures
    return {
        "schema": VERDICT_SCHEMA,
        "internal_state_specificity_candidate": passed,
        "generic_compliance_rejected_by_same_case_competition": passed,
        "abstract_state_challenge_sha256": att.get("abstract_state_challenge_sha256") if _sha(att.get("abstract_state_challenge_sha256")) else None,
        "v12_candidate_sha256": att.get("v12_candidate_sha256") if _sha(att.get("v12_candidate_sha256")) else None,
        "internal_state_analysis_sha256": canonical_sha(material),
        "target_summary": summary,
        "failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS reconstructs target-specific downstream internal-state and behavioral margins from the exact nine heldout target×code cases using an independent calibration-only probe and same-case competition among all three nuisance-residualized commands. It does not authenticate external runtime receipt bytes or mint semantic/model/system credit."
        ),
    }
