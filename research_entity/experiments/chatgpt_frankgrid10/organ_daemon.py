#!/usr/bin/env python3
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, signal, sqlite3, subprocess, sys, time, traceback, uuid
from pathlib import Path

BASE = Path("/workspace/frankgrid10-organ")
CODE = BASE / "code" / "frankgrid10_v2.py"
DB = BASE / "state" / "frankgrid10.sqlite3"
IPC = BASE / "ipc"; INBOX=IPC/"inbox"; PROCESSING=IPC/"processing"; OUTBOX=IPC/"outbox"; RECEIPTS=IPC/"receipts"; DEAD=IPC/"deadletter"
RUN=BASE/"run"; LOGS=BASE/"logs"; IDDIR=BASE/"identity"; EPOCHS=IDDIR/"epochs"
LOCK=RUN/"organ-daemon.lock"; HEART=RUN/"heartbeat.json"; CURRENT_EPOCH=IDDIR/"current_epoch.json"; IDENTITY=IDDIR/"identity.json"
EXPECTED_SOURCE_SHA="60ec27675b2900e9f71f3c22f50cb3ca28231272d4f3bb7ec016b3127608a03e"
SCHEMA="FRANKGRID10_ORGAN_COMMAND/v1"; RECEIPT_SCHEMA="FRANKGRID10_ORGAN_RECEIPT/v2"
MIN_MEM_AVAILABLE=512*1024*1024; MIN_DISK_FREE=2*1024*1024*1024; MAX_LOAD_PER_CPU=2.5
IDENT=None; EPOCH=None; STOP=False

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def atomic_json(path:Path,obj:dict):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_name("."+path.name+"."+uuid.uuid4().hex+".tmp")
    data=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    with open(tmp,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def verify_runtime():
    if not CODE.is_file():raise RuntimeError("SOURCE_MISSING")
    got=sha_bytes(CODE.read_bytes())
    if got!=EXPECTED_SOURCE_SHA:raise RuntimeError(f"SOURCE_HASH_MISMATCH:{got}")
    c=sqlite3.connect(DB)
    try: integrity=c.execute("PRAGMA integrity_check").fetchone()[0]; schema=c.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    finally:c.close()
    if integrity!="ok":raise RuntimeError(f"SQLITE_INTEGRITY:{integrity}")
    if not schema or schema[0]!="FRANKGRID10/v2":raise RuntimeError(f"SCHEMA_MISMATCH:{schema}")
    return {"source_sha256":got,"sqlite_integrity":integrity,"db_schema":schema[0]}

def resource_telemetry():
    try:
        mem={}
        for line in Path('/proc/meminfo').read_text().splitlines():
            if ':' in line:
                k,v=line.split(':',1); parts=v.strip().split(); mem[k]=int(parts[0])*1024 if parts else 0
        mem_avail=int(mem.get('MemAvailable',0)); load1=float(Path('/proc/loadavg').read_text().split()[0]); cpus=max(1,os.cpu_count() or 1)
        st=os.statvfs(BASE); disk_free=st.f_bavail*st.f_frsize; lpc=load1/cpus
        reasons=[]
        if mem_avail<MIN_MEM_AVAILABLE:reasons.append('LOW_MEMORY')
        if disk_free<MIN_DISK_FREE:reasons.append('LOW_DISK')
        if lpc>MAX_LOAD_PER_CPU:reasons.append('HIGH_LOAD')
        return {"status":"GREEN" if not reasons else "RED","reasons":reasons,"mem_available":mem_avail,"disk_free":disk_free,"load1":load1,"cpu_count":cpus,"load_per_cpu":lpc,
                "thresholds":{"min_mem_available":MIN_MEM_AVAILABLE,"min_disk_free":MIN_DISK_FREE,"max_load_per_cpu":MAX_LOAD_PER_CPU}}
    except Exception as e:return {"status":"RED","reasons":["TELEMETRY_ERROR:"+type(e).__name__+":"+str(e)]}

def load_identity():
    IDDIR.mkdir(parents=True,exist_ok=True); EPOCHS.mkdir(parents=True,exist_ok=True)
    if IDENTITY.exists(): return json.loads(IDENTITY.read_text())
    obj={"schema":"FRANKGRID10_ORGAN_IDENTITY/v1","entity_id":"entity-"+str(uuid.uuid4()),"installation_id":"install-"+str(uuid.uuid4()),"state_root_id":"state-"+str(uuid.uuid4()),"state_root":str(BASE/"state"),"created_at":time.time(),"host_binding":"VPS_ROOTLESS_PODMAN"}
    atomic_json(IDENTITY,obj); return obj

def open_epoch():
    prev=None
    if CURRENT_EPOCH.exists():
        try: prev=json.loads(CURRENT_EPOCH.read_text()).get('runtime_epoch_id')
        except Exception: prev=None
    obj={"schema":"FRANKGRID10_RUNTIME_EPOCH/v1","runtime_epoch_id":"epoch-"+str(uuid.uuid4()),"predecessor_epoch_id":prev,"opened_at":time.time(),"pid":os.getpid(),"status":"OPEN","entity_id":IDENT['entity_id'],"installation_id":IDENT['installation_id'],"state_root_id":IDENT['state_root_id']}
    atomic_json(EPOCHS/(obj['runtime_epoch_id']+'.json'),obj); atomic_json(CURRENT_EPOCH,obj); return obj

def close_epoch(reason):
    if not EPOCH:return
    obj=dict(EPOCH); obj.update({"status":"CLOSED","closed_at":time.time(),"termination_reason":reason})
    atomic_json(EPOCHS/(obj['runtime_epoch_id']+'.json'),obj); atomic_json(CURRENT_EPOCH,obj)

def cli(args,timeout=90):
    p=subprocess.run([sys.executable,str(CODE),"--db",str(DB)]+args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode!=0:raise RuntimeError(f"CLI_RC_{p.returncode}: {p.stderr[-4000:]}")
    try:return json.loads(p.stdout)
    except Exception:return {"stdout":p.stdout,"stderr":p.stderr,"returncode":p.returncode}

def command_args(obj):
    op=str(obj.get("op","")).upper()
    if op=="PRE":
        prompt=obj.get("prompt");
        if not isinstance(prompt,str) or not prompt.strip():raise ValueError("PRE_REQUIRES_PROMPT")
        a=["pre","--prompt",prompt]
        if obj.get("ablate"):
            if not isinstance(obj["ablate"],list):raise ValueError("ABLATE_MUST_BE_LIST")
            a += ["--ablate",",".join(map(str,obj["ablate"]))]
        return a
    if op=="POST":
        tid,response=obj.get("turn_id"),obj.get("response")
        if not isinstance(tid,str) or not tid:raise ValueError("POST_REQUIRES_TURN_ID")
        if not isinstance(response,str):raise ValueError("POST_REQUIRES_RESPONSE")
        return ["post","--turn-id",tid,"--response",response]
    if op=="INGEST":
        role,content=obj.get("role"),obj.get("content")
        if not isinstance(role,str) or not role:raise ValueError("INGEST_REQUIRES_ROLE")
        if not isinstance(content,str) or not content:raise ValueError("INGEST_REQUIRES_CONTENT")
        a=["ingest","--role",role,"--source-kind",str(obj.get("source_kind","ORGAN_INPUT")),"--content",content,"--confidence",str(float(obj.get("confidence",0.5))),"--salience",str(float(obj.get("salience",0.5)))]
        if obj.get("source_ref"):a += ["--source-ref",str(obj["source_ref"])]
        return a
    if op=="STATUS":return ["status"]
    if op=="CHECKPOINT":
        out=BASE/"state"/"checkpoints"/(str(obj.get("name") or ("cp-"+uuid.uuid4().hex))+".json");out.parent.mkdir(parents=True,exist_ok=True);return ["checkpoint","--out",str(out)]
    if op=="SELFTEST":return ["selftest"]
    raise ValueError("UNSUPPORTED_OP")

def receipt_base(cid,cmd_sha,op,seq,status,t0):
    return {"schema":RECEIPT_SCHEMA,"command_id":cid,"command_sha256":cmd_sha,"op":op,"status":status,"started_at":t0,"finished_at":time.time(),"heartbeat_seq":seq,
            "entity_id":IDENT['entity_id'],"installation_id":IDENT['installation_id'],"state_root_id":IDENT['state_root_id'],"runtime_epoch_id":EPOCH['runtime_epoch_id'],"truth_authority":False,"effect_authority":False}

def handle(path:Path,seq:int):
    raw=path.read_bytes();cmd_sha=sha_bytes(raw);obj=json.loads(raw)
    if obj.get("schema")!=SCHEMA:raise ValueError("BAD_SCHEMA")
    cid=obj.get("command_id")
    if not isinstance(cid,str) or not cid or "/" in cid or ".." in cid:raise ValueError("BAD_COMMAND_ID")
    op=str(obj.get('op','')).upper(); t0=time.time(); res=resource_telemetry()
    if res['status']!='GREEN' and op!='STATUS':raise RuntimeError("RESOURCE_ADMISSION_DENIED:"+','.join(res.get('reasons',[])))
    args=command_args(obj); pre=verify_runtime(); result=cli(args,timeout=min(120,max(5,int(obj.get("timeout_seconds",90))))); post=verify_runtime(); res_post=resource_telemetry()
    receipt=receipt_base(cid,cmd_sha,op,seq,"PASS",t0);receipt.update({"resource_pre":res,"resource_post":res_post,"runtime_pre":pre,"runtime_post":post,"result":result})
    atomic_json(OUTBOX/(cid+".json"),receipt);atomic_json(RECEIPTS/(cid+".json"),receipt)

def fail_receipt(q:Path,seq:int,e:Exception):
    cid=q.stem;t0=time.time();cmd_sha="UNKNOWN";op="UNKNOWN"
    try:
        raw=q.read_bytes();cmd_sha=sha_bytes(raw);obj=json.loads(raw);cid=str(obj.get('command_id') or cid);op=str(obj.get('op') or 'UNKNOWN').upper()
    except Exception:pass
    err=receipt_base(cid,cmd_sha,op,seq,"FAIL",t0);err.update({"error":type(e).__name__+":"+str(e),"trace":traceback.format_exc()[-6000:],"resource":resource_telemetry()})
    atomic_json(DEAD/(q.stem+"-"+uuid.uuid4().hex[:8]+".json"),err);atomic_json(OUTBOX/(cid+".json"),err);atomic_json(RECEIPTS/(cid+".json"),err)

def heartbeat(seq:int,status="RUNNING",error=None):
    obj={"schema":"FRANKGRID10_ORGAN_HEARTBEAT/v2","seq":seq,"pid":os.getpid(),"wall_time":time.time(),"monotonic":time.monotonic(),"status":status,
         "entity_id":IDENT.get('entity_id') if IDENT else None,"installation_id":IDENT.get('installation_id') if IDENT else None,"state_root_id":IDENT.get('state_root_id') if IDENT else None,
         "runtime_epoch_id":EPOCH.get('runtime_epoch_id') if EPOCH else None,"resource":resource_telemetry(),"truth_authority":False,"effect_authority":False}
    if error:obj["error"]=error
    atomic_json(HEART,obj)

def on_signal(signum,frame):
    global STOP; STOP=True

def main():
    global IDENT,EPOCH,STOP
    ap=argparse.ArgumentParser();ap.add_argument("--poll",type=float,default=0.5);ns=ap.parse_args()
    for p in (INBOX,PROCESSING,OUTBOX,RECEIPTS,DEAD,RUN,LOGS,IDDIR,EPOCHS):p.mkdir(parents=True,exist_ok=True)
    lf=open(LOCK,"a+")
    try:fcntl.flock(lf.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:print("ALREADY_RUNNING",file=sys.stderr);return 73
    IDENT=load_identity();EPOCH=open_epoch();signal.signal(signal.SIGTERM,on_signal);signal.signal(signal.SIGINT,on_signal)
    verify_runtime();tele=resource_telemetry()
    if tele['status']!='GREEN':raise RuntimeError("STARTUP_RESOURCE_RED:"+','.join(tele.get('reasons',[])))
    st=cli(["selftest"],timeout=120)
    if st.get("selftest")!="PASS" or st.get("checks_passed")!=st.get("checks_total"):raise RuntimeError("STARTUP_SELFTEST_FAILED")
    seq=0;heartbeat(seq,"RUNNING")
    while not STOP:
        seq+=1
        if seq%4==0:heartbeat(seq,"RUNNING")
        for p in sorted(INBOX.glob("*.json")):
            q=PROCESSING/p.name
            try:os.replace(p,q)
            except FileNotFoundError:continue
            try:handle(q,seq)
            except Exception as e:fail_receipt(q,seq,e)
            finally:q.unlink(missing_ok=True)
        time.sleep(max(0.1,ns.poll))
    close_epoch("SIGTERM_OR_SIGINT");heartbeat(seq,"STOPPED");return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        try:
            close_epoch("UNHANDLED_"+type(e).__name__);heartbeat(-1,"FAILED",type(e).__name__+":"+str(e))
        except Exception:pass
        raise
