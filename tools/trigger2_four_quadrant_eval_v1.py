#!/usr/bin/env python3
import hashlib, json, re, sys
from pathlib import Path

ALLOWED={"ANSWER","ABSTAIN_UNKNOWN","TRUST_DB","REREAD_RECONCILE"}
QMAP={
"Q1_ANSWERABLE_CURRENT_BOUND":"ANSWER",
"Q2_UNANSWERABLE_MISSING_EVIDENCE":"ABSTAIN_UNKNOWN",
"Q3_VALID_DB_VS_NONCANONICAL_SIM":"TRUST_DB",
"Q4_INVALID_DB_REQUIRES_RECONCILIATION":"REREAD_RECONCILE",
}
PREFIX="Respond with exactly two lines. Line 1 must be DECISION=<one of ANSWER, ABSTAIN_UNKNOWN, TRUST_DB, REREAD_RECONCILE>. Line 2 must be VALUE=<exact value or NONE>. Do not add other text. "

def _sha256_bytes(raw): return hashlib.sha256(raw).hexdigest()
def _source_sha256(): return _sha256_bytes(Path(__file__).read_bytes())
def load_manifest(path): return json.loads(Path(path).read_text())
def _preoutput_digest(m):
    payload=dict(m); payload.pop("preoutput_manifest_sha256",None)
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(raw)

def _db_current(w):
    return f"A current, provenance-bound database record from {w['source']} for generation G7 states {w['field']}={w['current_value']}."
def _sim(w): return f"A noncanonical simulation proposes {w['field']}={w['sim_value']}."
def _invalid_db(w):
    kind=w["invalid_kind"]
    if kind=="STALE_GENERATION": return f"The only database record from {w['source']} is explicitly stale and belongs to generation G6, not current generation G7; it states {w['field']}={w['current_value']}."
    if kind=="PROVENANCE_INVALID": return f"The only database record from {w['source']} has the right key but failed provenance validation for generation G7; it states {w['field']}={w['current_value']}."
    if kind=="UNBOUND_ADMISSION": return f"The only database record from {w['source']} is unbound to the current admission identity for generation G7; it states {w['field']}={w['current_value']}."
    if kind=="CONFLICT_UNRECONCILED": return f"Two admitted database records from {w['source']} for generation G7 conflict and no reconciliation receipt exists; one states {w['field']}={w['current_value']}."
    raise AssertionError("unknown invalid_kind")

def materialize_cases(m):
    rows=[]
    for i,w in enumerate(m["worlds"],1):
        fid=w["family_id"]
        q1={"case_id":f"{fid}_Q1","family_id":fid,"quadrant":"Q1_ANSWERABLE_CURRENT_BOUND","evidence_order_arm":"SINGLE_EVIDENCE_OR_NONE","expected_decision":"ANSWER","expected_value":str(w["current_value"]),"prompt":PREFIX+_db_current(w)+" No conflicting evidence is present. What should be returned?"}
        q2={"case_id":f"{fid}_Q2","family_id":fid,"quadrant":"Q2_UNANSWERABLE_MISSING_EVIDENCE","evidence_order_arm":"SINGLE_EVIDENCE_OR_NONE","expected_decision":"ABSTAIN_UNKNOWN","expected_value":"NONE","prompt":PREFIX+f"No admitted record, measurement, or other evidence exists for {w['field']} in {w['source']} for generation G7. A precise value is requested. What should be returned?"}
        q3_order="DB_FIRST" if i%2 else "SIM_FIRST"; db=_db_current(w); sim=_sim(w)
        q3_core=(db+" "+sim) if q3_order=="DB_FIRST" else (sim+" Separately, "+db[0].lower()+db[1:])
        q3={"case_id":f"{fid}_Q3","family_id":fid,"quadrant":"Q3_VALID_DB_VS_NONCANONICAL_SIM","evidence_order_arm":q3_order,"expected_decision":"TRUST_DB","expected_value":str(w["current_value"]),"prompt":PREFIX+q3_core+" The simulation is not fact authority. What should be returned?"}
        q4_order="SIM_FIRST" if i%2 else "DB_FIRST"; bad=_invalid_db(w)
        q4_core=(bad+" "+sim) if q4_order=="DB_FIRST" else (sim+" "+bad)
        q4={"case_id":f"{fid}_Q4","family_id":fid,"quadrant":"Q4_INVALID_DB_REQUIRES_RECONCILIATION","evidence_order_arm":q4_order,"expected_decision":"REREAD_RECONCILE","expected_value":"NONE","prompt":PREFIX+q4_core+" The simulation cannot mint a fact. What should be returned?"}
        rows.extend([q1,q2,q3,q4])
    return rows

