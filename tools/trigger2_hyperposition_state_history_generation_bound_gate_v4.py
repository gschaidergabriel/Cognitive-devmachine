#!/usr/bin/env python3
"""A02 producer-authenticated Trigger-2 Hyperposition proof composition v4.

This is the bounded successor to generation+epistemic+state-history gate v3 for the current
empty-history SYNTHETIC_PROOF pilot.  Ordering is:

    authority-resolved generation provenance
      -> repository-authority-resolved discriminator producer/policy
      -> deterministic producer invocation + exact receipt reconstruction
      -> epistemic pre-update admission
      -> retained replay/state-history proof

The row cannot grant producer identity, policy, admissibility, execution, receipt identity,
coverage or effect/truth authority.  PASS is source/component candidate evidence only and
mints zero dataset, training, runtime, J-Space, HCU, EntityOS, truth or effect credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_EPISTEMIC_PRODUCER_BOUND_GATE/v4"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY_V1.json"
AUTHORITY_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY/v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_sibling(filename: str, module_name: str):
    return _load_path(Path(__file__).resolve().with_name(filename), module_name)


generation = _load_sibling(
    "trigger2_generation_provenance_gate_v1.py",
    "trigger2_generation_provenance_for_hp_v4",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_hp_v4",
)


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _authority() -> dict[str, Any]:
    return json.loads((_repo_root() / AUTHORITY_PATH).read_text(encoding="utf-8"))


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "row_carried_producer_identity_is_authority": False,
        "row_carried_policy_is_authority": False,
        "row_carried_admissible_boolean_is_authority": False,
        "row_carried_executed_boolean_is_authority": False,
        "row_carried_execution_receipt_id_is_authority": False,
        "positive_D_E_promotion_ready": False,
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


def _failures_from(prefix: str, result: Any) -> list[str]:
    if not isinstance(result, dict):
        return [prefix + "RESULT_INVALID"]
    failures = result.get("failures")
    if isinstance(failures, list) and failures:
        return [prefix + str(x) for x in failures]
    return [prefix + "REJECTED"]


def _load_bound_producer(authority: Any) -> tuple[Any | None, dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(authority, dict) or authority.get("schema") != AUTHORITY_SCHEMA:
        return None, None, ["DISCRIMINATOR_AUTHORITY_SCHEMA_MISMATCH"]
    fences = authority.get("authority_fences")
    if fences != {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }:
        failures.append("DISCRIMINATOR_AUTHORITY_FENCES_INVALID")
    binding = authority.get("producer")
    if not isinstance(binding, dict):
        return None, None, failures + ["DISCRIMINATOR_PRODUCER_BINDING_REQUIRED"]
    path_text = binding.get("repo_path")
    if not isinstance(path_text, str) or not path_text:
        return None, binding, failures + ["DISCRIMINATOR_PRODUCER_PATH_REQUIRED"]
    path = (_repo_root() / path_text).resolve()
    try:
        path.relative_to(_repo_root().resolve())
    except ValueError:
        return None, binding, failures + ["DISCRIMINATOR_PRODUCER_PATH_ESCAPES_REPO"]
    if not path.is_file():
        return None, binding, failures + ["DISCRIMINATOR_PRODUCER_FILE_MISSING"]
    actual_sha = _source_sha256(path)
    if actual_sha != binding.get("source_sha256"):
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_SHA256_MISMATCH")
    try:
        producer = _load_path(path, "trigger2_bound_a02_discriminator_producer_v1")
    except Exception as exc:
        return None, binding, failures + ["DISCRIMINATOR_PRODUCER_IMPORT_FAILED:" + type(exc).__name__]
    if getattr(producer, "PRODUCER_SCHEMA", None) != binding.get("producer_schema_or_version"):
        failures.append("DISCRIMINATOR_PRODUCER_SCHEMA_MISMATCH")
    return producer, deepcopy(binding), sorted(set(failures))


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    failures: list[str] = []
    generation_result = None
    producer_receipt = None
    epistemic_result = None
    authority = None
    producer_binding = None
    policy = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or not generation_result.get("pass"):
            failures.extend(_failures_from("GENERATION:", generation_result))

    # A02 v1 is intentionally bounded to the already authority-pinned empty-history pilot.
    history_events = row.get("synthetic_event_history_evaluator_only")
    state_before = row.get("hyperposition_state_before_evaluator_only")
    genesis = row.get("hyperposition_genesis_state_evaluator_only")
    if history_events != []:
        failures.append("A02_V1_REQUIRES_EMPTY_GENERATION_BOUND_HISTORY")
    if not isinstance(state_before, dict) or genesis != state_before:
        failures.append("A02_V1_EMPTY_HISTORY_GENESIS_MUST_EQUAL_STATE_BEFORE")

    if not failures:
        try:
            authority = _authority()
        except Exception as exc:
            failures.append("DISCRIMINATOR_AUTHORITY_LOAD_FAILED:" + type(exc).__name__)
        else:
            producer, producer_binding, auth_failures = _load_bound_producer(authority)
            failures.extend(auth_failures)
            policy = authority.get("policy") if isinstance(authority, dict) else None
            scope = authority.get("bounded_scope") if isinstance(authority, dict) else None
            case_id = row.get("generation_case_id_evaluator_only")
            world = row.get("formal_task_world_evaluator_only")
            event = row.get("synthetic_test_event_evaluator_only")
            if not isinstance(scope, dict):
                failures.append("DISCRIMINATOR_AUTHORITY_BOUNDED_SCOPE_REQUIRED")
            else:
                if case_id != scope.get("case_id"):
                    failures.append("DISCRIMINATOR_CASE_SCOPE_MISMATCH")
                if not isinstance(world, dict) or world.get("world_id") != scope.get("world_id"):
                    failures.append("DISCRIMINATOR_WORLD_SCOPE_MISMATCH")
                if state_before.get("query_id") != scope.get("query_id"):
                    failures.append("DISCRIMINATOR_QUERY_SCOPE_MISMATCH")
                if not isinstance(event, dict) or event.get("event_id") != scope.get("event_id"):
                    failures.append("DISCRIMINATOR_EVENT_SCOPE_MISMATCH")
                if isinstance(event, dict) and event.get("test_id") != scope.get("test_id"):
                    failures.append("DISCRIMINATOR_TEST_SCOPE_MISMATCH")

            # Generation gate already reconstructed exact subjects. Recheck its digest output
            # against the concrete subjects used by the producer so the proof chain cannot
            # silently switch state between stages.
            reconstructed = generation_result.get("reconstructed_subject_hashes") if isinstance(generation_result, dict) else None
            try:
                concrete = {
                    "formal_world_jcs_sha256": generation._jcs_sha256(world),
                    "event_dependence_registry_jcs_sha256": generation._jcs_sha256(world.get("event_dependence_registry")),
                    "event_jcs_sha256": generation._jcs_sha256(event),
                    "state_before_jcs_sha256": generation._jcs_sha256(state_before),
                }
            except Exception as exc:
                failures.append("A02_BOUND_SUBJECT_JCS_FAILED:" + type(exc).__name__)
            else:
                if concrete != reconstructed:
                    failures.append("A02_PRODUCER_SUBJECTS_NOT_EXACT_GENERATION_RECONSTRUCTION")

            if not failures and producer is not None:
                try:
                    producer_receipt = producer.produce(
                        case_id=case_id,
                        world=world,
                        state_before=state_before,
                        event=event,
                        producer_binding=producer_binding,
                        policy=policy,
                    )
                except Exception as exc:
                    failures.append("DETERMINISTIC_DISCRIMINATOR_PRODUCER_FAILED:" + type(exc).__name__ + ":" + str(exc))

    sanitized = None
    if not failures and isinstance(producer_receipt, dict):
        claimed = row.get("discriminator_execution_receipts_evaluator_only")
        if claimed != [producer_receipt]:
            failures.append("ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_AUTHORITY_DERIVATION")
        else:
            sanitized = deepcopy(row)
            sanitized["discriminator_execution_receipts_evaluator_only"] = [deepcopy(producer_receipt)]

    if not failures and isinstance(sanitized, dict):
        try:
            epistemic_result = epistemic.adjudicate(sanitized)
        except Exception as exc:
            failures.append("EPISTEMIC_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or not epistemic_result.get("pass"):
                failures.extend(_failures_from("EPISTEMIC_STATE_HISTORY:", epistemic_result))

    return _result(
        failures,
        generation_provenance=generation_result,
        discriminator_authority=deepcopy(authority) if isinstance(authority, dict) else None,
        expected_discriminator_receipt=producer_receipt,
        epistemic_state_history_proof=epistemic_result,
        exact_order=[
            "GENERATION_PROVENANCE",
            "REPOSITORY_DISCRIMINATOR_PRODUCER_AND_POLICY_AUTHORITY",
            "EXACT_BOUND_SUBJECT_RECHECK",
            "DETERMINISTIC_DISCRIMINATOR_PRODUCER_INVOCATION",
            "EXACT_ROW_RECEIPT_MATCH",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPLAY_STATE_HISTORY_PROOF",
        ],
        a02_contract_status="SOURCE_IMPLEMENTED_EXECUTION_UNOBSERVED",
        remaining_p0=[
            "exact-current deterministic execution of A02 mutation suite",
            "immutable genesis/ordered-history authority before any nonempty-history positive",
            "producer-authenticated OBSERVED evidence before OBSERVED positive supervision",
            "rendered nuisance/full-cross-or-conditional-MI/family-provenance/tokenizer-ABI gates",
        ],
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_A02_IMPLEMENTATION_CANDIDATE",
        "positive_D_E_promotion_ready": False,
    })
