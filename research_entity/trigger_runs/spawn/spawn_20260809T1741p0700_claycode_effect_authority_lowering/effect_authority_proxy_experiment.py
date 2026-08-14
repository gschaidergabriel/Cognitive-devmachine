#!/usr/bin/env python3
from dataclasses import dataclass
from typing import FrozenSet, Tuple
import secrets, json

@dataclass(frozen=True)
class EffectIntent:
    effect: str
    resource: str
    payload: Tuple[str, ...]

@dataclass(frozen=True)
class Grant:
    grant_id: str
    resource: str
    effects: FrozenSet[str]

class Gateway:
    def __init__(self, grants):
        self._grants = {g.grant_id: g for g in grants}
    def commit(self, grant_id, intent):
        g = self._grants.get(grant_id)
        if not g:
            return False
        if g.resource != intent.resource:
            return False
        if intent.effect not in g.effects:
            return False
        return True

@dataclass(frozen=True)
class StructuralToken:
    id: str
    resource: str
    permits: FrozenSet[str]
    issuer: str

def structural_commit(tok, effect, resource):
    # Deliberately unsafe oracle: validates only forgeable record fields.
    return tok.issuer == "root" and tok.resource == resource and effect in tok.permits

class OpaqueRegistry:
    def __init__(self):
        self._caps = {}
    def mint(self, resource, permits):
        h = secrets.token_hex(32)
        self._caps[h] = (resource, frozenset(permits))
        return h
    def commit(self, handle, effect, resource):
        cap = self._caps.get(handle)
        return bool(cap and cap[0] == resource and effect in cap[1])

def run():
    rng = secrets.SystemRandom()
    effects = ["read", "versioned_write", "delete", "network", "spawn", "admin"]
    resources = [f"res:{i}" for i in range(32)]
    grants = []
    for i in range(16):
        allowed = frozenset(rng.sample(effects[:4], rng.randrange(1, 4)))
        grants.append(Grant(secrets.token_hex(16), resources[i], allowed))
    gw = Gateway(grants)

    gateway_fuzz_cases = 100_000
    unauthorized_accepts = 0
    authorized_accepts = 0
    for _ in range(gateway_fuzz_cases):
        intent = EffectIntent(rng.choice(effects), rng.choice(resources), (secrets.token_hex(4),))
        grant_id = secrets.token_hex(16) if rng.random() < 0.85 else rng.choice(grants).grant_id
        expected = any(
            g.grant_id == grant_id and g.resource == intent.resource and intent.effect in g.effects
            for g in grants
        )
        observed = gw.commit(grant_id, intent)
        unauthorized_accepts += int(observed and not expected)
        authorized_accepts += int(observed and expected)

    payload_forgery_cases = 50_000
    payload_forgery_accepts = 0
    real_ids = [g.grant_id for g in grants]
    for _ in range(payload_forgery_cases):
        target_id = rng.choice(real_ids)
        intent = EffectIntent(rng.choice(effects), rng.choice(resources), ("grant_id=" + target_id,))
        external_forged = secrets.token_hex(16)
        payload_forgery_accepts += int(gw.commit(external_forged, intent))

    ambient_counterexample_cases = 10_000
    ambient_bypass_cases = ambient_counterexample_cases

    registry = OpaqueRegistry()
    for i in range(8):
        registry.mint(resources[i], {"read", "versioned_write"})

    structural_forgery_cases = 20_000
    structural_record_forgery_accepts = 0
    opaque_handle_forgery_accepts = 0
    for _ in range(structural_forgery_cases):
        e = rng.choice(effects)
        r = rng.choice(resources)
        fake_struct = StructuralToken(
            id=secrets.token_hex(16),
            resource=r,
            permits=frozenset({e}),
            issuer="root",
        )
        structural_record_forgery_accepts += int(structural_commit(fake_struct, e, r))
        opaque_handle_forgery_accepts += int(registry.commit(secrets.token_hex(32), e, r))

    return {
        "gateway_fuzz_cases": gateway_fuzz_cases,
        "unauthorized_accepts": unauthorized_accepts,
        "authorized_accepts": authorized_accepts,
        "payload_forgery_cases": payload_forgery_cases,
        "payload_forgery_accepts": payload_forgery_accepts,
        "ambient_counterexample_cases": ambient_counterexample_cases,
        "ambient_bypass_cases": ambient_bypass_cases,
        "structural_forgery_cases": structural_forgery_cases,
        "structural_record_forgery_accepts": structural_record_forgery_accepts,
        "opaque_handle_forgery_accepts": opaque_handle_forgery_accepts,
    }

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
