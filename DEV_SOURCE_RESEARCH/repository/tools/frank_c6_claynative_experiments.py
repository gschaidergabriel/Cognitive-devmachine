#!/usr/bin/env python3
"""Reproducible synthetic/reference experiments for FRANK C6 Clay-native research.

These are architecture-mechanism probes, not live FRANK measurements.
"""
import json, math, random, statistics

SEED = 60608
rng = random.Random(SEED)
results = {"schema_version":"1.0","seed":SEED,"evidence_boundary":"synthetic/reference/analytic only; not live FRANK or target-Qwen full-fine-tune evidence","experiments":{}}

# 1. Semantic boundary vs common-mode sensitivity.
rows=[]
for q in [0.0,0.001,0.005,0.01]:
    for p in [0.001,0.005,0.01]:
        for n in [2,4,8,12]:
            rows.append({"common_semantic_bug_q":q,"per_translation_bug_p":p,"semantic_boundaries_n":n,"any_semantic_failure":1-(1-q)*((1-p)**n)})
results["experiments"]["EXP-C6-BOUNDARY-001"]={"class":"analytic_sensitivity_not_frank_estimate","formula":"1-(1-q)*(1-p)^n","rows":rows,"example":{"q":0.001,"p":0.005,"n8":1-(1-.001)*(1-.005)**8,"n2":1-(1-.001)*(1-.005)**2},"interpretation":"Unifying semantic representation can remove conversion-risk terms, but once those shrink, common semantic/compiler errors dominate the remaining risk."}

# 2. ClayVector fault-injection reference checker.
fault_types=["axis_permutation","unit_scale","stale_basis","length","payload_bitflip","semantic_miscompute_valid_rehash"]
N=120000
counts={f:0 for f in fault_types}; untyped={f:0 for f in fault_types}; typed={f:0 for f in fault_types}; hashed={f:0 for f in fault_types}
for _ in range(N):
    f=rng.choice(fault_types); counts[f]+=1
    if f=="length": untyped[f]+=1
    if f in {"axis_permutation","unit_scale","stale_basis","length"}: typed[f]+=1
    if f in {"axis_permutation","unit_scale","stale_basis","length","payload_bitflip"}: hashed[f]+=1
results["experiments"]["EXP-C6-CLAYVECTOR-002"]={"class":"reference_checker_fault_injection","n":N,"faults":{f:{"n":counts[f],"untyped_detection":untyped[f]/counts[f],"typed_schema_detection":typed[f]/counts[f],"typed_plus_semantic_hash_detection":hashed[f]/counts[f]} for f in fault_types},"interpretation":"Clay-native numeric state should carry basis/axis/unit/version semantics; payload integrity adds another layer, but a semantically wrong computation that is validly rehashed still needs invariant/causal checks."}

# 3. Literal text vs typed binary physical lowering.
dims=[9,32,128,1024,4096]; enc=[]
for d in dims:
    vals=[math.sin(i*0.13) for i in range(d)]
    text=json.dumps({"type":"ClayVector","basis":"epq-v1","unit":"normalized","values":[round(x,6) for x in vals]},separators=(",",":"))
    typed_binary=64+4*d # deliberately illustrative fixed header
    enc.append({"dims":d,"text_json_bytes":len(text.encode()),"float32_payload_bytes":4*d,"illustrative_clay_binary_bytes":typed_binary,"text_over_binary_ratio":len(text.encode())/typed_binary})
results["experiments"]["EXP-C6-PHYSICAL-ENCODING-003"]={"class":"deterministic_size_accounting","assumed_binary_header_bytes":64,"rows":enc,"interpretation":"Clay-native semantics must not mean textualizing every tensor; semantic identity can lower to compact binary/vector payloads."}

# 4. Relation-instance assembly compactness.
rng2=random.Random(123); entities=[f"entity_{i:04d}" for i in range(500)]; rels=[]
for i in range(300):
    rels.append({"rel_id":f"rel_{i:04d}","type":"interaction","roles":{"sender":rng2.choice(entities),"recipient":rng2.choice(entities),"asset":rng2.choice(entities)},"confidence":round(rng2.random(),4),"epoch":17})
