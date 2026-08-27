#!/usr/bin/env python3
"""Execute the hard native structural-label-free Qwen3-0.6B J-Space discriminator."""
from __future__ import annotations
import argparse, hashlib, json, math, os, subprocess, sys
from pathlib import Path
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools import trigger1_structural_label_free_cases as structural
from tools import trigger1_nuisance_residualize as residualizer
SCHEMA="CLAY_TRIGGER1_STRUCTURAL_NATIVE_ABSTRACT_RUNTIME/v1"
N_EMBD=1024; N_LAYER=28; INJECTION_LAYER=20; PRIMARY_LAYER_INP=21; DOWNSTREAM_LAYER_INP=24
CLASSES=("AFFIRMATIVE","NEGATIVE","NEUTRAL"); CODES=("A","B","C"); GAIN_GRID=(4.0,8.0,16.0,24.0,32.0)
EXPECTED_GGUF_SHA256="9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
EXPECTED_LLAMA_CPP="bb4caa7540188872173c44d161602d9271386413"
NUISANCE_PROMPTS={
"CANONICAL_LABEL_LEXEME":("/no_think\nAFFIRMATIVE","/no_think\nNEGATIVE","/no_think\nNEUTRAL"),
"SEMANTIC_SYNONYM_LEXICON":("/no_think\napprove support grant accept","/no_think\nreject oppose refuse decline","/no_think\ndefer undecided withhold pending"),
"GENERIC_INSTRUCTION_COMPLIANCE":("/no_think\nFollow every instruction exactly.","/no_think\nIgnore the instruction and do something else.","/no_think\nThere is no requested action to perform."),
"OUTPUT_CODE_IDENTITY":("/no_think\nA","/no_think\nB","/no_think\nC")}
def cbytes(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def csha(v): return hashlib.sha256(cbytes(v)).hexdigest()
def sha_file(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
 return h.hexdigest()
def unit(v,name):
 v=np.asarray(v,dtype=np.float64); n=float(np.linalg.norm(v))
 if not math.isfinite(n) or n<=1e-12: raise RuntimeError(f"DEGENERATE_VECTOR:{name}")
 return v/n
def write_json(p,v): p.write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def run(cmd,timeout=1800,env=None):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,env=env,check=False)
 if p.returncode!=0: raise RuntimeError(f"COMMAND_FAILED:{p.returncode}:{cmd[0]}:{p.stderr[-2000:]}")
 return p
def parse_jsonl(text,schema):
 rows=[json.loads(x) for x in text.splitlines() if x.strip()]
 if not rows: raise RuntimeError("EMPTY_JSONL")
 out={}
 for r in rows[1:]:
  if r.get("schema")!=schema: raise RuntimeError(f"UNEXPECTED_ROW_SCHEMA:{r.get('schema')}")
  cid=str(r.get("case_id") or "")
  if not cid or cid in out: raise RuntimeError(f"INVALID_OR_DUPLICATE_CASE_ID:{cid}")
  out[cid]=r
 return rows[0],out
def run_capture(harness,gguf,out,cases,tag,env):
 tsv=out/f"{tag}.capture.tsv"; lines=[]
 for r in cases:
  lines.append("\t".join([str(r["case_id"]),str(r.get("cvec_path") or "-"),str(INJECTION_LAYER),str(INJECTION_LAYER),str(PRIMARY_LAYER_INP),str(DOWNSTREAM_LAYER_INP),str(r["prompt"]).encode().hex()]))
 tsv.write_text("\n".join(lines)+"\n")
 p=run([str(harness),str(gguf),str(tsv),str(N_EMBD),str(N_LAYER)],3600,env)
 (out/f"{tag}.capture.stdout.jsonl").write_text(p.stdout); (out/f"{tag}.capture.stderr.txt").write_text(p.stderr)
 return parse_jsonl(p.stdout,"CLAY_LLAMA_CPP_LAYER_CAPTURE_OBSERVATION/v1")
def run_logits(harness,gguf,out,cases,tag,env):
 tsv=out/f"{tag}.logits.tsv"; lines=[]
 for r in cases:
  lines.append("\t".join([str(r["case_id"]),str(r.get("cvec_path") or "-"),str(INJECTION_LAYER),str(INJECTION_LAYER),str(r["prompt"]).encode().hex()]))
 tsv.write_text("\n".join(lines)+"\n")
 p=run([str(harness),str(gguf),str(tsv),str(N_EMBD),str(N_LAYER)],3600,env)
 (out/f"{tag}.logits.stdout.jsonl").write_text(p.stdout); (out/f"{tag}.logits.stderr.txt").write_text(p.stderr)
 return parse_jsonl(p.stdout,"CLAY_LLAMA_CPP_CVEC_LOGIT_OBSERVATION/v1")
def cvec_bytes(v):
 v=np.asarray(v,dtype="<f4")
 if v.shape!=(N_EMBD,): raise RuntimeError(f"CVEC_VECTOR_DIMENSION:{v.shape}")
 z=np.zeros(N_EMBD,dtype="<f4").tobytes(); d=v.tobytes(); raw=b"".join(d if il==INJECTION_LAYER else z for il in range(1,N_LAYER))
 if len(raw)!=(N_LAYER-1)*N_EMBD*4: raise RuntimeError("CVEC_BYTES_INVARIANT")
 return raw
def write_cvec(out,name,v):
 p=out/f"{name}.cvec.f32le"; raw=cvec_bytes(v); p.write_bytes(raw)
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"vector_sha256":hashlib.sha256(np.asarray(v,dtype="<f4").tobytes()).hexdigest(),"l2":float(np.linalg.norm(v))}
def grouped_semantic(cases,obs,field):
 rows={c:[] for c in CLASSES}
 for case in cases: rows[case["semantic_target"]].append(np.asarray(obs[case["case_id"]][field],dtype=np.float64))
 return {c:np.mean(np.stack(rows[c]),axis=0) for c in CLASSES}
