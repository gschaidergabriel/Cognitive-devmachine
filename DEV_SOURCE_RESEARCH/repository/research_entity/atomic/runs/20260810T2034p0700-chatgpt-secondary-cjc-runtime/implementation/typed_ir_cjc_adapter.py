#!/usr/bin/env python3
"""
Strict WP03/WP04 -> Counterfactual Jet Commutator adapter.

This research adapter deliberately does NOT infer transition semantics from ClayCode names,
caller constraints, body text, model output, or read/write similarity.

A transition becomes CJC-exact-eligible only when:
  * the WP03 bridge supplies a current typed semantic identity + state instance identity;
  * an explicit CJC TransitionSpec supplies operator semantics;
  * an admitted exact-call/runtime binding receipt (when a call target is involved) matches;
  * the effect class is PURE or INTERNAL_STATE;
  * epoch/version/provenance are explicit.

The adapter is therefore a falsifier for the tempting but forbidden shortcut
"name resembles operation -> invent exact causal/commutativity semantics".
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from causal_jet_commutator import (
    Add,
    CopyAdd,
    EffectClass,
    Scale,
    SetValue,
    StateIdentity,
    Swap,
    Transition,
    TransitionContract,
)


class AdapterError(ValueError):
    pass


EXPECTED_BRIDGE_SCHEMA = "ClayCodeBaseV18FrontendTypedIRBridge/v1"
ALLOWED_EXACT_EFFECTS = {"PURE", "INTERNAL_STATE"}


@dataclass(frozen=True)
class TypedIRRuntimeIdentity:
    semantic_id: str
    state_epoch: str
    state_version: str
    state_instance_id: str
    declared_fields: frozenset[str]


@dataclass(frozen=True)
class ExactCallAdmission:
    admitted: bool
    target: str
    arity: int
    contract_semantic_hash: str
    runtime_component_sha256: str
    effect_class: str
    effect_authority_minted_by_resolver: bool

    @classmethod
    def from_mapping(cls, obj: Mapping[str, Any]) -> "ExactCallAdmission":
        required = {
            "admitted", "target", "arity", "contract_semantic_hash",
            "runtime_component_sha256", "effect_class", "effect_authority_minted_by_resolver",
        }
        missing = required - set(obj)
        if missing:
            raise AdapterError(f"call admission missing fields: {sorted(missing)}")
        return cls(
            admitted=bool(obj["admitted"]), target=str(obj["target"]), arity=int(obj["arity"]),
            contract_semantic_hash=str(obj["contract_semantic_hash"]),
            runtime_component_sha256=str(obj["runtime_component_sha256"]),
            effect_class=str(obj["effect_class"]),
            effect_authority_minted_by_resolver=bool(obj["effect_authority_minted_by_resolver"]),
        )

    def validate_non_authoritative(self) -> None:
        if not self.admitted:
            raise AdapterError("call was not admitted")
        if self.effect_authority_minted_by_resolver:
            raise AdapterError("resolver illegally minted effect authority")
        if len(self.contract_semantic_hash) != 64:
            raise AdapterError("invalid call contract semantic hash")
        if len(self.runtime_component_sha256) != 64:
            raise AdapterError("invalid runtime component hash")
        if self.effect_class not in {"PURE", "READ_ONLY", "INTERNAL_STATE", "EXTERNAL_EFFECT"}:
            raise AdapterError("unknown effect class")


@dataclass(frozen=True)
class TransitionSpec:
    transition_id: str
    use_ref: str
    version: str
    operator: str
    params: Mapping[str, Any]
    reads: frozenset[str]
    writes: frozenset[str]
    evidence_refs: tuple[str, ...]
    effect_class: str = "INTERNAL_STATE"
    call_target: str | None = None
    call_arity: int | None = None
    expected_call_contract_hash: str | None = None

    @classmethod
    def from_mapping(cls, obj: Mapping[str, Any]) -> "TransitionSpec":
        required = {"transition_id", "use_ref", "version", "operator", "params", "reads", "writes", "evidence_refs"}
        missing = required - set(obj)
        if missing:
            raise AdapterError(f"transition spec missing fields: {sorted(missing)}")
        return cls(
            transition_id=str(obj["transition_id"]), use_ref=str(obj["use_ref"]),
            version=str(obj["version"]), operator=str(obj["operator"]).upper(), params=dict(obj["params"]),
            reads=frozenset(str(x) for x in obj["reads"]), writes=frozenset(str(x) for x in obj["writes"]),
            evidence_refs=tuple(str(x) for x in obj["evidence_refs"]),
            effect_class=str(obj.get("effect_class", "INTERNAL_STATE")),
            call_target=None if obj.get("call_target") is None else str(obj["call_target"]),
            call_arity=None if obj.get("call_arity") is None else int(obj["call_arity"]),
            expected_call_contract_hash=None if obj.get("expected_call_contract_hash") is None else str(obj["expected_call_contract_hash"]),
        )


def identity_from_wp03_bridge(bridge: Mapping[str, Any]) -> TypedIRRuntimeIdentity:
    if bridge.get("bridge_schema") != EXPECTED_BRIDGE_SCHEMA:
        raise AdapterError("unexpected/missing WP03 bridge schema")
    semantic_id = bridge.get("semantic_identity")
    if not isinstance(semantic_id, str) or not semantic_id.startswith("clayir:"):
        raise AdapterError("missing/invalid ClayCode semantic identity")
    state = bridge.get("state_identity")
    if not isinstance(state, Mapping):
        raise AdapterError("missing state_identity")
    if state.get("semantic_id") != semantic_id:
        raise AdapterError("state semantic identity does not match typed IR")
    epoch, version, state_instance_id = state.get("state_epoch"), state.get("state_version"), state.get("state_instance_id")
    if epoch is None or version is None:
        raise AdapterError("state epoch/version not bound")
    if not isinstance(state_instance_id, str) or not state_instance_id.startswith("claystate:"):
        raise AdapterError("state instance identity missing/invalid")
    authority = bridge.get("authority")
    if not isinstance(authority, Mapping):
        raise AdapterError("bridge authority invariants missing")
    if authority.get("typed_ir_description_mints_effect_authority") is not False:
        raise AdapterError("typed IR description authority invariant violated")
    if authority.get("frontend_artifact_mints_effect_authority") is not False:
        raise AdapterError("frontend authority invariant violated")
    declared_fields: set[str] = set()
    ir = bridge.get("typed_ir", {})
    for decl in ir.get("declarations", []) if isinstance(ir, Mapping) else []:
        if decl.get("kind") == "record":
            for field in decl.get("fields", []):
                name = field.get("name")
                if isinstance(name, str) and name:
                    declared_fields.add(name)
    return TypedIRRuntimeIdentity(semantic_id, str(epoch), str(version), state_instance_id, frozenset(declared_fields))


def state_identity_for_cjc(runtime: TypedIRRuntimeIdentity) -> StateIdentity:
    return StateIdentity(runtime.semantic_id, runtime.state_epoch, runtime.state_version, runtime.state_instance_id)


def validate_spec(runtime: TypedIRRuntimeIdentity, spec: TransitionSpec, admission: ExactCallAdmission | None = None) -> None:
    if not spec.transition_id or not spec.use_ref or not spec.version:
        raise AdapterError("transition identity/use/version must be explicit")
    if not spec.evidence_refs:
        raise AdapterError("transition spec lacks evidence provenance")
    if spec.effect_class not in ALLOWED_EXACT_EFFECTS:
        raise AdapterError("CJC exact lift is limited to PURE or INTERNAL_STATE")
    if not spec.writes:
        raise AdapterError("transition spec must write at least one explicit field")
    if runtime.declared_fields:
        unknown_fields = (spec.reads | spec.writes) - runtime.declared_fields
        if unknown_fields:
            raise AdapterError(f"transition touches undeclared field(s): {sorted(unknown_fields)}")
    if spec.call_target is None:
        if any(x is not None for x in (spec.call_arity, spec.expected_call_contract_hash)):
            raise AdapterError("partial call-binding metadata without call_target")
        if admission is not None:
            raise AdapterError("unexpected call admission for non-call transition")
    else:
        if spec.call_arity is None or spec.expected_call_contract_hash is None:
            raise AdapterError("call transition lacks exact arity/contract hash")
        if admission is None:
            raise AdapterError("call transition lacks exact admitted runtime binding")
        admission.validate_non_authoritative()
        if admission.target != spec.call_target:
            raise AdapterError("call target mismatch")
        if admission.arity != spec.call_arity:
            raise AdapterError("call arity mismatch")
        if admission.contract_semantic_hash != spec.expected_call_contract_hash:
            raise AdapterError("call contract semantic hash mismatch")
        if admission.effect_class != spec.effect_class:
            raise AdapterError("call effect class mismatch")


def compile_transition(runtime: TypedIRRuntimeIdentity, spec: TransitionSpec, admission: ExactCallAdmission | None = None) -> Transition:
    validate_spec(runtime, spec, admission)
    contract = TransitionContract(
        transition_id=spec.transition_id, use_ref=spec.use_ref, version=spec.version,
        state_epoch=runtime.state_epoch, effect_class=EffectClass(spec.effect_class),
        reads=spec.reads, writes=spec.writes, evidence_refs=tuple(sorted(set(spec.evidence_refs))),
        deterministic=True, reversible_internal=True,
    )
    p, op = spec.params, spec.operator
    if op == "ADD":
        field, amount = str(p["field"]), int(p["amount"])
        if spec.reads != {field} or spec.writes != {field}: raise AdapterError("ADD read/write contract mismatch")
        return Add(contract, field, amount)
    if op == "SET":
        field, value = str(p["field"]), int(p["value"])
        if spec.reads != {field} or spec.writes != {field}: raise AdapterError("SET read/write contract mismatch")
        return SetValue(contract, field, value)
    if op == "SCALE":
        field, factor = str(p["field"]), int(p["factor"])
        if spec.reads != {field} or spec.writes != {field}: raise AdapterError("SCALE read/write contract mismatch")
        return Scale(contract, field, factor)
    if op == "COPY_ADD":
        src, dst, factor = str(p["src"]), str(p["dst"]), int(p.get("factor", 1))
        if spec.reads != {src, dst} or spec.writes != {dst}: raise AdapterError("COPY_ADD read/write contract mismatch")
        return CopyAdd(contract, src, dst, factor)
    if op == "SWAP":
        left, right = str(p["left"]), str(p["right"])
        if left == right: raise AdapterError("SWAP fields must differ")
        if spec.reads != {left, right} or spec.writes != {left, right}: raise AdapterError("SWAP read/write contract mismatch")
        return Swap(contract, left, right)
    raise AdapterError(f"unsupported explicit operator semantics: {op!r}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bridge", type=Path, required=True)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--admission", type=Path)
    args = ap.parse_args()
    runtime = identity_from_wp03_bridge(load_json(args.bridge))
    spec = TransitionSpec.from_mapping(load_json(args.spec))
    admission = ExactCallAdmission.from_mapping(load_json(args.admission)) if args.admission else None
    transition = compile_transition(runtime, spec, admission)
    print(json.dumps({
        "compiled": True, "semantic_id": runtime.semantic_id, "state_instance_id": runtime.state_instance_id,
        "transition_contract_hash": transition.contract.semantic_hash, "operator_class": type(transition).__name__,
        "effect_authority_minted": False, "inference_from_name_or_similarity": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
