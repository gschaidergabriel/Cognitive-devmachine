#!/usr/bin/env python3
"""Trigger-2 dynamic-binding pilot blueprint generator (v2.1).

Produces deterministic, fully-factorial BLUEPRINT rows only. Rows are deliberately
non-trainable until the exact Claude-supplied ABI accepted-atom surface is resolved
against the pinned tokenizer. No invented symbol token can pass this generator.
"""
from __future__ import annotations
import argparse, itertools, json, math
from collections import Counter

SCHEMA="CLAY_TRIGGER2_DYNAMIC_BINDING_EPISODE_BLUEPRINT/v2.1"
MODEL="Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MODEL_REV="591852bda6e1979f59e4b0f5ee2919697b12e936"
SOURCE_PACKAGE_SHA256="a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
ABI_MANIFEST_SHA256="0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
CLASSES=("ALLOW","DENY","ABSTAIN"); POLARITIES=("POS","NEG"); PERMS=tuple(itertools.permutations(range(3)))
LAYOUTS=("EVIDENCE_THEN_QUERY","QUERY_THEN_EVIDENCE")
TRAIN_TEMPLATES=("T1_NUMERIC_COMPARISON","T2_SET_MEMBERSHIP","T3_ORDER_RELATION","T4_ATTRIBUTE_BINDING")
VALIDATION_TEMPLATE="T5_BOOLEAN_XOR_VALIDATION"; HOLDOUT_TEMPLATE="T6_PARITY_HOLDOUT"
TRAIN_TRIPLETS=((0,1,2),(3,4,5),(6,7,8),(9,10,11)); HOLDOUT_TRIPLET=(12,13,14)

def atom_ref(n:int)->str: return f"ABI_ACCEPTED_ORDINAL:{n:02d}"

def semantic_text(t:str,c:str,p:str):
    neg=p=="NEG"
    if t=="T1_NUMERIC_COMPARISON":
        q="Register r is not greater than 5." if neg else "Register r is greater than 5."
        tab=({"ALLOW":"Register r has value 3.","DENY":"Register r has value 7.","ABSTAIN":"Register s has value 3; no value for register r is given."} if neg else {"ALLOW":"Register r has value 7.","DENY":"Register r has value 3.","ABSTAIN":"Register s has value 7; no value for register r is given."})
    elif t=="T2_SET_MEMBERSHIP":
        q="Marker m does not belong to set K." if neg else "Marker m belongs to set K."
        tab=({"ALLOW":"Set K explicitly excludes marker m.","DENY":"Set K explicitly contains marker m.","ABSTAIN":"Set K contains marker n; membership of marker m is unspecified."} if neg else {"ALLOW":"Set K explicitly contains marker m.","DENY":"Set K explicitly excludes marker m.","ABSTAIN":"Set K contains marker n; membership of marker m is unspecified."})
    elif t=="T3_ORDER_RELATION":
        q="Node p does not occur before node q." if neg else "Node p occurs before node q."
        tab=({"ALLOW":"The order record states q before p.","DENY":"The order record states p before q.","ABSTAIN":"The order record states p before z; relation between p and q is unspecified."} if neg else {"ALLOW":"The order record states p before q.","DENY":"The order record states q before p.","ABSTAIN":"The order record states p before z; relation between p and q is unspecified."})
    elif t=="T4_ATTRIBUTE_BINDING":
        q="Object v does not have texture rough." if neg else "Object v has texture rough."
        tab=({"ALLOW":"Object v is recorded with texture smooth.","DENY":"Object v is recorded with texture rough.","ABSTAIN":"Object w is recorded with texture rough; texture of object v is unspecified."} if neg else {"ALLOW":"Object v is recorded with texture rough.","DENY":"Object v is recorded with texture smooth.","ABSTAIN":"Object w is recorded with texture rough; texture of object v is unspecified."})
    elif t==VALIDATION_TEMPLATE:
        q="It is not the case that exactly one of flags a and b is active." if neg else "Exactly one of flags a and b is active."
        tab=({"ALLOW":"Flags a and b are both active.","DENY":"Flag a is active and flag b is inactive.","ABSTAIN":"Flag a is active; the state of flag b is unspecified."} if neg else {"ALLOW":"Flag a is active and flag b is inactive.","DENY":"Flags a and b are both active.","ABSTAIN":"Flag a is active; the state of flag b is unspecified."})
    elif t==HOLDOUT_TEMPLATE:
        q="The recorded integer is not even." if neg else "The recorded integer is even."
        tab=({"ALLOW":"The recorded integer is 15.","DENY":"The recorded integer is 14.","ABSTAIN":"No integer value is recorded."} if neg else {"ALLOW":"The recorded integer is 14.","DENY":"The recorded integer is 15.","ABSTAIN":"No integer value is recorded."})
    else: raise ValueError(t)
    return tab[c],q

