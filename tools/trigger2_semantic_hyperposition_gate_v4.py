#!/usr/bin/env python3
"""Byte-grounded semantic-Hyperposition candidate gate v4.

This is a strict successor layer over ``trigger2_semantic_hyperposition_gate_v3.py``.
V3 proves the evaluator-side causal chain by recomputing formal-world -> relations ->
state update -> task-local resolution. V4 adds the owner's cross-cutting training-data
requirement: the Hyperposition state that the model is supposed to operate in must be
present in the *actual model-visible prompt/target bytes*, not only in hidden audit
metadata.

V4 therefore deterministically projects the v3 formal episode into an opaque-local-ref
model view and requires exact canonical serialization in the prompt and target. Stable
branch IDs and source hashes remain evaluator-only; branch-local semantic state,
evidence/provenance/dependence, falsifiers, scope, epistemic status, active test semantics
and observed event are model-visible.

SOURCE/DATA-DESIGN GATE ONLY. It mints no canonical dataset, truth, runtime, J-Space,
HCU, EntityOS, effect, provider, or training credit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_GATE/v4"
INPUT_SCHEMA = "XENO_MODEL_VISIBLE_SEMANTIC_HYPERPOSITION_INPUT/v1"
TARGET_SCHEMA = "XENO_MODEL_VISIBLE_SEMANTIC_HYPERPOSITION_TARGET/v1"
INPUT_BEGIN = "<SEMANTIC_HYPERPOSITION_INPUT>"
INPUT_END = "</SEMANTIC_HYPERPOSITION_INPUT>"
TARGET_BEGIN = "<SEMANTIC_HYPERPOSITION_TARGET>"
TARGET_END = "</SEMANTIC_HYPERPOSITION_TARGET>"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v3 = _load_sibling(
    "trigger2_semantic_hyperposition_gate_v3.py",
    "trigger2_semantic_hyperposition_gate_v3_for_v4",
)


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(obj: Any) -> str:
    return sha256(_canon(obj).encode("utf-8")).hexdigest()


def _clean_evidence(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    # Exact event identity and provenance/dependence remain model-visible because the
    # model must learn replay/ancestry independence. Evaluator source hashes/receipts do not.
    allowed = (
        "event_id",
        "evidence_event_id",
        "correlation_ancestry_id",
        "causal_ancestry_id",
        "independence_group",
        "payload_key",
        "provenance",
        "epistemic_type",
        "test_id",
        "observed_outcome",
        "derived_relation",
        "relation",
        "independent_credit",
    )
    return {k: item[k] for k in allowed if k in item}


def _branch_view(branch: dict[str, Any], ref: str, active_test_id: str | None) -> dict[str, Any]:
    predictions = branch.get("predictions", {})
    active_prediction = predictions.get(active_test_id) if isinstance(predictions, dict) and active_test_id else None
    return {
        "ref": ref,
        "v": branch.get("v"),
        "K": branch.get("K"),
        "E_plus": [_clean_evidence(x) for x in (branch.get("E_plus") or [])],
        "E_minus": [_clean_evidence(x) for x in (branch.get("E_minus") or [])],
        "F": [_clean_evidence(x) for x in (branch.get("F") or [])],
        "T": branch.get("T"),
        "A": branch.get("A"),
        "sigma": branch.get("sigma"),
        "projection_visibility": branch.get("projection_visibility"),
        "active_test_prediction": active_prediction,
    }


def _ref_map(state_before: dict[str, Any], state_after: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    counter = 0
    for state in (state_before, state_after):
        branches = state.get("branches", []) if isinstance(state, dict) else []
        for branch in branches if isinstance(branches, list) else []:
            if not isinstance(branch, dict):
                continue
            bid = branch.get("branch_id")
            if isinstance(bid, str) and bid not in mapping:
                mapping[bid] = f"h{counter}"
                counter += 1
    return mapping


def model_input_projection(ep: dict[str, Any]) -> dict[str, Any]:
    world = ep.get("world") if isinstance(ep.get("world"), dict) else {}
    before = ep.get("state_before") if isinstance(ep.get("state_before"), dict) else {}
    after = ep.get("state_after") if isinstance(ep.get("state_after"), dict) else {}
    event = ep.get("event") if isinstance(ep.get("event"), dict) else {}
    test_id = event.get("test_id") if isinstance(event.get("test_id"), str) else None
    mapping = _ref_map(before, after)
    test_spec = world.get("tests", {}).get(test_id, {}) if isinstance(world.get("tests"), dict) and test_id else {}
    branches = []
    for branch in before.get("branches", []) if isinstance(before.get("branches"), list) else []:
        if isinstance(branch, dict) and isinstance(branch.get("branch_id"), str):
            branches.append(_branch_view(branch, mapping[branch["branch_id"]], test_id))
    visible_event = {
        k: event[k]
        for k in (
            "correlation_ancestry_id",
            "independence_group",
            "payload_key",
            "provenance",
            "epistemic_type",
            "test_id",
            "observed_outcome",
            "independence_qualified",
        )
        if k in event
    }
    return {
        "schema": INPUT_SCHEMA,
        "query_id": before.get("query_id"),
        "context": world.get("context"),
        "active_test": {
            "test_id": test_id,
            "allowed_outcomes": test_spec.get("allowed_outcomes"),
            "mismatch_effect": test_spec.get("mismatch_effect"),
        },
        "branches": branches,
        "event": visible_event,
        "rules": {
            "majority_is_truth": False,
            "recurrence_is_evidence": False,
            "projection_is_deletion": False,
            "canonical_truth_minted_by_task_resolution": False,
        },
    }


def model_target_projection(ep: dict[str, Any]) -> dict[str, Any]:
    before = ep.get("state_before") if isinstance(ep.get("state_before"), dict) else {}
    after = ep.get("state_after") if isinstance(ep.get("state_after"), dict) else {}
    event = ep.get("event") if isinstance(ep.get("event"), dict) else {}
    test_id = event.get("test_id") if isinstance(event.get("test_id"), str) else None
    mapping = _ref_map(before, after)
    branches = []
    for branch in after.get("branches", []) if isinstance(after.get("branches"), list) else []:
        if isinstance(branch, dict) and isinstance(branch.get("branch_id"), str):
            branches.append(_branch_view(branch, mapping[branch["branch_id"]], test_id))
    resolution = ep.get("task_resolution")
    if not isinstance(resolution, dict):
        resolution = {}
    visible_resolution = dict(resolution)
    for field in ("selected_branch_id", "resolved_branch_id", "winner_branch_id"):
        if field in visible_resolution:
            raw = visible_resolution.pop(field)
            visible_resolution[field.replace("_id", "_ref")] = mapping.get(raw) if isinstance(raw, str) else None
    return {
        "schema": TARGET_SCHEMA,
        "query_id": after.get("query_id", before.get("query_id")),
        "branches": branches,
        "task_resolution": visible_resolution,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }


def render_input_block(ep: dict[str, Any]) -> str:
    return INPUT_BEGIN + "\n" + _canon(model_input_projection(ep)) + "\n" + INPUT_END


def render_target_block(ep: dict[str, Any]) -> str:
    return TARGET_BEGIN + "\n" + _canon(model_target_projection(ep)) + "\n" + TARGET_END


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    base = v3.adjudicate(row)
    if not base.get("candidate_admission_pass"):
        failures.extend("V3:" + x for x in base.get("failures", []))
    if not isinstance(row, dict):
        row = {}
    ep = row.get("formal_hyperposition") if isinstance(row.get("formal_hyperposition"), dict) else {}
    expected_input = model_input_projection(ep)
    expected_target = model_target_projection(ep)
    expected_input_block = render_input_block(ep)
    expected_target_block = render_target_block(ep)

    prompt = row.get("prompt")
    target = row.get("target")
    if not isinstance(prompt, str) or expected_input_block not in prompt:
        failures.append("MODEL_VISIBLE_HYPERPOSITION_INPUT_BYTES_MISSING_OR_MISMATCH")
    if not isinstance(target, str) or expected_target_block not in target:
        failures.append("MODEL_VISIBLE_HYPERPOSITION_TARGET_BYTES_MISSING_OR_MISMATCH")

    binding = row.get("model_visible_hyperposition_binding")
    if not isinstance(binding, dict):
        failures.append("MODEL_VISIBLE_HYPERPOSITION_BINDING_REQUIRED")
    else:
        if binding.get("schema") != "XENO_MODEL_VISIBLE_HYPERPOSITION_BINDING/v1":
            failures.append("MODEL_VISIBLE_HYPERPOSITION_BINDING_SCHEMA_MISMATCH")
        if binding.get("input_sha256") != _sha(expected_input):
            failures.append("MODEL_VISIBLE_HYPERPOSITION_INPUT_HASH_MISMATCH")
        if binding.get("target_sha256") != _sha(expected_target):
            failures.append("MODEL_VISIBLE_HYPERPOSITION_TARGET_HASH_MISMATCH")
        if binding.get("stable_branch_ids_model_visible") is not False:
            failures.append("STABLE_BRANCH_IDS_MUST_NOT_BE_MODEL_VISIBLE")
        if binding.get("reference_hashes_model_visible") is not False:
            failures.append("REFERENCE_HASHES_MUST_NOT_BE_MODEL_VISIBLE")

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "candidate_admission_pass": not failures,
        "failures": failures,
        "v3_candidate_admission_pass": bool(base.get("candidate_admission_pass")),
        "model_input_sha256": _sha(expected_input),
        "model_target_sha256": _sha(expected_target),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": "V3 causal candidate validation plus exact model-visible Hyperposition byte binding; still candidate/source design only.",
    }


def adjudicate_permutation_group(rows: Any) -> dict[str, Any]:
    failures: list[str] = []
    base = v3.adjudicate_permutation_group(rows)
    if not base.get("permutation_group_pass"):
        failures.extend("V3:" + x for x in base.get("failures", []))
    if not isinstance(rows, list) or len(rows) < 2:
        failures.append("PERMUTATION_GROUP_REQUIRES_AT_LEAST_TWO_ROWS")
        rows = []
    outcomes = []
    for index, row in enumerate(rows):
        result = adjudicate(row)
        if not result.get("candidate_admission_pass"):
            failures.append(f"ROW_{index}_FAILS_V4")
        ep = row.get("formal_hyperposition", {}) if isinstance(row, dict) else {}
        target = model_target_projection(ep if isinstance(ep, dict) else {})
        # Compare semantic target with opaque refs removed, so branch renaming/order cannot
        # create a false difference. V3 separately checks state permutation invariance.
        normalized = json.loads(_canon(target))
        for branch in normalized.get("branches", []):
            branch.pop("ref", None)
        normalized["branches"] = sorted(normalized.get("branches", []), key=lambda b: _canon(b))
        res = normalized.get("task_resolution", {})
        if isinstance(res, dict):
            for key in list(res):
                if key.endswith("_ref"):
                    res.pop(key, None)
        outcomes.append(_canon(normalized))
    if outcomes and len(set(outcomes)) != 1:
        failures.append("MODEL_VISIBLE_SEMANTIC_TARGET_CHANGED_ACROSS_BRANCH_PERMUTATION")
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA + "/PERMUTATION_GROUP",
        "permutation_group_pass": not failures,
        "failures": failures,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }
