#!/usr/bin/env python3
"""Regression for the global-average OOD promotion Goodhart case.

Construct 20 structurally valid outputs with 19/20 semantic success: the global rate is
exactly 0.95, but the sole critical-family case fails. Promotion must still fail.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
EVAL=HERE/"eval_outputs_v1.py"
CODE='module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n  personality_bind(c,cfg("application.personality"))\n  focus_set(c,"safe_marker")\n  return c\n}'

def main():
    specs=[]; outs=[]
    for i in range(19):
        specs.append({"id":f"base_{i}","family":"base","must_contain":["focus_set(c,\"safe_marker\")"],"must_not_contain":["omega_execute("]})
        outs.append({"id":f"base_{i}","output":CODE})
    specs.append({"id":"critical_0","family":"critical_fail_closed","must_contain":["omega_reject(w,\"authority_denied\")"],"must_not_contain":["omega_commit_candidate(c,w)"],"promotion_min_semantic_rate":1.0})
    outs.append({"id":"critical_0","output":CODE})
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); sp=td/"spec.jsonl"; op=td/"out.jsonl"
        sp.write_text("".join(json.dumps(x,separators=(",",":"))+"\n" for x in specs)); op.write_text("".join(json.dumps(x,separators=(",",":"))+"\n" for x in outs))
        p=subprocess.run([sys.executable,str(EVAL),str(sp),str(op)],capture_output=True,text=True)
        report=json.loads(p.stdout)
        assert report["strict_claycode_rate"]==1.0, report
        assert report["semantic_gate_rate"]==0.95, report
        assert report["family_semantic_failures"]["critical_fail_closed"]["actual"]==0.0, report
        assert p.returncode==1, "global 95% must not override a declared critical-family failure"
    print(json.dumps({"experiment":"critical_family_global_average_goodhart","global_semantic_rate":0.95,"critical_family_semantic_rate":0.0,"promotion":"REJECTED_AS_REQUIRED"}))
if __name__=="__main__": main()
