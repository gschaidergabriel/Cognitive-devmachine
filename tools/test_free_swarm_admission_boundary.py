#!/usr/bin/env python3
from __future__ import annotations
import asyncio, contextlib, hashlib, json, os, socket, sys, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(HERE)) if str(HERE) not in sys.path else None
import free_swarm_provider_admission as admission
import run_free_go_swarm as facade
FLAGS={"CLAY_FREE_ONLY_ATTESTED":"1","CLAY_GROQ_FREE_ATTESTED":"1","CLAY_MISTRAL_FREE_ATTESTED":"1","CLAY_NVIDIA_FREE_ATTESTED":"1"}
NAMES=set(sum((list(x) for x in admission.PROVIDER_SECRET_NAMES.values()),[]))|set(FLAGS)|{"CLAY_PROVIDER_ADMISSION_FILE","CLAY_PROVIDER_SECRET_FILES"}

def payload(cost="FREE", admitted=True, *, global_free=True, include=True):
    p={"schema":admission.SCHEMA,"source":admission.SOURCE,"mode":admission.MODE,"decision_id":"test","generation":7,"global_free_only":global_free,"providers":{}}
    p["providers"]["groq" if include else "mistral"]={"cost_class":cost if include else "UNKNOWN","admitted":admitted if include else False,"reason":"test"}
    return p

@contextlib.contextmanager
def env_clean():
    old={k:os.environ.get(k) for k in NAMES}
    try:
        for k in NAMES: os.environ.pop(k,None)
        yield
    finally:
        for k in NAMES: os.environ.pop(k,None)
        for k,v in old.items():
            if v is not None: os.environ[k]=v

def case(name,p,positive=False):
    with tempfile.TemporaryDirectory() as td, env_clean():
        td=Path(td); secret=td/"provider.env"
        secret.write_text("GROQ_API_KEY=sentinel-secret\nMISTRAL_API_KEY=must-not-be-read\n")
        os.environ.update(FLAGS); os.environ["CLAY_PROVIDER_SECRET_FILES"]=str(secret)
        ap=td/"admission.json"
        if p is None: os.environ["CLAY_PROVIDER_ADMISSION_FILE"]=str(td/"missing.json")
        else: ap.write_text(json.dumps(p)); os.environ["CLAY_PROVIDER_ADMISSION_FILE"]=str(ap)
        admission._CACHE_KEY=admission._CACHE_VALUE=None; admission.reset_metrics()
        attempts=0; real=socket.socket.connect
        def blocked(sock,address):
            nonlocal attempts; attempts+=1; admission.record_network_attempt(); raise AssertionError(address)
        socket.socket.connect=blocked
        try:
            spec=next(x for x in facade.PROVIDERS if x.name=="groq"); keys=facade.collect_keys(spec); m=admission.metrics_snapshot()
        finally: socket.socket.connect=real
        out={"case":name,"keys_returned":len(keys),"secret_lookup_count":m["secret_lookup_count"],"network_attempt_count":m["network_attempt_count"]+attempts}
        if positive: assert keys==["sentinel-secret"] and out["secret_lookup_count"]>0 and out["network_attempt_count"]==0, out
        else: assert keys==[] and out["secret_lookup_count"]==0 and out["network_attempt_count"]==0, out
        return out

class BoundaryTests(unittest.TestCase):
    def test_negative_matrix(self):
        for n,p in [("global_attestation_missing",payload(global_free=False)),("provider_admission_missing",payload(include=False)),("unknown",payload("UNKNOWN",False)),("paid",payload("PAID",False)),("subscription",payload("SUBSCRIPTION",False)),("admission_file_missing",None),("paid_admitted_contradiction",payload("PAID",True))]: case(n,p)
    def test_positive_free(self): case("free_positive",payload(),True)
    def test_positive_run_sync(self):
        with tempfile.TemporaryDirectory() as td, env_clean():
            td=Path(td); (td/"provider.env").write_text("GROQ_API_KEY=sentinel-secret\n"); (td/"admission.json").write_text(json.dumps(payload()))
            os.environ["CLAY_PROVIDER_SECRET_FILES"]=str(td/"provider.env"); os.environ["CLAY_PROVIDER_ADMISSION_FILE"]=str(td/"admission.json")
            admission._CACHE_KEY=admission._CACHE_VALUE=None; self.assertEqual(asyncio.run(facade.run(facade.parse_args([]))),0)
    def test_supervisor_no_secret_sourcing(self):
        t=(HERE/"run_24h_entityos_swarm_supervisor.sh").read_text(); self.assertNotIn("load_secret_file",t); self.assertNotIn("has_provider_key",t); self.assertLess(t.index("free_swarm_provider_admission.py"),t.index("run_24h_entityos_swarm.py"))
    def test_facade_order_and_frozen_collector(self):
        t=(HERE/"run_free_go_swarm.py").read_text(); b=t[t.index("def collect_keys"):t.index("\n\ndef ",t.index("def collect_keys")+5)]
        self.assertLess(b.index("_typed_admission()"),b.index("_ORIGINAL_COLLECT_KEYS(spec)")); self.assertIn("_ORIGINAL_COLLECT_KEYS = _legacy.collect_keys",t)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def receipt():
    results=[case(n,p) for n,p in [("global_attestation_missing",payload(global_free=False)),("provider_admission_missing",payload(include=False)),("unknown",payload("UNKNOWN",False)),("paid",payload("PAID",False)),("subscription",payload("SUBSCRIPTION",False)),("admission_file_missing",None),("paid_admitted_contradiction",payload("PAID",True))]]
    pos=case("free_positive",payload(),True); files=[HERE/"free_swarm_provider_admission.py",HERE/"run_free_go_swarm.py",HERE/"run_24h_entityos_swarm_supervisor.sh",HERE/"test_free_swarm_admission_boundary.py"]
    return {"schema":"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1","authority_epoch_target":"8.67","scope":"FREE_SWARM_ADMISSION_BOUNDARY_COMPONENT_ONLY","observed_environment":"CHATGPT_LOCAL_CONTAINER_COMPONENT_TEST","negative_acceptance":{"required":"secret_lookup_count=0 AND network_attempt_count=0","pass":all(x["secret_lookup_count"]==x["network_attempt_count"]==x["keys_returned"]==0 for x in results),"cases":results},"positive_control":pos,"source_sha256":{str(p.relative_to(ROOT)):sha(p) for p in files},"legacy_env_attestation_is_authority":False,"shell_sources_secret_files":False,"whole_entityos_runtime_credit":0,"whole_hcu_runtime_credit":0,"provider_runtime_credit":0,"training_credit":0,"note":"Local component evidence only; no provider network call or paid execution."}
if __name__=="__main__":
    r=receipt(); (ROOT/"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT.v1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n"); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r["negative_acceptance"]["pass"] else 1)
