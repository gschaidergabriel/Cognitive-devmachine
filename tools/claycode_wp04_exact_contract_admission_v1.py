#!/usr/bin/env python3
"""Fail-closed WP04 exact CallContract admission checker.

Research/build candidate for the selected V18 call-contract frontier.  This tool does
*not* infer callable signatures.  It accepts only an explicit typed declaration or an
exact runtime-export contract whose target/arity/types/return/effect class are directly
present in the evidence record.  Caller constraints, fuzzy names, type-name resemblance,
model output and graph salience are non-authoritative evidence classes.

Admission of a semantic CallContract is deliberately separate from execution admission.
A runtime binding is validated as a second identity layer and even a valid pair remains
non-executable until WP05 type/effect/evaluator gates consume it.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "ClayCodeExactCallContractAdmission/v1-research"
DOMAIN = b"ClayCodeExactCallContract/v1\x00"
BINDING_DOMAIN = b"ClayCodeCallRuntimeBinding/v1\x00"

ALLOWED_EVIDENCE_KINDS = {
    "EXPLICIT_TYPED_CALLABLE_DECLARATION",
    "EXACT_RUNTIME_EXPORT_CONTRACT",
}
REJECTED_INFERENCE_KINDS = {
    "CALLER_CONSTRAINTS",
    "TARGET_NAME_SIMILARITY",
    "BASENAME_OR_SUFFIX_MATCH",
    "TYPE_NAME_RESEMBLANCE",
    "HISTORICAL_ROLE_SIMILARITY",
    "MODEL_OUTPUT",
    "CLAYGRAPH_SALIENCE",
}
EFFECT_CLASSES = {"PURE", "READ_STATE", "DERIVED_STATE", "RESEARCH_ONLY", "EXTERNAL_EFFECT"}
FORBIDDEN_ESCAPE_TYPES = {"Any", "Unknown", "Dynamic", "OpaqueParam"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ContractAdmissionError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + stable_json(value)).hexdigest()


def _nonempty_symbol(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractAdmissionError(f"{label} must be a non-empty exact symbol")
    return value


def _validate_type(type_name: Any, label: str) -> str:
    value = _nonempty_symbol(type_name, label)
    if value in FORBIDDEN_ESCAPE_TYPES:
        raise ContractAdmissionError(f"{label} uses forbidden dynamic escape type {value}")
    return value


def admit_exact_contract(obligation: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Admit semantic contract identity only from exact explicit evidence."""
    identity = obligation.get("identity")
    if not isinstance(identity, dict):
        raise ContractAdmissionError("obligation.identity missing")
    target = _nonempty_symbol(identity.get("target"), "obligation target")
    arity = identity.get("arity")
    if not isinstance(arity, int) or arity < 0:
        raise ContractAdmissionError("obligation arity must be non-negative int")

    kind = evidence.get("kind")
    if kind in REJECTED_INFERENCE_KINDS:
        raise ContractAdmissionError(f"non-authoritative signature evidence kind: {kind}")
    if kind not in ALLOWED_EVIDENCE_KINDS:
        raise ContractAdmissionError(f"unsupported signature evidence kind: {kind!r}")

    ev_target = _nonempty_symbol(evidence.get("target"), "evidence target")
    if ev_target != target:
        raise ContractAdmissionError(f"exact target mismatch: {ev_target!r} != {target!r}")
    ev_arity = evidence.get("arity")
    if ev_arity != arity:
        raise ContractAdmissionError(f"exact arity mismatch: {ev_arity!r} != {arity!r}")

    params = evidence.get("params")
    if not isinstance(params, list) or len(params) != arity:
        raise ContractAdmissionError("parameter list must exist and exactly match arity")
    normalized_params = []
    for i, param in enumerate(params):
        if not isinstance(param, dict):
            raise ContractAdmissionError(f"param {i} must be typed object")
        normalized_params.append({
            "name": _nonempty_symbol(param.get("name"), f"param {i} name"),
            "type_name": _validate_type(param.get("type_name"), f"param {i} type"),
        })

    returns = _validate_type(evidence.get("returns"), "return type")
    effect_class = evidence.get("effect_class")
    if effect_class not in EFFECT_CLASSES:
        raise ContractAdmissionError(f"invalid or missing effect class: {effect_class!r}")

    evidence_ref = _nonempty_symbol(evidence.get("evidence_ref"), "evidence_ref")
    source_sha256 = evidence.get("source_sha256")
    if not isinstance(source_sha256, str) or not HEX64.fullmatch(source_sha256):
        raise ContractAdmissionError("source_sha256 must be exact lowercase SHA-256")

    core = {
        "identity": {"target": target, "arity": arity},
        "params": normalized_params,
        "returns": returns,
        "effect_class": effect_class,
    }
    contract_hash = digest(DOMAIN, core)
    return {
        "schema": SCHEMA,
        "status": "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING",
        "contract": core,
        "contract_semantic_hash": contract_hash,
        "evidence": {
            "kind": kind,
            "evidence_ref": evidence_ref,
            "source_sha256": source_sha256,
        },
        "execution_admitted": False,
        "truth_authority": "NONE",
        "effect_authority": "NONE_FROM_CONTRACT",
        "inference_used": False,
    }


