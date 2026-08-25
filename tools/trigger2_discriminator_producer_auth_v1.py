#!/usr/bin/env python3
"""Repository-authorized deterministic discriminator producer for Trigger-2 A02.

This component closes a narrow producer-authenticity gap for the currently pinned,
empty-history SYNTHETIC_PROOF pilot. It is callable only after the generation-provenance
gate has passed. Producer identity and policy come from a repository authority manifest,
not from the candidate row. The component executes the retained u_test_order function,
derives admissibility from the pinned policy, constructs a deterministic synthetic
execution receipt, and rejects any row-carried receipt that differs from that output.

PASS is source/candidate pre-admission evidence only. It mints zero canonical truth,
effect, dataset, runtime, J-Space, HCU, EntityOS, BASE, or training credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_DETERMINISTIC_DISCRIMINATOR_PRODUCER_AUTH/v1"
AUTHORITY_SCHEMA = "CLAY_TRIGGER2_DETERMINISTIC_DISCRIMINATOR_PRODUCER_AUTHORITY/v1"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_DETERMINISTIC_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
EVENT_BINDING_SCHEMA = "XENO_WORLD_HISTORY_SCOPED_EVENT_BINDING/v1"
EXPECTED_UPSTREAM_GENERATION_SCHEMA = "CLAY_TRIGGER2_GENERATION_PROVENANCE_GATE/v1"
EXPECTED_REPO_PATH = "tools/trigger2_discriminator_producer_auth_v1.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = _load_sibling(
    "trigger2_hyperposition_state_history_proof_gate_v1.py",
    "trigger2_state_history_for_discriminator_producer_auth_v1",
)


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _source_sha256() -> str:
    return sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _authority() -> dict[str, Any]:
    return json.loads((_repo_root() / AUTHORITY_PATH).read_text(encoding="utf-8"))


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "row_carried_executed_boolean_is_authority": False,
        "row_carried_admissible_boolean_is_authority": False,
        "repository_authority_required": True,
        "synthetic_execution_only": True,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "base_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
    out.update(extra)
    return out


def _world_history_binding(world: Any, history_events: Any, event: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or not isinstance(history_events, list) or not isinstance(event, dict):
        raise ValueError("WORLD_HISTORY_EVENT_OBJECTS_REQUIRED")
    event_digest = history.event_semantic_sha256(event)
    if not isinstance(event_digest, str):
        raise ValueError("EVENT_SEMANTIC_DIGEST_REQUIRED")
    world_digest = history._world_sha256(world)
    if not isinstance(world_digest, str):
        raise ValueError("WORLD_DIGEST_REQUIRED")
    ordered_history = []
    for idx, prior in enumerate(history_events):
        prior_digest = history.event_semantic_sha256(prior)
        if not isinstance(prior_digest, str):
            raise ValueError(f"HISTORY_EVENT_SEMANTIC_DIGEST_REQUIRED:{idx}")
        ordered_history.append(
            {
                "index": idx,
                "event_id": prior.get("event_id"),
                "event_semantic_sha256": prior_digest,
            }
        )
    ordered_history_digest = _digest(ordered_history)
    preimage = {
        "world_sha256": world_digest,
        "ordered_history_sha256": ordered_history_digest,
        "event_semantic_sha256": event_digest,
    }
    return {
        "schema": EVENT_BINDING_SCHEMA,
        "event_id": event.get("event_id"),
        "event_semantic_sha256": event_digest,
        "world_sha256": world_digest,
        "ordered_history_sha256": ordered_history_digest,
        "scoped_event_id": "t2scope:" + _digest(preimage),
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def _load_case(authority: Any, row: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(authority, dict) or authority.get("schema") != AUTHORITY_SCHEMA:
        return None, ["DISCRIMINATOR_PRODUCER_AUTHORITY_SCHEMA_MISMATCH"]

    producer = authority.get("producer")
    if not isinstance(producer, dict):
        return None, ["DISCRIMINATOR_PRODUCER_AUTHORITY_OBJECT_REQUIRED"]
    if producer.get("repo_path") != EXPECTED_REPO_PATH:
        failures.append("DISCRIMINATOR_PRODUCER_REPO_PATH_AUTHORITY_MISMATCH")
    if producer.get("producer_schema_or_version") != SCHEMA:
        failures.append("DISCRIMINATOR_PRODUCER_SCHEMA_AUTHORITY_MISMATCH")
    if producer.get("source_sha256") != _source_sha256():
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_SHA256_AUTHORITY_MISMATCH")

    fences = authority.get("authority_fences")
    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
    if fences != expected_fences:
        failures.append("DISCRIMINATOR_PRODUCER_AUTHORITY_FENCES_INVALID")

    case_id = row.get("generation_case_id_evaluator_only")
    cases = authority.get("allowed_cases")
    if not isinstance(cases, dict) or case_id not in cases:
        return None, failures + ["DISCRIMINATOR_PRODUCER_CASE_NOT_AUTHORIZED"]
    case = cases[case_id]
    if not isinstance(case, dict):
        return None, failures + ["DISCRIMINATOR_PRODUCER_CASE_OBJECT_REQUIRED"]
    return case, sorted(set(failures))


def _derive_receipt(
    authority: dict[str, Any],
    case: dict[str, Any],
    world: dict[str, Any],
    state_before: dict[str, Any],
    event: dict[str, Any],
    event_binding: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], dict[str, Any] | None]:
    failures: list[str] = []
    policy = case.get("policy")
    if not isinstance(policy, dict):
        return None, ["DISCRIMINATOR_POLICY_REQUIRED"], None

    if world.get("world_id") != case.get("world_id"):
        failures.append("DISCRIMINATOR_WORLD_ID_AUTHORITY_MISMATCH")
    if event.get("event_id") != case.get("event_id"):
        failures.append("DISCRIMINATOR_EVENT_ID_AUTHORITY_MISMATCH")
    if event.get("epistemic_type") != policy.get("required_epistemic_type"):
        failures.append("DISCRIMINATOR_EPISTEMIC_TYPE_POLICY_MISMATCH")
    if event.get("canonical_truth_allowed") is not False:
        failures.append("DISCRIMINATOR_EVENT_CANONICAL_TRUTH_FORBIDDEN")
    if event.get("direct_effect_authority") is not False:
        failures.append("DISCRIMINATOR_EVENT_DIRECT_EFFECT_FORBIDDEN")

    test_id = event.get("test_id")
    if not isinstance(test_id, str) or not test_id:
        return None, failures + ["DISCRIMINATOR_TEST_ID_REQUIRED"], None
    if test_id != case.get("test_id"):
        failures.append("DISCRIMINATOR_TEST_ID_AUTHORITY_MISMATCH")

    formal_spec = case.get("formal_discriminator_spec")
    if not isinstance(formal_spec, dict):
        return None, failures + ["FORMAL_DISCRIMINATOR_SPEC_AUTHORITY_REQUIRED"], None
    if _digest(formal_spec) != case.get("formal_discriminator_spec_sha256"):
        failures.append("FORMAL_DISCRIMINATOR_SPEC_AUTHORITY_DIGEST_MISMATCH")
    world_test = world.get("tests", {}).get(test_id) if isinstance(world.get("tests"), dict) else None
    if world_test != formal_spec:
        failures.append("FORMAL_DISCRIMINATOR_SPEC_MISMATCH")

    allowed_outcomes = policy.get("allowed_outcomes")
    if not isinstance(allowed_outcomes, list) or event.get("observed_outcome") not in allowed_outcomes:
        failures.append("DISCRIMINATOR_OUTCOME_NOT_POLICY_ADMISSIBLE")

    try:
        ordering = history.lab.u_test_order(world, state_before, [test_id])
    except Exception as exc:
        return None, failures + ["DISCRIMINATOR_EXECUTION_EXCEPTION:" + type(exc).__name__], None
    if not isinstance(ordering, dict) or not ordering.get("pass"):
        return None, failures + ["DISCRIMINATOR_EXECUTION_REJECTED"], ordering if isinstance(ordering, dict) else None
    rows = ordering.get("ordering")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        return None, failures + ["DISCRIMINATOR_EXECUTION_RESULT_INVALID"], ordering
    ordering_row = rows[0]
    separated = ordering_row.get("separated_live_pairs")
    full_coverage = ordering_row.get("separates_all_live_pairs")

    minimum = policy.get("min_separated_live_pairs")
    if not isinstance(minimum, int) or minimum < 1:
        failures.append("DISCRIMINATOR_POLICY_MIN_COVERAGE_INVALID")
    elif not isinstance(separated, int) or separated < minimum:
        failures.append("DISCRIMINATOR_POLICY_MIN_COVERAGE_NOT_MET")
    if policy.get("require_complete_live_pair_coverage") is not True:
        failures.append("DISCRIMINATOR_POLICY_MUST_REQUIRE_COMPLETE_COVERAGE")
    elif full_coverage is not True:
        failures.append("DISCRIMINATOR_COMPLETE_LIVE_PAIR_COVERAGE_NOT_MET")

    if failures:
        return None, sorted(set(failures)), ordering

    producer_binding = {
        "schema": SCHEMA,
        "authority_path": AUTHORITY_PATH,
        "authority_sha256": _digest(authority),
        "producer_repo_path": EXPECTED_REPO_PATH,
        "producer_source_sha256": _source_sha256(),
        "generation_case_id": case.get("case_id"),
        "world_scoped_event_id": event_binding.get("scoped_event_id"),
        "world_sha256": event_binding.get("world_sha256"),
        "ordered_history_sha256": event_binding.get("ordered_history_sha256"),
        "event_semantic_sha256": event_binding.get("event_semantic_sha256"),
        "state_before_sha256": _digest(state_before),
        "formal_discriminator_spec_sha256": case.get("formal_discriminator_spec_sha256"),
        "test_id": test_id,
        "observed_outcome": deepcopy(event.get("observed_outcome")),
        "ordering_result_sha256": _digest(ordering),
    }
    execution_receipt_id = "t2disc:" + _digest(producer_binding)
    receipt = {
        "schema": history.DISCRIMINATOR_RECEIPT_SCHEMA,
        "execution_receipt_id": execution_receipt_id,
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": deepcopy(event.get("observed_outcome")),
        "event_semantic_sha256": event_binding.get("event_semantic_sha256"),
        "world_sha256": event_binding.get("world_sha256"),
        "admissible": True,
        "executed": True,
        "synthetic_execution": True,
        "execution_scope": "DETERMINISTIC_EVALUATOR_ONLY",
        "separated_live_pairs": separated,
        "separates_all_live_pairs": True,
        "producer": producer_binding,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    return receipt, [], ordering


def authenticate_and_sanitize(
    row: Any,
    upstream_generation_result: Any,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"]), None
    failures: list[str] = []

    if (
        not isinstance(upstream_generation_result, dict)
        or upstream_generation_result.get("schema") != EXPECTED_UPSTREAM_GENERATION_SCHEMA
        or upstream_generation_result.get("pass") is not True
        or upstream_generation_result.get("generation_provenance_pass") is not True
    ):
        return _result(["UPSTREAM_GENERATION_PROVENANCE_PASS_REQUIRED"]), None

    try:
        authority = _authority()
    except Exception as exc:
        return _result(["DISCRIMINATOR_PRODUCER_AUTHORITY_LOAD_FAILED:" + type(exc).__name__]), None

    case, authority_failures = _load_case(authority, row)
    failures.extend(authority_failures)
    if not isinstance(case, dict):
        return _result(failures), None

    history_events = row.get("synthetic_event_history_evaluator_only")
    if history_events != []:
        failures.append("DISCRIMINATOR_PRODUCER_V1_REQUIRES_EMPTY_HISTORY")
    state_before = row.get("hyperposition_state_before_evaluator_only")
    genesis = row.get("hyperposition_genesis_state_evaluator_only")
    if not isinstance(state_before, dict):
        failures.append("DISCRIMINATOR_STATE_BEFORE_REQUIRED")
    if genesis != state_before:
        failures.append("EMPTY_HISTORY_GENESIS_MUST_EQUAL_STATE_BEFORE")
    world = row.get("formal_task_world_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    if not isinstance(world, dict):
        failures.append("DISCRIMINATOR_WORLD_REQUIRED")
    if not isinstance(event, dict):
        failures.append("DISCRIMINATOR_EVENT_REQUIRED")

    event_binding = None
    derived_receipt = None
    ordering = None
    if not failures:
        try:
            event_binding = _world_history_binding(world, history_events, event)
        except Exception as exc:
            failures.append("WORLD_HISTORY_EVENT_BINDING_FAILED:" + type(exc).__name__ + ":" + str(exc))
        else:
            derived_receipt, derivation_failures, ordering = _derive_receipt(
                authority, case, world, state_before, event, event_binding
            )
            failures.extend(derivation_failures)

    if isinstance(derived_receipt, dict):
        claimed_receipts = row.get("discriminator_execution_receipts_evaluator_only")
        if claimed_receipts not in (None, [], [derived_receipt]):
            failures.append("ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT")
        claimed_binding = row.get("world_history_scoped_event_binding_evaluator_only")
        if claimed_binding not in (None, event_binding):
            failures.append("ROW_CARRIED_WORLD_HISTORY_EVENT_BINDING_DIFFERS_FROM_RECONSTRUCTION")

    failures = sorted(set(failures))
    sanitized = None
    if not failures and isinstance(derived_receipt, dict) and isinstance(event_binding, dict):
        sanitized = deepcopy(row)
        sanitized["discriminator_execution_receipts_evaluator_only"] = [deepcopy(derived_receipt)]
        sanitized["world_history_scoped_event_binding_evaluator_only"] = deepcopy(event_binding)

    return (
        _result(
            failures,
            authority_path=AUTHORITY_PATH,
            authority_sha256=_digest(authority),
            world_history_scoped_event_binding=event_binding,
            reconstructed_discriminator_receipt=derived_receipt,
            ordering_result=ordering,
            positive_D_E_promotion_ready=False,
            remaining_p0=[
                "nonempty ordered history requires separately authority-bound history generation/commitment",
                "OBSERVED events require producer-authenticated observation evidence authority",
                "exact-current admitted execution plus rendered nuisance/family/tokenizer/checkpoint gates remain required",
            ],
        ),
        sanitized,
    )


def adjudicate(row: Any, upstream_generation_result: Any) -> dict[str, Any]:
    result, _ = authenticate_and_sanitize(row, upstream_generation_result)
    return result


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
                "positive_D_E_promotion_ready": False,
            },
            sort_keys=True,
        )
    )
