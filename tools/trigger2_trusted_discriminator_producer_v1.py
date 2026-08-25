#!/usr/bin/env python3
"""Repository-authority-bound deterministic discriminator producer for Trigger-2 A02.

Bounded to the source-pinned empty-history SYNTHETIC_PROOF pilot. Row-carried producer,
policy, admissible/executed, coverage and receipt-id claims have zero authority. The producer
binds its own source identity plus repository lineage, exact formal world/pre-state/test/event
identities, recomputes retained v3 u_test_order, derives admissibility from pinned policy and
returns one deterministic synthetic receipt. PASS is nonpromoting and mints zero credit.
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
AUTHORITY_RELATIVE_PATH = Path("research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY_V1.json")
LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v3.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return sha256(_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_sibling(filename: str, name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lab = _load_sibling(LABELER_FILENAME, "trigger2_reference_v3_for_a02_producer")


def _authority() -> dict[str, Any]:
    value = json.loads((_repo_root() / AUTHORITY_RELATIVE_PATH).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("AUTHORITY_OBJECT_REQUIRED")
    return value


def _event_payload(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    keys = (
        "schema", "event_id", "correlation_ancestry_id", "independence_group",
        "payload_key", "provenance", "epistemic_type", "test_id", "observed_outcome",
        "canonical_truth_allowed", "direct_effect_authority",
    )
    if any(k not in event for k in keys):
        return None
    return {k: deepcopy(event[k]) for k in keys}


def _world_scoped_event_sha256(world: Any, event: Any) -> str | None:
    payload = _event_payload(event)
    if not isinstance(world, dict) or not isinstance(world.get("world_id"), str) or payload is None:
        return None
    return _digest({"world_id": world["world_id"], "event": payload})


def _live_projection(state: Any) -> list[dict[str, Any]] | None:
    if not isinstance(state, dict) or not isinstance(state.get("branches"), list):
        return None
    rows: list[dict[str, Any]] = []
    for b in state["branches"]:
        if not isinstance(b, dict):
            return None
        if b.get("sigma") == "FALSIFIED":
            continue
        rows.append({k: deepcopy(b.get(k)) for k in (
            "branch_id", "v", "K", "sigma", "predictions", "T", "projection_visibility"
        )})
    rows.sort(key=lambda x: str(x.get("branch_id")))
    return rows


def _producer_binding(authority: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    spec = authority.get("producer")
    if not isinstance(spec, dict):
        return {}, ["DISCRIMINATOR_AUTHORITY_PRODUCER_REQUIRED"]
    current_sha = _file_sha256(Path(__file__).resolve())
    if spec.get("repo_path") != "tools/trigger2_trusted_discriminator_producer_v1.py":
        failures.append("DISCRIMINATOR_PRODUCER_PATH_NOT_AUTHORIZED")
    if spec.get("source_sha256") != current_sha:
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_SHA_MISMATCH")
    if spec.get("producer_schema_or_version") != PRODUCER_SCHEMA:
        failures.append("DISCRIMINATOR_PRODUCER_SCHEMA_NOT_AUTHORIZED")
    lineage = spec.get("source_lineage")
    if not isinstance(lineage, dict):
        failures.append("DISCRIMINATOR_PRODUCER_SOURCE_LINEAGE_REQUIRED")
        lineage = {}
    for field in ("introduced_commit_sha", "branch_base_sha"):
        value = lineage.get(field)
        if not isinstance(value, str) or len(value) != 40:
            failures.append("DISCRIMINATOR_PRODUCER_SOURCE_LINEAGE_INVALID:" + field)
    return {
        "repo_path": spec.get("repo_path"),
        "source_sha256": current_sha,
        "producer_schema_or_version": PRODUCER_SCHEMA,
        "source_lineage": deepcopy(lineage),
    }, sorted(set(failures))


def produce(case_id: Any, world: Any, state: Any, event: Any) -> dict[str, Any]:
    failures: list[str] = []
    authority_path = _repo_root() / AUTHORITY_RELATIVE_PATH
    try:
        authority = _authority()
        authority_sha = _file_sha256(authority_path)
    except Exception as exc:
        return {"schema": PRODUCER_SCHEMA, "pass": False, "failures": ["DISCRIMINATOR_AUTHORITY_LOAD_FAILED:" + type(exc).__name__], "receipt": None}
    if authority.get("schema") != AUTHORITY_SCHEMA:
        failures.append("DISCRIMINATOR_AUTHORITY_SCHEMA_MISMATCH")
    binding, fs = _producer_binding(authority)
    failures.extend(fs)

    cases = authority.get("allowed_cases")
    case = cases.get(case_id) if isinstance(cases, dict) and isinstance(case_id, str) else None
    if not isinstance(case, dict):
        failures.append("DISCRIMINATOR_CASE_NOT_AUTHORIZED")
        case = {}
    if not isinstance(world, dict):
        failures.append("DISCRIMINATOR_WORLD_OBJECT_REQUIRED"); world = {}
    if not isinstance(state, dict):
        failures.append("DISCRIMINATOR_STATE_OBJECT_REQUIRED"); state = {}
    if not isinstance(event, dict):
        failures.append("DISCRIMINATOR_EVENT_OBJECT_REQUIRED"); event = {}

    scope = case.get("semantic_scope") if isinstance(case.get("semantic_scope"), dict) else {}
    for got, expected, code in (
        (world.get("world_id"), scope.get("world_id"), "DISCRIMINATOR_WORLD_ID_NOT_AUTHORIZED"),
        (event.get("event_id"), scope.get("event_id"), "DISCRIMINATOR_EVENT_ID_NOT_AUTHORIZED"),
        (event.get("test_id"), scope.get("test_id"), "DISCRIMINATOR_TEST_ID_NOT_AUTHORIZED"),
    ):
        if got != expected:
            failures.append(code)

    formal_world_sha = _digest(world)
    state_sha = _digest(state)
    if formal_world_sha != case.get("formal_world_sha256"):
        failures.append("DISCRIMINATOR_FORMAL_WORLD_DIGEST_MISMATCH")
    if state_sha != case.get("pre_state_sha256"):
        failures.append("DISCRIMINATOR_PRESTATE_DIGEST_MISMATCH")

    test_id = event.get("test_id")
    test_spec = world.get("tests", {}).get(test_id) if isinstance(world.get("tests"), dict) else None
    test_spec_sha = _digest(test_spec) if isinstance(test_spec, dict) else None
    if test_spec_sha != case.get("formal_discriminator_spec_sha256"):
        failures.append("DISCRIMINATOR_FORMAL_SPEC_DIGEST_MISMATCH")
    event_sha = _world_scoped_event_sha256(world, event)
    if event_sha is None:
        failures.append("DISCRIMINATOR_WORLD_SCOPED_EVENT_IDENTITY_INVALID")
    live = _live_projection(state)
    live_sha = _digest(live) if isinstance(live, list) else None
    if not live:
        failures.append("DISCRIMINATOR_LIVE_BRANCH_SET_REQUIRED")

    policy = case.get("policy") if isinstance(case.get("policy"), dict) else {}
    policy_sha = _digest(policy) if policy else None
    if policy_sha != case.get("policy_sha256"):
        failures.append("DISCRIMINATOR_POLICY_DIGEST_MISMATCH")

    ordering_result = None
    ordering_row = None
    if not failures:
        try:
            ordering_result = lab.u_test_order(world, state, [test_id])
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_U_TEST_ORDER_EXCEPTION:" + type(exc).__name__)
        else:
            ordering = ordering_result.get("ordering") if isinstance(ordering_result, dict) and ordering_result.get("pass") else None
            if not isinstance(ordering, list) or len(ordering) != 1 or not isinstance(ordering[0], dict):
                failures.append("DISCRIMINATOR_PRODUCER_ORDERING_INVALID")
            else:
                ordering_row = ordering[0]

    if isinstance(ordering_row, dict) and not failures:
        full_ok = policy.get("require_complete_live_pair_coverage") is not True or ordering_row.get("separates_all_live_pairs") is True
        positive_ok = policy.get("require_positive_pair_separation") is not True or (isinstance(ordering_row.get("separated_live_pairs"), int) and ordering_row["separated_live_pairs"] > 0)
        outcome_ok = isinstance(test_spec, dict) and event.get("observed_outcome") in test_spec.get("allowed_outcomes", [])
        if not (full_ok and positive_ok and outcome_ok):
            failures.append("DISCRIMINATOR_POLICY_REJECTED")

    producer_result_sha = _digest(ordering_result) if isinstance(ordering_result, dict) else None
    receipt = None
    if not failures and isinstance(ordering_row, dict):
        core = {
            "schema": RECEIPT_SCHEMA,
            "producer": binding,
            "authority_schema": AUTHORITY_SCHEMA,
            "authority_repo_path": AUTHORITY_RELATIVE_PATH.as_posix(),
            "authority_sha256": authority_sha,
            "case_id": case_id,
            "policy_sha256": policy_sha,
            "world_id": world.get("world_id"),
            "formal_world_sha256": formal_world_sha,
            "pre_state_sha256": state_sha,
            "live_branch_projection_sha256": live_sha,
            "formal_discriminator_spec_sha256": test_spec_sha,
            "event_id": event.get("event_id"),
            "test_id": test_id,
            "observed_outcome": event.get("observed_outcome"),
            "world_scoped_event_sha256": event_sha,
            "producer_result_sha256": producer_result_sha,
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
        receipt = deepcopy(core)
        receipt["execution_receipt_id"] = "t2disc:v2:" + _digest(core)

    failures = sorted(set(failures))
    return {
        "schema": PRODUCER_SCHEMA, "pass": not failures, "failures": failures,
        "receipt": receipt, "producer_binding": binding,
        "authority_repo_path": AUTHORITY_RELATIVE_PATH.as_posix(), "authority_sha256": authority_sha,
        "formal_world_sha256": formal_world_sha, "pre_state_sha256": state_sha,
        "formal_discriminator_spec_sha256": test_spec_sha,
        "live_branch_projection_sha256": live_sha,
        "world_scoped_event_sha256": event_sha, "producer_result_sha256": producer_result_sha,
        "admissibility_derived_not_asserted": True, "execution_receipt_derived_not_asserted": True,
        "canonical_truth_minted": False, "direct_effect_authority_minted": False,
        "accepted_dataset_tokens_minted": 0, "training_credit_minted": 0, "runtime_credit_minted": 0,
    }


if __name__ == "__main__":
    print(json.dumps({"schema": PRODUCER_SCHEMA, "status": "SOURCE_ONLY_A02", "training_credit_minted": 0}, sort_keys=True))
