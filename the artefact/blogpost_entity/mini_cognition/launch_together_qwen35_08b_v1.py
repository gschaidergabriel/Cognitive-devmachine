#!/usr/bin/env python3
"""Fail-closed direct Together Full-FT launcher for ~1B ClayCode cognition."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent

def _default_supervisor_policy():
    try:
        repo_root=HERE.parents[2]
    except IndexError:
        return HERE/"__missing_supervisor_policy__"
    return repo_root/"research_entity"/"claycode"/"autonomous"/"SUPERVISOR_INBOX.json"

SUPERVISOR_POLICY=_default_supervisor_policy()
TRAIN=HERE/"train_v2.jsonl"; VALID=HERE/"validation_v2.jsonl"; V2_VALIDATOR=HERE/"validate_corpus_v2.py"
EXPECTED_MODEL="Qwen/Qwen3.5-0.8B"; MODEL=os.environ.get("CLAYCOG_08B_MODEL",EXPECTED_MODEL)
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3")); EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
RANDOM_SEED=int(os.environ.get("CLAYCOG_RANDOM_SEED","3407")); LEARNING_RATE=float(os.environ.get("CLAYCOG_LEARNING_RATE","1e-5")); WARMUP_RATIO=float(os.environ.get("CLAYCOG_WARMUP_RATIO","0.03"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00")); FILE_WAIT_SECONDS=int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS","600"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"; CREATE_LEDGER_DIR_ENV="CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT={"pending","queued","running","compressing","uploading","cancel_requested","cancelled","error","completed"}

def current_free_only(path=None):
    p=Path(path) if path is not None else SUPERVISOR_POLICY
    try:
        doc=json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"EXECUTION_POLICY_UNREADABLE {p}: {type(e).__name__}") from e
    verified=doc.get("verified_updates")
    if not isinstance(verified,dict) or type(verified.get("free_only")) is not bool:
        raise SystemExit("EXECUTION_POLICY_FREE_ONLY_UNKNOWN")
    return verified["free_only"]

def assert_provider_execution_allowed(path=None):
    if current_free_only(path):
        raise SystemExit(
            f"FREE_ONLY_PROVIDER_REJECT cost_class=PAID provider=Together model={MODEL} "
            "before_secret_lookup=true before_network=true"
        )

def validate_static_contract():
    if MODEL!=EXPECTED_MODEL: raise SystemExit(f"MODEL_OVERRIDE_REJECTED expected {EXPECTED_MODEL!r}, got {MODEL!r}")
    if not 1<=EPOCHS<=20 or not 0<=EVALS<=20: raise SystemExit("TRAINING_COUNT_OUT_OF_RANGE")
    if RANDOM_SEED<0 or not 0<LEARNING_RATE<=1 or not 0<=WARMUP_RATIO<=1: raise SystemExit("HYPERPARAMETER_OUT_OF_RANGE")
    if not 0<MAX_USD<=18: raise SystemExit("BUDGET_GATE_OUT_OF_RANGE")

def local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(V2_VALIDATOR),str(TRAIN),str(VALID)],check=True)

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def training_method(): return {"method":"sft","train_on_inputs":"auto"}
def training_type(): return {"type":"Full"}
def campaign_descriptor(): return {"schema":"claycog-08b-together-direct-campaign/v2","model":MODEL,"training_sha256":sha256_file(TRAIN),"validation_sha256":sha256_file(VALID),"epochs":EPOCHS,"evals":EVALS,"random_seed":RANDOM_SEED,"learning_rate":LEARNING_RATE,"warmup_ratio":WARMUP_RATIO,"training_method":training_method(),"training_type":training_type(),"n_checkpoints":1}
def campaign_fingerprint(): return hashlib.sha256(json.dumps(campaign_descriptor(),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def campaign_suffix(fp): return "claycog08b-v2-"+fp[:24]
def objdict(x): return x.model_dump() if hasattr(x,"model_dump") else x.dict() if hasattr(x,"dict") else x if isinstance(x,dict) else str(x)
def _field(x,n,d=None): return x.get(n,d) if isinstance(x,dict) else getattr(x,n,d)

def get_full_training_limits(client):
    limits=client.fine_tuning.model_limits(model_name=MODEL)
    if not getattr(limits,"supports_full_training",False) or getattr(limits,"full_training",None) is None: raise SystemExit(f"MODEL_LIMITS_REJECT full fine-tuning not supported for {MODEL}")
    return limits

def wait_file(client,file_id,timeout_seconds=FILE_WAIT_SECONDS):
    deadline=time.monotonic()+timeout_seconds
    while True:
        meta=client.files.retrieve(file_id)
        if getattr(meta,"processed",None) is True or str(getattr(meta,"processing_status","") or "").upper()=="COMPLETED": return meta
        status=str(getattr(meta,"processing_status","") or "").upper()
        if status in {"INVALID_FORMAT","FAILED","ERROR"}: raise RuntimeError(f"Together rejected {file_id}: {status}")
        if time.monotonic()>=deadline: raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)
def estimate_price(client,train_id,valid_id): return client.fine_tuning.estimate_price(training_file=train_id,validation_file=valid_id,model=MODEL,n_epochs=EPOCHS,n_evals=EVALS,training_method=training_method(),training_type=training_type())
def create_payload(train_id,valid_id,suffix): return {"training_file":train_id,"validation_file":valid_id,"model":MODEL,"n_epochs":EPOCHS,"n_evals":EVALS,"n_checkpoints":1,"random_seed":RANDOM_SEED,"learning_rate":LEARNING_RATE,"warmup_ratio":WARMUP_RATIO,"suffix":suffix,"training_method":training_method(),"training_type":training_type()}

def _items(x):
    if x is None:return []
    if hasattr(x,"data"):return list(x.data or [])
    if isinstance(x,dict):return list(x.get("data") or [])
    return list(x) if isinstance(x,(list,tuple)) else []
def matching_campaign_jobs(client,suffix):
    out=[]
    for job in _items(client.fine_tuning.list()):
        status=str(_field(job,"status","")).lower(); name=str(_field(job,"model_output_name","") or "")
        if status and status not in ACTIVE_OR_SPENT: continue
        if suffix not in name or _field(job,"model",None) not in (None,"",MODEL): continue
        out.append(job)
    return out
def assert_no_duplicate_campaign(client,suffix):
    m=matching_campaign_jobs(client,suffix)
    if m: raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): "+",".join(str(_field(x,"id","UNKNOWN")) for x in m))
def require_create_confirmation(fp):
    if os.environ.get(CREATE_CONFIRM_ENV,"")!=fp: raise SystemExit(f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to exact preflight fingerprint {fp}")
def create_ledger_dir(): return Path(os.environ[CREATE_LEDGER_DIR_ENV]).expanduser() if os.environ.get(CREATE_LEDGER_DIR_ENV) else Path.home()/".local"/"state"/"claycog"/"training"
def create_ledger_path(fp): return create_ledger_dir()/(fp+".json")
def read_create_ledger(fp):
    p=create_ledger_path(fp)
    if not p.exists():return None
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:raise SystemExit(f"CREATE_LEDGER_UNREADABLE {p}: {e}") from e
def assert_no_local_create_intent(fp):
    e=read_create_ledger(fp)
    if e is not None: raise SystemExit(f"LOCAL_CREATE_INTENT_ABORT fingerprint={fp} status={e.get('status','UNKNOWN')}; reconcile provider state first")
def _fsync_dir(p):
    fd=os.open(str(p),os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def arm_create_intent(fp,suffix):
    d=create_ledger_dir(); d.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:os.chmod(d,0o700)
    except OSError:pass
    p=create_ledger_path(fp); payload={"schema":"claycog-together-create-intent/v2","fingerprint":fp,"campaign_suffix":suffix,"status":"CREATE_ARMED","campaign":campaign_descriptor(),"created_unix":int(time.time())}; data=(json.dumps(payload,sort_keys=True,indent=2)+"\n").encode()
    try:fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:assert_no_local_create_intent(fp);raise
    with os.fdopen(fd,"wb",closefd=True) as f:f.write(data);f.flush();os.fsync(f.fileno())
    _fsync_dir(d);return p
def update_create_intent(p,status,job_id=None,error_class=None):
    payload=json.loads(Path(p).read_text());payload["status"]=status;payload["updated_unix"]=int(time.time())
    if job_id is not None:payload["job_id"]=str(job_id)
    if error_class is not None:payload["error_class"]=str(error_class)
    tmp=Path(str(p)+f".tmp.{os.getpid()}");fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb",closefd=True) as f:f.write((json.dumps(payload,sort_keys=True,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
        os.replace(tmp,p);_fsync_dir(Path(p).parent)
    finally:
        try:tmp.unlink()
        except OSError:pass
def new_zero_retry_create_client(cls): return cls(max_retries=0)
def _identity_observed(value,want):
    if isinstance(want,dict):
        return {key:_identity_observed(_field(value,key,None),child) for key,child in want.items()}
    return value
def created_job_identity_mismatches(meta,expected):
    out={}
    for key,want in expected.items():
        got=_identity_observed(_field(meta,key,None),want)
        if got!=want:out[key]={"expected":want,"observed":got}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--create",action="store_true");args=ap.parse_args();validate_static_contract();local_checks()
    assert_provider_execution_allowed()
    if not os.environ.get("TOGETHER_API_KEY"):raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    from together import Together
    client=Together();get_full_training_limits(client);fp=campaign_fingerprint();suffix=campaign_suffix(fp)
    if args.create:require_create_confirmation(fp);assert_no_local_create_intent(fp);assert_no_duplicate_campaign(client,suffix)
    tf=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True);vf=client.files.upload(file=str(VALID),purpose="fine-tune",check=True);wait_file(client,tf.id);wait_file(client,vf.id)
    est=estimate_price(client,tf.id,vf.id);price=float(est.estimated_total_price)
    print(json.dumps({"schema":"CLAYCOG_08B_TOGETHER_DIRECT_PREFLIGHT/v2","mode":"create" if args.create else "preflight","campaign_fingerprint":fp,"campaign_suffix":suffix,"model":MODEL,"random_seed":RANDOM_SEED,"learning_rate":LEARNING_RATE,"warmup_ratio":WARMUP_RATIO,"training_type":training_type(),"estimated_usd":price,"allowed_to_proceed":bool(est.allowed_to_proceed),"price_detail":objdict(est),"model_limits_full_ft":True,"byom_fields":"ABSENT_BY_DESIGN"},indent=2,default=str))
    if not est.allowed_to_proceed:raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD:raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fp} for this exact create");return
    assert_no_local_create_intent(fp);assert_no_duplicate_campaign(client,suffix);intent=arm_create_intent(fp,suffix);cc=new_zero_retry_create_client(Together)
    try:job=cc.fine_tuning.create(**create_payload(tf.id,vf.id,suffix))
    except Exception as e:update_create_intent(intent,"UNKNOWN_REMOTE_CREATE",error_class=type(e).__name__);raise SystemExit("CREATE_OUTCOME_UNKNOWN; do not retry until exact provider reconciliation") from e
    update_create_intent(intent,"JOB_KNOWN",job_id=job.id)
    expected={"training_file":tf.id,"validation_file":vf.id,"model":MODEL,"suffix":suffix,"n_epochs":EPOCHS,"n_evals":EVALS,"n_checkpoints":1,"random_seed":RANDOM_SEED,"learning_rate":LEARNING_RATE,"warmup_ratio":WARMUP_RATIO,"training_method":training_method(),"training_type":training_type()}
    try:meta=client.fine_tuning.retrieve(id=job.id)
    except Exception as e:raise SystemExit(f"JOB_CREATED_IDENTITY_VERIFY_UNAVAILABLE job_id={job.id}; inspect this exact job, do not create another: {type(e).__name__}") from e
    mismatches=created_job_identity_mismatches(meta,expected)
    if mismatches:raise SystemExit("JOB_CREATED_IDENTITY_MISMATCH job_id="+str(job.id)+" "+json.dumps(mismatches,sort_keys=True,default=str))
    print(json.dumps({"job_id":job.id,"campaign_fingerprint":fp,"model":MODEL,"estimated_usd":price,"local_create_intent":str(intent),"created_job_identity":"VERIFIED"},indent=2))
if __name__=="__main__":main()
