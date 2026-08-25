#!/usr/bin/env python3
"""Authority-resolved generation-provenance pilot gate for Trigger-2.

The caller supplies only a pinned case id, deterministic parameters and model-visible prompt.
Evaluator subjects are reconstructed from the repository-pinned trusted generator authority;
caller-supplied world/registry/event/state/receipt overrides are rejected. The reconstructed
subjects are then delegated to the retained epistemic-preupdate -> state-history proof lane.

Pilot/component candidate only. PASS mints no canonical truth/effect, dataset, runtime,
J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_GENERATION_PROVENANCE_PILOT_GATE/v1"
GENERATION_RECEIPT_SCHEMA = "XENO_SYNTHETIC_GENERATION_RECEIPT/v1"
ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = "tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY_V1.json"
GUARD_PATH = "tools/trigger2_hyperposition_epistemic_preupdate_guard_v1.py"
JCS_PATH = "the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"

FORBIDDEN_CALLER_FIELDS = frozenset({
    "generator_repo_path", "generator_source_sha256", "materials_manifest",
    "formal_task_world_evaluator_only", "event_dependence_registry_evaluator_only",
    "synthetic_test_event_evaluator_only", "hyperposition_state_before_evaluator_only",
    "hyperposition_genesis_state_evaluator_only", "synthetic_event_history_evaluator_only",
    "event_digest_registry_evaluator_only", "discriminator_execution_receipts_evaluator_only",
    "typed_observation_evidence_receipts_evaluator_only", "v3_reference_target_evaluator_only",
    "state_history_reference_target_evaluator_only", "source_binding", "generation_receipt",
})


def _load_path(path: str, name: str):
    p = ROOT / path
    spec = importlib.util.spec_from_file_location(name, p)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


generator = _load_path(GENERATOR_PATH, "trigger2_trusted_generator_for_gp_gate")
guard = _load_path(GUARD_PATH, "trigger2_epistemic_guard_for_gp_gate")
state_gate = guard.base
base = state_gate.base
lab = state_gate.lab
jcs = _load_path(JCS_PATH, "entityos_jcs_for_trigger2_gp_gate")


def _bytes_sha256(path: str) -> str:
    return sha256((ROOT / path).read_bytes()).hexdigest()


def _jcs_sha256(obj: Any) -> str:
    return sha256(jcs.canonicalize(obj)).hexdigest()


def _authority() -> dict[str, Any]:
    data = json.loads((ROOT / AUTHORITY_PATH).read_text(encoding="utf-8"))
    if data.get("schema") != "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY/v1":
        raise ValueError("TRUSTED_GENERATOR_AUTHORITY_SCHEMA_MISMATCH")
    return data


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "trusted deterministic generation-provenance pilot component only",
    }
    out.update(extra)
    return out


def _verify_generator_and_reconstruct(case_id: Any, parameters: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    try:
        authority = _authority()
    except Exception as exc:
        return None, None, ["AUTHORITY_LOAD_FAILED:" + type(exc).__name__]
    gen_auth = authority.get("generator")
    if not isinstance(gen_auth, dict):
        return authority, None, ["GENERATOR_AUTHORITY_REQUIRED"]
    if gen_auth.get("repo_path") != GENERATOR_PATH:
        failures.append("EXPECTED_GENERATOR_PATH_MISMATCH")
    if gen_auth.get("source_sha256") != _bytes_sha256(GENERATOR_PATH):
        failures.append("EXPECTED_GENERATOR_SOURCE_SHA256_MISMATCH")
    if gen_auth.get("generator_schema_or_version") != getattr(generator, "GENERATOR_SCHEMA", None):
        failures.append("EXPECTED_GENERATOR_SCHEMA_MISMATCH")
    cases = authority.get("allowed_cases")
    case = cases.get(case_id) if isinstance(cases, dict) and isinstance(case_id, str) else None
    if not isinstance(case, dict):
        failures.append("GENERATION_CASE_NOT_AUTHORIZED")
        return authority, None, failures
    expected_parameters = case.get("deterministic_parameters")
    if parameters != expected_parameters:
        failures.append("GENERATION_PARAMETERS_MISMATCH")
    if _jcs_sha256(expected_parameters) != case.get("deterministic_parameters_jcs_sha256"):
        failures.append("AUTHORITY_PARAMETER_DIGEST_MISMATCH")
    materials = case.get("materials_manifest")
    if _jcs_sha256(materials) != case.get("materials_manifest_jcs_sha256"):
        failures.append("AUTHORITY_MATERIALS_DIGEST_MISMATCH")
    if failures:
        return authority, None, failures
    try:
        subjects = generator.build_subjects(case_id, deepcopy(parameters))
    except Exception as exc:
        return authority, None, ["TRUSTED_GENERATOR_INVOCATION_FAILED:" + type(exc).__name__]
    expected = case.get("subjects", {})
    actual_subjects = {
        "formal_world_jcs_sha256": _jcs_sha256(subjects.get("formal_world")),
        "event_dependence_registry_jcs_sha256": _jcs_sha256(subjects.get("event_dependence_registry")),
        "event_jcs_sha256": _jcs_sha256(subjects.get("event")),
        "state_before_jcs_sha256": _jcs_sha256(subjects.get("state_before")),
    }
    if actual_subjects != expected:
        failures.append("RECONSTRUCTED_SUBJECT_DIGEST_MISMATCH")
    scope = case.get("semantic_scope", {})
    if subjects.get("formal_world", {}).get("world_id") != scope.get("world_id"):
        failures.append("SEMANTIC_SCOPE_WORLD_ID_MISMATCH")
    if subjects.get("state_before", {}).get("query_id") != scope.get("query_id"):
        failures.append("SEMANTIC_SCOPE_QUERY_ID_MISMATCH")
    if subjects.get("event", {}).get("event_id") != scope.get("event_id"):
        failures.append("SEMANTIC_SCOPE_EVENT_ID_MISMATCH")
    return authority, subjects, failures


def _generation_receipt(authority: dict[str, Any], subjects: dict[str, Any], case_id: str) -> dict[str, Any]:
    case = authority["allowed_cases"][case_id]
    invocation_core = {
        "case_id": case_id,
        "deterministic_parameters_jcs_sha256": case["deterministic_parameters_jcs_sha256"],
        "materials_manifest_jcs_sha256": case["materials_manifest_jcs_sha256"],
    }
    receipt = {
        "schema": GENERATION_RECEIPT_SCHEMA,
        "generator": deepcopy(authority["generator"]),
        "invocation": {"invocation_id": "sha256:" + _jcs_sha256(invocation_core), **invocation_core},
        "subjects": deepcopy(case["subjects"]),
        "semantic_scope": deepcopy(case["semantic_scope"]),
        "authority_fences": {
            "canonical_truth_allowed": False, "direct_effect_authority": False,
            "training_eligible": False, "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
        },
    }
    receipt["receipt_jcs_sha256"] = _jcs_sha256(receipt)
    return receipt


def _lower_row(subjects: dict[str, Any], prompt: str) -> dict[str, Any]:
    world = deepcopy(subjects["formal_world"])
    event = deepcopy(subjects["event"])
    before = deepcopy(subjects["state_before"])
    genesis = deepcopy(subjects["genesis_state"])
    history = deepcopy(subjects["event_history"])
    event_sha = state_gate.event_semantic_sha256(event)
    digest_registry = {"schema": state_gate.DIGEST_REGISTRY_SCHEMA, "events": {event["event_id"]: event_sha}}
    ordering = lab.u_test_order(world, before, [event["test_id"]])
    if not ordering.get("pass"):
        raise ValueError("DISCRIMINATOR_ORDERING_REJECTED")
    order = ordering["ordering"][0]
    disc = {
        "schema": state_gate.DISCRIMINATOR_RECEIPT_SCHEMA,
        "event_id": event["event_id"], "test_id": event["test_id"],
        "observed_outcome": deepcopy(event["observed_outcome"]),
        "event_semantic_sha256": event_sha, "world_sha256": state_gate._world_sha256(world),
        "admissible": True, "executed": True,
        "execution_receipt_id": "trusted-generator:" + event_sha,
        "separated_live_pairs": order["separated_live_pairs"],
        "separates_all_live_pairs": order["separates_all_live_pairs"],
    }
    binding = base.current_source_binding(GENERATOR_PATH)
    if not binding.get("pass"):
        raise ValueError("BASE_SOURCE_BINDING_REJECTED")
    independence = base.derive_independence(world, before, event)
    if not independence.get("pass") and any(x != "CALLER_INDEPENDENCE_FLAG_MISMATCH_DERIVED_VALUE" for x in independence.get("failures", [])):
        raise ValueError("BASE_INDEPENDENCE_REJECTED")
    ev2 = deepcopy(event)
    ev2["independence_qualified"] = bool(independence.get("derived_independence_qualified", False))
    update = lab.u_state(world, before, ev2)
    resolution = lab.d_resolve(world, update["state_after"])
    v3_target = {
        "state_after": update.get("state_after"), "updates": update.get("updates"),
        "derivation_receipt": update.get("derivation_receipt"),
        "independent_evidence_credit": update.get("independent_evidence_credit"),
        "nonindependence_reasons": update.get("nonindependence_reasons"),
        "task_resolution": resolution.get("resolution"),
    }
    row = {
        "schema": base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL", "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE", "canonical_truth_allowed": False,
        "direct_effect_authority": False, "training_eligible": False,
        "model_visible_fields": ["prompt"], "prompt": prompt,
        "split": "TRAIN", "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_binding": {k: v for k, v in binding.items() if k != "pass"},
        "formal_task_world_evaluator_only": world,
        "hyperposition_state_before_evaluator_only": before,
        "hyperposition_genesis_state_evaluator_only": genesis,
        "synthetic_event_history_evaluator_only": history,
        "synthetic_test_event_evaluator_only": event,
        "event_digest_registry_evaluator_only": digest_registry,
        "discriminator_execution_receipts_evaluator_only": [disc],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "v3_reference_target_evaluator_only": v3_target,
    }
    dry = state_gate.adjudicate(row)
    target = dry.get("recomputed_target")
    if not isinstance(target, dict):
        raise ValueError("STATE_HISTORY_TARGET_RECOMPUTE_FAILED")
    row["state_history_reference_target_evaluator_only"] = target
    return row


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    forbidden = sorted(FORBIDDEN_CALLER_FIELDS & set(row))
    if forbidden:
        return _result(["CALLER_EVALUATOR_OVERRIDE_FORBIDDEN:" + x for x in forbidden], trusted_generator_invoked=False)
    case_id = row.get("generation_case_id")
    parameters = row.get("generation_parameters_evaluator_only")
    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return _result(["MODEL_VISIBLE_PROMPT_REQUIRED"], trusted_generator_invoked=False)
    authority, subjects, failures = _verify_generator_and_reconstruct(case_id, parameters)
    if failures or not isinstance(authority, dict) or not isinstance(subjects, dict):
        return _result(failures or ["TRUSTED_RECONSTRUCTION_FAILED"], trusted_generator_invoked=True)
    receipt = _generation_receipt(authority, subjects, case_id)
    try:
        lower = _lower_row(subjects, prompt)
        lower_result = guard.adjudicate(lower)
    except Exception as exc:
        return _result(["RETAINED_GATE_PREPARATION_FAILED:" + type(exc).__name__], generation_receipt=receipt, trusted_generator_invoked=True)
    failures = [] if lower_result.get("pass") else ["RETAINED_GATE:" + str(x) for x in lower_result.get("failures", [])]
    semantic_target_sha = _jcs_sha256(lower.get("state_history_reference_target_evaluator_only"))
    return _result(
        failures,
        trusted_generator_invoked=True,
        authority_path=AUTHORITY_PATH,
        expected_generator_path=GENERATOR_PATH,
        generation_receipt=receipt,
        retained_gate_result=lower_result,
        reconstructed_subjects_model_visible=False,
        caller_selects_generator_identity=False,
        caller_supplies_evaluator_subjects=False,
        semantic_target_jcs_sha256=semantic_target_sha,
    )
