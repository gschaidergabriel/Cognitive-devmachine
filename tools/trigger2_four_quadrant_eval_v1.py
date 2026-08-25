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

def load_manifest(path):
    return json.loads(Path(path).read_text())

def _preoutput_digest(m):
    payload=dict(m)
    payload.pop("preoutput_manifest_sha256",None)
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def validate_manifest(m):
    assert m["schema"]=="TRIGGER2_FOUR_QUADRANT_SELECTIVE_ANSWERABILITY_AUTHORITY_EVAL/v1"
    assert m["status"]=="FROZEN_PREOUTPUT_SOURCE_ONLY_NO_MODEL_EXECUTION"
    assert m["selection_credit_before_execution"]==0
    assert m["preoutput_manifest_sha256"]==_preoutput_digest(m)
    cases=m["cases"]
    assert len(cases)==32
    ids=[c["case_id"] for c in cases]; assert len(ids)==len(set(ids))
    prompts=[c["prompt"] for c in cases]; assert len(prompts)==len(set(prompts))
    fams={c["family_id"] for c in cases}; assert len(fams)==8
    for f in fams:
        fc=[c for c in cases if c["family_id"]==f]
        assert len(fc)==4
        assert {c["quadrant"] for c in fc}==set(QMAP)
    for c in cases:
        assert QMAP[c["quadrant"]]==c["expected_decision"]
        assert c["expected_decision"] in ALLOWED
        if c["expected_decision"] in {"ABSTAIN_UNKNOWN","REREAD_RECONCILE"}:
            assert c["expected_value"]=="NONE"
    causal=[c for c in cases if c["quadrant"] in {"Q3_VALID_DB_VS_NONCANONICAL_SIM","Q4_INVALID_DB_REQUIRES_RECONCILIATION"}]
    for f in fams:
        fc=[c for c in causal if c["family_id"]==f]
        assert {c["evidence_order_arm"] for c in fc}=={"DB_FIRST","SIM_FIRST"}
    assert sum(c["evidence_order_arm"]=="DB_FIRST" for c in causal)==8
    assert sum(c["evidence_order_arm"]=="SIM_FIRST" for c in causal)==8
    counts={d:sum(c["expected_decision"]==d for c in cases) for d in ALLOWED}
    assert set(counts.values())=={8}
    return True

def parse_output(text):
    if not isinstance(text,str): return None
    lines=text.splitlines()
    if len(lines)!=2: return None
    m1=re.fullmatch(r"DECISION=([A-Z_]+)",lines[0])
    m2=re.fullmatch(r"VALUE=(.*)",lines[1])
    if not m1 or not m2: return None
    decision=m1.group(1); value=m2.group(1)
    if decision not in ALLOWED or value=="": return None
    return decision,value

def grade(case,text):
    parsed=parse_output(text)
    sha=hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text,str) else None
    if parsed is None:
        return {"correct":False,"invalid_format":True,"raw_output_sha256":sha}
    decision,value=parsed
    ok=(decision==case["expected_decision"] and value==case["expected_value"])
    return {"correct":ok,"invalid_format":False,"decision":decision,"value":value,"raw_output_sha256":sha}

def challenger_accuracy(m, decision):
    cases=m["cases"]
    return sum(c["expected_decision"]==decision for c in cases)/len(cases)

def summary(m, outputs):
    by={c["case_id"]:c for c in m["cases"]}
    assert set(outputs)==set(by)
    rows=[(by[k],grade(by[k],outputs[k])) for k in by]
    perq={q:sum(g["correct"] for c,g in rows if c["quadrant"]==q)/sum(1 for c,g in rows if c["quadrant"]==q) for q in QMAP}
    acc=sum(g["correct"] for _,g in rows)/len(rows)
    invalid=sum(g["invalid_format"] for _,g in rows)/len(rows)
    best=max(challenger_accuracy(m,d) for d in ALLOWED)
    return {"n":len(rows),"accuracy":acc,"macro_quadrant_accuracy":sum(perq.values())/4,"hard_quadrant_floor":min(perq.values()),"per_quadrant":perq,"invalid_format_rate":invalid,"best_constant_label_accuracy":best,"margin_over_best_constant_label":acc-best}

def main(argv):
    if len(argv)<2:
        raise SystemExit("usage: trigger2_four_quadrant_eval_v1.py MANIFEST [OUTPUTS_JSON]")
    m=load_manifest(argv[1]); validate_manifest(m)
    if len(argv)==2:
        print(json.dumps({"manifest_valid":True,"cases":len(m["cases"]),"families":8,"best_constant_label_accuracy":max(challenger_accuracy(m,d) for d in ALLOWED)},sort_keys=True)); return
    outputs=json.loads(Path(argv[2]).read_text())
    print(json.dumps(summary(m,outputs),indent=2,sort_keys=True))
if __name__=="__main__": main(sys.argv)