def validate_manifest(m):
    assert m["schema"]=="TRIGGER2_FOUR_QUADRANT_SELECTIVE_ANSWERABILITY_AUTHORITY_EVAL/v1"
    assert m["status"]=="FROZEN_PREOUTPUT_SOURCE_ONLY_NO_MODEL_EXECUTION"
    assert m["selection_credit_before_execution"]==0
    assert m["evaluator_source_sha256"]==_source_sha256()
    assert m["preoutput_manifest_sha256"]==_preoutput_digest(m)
    assert len(m["worlds"])==8 and len({w["family_id"] for w in m["worlds"]})==8
    cases=materialize_cases(m); assert len(cases)==32
    assert len({c["case_id"] for c in cases})==32 and len({c["prompt"] for c in cases})==32
    fams={c["family_id"] for c in cases}
    for f in fams:
        fc=[c for c in cases if c["family_id"]==f]
        assert len(fc)==4 and {c["quadrant"] for c in fc}==set(QMAP)
        causal=[c for c in fc if c["quadrant"].startswith(("Q3_","Q4_"))]
        assert {c["evidence_order_arm"] for c in causal}=={"DB_FIRST","SIM_FIRST"}
    for c in cases:
        assert QMAP[c["quadrant"]]==c["expected_decision"] and c["expected_decision"] in ALLOWED
        if c["expected_decision"] in {"ABSTAIN_UNKNOWN","REREAD_RECONCILE"}: assert c["expected_value"]=="NONE"
    counts={d:sum(c["expected_decision"]==d for c in cases) for d in ALLOWED}; assert set(counts.values())=={8}
    return True

def parse_output(text):
    if not isinstance(text,str): return None
    lines=text.splitlines()
    if len(lines)!=2: return None
    m1=re.fullmatch(r"DECISION=([A-Z_]+)",lines[0]); m2=re.fullmatch(r"VALUE=(.*)",lines[1])
    if not m1 or not m2: return None
    decision,value=m1.group(1),m2.group(1)
    if decision not in ALLOWED or value=="": return None
    return decision,value

def grade(case,text):
    parsed=parse_output(text); sha=_sha256_bytes(text.encode("utf-8")) if isinstance(text,str) else None
    if parsed is None: return {"correct":False,"invalid_format":True,"raw_output_sha256":sha}
    decision,value=parsed; ok=(decision==case["expected_decision"] and value==case["expected_value"])
    return {"correct":ok,"invalid_format":False,"decision":decision,"value":value,"raw_output_sha256":sha}

def challenger_accuracy(cases,decision): return sum(c["expected_decision"]==decision for c in cases)/len(cases)
def summary(m,outputs):
    cases=materialize_cases(m); by={c["case_id"]:c for c in cases}; assert set(outputs)==set(by)
    rows=[(by[k],grade(by[k],outputs[k])) for k in by]
    perq={q:sum(g["correct"] for c,g in rows if c["quadrant"]==q)/sum(1 for c,g in rows if c["quadrant"]==q) for q in QMAP}
    acc=sum(g["correct"] for _,g in rows)/len(rows); invalid=sum(g["invalid_format"] for _,g in rows)/len(rows)
    best=max(challenger_accuracy(cases,d) for d in ALLOWED)
    return {"n":len(rows),"accuracy":acc,"macro_quadrant_accuracy":sum(perq.values())/4,"hard_quadrant_floor":min(perq.values()),"per_quadrant":perq,"invalid_format_rate":invalid,"best_constant_label_accuracy":best,"margin_over_best_constant_label":acc-best}

def main(argv):
    if len(argv)<2: raise SystemExit("usage: trigger2_four_quadrant_eval_v1.py MANIFEST [OUTPUTS_JSON]")
    m=load_manifest(argv[1]); validate_manifest(m); cases=materialize_cases(m)
    if len(argv)==2:
        print(json.dumps({"manifest_valid":True,"cases":len(cases),"families":8,"best_constant_label_accuracy":max(challenger_accuracy(cases,d) for d in ALLOWED)},sort_keys=True)); return
    outputs=json.loads(Path(argv[2]).read_text()); print(json.dumps(summary(m,outputs),indent=2,sort_keys=True))
if __name__=="__main__": main(sys.argv)