def validate_runtime_binding(contract_row: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    """Validate current runtime identity without minting execution/effect authority."""
    contract_hash = contract_row.get("contract_semantic_hash")
    if not isinstance(contract_hash, str) or not HEX64.fullmatch(contract_hash):
        raise ContractAdmissionError("valid contract_semantic_hash required")

    required_hashes = ["runtime_component_hash", "target_binary_build_hash"]
    normalized: dict[str, Any] = {"contract_semantic_hash": contract_hash}
    for key in required_hashes:
        value = binding.get(key)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise ContractAdmissionError(f"{key} must be exact lowercase SHA-256")
        normalized[key] = value

    normalized["current_work_revision"] = _nonempty_symbol(binding.get("current_work_revision"), "current_work_revision")
    epoch = binding.get("state_lineage_epoch")
    lease_epoch = binding.get("instance_lease_epoch")
    if not isinstance(epoch, int) or epoch < 0:
        raise ContractAdmissionError("state_lineage_epoch must be non-negative int")
    if not isinstance(lease_epoch, int) or lease_epoch < 0:
        raise ContractAdmissionError("instance_lease_epoch must be non-negative int")
    normalized["state_lineage_epoch"] = epoch
    normalized["instance_lease_ref"] = _nonempty_symbol(binding.get("instance_lease_ref"), "instance_lease_ref")
    normalized["instance_lease_epoch"] = lease_epoch

    effect_class = contract_row.get("contract", {}).get("effect_class")
    sealed = binding.get("sealed") is True
    normalized["sealed"] = sealed
    normalized["authority_scope_ref"] = binding.get("authority_scope_ref")
    normalized["rollback_ref"] = binding.get("rollback_ref")

    if effect_class == "EXTERNAL_EFFECT":
        if not sealed:
            raise ContractAdmissionError("EXTERNAL_EFFECT runtime binding must be sealed")
        if not isinstance(binding.get("authority_scope_ref"), str) or not binding["authority_scope_ref"]:
            raise ContractAdmissionError("EXTERNAL_EFFECT requires explicit authority_scope_ref")
        if not isinstance(binding.get("rollback_ref"), str) or not binding["rollback_ref"]:
            raise ContractAdmissionError("EXTERNAL_EFFECT requires rollback_ref")

    return {
        "schema": SCHEMA,
        "status": "BOUND_CURRENT_RUNTIME_NONEXECUTABLE_UNTIL_WP05",
        "binding": normalized,
        "runtime_binding_hash": digest(BINDING_DOMAIN, normalized),
        "execution_admitted": False,
        "truth_authority": "NONE",
        "effect_authority": "RUNTIME_BROKER_ONLY_IF_SEPARATELY_AUTHORIZED" if effect_class == "EXTERNAL_EFFECT" else "NONE",
    }


def main() -> int:
    # Intentionally library-first. Production population must pass repository/runtime evidence,
    # not CLI guesses. Tests exercise the executable admission boundary.
    print(json.dumps({
        "schema": SCHEMA,
        "status": "READY",
        "signature_inference": "FORBIDDEN",
        "execution_admitted": False,
        "effect_authority": "NONE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
