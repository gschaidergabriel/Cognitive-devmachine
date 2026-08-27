#!/usr/bin/env python3
import argparse, hashlib, json, random, uuid
from pathlib import Path

RULES = [
    ("CC.TYPE.MISMATCH",1,"typecheck"),
    ("CC.EFFECT.AUTHORITY_MISSING",1,"effectcheck"),
    ("CC.EFFECT.REVOKED",2,"effectcheck"),
    ("CC.IR.UNKNOWN_FIELD",1,"ir_validate"),
    ("CC.PARSER.UNEXPECTED_TOKEN",3,"parse"),
    ("CC.RUNTIME.RESOURCE_EPOCH_STALE",1,"runtime"),
]
MESSAGES = {
    "CC.TYPE.MISMATCH":["type mismatch","expected value of another type","types are incompatible"],
    "CC.EFFECT.AUTHORITY_MISSING":["missing capability authority","required authority not possessed","effect cannot be authorized"],
    "CC.EFFECT.REVOKED":["capability revoked","authority epoch is stale","revoked capability"],
    "CC.IR.UNKNOWN_FIELD":["unknown field","field is not declared","invalid record field"],
    "CC.PARSER.UNEXPECTED_TOKEN":["unexpected token","token is not valid here","parse error at token"],
    "CC.RUNTIME.RESOURCE_EPOCH_STALE":["resource epoch stale","stale resource generation","resource version no longer current"],
}
SCHEMES=("text_span","rule_only","rule_anchor","structured_v1")

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def ids(d):
    return {
        "text_span":sha({"message":d["message"],"file":d["file"],"line":d["line"],"col":d["col"]}),
        "rule_only":sha({"rule_id":d["rule_id"]}),
        "rule_anchor":sha({"rule_id":d["rule_id"],"anchor":d["anchor"]}),
        "structured_v1":sha({"rule_id":d["rule_id"],"rule_revision":d["rule_revision"],
                            "stage":d["stage"],"semantic_anchor":d["anchor"],
                            "cause_signature":d["cause_signature"]}),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",type=int,default=10000)
    ap.add_argument("--seed",type=int,default=202608091923)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    rng=random.Random(a.seed)
    invariant={s:0 for s in SCHEMES}; sensitivity={s:0 for s in SCHEMES}; events=[]
    for _ in range(a.cases):
        rule_id,rev,stage=rng.choice(RULES)
        base={"rule_id":rule_id,"rule_revision":rev,"stage":stage,
              "anchor":f"node:{rng.randrange(3000):04d}",
              "cause_signature":f"cause:{rng.randrange(200):03d}",
              "message":MESSAGES[rule_id][0],
              "file":f"/repo/src/mod_{rng.randrange(40):02d}.clay",
              "line":rng.randrange(1,600),"col":rng.randrange(1,90)}
        bid=ids(base)
        v=dict(base); v["message"]=rng.choice(MESSAGES[rule_id])
        v["file"]=f"/tmp/build/{uuid.UUID(int=rng.getrandbits(128))}/"+Path(base["file"]).name
        v["line"]=base["line"]+rng.randrange(80); v["col"]=max(1,base["col"]+rng.randrange(-3,8))
        vid=ids(v)
        m=dict(base); m["cause_signature"]=f"cause:mut:{rng.randrange(10_000_000)}"; mid=ids(m)
        for s in SCHEMES:
            invariant[s]+=bid[s]==vid[s]; sensitivity[s]+=bid[s]!=mid[s]
        events.append((base,bid))
    semantic_keys={}
    for d,bid in events:
        key=(d["rule_id"],d["rule_revision"],d["stage"],d["anchor"],d["cause_signature"]); semantic_keys[key]=bid
    metrics={}
    for s in SCHEMES:
        buckets={}
        for d,bid in events:
            key=(d["rule_id"],d["rule_revision"],d["stage"],d["anchor"],d["cause_signature"])
            buckets.setdefault(bid[s],set()).add(key)
        metrics[s]={"nonsemantic_invariance_rate":invariant[s]/a.cases,
                    "semantic_cause_mutation_detection_rate":sensitivity[s]/a.cases,
                    "semantically_distinct_items_in_collision_buckets":sum(len(v) for v in buckets.values() if len(v)>1),
                    "collision_buckets":sum(1 for v in buckets.values() if len(v)>1),
                    "unique_ids":len(buckets)}
    out={"schema_version":"1.0","experiment":"diagnostic_identity_discriminator","seed":a.seed,"cases":a.cases,
         "unique_semantic_events":len(semantic_keys),"metrics":metrics,
         "interpretation_scope":"synthetic discriminator only; not Ubuntu ClayCode production acceptance"}
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
