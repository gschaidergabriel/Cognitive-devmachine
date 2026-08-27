#!/usr/bin/env python3
"""Exact, fail-closed ClayCode CallContract/runtime-binding resolver.

GO independent adversarial research probe for CC-WP-03/WP-04/WP-05. This module is
NOT a production implementation lane and is NOT a source of Clay semantic authority: it
never invents CallContracts. Contracts must be supplied with evidence/provenance by an
upstream ClayCode-native contract source.

Admission requires exact target+arity, exact typed arguments, explicit concrete return,
unique contract identity, and a current runtime binding. Effectful calls have an additional
sealed authority+rollback boundary. Diagnostic alternatives never become admission.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Literal

FORBIDDEN_DYNAMIC_TYPES = {"Any", "Unknown", "Dynamic", "Opaque"}
NON_EFFECT_CLASSES = {"PURE", "READ_ONLY", "INTERNAL_STATE"}
EFFECT_CLASS = {"PURE", "READ_ONLY", "INTERNAL_STATE", "EXTERNAL_EFFECT"}
DOMAIN = b"ClayCodeCallContract/v1\x00"


class CallContractError(ValueError):
    pass


@dataclass(frozen=True)
class CallContract:
    target: str
    param_types: tuple[str, ...]
    return_type: str
    effect_class: Literal["PURE", "READ_ONLY", "INTERNAL_STATE", "EXTERNAL_EFFECT"]
    evidence_refs: tuple[str, ...]

    @property
    def arity(self) -> int:
        return len(self.param_types)

    @property
    def semantic_hash(self) -> str:
        payload = {
            "target": self.target,
            "arity": self.arity,
            "param_types": list(self.param_types),
            "return_type": self.return_type,
            "effect_class": self.effect_class,
            "evidence_refs": sorted(self.evidence_refs),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return hashlib.sha256(DOMAIN + raw).hexdigest()


@dataclass(frozen=True)
class RuntimeBinding:
    target: str
    arity: int
    contract_semantic_hash: str
    component_sha256: str
    work_revision: str
    target_binary_sha256: str
    state_lineage_epoch: str
    instance_lease_ref: str
    instance_lease_epoch: str
    sealed: bool = True
    authority_scope: str | None = None
    rollback_ref: str | None = None


@dataclass(frozen=True)
class CurrentExecutionIdentity:
    work_revision: str
    target_binary_sha256: str
    state_lineage_epoch: str
    instance_lease_ref: str
    instance_lease_epoch: str


@dataclass(frozen=True)
class CallSite:
    target: str
    arg_types: tuple[str, ...]

    @property
    def arity(self) -> int:
        return len(self.arg_types)


def _concrete_type(typ: str) -> bool:
    if not isinstance(typ, str) or not typ.strip():
        return False
    atoms = []
    cur = ""
    for ch in typ:
        if ch.isalnum() or ch in "_.":
            cur += ch
        else:
            if cur:
                atoms.append(cur)
                cur = ""
    if cur:
        atoms.append(cur)
    return not any(atom in FORBIDDEN_DYNAMIC_TYPES for atom in atoms)


def validate_contract(contract: CallContract) -> None:
    if not contract.target or contract.target.strip() != contract.target:
        raise CallContractError("invalid exact target")
    if contract.effect_class not in EFFECT_CLASS:
        raise CallContractError("invalid effect class")
    if not contract.evidence_refs:
        raise CallContractError("contract lacks evidence provenance")
    if not all(_concrete_type(t) for t in contract.param_types):
        raise CallContractError("parameter types must be explicit/concrete")
    if not _concrete_type(contract.return_type):
        raise CallContractError("return type must be explicit/concrete")


def exact_contract(site: CallSite, contracts: Iterable[CallContract]) -> CallContract:
    hits = []
    for contract in contracts:
        validate_contract(contract)
        if contract.target == site.target and contract.arity == site.arity:
            hits.append(contract)
    if not hits:
        raise CallContractError("no exact target+arity CallContract")
    hashes = {c.semantic_hash for c in hits}
    if len(hits) != 1 or len(hashes) != 1:
        raise CallContractError("ambiguous exact CallContract identity")
    return hits[0]


def validate_types(site: CallSite, contract: CallContract) -> None:
    if site.arg_types != contract.param_types:
        raise CallContractError(
            f"argument type mismatch: site={site.arg_types!r} contract={contract.param_types!r}"
        )


def validate_current_binding(
    contract: CallContract,
    binding: RuntimeBinding,
    current: CurrentExecutionIdentity,
) -> None:
    if not binding.sealed:
        raise CallContractError("runtime binding is not sealed")
    if (binding.target, binding.arity) != (contract.target, contract.arity):
        raise CallContractError("runtime binding target/arity mismatch")
    if binding.contract_semantic_hash != contract.semantic_hash:
        raise CallContractError("runtime binding contract hash mismatch")
    if not binding.component_sha256 or len(binding.component_sha256) != 64:
        raise CallContractError("runtime component hash missing/invalid")
    current_pairs = [
        (binding.work_revision, current.work_revision, "work revision"),
        (binding.target_binary_sha256, current.target_binary_sha256, "target binary"),
        (binding.state_lineage_epoch, current.state_lineage_epoch, "state-lineage epoch"),
        (binding.instance_lease_ref, current.instance_lease_ref, "instance lease ref"),
        (binding.instance_lease_epoch, current.instance_lease_epoch, "instance lease epoch"),
    ]
    for observed, expected, label in current_pairs:
        if not observed or observed != expected:
            raise CallContractError(f"stale/mismatched {label}")
    if contract.effect_class == "EXTERNAL_EFFECT":
        if not binding.authority_scope:
            raise CallContractError("external effect lacks explicit authority scope")
        if not binding.rollback_ref:
            raise CallContractError("external effect lacks rollback/recovery reference")
    elif binding.authority_scope or binding.rollback_ref:
        raise CallContractError("non-effect contract carries effect authority/rollback metadata")


def admit_call(
    site: CallSite,
    contracts: Iterable[CallContract],
    bindings: Iterable[RuntimeBinding],
    current: CurrentExecutionIdentity,
) -> dict:
    contract = exact_contract(site, contracts)
    validate_types(site, contract)
    exact_bindings = [
        b for b in bindings if (b.target, b.arity) == (contract.target, contract.arity)
    ]
    if len(exact_bindings) != 1:
        raise CallContractError("missing or ambiguous exact runtime binding")
    binding = exact_bindings[0]
    validate_current_binding(contract, binding, current)
    return {
        "admitted": True,
        "target": contract.target,
        "arity": contract.arity,
        "contract_semantic_hash": contract.semantic_hash,
        "runtime_component_sha256": binding.component_sha256,
        "effect_class": contract.effect_class,
        "effect_authority_minted_by_resolver": False,
    }


def diagnostic_alternatives(site: CallSite, contracts: Iterable[CallContract]) -> list[dict]:
    """Similarity hints for humans/tools only. Never consumed by admit_call."""
    out = []
    for c in contracts:
        same_leaf = c.target.rsplit(".", 1)[-1] == site.target.rsplit(".", 1)[-1]
        if same_leaf or c.target == site.target:
            out.append({"target": c.target, "arity": c.arity, "diagnostic_only": True})
    return sorted(out, key=lambda x: (x["target"], x["arity"]))
