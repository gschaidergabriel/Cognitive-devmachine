#!/usr/bin/env python3
"""
ClayCode Lane D: Intent Adequacy / Context-to-Execution Noninterference lab.

Constructed mechanism test. Frequencies are deliberately chosen for coverage and
MUST NOT be interpreted as production risk estimates.

The test compares:
  1) broad capability-only admission,
  2) coarse task-only admission,
  3) static exact-target intent (secure but rejects dynamic release tasks),
  4) UIC+TypedRelease admission.

It also tests consent-to-manifest binding for high-impact effects.
"""
from __future__ import annotations
import hashlib, json, random
from collections import Counter

SEED = 2026080902
N = 120_000
R = random.Random(SEED)

OPS = ("email_send","file_write","deploy","db_update","api_post","package_install","transfer")
ATTACKS = (
    "TARGET_DRIFT","TARGET_PROV_LAUNDER","PAYLOAD_SOURCE_SWAP","AMOUNT_OVERSHOOT",
    "STALE_EPOCH","TASK_REBIND","INVOCATION_INJECTION","RELEASE_SELECTOR_SWAP","APPROVAL_SWAP"
)

def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",",":")).encode()).hexdigest()

def target_for(op, alternate=False):
    if op == "email_send":
        return f"{'attacker' if alternate else 'user'}{R.randint(1,999)}@example.com"
    if op == "file_write":
        return f"/project/{'tmp' if alternate else 'docs'}/file{R.randint(1,999)}.md"
    if op == "deploy":
        return R.choice(("cluster:staging/appA","cluster:staging/appB","cluster:prod/appA","cluster:prod/appB"))
    if op == "db_update":
        return f"db:main/table{R.randint(1,20)}/row{R.randint(501 if alternate else 1,999 if alternate else 500)}"
    if op == "api_post":
        return f"api:example/v{R.randint(1,3)}/resource{R.randint(51 if alternate else 1,99 if alternate else 50)}"
    if op == "package_install":
        return f"pkg:project/{'evilpkg' if alternate else R.choice(('numpy','pandas','requests','pydantic','rich','pytest'))}"
    return f"bank:acct/{R.randint(100000,999999)}"

def scope_for(op):
    return {
        "email_send":"email:*@example.com",
        "file_write":"/project/*",
        "deploy":"cluster:*",
        "db_update":"db:main/*",
        "api_post":"api:example/*",
        "package_install":"pkg:project/*",
        "transfer":"bank:acct/*",
    }[op]

def cap_target_ok(scope, target):
    if scope == "email:*@example.com":
        return target.endswith("@example.com")
    if scope == "cluster:*":
        return target.startswith("cluster:")
    if scope.endswith("/*"):
        return target.startswith(scope[:-1])
    return False

