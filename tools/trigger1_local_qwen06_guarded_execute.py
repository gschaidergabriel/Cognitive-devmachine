#!/usr/bin/env python3
"""Guarded exact-source launcher for the local Qwen3-0.6B Trigger-1 experiment."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, subprocess, sys, tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "tools/trigger1_local_qwen06_activation_api_execute.py"
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_GUARDED_RUNTIME_RECEIPT/v1"
PROVIDERS = ("GROQ","MISTRAL","NVIDIA","NGC","OPENROUTER","TOGETHER","ANTHROPIC","OPENAI")
SECRET_WORDS = ("API_KEY","TOKEN","SECRET","CREDENTIAL","AUTH")
KEEP = {"PATH","HOME","USER","LOGNAME","SHELL","LANG","LC_ALL","LC_CTYPE","TZ","TMPDIR","TMP","TEMP","HF_HOME","HF_HUB_CACHE","HUGGINGFACE_HUB_CACHE","TRANSFORMERS_CACHE","XDG_CACHE_HOME","CUDA_VISIBLE_DEVICES","LD_LIBRARY_PATH","VIRTUAL_ENV","CONDA_PREFIX","PYTHONPATH","OMP_NUM_THREADS","MKL_NUM_THREADS"}


def csha(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()


def fsha(p: pathlib.Path):
    if not p.is_file(): return None
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024), b""): h.update(b)
    return h.hexdigest()


def git(*a):
    try:
        p=subprocess.run(["git","-C",str(ROOT),*a],text=True,capture_output=True,timeout=10)
        return p.stdout.strip() if p.returncode==0 else "UNKNOWN"
    except Exception: return "UNKNOWN"


def sensitive(k: str) -> bool:
    u=str(k).upper(); return any(p in u for p in PROVIDERS) and any(s in u for s in SECRET_WORDS)


def source():
    s=git("status","--porcelain=v1","--untracked-files=all")
    return {"repo_head":git("rev-parse","HEAD"),"repo_tree":git("rev-parse","HEAD^{tree}"),"dirty":s not in ("","UNKNOWN"),"git_status_observed":s!="UNKNOWN","dirty_status_sha256":None if s=="UNKNOWN" else csha(s.splitlines()),"dirty_entry_count":0 if s in ("","UNKNOWN") else len(s.splitlines())}


def guard_code():
    return r'''import datetime as d, ipaddress as i, json as j, os, socket, threading
A=os.environ.get("CLAY_LOCAL_GUARD_AUDIT_LOG"); L=threading.Lock()
P=("GROQ","MISTRAL","NVIDIA","NGC","OPENROUTER","TOGETHER","ANTHROPIC","OPENAI"); S=("API_KEY","TOKEN","SECRET","CREDENTIAL","AUTH")
def sen(k):
 u=str(k).upper(); return any(p in u for p in P) and any(s in u for s in S)
def log(e,**x):
 if not A:return
 with L:
  with open(A,"a",encoding="utf-8") as f:f.write(j.dumps({"event":e,"at":d.datetime.now(d.timezone.utc).isoformat(),**x},sort_keys=True,separators=(",",":"))+"\n")
def loop(h):
 if h is None:return True
 h=h.decode() if isinstance(h,(bytes,bytearray)) else str(h)
 if h.lower()=="localhost":return True
 try:return i.ip_address(h.split("%",1)[0]).is_loopback
 except Exception:return False
og=os.getenv; oi=os._Environ.__getitem__; oc=os._Environ.__contains__; oga=socket.getaddrinfo; con=socket.socket.connect; cex=socket.socket.connect_ex
def gg(k,z=None):
 if sen(k):log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return og(k,z)
def gi(self,k):
 if sen(k):log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return oi(self,k)
def gc(self,k):
 if sen(k):log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return oc(self,k)
def ga(h,*a,**kw):
 if not loop(h):log("blocked_non_loopback_dns",host=str(h)[:300]);raise socket.gaierror("BLOCKED_NON_LOOPBACK_DNS")
 return oga(h,*a,**kw)
def co(self,a):
 h=a[0] if isinstance(a,tuple) and a else a
 if not loop(h):log("blocked_non_loopback_connect",host=str(h)[:300]);raise OSError("BLOCKED_NON_LOOPBACK_CONNECT")
 return con(self,a)
def cx(self,a):
 h=a[0] if isinstance(a,tuple) and a else a
 if not loop(h):log("blocked_non_loopback_connect_ex",host=str(h)[:300]);raise OSError("BLOCKED_NON_LOOPBACK_CONNECT_EX")
 return cex(self,a)
os.getenv=gg; os._Environ.__getitem__=gi; os._Environ.__contains__=gc; socket.getaddrinfo=ga; socket.socket.connect=co; socket.socket.connect_ex=cx; log("guard_installed")
'''


def env_for(audit):
    removed=sorted(k for k in os.environ if sensitive(k)); e={}
    for k,v in os.environ.items():
        if sensitive(k): continue
        if k in KEEP or k.startswith(("LC_","CUDA_","ROCR_")): e[k]=v
    e.update({"CLAY_LOCAL_GUARD_AUDIT_LOG":str(audit),"HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","HF_DATASETS_OFFLINE":"1","NO_PROXY":"127.0.0.1,localhost,::1","no_proxy":"127.0.0.1,localhost,::1"})
    return e,removed


def audit_rows(p):
    if not p.is_file(): return []
    out=[]
    for l in p.read_text().splitlines():
        try:
            x=json.loads(l); out.append(x) if isinstance(x,dict) else None
        except Exception: pass
    return out


def selftest():
    with tempfile.TemporaryDirectory() as td:
        d=pathlib.Path(td); g=d/"g.py"; a=d/"a.jsonl"; g.write_text(guard_code()); e,_=env_for(a)
        code='''import json,os,socket\nr={}\ntry:os.getenv("OPENROUTER_API_KEY");r["cred"]=False\nexcept Exception:r["cred"]=True\ntry:socket.getaddrinfo("example.com",443);r["net"]=False\nexcept Exception:r["net"]=True\ntry:socket.getaddrinfo("localhost",80);r["loop"]=True\nexcept Exception:r["loop"]=False\nprint(json.dumps(r))'''
        b="import pathlib;exec(pathlib.Path(%r).read_text(),{});exec(%r,{})"%(str(g),code)
        p=subprocess.run([sys.executable,"-c",b],env=e,text=True,capture_output=True,timeout=20); rows=audit_rows(a); names=[x.get("event") for x in rows]
        r=json.loads(p.stdout.splitlines()[-1]) if p.stdout.strip() else {}; ok=p.returncode==0 and r=={"cred":True,"net":True,"loop":True} and "guard_installed" in names and "blocked_provider_credential_lookup" in names and "blocked_non_loopback_dns" in names
        print(json.dumps({"schema":"CLAY_TRIGGER1_LOCAL_QWEN06_GUARD_SELFTEST/v1","pass":ok,"probe":r,"audit_events":names},indent=2,sort_keys=True)); return 0 if ok else 1


def write(p,obj): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")


def execute(a):
    out=pathlib.Path(a.output_dir).expanduser().resolve(); cache=pathlib.Path(a.cache_dir).expanduser().resolve(); pre=source(); failures=[]
    try: out.relative_to(ROOT.resolve()); failures.append("OUTPUT_DIR_MUST_BE_OUTSIDE_REPO")
    except ValueError: pass
    if not TARGET.is_file(): failures.append("TARGET_MISSING")
    if pre["repo_head"]=="UNKNOWN" or pre["repo_tree"]=="UNKNOWN" or not pre["git_status_observed"]: failures.append("SOURCE_IDENTITY_UNOBSERVED")
    if pre["dirty"]: failures.append("SOURCE_TREE_DIRTY")
    if pre["repo_head"]!=a.expected_head: failures.append("EXPECTED_HEAD_MISMATCH")
    if a.expected_tree and pre["repo_tree"]!=a.expected_tree: failures.append("EXPECTED_TREE_MISMATCH")
    if not cache.exists(): failures.append("CACHE_DIR_MISSING")
    if failures:
        r={"schema":SCHEMA,"status":"PRECONDITION_BLOCKED","source_before":pre,"failures":failures,"credit":{"whole_entityos_hcu":0,"hcu_full":0,"jspace_model":0,"training":0}}
        r["receipt_sha256"]=csha(r)
        if "OUTPUT_DIR_MUST_BE_OUTSIDE_REPO" not in failures: write(out/"trigger1_local_activation_api_guard_receipt.json",r)
        else: print(json.dumps(r,indent=2,sort_keys=True))
        return 4
    out.mkdir(parents=True,exist_ok=True); resultp=out/"trigger1_local_activation_api_result.json"; started=dt.datetime.now(dt.timezone.utc).isoformat()
    with tempfile.TemporaryDirectory() as td:
        d=pathlib.Path(td); gf=d/"guard.py"; al=d/"audit.jsonl"; gf.write_text(guard_code()); env,removed=env_for(al)
        boot='import pathlib,runpy,sys;exec(pathlib.Path(sys.argv[1]).read_text(),{});t=sys.argv[2];sys.argv=[t]+sys.argv[3:];runpy.run_path(t,run_name="__main__")'
        cmd=[sys.executable,"-c",boot,str(gf),str(TARGET),"--output-dir",str(out),"--cache-dir",str(cache)]
        p=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=a.timeout_seconds); rows=audit_rows(al)
    post=source(); obj=None; err=None
    try:
        obj=json.loads(resultp.read_text()); assert isinstance(obj,dict)
    except Exception as x: err=f"{type(x).__name__}:{str(x)[:200]}"
    names=[str(x.get("event")) for x in rows]; cred=sum(n=="blocked_provider_credential_lookup" for n in names); net=sum(n.startswith("blocked_non_loopback") for n in names)
    valid=bool(obj and obj.get("result_sha256")==csha({k:v for k,v in obj.items() if k!="result_sha256"})); sm=bool(obj and isinstance(obj.get("source"),dict) and obj["source"].get("repo_head")==pre["repo_head"] and obj["source"].get("repo_tree")==pre["repo_tree"])
    stable=post["repo_head"]==pre["repo_head"] and post["repo_tree"]==pre["repo_tree"] and post["dirty"] is False and post["git_status_observed"]
    bound=bool(obj and obj.get("status") in {"PASS","SCIENTIFIC_NEGATIVE"} and isinstance(obj.get("runtime_manifest"),dict) and obj.get("runtime_build_sha256") and obj.get("checkpoint_sha256") and obj.get("tokenizer_sha256") and obj.get("api_loopback_only") is True and obj.get("zero_provider_billing") is True and obj.get("external_provider_credentials_read") is False)
    guard="guard_installed" in names and not any(sensitive(k) for k in env) and cred==0 and net==0 and valid and sm and stable and err is None
    ts=obj.get("status") if obj else None
    if guard and ts=="PASS" and bound and p.returncode==0: status,rc="EXECUTED_PASS_GUARDED",0
    elif guard and ts=="SCIENTIFIC_NEGATIVE" and bound: status,rc="EXECUTED_SCIENTIFIC_NEGATIVE_GUARDED",2
    elif guard and ts=="BLOCKED_LOCAL_FASTPATH": status,rc="TARGET_BLOCKED_GUARD_INTACT",3
    else: status,rc="GUARD_OR_IDENTITY_BLOCKED",4
    r={"schema":SCHEMA,"status":status,"started_at":started,"finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),"source_before":pre,"source_after":post,"repo_stable_clean":stable,"executor":{"python":sys.executable,"python_sha256":fsha(pathlib.Path(sys.executable)),"target_sha256":fsha(TARGET),"guard_sha256":hashlib.sha256(guard_code().encode()).hexdigest()},"environment_fence":{"removed_sensitive_env_names":removed,"sensitive_names_in_child":[k for k in env if sensitive(k)],"offline_model_cache_required":True,"network_policy":"LOOPBACK_ONLY"},"guard":{"installed":"guard_installed" in names,"credential_lookup_attempts":cred,"nonloopback_network_attempts":net,"audit_sha256":csha(rows)},"child":{"exit_code":p.returncode,"stdout_sha256":hashlib.sha256(p.stdout.encode()).hexdigest(),"stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest()},"target":{"status":ts,"file_sha256":fsha(resultp),"declared_result_valid":valid,"source_matches":sm,"runtime_fields_bound":bound,"parse_error":err,"model":obj.get("model") if obj else None,"model_revision":obj.get("model_revision") if obj else None,"checkpoint_sha256":obj.get("checkpoint_sha256") if obj else None,"tokenizer_sha256":obj.get("tokenizer_sha256") if obj else None,"runtime_build_sha256":obj.get("runtime_build_sha256") if obj else None,"api_endpoint":obj.get("api_endpoint") if obj else None},"evidence_scope":"LOCAL_QWEN06_GUARD_AND_RUNTIME_BINDING_ONLY","credit":{"whole_entityos_hcu":0,"hcu_full":0,"jspace_model":0,"training":0,"canonical_semantics":False}}
    r["receipt_sha256"]=csha(r); write(out/"trigger1_local_activation_api_guard_receipt.json",r); return rc


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--output-dir"); ap.add_argument("--cache-dir",default=os.getenv("HF_HOME") or str(pathlib.Path.home()/".cache/huggingface")); ap.add_argument("--expected-head"); ap.add_argument("--expected-tree"); ap.add_argument("--timeout-seconds",type=int,default=3600); a=ap.parse_args()
    if a.self_test:return selftest()
    if not a.output_dir or not a.expected_head:ap.error("--output-dir and --expected-head are required")
    return execute(a)
if __name__=="__main__":raise SystemExit(main())
