#!/usr/bin/env python3
"""FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 deterministic verifier.

The capsule performs no real provider I/O. It uses temporary canonical admission
objects plus secret/socket tripwires to verify the current source checkout.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import free_provider_admission_gate as gate
import run_free_go_swarm as base
import run_24h_entityos_swarm as driver

ROOT=Path(__file__).resolve().parents[1]
SUPERVISOR=ROOT/"research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
SUPERVISOR_SH=ROOT/"tools/run_24h_entityos_swarm_supervisor.sh"
DISTILLERY_ENTRY=ROOT/"tools/run_research_distillery_entry.py"
FILES=[ROOT/"tools/free_provider_admission_gate.py",ROOT/"tools/run_free_go_swarm.py",ROOT/"tools/run_24h_entityos_swarm.py",SUPERVISOR_SH,DISTILLERY_ENTRY]


def admission(cost="UNKNOWN",admitted=False,epoch="8.67",include=True,schema=gate.EXPECTED_SCHEMA,evidence="TEST"):
    providers={}
    if include: providers["groq"]={"admitted":admitted,"cost_class":cost,"evidence_ref":evidence}
    return {"schema":schema,"authority_epoch":epoch,"mode":"FREE_ONLY","product":"EntityOS","compute_architecture":"HCU","providers":providers}


def supervisor(epoch="8.67"):
    return {"schema_version":epoch}


def write_pair(root:Path,a:dict,s:dict):
    ap=root/"FREE_PROVIDER_ADMISSION.json";sp=root/"SUPERVISOR_INBOX.json"
    ap.write_text(json.dumps(a),encoding="utf-8");sp.write_text(json.dumps(s),encoding="utf-8");return ap,sp


def negative_case(name,a,s):
    with tempfile.TemporaryDirectory() as td:
        ap,sp=write_pair(Path(td),a,s)
        decision=gate.resolve("groq",ap,sp)
        assert not decision.allowed,(name,dataclasses.asdict(decision))
        old_resolver=base.resolve_provider_admission;old_urlopen=base.urllib.request.urlopen;old_getenv=base.os.getenv
        counts={"secret_lookup_count":0,"network_attempt_count":0}
        def resolver(provider): return gate.resolve(provider,ap,sp)
        def poison_getenv(key,default=None):
            if key.startswith(("GROQ","MISTRAL","NVIDIA","NGC")) and ("KEY" in key):
                counts["secret_lookup_count"]+=1;raise AssertionError("secret lookup before admission")
            return old_getenv(key,default)
        def poison_urlopen(*args,**kwargs):
            counts["network_attempt_count"]+=1;raise AssertionError("network before admission")
        try:
            base.resolve_provider_admission=resolver;driver.base.resolve_provider_admission=resolver;base.os.getenv=poison_getenv;base.urllib.request.urlopen=poison_urlopen;driver.urllib.request.urlopen=poison_urlopen
            assert base.collect_keys(base.PROVIDERS[0])==[]
            status,_,payload=base.request_chat(base.PROVIDERS[0],"synthetic-never-used","model","prompt",8,0.01)
            assert status==0 and isinstance(payload,dict) and payload.get("classification")=="PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED"
            report=driver.discover_and_export(0.01)
            assert report["groq"]["source"]=="admission_blocked"
            assert counts=={"secret_lookup_count":0,"network_attempt_count":0},counts
            return {"case":name,"verdict":"PASS","reason":decision.reason,**counts}
        finally:
            base.resolve_provider_admission=old_resolver;driver.base.resolve_provider_admission=old_resolver;base.os.getenv=old_getenv;base.urllib.request.urlopen=old_urlopen;driver.urllib.request.urlopen=old_urlopen


def positive_control():
    with tempfile.TemporaryDirectory() as td:
        ap,sp=write_pair(Path(td),admission("FREE",True),supervisor())
        d=gate.resolve("groq",ap,sp);assert d.allowed,dataclasses.asdict(d)
        return {"case":"EXACT_FREE_POSITIVE_CONTROL","verdict":"PASS","reason":d.reason,"external_network_performed":False}


def static_guards():
    shell=SUPERVISOR_SH.read_text(encoding="utf-8")
    entry=DISTILLERY_ENTRY.read_text(encoding="utf-8")
    forbidden=("load_all_secret_sources","/run/secrets/clay_provider.env","research_entity/private/API_TOKENS.env",'source "$f"')
    found=[x for x in forbidden if x in shell];assert not found,found
    for required in ("free_provider_admission_gate.py","provider_is_admitted","clear_provider_secret_env","load_admitted_provider_secrets"):
        assert required in shell,required
    for required in ("resolve_provider_admission","admitted_secret","d.secret = admitted_secret"):
        assert required in entry,required
    bash=subprocess.run(["bash","-n",str(SUPERVISOR_SH)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    assert bash.returncode==0,bash.stderr
    return {"case":"STATIC_SECRET_SOURCE_AND_DISTILLERY_GUARDS","verdict":"PASS","bash_n_exit":bash.returncode,"forbidden_generic_secret_sources_present":found}


def main()->int:
    cases=[
      ("MISSING",admission(include=False),supervisor()),
      ("UNKNOWN",admission("UNKNOWN",False),supervisor()),
      ("PAID",admission("PAID",True),supervisor()),
      ("SUBSCRIPTION",admission("SUBSCRIPTION",True),supervisor()),
      ("STALE_EPOCH",admission("FREE",True,epoch="8.66"),supervisor("8.67")),
      ("MALFORMED_SCHEMA",admission("FREE",True,schema="ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v0"),supervisor()),
      ("FREE_NOT_ADMITTED",admission("FREE",False),supervisor()),
      ("FREE_NO_EVIDENCE",admission("FREE",True,evidence=""),supervisor()),
    ]
    results=[negative_case(*x) for x in cases]+[positive_control(),static_guards()]
    receipt={"schema":"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1","observed_at":dt.datetime.now(dt.timezone.utc).isoformat(),"scope":"EXACT_CHECKOUT_DETERMINISTIC_SOURCE_MECHANISM_NO_PROVIDER_IO","repo_head":subprocess.run(["git","-C",str(ROOT),"rev-parse","HEAD"],stdout=subprocess.PIPE,text=True,check=False).stdout.strip(),"source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES},"results":results,"summary":{"tests":len(results),"passed":sum(r["verdict"]=="PASS" for r in results),"blocked_secret_lookup_count":sum(r.get("secret_lookup_count",0) for r in results),"blocked_network_attempt_count":sum(r.get("network_attempt_count",0) for r in results),"external_provider_network_performed":False},"credit":{"provider_runtime":0,"entityos_whole_runtime":0,"hcu_full_runtime":0,"jspace_model_runtime":0,"training":0},"verdict":"PASS"}
    print(json.dumps(receipt,indent=2,sort_keys=True));return 0

if __name__=="__main__":raise SystemExit(main())
