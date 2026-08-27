#!/usr/bin/env python3
"""GAR-001 deterministic reference discriminator.
Synthetic research model only; not Frank target-runtime evidence.
"""
from enum import Enum

class V(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; RECONCILE="RECONCILE"

SCENARIOS=[
"normal_current","stale_epoch_turnover","same_epoch_execution_rebind",
"snapshot_rollback_resurrection","copied_persistent_tuple",
"serialized_capability_resurrection","provider_precheck_turnover",
"unknown_outcome_reconciliation_after_turnover"]

EXPECTED={
"normal_current":V.ALLOW,
"stale_epoch_turnover":V.DENY,
"same_epoch_execution_rebind":V.DENY,
"snapshot_rollback_resurrection":V.DENY,
"copied_persistent_tuple":V.DENY,
"serialized_capability_resurrection":V.DENY,
"provider_precheck_turnover":V.DENY,
"unknown_outcome_reconciliation_after_turnover":V.RECONCILE}

FEATURES={
"V14_UNBOUND":dict(epoch=False,exec=False,inc=False,opaque=False,scope=False),
"EXACT_DURABLE_TUPLE":dict(epoch=True,exec=True,inc=False,opaque=False,scope=False),
"TUPLE_PLUS_NONROLLBACK_INCARNATION":dict(epoch=True,exec=True,inc=True,opaque=False,scope=False),
"OPAQUE_LIVE_CAP_PRECHECK":dict(epoch=True,exec=True,inc=True,opaque=True,scope=False),
"CONVENTIONAL_SCOPED_CAPABILITY":dict(epoch=True,exec=True,inc=True,opaque=True,scope=True),
"GAR_GENERATIVE_AUTHORITY_REGION":dict(epoch=True,exec=True,inc=True,opaque=True,scope=True),
}

def outcome(f,s):
    if s=="normal_current": return V.ALLOW
    if s=="stale_epoch_turnover": return V.DENY if f["epoch"] else V.ALLOW
    if s=="same_epoch_execution_rebind": return V.DENY if f["exec"] else V.ALLOW
    if s=="snapshot_rollback_resurrection": return V.DENY if (f["inc"] or f["opaque"]) else V.ALLOW
    if s in ("copied_persistent_tuple","serialized_capability_resurrection"):
        return V.DENY if f["opaque"] else V.ALLOW
    if s=="provider_precheck_turnover": return V.DENY if f["scope"] else V.ALLOW
    if s=="unknown_outcome_reconciliation_after_turnover": return V.RECONCILE
    raise KeyError(s)

def runtime_matrix():
    out={}
    for a,f in FEATURES.items():
        results={s:outcome(f,s) for s in SCENARIOS}
        out[a]=sum(results[s]!=EXPECTED[s] for s in SCENARIOS)
    return out

PROGRAMS={
"VALID_CURRENT_EFFECT":[("acquire","k1"),("reserve","e1","k1"),("provider_scope","e1","k1"),("release","k1")],
"STALE_BRAND_AFTER_TURNOVER":[("acquire","k1"),("reserve","e1","k1"),("release","k1"),("acquire","k2"),("provider_scope","e1","k2")],
"SAME_EPOCH_REBIND_DIFFERENT_EXECUTION":[("acquire","k1"),("reserve","e1","k1"),("rebind_same_epoch","k2"),("provider_scope","e1","k2")],
"SERIALIZE_AUTHORITY":[("acquire","k1"),("serialize_cap","k1")],
"ESCAPE_AUTHORITY":[("acquire","k1"),("return_cap","k1")],
"DUPLICATE_AUTHORITY":[("acquire","k1"),("copy_cap","k1")],
"LEAK_BOOLEAN_PRECHECK":[("acquire","k1"),("reserve","e1","k1"),("precheck_to_permit","p1","e1","k1"),("release","k1"),("provider_with_permit","p1")],
"RECONCILE_OLD_EVIDENCE":[("acquire","k1"),("reserve","e1","k1"),("release","k1"),("reconcile_evidence","e1")],
}

def typecheck(prog):
    live=set(); reservations={}; errors=[]
    for op in prog:
        tag=op[0]
        if tag=="acquire": live.add(op[1])
        elif tag=="rebind_same_epoch": live.add(op[1])
        elif tag=="reserve":
            e,k=op[1],op[2]
            if k not in live: errors.append("reserve_without_live_brand")
            reservations[e]=k
        elif tag=="provider_scope":
            e,k=op[1],op[2]
            if k not in live: errors.append("provider_without_live_brand")
            if reservations.get(e)!=k: errors.append("brand_mismatch")
        elif tag=="release": live.discard(op[1])
        elif tag in ("serialize_cap","return_cap","copy_cap"): errors.append(tag+"_forbidden")
        elif tag=="precheck_to_permit": errors.append("detached_commit_permit_forbidden")
        elif tag=="provider_with_permit": errors.append("provider_requires_region_scope")
        elif tag=="reconcile_evidence": pass
    return errors

if __name__=="__main__":
    print("RUNTIME", runtime_matrix())
    for n,p in PROGRAMS.items():
        print(n, "ACCEPT" if not typecheck(p) else "REJECT", typecheck(p))
