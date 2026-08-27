#!/usr/bin/env python3
"""CC-RC1.4 research reference: Certified Basis + Compositional Closure.

Research-only executable semantics. It demonstrates four rules:
1) operation-specific typed basis witnesses, not one universal "latest" check;
2) compositional effect/dependency closure over calls and finite dynamic dispatch;
3) canonical resource identity before conflict/capability reasoning;
4) model-facing projection receipt separate from semantic identity and authority.

This is not the production FRANK kernel and does not claim complete Python/FFI analysis.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import FrozenSet, Iterable, Mapping, Optional, Set, Tuple


def h(tag: str, obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256((tag + ":" + payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BasisRequirement:
    kind: str
    name: str
    expected_version: str
    policy: str = "EXACT"


@dataclass(frozen=True)
class OpSpec:
    op_id: str
    semantics_hash: str
    direct_resources: FrozenSet[str] = frozenset()
    predicates: FrozenSet[str] = frozenset()
    invariants: FrozenSet[str] = frozenset()
    volatile_inputs: FrozenSet[str] = frozenset()
    required_caps: FrozenSet[str] = frozenset()
    calls: FrozenSet[str] = frozenset()
    dynamic_targets: Optional[FrozenSet[str]] = frozenset()
    basis_requirements: Tuple[BasisRequirement, ...] = ()


@dataclass(frozen=True)
class Closure:
    resources: FrozenSet[str]
    predicates: FrozenSet[str]
    invariants: FrozenSet[str]
    volatile_inputs: FrozenSet[str]
    required_caps: FrozenSet[str]
    op_semantics: FrozenSet[Tuple[str, str]]
    complete: bool


@dataclass(frozen=True)
class ProjectionReceipt:
    semantic_hash: str
    projection_schema_hash: str
    projection_hash: str


def canonical_resource(name: str, alias_map: Mapping[str, str]) -> str:
    seen: Set[str] = set()
    cur = name
    while cur in alias_map:
        if cur in seen:
            raise ValueError("alias cycle")
        seen.add(cur)
        cur = alias_map[cur]
    return cur


def derive_closure(op_id: str, registry: Mapping[str, OpSpec], alias_map: Mapping[str, str]) -> Closure:
    seen: Set[str] = set(); resources: Set[str] = set(); predicates: Set[str] = set()
    invariants: Set[str] = set(); volatile: Set[str] = set(); caps: Set[str] = set()
    sem: Set[Tuple[str, str]] = set(); complete = True

    def visit(oid: str) -> None:
        nonlocal complete
        if oid in seen:
            return
        seen.add(oid)
        spec = registry[oid]
        sem.add((spec.op_id, spec.semantics_hash))
        resources.update(canonical_resource(x, alias_map) for x in spec.direct_resources)
        predicates.update(spec.predicates); invariants.update(spec.invariants)
        volatile.update(spec.volatile_inputs); caps.update(spec.required_caps)
        for child in spec.calls:
            visit(child)
        if spec.dynamic_targets is None:
            complete = False
        else:
            for target in spec.dynamic_targets:
                visit(target)

    visit(op_id)
    return Closure(frozenset(resources), frozenset(predicates), frozenset(invariants),
                   frozenset(volatile), frozenset(caps), frozenset(sem), complete)


def basis_compatible(requirements: Iterable[BasisRequirement], current: Mapping[Tuple[str, str], str]) -> bool:
    for r in requirements:
        cur = current.get((r.kind, r.name))
        if r.policy == "EXACT":
            if cur != r.expected_version:
                return False
        else:
            return False  # unknown compatibility policy fails closed in this minimal kernel
    return True


def trace_within_closure(trace, closure: Closure, alias_map: Mapping[str, str]) -> bool:
    if not closure.complete:
        return False
    observed_resources = {canonical_resource(x, alias_map) for x in trace.get("resources", [])}
    return (observed_resources <= closure.resources
            and set(trace.get("predicates", [])) <= closure.predicates
            and set(trace.get("invariants", [])) <= closure.invariants
            and set(trace.get("volatile_inputs", [])) <= closure.volatile_inputs
            and set(trace.get("required_caps", [])) <= closure.required_caps)


def make_projection_receipt(semantic_obj, projection_schema, projection_bytes: bytes) -> ProjectionReceipt:
    return ProjectionReceipt(h("semantic:v1", semantic_obj), h("projection-schema:v1", projection_schema),
                             sha256(b"projection:v1:" + projection_bytes).hexdigest())


def self_test() -> dict:
    alias = {"user_alias_A":"account:42", "user_alias_B":"account:42"}
    registry = {
        "read": OpSpec("read","s1",frozenset({"user_alias_A"})),
        "notify": OpSpec("notify","s2",frozenset({"mailbox:7"}),required_caps=frozenset({"cap:mail"})),
        "dispatch": OpSpec("dispatch","s3",calls=frozenset({"read"}),dynamic_targets=frozenset({"notify"}),
            basis_requirements=(BasisRequirement("frame","cognitive","f9"),BasisRequirement("graph","semantic","g12"),BasisRequirement("activation","latent","a31"))),
        "reflect": OpSpec("reflect","s4",dynamic_targets=None),
    }
    c = derive_closure("dispatch", registry, alias)
    assert c.complete and "account:42" in c.resources and "mailbox:7" in c.resources and "cap:mail" in c.required_caps
    assert trace_within_closure({"resources":["user_alias_B","mailbox:7"],"required_caps":["cap:mail"]}, c, alias)
    assert not derive_closure("reflect", registry, alias).complete
    current={("frame","cognitive"):"f9",("graph","semantic"):"g12",("activation","latent"):"a31",("unrelated","telemetry"):"z999"}
    assert basis_compatible(registry["dispatch"].basis_requirements,current)
    stale=dict(current); stale[("activation","latent")]="a32"; assert not basis_compatible(registry["dispatch"].basis_requirements,stale)
    changed=dict(current); changed[("unrelated","telemetry")]="z1000"; assert basis_compatible(registry["dispatch"].basis_requirements,changed)
    sem={"op":"dispatch","args":{"x":1}}; schema={"fields":["op","args"],"version":3}
    p1=make_projection_receipt(sem,schema,b'["dispatch",{"x":1}]'); p2=make_projection_receipt(sem,schema,b'[ "dispatch", {"x":1} ]')
    assert p1.semantic_hash==p2.semantic_hash and p1.projection_hash!=p2.projection_hash
    return {"closure_complete":c.complete,"canonical_resources":sorted(c.resources),"caps":sorted(c.required_caps),"unknown_dynamic_fails_closed":True,"stale_required_epoch_rejected":True,"unrelated_epoch_churn_allowed":True,"semantic_identity_independent_of_wire":True}


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
