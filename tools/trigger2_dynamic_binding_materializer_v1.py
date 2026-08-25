#!/usr/bin/env python3
"""Trigger-2 evidence-bound dynamic-binding materializer v1.

Creates PRE-HOLDOUT candidate rows only. It deliberately does not contain the frozen
holdout template body, holdout lexical family, or held-out ABI atom surfaces.
Actual atom surfaces must be supplied from the exact admitted 46-atom inventory.

The materializer reserves:
  TRAIN_CORE perms: P012, P021, P102, P120
  VALIDATION_PERM: P201
  HOLDOUT_PERM: P210 (not emitted pre-holdout)
  HOLDOUT_SYMBOL: 10 accepted atoms selected by a preregistered hash partition (not emitted pre-holdout)
  HOLDOUT_TEMPLATE: T5_FROZEN_UNMATERIALIZED (body absent)

This is source/candidate tooling only and cannot mint training/runtime/J-Space credit.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, re
from pathlib import Path

SCHEMA="TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v2"
CLASSES=("ALLOW","DENY","ABSTAIN")
S3={
 "P012":(0,1,2),"P021":(0,2,1),"P102":(1,0,2),
 "P120":(1,2,0),"P201":(2,0,1),"P210":(2,1,0),
}
TRAIN_PERMS=("P012","P021","P102","P120")
VALIDATION_PERM="P201"
HOLDOUT_PERM="P210"
HOLDOUT_COUNT=10
HOLDOUT_PARTITION_SEED="TRIGGER2_SYMBOL_HOLDOUT_V1_20260825"
TEMPLATES=("T1_RECORD","T2_CASE","T3_DIALOGUE","T4_STRUCTURED")
FROZEN_TEMPLATE_ID="T5_FROZEN_UNMATERIALIZED"
CODEBOOK_LABELS=("ALLOW","DENY","ABSTAIN")


def sha256_bytes(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def load_atoms(path:Path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    atoms=obj.get("accepted_atoms") if isinstance(obj,dict) else obj
    if not isinstance(atoms,list) or len(atoms)!=46 or not all(isinstance(x,str) and x for x in atoms):
        raise ValueError("atom inventory must resolve to exactly 46 non-empty accepted atom strings")
    if len(set(atoms))!=46: raise ValueError("accepted atom inventory contains duplicates")
    return atoms

def load_families(path:Path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): raise ValueError("semantic family input must be an object")
    out={}
    for split in ("TRAIN","VALIDATION"):
      rows=obj.get(split,[])
      if not isinstance(rows,list) or not rows: raise ValueError(f"{split} needs >=1 semantic family")
      out[split]=[]
      for f in rows:
        if not isinstance(f,dict): raise ValueError("family must be object")
        cases=f.get("cases")
        if not isinstance(cases,dict) or set(cases)!=set(CLASSES): raise ValueError("family cases must be exactly ALLOW/DENY/ABSTAIN")
        if not all(isinstance(cases[c],str) and cases[c] for c in CLASSES): raise ValueError("case texts must be non-empty")
        out[split].append({"family_id":str(f["family_id"]),"ancestry_id":str(f["ancestry_id"]),"cases":cases})
    train_ids={f["family_id"] for f in out["TRAIN"]}; val_ids={f["family_id"] for f in out["VALIDATION"]}
    if train_ids & val_ids: raise ValueError("semantic family ids cross train/validation")
    train_a={f["ancestry_id"] for f in out["TRAIN"]}; val_a={f["ancestry_id"] for f in out["VALIDATION"]}
    if train_a & val_a: raise ValueError("ancestry ids cross train/validation")
    return out

def load_lexemes(path:Path):
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,list) or not v or not all(isinstance(x,str) and x for x in v): raise ValueError("forbidden lexemes must be non-empty string array")
    return tuple(v)

def render(template, evidence, query="P"):
    if template=="T1_RECORD": return f"Evidence record:\n{evidence}\nQuery: {query}\nReturn exactly one codebook atom."
    if template=="T2_CASE": return f"CASE[ evidence = {evidence} ]\nEvaluate proposition {query} through this episode mapping.\nEmit one atom only."
    if template=="T3_DIALOGUE": return f"Observer: {evidence}\nAuditor: use the current episode mapping.\nTask: evaluate {query}; output one atom."
    if template=="T4_STRUCTURED": return f"<CASE>proposition=P;evidence={evidence}</CASE>\nQUERY={query}\nOUTPUT=one_atom"
    raise ValueError(template)

def codebook(mapping,order):
    return "[CODEBOOK]\n"+"\n".join(f"{c} => {mapping[c]}" for c in order)+"\n[/CODEBOOK]"

def rotations3(xs): return (xs, (xs[1],xs[2],xs[0]), (xs[2],xs[0],xs[1]))
def flip(c): return {"ALLOW":"DENY","DENY":"ALLOW","ABSTAIN":"ABSTAIN"}[c]

def partition_atoms(atoms):
    ranked=sorted(atoms,key=lambda a: hashlib.sha256((HOLDOUT_PARTITION_SEED+"\0"+a).encode()).hexdigest())
    holdout=tuple(ranked[:HOLDOUT_COUNT]); pre=tuple(ranked[HOLDOUT_COUNT:])
    assert len(pre)==36 and len(holdout)==10
    return pre,holdout

def triplets(atoms):
    pool,_=partition_atoms(atoms)
    return tuple(tuple(pool[i:i+3]) for i in range(0,36,3))

def emit_split(split,families,atoms,hashes):
    eval_family="TRAIN_CORE" if split=="TRAIN" else "VALIDATION_PERM"
    perms=TRAIN_PERMS if split=="TRAIN" else (VALIDATION_PERM,)
    rows=[]; groups=triplets(atoms)
    for fam in families:
      for template in TEMPLATES:
       for gi,base_triplet in enumerate(groups):
        for atom_order_i,ordered in enumerate(rotations3(base_triplet)):
         for pid in perms:
          p=S3[pid]; mapping={CLASSES[i]:ordered[p[i]] for i in range(3)}
          for base_cls in CLASSES:
           for polarity in ("DIRECT","NEGATED"):
            target_cls=base_cls if polarity=="DIRECT" else flip(base_cls)
            query="P" if polarity=="DIRECT" else "NOT P"
            order=tuple(CLASSES[(i+gi+atom_order_i)%3] for i in range(3))
            prompt=codebook(mapping,order)+"\n"+render(template,fam["cases"][base_cls],query)
            row={
             "schema":SCHEMA,"split":split,"eval_family":eval_family,
             "canonical_truth_allowed":False,"direct_effect_authority":False,"selected_using_holdout":False,
             "target_semantic_class":target_cls,"episode_atom_triplet":list(ordered),"permutation_id":pid,
             "realized_codebook":mapping,"target":mapping[target_cls],"prompt":prompt,"template_id":template,
             "family_id":fam["family_id"],"provenance_ancestry_id":fam["ancestry_id"],
             "query_polarity":polarity,"base_semantic_class":base_cls,
             "atom_group":gi,"atom_order_rotation":atom_order_i,
             **hashes,
            }
            row["row_id"]="T2MAT-"+hashlib.sha256(canon({k:v for k,v in row.items() if k!="row_id"}).encode()).hexdigest()[:20]
            rows.append(row)
    return rows

def mi(rows):
    n=len(rows); j=collections.Counter((r["target_semantic_class"],r["target"]) for r in rows)
    pc=collections.Counter(r["target_semantic_class"] for r in rows); ps=collections.Counter(r["target"] for r in rows)
    return sum((k/n)*math.log2((k/n)/((pc[c]/n)*(ps[s]/n))) for (c,s),k in j.items()) if n else float("inf")

def validate_prehHoldout(rows, atoms, forbidden):
    fails=[]
    if not rows: fails.append("NO_ROWS")
    ids=[r["row_id"] for r in rows]
    if len(ids)!=len(set(ids)): fails.append("DUPLICATE_ROW_ID")
    if any(r["permutation_id"]==HOLDOUT_PERM for r in rows): fails.append("HOLDOUT_PERM_LEAK")
    _,held_tuple=partition_atoms(atoms); held=set(held_tuple)
    joined="\n".join(r["prompt"]+"\n"+r["target"] for r in rows)
    if any(a in joined for a in held): fails.append("HOLDOUT_SYMBOL_LEAK")
    if any(r["template_id"]==FROZEN_TEMPLATE_ID for r in rows): fails.append("HOLDOUT_TEMPLATE_LEAK")
    train=[r for r in rows if r["eval_family"]=="TRAIN_CORE"]
    m=mi(train)
    if not math.isfinite(m) or m>1e-12: fails.append("TRAIN_CLASS_SYMBOL_MI_NONZERO")
    per=collections.defaultdict(collections.Counter)
    for r in train: per[r["target"]][r["target_semantic_class"]]+=1
    if any(max(c.get(k,0) for k in CLASSES)-min(c.get(k,0) for k in CLASSES)>0 for c in per.values()): fails.append("TRAIN_CLASS_SYMBOL_IMBALANCE")
    pat=re.compile(r"\[CODEBOOK\].*?\[/CODEBOOK\]",re.S)
    for r in rows:
      outside=pat.sub("",r["prompt"])
      for lx in (*CODEBOOK_LABELS,*forbidden):
        if re.search(rf"\b{re.escape(lx)}\b",outside,re.I):
          fails.append("LEXEME_LEAK:"+r["row_id"]+":"+lx); break
    return {
      "status":"PASS" if not fails else "FAIL","failures":sorted(set(fails)),"rows":len(rows),"train_rows":len(train),
      "validation_rows":sum(r["split"]=="VALIDATION" for r in rows),"train_mi_bits":m,
      "train_atoms":len({r["target"] for r in train}),"reserved_holdout_atom_count":len(held),"holdout_partition_seed":HOLDOUT_PARTITION_SEED,
      "train_perms":list(TRAIN_PERMS),"validation_perm":VALIDATION_PERM,"reserved_holdout_perm":HOLDOUT_PERM,
      "frozen_holdout_template":FROZEN_TEMPLATE_ID,
      "credit":{"accepted_dataset_tokens":0,"training_credit":0,"jspace_model_runtime_credit":0},
    }

def materialize(abi_path,atom_path,family_path,lexeme_path,generator_path,model_path,tokenizer_path):
    atoms=load_atoms(atom_path); families=load_families(family_path); forbidden=load_lexemes(lexeme_path)
    hashes={
      "abi_manifest_sha256":sha256_bytes(abi_path),
      "atom_inventory_sha256":sha256_bytes(atom_path),"generator_sha256":sha256_bytes(generator_path),
      "forbidden_lexeme_inventory_sha256":sha256_bytes(lexeme_path),"model_identity_sha256":sha256_bytes(model_path),
      "tokenizer_identity_sha256":sha256_bytes(tokenizer_path),
    }
    rows=emit_split("TRAIN",families["TRAIN"],atoms,hashes)+emit_split("VALIDATION",families["VALIDATION"],atoms,hashes)
    return rows,validate_prehHoldout(rows,atoms,forbidden)

def synthetic_selftest():
    atoms=[f"¤{i:02d}" for i in range(46)]
    fam={
      "TRAIN":[{"family_id":"train_A","ancestry_id":"anc_A","cases":{"ALLOW":"Two independent confirmations establish P.","DENY":"A binding contradiction defeats P.","ABSTAIN":"The decisive observation is missing for P."}}],
      "VALIDATION":[{"family_id":"val_B","ancestry_id":"anc_B","cases":{"ALLOW":"Separate witnesses corroborate P.","DENY":"A higher priority veto defeats P.","ABSTAIN":"Evidence remains insufficient to settle P."}}],
    }
    hashes={k:"0"*64 for k in ("abi_manifest_sha256","atom_inventory_sha256","generator_sha256","forbidden_lexeme_inventory_sha256","model_identity_sha256","tokenizer_identity_sha256")}
    rows=emit_split("TRAIN",fam["TRAIN"],atoms,hashes)+emit_split("VALIDATION",fam["VALIDATION"],atoms,hashes)
    return validate_prehHoldout(rows,atoms,("permit","reject"))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--abi-manifest"); ap.add_argument("--atom-inventory"); ap.add_argument("--semantic-families"); ap.add_argument("--forbidden-lexemes"); ap.add_argument("--model-identity"); ap.add_argument("--tokenizer-identity"); ap.add_argument("--jsonl"); ap.add_argument("--audit")
    ns=ap.parse_args()
    if ns.self_test:
      r=synthetic_selftest(); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r["status"]=="PASS" else 1
    req=[ns.abi_manifest,ns.atom_inventory,ns.semantic_families,ns.forbidden_lexemes,ns.model_identity,ns.tokenizer_identity]
    if not all(req): raise SystemExit("materialization requires ABI manifest, atom inventory, semantic families, forbidden lexemes, model identity and tokenizer identity")
    rows,audit=materialize(Path(ns.abi_manifest),Path(ns.atom_inventory),Path(ns.semantic_families),Path(ns.forbidden_lexemes),Path(__file__),Path(ns.model_identity),Path(ns.tokenizer_identity))
    blob="".join(canon(r)+"\n" for r in rows)
    audit["jsonl_sha256"]=hashlib.sha256(blob.encode()).hexdigest()
    if ns.jsonl: Path(ns.jsonl).write_text(blob,encoding="utf-8")
    if ns.audit: Path(ns.audit).write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(audit,indent=2,sort_keys=True)); return 0 if audit["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
