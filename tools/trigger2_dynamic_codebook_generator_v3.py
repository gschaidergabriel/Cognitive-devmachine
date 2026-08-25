#!/usr/bin/env python3
"""Trigger-2 dynamic codebook binding generator v3.

Factorial successor to rejected v2. It destroys the observed second-order
mapping+template+display-order shortcut by independently crossing every semantic
scenario with every S3 mapping, all six display orders, two query polarities,
and four training templates. Abstract slots are candidate/method material only.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
ROW_SCHEMA="ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
AUDIT_SCHEMA="TRIGGER2_DYNAMIC_CODEBOOK_GENERATOR_AUDIT/v3"
CLASSES=("ALLOW","DENY","ABSTAIN"); SLOTS=("@0","@1","@2")
S3=tuple(itertools.permutations(SLOTS)); ORDERS=tuple(itertools.permutations(CLASSES))
TEMPLATES=("T1","T2","T3","T4"); QUERY_POLARITIES=("Q_POS","Q_NEG")
RESERVED_VALIDATION_TEMPLATE="T5_UNOPENED"; RESERVED_HOLDOUT_TEMPLATE="T6_FROZEN_UNOPENED"
ABI_MANIFEST_SHA256="0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_PACKAGE_SHA256="a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
MEASUREMENT_DONOR_MODEL="Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MEASUREMENT_DONOR_SNAPSHOT="591852bda6e1979f59e4b0f5ee2919697b12e936"
CLASS_WORD_POLICY="CLASS_LABELS_ALLOWED_INSIDE_CODEBOOK_ONLY_V1"
SCENARIOS={
 "SC_PASS":{"semantic_class":"ALLOW","text":"Every mandatory check is satisfied; all required evidence is present; no blocking condition applies."},
 "SC_BLOCK":{"semantic_class":"DENY","text":"A mandatory condition is explicitly violated; the requested transition conflicts with an active hard rule."},
 "SC_OPEN":{"semantic_class":"ABSTAIN","text":"A required observation is missing; the supplied record is insufficient to resolve the decision."},
}
def perm_id(p:tuple[str,...],prefix:str)->str:
 return ("M"+"".join(x[-1] for x in p)) if prefix=="M" else ("O"+"".join(str(CLASSES.index(x)) for x in p))
def codebook(mapping:dict[str,str],order:tuple[str,...])->str:
 return "<CODEBOOK>"+";".join(f"{c}=>{mapping[c]}" for c in order)+"</CODEBOOK>"
def render(template:str,qpol:str,mapping:dict[str,str],order:tuple[str,...],scenario:str)->str:
 cb=codebook(mapping,order)
 q="Return exactly the codebook marker corresponding to the case. Output the marker only." if qpol=="Q_POS" else "Do not emit a marker for any decision contradicted or unsupported by the case. Emit only the marker that remains consistent with the case."
 if template=="T1": return f"{cb}\n<SITUATION>{scenario}</SITUATION>\n<QUERY>{q}</QUERY>"
 if template=="T2": return f"<EPISODE>{cb}\n<OBSERVATION>{scenario}</OBSERVATION>\n<INSTRUCTION>{q}</INSTRUCTION></EPISODE>"
 if template=="T3": return f"{cb}<STATE>{scenario}</STATE><QUERY>{q}</QUERY>"
 if template=="T4": return f"<MAPPING>{cb}</MAPPING>\n<CASE>{scenario}</CASE>\n<OUTPUT_CONTRACT>{q}</OUTPUT_CONTRACT>"
 raise ValueError(template)
def build_rows()->list[dict[str,Any]]:
 rows=[]
 for scenario_id,sc in SCENARIOS.items():
  semantic_class=sc["semantic_class"]
  for mp in S3:
   mapping=dict(zip(CLASSES,mp)); mid=perm_id(mp,"M"); target=mapping[semantic_class]
   for order in ORDERS:
    oid=perm_id(order,"O")
    for qpol in QUERY_POLARITIES:
     for template in TEMPLATES:
      rows.append({"schema":ROW_SCHEMA,"evidence_class":"METHOD_ONLY","reality_level":"R2","family_id":f"BIND_V3_{scenario_id}_F01","provenance_ancestry_id":f"trigger2-v5-binding-v3-{scenario_id.lower()}","canonical_truth_allowed":False,"direct_effect_authority":False,"fact_status":"NOT_APPLICABLE","target_type":"DYNAMIC_CODEBOOK_BINDING_FACTORIAL_V3","split":"TRAIN","split_unit":"CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY","selected_using_holdout":False,"prompt":render(template,qpol,mapping,order,sc["text"]),"target":target,"scenario_id":scenario_id,"semantic_class_metadata_only":semantic_class,"mapping_id":mid,"realized_mapping":mapping,"display_order_id":oid,"codebook_entry_order":list(order),"query_polarity":qpol,"template_id":template,"selected_symbol_slot":target,"class_word_policy":CLASS_WORD_POLICY,"model_input_fields":["prompt"],"model_target_fields":["target"],"metadata_excluded_from_model_input":True,"requires_abi_atom_resolution":True,"candidate_train_ready":False,"abi_manifest_sha256":ABI_MANIFEST_SHA256,"measurement_source_package_sha256":SOURCE_PACKAGE_SHA256,"measurement_donor_model_id":MEASUREMENT_DONOR_MODEL,"measurement_donor_snapshot":MEASUREMENT_DONOR_SNAPSHOT,"jspace_label_transfer_allowed":False})
 return rows
def class_word_leak(prompt:str)->bool:
 start=prompt.find("<CODEBOOK>"); end=prompt.find("</CODEBOOK>")
 if start<0 or end<0 or end<start:return True
 outside=(prompt[:start]+prompt[end+len("</CODEBOOK>"):]).upper(); return any(c in outside for c in CLASSES)
def conditional_mi(rows:list[dict[str,Any]])->float:
 groups=defaultdict(list)
 for r in rows:groups[(r["mapping_id"],r["template_id"],r["query_polarity"])].append(r)
 total=len(rows); out=0.0
 for g in groups.values():
  n=len(g); cc=Counter(r["semantic_class_metadata_only"] for r in g); oo=Counter(r["display_order_id"] for r in g); joint=Counter((r["semantic_class_metadata_only"],r["display_order_id"]) for r in g); mi=0.0
  for (c,o),k in joint.items():
   p=k/n; mi+=p*math.log2(p/((cc[c]/n)*(oo[o]/n)))
  out+=(n/total)*mi
 return out
def nuisance_accuracy(rows:list[dict[str,Any]])->float:
 g=defaultdict(Counter)
 for r in rows:g[(r["mapping_id"],r["template_id"],r["display_order_id"],r["query_polarity"])][r["semantic_class_metadata_only"]]+=1
 return sum(max(x.values()) for x in g.values())/sum(sum(x.values()) for x in g.values())
def validate(rows:list[dict[str,Any]])->dict[str,Any]:
 fail=[]; expected=3*6*6*2*4
 if len(rows)!=expected:fail.append(f"ROW_COUNT_EXPECTED_{expected}_GOT_{len(rows)}")
 if {r["mapping_id"] for r in rows}!={perm_id(p,"M") for p in S3}:fail.append("EXACT_S3_MAPPING_COVERAGE_FAIL")
 if {r["display_order_id"] for r in rows}!={perm_id(o,"O") for o in ORDERS}:fail.append("EXACT_SIX_DISPLAY_ORDER_COVERAGE_FAIL")
 if {r["template_id"] for r in rows}!=set(TEMPLATES):fail.append("FOUR_TEMPLATE_COVERAGE_FAIL")
 if {r["query_polarity"] for r in rows}!=set(QUERY_POLARITIES):fail.append("QUERY_POLARITY_COVERAGE_FAIL")
 cf_order=defaultdict(list)
 for r in rows:cf_order[(r["scenario_id"],r["mapping_id"],r["template_id"],r["query_polarity"])].append(r)
 for k,g in cf_order.items():
  if len(g)!=6 or len({r["display_order_id"] for r in g})!=6:fail.append("COUNTERFACTUAL_DISPLAY_ORDER_SUPPORT_FAIL:"+str(k));break
  if len({r["target"] for r in g})!=1:fail.append("DISPLAY_ORDER_CHANGED_TARGET:"+str(k));break
 cf_map=defaultdict(list)
 for r in rows:cf_map[(r["scenario_id"],r["template_id"],r["query_polarity"],r["display_order_id"])].append(r)
 for k,g in cf_map.items():
  if len(g)!=6 or len({r["mapping_id"] for r in g})!=6:fail.append("COUNTERFACTUAL_MAPPING_SUPPORT_FAIL:"+str(k));break
  if any(r["realized_mapping"][r["semantic_class_metadata_only"]]!=r["target"] for r in g):fail.append("MAPPING_TARGET_MISMATCH:"+str(k));break
 cf_q=defaultdict(list)
 for r in rows:cf_q[(r["scenario_id"],r["mapping_id"],r["template_id"],r["display_order_id"])].append(r)
 for k,g in cf_q.items():
  if len(g)!=2 or {r["query_polarity"] for r in g}!=set(QUERY_POLARITIES):fail.append("QUERY_COUNTERFACTUAL_SUPPORT_FAIL:"+str(k));break
  if len({r["target"] for r in g})!=1:fail.append("QUERY_POLARITY_CHANGED_TARGET:"+str(k));break
 pairs=Counter((r["semantic_class_metadata_only"],r["target"]) for r in rows); n=len(rows); cc=Counter(r["semantic_class_metadata_only"] for r in rows); ss=Counter(r["target"] for r in rows); mi=0.0
 if len(pairs)!=9 or len(set(pairs.values()))!=1:fail.append("CLASS_SYMBOL_COUNTERBALANCE_FAIL")
 for (c,s),k in pairs.items():
  p=k/n; mi+=p*math.log2(p/((cc[c]/n)*(ss[s]/n)))
 if abs(mi)>1e-12:fail.append("CLASS_SYMBOL_MI_NONZERO")
 cmi=conditional_mi(rows); na=nuisance_accuracy(rows)
 if abs(cmi)>1e-12:fail.append("CONDITIONAL_MI_CLASS_ORDER_NONZERO")
 if abs(na-1/3)>1e-12:fail.append("NUISANCE_ONLY_DECODER_ABOVE_CHANCE")
 for i,r in enumerate(rows):
  if class_word_leak(r["prompt"]):fail.append(f"ROW_{i}:CLASS_WORD_LEAK_OUTSIDE_CODEBOOK");break
  if r["canonical_truth_allowed"] is not False or r["direct_effect_authority"] is not False:fail.append(f"ROW_{i}:AUTHORITY_FAIL");break
  if r["candidate_train_ready"] is not False or r["requires_abi_atom_resolution"] is not True:fail.append(f"ROW_{i}:ABI_FAIL_CLOSED_GUARD");break
  if r["metadata_excluded_from_model_input"] is not True or r["model_input_fields"]!=["prompt"] or r["model_target_fields"]!=["target"]:fail.append(f"ROW_{i}:TRAINING_FIELD_BOUNDARY_FAIL");break
 return {"schema":AUDIT_SCHEMA,"pass":not fail,"failures":sorted(set(fail)),"rows":len(rows),"factorization":{"scenarios":3,"s3_mappings":6,"display_orders":6,"query_polarities":2,"templates":4},"conditional_mi_semantic_class_display_order_given_mapping_template_query_bits":cmi,"nuisance_only_decoder_accuracy_mapping_template_order_query":na,"nuisance_only_decoder_chance":1/3,"class_symbol_mutual_information_bits":mi,"counterfactual_display_order_cells":len(cf_order),"counterfactual_mapping_cells":len(cf_map),"counterfactual_query_cells":len(cf_q),"reserved_validation_template":RESERVED_VALIDATION_TEMPLATE,"reserved_holdout_template":RESERVED_HOLDOUT_TEMPLATE,"candidate_train_ready":False,"abi_materialization_required":True,"accepted_dataset_tokens_minted":0,"training_credit_minted":False,"jspace_model_runtime_credit_minted":False,"whole_hcu_runtime_credit_minted":False,"whole_entityos_runtime_credit_minted":False}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--jsonl",type=Path);ap.add_argument("--audit",type=Path);args=ap.parse_args();rows=build_rows();audit=validate(rows)
 if args.jsonl:args.jsonl.write_text("".join(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8");audit["jsonl_sha256"]=hashlib.sha256(args.jsonl.read_bytes()).hexdigest()
 if args.audit:args.audit.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(audit,indent=2,sort_keys=True));return 0 if audit["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
