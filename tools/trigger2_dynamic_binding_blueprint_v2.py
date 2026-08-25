#!/usr/bin/env python3
"""Generate non-trainable Trigger-2 dynamic-binding blueprints.

Blueprints are intentionally NOT rendered to model text until the exact Claude-supplied
ABI atom surface and pinned tokenizer are available. This prevents invented/unchecked
symbol tokens from entering the training lane.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, random
from collections import Counter, defaultdict

SCHEMA = "CLAY_TRIGGER2_DYNAMIC_BINDING_EPISODE_BLUEPRINT/v2"
MODEL = "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MODEL_REV = "591852bda6e1979f59e4b0f5ee2919697b12e936"
SOURCE_PACKAGE_SHA256 = "a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
POLARITIES = ("POS", "NEG")
PERMS = tuple(itertools.permutations(range(3)))
TRAIN_TEMPLATES = ("T1_NUMERIC_COMPARISON", "T2_SET_MEMBERSHIP", "T3_ORDER_RELATION", "T4_ATTRIBUTE_BINDING")
HOLDOUT_TEMPLATE = "T5_PARITY_HOLDOUT"
TRAIN_TRIPLETS = ((0,1,2),(3,4,5),(6,7,8),(9,10,11))
HOLDOUT_TRIPLET = (12,13,14)


def atom_ref(n:int)->str: return f"ABI_ACCEPTED_ORDINAL:{n:02d}"


def semantic_text(template:str, cls:str, pol:str):
    if template == "T1_NUMERIC_COMPARISON":
        q = "Register r is greater than 5." if pol=="POS" else "Register r is not greater than 5."
        table = ({"ALLOW":"Register r has value 7.","DENY":"Register r has value 3.","ABSTAIN":"Register s has value 7; no value for register r is given."}
                 if pol=="POS" else
                 {"ALLOW":"Register r has value 3.","DENY":"Register r has value 7.","ABSTAIN":"Register s has value 3; no value for register r is given."})
    elif template == "T2_SET_MEMBERSHIP":
        q = "Marker m belongs to set K." if pol=="POS" else "Marker m does not belong to set K."
        table = ({"ALLOW":"Set K explicitly contains marker m.","DENY":"Set K explicitly excludes marker m.","ABSTAIN":"Set K contains marker n; membership of marker m is unspecified."}
                 if pol=="POS" else
                 {"ALLOW":"Set K explicitly excludes marker m.","DENY":"Set K explicitly contains marker m.","ABSTAIN":"Set K contains marker n; membership of marker m is unspecified."})
    elif template == "T3_ORDER_RELATION":
        q = "Node p occurs before node q." if pol=="POS" else "Node p does not occur before node q."
        table = ({"ALLOW":"The order record states p before q.","DENY":"The order record states q before p.","ABSTAIN":"The order record states p before z; relation between p and q is unspecified."}
                 if pol=="POS" else
                 {"ALLOW":"The order record states q before p.","DENY":"The order record states p before q.","ABSTAIN":"The order record states p before z; relation between p and q is unspecified."})
    elif template == "T4_ATTRIBUTE_BINDING":
        q = "Object v has texture rough." if pol=="POS" else "Object v does not have texture rough."
        table = ({"ALLOW":"Object v is recorded with texture rough.","DENY":"Object v is recorded with texture smooth.","ABSTAIN":"Object w is recorded with texture rough; texture of object v is unspecified."}
                 if pol=="POS" else
                 {"ALLOW":"Object v is recorded with texture smooth.","DENY":"Object v is recorded with texture rough.","ABSTAIN":"Object w is recorded with texture rough; texture of object v is unspecified."})
    elif template == HOLDOUT_TEMPLATE:
        q = "The recorded integer is even." if pol=="POS" else "The recorded integer is not even."
        table = ({"ALLOW":"The recorded integer is 14.","DENY":"The recorded integer is 15.","ABSTAIN":"No integer value is recorded."}
                 if pol=="POS" else
                 {"ALLOW":"The recorded integer is 15.","DENY":"The recorded integer is 14.","ABSTAIN":"No integer value is recorded."})
    else: raise ValueError(template)
    return table[cls], q


def build_rows():
    rows=[]
    templates=TRAIN_TEMPLATES+(HOLDOUT_TEMPLATE,)
    for ti,template in enumerate(templates):
        split="TRAIN" if template in TRAIN_TEMPLATES else "HOLDOUT_FROZEN"
        for pi,perm in enumerate(PERMS):
            triplet=TRAIN_TRIPLETS[(ti+pi)%len(TRAIN_TRIPLETS)] if split=="TRAIN" else HOLDOUT_TRIPLET
            for ci,cls in enumerate(CLASSES):
                for pol in POLARITIES:
                    eid=f"{template}_P{pi}_{cls}_{pol}"
                    rng=random.Random(int(hashlib.sha256(eid.encode()).hexdigest()[:16],16))
                    order=list(range(3)); rng.shuffle(order)
                    evidence,query=semantic_text(template,cls,pol)
                    rows.append({"schema":SCHEMA,"id":eid,"split":split,"t":template,"c":cls,"p":pol,
                        "perm":list(perm),"sym":[atom_ref(x) for x in triplet],"ord":order,
                        "target":atom_ref(triplet[perm[ci]]),"e":evidence,"q":query,
                        "model":MODEL,"model_revision":MODEL_REV,"source_package_sha256":SOURCE_PACKAGE_SHA256,
                        "abi_manifest_sha256":ABI_MANIFEST_SHA256,
                        "class_word_policy":"LABELS_ONLY_INSIDE_CODEBOOK_BLOCK",
                        "render_status":"BLOCKED_UNTIL_EXACT_ABI_ATOM_SURFACE_AND_TOKENIZER_BINDING",
                        "training_eligible":False,"selected_using_holdout":False})
    # Layout is balanced inside every target x output-slot x polarity cell.
    groups=defaultdict(list)
    for r in rows:
        ci=CLASSES.index(r["c"]); slot=r["perm"][ci]
        groups[(r["t"],r["c"],slot,r["p"])].append(r)
    for items in groups.values():
        items.sort(key=lambda x:x["id"])
        assert len(items)==2
        items[0]["lay"]="EVIDENCE_THEN_QUERY"; items[1]["lay"]="QUERY_THEN_EVIDENCE"
    return rows


def mutual_information(rows):
    joint=Counter((r["c"],r["target"]) for r in rows); xs=Counter(r["c"] for r in rows); ys=Counter(r["target"] for r in rows); n=len(rows)
    return sum((v/n)*math.log2((v/n)/((xs[x]/n)*(ys[y]/n))) for (x,y),v in joint.items())


def selftest(rows):
    train=[r for r in rows if r["split"]=="TRAIN"]; hold=[r for r in rows if r["split"]=="HOLDOUT_FROZEN"]
    assert (len(train),len(hold))==(144,36)
    assert {r["t"] for r in train}==set(TRAIN_TEMPLATES) and {r["t"] for r in hold}=={HOLDOUT_TEMPLATE}
    assert {tuple(r["perm"]) for r in train}==set(PERMS) and {tuple(r["perm"]) for r in hold}==set(PERMS)
    for r in rows:
        ci=CLASSES.index(r["c"]); assert r["target"]==r["sym"][r["perm"][ci]]
        assert not any(x in (r["e"]+" "+r["q"]).upper() for x in CLASSES)
    for t in TRAIN_TEMPLATES+(HOLDOUT_TEMPLATE,):
        rr=[r for r in rows if r["t"]==t]
        c=Counter((r["c"],r["perm"][CLASSES.index(r["c"])],r["p"],r["lay"]) for r in rr)
        assert len(c)==36 and set(c.values())=={1}
    train_syms={s for r in train for s in r["sym"]}; hold_syms={s for r in hold for s in r["sym"]}
    assert train_syms.isdisjoint(hold_syms)
    target_counts=Counter(r["target"] for r in train); assert len(target_counts)==12 and set(target_counts.values())=={12}
    mi=mutual_information(train); assert abs(mi)<1e-12
    return {"pass":True,"rows":len(rows),"train":len(train),"holdout":len(hold),"train_templates":4,
            "frozen_unseen_templates":1,"s3_permutations":6,"target_code_polarity_layout_cells_per_template":36,
            "class_target_symbol_mi_bits":mi,"train_symbols":12,"holdout_unseen_symbols":3,
            "training_eligible":False,"blocker":"exact ABI atom strings + pinned-tokenizer rendering are not available in canonical repo evidence"}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--split",choices=("all","train","holdout"),default="all"); ap.add_argument("--selftest",action="store_true"); args=ap.parse_args()
    rows=build_rows()
    if args.selftest: print(json.dumps(selftest(rows),sort_keys=True)); return
    wanted={"all":rows,"train":[r for r in rows if r["split"]=="TRAIN"],"holdout":[r for r in rows if r["split"]=="HOLDOUT_FROZEN"]}[args.split]
    for r in wanted: print(json.dumps(r,separators=(",",":"),ensure_ascii=False))
if __name__=="__main__": main()
