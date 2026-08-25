#!/usr/bin/env python3
"""Derivation-bound Trigger-2 semantic-Hyperposition candidate gate v3.

This successor binds one integrated candidate episode to the converged formal-world v3
reference semantics. The row cannot supply relation/target labels as authority: the gate
recomputes formal world -> derived targets/relations -> event/dependence-aware state update
-> task-local resolution and requires exact agreement.

Synthetic task resolution remains METHOD_ONLY candidate supervision. It is intentionally
separate from legacy causal/evidence ``hyperposition.resolution_status`` and cannot mint
canonical dataset, world truth, J-Space, runtime, HCU, EntityOS, effect or training credit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_GATE/v3"
EPISODE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EPISODE/v3"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_gate = _load_sibling(
    "entityos_hcu_trainingtrace_candidate_gate_v1.py",
    "trigger2_base_candidate_gate_v1_for_shp_v3",
)
lab = _load_sibling(
    "trigger2_hyperposition_reference_labelers_v3.py",
    "trigger2_hyperposition_reference_labelers_v3_for_gate",
)


def _file_sha256(path: str | Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def _digest(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def reference_binding(world: Any) -> dict[str, Any]:
    return {
        "labeler_schema": lab.SCHEMA,
        "labeler_source_sha256": _file_sha256(lab.__file__),
        "world_sha256": _digest(world),
    }


def _result(failures: list[str]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "candidate_admission_pass": not failures,
        "failures": failures,
        "gate_source_sha256": _file_sha256(__file__),
        "labeler_source_sha256": _file_sha256(lab.__file__),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "Exact-source candidate validation only. Deterministic synthetic task labels are "
            "METHOD_ONLY and remain distinct from admitted causal/world evidence."
        ),
    }


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")

    base = base_gate.adjudicate(row)
    if not base.get("candidate_admission_pass"):
        failures.extend("BASE_GATE:" + x for x in base.get("failures", []))
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("ROW_CANONICAL_TRUTH_MUST_BE_FALSE")
    if row.get("direct_effect_authority") is not False:
        failures.append("ROW_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if row.get("evidence_class") not in {"METHOD_ONLY", "SYNTHETIC_HARD_NEGATIVE"}:
        failures.append("FORMAL_SYNTHETIC_EPISODE_MUST_REMAIN_METHOD_OR_HARD_NEGATIVE")
    if "hyperposition" in row:
        failures.append("LEGACY_CAUSAL_HYPERPOSITION_FIELD_FORBIDDEN_ON_FORMAL_SYNTHETIC_EPISODE")
    if row.get("audit_metadata_model_visible") is not False:
        failures.append("AUDIT_METADATA_MUST_NOT_BE_MODEL_VISIBLE")
    if row.get("training_admission_scope") != "CANDIDATE_SOURCE_ONLY":
        failures.append("TRAINING_ADMISSION_SCOPE_MUST_BE_CANDIDATE_SOURCE_ONLY")

    ep = row.get("formal_hyperposition")
    if not isinstance(ep, dict):
        failures.append("FORMAL_HYPERPOSITION_EPISODE_OBJECT_REQUIRED")
        return _result(failures)
    if ep.get("schema") != EPISODE_SCHEMA:
        failures.append("FORMAL_HYPERPOSITION_EPISODE_SCHEMA_MISMATCH")
    if ep.get("canonical_truth_allowed") is not False:
        failures.append("EPISODE_CANONICAL_TRUTH_MUST_BE_FALSE")
    if ep.get("direct_effect_authority") is not False:
        failures.append("EPISODE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")

    world = ep.get("world")
    state_before = ep.get("state_before")
    event = ep.get("event")
    expected_binding = reference_binding(world)
    if ep.get("reference_binding") != expected_binding:
        failures.append("REFERENCE_SOURCE_OR_WORLD_BINDING_MISMATCH")

    derived = lab.derive_relations(world, state_before, event)
    if not derived.get("pass"):
        failures.append("REFERENCE_DERIVATION_REJECTED:" + str(derived.get("failure")))
        return _result(failures)
    if ep.get("derived_target_branch_ids") != derived.get("target_branch_ids"):
        failures.append("DERIVED_TARGET_BRANCH_IDS_MISMATCH")
    if ep.get("derived_relations") != derived.get("relations"):
        failures.append("DERIVED_RELATIONS_MISMATCH")
    if ep.get("derivation_receipt") != derived.get("derivation_receipt"):
        failures.append("DERIVATION_RECEIPT_MISMATCH")

    updated = lab.u_state(world, state_before, event)
    if not updated.get("pass"):
        failures.append("REFERENCE_UPDATE_REJECTED:" + str(updated.get("failure")))
        return _result(failures)
    if ep.get("state_after") != updated.get("state_after"):
        failures.append("STATE_AFTER_MISMATCH")
    if ep.get("update_receipt") != updated.get("updates"):
        failures.append("UPDATE_RECEIPT_MISMATCH")
    if ep.get("independent_evidence_credit") != updated.get("independent_evidence_credit"):
        failures.append("INDEPENDENT_EVIDENCE_CREDIT_MISMATCH")
    if ep.get("nonindependence_reasons") != updated.get("nonindependence_reasons"):
        failures.append("NONINDEPENDENCE_REASONS_MISMATCH")
    if ep.get("born_branch_ids") != updated.get("born_branch_ids"):
        failures.append("BORN_BRANCH_IDS_MISMATCH")

    resolved = lab.d_resolve(world, updated["state_after"])
    if not resolved.get("pass"):
        failures.append("REFERENCE_RESOLUTION_REJECTED:" + str(resolved.get("failure")))
    elif ep.get("task_resolution") != resolved.get("resolution"):
        failures.append("TASK_RESOLUTION_MISMATCH")

    # The model-visible target may teach the task-local transition, but these audit labels
    # and exact hashes remain outside model-visible input/target by contract.
    if ep.get("model_visible_contains_reference_hashes") is not False:
        failures.append("REFERENCE_HASHES_MUST_NOT_BE_MODEL_VISIBLE")
    if ep.get("model_visible_contains_branch_ids") is not False:
        failures.append("BRANCH_IDS_MUST_BE_NUISANCE_NOT_MODEL_VISIBLE_LABELS")

    return _result(failures)


def adjudicate_permutation_group(rows: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(rows, list) or len(rows) < 2:
        return {
            "schema": SCHEMA + "/PERMUTATION_GROUP",
            "permutation_group_pass": False,
            "failures": ["PERMUTATION_GROUP_REQUIRES_AT_LEAST_TWO_ROWS"],
            "training_credit_minted": False,
        }

    cases = []
    for idx, row in enumerate(rows):
        result = adjudicate(row)
        if not result.get("candidate_admission_pass"):
            failures.append(f"ROW_{idx}_FAILS_GATE")
        ep = row.get("formal_hyperposition", {}) if isinstance(row, dict) else {}
        case = ep.get("permutation_case")
        if not isinstance(case, dict):
            failures.append(f"ROW_{idx}_PERMUTATION_CASE_REQUIRED")
            case = {}
        cases.append((row, ep, case))

    group_ids = {case.get("group_id") for _, _, case in cases}
    semantic_keys = {case.get("semantic_equivalence_key") for _, _, case in cases}
    target_keys = {case.get("target_semantic_key") for _, _, case in cases}
    permutation_ids = [case.get("permutation_id") for _, _, case in cases]
    if len(group_ids) != 1 or None in group_ids:
        failures.append("PERMUTATION_GROUP_ID_MISMATCH")
    if len(semantic_keys) != 1 or None in semantic_keys:
        failures.append("SEMANTIC_EQUIVALENCE_KEY_MISMATCH")
    if len(target_keys) != 1 or None in target_keys:
        failures.append("TARGET_SEMANTIC_KEY_MISMATCH")
    if len(permutation_ids) != len(set(permutation_ids)) or any(x is None for x in permutation_ids):
        failures.append("PERMUTATION_IDS_MUST_BE_UNIQUE")

    before = [ep.get("state_before") for _, ep, _ in cases]
    after = [ep.get("state_after") for _, ep, _ in cases]
    for other in before[1:]:
        chk = lab.permutation_invariance_check(before[0], other)
        if not chk.get("pass") or not chk.get("invariant"):
            failures.append("STATE_BEFORE_NOT_SEMANTICALLY_PERMUTATION_INVARIANT")
    for other in after[1:]:
        chk = lab.permutation_invariance_check(after[0], other)
        if not chk.get("pass") or not chk.get("invariant"):
            failures.append("STATE_AFTER_NOT_SEMANTICALLY_PERMUTATION_INVARIANT")

    statuses = {ep.get("task_resolution", {}).get("status") for _, ep, _ in cases}
    if len(statuses) != 1:
        failures.append("TASK_RESOLUTION_STATUS_CHANGED_ACROSS_PERMUTATION")

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA + "/PERMUTATION_GROUP",
        "permutation_group_pass": not failures,
        "failures": failures,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }
