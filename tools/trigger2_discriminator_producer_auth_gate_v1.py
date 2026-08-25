#!/usr/bin/env python3
"""Repository-authority-bound Trigger-2 discriminator producer authentication gate v1.

This gate closes bounded-pilot A02 without creating a second Hyperposition semantic oracle.
It runs only after generation provenance has passed, resolves producer+policy from repository
authority, verifies exact producer bytes, derives world/history/prestate/event bindings,
executes the deterministic SYNTHETIC_PROOF producer, independently recomputes retained
u_test_order coverage, and injects only the exact reconstructed discriminator receipt.

Candidate-carried admissible/executed booleans and receipt IDs have zero authority. A claimed
receipt is accepted only when byte/object-equivalent to the independently reconstructed one.
PASS is source/candidate pre-admission evidence only and mints zero canonical, dataset,
training, runtime, J-Space, HCU, EntityOS, provider, truth, or effect credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_DISCRIMINATOR_PRODUCER_AUTH_GATE/v1"
AUTHORITY_SCHEMA = "CLAY_TRIGGER2_TRUSTED_DISCRIMINATOR_PRODUCER_AUTHORITY/v1"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_TRUSTED_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
EVENT_BINDING_SCHEMA = "XENO_WORLD_HISTORY_PRESTATE_SCOPED_EVENT_BINDING/v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generation = _load_module(
    Path(__file__).resolve().with_name("trigger2_generation_provenance_gate_v1.py"),
    "trigger2_generation_for_discriminator_producer_auth_v1",
)
history = _load_module(
    Path(__file__).resolve().with_name("trigger2_hyperposition_state_history_proof_gate_v1.py"),
    "trigger2_history_for_discriminator_producer_auth_v1",
)


def _authority() -> dict[str, Any]:
    return json.loads((_repo_root() / AUTHORITY_PATH).read_text(encoding="utf-8"))


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _jcs_sha256(value: Any) -> str:
    return generation._jcs_sha256(value)


def _policy_subject(policy: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(policy)
    out.pop("policy_jcs_sha256", None)
    out.pop("formal_discriminator_spec_jcs_sha256", None)
    return out


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "producer_auth_pass": not failures,
        "failures": failures,
        "row_carried_admissible_is_authority": False,
        "row_carried_executed_is_authority": False,
        "row_carried_execution_receipt_id_is_authority": False,
        "repository_authority_resolved": False,
        "producer_invoked": False,
        "candidate_pre_admission_pass": not failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
    out.update(extra)
    return out


def _event_binding(world: Any, state_before: Any, history_events: Any, event: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or not isinstance(state_before, dict) or not isinstance(history_events, list) or not isinstance(event, dict):
        raise ValueError("WORLD_STATE_HISTORY_EVENT_OBJECTS_REQUIRED")
    event_digest = history.event_semantic_sha256(event)
    if not isinstance(event_digest, str):
        raise ValueError("EVENT_SEMANTIC_DIGEST_REQUIRED")
    ordered_history = []
    for idx, prior in enumerate(history_events):
        prior_digest = history.event_semantic_sha256(prior)
        if not isinstance(prior, dict) or not isinstance(prior_digest, str):
            raise ValueError(f"HISTORY_EVENT_SEMANTIC_DIGEST_REQUIRED:{idx}")
        ordered_history.append({
            "index": idx,
            "event_id": prior.get("event_id"),
            "event_semantic_sha256": prior_digest,
        })
    world_sha = _jcs_sha256(world)
    history_sha = _jcs_sha256(ordered_history)
    state_sha = _jcs_sha256(state_before)
    test_id = event.get("test_id")
    preimage = {
        "world_id": world.get("world_id"),
        "world_jcs_sha256": world_sha,
        "ordered_history_jcs_sha256": history_sha,
        "state_before_jcs_sha256": state_sha,
        "event_id": event.get("event_id"),
        "event_semantic_sha256": event_digest,
        "test_id": test_id,
    }
    return {
        "schema": EVENT_BINDING_SCHEMA,
        **preimage,
        "world_scoped_event_id": "t2scope:" + _jcs_sha256(preimage),
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def _load_bound_producer(authority: dict[str, Any]) -> tuple[Any | None, dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    producer_auth = authority.get("producer")
    if not isinstance(producer_auth, dict):
        return None, None, ["DISCRIMINATOR_PRODUCER_AUTHORITY_OBJECT_REQUIRED"]
    repo_path = producer_auth.get("repo_path")
    if not isinstance(repo_path, str) or not repo_path:
        return None, producer_auth, ["DISCRIMINATOR_PRODUCER_PATH_REQUIRED"]
    producer_path = (_repo_root() / repo_path).resolve()
    try:
        producer_path.relative_to(_repo_root().resolve())
    except ValueError:
        return None, producer_auth, ["DISCRIMINATOR_PRODUCER_PATH_ESCAPES_REPO"]
    if not producer_path.is_file():
        return None, producer_auth, ["DISCRIMINATOR_PRODUCER_FILE_MISSING"]
    actual_sha = _source_sha256(producer_path)
    if actual_sha != producer_auth.get("source_sha256"):
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_IDENTITY_MISMATCH")
    commit_sha = producer_auth.get("git_commit_sha")
    if not isinstance(commit_sha, str) or len(commit_sha) != 40:
        failures.append("DISCRIMINATOR_PRODUCER_COMMIT_IDENTITY_INVALID")
    try:
        module = _load_module(producer_path, "trigger2_trusted_discriminator_producer_bound_v1")
    except Exception as exc:
        return None, producer_auth, failures + ["DISCRIMINATOR_PRODUCER_IMPORT_FAILED:" + type(exc).__name__]
    if getattr(module, "PRODUCER_SCHEMA", None) != producer_auth.get("producer_schema_or_version"):
        failures.append("DISCRIMINATOR_PRODUCER_SCHEMA_MISMATCH")
    if getattr(module, "EXECUTION_SCHEMA", None) != producer_auth.get("execution_schema"):
        failures.append("DISCRIMINATOR_PRODUCER_EXECUTION_SCHEMA_MISMATCH")
    return module, producer_auth, sorted(set(failures))


def authenticate_after_generation(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    try:
        authority = _authority()
    except Exception as exc:
        return _result(["DISCRIMINATOR_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != AUTHORITY_SCHEMA:
        failures.append("DISCRIMINATOR_AUTHORITY_SCHEMA_MISMATCH")
    fences = authority.get("authority_fences")
    if not isinstance(fences, dict) or fences != {
        "epistemic_type": "SYNTHETIC_PROOF",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }:
        failures.append("DISCRIMINATOR_AUTHORITY_FENCES_INVALID")

    case_id = row.get("generation_case_id_evaluator_only")
    policies = authority.get("allowed_cases")
    if not isinstance(policies, dict) or case_id not in policies:
        return _result(failures + ["DISCRIMINATOR_CASE_NOT_AUTHORIZED"])
    policy = policies[case_id]
    if not isinstance(policy, dict):
        return _result(failures + ["DISCRIMINATOR_POLICY_OBJECT_REQUIRED"])

    policy_subject = _policy_subject(policy)
    policy_sha = _jcs_sha256(policy_subject)
    if policy_sha != policy.get("policy_jcs_sha256"):
        failures.append("DISCRIMINATOR_POLICY_AUTHORITY_MISMATCH")
    formal_spec = policy.get("formal_discriminator_spec")
    formal_spec_sha = _jcs_sha256(formal_spec)
    if formal_spec_sha != policy.get("formal_discriminator_spec_jcs_sha256"):
        failures.append("FORMAL_DISCRIMINATOR_SPEC_AUTHORITY_MISMATCH")

    world = row.get("formal_task_world_evaluator_only")
    state_before = row.get("hyperposition_state_before_evaluator_only")
    genesis = row.get("hyperposition_genesis_state_evaluator_only")
    history_events = row.get("synthetic_event_history_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    if history_events != []:
        failures.append("A02_V1_REQUIRES_EMPTY_GENERATION_BOUND_HISTORY")
    if isinstance(state_before, dict) and genesis != state_before:
        failures.append("A02_V1_EMPTY_HISTORY_GENESIS_STATE_MISMATCH")
    if not isinstance(world, dict) or world.get("world_id") != policy.get("world_id"):
        failures.append("DISCRIMINATOR_POLICY_WORLD_ID_MISMATCH")
    test_id = event.get("test_id") if isinstance(event, dict) else None
    if test_id != policy.get("test_id"):
        failures.append("DISCRIMINATOR_POLICY_TEST_ID_MISMATCH")
    world_tests = world.get("tests") if isinstance(world, dict) else None
    if not isinstance(world_tests, dict) or world_tests.get(test_id) != formal_spec:
        failures.append("FORMAL_DISCRIMINATOR_SPEC_MISMATCH")
    if not isinstance(event, dict) or event.get("epistemic_type") != "SYNTHETIC_PROOF":
        failures.append("A02_V1_REQUIRES_SYNTHETIC_PROOF_EVENT")

    producer, producer_auth, producer_failures = _load_bound_producer(authority)
    failures.extend(producer_failures)
    if failures:
        return _result(
            failures,
            repository_authority_resolved=isinstance(authority, dict),
            policy_jcs_sha256=policy_sha,
            formal_discriminator_spec_jcs_sha256=formal_spec_sha,
        )

    try:
        binding = _event_binding(world, state_before, history_events, event)
    except Exception as exc:
        return _result(["WORLD_SCOPED_EVENT_BINDING_FAILED:" + type(exc).__name__ + ":" + str(exc)])

    invocation_preimage = {
        "producer_repo_path": producer_auth["repo_path"],
        "producer_source_sha256": producer_auth["source_sha256"],
        "producer_git_commit_sha": producer_auth["git_commit_sha"],
        "producer_schema_or_version": producer_auth["producer_schema_or_version"],
        "policy_id": policy.get("policy_id"),
        "policy_jcs_sha256": policy_sha,
        "formal_discriminator_spec_jcs_sha256": formal_spec_sha,
        "world_scoped_event_id": binding["world_scoped_event_id"],
        "world_jcs_sha256": binding["world_jcs_sha256"],
        "ordered_history_jcs_sha256": binding["ordered_history_jcs_sha256"],
        "state_before_jcs_sha256": binding["state_before_jcs_sha256"],
        "test_id": test_id,
    }
    invocation_id = "t2disc-invoke:" + _jcs_sha256(invocation_preimage)

    try:
        execution_result = producer.execute(
            case_id=case_id,
            world=deepcopy(world),
            state_before=deepcopy(state_before),
            event_binding=deepcopy(binding),
            policy=deepcopy(policy_subject),
        )
    except Exception as exc:
        return _result(
            ["DISCRIMINATOR_PRODUCER_EXECUTION_FAILED:" + type(exc).__name__ + ":" + str(exc)],
            repository_authority_resolved=True,
            producer_invocation_id=invocation_id,
        )
    if not isinstance(execution_result, dict) or execution_result.get("schema") != producer_auth.get("execution_schema"):
        failures.append("DISCRIMINATOR_PRODUCER_RESULT_SCHEMA_MISMATCH")
    if isinstance(execution_result, dict):
        if execution_result.get("execution_completed") is not True:
            failures.append("DISCRIMINATOR_PRODUCER_EXECUTION_NOT_AUTHENTICATED")
        if execution_result.get("canonical_truth_allowed") is not False:
            failures.append("DISCRIMINATOR_PRODUCER_RESULT_CANONICAL_TRUTH_FORBIDDEN")
        if execution_result.get("direct_effect_authority") is not False:
            failures.append("DISCRIMINATOR_PRODUCER_RESULT_EFFECT_AUTHORITY_FORBIDDEN")
        if execution_result.get("training_eligible") is not False:
            failures.append("DISCRIMINATOR_PRODUCER_RESULT_TRAINING_ELIGIBLE_FORBIDDEN")
        if execution_result.get("observed_outcome") != event.get("observed_outcome"):
            failures.append("DISCRIMINATOR_PRODUCER_RESULT_EVENT_OUTCOME_MISMATCH")

    try:
        ordering = history.lab.u_test_order(world, state_before, [test_id])
    except Exception as exc:
        failures.append("DISCRIMINATOR_COVERAGE_RECOMPUTE_FAILED:" + type(exc).__name__)
        ordering = None
    separated = None
    full_coverage = None
    if isinstance(ordering, dict) and ordering.get("pass"):
        rows = ordering.get("ordering")
        if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
            separated = rows[0].get("separated_live_pairs")
            full_coverage = rows[0].get("separates_all_live_pairs")
    if not isinstance(separated, int) or separated <= 0:
        failures.append("DISCRIMINATOR_MUST_SEPARATE_AT_LEAST_ONE_LIVE_PAIR")
    if full_coverage is not True:
        failures.append("DISCRIMINATOR_INCOMPLETE_APPLICABLE_COMPETITOR_COVERAGE")

    execution_result_sha = _jcs_sha256(execution_result)
    ordering_sha = _jcs_sha256(ordering)
    producer_binding = {
        **invocation_preimage,
        "producer_invocation_id": invocation_id,
        "producer_result_jcs_sha256": execution_result_sha,
        "ordering_result_jcs_sha256": ordering_sha,
        "derived_admissible": not failures,
        "derived_executed": isinstance(execution_result, dict) and execution_result.get("execution_completed") is True,
    }
    receipt_id_preimage = {
        "producer_binding": producer_binding,
        "observed_outcome": execution_result.get("observed_outcome") if isinstance(execution_result, dict) else None,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": full_coverage,
    }
    execution_receipt_id = "t2disc:" + _jcs_sha256(receipt_id_preimage)
    expected_receipt = {
        "schema": history.DISCRIMINATOR_RECEIPT_SCHEMA,
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": execution_result.get("observed_outcome") if isinstance(execution_result, dict) else None,
        "event_semantic_sha256": binding["event_semantic_sha256"],
        "world_sha256": history._world_sha256(world),
        "admissible": not failures,
        "executed": isinstance(execution_result, dict) and execution_result.get("execution_completed") is True,
        "execution_receipt_id": execution_receipt_id,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": full_coverage,
        "producer_auth": producer_binding,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }

    claimed = row.get("discriminator_execution_receipts_evaluator_only")
    if claimed not in (None, [], [expected_receipt]):
        failures.append("DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER")

    sanitized = deepcopy(row)
    sanitized["discriminator_execution_receipts_evaluator_only"] = [deepcopy(expected_receipt)]
    sanitized["world_history_scoped_event_binding_evaluator_only"] = deepcopy(binding)

    return _result(
        failures,
        repository_authority_resolved=True,
        producer_invoked=True,
        producer_repo_path=producer_auth["repo_path"],
        producer_source_sha256=producer_auth["source_sha256"],
        producer_git_commit_sha=producer_auth["git_commit_sha"],
        producer_schema_or_version=producer_auth["producer_schema_or_version"],
        policy_id=policy.get("policy_id"),
        policy_jcs_sha256=policy_sha,
        formal_discriminator_spec_jcs_sha256=formal_spec_sha,
        world_scoped_event_binding=binding,
        producer_invocation_id=invocation_id,
        producer_execution_result=execution_result,
        producer_result_jcs_sha256=execution_result_sha,
        recomputed_ordering=ordering,
        expected_discriminator_receipt=expected_receipt,
        sanitized_row_evaluator_only=sanitized,
        synthetic_execution_noncanonical=True,
    )


def adjudicate(row: Any) -> dict[str, Any]:
    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        return _result(["GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__])
    if not isinstance(generation_result, dict) or not generation_result.get("pass"):
        failures = generation_result.get("failures", []) if isinstance(generation_result, dict) else ["RESULT_INVALID"]
        return _result(["GENERATION:" + str(x) for x in failures], generation_provenance=generation_result)
    result = authenticate_after_generation(row)
    result["generation_provenance"] = generation_result
    return result


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_A02_PRODUCER_AUTH_CANDIDATE",
        "positive_D_E_promotion_ready": False,
    })
