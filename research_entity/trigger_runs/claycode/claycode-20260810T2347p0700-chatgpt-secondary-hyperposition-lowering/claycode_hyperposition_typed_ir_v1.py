from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import hashlib, json, random

DOMAIN = b"ClayCodeHyperpositionTypedIR/v1\x00"

class IRValidationError(ValueError):
    pass

def canon_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha(obj: Any, domain: bytes=b"") -> str:
    return hashlib.sha256(domain + canon_bytes(obj)).hexdigest()

@dataclass(frozen=True)
class HyperRelationIR:
    relation_id: str
    roles: tuple[str, ...]
    allowed: frozenset[tuple[Any, ...]]
    evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        if len(self.roles) < 2:
            raise IRValidationError("arity<2")
        if len(set(self.roles)) != len(self.roles):
            raise IRValidationError("duplicate role")
        for row in self.allowed:
            if len(row) != len(self.roles):
                raise IRValidationError("tuple arity mismatch")

    def semantic_payload(self) -> dict:
        self.validate()
        return {
            "schema": "HyperRelationIR/v1",
            "relation_id": self.relation_id,
            "roles": list(self.roles),
            "allowed": sorted([list(x) for x in self.allowed], key=lambda x: json.dumps(x, sort_keys=True)),
        }

    @property
    def semantic_hash(self) -> str:
        return sha(self.semantic_payload(), DOMAIN)

def lower_native(rel: HyperRelationIR) -> dict:
    rel.validate()
    physical = {
        "backend": "NATIVE_NARY",
        "semantic_hash": rel.semantic_hash,
        "arity": len(rel.roles),
        "tuples": sorted([list(x) for x in rel.allowed]),
    }
    return {**physical, "physical_hash": sha(physical, b"ClayHPPhysical/v1\x00")}

def lower_latent_star(rel: HyperRelationIR) -> dict:
    rel.validate()
    states=[]
    edges=[]
    for idx,row in enumerate(sorted(rel.allowed)):
        hid=f"h{idx}"
        states.append({"h":hid,"tuple":list(row)})
        for pos,role in enumerate(rel.roles):
            edges.append({"h":hid,"role":role,"value":row[pos]})
    physical={
        "backend":"LATENT_FACTOR_STAR",
        "semantic_hash":rel.semantic_hash,
        "latent_states":states,
        "compatibility_edges":edges,
    }
    return {**physical,"physical_hash":sha(physical,b"ClayHPPhysical/v1\x00")}

def decode_latent_star(plan: dict, rel: HyperRelationIR) -> HyperRelationIR:
    by_h={x["h"]:tuple(x["tuple"]) for x in plan["latent_states"]}
    for h,row in by_h.items():
        e=[x for x in plan["compatibility_edges"] if x["h"]==h]
        if len(e)!=len(rel.roles):
            raise IRValidationError("incomplete latent compatibility")
        emap={x["role"]:x["value"] for x in e}
        if set(emap)!=set(rel.roles):
            raise IRValidationError("role mismatch")
        if tuple(emap[r] for r in rel.roles)!=row:
            raise IRValidationError("latent tuple mismatch")
    out=HyperRelationIR(rel.relation_id,rel.roles,frozenset(by_h.values()),rel.evidence)
    out.validate()
    if out.semantic_hash != rel.semantic_hash:
        raise IRValidationError("semantic hash drift")
    return out

def fuzz(seed=0xC1A7, trials=2000):
    rng=random.Random(seed)
    mismatches=0
    semantic_hash_drift=0
    physical_hash_equal=0
    malformed_rejected=0
    from itertools import product
    for i in range(trials):
        arity=rng.randint(3,6)
        roles=tuple(f"r{j}" for j in range(arity))
        domains=[list(range(rng.randint(2,4))) for _ in roles]
        universe=list(product(*domains))
        allowed=frozenset(rng.sample(universe,rng.randint(1,len(universe))))
        rel=HyperRelationIR(f"R{i}",roles,allowed)
        n=lower_native(rel)
        l=lower_latent_star(rel)
        dec=decode_latent_star(l,rel)
        mismatches += (dec.allowed != rel.allowed)
        semantic_hash_drift += (n["semantic_hash"] != l["semantic_hash"])
        physical_hash_equal += (n["physical_hash"] == l["physical_hash"])
        if l["compatibility_edges"]:
            bad={**l,"compatibility_edges":l["compatibility_edges"][1:]}
            try:
                decode_latent_star(bad,rel)
            except IRValidationError:
                malformed_rejected += 1
    return {
        "trials":trials,
        "projection_mismatches":mismatches,
        "semantic_hash_drift_across_backends":semantic_hash_drift,
        "physical_hash_equal_across_backends":physical_hash_equal,
        "malformed_latent_plan_rejected":malformed_rejected,
    }

if __name__ == "__main__":
    xor=HyperRelationIR("xor3",("a","b","c"),frozenset({(0,0,0),(0,1,1),(1,0,1),(1,1,0)}))
    native=lower_native(xor)
    latent=lower_latent_star(xor)
    out={
        "xor":{
            "semantic_hash":xor.semantic_hash,
            "native_physical_hash":native["physical_hash"],
            "latent_physical_hash":latent["physical_hash"],
            "semantic_hash_same":native["semantic_hash"]==latent["semantic_hash"],
            "physical_hash_diff":native["physical_hash"]!=latent["physical_hash"],
            "roundtrip_equal":decode_latent_star(latent,xor).allowed==xor.allowed,
        },
        "fuzz":fuzz(),
    }
    print(json.dumps(out,indent=2,sort_keys=True))
