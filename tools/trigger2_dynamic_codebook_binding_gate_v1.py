#!/usr/bin/env python3
"""Fail-closed specialized gate for Trigger-2 dynamic codebook/binding candidates.

Stricter than the generic trainingtrace candidate gate. It verifies causal S3 mapping,
target derivation, semantic-label leakage, provenance/split isolation, unseen template/
symbol/permutation holdouts, and train class<->symbol shortcut pressure.

P0-P5 follows the current canonical Trigger-2 S3 template-generator convention.
This gate is for materialized/split candidate rows, not the 72-row pre-materialization
design matrix. It cannot admit a canonical dataset or mint runtime/training credit.
"""
from __future__ import annotations
import argparse, collections, json, math, re
from pathlib import Path

SCHEMA="TRIGGER2_DYNAMIC_CODEBOOK_BINDING_GATE/v1.1"
ROW_SCHEMA="TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v1"
CLASSES=("ALLOW","DENY","ABSTAIN")
S3={
 "P0":(0,1,2), "P1":(0,2,1), "P2":(1,0,2),
 "P3":(1,2,0), "P4":(2,0,1), "P5":(2,1,0),
}
SPLITS={"TRAIN","VALIDATION","HOLDOUT"}
EVAL_FAMILIES={"TRAIN_CORE","VALIDATION_PERM","HOLDOUT_PERM","HOLDOUT_SYMBOL","HOLDOUT_TEMPLATE"}
CODEBOOK_RE=re.compile(r"\[CODEBOOK\](.*?)\[/CODEBOOK\]",re.S)
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")

def _mi_bits(rows):
 pairs=[(r["target_semantic_class"],r["target"]) for r in rows]
 if not pairs:return float("inf")
 n=len(pairs); joint=collections.Counter(pairs); pc=collections.Counter(c for c,_ in pairs); ps=collections.Counter(s for _,s in pairs)
 return sum((k/n)*math.log2((k/n)/((pc[c]/n)*(ps[s]/n))) for (c,s),k in joint.items())

def _strip_codebook(prompt):
 m=CODEBOOK_RE.search(prompt)
 return (None,prompt) if not m else (m.group(1),prompt[:m.start()]+prompt[m.end():])

