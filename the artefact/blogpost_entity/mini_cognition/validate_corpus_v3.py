#!/usr/bin/env python3
"""Validate SFT v3 using the single canonical ClayCode validator plus v3 corpus gates."""
import hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("claycog_core_validator",HERE/"validate_sft_v1.py")
CORE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(CORE)
validate_code=CORE.validate_code
EXPECTED_TRAIN=1773; EXPECTED_VALID=197
REQUIRED={"omega_authority_reject":80,"omega_generation_reject":80,"omega_missing_cfg_reject":80,"recovery_unknown_no_replay":80}

def load(path):
    rows=[]; bad=[]
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        try:
            row=json.loads(line); ms=row["messages"]
            if [m["role"] for m in ms] != ["system","user","assistant"]: raise ValueError("role order")
            errs=validate_code(ms[-1]["content"])
            if errs: bad.append((no,errs))
            rows.append(row)
        except Exception as exc: bad.append((no,["schema:"+repr(exc)]))
    return rows,bad

def canon(x): return json.dumps(x["messages"],ensure_ascii=False,separators=(",",":"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def classify(s):
    if 'omega_reject(w,"authority_denied")' in s:return "omega_authority_reject"
    if 'omega_reject(w,"stale_generation")' in s:return "omega_generation_reject"
    if 'omega_reject(w,"missing_runtime_cfg")' in s:return "omega_missing_cfg_reject"
    if 'recovery_state(c,"UNKNOWN_AFTER_CRASH")' in s and 'focus_set(c,"preserve_unknown_effect_outcome")' in s:return "recovery_unknown_no_replay"
    return None

def late_errors(s,fam):
    e=[]
    if fam and 'omega_commit_candidate(c,w)' in s:e.append("negative_path_commits")
    gates={"omega_authority_reject":("grammar","types","schema","authority"),"omega_generation_reject":("grammar","types","schema","authority","generation")}.get(fam,())
    for g in gates:
        if f'omega_validate(w,"{g}")' not in s:e.append("missing_gate:"+g)
    if fam=="omega_missing_cfg_reject" and 'unknown_preserve(c,' not in s:e.append("missing_cfg_not_unknown")
    if fam=="recovery_unknown_no_replay":
        if 'unknown_preserve(c,"effect_outcome"' not in s:e.append("crash_outcome_not_unknown")
        if 'policy_select(c,"do_not_replay")' not in s:e.append("crash_replay_not_denied")
    return e

def main(trp,vap):
    tr,tbad=load(trp); va,vbad=load(vap); tc=[canon(x) for x in tr]; vc=[canon(x) for x in va]; tp={x["messages"][1]["content"] for x in tr}; vp={x["messages"][1]["content"] for x in va}
    counts=Counter(); late_bad=[]
    for split,rows in (("train",tr),("validation",va)):
        for no,row in enumerate(rows,1):
            code=row["messages"][-1]["content"]; fam=classify(code)
            if fam:
                counts[fam]+=1
                for err in late_errors(code,fam): late_bad.append(f"{split}:{no}:{fam}:{err}")
    wrong={k:{"have":counts[k],"need":v} for k,v in REQUIRED.items() if counts[k]!=v}
    r={"schema":"claycog-corpus-validation/v3","canonical_code_validator":"validate_sft_v1.py","train_lines":len(tr),"validation_lines":len(va),"train_structural_invalid":len(tbad),"validation_structural_invalid":len(vbad),"train_unique":len(set(tc)),"validation_unique":len(set(vc)),"exact_cross_split_overlap":len(set(tc)&set(vc)),"prompt_cross_split_overlap":len(tp&vp),"late_gate_counts":dict(sorted(counts.items())),"late_gate_expected":REQUIRED,"late_gate_wrong":wrong,"late_gate_violations":late_bad,"train_sha256":sha(trp),"validation_sha256":sha(vap)}
    r["ok"]=(len(tr)==EXPECTED_TRAIN and len(va)==EXPECTED_VALID and not tbad and not vbad and len(set(tc))==len(tc) and len(set(vc))==len(vc) and r["exact_cross_split_overlap"]==0 and r["prompt_cross_split_overlap"]==0 and not wrong and not late_bad)
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r["ok"] else 1
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: validate_corpus_v3.py train_v3.jsonl validation_v3.jsonl")
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
