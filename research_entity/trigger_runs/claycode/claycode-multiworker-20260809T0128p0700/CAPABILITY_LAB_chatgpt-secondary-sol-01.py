#!/usr/bin/env python3
import random, hashlib, json

SEED = 202608090130
OPS = ("fs.write","fs.delete","service.restart","net.send")

def canonical_intent(intent):
    obj = {"op": intent["op"], "target": intent["target"], "amount": intent["amount"], "epoch": intent["epoch"], "origins": sorted(intent["origins"]), "nonce": intent["nonce"]}
    return json.dumps(obj, sort_keys=True, separators=(",",":"))

def intent_hash(intent):
    return hashlib.sha256(canonical_intent(intent).encode()).hexdigest()

def strong_guard(intent, permit, now_epoch, used):
    if intent["op"] not in permit["allowed_ops"]: return False
    if not intent["target"].startswith(permit["target_prefix"]): return False
    if intent["amount"] > permit["max_call"]: return False
    if used + intent["amount"] > permit["max_total"]: return False
    if now_epoch > permit["expiry_epoch"]: return False
    if intent["epoch"] != permit["epoch"] or now_epoch != permit["epoch"]: return False
    if any(o not in permit["allowed_origins"] for o in intent["origins"]): return False
    if intent_hash(intent) != permit["intent_hash"]: return False
    return True

def oracle_guard(intent, permit, now_epoch, used):
    canonical = json.dumps({"amount":intent["amount"], "epoch":intent["epoch"], "nonce":intent["nonce"], "op":intent["op"], "origins":sorted(intent["origins"]), "target":intent["target"]}, sort_keys=True, separators=(",",":"))
    return all([{intent["op"]}.issubset(set(permit["allowed_ops"])), intent["target"][:len(permit["target_prefix"])] == permit["target_prefix"], 0 <= intent["amount"] <= permit["max_call"], used >= 0 and used + intent["amount"] <= permit["max_total"], now_epoch <= permit["expiry_epoch"], (intent["epoch"], now_epoch) == (permit["epoch"], permit["epoch"]), set(intent["origins"]) <= set(permit["allowed_origins"]), hashlib.sha256(canonical.encode()).hexdigest() == permit["intent_hash"]])

def naive_guard(intent, permit, now_epoch, used):
    return (intent["op"] in permit["allowed_ops"] and intent["target"].startswith(permit["target_prefix"]) and intent["amount"] <= permit["max_call"] and now_epoch <= permit["expiry_epoch"])

def run():
    rng = random.Random(SEED)
    attack_types = ["target_mutation","op_mutation","amount_mutation","epoch_stale","origin_launder","intent_replay","path_escape","expired","cumulative_overshoot"]
    counts = {a: {"cases":0,"naive_accepts":0,"strong_accepts":0} for a in attack_types}
    total = 120000
    legit = attacks = naive_false = strong_false = oracle_mismatch = false_reject = 0
    def make_case(i):
        epoch = rng.randint(1,50); op = rng.choice(OPS); target_prefix = rng.choice(("/srv/app/","/data/project/","user:alice/")); target = target_prefix + f"obj{i%997}"; amount = rng.randint(1,64); origins = [rng.choice(("trusted_user","trusted_runtime"))]
        intent = {"op":op,"target":target,"amount":amount,"epoch":epoch,"origins":origins,"nonce":f"n{i}-{rng.randrange(1<<30)}"}
        permit = {"allowed_ops":[op],"target_prefix":target_prefix,"max_call":64,"max_total":rng.randint(96,512),"allowed_origins":["trusted_user","trusted_runtime"],"epoch":epoch,"expiry_epoch":epoch,"intent_hash":intent_hash(intent)}
        used = rng.randint(0,max(0,permit["max_total"]-amount)); return intent, permit, epoch, used
    for i in range(total):
        intent, permit, now, used = make_case(i); is_legit = rng.random() < 0.45; at = None
        if not is_legit:
            attacks += 1; at = rng.choice(attack_types); counts[at]["cases"] += 1
            if at == "target_mutation": intent["target"] = permit["target_prefix"] + f"other{i}"
            elif at == "op_mutation": intent["op"] = "db.drop"
            elif at == "amount_mutation": intent["amount"] = permit["max_call"] + rng.randint(1,64)
            elif at == "epoch_stale": intent["epoch"] = permit["epoch"] - 1
            elif at == "origin_launder": intent["origins"] = ["tool_echo"]
            elif at == "intent_replay": intent["nonce"] += "-replay"
            elif at == "path_escape": intent["target"] = "/etc/passwd"
            elif at == "expired": now = permit["expiry_epoch"] + 1
            elif at == "cumulative_overshoot": used = max(permit["max_total"] - intent["amount"] + 1, 0)
        else: legit += 1
        n = naive_guard(intent,permit,now,used); s = strong_guard(intent,permit,now,used); o = oracle_guard(intent,permit,now,used)
        oracle_mismatch += int(s != o); false_reject += int(is_legit and not s)
        if not is_legit:
            if n: naive_false += 1; counts[at]["naive_accepts"] += 1
            if s: strong_false += 1; counts[at]["strong_accepts"] += 1
    sessions = 20000; stateless_overshoot = stateful_overshoot = stateless_units = stateful_blocked = 0
    for _ in range(sessions):
        max_call = rng.randint(8,64); max_total = rng.randint(max_call,max_call*4); calls = [rng.randint(1,max_call) for _ in range(rng.randint(2,12))]; total_used = sum(calls)
        if total_used > max_total: stateless_overshoot += 1; stateless_units += total_used - max_total
        used = 0
        for c in calls:
            if used + c <= max_total: used += c
            else: stateful_blocked += 1
        stateful_overshoot += int(used > max_total)
    chains = 50000; naive_launder = origin_bound_launder = 0
    for _ in range(chains):
        ancestry = ["untrusted_memory"]; current_producer = "trusted_runtime"; naive_launder += int(current_producer == "trusted_runtime"); origin_bound_launder += int(all(x in {"trusted_user","trusted_runtime"} for x in ancestry))
    result = {"seed":SEED,"authority_mutation_cases":total,"legit_controls":legit,"attack_cases":attacks,"strong_vs_independent_oracle_mismatches":oracle_mismatch,"naive_guard_false_accepts":naive_false,"strong_guard_false_accepts":strong_false,"strong_guard_legit_false_rejects":false_reject,"attack_breakdown":counts,"cumulative_sessions":sessions,"stateless_per_call_budget_overshoot_sessions":stateless_overshoot,"stateful_monotone_budget_overshoot_sessions":stateful_overshoot,"stateless_total_overshoot_units":stateless_units,"stateful_blocked_calls":stateful_blocked,"laundering_chains":chains,"naive_current_producer_launder_success":naive_launder,"origin_bound_launder_success":origin_bound_launder}
    print(json.dumps(result,sort_keys=True))

if __name__ == "__main__": run()
