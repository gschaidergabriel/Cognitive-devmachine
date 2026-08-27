import hashlib, json, itertools, copy

VERBS = {"read", "write", "exec"}

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))

def h(x):
    return hashlib.sha256(canon(x).encode()).hexdigest()

def authority_leq(src, tgt):
    if not tgt:
        return False
    if src["resource"] != tgt["resource"]:
        return False
    if not set(tgt["permits"]) <= set(src["permits"]):
        return False
    if not set(tgt["constraints"]) >= set(src["constraints"]):
        return False
    if not set(tgt["delegate_to"]) <= set(src["delegate_to"]):
        return False
    if src.get("revocation") != tgt.get("revocation"):
        return False
    return True

def validate(src, tgt):
    errors=[]
    if not authority_leq(src["authority"], tgt.get("authority")):
        errors.append("AUTHORITY")
    if src["epistemic"] != tgt.get("epistemic"):
        errors.append("EPISTEMIC")
    if src["provenance_hash"] != tgt.get("provenance_hash"):
        errors.append("PROVENANCE")
    expected = h({"authority":tgt.get("authority"),"epistemic":tgt.get("epistemic"),"provenance_hash":tgt.get("provenance_hash")})
    if expected != tgt.get("semantic_envelope_hash"):
        errors.append("ENVELOPE")
    return errors

src={
 "authority":{"resource":"file:/tmp/demo","permits":["read","write"],"constraints":["path=/tmp/demo","max_bytes=4096"],"delegate_to":["workerA"],"revocation":"rev-7"},
 "epistemic":{"status":"CONFLICT","basis":["ev1","ev2"]},
 "provenance_hash":h({"op":"ALL","sources":["ev1","ev2"]})
}
tgt=copy.deepcopy(src)
tgt["semantic_envelope_hash"] = h({"authority":tgt["authority"],"epistemic":tgt["epistemic"],"provenance_hash":tgt["provenance_hash"]})

mutants=[]
def m(name, fn):
    x=copy.deepcopy(tgt); fn(x); x["semantic_envelope_hash"] = h({"authority":x.get("authority"),"epistemic":x.get("epistemic"),"provenance_hash":x.get("provenance_hash")}); mutants.append((name,x))

m("drop_authority", lambda x: x.__setitem__("authority", None))
m("broaden_permits", lambda x: x["authority"].__setitem__("permits", ["read","write","exec"]))
m("relax_constraints", lambda x: x["authority"].__setitem__("constraints", ["path=/tmp/demo"]))
m("broaden_delegation", lambda x: x["authority"].__setitem__("delegate_to", ["workerA","workerB"]))
m("change_resource", lambda x: x["authority"].__setitem__("resource", "file:/etc/passwd"))
m("drop_revocation", lambda x: x["authority"].__setitem__("revocation", None))
m("epistemic_upgrade", lambda x: x["epistemic"].__setitem__("status", "KNOWN"))
m("drop_epistemic", lambda x: x.__setitem__("epistemic", None))
m("drop_provenance", lambda x: x.__setitem__("provenance_hash", None))
m("forge_provenance", lambda x: x.__setitem__("provenance_hash", "0"*64))
x=copy.deepcopy(tgt); x["semantic_envelope_hash"]="f"*64; mutants.append(("tamper_envelope",x))
m("attenuate_but_rebind_resource", lambda x: (x["authority"].__setitem__("permits", ["read"]), x["authority"].__setitem__("resource", "file:/tmp/other")))

baseline_errors=validate(src,tgt)
rejected=[name for name,x in mutants if validate(src,x)]

subsets=[]
for r in range(4):
    subsets += [set(c) for c in itertools.combinations(sorted(VERBS), r)]
mis=0
for s in subsets:
    for t in subsets:
        sa={"resource":"r","permits":sorted(s),"constraints":["c"],"delegate_to":[],"revocation":"r1"}
        ta={"resource":"r","permits":sorted(t),"constraints":["c"],"delegate_to":[],"revocation":"r1"}
        oracle=t <= s
        if authority_leq(sa,ta) != oracle:
            mis += 1

out={
 "baseline_errors":baseline_errors,
 "mutations_total":len(mutants),
 "mutations_rejected":len(rejected),
 "rejected_names":rejected,
 "permission_cases":len(subsets)*len(subsets),
 "authority_oracle_mismatches":mis
}
print(json.dumps(out, sort_keys=True))
