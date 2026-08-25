#!/usr/bin/env python3
"""Trigger-2 Hyperposition evidence-independence deriver v1.

Closes the current v3 positive-label blocker: ``independence_qualified`` is NOT accepted
from a row/generator. Correlation ancestry, dependence group and payload identity are also
not accepted from the event. They are looked up from an immutable, digest-bound dependency
registry keyed by ``source_event_key``. Independence is then mechanically derived against
an append-only hash-chained event history before the current formal-world Hyperposition v3
labeler is called.

Candidate/source logic only. No canonical truth, effect authority, accepted dataset tokens,
runtime/J-Space/HCU/EntityOS credit, provider execution, or training credit is minted.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LABELER_PATH = HERE / "trigger2_hyperposition_reference_labelers_v3.py"
_spec = importlib.util.spec_from_file_location("trigger2_hp_v3", LABELER_PATH)
V3 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(V3)

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_INDEPENDENCE_DERIVER/v1"
HISTORY_SCHEMA = "XENO_HYPERPOSITION_DEPENDENCE_HISTORY/v1"
RECEIPT_SCHEMA = "XENO_HYPERPOSITION_DEPENDENCE_RECEIPT/v1"
GENESIS = "GENESIS"
FORBIDDEN_RAW_FIELDS = {
    "independence_qualified",
    "correlation_ancestry_id",
    "independence_group",
    "payload_key",
    "relation",
    "relations",
    "target_branch_ids",
    "supports_branch_ids",
    "counters_branch_ids",
    "falsifies_branch_ids",
    "winner_branch_id",
}
DEPENDENCE_FIELDS = ("correlation_ancestry_id", "independence_group", "payload_key")


class IndependenceDerivationError(ValueError):
    pass


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(obj: Any) -> str:
    return sha256(_canon(obj)).hexdigest()


def _file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    return {
        "hyperposition_labeler_v3_sha256": _file_sha(LABELER_PATH),
        "independence_deriver_v1_sha256": _file_sha(Path(__file__).resolve()),
    }


def make_history(history_id: str, dependency_registry: dict[str, dict[str, str]]) -> dict[str, Any]:
    if not isinstance(history_id, str) or not history_id:
        raise IndependenceDerivationError("HISTORY_ID_REQUIRED")
    _validate_registry(dependency_registry)
    return {
        "schema": HISTORY_SCHEMA,
        "history_id": history_id,
        "dependency_registry": deepcopy(dependency_registry),
        "registry_digest": _digest(dependency_registry),
        "receipts": [],
        "last_receipt_hash": GENESIS,
    }


def _validate_registry(registry: Any) -> None:
    if not isinstance(registry, dict) or not registry:
        raise IndependenceDerivationError("DEPENDENCY_REGISTRY_REQUIRED")
    for key, row in registry.items():
        if not isinstance(key, str) or not key:
            raise IndependenceDerivationError("SOURCE_EVENT_KEY_INVALID")
        if not isinstance(row, dict):
            raise IndependenceDerivationError("DEPENDENCY_REGISTRY_ROW_OBJECT_REQUIRED")
        if not all(isinstance(row.get(f), str) and row[f] for f in DEPENDENCE_FIELDS):
            raise IndependenceDerivationError("DEPENDENCY_REGISTRY_IDENTITY_FIELDS_REQUIRED")


def _event_snapshot(prepared_event: dict[str, Any]) -> dict[str, Any]:
    # The qualification bit is deliberately excluded: it is an output of derivation.
    return {k: deepcopy(v) for k, v in prepared_event.items() if k != "independence_qualified"}


def _receipt_hash(receipt_without_hash: dict[str, Any]) -> str:
    return _digest(receipt_without_hash)


def validate_history(history: Any) -> None:
    if not isinstance(history, dict) or history.get("schema") != HISTORY_SCHEMA:
        raise IndependenceDerivationError("HISTORY_SCHEMA_MISMATCH")
    if not isinstance(history.get("history_id"), str) or not history["history_id"]:
        raise IndependenceDerivationError("HISTORY_ID_REQUIRED")
    registry = history.get("dependency_registry")
    _validate_registry(registry)
    if history.get("registry_digest") != _digest(registry):
        raise IndependenceDerivationError("DEPENDENCY_REGISTRY_DIGEST_MISMATCH")
    receipts = history.get("receipts")
    if not isinstance(receipts, list):
        raise IndependenceDerivationError("HISTORY_RECEIPTS_LIST_REQUIRED")
    previous = GENESIS
    seen_sequence = 0
    for receipt in receipts:
        if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
            raise IndependenceDerivationError("RECEIPT_SCHEMA_MISMATCH")
        seen_sequence += 1
        if receipt.get("sequence") != seen_sequence:
            raise IndependenceDerivationError("RECEIPT_SEQUENCE_MISMATCH")
        if receipt.get("previous_receipt_hash") != previous:
            raise IndependenceDerivationError("RECEIPT_HASH_CHAIN_BROKEN")
        snapshot = receipt.get("event_snapshot")
        if not isinstance(snapshot, dict):
            raise IndependenceDerivationError("RECEIPT_EVENT_SNAPSHOT_REQUIRED")
        if receipt.get("event_digest") != _digest(snapshot):
            raise IndependenceDerivationError("RECEIPT_EVENT_DIGEST_MISMATCH")
        basis = {k: deepcopy(v) for k, v in receipt.items() if k != "receipt_hash"}
        expected_hash = _receipt_hash(basis)
        if receipt.get("receipt_hash") != expected_hash:
            raise IndependenceDerivationError("RECEIPT_HASH_MISMATCH")
        previous = expected_hash
    if history.get("last_receipt_hash") != previous:
        raise IndependenceDerivationError("HISTORY_LAST_RECEIPT_HASH_MISMATCH")


def _state_event_ids(state: Any) -> set[str]:
    ids: set[str] = set()
    if not isinstance(state, dict):
        return ids
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for record in branch.get(field, []) or []:
                if isinstance(record, dict) and isinstance(record.get("event_id"), str):
                    ids.add(record["event_id"])
    for field in ("correlated_observations", "nonupdating_observations"):
        for record in state.get(field, []) or []:
            if isinstance(record, dict) and isinstance(record.get("event_id"), str):
                ids.add(record["event_id"])
    return ids


def _history_event_ids(history: dict[str, Any]) -> set[str]:
    return {
        str(r["event_snapshot"].get("event_id"))
        for r in history["receipts"]
        if isinstance(r.get("event_snapshot"), dict) and r["event_snapshot"].get("event_id") is not None
    }


def _bind_dependency_identity(raw_event: Any, history: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_event, dict):
        raise IndependenceDerivationError("RAW_EVENT_OBJECT_REQUIRED")
    forbidden = sorted(FORBIDDEN_RAW_FIELDS & set(raw_event))
    if forbidden:
        raise IndependenceDerivationError("CALLER_ASSERTED_DERIVED_OR_DEPENDENCE_FIELD_FORBIDDEN:" + ",".join(forbidden))
    source_key = raw_event.get("source_event_key")
    if not isinstance(source_key, str) or not source_key:
        raise IndependenceDerivationError("SOURCE_EVENT_KEY_REQUIRED")
    registry = history["dependency_registry"]
    if source_key not in registry:
        raise IndependenceDerivationError("SOURCE_EVENT_KEY_NOT_IN_IMMUTABLE_REGISTRY")
    prepared = deepcopy(raw_event)
    for field in DEPENDENCE_FIELDS:
        prepared[field] = registry[source_key][field]
    return prepared


def derive_independence(state: Any, raw_event: Any, history: Any) -> dict[str, Any]:
    """Derive qualification from immutable registry + prior hash-chained event history."""
    validate_history(history)
    state_ids = _state_event_ids(state)
    history_ids = _history_event_ids(history)
    missing = sorted(state_ids - history_ids)
    if missing:
        raise IndependenceDerivationError("STATE_EVENT_HISTORY_DRIFT:" + ",".join(missing))

    prepared = _bind_dependency_identity(raw_event, history)
    snapshot = _event_snapshot(prepared)
    event_digest = _digest(snapshot)
    event_id = prepared.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise IndependenceDerivationError("EVENT_ID_REQUIRED")

    reasons: list[str] = []
    exact_replay = False
    for receipt in history["receipts"]:
        prior = receipt["event_snapshot"]
        prior_digest = receipt["event_digest"]
        if prior.get("event_id") == event_id:
            if prior_digest != event_digest:
                raise IndependenceDerivationError("EVENT_ID_DIGEST_COLLISION")
            exact_replay = True
            reasons.append("EXACT_EVENT_REPLAY")
        elif prior_digest == event_digest:
            reasons.append("DUPLICATE_IMMUTABLE_EVENT_CONTENT")
        if prior.get("correlation_ancestry_id") == prepared["correlation_ancestry_id"]:
            reasons.append("CORRELATION_ANCESTRY_REUSE")
        if prior.get("independence_group") == prepared["independence_group"]:
            reasons.append("DEPENDENCE_GROUP_REUSE")
        if prior.get("payload_key") == prepared["payload_key"]:
            reasons.append("PAYLOAD_REPACKAGING")

    reasons = sorted(set(reasons))
    qualified = not reasons
    prepared["independence_qualified"] = qualified
    return {
        "schema": SCHEMA,
        "pass": True,
        "prepared_event": prepared,
        "event_digest": event_digest,
        "independence_qualified": qualified,
        "independence_reasons": reasons,
        "exact_replay": exact_replay,
        "history_registry_digest": history["registry_digest"],
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "accepted_dataset_tokens_minted": 0,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }


def append_receipt(history: Any, derivation: dict[str, Any]) -> dict[str, Any]:
    validate_history(history)
    if derivation.get("schema") != SCHEMA or derivation.get("pass") is not True:
        raise IndependenceDerivationError("VALID_DERIVATION_REQUIRED")
    if derivation.get("exact_replay") is True:
        return deepcopy(history)
    out = deepcopy(history)
    snapshot = _event_snapshot(derivation["prepared_event"])
    basis = {
        "schema": RECEIPT_SCHEMA,
        "sequence": len(out["receipts"]) + 1,
        "previous_receipt_hash": out["last_receipt_hash"],
        "event_digest": _digest(snapshot),
        "event_snapshot": snapshot,
        "derived_independence_qualified": bool(derivation["independence_qualified"]),
        "derived_independence_reasons": list(derivation["independence_reasons"]),
        "registry_digest": out["registry_digest"],
    }
    receipt = {**basis, "receipt_hash": _receipt_hash(basis)}
    out["receipts"].append(receipt)
    out["last_receipt_hash"] = receipt["receipt_hash"]
    validate_history(out)
    return out


def bound_update(world: Any, state: Any, raw_event: Any, history: Any, *, expected_source_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    """Derive independence, then invoke the retained formal-world v3 labeler."""
    current_hashes = source_hashes()
    if expected_source_hashes is not None and expected_source_hashes != current_hashes:
        raise IndependenceDerivationError("SOURCE_HASH_BINDING_MISMATCH")
    derivation = derive_independence(state, raw_event, history)
    result = V3.u_state(world, state, derivation["prepared_event"])
    if not isinstance(result, dict) or result.get("pass") is not True:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failure": "V3_LABELER_REJECTED_PREPARED_EVENT",
            "v3_result": result,
            "source_hashes": current_hashes,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "accepted_dataset_tokens_minted": 0,
            "runtime_credit_minted": False,
            "training_credit_minted": False,
        }
    history_after = append_receipt(history, derivation)
    return {
        "schema": SCHEMA,
        "pass": True,
        "derivation": derivation,
        "v3_result": result,
        "history_after": history_after,
        "source_hashes": current_hashes,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "accepted_dataset_tokens_minted": 0,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": "Source/candidate derivation only; canonical admission and executable/model acceptance remain separate.",
    }
