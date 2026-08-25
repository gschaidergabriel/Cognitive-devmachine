#!/usr/bin/env python3
"""Repository-bound deterministic discriminator producer for Trigger-2 pilot proof v1.

The producer closes a narrow source-authenticity gap in the bounded Trigger-2
Hyperposition pilot.  It does not trust row-carried ``admissible``, ``executed`` or
``execution_receipt_id`` fields.  Instead it resolves one producer/policy authority from
repository state, binds exact producer source bytes, world/test specification, pre-state
semantics and a world-scoped event identity, then invokes the retained v3 ``u_test_order``
reference function and derives a synthetic execution receipt from that result.

This is deterministic synthetic evaluator infrastructure only.  It creates no canonical
truth/effect authority and mints zero dataset, runtime, J-Space, HCU, EntityOS or training
credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_PRODUCER/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v2"
AUTHORITY_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY/v1"
AUTHORITY_RELATIVE_PATH = Path(
    "research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY_V1.json"
)
LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v3.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("AUTHORITY_OBJECT_REQUIRED")
    return value


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lab = _load_sibling(LABELER_FILENAME, "trigger2_reference_labelers_v3_for_discriminator_producer")


def _authority() -> dict[str, Any]:
    return _load_json(_repo_root() / AUTHORITY_RELATIVE_PATH)


def _event_semantic_payload(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    keys = (
        "schema",
        "event_id",
        "correlation_ancestry_id",
        "independence_group",
        "payload_key",
        "provenance",
        "epistemic_type",
        "test_id",
        "observed_outcome",
        "canonical_truth_allowed",
        "direct_effect_authority",
    )
    if any(key not in event for key in keys):
        return None
    return {key: deepcopy(event[key]) for key in keys}


def _world_scoped_event_sha256(world: Any, event: Any) -> str | None:
    if not isinstance(world, dict) or not isinstance(world.get("world_id"), str):
        return None
    payload = _event_semantic_payload(event)
    if payload is None:
        return None
    return _digest({"world_id": world["world_id"], "event": payload})


def _live_branch_projection(world: Any, state: Any) -> list[dict[str, Any]] | None:
    if not isinstance(world, dict) or not isinstance(state, dict):
        return None
    branches = state.get("branches")
    if not isinstance(branches, list):
        return None
    out: list[dict[str, Any]] = []
    for branch in branches:
        if not isinstance(branch, dict):
            return None
        if branch.get("sigma") == "FALSIFIED":
            continue
        # The retained u_test_order validates K/context.  This digest intentionally binds
        # all state-side fields that can change pair-separation semantics for the pilot.
        out.append({
            "branch_id": branch.get("branch_id"),
            "v": branch.get("v"),
            "K": deepcopy(branch.get("K")),
            "sigma": branch.get("sigma"),
            "predictions": deepcopy(branch.get("predictions")),
            "T": deepcopy(branch.get("T")),
            "projection_visibility": branch.get("projection_visibility"),
        })
    out.sort(key=lambda item: str(item.get("branch_id")))
    return out


def _producer_binding(authority: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    producer = authority.get("producer")
    if not isinstance(producer, dict):
        return {}, ["DISCRIMINATOR_AUTHORITY_PRODUCER_REQUIRED"]
    expected_path = producer.get("repo_path")
    if expected_path != "tools/trigger2_trusted_discriminator_producer_v1.py":
        failures.append("DISCRIMINATOR_PRODUCER_PATH_NOT_AUTHORIZED")
    current_path = Path(__file__).resolve()
    current_sha = _file_sha256(current_path)
    if producer.get("source_sha256") != current_sha:
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_SHA_MISMATCH")
    if producer.get("producer_schema_or_version") != PRODUCER_SCHEMA:
        failures.append("DISCRIMINATOR_PRODUCER_SCHEMA_NOT_AUTHORIZED")
    return {
        "repo_path": expected_path,
        "source_sha256": current_sha,
        "producer_schema_or_version": PRODUCER_SCHEMA,
    }, sorted(set(failures))


def produce(case_id: Any, world: Any, state: Any, event: Any) -> dict[str, Any]:
    """Derive the exact bounded-pilot discriminator receipt from repository authority."""
    failures: list[str] = []
    authority_path = _repo_root() / AUTHORITY_RELATIVE_PATH
    try:
        authority = _authority()
        authority_sha256 = _file_sha256(authority_path)
    except Exception as exc:
        return {
            "schema": PRODUCER_SCHEMA,
            "pass": False,
            "failures": ["DISCRIMINATOR_AUTHORITY_LOAD_FAILED:" + type(exc).__name__],
            "receipt": None,
        }
    if authority.get("schema") != AUTHORITY_SCHEMA:
        failures.append("DISCRIMINATOR_AUTHORITY_SCHEMA_MISMATCH")

    binding, binding_failures = _producer_binding(authority)
    failures.extend(binding_failures)

    cases = authority.get("allowed_cases")
    case = cases.get(case_id) if isinstance(cases, dict) and isinstance(case_id, str) else None
    if not isinstance(case, dict):
        failures.append("DISCRIMINATOR_CASE_NOT_AUTHORIZED")
        case = {}

    if not isinstance(world, dict):
        failures.append("DISCRIMINATOR_WORLD_OBJECT_REQUIRED")
        world = {}
    if not isinstance(state, dict):
        failures.append("DISCRIMINATOR_STATE_OBJECT_REQUIRED")
        state = {}
    if not isinstance(event, dict):
        failures.append("DISCRIMINATOR_EVENT_OBJECT_REQUIRED")
        event = {}

    semantic_scope = case.get("semantic_scope") if isinstance(case.get("semantic_scope"), dict) else {}
    if world.get("world_id") != semantic_scope.get("world_id"):
        failures.append("DISCRIMINATOR_WORLD_ID_NOT_AUTHORIZED")
    if event.get("event_id") != semantic_scope.get("event_id"):
        failures.append("DISCRIMINATOR_EVENT_ID_NOT_AUTHORIZED")
    if event.get("test_id") != semantic_scope.get("test_id"):
        failures.append("DISCRIMINATOR_TEST_ID_NOT_AUTHORIZED")

    test_id = event.get("test_id")
    test_spec = world.get("tests", {}).get(test_id) if isinstance(world.get("tests"), dict) else None
    test_spec_sha = _digest(test_spec) if isinstance(test_spec, dict) else None
    if test_spec_sha != case.get("formal_discriminator_spec_sha256"):
        failures.append("DISCRIMINATOR_FORMAL_SPEC_DIGEST_MISMATCH")

    live_projection = _live_branch_projection(world, state)
    live_projection_sha = _digest(live_projection) if isinstance(live_projection, list) else None
    if not isinstance(live_projection, list) or not live_projection:
        failures.append("DISCRIMINATOR_LIVE_BRANCH_SET_REQUIRED")

    state_sha = _digest(state) if isinstance(state, dict) else None
    event_sha = _world_scoped_event_sha256(world, event)
    if event_sha is None:
        failures.append("DISCRIMINATOR_WORLD_SCOPED_EVENT_IDENTITY_INVALID")

    ordering_result = None
    ordering_row = None
    if not failures:
        try:
            ordering_result = lab.u_test_order(world, state, [test_id])
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_U_TEST_ORDER_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(ordering_result, dict) or not ordering_result.get("pass"):
                failures.append("DISCRIMINATOR_PRODUCER_U_TEST_ORDER_REJECTED")
            else:
                ordering = ordering_result.get("ordering")
                if not isinstance(ordering, list) or len(ordering) != 1 or not isinstance(ordering[0], dict):
                    failures.append("DISCRIMINATOR_PRODUCER_ORDERING_SHAPE_INVALID")
                else:
                    ordering_row = ordering[0]

    policy = case.get("policy") if isinstance(case.get("policy"), dict) else {}
    policy_sha = _digest(policy) if policy else None
    if policy_sha != case.get("policy_sha256"):
        failures.append("DISCRIMINATOR_POLICY_DIGEST_MISMATCH")

    admissible = False
    if isinstance(ordering_row, dict) and not failures:
        require_full = policy.get("require_complete_live_pair_coverage") is True
        require_positive = policy.get("require_positive_pair_separation") is True
        full_ok = (not require_full) or ordering_row.get("separates_all_live_pairs") is True
        positive_ok = (not require_positive) or (
            isinstance(ordering_row.get("separated_live_pairs"), int)
            and ordering_row.get("separated_live_pairs", 0) > 0
        )
        outcome_ok = isinstance(test_spec, dict) and event.get("observed_outcome") in test_spec.get("allowed_outcomes", [])
        admissible = bool(full_ok and positive_ok and outcome_ok)
        if not admissible:
            failures.append("DISCRIMINATOR_POLICY_REJECTED")

    receipt = None
    if not failures and isinstance(ordering_row, dict):
        receipt_core = {
            "schema": RECEIPT_SCHEMA,
            "producer": binding,
            "authority_schema": AUTHORITY_SCHEMA,
            "authority_repo_path": AUTHORITY_RELATIVE_PATH.as_posix(),
            "authority_sha256": authority_sha256,
            "case_id": case_id,
            "policy_sha256": policy_sha,
            "world_id": world.get("world_id"),
            "world_sha256": _digest(world),
            "formal_discriminator_spec_sha256": test_spec_sha,
            "pre_state_sha256": state_sha,
            "live_branch_projection_sha256": live_projection_sha,
            "event_id": event.get("event_id"),
            "test_id": test_id,
            "observed_outcome": event.get("observed_outcome"),
            "world_scoped_event_sha256": event_sha,
            "admissible": True,
            "executed": True,
            "synthetic_execution": True,
            "separated_live_pairs": ordering_row.get("separated_live_pairs"),
            "separates_all_live_pairs": ordering_row.get("separates_all_live_pairs"),
            "ordinal_rank": ordering_row.get("ordinal_rank"),
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "runtime_credit_minted": 0,
        }
        receipt = deepcopy(receipt_core)
        receipt["execution_receipt_id"] = "t2disc:v2:" + _digest(receipt_core)

    failures = sorted(set(failures))
    return {
        "schema": PRODUCER_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "receipt": receipt,
        "producer_binding": binding,
        "authority_repo_path": AUTHORITY_RELATIVE_PATH.as_posix(),
        "authority_sha256": authority_sha256 if 'authority_sha256' in locals() else None,
        "formal_discriminator_spec_sha256": test_spec_sha,
        "pre_state_sha256": state_sha,
        "live_branch_projection_sha256": live_projection_sha,
        "world_scoped_event_sha256": event_sha,
        "admissibility_derived_not_asserted": True,
        "execution_receipt_derived_not_asserted": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
    }


if __name__ == "__main__":
    print(json.dumps({
        "schema": PRODUCER_SCHEMA,
        "status": "SOURCE_ONLY_BOUNDED_SYNTHETIC_PRODUCER",
        "receipt_schema": RECEIPT_SCHEMA,
        "canonical_truth_minted": False,
        "training_credit_minted": 0,
    }, sort_keys=True))