def grouped_nuisance(ids,obs,field):
 out={}
 for fam,cids in ids.items():
  arr=[np.asarray(obs[c][field],dtype=np.float64) for c in cids]; g=np.mean(np.stack(arr),axis=0); out[fam]=[x-g for x in arr]
 return out
def residualized(semantic,nuisance,sreceipt,nreceipt):
 return residualizer.residualize({"schema":residualizer.INPUT_SCHEMA,"fit_split":"CALIBRATION","frozen_before_holdout":True,"dimension":N_EMBD,"semantic_source_receipt_sha256":sreceipt,"nuisance_source_receipt_sha256":nreceipt,"semantic_vectors":{k:v.tolist() for k,v in semantic.items()},"nuisance_vectors":{k:[v.tolist() for v in vs] for k,vs in nuisance.items()}})
def margin(row,code):
 l=row["token_logits"]; o=[c for c in CODES if c!=code]; return float(l[code])-0.5*(float(l[o[0]])+float(l[o[1]]))
def argmax_code(row): return max(CODES,key=lambda c:float(row["token_logits"][c]))
def orthogonal(v):
 v=unit(v,"ORTH_IN"); x=np.roll(v,173); x=x-float(np.dot(x,v))*v
 if float(np.linalg.norm(x))<=1e-8:
  x=np.arange(v.size,dtype=np.float64); x=x-x.mean(); x=x-float(np.dot(x,v))*v
 return unit(x,"ORTH_OUT")