def validate(rows,forbidden_lexemes):
 global_failures=[]; row_failures=[]; family_split={}; ancestry_split={}
 for i,r in enumerate(rows):
  f=[]
  if r.get("schema")!=ROW_SCHEMA:f.append("ROW_SCHEMA")
  if r.get("split") not in SPLITS:f.append("SPLIT")
  if r.get("eval_family") not in EVAL_FAMILIES:f.append("EVAL_FAMILY")
  if r.get("canonical_truth_allowed") is not False:f.append("CANONICAL_TRUTH_FALSE_REQUIRED")
  if r.get("direct_effect_authority") is not False:f.append("DIRECT_EFFECT_FALSE_REQUIRED")
  if r.get("selected_using_holdout") is not False:f.append("HOLDOUT_SELECTION_FORBIDDEN")
  cls=r.get("target_semantic_class"); atoms=r.get("episode_atom_triplet"); pid=r.get("permutation_id"); perm=S3.get(pid); mapping=r.get("realized_codebook")
  if cls not in CLASSES:f.append("TARGET_CLASS")
  if not isinstance(atoms,list) or len(atoms)!=3 or len(set(map(str,atoms)))!=3:f.append("ATOM_TRIPLET")
  if perm is None:f.append("PERMUTATION_ID")
  if not isinstance(mapping,dict) or set(mapping)!=set(CLASSES):f.append("REALIZED_CODEBOOK")
  elif isinstance(atoms,list) and len(atoms)==3 and perm:
   expected={c:atoms[perm[j]] for j,c in enumerate(CLASSES)}
   if mapping!=expected:f.append("PERMUTATION_NOT_CAUSALLY_REALIZED")
   if cls in CLASSES and r.get("target")!=expected.get(cls):f.append("TARGET_NOT_DERIVED_FROM_MAPPING")
  prompt=r.get("prompt")
  if not isinstance(prompt,str):f.append("PROMPT")
  else:
   codebook,outside=_strip_codebook(prompt)
   if codebook is None:f.append("CODEBOOK_SPAN_REQUIRED")
   elif isinstance(mapping,dict):
    for c in CLASSES:
     if not re.search(rf"\b{c}\b\s*=>\s*{re.escape(str(mapping.get(c,'')))}",codebook):f.append("PROMPT_CODEBOOK_MISMATCH:"+c)
   for lexeme in list(CLASSES)+forbidden_lexemes:
    if lexeme and re.search(rf"\b{re.escape(lexeme)}\b",outside,flags=re.I):f.append("SEMANTIC_LABEL_LEAK:"+lexeme.lower())
  tid=r.get("template_id")
  if not isinstance(tid,str) or not tid:f.append("TEMPLATE_ID")
  elif tid=="T5_FROZEN_UNSEEN" and r.get("eval_family")!="HOLDOUT_TEMPLATE":f.append("FROZEN_TEMPLATE_LEAK")
  for name,value,registry in (("FAMILY",r.get("family_id"),family_split),("ANCESTRY",r.get("provenance_ancestry_id"),ancestry_split)):
   if not isinstance(value,str) or not value:f.append(name+"_ID")
   else:
    split=str(r.get("split")); prior=registry.get(value)
    if prior is not None and prior!=split:f.append(name+"_CROSSES_SPLIT")
    registry[value]=split
  for key in ("abi_manifest_sha256","atom_inventory_sha256","generator_sha256","forbidden_lexeme_inventory_sha256"):
   value=r.get(key)
   if not isinstance(value,str) or not SHA256_RE.fullmatch(value):f.append("PROVENANCE_SHA:"+key)
  if f:row_failures.append({"row":i,"failures":sorted(set(f))})
 train=[r for r in rows if r.get("eval_family")=="TRAIN_CORE" and r.get("target_semantic_class") in CLASSES and isinstance(r.get("target"),str)]
 mi=_mi_bits(train) if train else float("inf")
 per_symbol=collections.defaultdict(collections.Counter)
 for r in train:per_symbol[r["target"]][r["target_semantic_class"]]+=1
 imbalance={s:dict(c) for s,c in per_symbol.items() if max(c.get(k,0) for k in CLASSES)-min(c.get(k,0) for k in CLASSES)>1}
 if imbalance:global_failures.append("TRAIN_CLASS_SYMBOL_COUNTERBALANCE")
 if not math.isfinite(mi) or mi>1e-6:global_failures.append("TRAIN_CLASS_SYMBOL_MI_NONZERO")
 all_perm={r.get("permutation_id") for r in rows}; train_perm={r.get("permutation_id") for r in rows if r.get("eval_family")=="TRAIN_CORE"}; hold_perm={r.get("permutation_id") for r in rows if r.get("eval_family")=="HOLDOUT_PERM"}
 if all_perm!=set(S3):global_failures.append("FULL_S3_CORPUS_COVERAGE_REQUIRED")
 if not hold_perm or train_perm & hold_perm:global_failures.append("UNSEEN_PERM_HOLDOUT_NOT_ISOLATED")
 train_atoms={a for r in rows if r.get("eval_family")=="TRAIN_CORE" for a in r.get("episode_atom_triplet",[]) if isinstance(a,str)}
 hold_atoms={a for r in rows if r.get("eval_family")=="HOLDOUT_SYMBOL" for a in r.get("episode_atom_triplet",[]) if isinstance(a,str)}
 if not hold_atoms or train_atoms & hold_atoms:global_failures.append("UNSEEN_SYMBOL_HOLDOUT_NOT_ISOLATED")
 if any(r.get("template_id")=="T5_FROZEN_UNSEEN" and r.get("split")!="HOLDOUT" for r in rows):global_failures.append("FROZEN_TEMPLATE_VISIBLE_PRE_HOLDOUT")
 return {"schema":SCHEMA,"candidate_binding_gate_pass":not global_failures and not row_failures,"failures":sorted(set(global_failures)),"row_failures":row_failures,"metrics":{"rows":len(rows),"train_rows":len(train),"train_class_symbol_mi_bits":mi,"full_s3_ids":sorted(x for x in all_perm if x),"train_permutation_ids":sorted(x for x in train_perm if x),"holdout_permutation_ids":sorted(x for x in hold_perm if x),"train_symbols":len(train_atoms),"holdout_symbols":len(hold_atoms)},"credits":{"canonical_dataset_write":0,"accepted_dataset_tokens":0,"training_credit":0,"jspace_model_runtime_credit":0},"boundary":"Materialized candidate source validation only; 72-row template matrix is upstream design input, not TRAIN itself."}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("jsonl"); ap.add_argument("--forbidden-lexemes",required=True); ns=ap.parse_args()
 rows=[json.loads(x) for x in Path(ns.jsonl).read_text().splitlines() if x.strip()]; lexemes=json.loads(Path(ns.forbidden_lexemes).read_text())
 if not isinstance(lexemes,list) or not all(isinstance(x,str) for x in lexemes):raise SystemExit("forbidden lexeme file must be a JSON string array")
 result=validate(rows,lexemes); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["candidate_binding_gate_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
