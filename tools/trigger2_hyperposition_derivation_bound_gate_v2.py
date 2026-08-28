#!/usr/bin/env python3
"""v3-bound fail-closed pre-admission gate for Trigger-2 Hyperposition rows.

This gate closes the remaining positive-label provenance root around the converged
formal-world Hyperposition reference labeler v3. It does not trust caller relation,
target, winner or independent-evidence labels. Instead it:
- binds the actual local v3 labeler bytes and the declared generator bytes;
- requires evaluator-only formal-world event registry/dependence metadata;
- derives independence qualification from immutable prior event identities plus declared
  formal-world dependency edges, then overwrites the event flag before recomputation;
- recomputes v3 formal relation -> update -> task-local resolution exactly;
- keeps synthetic task resolution distinct from generic causal RESOLVED_BY_EVIDENCE;
- permits only prompt in model-visible fields.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS does not write the canonical dataset and cannot
mint truth/effect/runtime/J-Space/HCU/EntityOS/provider/training credit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_DERIVATION_BOUND_GATE/v2"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v3.py"
LABELER_REPO_PATH = "tools/" + LABELER_FILENAME
DEPENDENCE_SCHEMA = "XENO_SYNTHETIC_EVENT_DEPENDENCE_REGISTRY/v1"


def _load_labeler():
    path = Path(__file__).resolve().with_name(LABELER_FILENAME)
    spec = importlib.util.spec_from_file_location("trigger2_hp_labeler_v3_bound", path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load converged Hyperposition labeler v3")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lab = _load_labeler()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_repo_path(repo_path: Any) -> Path | None:
    if not isinstance(repo_path, str) or not repo_path or repo_path.startswith("/"):
        return None
    candidate = (_repo_root() / repo_path).resolve()
    root = _repo_root().resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def current_source_binding(generator_repo_path: Any) -> dict[str, Any]:
    here = Path(__file__).resolve().parent
    generator = _safe_repo_path(generator_repo_path)
    if generator is None:
        return {"pass": False, "failure": "GENERATOR_REPO_PATH_INVALID_OR_MISSING"}
    labeler = here / LABELER_FILENAME
    return {
        "pass": True,
        "labeler_path": LABELER_REPO_PATH,
        "labeler_sha256": _sha256(labeler),
        "labeler_schema": lab.SCHEMA,
        "generator_path": str(generator_repo_path),
        "generator_sha256": _sha256(generator),
    }


def _records(state: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(state, dict):
        return out
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for item in branch.get(field, []) or []:
                if isinstance(item, dict):
                    out.append(item)
    return out


def derive_independence(world: Any, state: Any, event: Any) -> dict[str, Any]:
    """Derive independent-evidence qualification from formal registry + prior history."""
    failures: list[str] = []
    if not isinstance(world, dict):
        return {"pass": False, "failures": ["FORMAL_WORLD_OBJECT_REQUIRED"]}
    registry = world.get("event_dependence_registry")
    if not isinstance(registry, dict) or registry.get("schema") != DEPENDENCE_SCHEMA:
        return {"pass": False, "failures": ["EVENT_DEPENDENCE_REGISTRY_REQUIRED"]}
    events = registry.get("events")
    if not isinstance(events, dict):
        return {"pass": False, "failures": ["EVENT_DEPENDENCE_REGISTRY_EVENTS_REQUIRED"]}
    if not isinstance(event, dict) or not isinstance(event.get("event_id"), str) or not event.get("event_id"):
        return {"pass": False, "failures": ["EVENT_ID_REQUIRED_FOR_DEPENDENCE_DERIVATION"]}
    entry = events.get(event["event_id"])
    if not isinstance(entry, dict):
        return {"pass": False, "failures": ["EVENT_NOT_IN_FORMAL_DEPENDENCE_REGISTRY"]}

    bound_fields = (
        "correlation_ancestry_id", "independence_group", "payload_key",
        "provenance", "test_id", "observed_outcome",
    )
    for key in bound_fields:
        if entry.get(key) != event.get(key):
            failures.append("EVENT_REGISTRY_BINDING_MISMATCH:" + key)

    depends = entry.get("depends_on_event_ids")
    if not isinstance(depends, list) or not all(isinstance(x, str) and x for x in depends):
        failures.append("DEPENDENCY_EVENT_IDS_LIST_REQUIRED")
        depends = []

    prior = _records(state)
    prior_ids = {str(x.get("event_id")) for x in prior if x.get("event_id") is not None}
    missing_dependencies = sorted(set(depends) - prior_ids)
    if missing_dependencies:
        failures.append("DEPENDENCY_REFERENCE_NOT_IN_PRIOR_STATE:" + ",".join(missing_dependencies))

    reasons: list[str] = []
    if event["event_id"] in prior_ids:
        reasons.append("EXACT_EVENT_REPLAY")
    if any(x.get("correlation_ancestry_id") == event.get("correlation_ancestry_id") for x in prior):
        reasons.append("CORRELATION_ANCESTRY_REUSE")
    if any(x.get("independence_group") == event.get("independence_group") for x in prior):
        reasons.append("INDEPENDENCE_GROUP_REUSE")
    if any(x.get("payload_key") == event.get("payload_key") for x in prior):
        reasons.append("PAYLOAD_REPACKAGING")
    if depends:
        reasons.append("FORMAL_DEPENDENCY_EDGE_PRESENT")

    expected = not reasons and not failures
    if event.get("independence_qualified") is not expected:
        failures.append("CALLER_INDEPENDENCE_FLAG_MISMATCH_DERIVED_VALUE")

    return {
        "pass": not failures,
        "failures": sorted(set(failures)),
        "derived_independence_qualified": expected,
        "nonindependence_reasons": sorted(set(reasons)),
        "registry_event_id": event["event_id"],
        "dependence_source": "FORMAL_WORLD_EVENT_REGISTRY_PLUS_PRIOR_STATE_EVENT_IDENTITIES",
        "caller_boolean_is_authoritative": False,
    }


def _result(failures: list[str], *, recomputed: Any = None, source_binding: Any = None, independence: Any = None) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "source_binding": source_binding,
        "independence_derivation": independence,
        "recomputed_target": recomputed,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "v3-bound synthetic candidate pre-admission only; no canonical dataset/model/runtime credit.",
    }


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("evidence_class") != "SYNTHETIC_DETERMINISTIC_LABEL":
        failures.append("SYNTHETIC_DETERMINISTIC_LABEL_REQUIRED")
    if row.get("reality_level") not in {"R2", "R3"}:
        failures.append("SYNTHETIC_REALITY_LEVEL_REQUIRED")
    if row.get("fact_status") not in {"UNKNOWN", "NOT_APPLICABLE"}:
        failures.append("SYNTHETIC_ROW_CANNOT_ASSERT_FACT")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("CANONICAL_TRUTH_ALLOWED_MUST_BE_FALSE")
    if row.get("direct_effect_authority") is not False:
        failures.append("DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if row.get("training_eligible") is not False:
        failures.append("TRAINING_ELIGIBLE_MUST_REMAIN_FALSE_AT_PRE_ADMISSION_GATE")
    if row.get("model_visible_fields") != ["prompt"]:
        failures.append("ONLY_PROMPT_MAY_BE_MODEL_VISIBLE")
    if not isinstance(row.get("prompt"), str) or not row.get("prompt"):
        failures.append("PROMPT_REQUIRED")
    if row.get("split") not in {"TRAIN", "VALIDATION", "HOLDOUT"}:
        failures.append("SPLIT_INVALID")
    if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
        failures.append("FAMILY_PROVENANCE_SPLIT_UNIT_REQUIRED")
    if row.get("selected_using_holdout") is not False:
        failures.append("HOLDOUT_SELECTION_FORBIDDEN")

    generic_hp = row.get("hyperposition")
    if isinstance(generic_hp, dict) and generic_hp.get("resolution_status") == "RESOLVED_BY_EVIDENCE":
        failures.append("SYNTHETIC_TASK_RESOLUTION_CANNOT_USE_CAUSAL_RESOLVED_BY_EVIDENCE")

    requested_binding = row.get("source_binding")
    generator_path = requested_binding.get("generator_path") if isinstance(requested_binding, dict) else None
    actual_binding = current_source_binding(generator_path)
    if not actual_binding.get("pass"):
        failures.append(str(actual_binding.get("failure")))
    elif requested_binding != {k: v for k, v in actual_binding.items() if k != "pass"}:
        failures.append("SOURCE_BINDING_MISMATCH_ACTUAL_LOCAL_BYTES")

    world = row.get("formal_task_world_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    before = row.get("hyperposition_state_before_evaluator_only")
    claimed = row.get("v3_reference_target_evaluator_only")
    for value, code in (
        (world, "FORMAL_TASK_WORLD_REQUIRED"),
        (event, "SYNTHETIC_TEST_EVENT_REQUIRED"),
        (before, "HYPERPOSITION_STATE_BEFORE_REQUIRED"),
        (claimed, "V3_REFERENCE_TARGET_REQUIRED"),
    ):
        if value is None:
            failures.append(code)

    independence = None
    recomputed = None
    if world is not None and event is not None and before is not None:
        independence = derive_independence(world, before, event)
        if not independence.get("pass"):
            failures.extend("INDEPENDENCE:" + x for x in independence.get("failures", []))
        event_for_lab = deepcopy(event)
        event_for_lab["independence_qualified"] = bool(independence.get("derived_independence_qualified", False))
        try:
            update = lab.u_state(world, before, event_for_lab)
        except Exception as exc:
            failures.append("V3_UPDATE_RECOMPUTE_EXCEPTION:" + type(exc).__name__)
        else:
            if not update.get("pass"):
                failures.append("V3_UPDATE_RECOMPUTE_REJECTED:" + str(update.get("failure")))
            else:
                try:
                    resolution = lab.d_resolve(world, update["state_after"])
                except Exception as exc:
                    failures.append("V3_RESOLUTION_RECOMPUTE_EXCEPTION:" + type(exc).__name__)
                else:
                    if not resolution.get("pass"):
                        failures.append("V3_RESOLUTION_RECOMPUTE_REJECTED:" + str(resolution.get("failure")))
                    recomputed = {
                        "state_after": update.get("state_after"),
                        "updates": update.get("updates"),
                        "derivation_receipt": update.get("derivation_receipt"),
                        "independent_evidence_credit": update.get("independent_evidence_credit"),
                        "nonindependence_reasons": update.get("nonindependence_reasons"),
                        "task_resolution": resolution.get("resolution"),
                    }
                    if isinstance(recomputed["task_resolution"], dict):
                        status = recomputed["task_resolution"].get("status")
                        if status not in {"UNRESOLVED", "RESOLVED_WITHIN_SYNTHETIC_WORLD"}:
                            failures.append("SYNTHETIC_TASK_RESOLUTION_TYPE_INVALID")
                    if claimed is not None and claimed != recomputed:
                        failures.append("CLAIMED_TARGET_DOES_NOT_MATCH_RECOMPUTED_V3_CHAIN")

    return _result(
        failures,
        recomputed=recomputed,
        source_binding={k: v for k, v in actual_binding.items() if k != "pass"},
        independence=independence,
    )