def causal_matrix(hold,rows,base):
 m={i:{j:[] for j in CLASSES} for i in CLASSES}
 for c in hold:
  cid=c["case_id"]; target=c["semantic_target"]; code=c["output_code_identity"]
  for i in CLASSES: m[i][target].append(margin(rows[f"h:{cid}:sem:{i}"],code)-base[cid])
 means={i:{j:float(np.mean(m[i][j])) for j in CLASSES} for i in CLASSES}; diag=[means[c][c] for c in CLASSES]; off=[means[i][j] for i in CLASSES for j in CLASSES if i!=j]
 return {"mean_delta_matrix_intervention_x_requested_target":means,"diagonal_mean":float(np.mean(diag)),"off_diagonal_mean":float(np.mean(off)),"diagonal_advantage":float(np.mean(diag)-np.mean(off)),"diagonal_each_positive":all(x>0 for x in diag)}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",required=True); ap.add_argument("--llama-root",required=True); ap.add_argument("--gguf",required=True); ap.add_argument("--capture-harness",required=True); ap.add_argument("--logits-harness",required=True); ap.add_argument("--source-head",default=""); a=ap.parse_args()
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); llama=Path(a.llama_root); gguf=Path(a.gguf); caph=Path(a.capture_harness); logh=Path(a.logits_harness); result_path=out/"trigger1_structural_native_abstract_result.json"
 env=dict(os.environ); lib=str(llama/"build"/"bin"); env["LD_LIBRARY_PATH"]=lib+(":"+env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
 try:
  if sha_file(gguf)!=EXPECTED_GGUF_SHA256: raise RuntimeError("GGUF_SHA256_MISMATCH")
  got_llama=run(["git","-C",str(llama),"rev-parse","HEAD"],30).stdout.strip()
  if got_llama!=EXPECTED_LLAMA_CPP: raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{got_llama}")
  bundle=structural.build_bundle(); write_json(out/"structural_case_bundle.json",bundle); cal=bundle["calibration"]["cases"]; hold=bundle["holdout"]["cases"]
  cc=[{"case_id":c["case_id"],"prompt":c["prompt"],"cvec_path":"-"} for c in cal]; nids={}
  for fam,prompts in NUISANCE_PROMPTS.items():
   nids[fam]=[]
   for i,prompt in enumerate(prompts):
    cid=f"nuis:{fam}:{i}"; nids[fam].append(cid); cc.append({"case_id":cid,"prompt":prompt,"cvec_path":"-"})
  cap_header,obs=run_capture(caph,gguf,out,cc,"calibration",env)
  s21=grouped_semantic(cal,obs,"primary_activation"); s24=grouped_semantic(cal,obs,"downstream_activation"); n21=grouped_nuisance(nids,obs,"primary_activation"); n24=grouped_nuisance(nids,obs,"downstream_activation")
  r21=residualized(s21,n21,csha({k:v.tolist() for k,v in s21.items()}),csha({k:[v.tolist() for v in vs] for k,vs in n21.items()})); r24=residualized(s24,n24,csha({k:v.tolist() for k,v in s24.items()}),csha({k:[v.tolist() for v in vs] for k,vs in n24.items()})); write_json(out/"residualized_layer21.json",r21); write_json(out/"residualized_layer24.json",r24)
  v21={c:np.asarray(r21["projected_semantic_unit_vectors"][c],dtype=np.float64) for c in CLASSES}; v24={c:np.asarray(r24["projected_semantic_unit_vectors"][c],dtype=np.float64) for c in CLASSES}
  ns=np.stack([unit(v,f"NUIS_{k}") for k,vs in n21.items() for v in vs]); _,_,vh=np.linalg.svd(ns,full_matrices=False); naxis=unit(vh[0],"NUIS_PC1")
  gain_cases=[{"case_id":f"cal:{c['case_id']}:base","prompt":c["prompt"],"cvec_path":"-"} for c in cal]; grec={}
  for g in GAIN_GRID:
   k=str(int(g)); grec[k]={c:write_cvec(out,f"cal-g{k}-{c.lower()}",v21[c]*g) for c in CLASSES}
   for c in cal: gain_cases.append({"case_id":f"cal:{c['case_id']}:g{k}","prompt":c["prompt"],"cvec_path":grec[k][c["semantic_target"]]["path"]})
  lhc,clog=run_logits(logh,gguf,out,gain_cases,"gain_calibration",env); bcal={c["case_id"]:margin(clog[f"cal:{c['case_id']}:base"],c["output_code_identity"]) for c in cal}; gs={}
  for g in GAIN_GRID:
   k=str(int(g)); ds=[]; hits=[]
   for c in cal:
    row=clog[f"cal:{c['case_id']}:g{k}"]; ds.append(margin(row,c["output_code_identity"])-bcal[c["case_id"]]); hits.append(1.0 if argmax_code(row)==c["output_code_identity"] else 0.0)
   gs[k]={"mean_delta_vs_baseline":float(np.mean(ds)),"median_delta_vs_baseline":float(np.median(ds)),"target_code_hit_rate":float(np.mean(hits))}
  sgk=max(gs,key=lambda k:(gs[k]["mean_delta_vs_baseline"],gs[k]["target_code_hit_rate"])); gain=float(sgk)
  cv={"semantic":{},"signflip":{},"orthogonal":{},"permuted":{}}
  for c in CLASSES:
   v=v21[c]; cv["semantic"][c]=write_cvec(out,f"holdout-sem-{c.lower()}",v*gain); cv["signflip"][c]=write_cvec(out,f"holdout-sign-{c.lower()}",-v*gain); cv["orthogonal"][c]=write_cvec(out,f"holdout-orth-{c.lower()}",orthogonal(v)*gain); cv["permuted"][c]=write_cvec(out,f"holdout-perm-{c.lower()}",unit(np.roll(v,257),f"PERM_{c}")*gain)
  cv["null"]=write_cvec(out,"holdout-null",np.zeros(N_EMBD)); cv["nuisance"]=write_cvec(out,"holdout-nuisance",naxis*gain); hcases=[]
  for c in hold:
   cid=c["case_id"]; hcases.append({"case_id":f"h:{cid}:base","prompt":c["prompt"],"cvec_path":"-"})
   for cls in CLASSES: hcases.append({"case_id":f"h:{cid}:sem:{cls}","prompt":c["prompt"],"cvec_path":cv["semantic"][cls]["path"]})
   t=c["semantic_target"]
   for ctrl,path in (("sign",cv["signflip"][t]["path"]),("null",cv["null"]["path"]),("orth",cv["orthogonal"][t]["path"]),("perm",cv["permuted"][t]["path"]),("nuis",cv["nuisance"]["path"])): hcases.append({"case_id":f"h:{cid}:{ctrl}","prompt":c["prompt"],"cvec_path":path})
  lhh,hlog=run_logits(logh,gguf,out,hcases,"holdout",env); hch,hcap=run_capture(caph,gguf,out,hcases,"holdout",env); base={c["case_id"]:margin(hlog[f"h:{c['case_id']}:base"],c["output_code_identity"]) for c in hold}; matrix=causal_matrix(hold,hlog,base)
  md=[]; sd=[]; nd=[]; od=[]; pd=[]; ud=[]; bh=[]; mh=[]; tt=[]; to=[]; ts=[]; tc=[]
  for c in hold:
   cid=c["case_id"]; t=c["semantic_target"]; code=c["output_code_identity"]; bm=base[cid]; matched=hlog[f"h:{cid}:sem:{t}"]
   vals={x:hlog[f"h:{cid}:{x}"] for x in ("sign","null","orth","perm","nuis")}; md.append(margin(matched,code)-bm); sd.append(margin(vals["sign"],code)-bm); nd.append(margin(vals["null"],code)-bm); od.append(margin(vals["orth"],code)-bm); pd.append(margin(vals["perm"],code)-bm); ud.append(margin(vals["nuis"],code)-bm); bh.append(1.0 if argmax_code(hlog[f"h:{cid}:base"])==code else 0.0); mh.append(1.0 if argmax_code(matched)==code else 0.0)
   ba=np.asarray(hcap[f"h:{cid}:base"]["downstream_activation"],dtype=np.float64); ma=np.asarray(hcap[f"h:{cid}:sem:{t}"]["downstream_activation"],dtype=np.float64); sa=np.asarray(hcap[f"h:{cid}:sign"]["downstream_activation"],dtype=np.float64); d=ma-ba; tt.append(float(np.dot(d,v24[t]))); to.extend(abs(float(np.dot(d,v24[o]))) for o in CLASSES if o!=t); ts.append(float(np.dot(sa-ba,v24[t]))); tc.extend(abs(float(np.dot(np.asarray(hcap[f"h:{cid}:{ctrl}"]["downstream_activation"],dtype=np.float64)-ba,v24[t]))) for ctrl in ("null","orth","perm","nuis"))
  beh={"matched_mean_delta":float(np.mean(md)),"matched_median_delta":float(np.median(md)),"signflip_mean_delta":float(np.mean(sd)),"null_mean_abs_delta":float(np.mean(np.abs(nd))),"orthogonal_mean_abs_delta":float(np.mean(np.abs(od))),"permuted_mean_abs_delta":float(np.mean(np.abs(pd))),"nuisance_mean_abs_delta":float(np.mean(np.abs(ud))),"baseline_hit_rate":float(np.mean(bh)),"matched_hit_rate":float(np.mean(mh))}; trans={"matched_target_coordinate_mean":float(np.mean(tt)),"matched_target_coordinate_median":float(np.median(tt)),"matched_offaxis_abs_mean":float(np.mean(to)),"signflip_target_coordinate_mean":float(np.mean(ts)),"control_target_coordinate_abs_mean":float(np.mean(tc))}
  maxc=max(beh["null_mean_abs_delta"],beh["orthogonal_mean_abs_delta"],beh["permuted_mean_abs_delta"],beh["nuisance_mean_abs_delta"]); bp=beh["matched_mean_delta"]>0 and matrix["diagonal_advantage"]>0 and beh["matched_mean_delta"]>maxc and beh["signflip_mean_delta"]<beh["matched_mean_delta"]; tp=trans["matched_target_coordinate_mean"]>0 and trans["matched_target_coordinate_mean"]>trans["matched_offaxis_abs_mean"] and trans["matched_target_coordinate_mean"]>trans["control_target_coordinate_abs_mean"] and trans["signflip_target_coordinate_mean"]<trans["matched_target_coordinate_mean"]; passed=bool(bp and tp)
  core={"schema":SCHEMA,"status":"PASS_ABSTRACT_NATIVE_DISCRIMINATOR" if passed else "FAIL_ABSTRACT_NATIVE_DISCRIMINATOR","source_head":a.source_head,"model":"Qwen/Qwen3-0.6B-GGUF:Q8_0","gguf_sha256":sha_file(gguf),"llama_cpp_commit":got_llama,"native_api":"llama_set_adapter_cvec","native_token_scope":"ALL_PROMPT_TOKENS","injection_layer":INJECTION_LAYER,"primary_layer_input":PRIMARY_LAYER_INP,"downstream_layer_input":DOWNSTREAM_LAYER_INP,"case_bundle_sha256":bundle["bundle_sha256"],"lexical_disjointness":bundle["lexical_disjointness_audit"],"calibration_case_count":len(cal),"holdout_case_count":len(hold),"nuisance_families":list(NUISANCE_PROMPTS),"layer21_residualizer":{"result_sha256":r21["result_sha256"],"nuisance_subspace_rank":r21["nuisance_subspace_rank"],"post_projection_max_abs_nuisance_cosine":r21["post_projection_max_abs_nuisance_cosine"],"retained_semantic_subspace_norm_fraction":r21["retained_semantic_subspace_norm_fraction"],"projected_semantic_vector_sha256":r21["projected_semantic_vector_sha256"]},"layer24_downstream_estimator":{"result_sha256":r24["result_sha256"],"nuisance_subspace_rank":r24["nuisance_subspace_rank"],"post_projection_max_abs_nuisance_cosine":r24["post_projection_max_abs_nuisance_cosine"],"retained_semantic_subspace_norm_fraction":r24["retained_semantic_subspace_norm_fraction"]},"gain_grid":list(GAIN_GRID),"gain_scores":gs,"selected_gain_calibration_only":gain,"behavior":beh,"behavioral_causal_matrix":matrix,"downstream_transport":trans,"behavior_pass":bp,"downstream_transport_pass":tp,"abstract_native_discriminator_pass":passed,"direct_native_scope_evidence":True,"legacy_last_token_witness_used_as_causal_identity_premise":False,"cross_scope_mechanistic_identity_claimed":False,"holdout_opened_only_after_calibration_residualizer_and_gain_frozen":True,"external_provider_used":False,"canonical_credit_minted":False,"canonical_semantics_promotion":False,"jspace_model_runtime_credit":0,"whole_hcu_credit":0,"whole_entityos_hcu_credit":0,"training_credit":0,"evidence_boundary":"Direct native ALL_PROMPT_TOKENS cvec on structural label-free lexically-disjoint holdout after calibration-only nuisance residualization and gain selection. PASS is strong component evidence only; FAIL is preserved as falsifying evidence.","headers":{"calibration_capture":cap_header,"calibration_logits":lhc,"holdout_logits":lhh,"holdout_capture":hch},"cvec_receipts":cv}; result={**core,"result_sha256":csha(core)}; write_json(result_path,result); print(json.dumps({"status":result["status"],"result_sha256":result["result_sha256"]},sort_keys=True)); return 0
 except Exception as e:
  fail={"schema":SCHEMA,"status":"BLOCKED_OR_FAILED","source_head":a.source_head,"error":f"{type(e).__name__}:{e}","external_provider_used":False,"canonical_credit_minted":False,"jspace_model_runtime_credit":0}; write_json(result_path,fail); print(json.dumps(fail,sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