verbose=len(json.dumps(rels,separators=(",",":")).encode())
clay_lines=[f"r{i}:i s={r['roles']['sender'][7:]} t={r['roles']['recipient'][7:]} a={r['roles']['asset'][7:]} c={int(r['confidence']*10000)} e=17" for i,r in enumerate(rels)]
compact=len("\n".join(clay_lines).encode())
results["experiments"]["EXP-C6-ASSEMBLY-COMPACT-004"]={"class":"synthetic_wire_size_proxy_not_tokenizer_benchmark","relations":300,"verbose_json_bytes":verbose,"compact_clay_text_bytes":compact,"byte_reduction":1-compact/verbose,"interpretation":"Stable IDs and native typed relation roles can remove repeated schema/name material before model exposure; target-Qwen token savings must be measured separately."}

# 5. Selection/authority exhaustive reference policy.
statuses=["CURRENT","UNTRUSTED","UNKNOWN","REVOKED"]; selectors=["VALID","INVALID"]; effects=["READ_ONLY","REVERSIBLE","IRREVERSIBLE"]
cases=[]; unsafe=0
for s in statuses:
    for sel in selectors:
        for e in effects:
            trusted=(s=="CURRENT" and sel=="VALID")
            effect_authorized=True if e=="READ_ONLY" else trusted
            if e=="IRREVERSIBLE" and not trusted and effect_authorized: unsafe+=1
            cases.append({"status":s,"selector":sel,"effect":e,"effect_authorized":effect_authorized})
results["experiments"]["EXP-C6-SELECTION-AUTHORITY-005"]={"class":"reference_policy_exhaustive_truth_table","cases":len(cases),"unsafe_irreversible_accepts":unsafe,"interpretation":"Associative/untrusted Clay may remain available for reversible cognition without becoming effect authority."}

# 6. Projection/schema cache integrity.
N=100000; mutations=stale=detected=miscompile=0
for _ in range(N):
    kind=rng.choices(["none","schema_mutation","semantic_miscompile_valid_hash"],weights=[0.8,0.15,0.05])[0]
    if kind=="schema_mutation": mutations+=1; stale+=1; detected+=1
    elif kind=="semantic_miscompile_valid_hash": miscompile+=1
results["experiments"]["EXP-C6-SCHEMA-CACHE-006"]={"class":"synthetic_cache_integrity_counterexample","n":N,"schema_mutations":mutations,"stale_uses_without_versioning":stale,"schema_hash_detected":detected,"semantic_miscompile_valid_hash":miscompile,"interpretation":"Version/hash identity can eliminate stale compiled Clay in this construction; it cannot detect a trusted compiler that computes the wrong semantics."}

# 7. Needle is the sole non-Clay semantic route source; model/memory cannot change tool class.
routes=["NONE","SEARCH","MAIL","SHELL"]; caps={"NONE":True,"SEARCH":True,"MAIL":True,"SHELL":False}
cases7=denied=cross=0
for needle in routes:
    for model in routes:
        for poisoned in [False,True]:
            cases7+=1; chosen=needle; authorized=caps[chosen]
            if not authorized: denied+=1
            if model!=needle and chosen==model and authorized: cross+=1
results["experiments"]["EXP-C6-NEEDLE-ISOLATION-007"]={"class":"exhaustive_reference_routing_property","cases":cases7,"cross_route_overrides_by_model_or_memory":cross,"capability_denials":denied,"interpretation":"A strict Needle->typed Clay route bridge prevents model/memory from changing the tool class in the reference policy. This does not measure Needle accuracy; wrong Needle output remains a Needle error."}

# 8. Clay self-description may propose architecture edits, but owner/core constraints remain immutable without external authority.
protected={"clay_native_target","needle_is_sole_foreign_semantic_subsystem","model_output_not_authority","canonical_truth_not_activation"}
fields=list(protected)+["assembly_budget","decay","projection_order","reader_profile","compaction_policy"]
N=100000; protected_attempts=accepted_protected=accepted_unprotected=0
for _ in range(N):
    f=rng.choice(fields)
    if f in protected:
        protected_attempts+=1; accepted=False
    else:
        accepted=True; accepted_unprotected+=1
    if f in protected and accepted: accepted_protected+=1
results["experiments"]["EXP-C6-SELF-MODIFY-008"]={"class":"reference_validator_property_fuzz","n":N,"protected_write_attempts":protected_attempts,"accepted_protected_writes":accepted_protected,"accepted_unprotected_writes":accepted_unprotected,"interpretation":"Self-representing Clay can remain editable without allowing model-authored Clay to rewrite owner/authority invariants in the reference validator."}

print(json.dumps(results,indent=2,sort_keys=True))
