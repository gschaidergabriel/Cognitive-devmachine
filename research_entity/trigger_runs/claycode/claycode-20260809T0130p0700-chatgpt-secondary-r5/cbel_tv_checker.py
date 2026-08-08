import json, hashlib, hmac, sys

SECRET = b"local-experiment-host-secret-v1"

def enc(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()

def h(o):
    return hashlib.sha256(enc(o)).hexdigest()

def permit_payload(p):
    return {k:p[k] for k in (
        "intent_hash","basis_hash","selection_hash","revocation_epoch",
        "expires_epoch","capability_scope","nonce"
    )}

def sig_ok(p):
    exp = hmac.new(SECRET, enc(permit_payload(p)), hashlib.sha256).hexdigest()
    return hmac.compare_digest(exp, p["signature"])

def reference(case):
    i,p,c = case["intent"],case["permit"],case["current"]
    if not sig_ok(p): return "DENY_BAD_SIGNATURE"
    if h(i) != p["intent_hash"]: return "DENY_INTENT_DRIFT"
    if c["current_basis_hash"] != p["basis_hash"]: return "DENY_BASIS_DRIFT"
    if c["current_selection_hash"] != p["selection_hash"]: return "DENY_SELECTION_DRIFT"
    if c["current_revocation_epoch"] != p["revocation_epoch"]: return "DENY_REVOCATION_DRIFT"
    if c["current_epoch"] > p["expires_epoch"]: return "DENY_EXPIRED"
    if c["current_closure_state"] != "KNOWN_VALID": return "DENY_CLOSURE"
    if i["operation"] not in p["capability_scope"]: return "DENY_SCOPE"
    return "ALLOW"

def lowered(case):
    i,p,c = case["intent"],case["permit"],case["current"]
    checks = {
        "signature": sig_ok(p),
        "scope": i["operation"] in p["capability_scope"],
        "fresh_revocation": p["revocation_epoch"] == c["current_revocation_epoch"],
        "fresh_time": c["current_epoch"] <= p["expires_epoch"],
        "basis": p["basis_hash"] == c["current_basis_hash"],
        "selection": p["selection_hash"] == c["current_selection_hash"],
        "closure": c["current_closure_state"] == "KNOWN_VALID",
        "intent": p["intent_hash"] == h(i),
    }
    return "ALLOW" if all(checks.values()) else "DENY"

def mutant(case, drop):
    i,p,c = case["intent"],case["permit"],case["current"]
    checks = {
        "signature": sig_ok(p),
        "scope": i["operation"] in p["capability_scope"],
        "revocation": p["revocation_epoch"] == c["current_revocation_epoch"],
        "expiry": c["current_epoch"] <= p["expires_epoch"],
        "basis": p["basis_hash"] == c["current_basis_hash"],
        "selection": p["selection_hash"] == c["current_selection_hash"],
        "closure": c["current_closure_state"] == "KNOWN_VALID",
        "intent": p["intent_hash"] == h(i),
    }
    if drop in checks:
        checks[drop] = True
    return "ALLOW" if all(checks.values()) else "DENY"

for line in sys.stdin:
    case=json.loads(line)
    out={"reference":reference(case),"lowered":lowered(case)}
    for m in ["signature","scope","revocation","expiry","basis","selection","closure","intent"]:
        out["mutant_"+m]=mutant(case,m)
    print(json.dumps(out,separators=(",",":")))
