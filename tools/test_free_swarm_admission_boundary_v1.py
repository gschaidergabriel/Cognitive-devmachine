#!/usr/bin/env python3
"""Deterministic no-network regression for FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1."""
from __future__ import annotations
import argparse, asyncio, datetime as dt, json, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import free_swarm_provider_admission as adm
import free_swarm_secret_loader as secrets
import run_free_go_swarm as base
import run_24h_entityos_swarm as driver

COUNTS={"secret_lookup_count":0,"key_lookup_count":0,"network_attempt_count":0}

def doc(path:Path, providers:dict):
    path.write_text(json.dumps({"schema":adm.SCHEMA,"authority":adm.AUTHORITY,"mode":adm.MODE,"admission_id":"TEST_ONLY","generation":1,"source_ref":"deterministic-test-fixture","providers":providers}),encoding="utf-8")

def secret_reader(_path): COUNTS["secret_lookup_count"]+=1; return "GROQ_API_KEY=tripwire"
def key_tripwire(_spec): COUNTS["key_lookup_count"]+=1; return []
def net_tripwire(*_a,**_k): COUNTS["network_attempt_count"]+=1; raise AssertionError("network tripwire fired")

def reset():
    for k in COUNTS: COUNTS[k]=0

def main():
    results=[]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); missing=root/"missing.json"
        cases=[("GLOBAL_ADMISSION_MISSING",missing,None),("PROVIDER_ADMISSION_MISSING",root/"none.json",{}),("UNKNOWN",root/"unknown.json",{"groq":{"cost_class":"UNKNOWN"}}),("PAID",root/"paid.json",{"groq":{"cost_class":"PAID"}}),("SUBSCRIPTION",root/"sub.json",{"groq":{"cost_class":"SUBSCRIPTION"}})]
        for name,path,providers in cases:
            if providers is not None: doc(path,providers)
            reset(); base.collect_keys=key_tripwire; driver.base.collect_keys=key_tripwire; driver.fetch_catalog=net_tripwire
            args=argparse.Namespace(hours=.001,max_tokens=1,context_chars=100,timeout=.01,drain_seconds=.01,output_dir=str(root/"out"),provider_admission_file=str(path))
            rc=asyncio.run(base.run(args))
            try: driver.discover_and_export(.01,str(path))
            except adm.AdmissionError: pass
            try: secrets.load_provider_secret_files(str(path),"groq",[str(root/"secret.env")],read_text=secret_reader)
            except adm.AdmissionError: pass
            passed=(COUNTS=={"secret_lookup_count":0,"key_lookup_count":0,"network_attempt_count":0}) and rc==3
            results.append({"case":name,"pass":passed,**COUNTS,"base_rc":rc})
        free=root/"free.json"; doc(free,{"groq":{"cost_class":"FREE","valid_until":"2999-01-01T00:00:00Z","cost_evidence":{"claim":"TEST_FIXTURE_ONLY"}}})
        reset(); base.collect_keys=key_tripwire; driver.base.collect_keys=key_tripwire; driver.fetch_catalog=net_tripwire
        _doc,report=driver.discover_and_export(.01,str(free))
        positive=(COUNTS["key_lookup_count"]==1 and COUNTS["network_attempt_count"]==0 and report["mistral"]["source"]=="admission_blocked" and report["nvidia"]["source"]=="admission_blocked")
        results.append({"case":"FREE_POSITIVE_CONTROL","pass":positive,**COUNTS})
    receipt={"schema":"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1","scope":"DETERMINISTIC_LOCAL_REGRESSION_NO_PROVIDER_RUNTIME_CREDIT","observed_at":dt.datetime.now(dt.timezone.utc).isoformat(),"results":results,"pass":all(x["pass"] for x in results),"required_negative_invariant":"secret_lookup_count=0,key_lookup_count=0,network_attempt_count=0"}
    print(json.dumps(receipt,indent=2)); return 0 if receipt["pass"] else 1
if __name__=="__main__": raise SystemExit(main())
