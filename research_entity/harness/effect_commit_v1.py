#!/usr/bin/env python3
"""H-WP-10 reference effect-commit oracle.

Host-language executable foundation for FRANK Harness during BASE. It models the
runtime authority boundary; it does not execute effects and does not grant authority
from model, Needle, GWT, ClayGraph, recurrence, or ordinary semantic state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass, replace
from typing import Any

SCHEMA_VERSION = "1.0"
EXTERNAL_AUTHORITY_ORIGINS = {"RUNTIME_CAPABILITY_GRANT", "OWNER_BROKER_GRANT"}
IRREVERSIBLE = "EXTERNALLY_AUTHORIZED_IRREVERSIBLE"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapabilityWitness:
    capability_id: str
    generation: int
    epoch: int
    authority_origin: str


@dataclass(frozen=True)
class ResourceWitness:
    slot: int
    generation: int
    resource_id: str


@dataclass(frozen=True)
class DecisionEnvelope:
    decision_id: str
    decision_dependencies: dict[str, int]
    capability: CapabilityWitness
    resource: ResourceWitness
    budget_key: str
    budget_cost: int
    information_flow_ok: bool
    effect_class: str
    external_approval_id: str | None
    idempotency_key: str
    effect_hash: str
    observed_global_epoch: int


class RuntimeState:
    def __init__(self) -> None:
        self.global_epoch = 1
        self.dependencies = {"task": 1, "policy": 1, "target": 1, "unrelated": 1}
        self.capabilities = {
            "cap:file.write": {"generation": 1, "epoch": 1, "valid": True, "authority_origin": "RUNTIME_CAPABILITY_GRANT"}
        }
        self.resources = {0: {"generation": 1, "resource_id": "file:A"}}
        self.budgets = {"writes": 10}
        self.external_approvals: set[str] = set()
        self.committed: dict[str, str] = {}

    def bump(self) -> None:
        self.global_epoch += 1

    def churn_unrelated(self) -> None:
        self.dependencies["unrelated"] += 1; self.bump()

    def change_critical(self, name: str = "target") -> None:
        self.dependencies[name] += 1; self.bump()

    def revoke_regrant_capability(self) -> None:
        c = self.capabilities["cap:file.write"]
        c["valid"] = False; c["epoch"] += 1; self.bump()
        c["generation"] += 1; c["epoch"] += 1; c["valid"] = True; self.bump()

    def recycle_resource(self) -> None:
        old = self.resources[0]
        self.resources[0] = {"generation": old["generation"] + 1, "resource_id": "file:B"}; self.bump()

    def shrink_budget(self, value: int = 0) -> None:
        self.budgets["writes"] = value; self.bump()


def make_envelope(state: RuntimeState, *, effect_class: str = "REVERSIBLE", approval: str | None = None) -> DecisionEnvelope:
    c = state.capabilities["cap:file.write"]; r = state.resources[0]
    semantic = {
        "decision_dependencies": {k: state.dependencies[k] for k in ("task", "policy", "target")},
        "capability_id": "cap:file.write", "resource_id": r["resource_id"],
        "effect_class": effect_class, "payload": "versioned-write:test",
    }
    return DecisionEnvelope(
        decision_id="decision:" + sha256_obj(semantic)[:20],
        decision_dependencies=semantic["decision_dependencies"],
        capability=CapabilityWitness("cap:file.write", c["generation"], c["epoch"], c["authority_origin"]),
        resource=ResourceWitness(0, r["generation"], r["resource_id"]),
        budget_key="writes", budget_cost=1, information_flow_ok=True,
        effect_class=effect_class, external_approval_id=approval,
        idempotency_key="idem:" + sha256_obj(semantic)[:24],
        effect_hash=sha256_obj({"effect": semantic}), observed_global_epoch=state.global_epoch,
    )


def validate_scoped(state: RuntimeState, env: DecisionEnvelope, *, commit: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    if env.capability.authority_origin not in EXTERNAL_AUTHORITY_ORIGINS:
        failures.append("AUTHORITY_ORIGIN_NOT_EXTERNAL")
    for dep, expected in sorted(env.decision_dependencies.items()):
        if state.dependencies.get(dep) != expected: failures.append(f"STALE_DEPENDENCY:{dep}")
    cap = state.capabilities.get(env.capability.capability_id)
    if cap is None:
        failures.append("CAPABILITY_MISSING")
    else:
        if not cap.get("valid"): failures.append("CAPABILITY_REVOKED")
        if cap.get("generation") != env.capability.generation: failures.append("CAPABILITY_GENERATION_MISMATCH")
        if cap.get("epoch") != env.capability.epoch: failures.append("CAPABILITY_EPOCH_MISMATCH")
        if cap.get("authority_origin") != env.capability.authority_origin: failures.append("CAPABILITY_ORIGIN_MISMATCH")
    resource = state.resources.get(env.resource.slot)
    if resource is None:
        failures.append("RESOURCE_MISSING")
    else:
        if resource.get("generation") != env.resource.generation: failures.append("RESOURCE_GENERATION_MISMATCH")
        if resource.get("resource_id") != env.resource.resource_id: failures.append("RESOURCE_IDENTITY_MISMATCH")
    available = state.budgets.get(env.budget_key)
    if not isinstance(available, int) or available < env.budget_cost: failures.append("BUDGET_INSUFFICIENT")
    if not env.information_flow_ok: failures.append("INFORMATION_FLOW_NOT_ALLOWED")
    if env.effect_class == IRREVERSIBLE and (not env.external_approval_id or env.external_approval_id not in state.external_approvals):
        failures.append("IRREVERSIBLE_EXTERNAL_APPROVAL_REQUIRED")
    previous = state.committed.get(env.idempotency_key)
    if previous is not None:
        if previous == env.effect_hash:
            return {"status":"IDEMPOTENT_REPLAY","commit_allowed":True,"failures":[],"authority_minted":False,"state_changed":False}
        failures.append("IDEMPOTENCY_KEY_COLLISION")
    allowed = not failures
    if allowed and commit:
        state.budgets[env.budget_key] -= env.budget_cost
        state.committed[env.idempotency_key] = env.effect_hash
        state.bump()
    return {"status":"ALLOW" if allowed else "REJECT","commit_allowed":allowed,"failures":failures,"authority_minted":False,"state_changed":bool(allowed and commit)}


def validate_retained_permit(state: RuntimeState, env: DecisionEnvelope) -> bool:
    return env.capability.authority_origin in EXTERNAL_AUTHORITY_ORIGINS and env.information_flow_ok


def validate_global_epoch(state: RuntimeState, env: DecisionEnvelope) -> bool:
    return state.global_epoch == env.observed_global_epoch and validate_retained_permit(state, env)


def safety_oracle(state: RuntimeState, env: DecisionEnvelope) -> bool:
    if env.capability.authority_origin not in EXTERNAL_AUTHORITY_ORIGINS: return False
    if any(state.dependencies.get(k) != v for k, v in env.decision_dependencies.items()): return False
    cap = state.capabilities.get(env.capability.capability_id)
    if not cap or not cap["valid"] or cap["generation"] != env.capability.generation or cap["epoch"] != env.capability.epoch: return False
    res = state.resources.get(env.resource.slot)
    if not res or res["generation"] != env.resource.generation or res["resource_id"] != env.resource.resource_id: return False
    if state.budgets.get(env.budget_key, -1) < env.budget_cost: return False
    if not env.information_flow_ok: return False
    if env.effect_class == IRREVERSIBLE and (not env.external_approval_id or env.external_approval_id not in state.external_approvals): return False
    return True


def exhaustive_discriminator() -> dict[str, Any]:
    events = ["unrelated", "critical", "capability", "resource", "budget"]
    counts = {f"{name}_{kind}":0 for name in ("retained","global","scoped") for kind in ("unsafe","false_abort")}
    for mask in range(1 << len(events)):
        s = RuntimeState(); env = make_envelope(s)
        for i, event in enumerate(events):
            if not (mask & (1 << i)): continue
            if event == "unrelated": s.churn_unrelated()
            elif event == "critical": s.change_critical()
            elif event == "capability": s.revoke_regrant_capability()
            elif event == "resource": s.recycle_resource()
            elif event == "budget": s.shrink_budget()
        truth = safety_oracle(s, env)
        decisions = {"retained":validate_retained_permit(s, env),"global":validate_global_epoch(s, env),"scoped":validate_scoped(s, env)["commit_allowed"]}
        for name, decision in decisions.items():
            if decision and not truth: counts[f"{name}_unsafe"] += 1
            if not decision and truth: counts[f"{name}_false_abort"] += 1
    return {"cases":1 << len(events),"counts":counts}


def fuzz_discriminator(n: int = 50000, seed: int = 20260809) -> dict[str, Any]:
    rng = random.Random(seed)
    counts = {f"{name}_{kind}":0 for name in ("retained","global","scoped") for kind in ("unsafe","false_abort")}
    for _ in range(n):
        s = RuntimeState(); env = make_envelope(s)
        if rng.random() < .55:
            for _ in range(rng.randrange(1, 5)): s.churn_unrelated()
        if rng.random() < .20: s.change_critical(rng.choice(["task", "policy", "target"]))
        if rng.random() < .15: s.revoke_regrant_capability()
        if rng.random() < .15: s.recycle_resource()
        if rng.random() < .10: s.shrink_budget(rng.randrange(0, 2))
        truth = safety_oracle(s, env)
        decisions = {"retained":validate_retained_permit(s, env),"global":validate_global_epoch(s, env),"scoped":validate_scoped(s, env)["commit_allowed"]}
        for name, decision in decisions.items():
            if decision and not truth: counts[f"{name}_unsafe"] += 1
            if not decision and truth: counts[f"{name}_false_abort"] += 1
    return {"cases":n,"seed":seed,"counts":counts}


def self_test() -> dict[str, Any]:
    tests: list[tuple[str, bool]] = []
    s=RuntimeState(); env=make_envelope(s); tests.append(("baseline_allows",validate_scoped(s,env)["commit_allowed"] is True))
    s=RuntimeState(); env=make_envelope(s); s.churn_unrelated(); tests.append(("unrelated_churn_does_not_abort",validate_scoped(s,env)["commit_allowed"] is True)); tests.append(("global_epoch_false_aborts_unrelated_churn",validate_global_epoch(s,env) is False))
    s=RuntimeState(); env=make_envelope(s); s.change_critical(); tests.append(("critical_dependency_change_rejected",validate_scoped(s,env)["commit_allowed"] is False))
    s=RuntimeState(); env=make_envelope(s); s.revoke_regrant_capability(); tests.append(("capability_regrant_same_name_not_same_grant",validate_scoped(s,env)["commit_allowed"] is False))
    s=RuntimeState(); env=make_envelope(s); s.recycle_resource(); tests.append(("resource_aba_rejected",validate_scoped(s,env)["commit_allowed"] is False))
    s=RuntimeState(); env=make_envelope(s); s.shrink_budget(); tests.append(("budget_shrink_rejected",validate_scoped(s,env)["commit_allowed"] is False))
    s=RuntimeState(); env=make_envelope(s); bad=replace(env,capability=replace(env.capability,authority_origin="MODEL_OUTPUT")); tests.append(("model_cannot_mint_authority",validate_scoped(s,bad)["commit_allowed"] is False)); bad2=replace(env,capability=replace(env.capability,authority_origin="NEEDLE_ROUTE")); tests.append(("needle_cannot_mint_authority",validate_scoped(s,bad2)["commit_allowed"] is False))
    s=RuntimeState(); irr=make_envelope(s,effect_class=IRREVERSIBLE,approval="approval:1"); tests.append(("irreversible_without_external_approval_rejected",validate_scoped(s,irr)["commit_allowed"] is False)); s.external_approvals.add("approval:1"); tests.append(("irreversible_with_external_approval_allowed",validate_scoped(s,irr)["commit_allowed"] is True))
    s=RuntimeState(); env=make_envelope(s); first=validate_scoped(s,env,commit=True); second=validate_scoped(s,env,commit=True); tests.append(("first_commit_changes_state",first["state_changed"] is True)); tests.append(("idempotent_replay_no_second_effect",second["status"]=="IDEMPOTENT_REPLAY" and second["state_changed"] is False))
    s=RuntimeState(); env=make_envelope(s); env2=replace(env,effect_hash="0"*64); validate_scoped(s,env,commit=True); tests.append(("idempotency_collision_rejected",validate_scoped(s,env2)["commit_allowed"] is False))
    ex=exhaustive_discriminator(); tests.append(("exhaustive_scoped_zero_unsafe",ex["counts"]["scoped_unsafe"]==0)); tests.append(("exhaustive_scoped_zero_false_abort",ex["counts"]["scoped_false_abort"]==0)); tests.append(("retained_permit_exposes_staleness",ex["counts"]["retained_unsafe"]>0)); tests.append(("global_epoch_exposes_false_abort",ex["counts"]["global_false_abort"]>0))
    failed=[name for name,ok in tests if not ok]
    return {"status":"PASS" if not failed else "FAIL","tests_total":len(tests),"tests_passed":len(tests)-len(failed),"failed":failed,"exhaustive":ex["counts"]}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--fuzz",type=int,default=0); p.add_argument("--seed",type=int,default=20260809); args=p.parse_args()
    if args.self_test: print(json.dumps(self_test(),indent=2,sort_keys=True))
    if args.fuzz: print(json.dumps(fuzz_discriminator(args.fuzz,args.seed),indent=2,sort_keys=True))
    if not args.self_test and not args.fuzz: p.error("choose --self-test and/or --fuzz N")


if __name__ == "__main__": main()