def build_rows():
    rows=[]
    specs=[*( (t,"TRAIN",TRAIN_TRIPLETS) for t in TRAIN_TEMPLATES), (VALIDATION_TEMPLATE,"VALIDATION",TRAIN_TRIPLETS), (HOLDOUT_TEMPLATE,"HOLDOUT_FROZEN",(HOLDOUT_TRIPLET,))]
    for t,split,triplets in specs:
      for triple in triplets:
       for mi,mapping in enumerate(PERMS):
        for oi,order in enumerate(PERMS):
         for li,layout in enumerate(LAYOUTS):
          for ci,c in enumerate(CLASSES):
           for p in POLARITIES:
            e,q=semantic_text(t,c,p); eid=f"{t}_S{triple[0]:02d}_M{mi}_O{oi}_L{li}_{c}_{p}"
            rows.append({"schema":SCHEMA,"id":eid,"split":split,"t":t,"c":c,"p":p,"perm":list(mapping),"sym":[atom_ref(x) for x in triple],"ord":list(order),"lay":layout,"target":atom_ref(triple[mapping[ci]]),"e":e,"q":q,"model":MODEL,"model_revision":MODEL_REV,"source_package_sha256":SOURCE_PACKAGE_SHA256,"abi_manifest_sha256":ABI_MANIFEST_SHA256,"class_word_policy":"LABELS_ONLY_INSIDE_CODEBOOK_BLOCK","render_status":"BLOCKED_UNTIL_EXACT_ABI_ATOM_SURFACE_AND_PINNED_TOKENIZER_BINDING","training_eligible":False,"selected_using_holdout":False})
    return rows

def mi(rows,fa,fb):
    n=len(rows); j=Counter((fa(r),fb(r)) for r in rows); a=Counter(fa(r) for r in rows); b=Counter(fb(r) for r in rows)
    return sum((v/n)*math.log2((v/n)/((a[x]/n)*(b[y]/n))) for (x,y),v in j.items())

def selftest(rows):
    train=[r for r in rows if r["split"]=="TRAIN"]; val=[r for r in rows if r["split"]=="VALIDATION"]; hold=[r for r in rows if r["split"]=="HOLDOUT_FROZEN"]
    assert (len(train),len(val),len(hold))==(6912,1728,432)
    assert {r["t"] for r in train}==set(TRAIN_TEMPLATES) and {r["t"] for r in val}=={VALIDATION_TEMPLATE} and {r["t"] for r in hold}=={HOLDOUT_TEMPLATE}
    for r in rows:
        ci=CLASSES.index(r["c"]); assert r["target"]==r["sym"][r["perm"][ci]]
        assert tuple(r["perm"]) in PERMS and tuple(r["ord"]) in PERMS and r["lay"] in LAYOUTS
        assert not any(x in (r["e"]+" "+r["q"]).upper() for x in CLASSES)
    for t in TRAIN_TEMPLATES+(VALIDATION_TEMPLATE,HOLDOUT_TEMPLATE):
      for syms in {tuple(r["sym"]) for r in rows if r["t"]==t}:
        rr=[r for r in rows if r["t"]==t and tuple(r["sym"])==syms]
        cells=Counter((tuple(r["perm"]),tuple(r["ord"]),r["lay"],r["c"],r["p"]) for r in rr)
        assert len(cells)==432 and set(cells.values())=={1}
    train_syms={s for r in train for s in r["sym"]}; val_syms={s for r in val for s in r["sym"]}; hold_syms={s for r in hold for s in r["sym"]}
    assert train_syms==val_syms and train_syms.isdisjoint(hold_syms)
    metrics={
      "class__target_symbol":mi(train,lambda r:r["c"],lambda r:r["target"]),
      "target_symbol__template":mi(train,lambda r:r["target"],lambda r:r["t"]),
      "target_symbol__codebook_order":mi(train,lambda r:r["target"],lambda r:tuple(r["ord"])),
      "target_symbol__layout":mi(train,lambda r:r["target"],lambda r:r["lay"]),
      "target_symbol__polarity":mi(train,lambda r:r["target"],lambda r:r["p"]),
      "mapping__codebook_order":mi(train,lambda r:tuple(r["perm"]),lambda r:tuple(r["ord"])),
      "class__codebook_order":mi(train,lambda r:r["c"],lambda r:tuple(r["ord"])),
    }
    assert all(abs(v)<1e-12 for v in metrics.values())
    assert set(Counter(r["target"] for r in train).values())=={576}
    return {"pass":True,"rows":len(rows),"train":len(train),"validation":len(val),"holdout":len(hold),"train_templates":4,"validation_templates":1,"frozen_unseen_templates":1,"s3_mapping_permutations":6,"s3_codebook_orders":6,"layouts":2,"train_symbols":12,"holdout_unseen_symbols":3,"shortcut_mi_bits":metrics,"training_eligible":False,"blocker":"exact ABI accepted-atom strings and exact pinned-tokenizer rendering/last-token checks are not available in current canonical repo evidence"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--split",choices=("all","train","validation","holdout"),default="all"); ap.add_argument("--selftest",action="store_true"); args=ap.parse_args(); rows=build_rows()
    if args.selftest: print(json.dumps(selftest(rows),sort_keys=True)); return
    key={"train":"TRAIN","validation":"VALIDATION","holdout":"HOLDOUT_FROZEN"}.get(args.split)
    for r in rows if key is None else [x for x in rows if x["split"]==key]: print(json.dumps(r,separators=(",",":"),ensure_ascii=False))
if __name__=="__main__": main()