def make_episode(i):
    op = R.choice(OPS)
    task_id = f"task-{i}"
    epoch = R.randint(1, 1_000_000)
    dynamic = R.random() < 0.28 and op in {"email_send","file_write","db_update","api_post"}
    high = op in {"deploy","db_update","package_install","transfer"} or R.random() < 0.15
    target = target_for(op)
    amount = R.randint(1,500) if op == "transfer" else R.randint(1,50)
    max_amount = amount + R.randint(0,max(1,amount//2))
    source = f"source:{R.randint(1,1_000_000)}"

    if dynamic:
        slot = {"email_send":"recipient","file_write":"path","db_update":"row","api_post":"endpoint"}[op]
        field = {"email_send":"sender","file_write":"safe_name","db_update":"row_id","api_post":"canonical_endpoint"}[op]
        selector = f"selector:{R.randint(1,10000)}"
        target_rule = {"kind":"release","slot":slot,"selector":selector,"source":source,"field":field}
        release = dict(target_rule)
        release["value"] = target
        release["valid"] = True
        target_prov = f"RELEASE:{slot}"
    else:
        target_rule = {"kind":"fixed","value":target}
        release = None
        target_prov = "USER"

    payload_source = source if op not in {"package_install","transfer"} else "USER"
    payload_prov = f"UNTRUSTED:{payload_source}" if payload_source != "USER" else "USER"

    uic = {
        "task_id": task_id,
        "epoch": epoch,
        "op": op,
        "target_rule": target_rule,
        "max_amount": max_amount,
        "allowed_payload_sources": [payload_source],
        "invocation_origins": ["USER_PLAN","HOST_PLAN"],
        "high": high,
    }
    proposal = {
        "task_id": task_id, "epoch": epoch, "op": op, "target": target, "amount": amount,
        "target_prov": target_prov, "payload_prov": payload_prov,
        "invocation_origin": "USER_PLAN", "release": release,
    }
    core = {k:proposal[k] for k in ("task_id","epoch","op","target","amount")}
    proposal["approval_hash"] = sha(core) if high else None
    cap = {"op":op, "scope":scope_for(op), "max_amount":max(1000,max_amount*10)}
    return uic, cap, proposal, dynamic

def capability_gate(u, c, p):
    return p["op"] == c["op"] and cap_target_ok(c["scope"],p["target"]) and p["amount"] <= c["max_amount"]

def task_gate(u, c, p):
    return capability_gate(u,c,p) and p["task_id"] == u["task_id"] and p["op"] == u["op"]

def static_exact_gate(u,c,p):
    if not task_gate(u,c,p) or u["target_rule"]["kind"] != "fixed":
        return False
    return p["target"] == u["target_rule"]["value"] and p["amount"] <= u["max_amount"] and p["epoch"] == u["epoch"]

def uic_release_gate(u,c,p, omit=()):
    omit = set(omit)
    if "capability" not in omit and not capability_gate(u,c,p): return False
    if "task" not in omit and p["task_id"] != u["task_id"]: return False
    if "op" not in omit and p["op"] != u["op"]: return False
    if "epoch" not in omit and p["epoch"] != u["epoch"]: return False
    if "amount" not in omit and p["amount"] > u["max_amount"]: return False
    if "invocation" not in omit and p["invocation_origin"] not in u["invocation_origins"]: return False

    rule = u["target_rule"]
    if rule["kind"] == "fixed":
        if "target" not in omit and p["target"] != rule["value"]: return False
        if "target_prov" not in omit and p["target_prov"] not in {"USER","HOST"}: return False
    else:
        if "release" not in omit:
            rel = p.get("release")
            if not rel or not rel.get("valid"): return False
            for k in ("slot","selector","source","field"):
                if rel.get(k) != rule[k]: return False
            if rel.get("value") != p["target"]: return False
        if "target_prov" not in omit and p["target_prov"] != f"RELEASE:{rule['slot']}": return False

    if "payload_flow" not in omit:
        prov = p["payload_prov"]
        if prov in {"USER","HOST"}:
            pass
        elif prov.startswith("UNTRUSTED:"):
            if prov.split(":",1)[1] not in set(u["allowed_payload_sources"]): return False
        else:
            return False

    if u["high"] and "approval" not in omit:
        core = {k:p[k] for k in ("task_id","epoch","op","target","amount")}
        if p.get("approval_hash") != sha(core): return False
    return True

def mutate(u,c,p,attack):
    p = json.loads(json.dumps(p))
    if attack == "TARGET_DRIFT":
        old = p["target"]
        for _ in range(100):
            new = target_for(u["op"], alternate=True)
            if new != old and cap_target_ok(c["scope"],new):
                p["target"] = new
                break
    elif attack == "TARGET_PROV_LAUNDER":
        p["target_prov"] = "UNTRUSTED:evil-context"
    elif attack == "PAYLOAD_SOURCE_SWAP":
        p["payload_prov"] = "UNTRUSTED:evil-context"
    elif attack == "AMOUNT_OVERSHOOT":
        p["amount"] = min(c["max_amount"], u["max_amount"] + R.randint(1,50))
    elif attack == "STALE_EPOCH":
        p["epoch"] = u["epoch"] + 1
    elif attack == "TASK_REBIND":
        p["task_id"] = f"other-task-{R.randint(1,1_000_000)}"
    elif attack == "INVOCATION_INJECTION":
        p["invocation_origin"] = "UNTRUSTED_TOOL_STREAM"
    elif attack == "RELEASE_SELECTOR_SWAP":
        if u["target_rule"]["kind"] == "release":
            p["release"]["selector"] += ":other"
        else:
            p["target_prov"] = "RELEASE:forged"
    elif attack == "APPROVAL_SWAP":
        p["approval_hash"] = sha({"other_manifest":R.randint(1,1_000_000)})
    return p

def classify():
    rows=[]
    for i in range(N):
        u,c,p,dyn = make_episode(i)
        if R.random() < 0.25:
            rows.append((u,c,p,dyn,True,"BENIGN"))
            continue
        attack = R.choice(ATTACKS)
        if attack == "RELEASE_SELECTOR_SWAP" and u["target_rule"]["kind"] != "release":
            attack = "TARGET_PROV_LAUNDER"
        if attack == "APPROVAL_SWAP" and not u["high"]:
            attack = "INVOCATION_INJECTION"
        q = mutate(u,c,p,attack)
        rows.append((u,c,q,dyn,False,attack))

    gates = {
        "capability_only": capability_gate,
        "task_only": task_gate,
        "static_exact": static_exact_gate,
        "uic_typed_release": uic_release_gate,
    }
    out={}
    for name,gate in gates.items():
        tp=tn=fp=fn=0
        attacks=Counter()
        dyn_denied=dyn_total=0
        for u,c,p,dyn,expected,attack in rows:
            pred=gate(u,c,p)
            if expected and pred: tp += 1
            elif expected and not pred: fn += 1
            elif not expected and pred: fp += 1; attacks[attack] += 1
            else: tn += 1
            if expected and dyn:
                dyn_total += 1
                if not pred: dyn_denied += 1
        out[name] = {
            "benign_allowed":tp, "benign_denied":fn, "attack_allowed":fp, "attack_denied":tn,
            "attack_accept_by_class":dict(attacks),
            "dynamic_benign_denied":dyn_denied, "dynamic_benign_total":dyn_total,
        }
    return out

def consent_test(n=40_000):
    # Structural correspondence test, not a human-comprehension model.
    naive_attack_accept=bound_attack_accept=0
    clean_naive=clean_bound=0
    for i in range(n):
        manifest = {
            "task_id":f"consent-{i}",
            "epoch":R.randint(1,100000),
            "op":R.choice(("deploy","db_update","package_install","transfer")),
            "target":f"resource:{R.randint(1,100000)}",
            "amount":R.randint(1,500),
            "nonce":R.randint(1,2**31-1),
        }
        displayed = dict(manifest)
        approval_token = sha(displayed)
        attack = R.random() < 0.65
        executing = dict(manifest)
        if attack:
            field=R.choice(("target","amount","epoch","op"))
            if field=="target": executing[field]=f"resource:{R.randint(100001,200000)}"
            elif field=="amount": executing[field]+=R.randint(1,500)
            elif field=="epoch": executing[field]+=1
            else: executing[field]="transfer" if executing[field]!="transfer" else "deploy"

        naive=True
        bound=(approval_token == sha(executing))
        if attack:
            naive_attack_accept += int(naive)
            bound_attack_accept += int(bound)
        else:
            clean_naive += int(naive)
            clean_bound += int(bound)
    return {
        "cases":n,
        "naive_boolean_confirmation_attack_accepts":naive_attack_accept,
        "manifest_bound_confirmation_attack_accepts":bound_attack_accept,
        "naive_clean_accepts":clean_naive,
        "manifest_bound_clean_accepts":clean_bound,
        "boundary":"This proves only structural display/manifest binding in the constructed model; it does not model human comprehension or coercion."
    }

def targeted_ablation(m=3000):
    result={}
    specs=[
        ("target","TARGET_DRIFT",lambda u,d: u["target_rule"]["kind"]=="fixed" and not u["high"]),
        ("release","RELEASE_SELECTOR_SWAP",lambda u,d: u["target_rule"]["kind"]=="release" and not u["high"]),
        ("target_prov","TARGET_PROV_LAUNDER",lambda u,d: not u["high"]),
        ("payload_flow","PAYLOAD_SOURCE_SWAP",lambda u,d: not u["high"]),
        ("amount","AMOUNT_OVERSHOOT",lambda u,d: not u["high"]),
        ("epoch","STALE_EPOCH",lambda u,d: not u["high"]),
        ("task","TASK_REBIND",lambda u,d: not u["high"]),
        ("invocation","INVOCATION_INJECTION",lambda u,d: not u["high"]),
        ("approval","APPROVAL_SWAP",lambda u,d: u["high"]),
    ]
    for dim,attack,cond in specs:
        cases=[]
        while len(cases)<m:
            u,c,p,d=make_episode(50_000_000+len(cases)+R.randint(1,10_000_000))
            if not cond(u,d): continue
            q=mutate(u,c,p,attack)
            if u["high"] and dim!="approval":
                core={k:q[k] for k in ("task_id","epoch","op","target","amount")}
                q["approval_hash"]=sha(core)
            cases.append((u,c,q))
        full=sum(uic_release_gate(u,c,p) for u,c,p in cases)
        omitted=sum(uic_release_gate(u,c,p,omit=(dim,)) for u,c,p in cases)
        result[dim]={"cases":m,"full_gate_accepts":full,"omit_named_check_accepts":omitted}
    return result

def main():
    result = {
        "schema_version":"1.0",
        "experiment_id":"EXP-CC-LANE-D-UIC-NONINTERFERENCE-001",
        "seed":SEED,
        "classification":"constructed_local_mechanism_evidence",
        "main_matrix":classify(),
        "targeted_ablation":targeted_ablation(),
        "consent_binding":consent_test(),
        "claim_boundary":[
            "Generated attack frequencies are coverage choices, not production risk estimates.",
            "The UIC gate is tested against constructed mutation families, not arbitrary semantic attacks.",
            "No target Qwen model, OS sandbox, cryptographic signature implementation, or human-comprehension study is executed here.",
            "Zero observed false accepts is not a formal proof."
        ]
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
