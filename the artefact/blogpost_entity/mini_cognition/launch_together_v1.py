#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Uses leakage-free SFT v2. Billed create is bound to exact dataset bytes, training config,
HF model and exact HF revision; create is zero-retry and protected by the existing local
intent ledger. Together BYOM compatibility remains open until the exact pair is accepted
and the job reaches training.

Current public Together fine-tuning documentation checked 2026-08-22 exposes no Qwen2/
Qwen2.5 Full-FT base. Therefore there is deliberately no implicit training template.
The operator must name a currently verified Qwen2-compatible template explicitly; a
Qwen3-family substitution is rejected locally because it changes model architecture.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v2.jsonl"
VALID=HERE/"validation_v2.jsonl"
PRIMARY_HF_MODEL="Qwen/Qwen2.5-0.5B"
PRIMARY_HF_REVISION="060db6499f32faf8b98477b0a26969ef7d8b9987"
INSTRUCT_HF_MODEL="Qwen/Qwen2.5-0.5B-Instruct"
INSTRUCT_HF_REVISION="7ae557604adf67be50417f59c2c2f167def9a775"
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","").strip()
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3")); EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"; CREATE_LEDGER_DIR_ENV="CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT_STATUSES={"pending","queued","running","compressing","uploading","cancel_requested","cancelled","error","completed"}

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_corpus_v2.py"),str(TRAIN),str(VALID)],check=True)

def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id); status=str(meta.processing_status)
        if status=="COMPLETED": return meta
        if status in ("INVALID_FORMAT","FAILED"): raise RuntimeError(f"Together rejected {file_id}: {status} {getattr(meta,'validation_report',None)}")
        time.sleep(5)

def objdict(x):
    if hasattr(x,"model_dump"): return x.model_dump()
    if hasattr(x,"dict"): return x.dict()
    if isinstance(x,dict): return x
    return str(x)

def resolve_template():
    template=TEMPLATE.strip()
    if not template:
        raise SystemExit(
            "TOGETHER_TEMPLATE_BLOCKED: no implicit template is admitted. Current public Together fine-tuning "
            "documentation lists no Qwen2/Qwen2.5 Full-FT base; set CLAYCOG_TOGETHER_TEMPLATE only after "
            "current verification of a Qwen2-compatible training template."
        )
    if "qwen3" in template.lower():
        raise SystemExit(
            f"ARCHITECTURE_ABORT: {template} is a Qwen3-family template while the owner-required checkpoint "
            "is Qwen2/Qwen2.5. Do not change architecture family to bypass BYOM admission."
        )
    return template

def exact_revision(model,revision_env,default_model,default_revision):
    revision=os.environ.get(revision_env,"").strip()
    if not revision:
        if model!=default_model: raise SystemExit(f"{revision_env} is required when overriding {default_model} with {model}")
        revision=default_revision
    if not re.fullmatch(r"[0-9a-fA-F]{40}",revision): raise SystemExit(f"{revision_env} must be an exact 40-hex Hugging Face commit SHA")
    return revision.lower()

def resolve_hf_source(instruct_ablation):
    if instruct_ablation:
        model=os.environ.get("CLAYCOG_INSTRUCT_HF_MODEL",INSTRUCT_HF_MODEL)
        return model,exact_revision(model,"CLAYCOG_INSTRUCT_HF_REVISION",INSTRUCT_HF_MODEL,INSTRUCT_HF_REVISION)
    model=os.environ.get("CLAYCOG_HF_MODEL",PRIMARY_HF_MODEL)
    return model,exact_revision(model,"CLAYCOG_HF_REVISION",PRIMARY_HF_MODEL,PRIMARY_HF_REVISION)

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def campaign_descriptor(hf_model,hf_revision):
    return {"schema":"claycog-05b-together-campaign/v1","from_hf_model":hf_model,"hf_model_revision":hf_revision,"template_model":TEMPLATE,"training_sha256":sha256_file(TRAIN),"validation_sha256":sha256_file(VALID),"epochs":EPOCHS,"evals":EVALS,"training_method":"sft","training_type":"Full","train_on_inputs":"auto","learning_rate":1e-5,"warmup_ratio":0.03,"n_checkpoints":1}

def campaign_fingerprint(hf_model,hf_revision):
    raw=json.dumps(campaign_descriptor(hf_model,hf_revision),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def campaign_suffix(fingerprint): return "claycog05b-"+fingerprint[:24]
def _items(x):
    if x is None:return []
    if hasattr(x,"data"):return list(x.data or [])
    if isinstance(x,dict):return list(x.get("data") or [])
    return list(x) if isinstance(x,(list,tuple)) else []
def _field(x,name,default=None): return x.get(name,default) if isinstance(x,dict) else getattr(x,name,default)
def matching_campaign_jobs(client,hf_model,template,suffix):
    matches=[]
    for job in _items(client.fine_tuning.list()):
        status=str(_field(job,"status","")).lower(); output_name=str(_field(job,"model_output_name","") or "")
        if status and status not in ACTIVE_OR_SPENT_STATUSES: continue
        if suffix not in output_name: continue
        if _field(job,"model",None) not in (None,"",template): continue
        if _field(job,"from_hf_model",None) not in (None,"",hf_model): continue
        matches.append(job)
    return matches
def assert_no_duplicate_campaign(client,hf_model,template,suffix):
    matches=matching_campaign_jobs(client,hf_model,template,suffix)
    if matches: raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): "+",".join(str(_field(x,"id","UNKNOWN")) for x in matches))
def require_create_confirmation(fingerprint):
    if os.environ.get(CREATE_CONFIRM_ENV,"")!=fingerprint: raise SystemExit(f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to the exact preflight fingerprint {fingerprint}")
def create_ledger_dir(): return Path(os.environ[CREATE_LEDGER_DIR_ENV]).expanduser() if os.environ.get(CREATE_LEDGER_DIR_ENV) else Path.home()/".local"/"state"/"claycog"/"training"
def create_ledger_path(fingerprint): return create_ledger_dir()/(fingerprint+".json")
def read_create_ledger(fingerprint):
    path=create_ledger_path(fingerprint)
    if not path.exists(): return None
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: raise SystemExit(f"CREATE_LEDGER_UNREADABLE {path}: {exc}")
def assert_no_local_create_intent(fingerprint):
    existing=read_create_ledger(fingerprint)
    if existing is None:return
    status=str(existing.get("status","UNKNOWN")); job_id=existing.get("job_id"); suffix=f" job_id={job_id}" if job_id else ""
    raise SystemExit(f"LOCAL_CREATE_INTENT_ABORT fingerprint={fingerprint} status={status}{suffix}; reconcile exact provider state before any new billed create")
def _fsync_dir(path):
    fd=os.open(str(path),os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def arm_create_intent(fingerprint,hf_model,hf_revision,suffix):
    directory=create_ledger_dir(); directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:os.chmod(directory,0o700)
    except OSError:pass
    path=create_ledger_path(fingerprint); payload={"schema":"claycog-together-create-intent/v1","fingerprint":fingerprint,"campaign_suffix":suffix,"status":"CREATE_ARMED","campaign":campaign_descriptor(hf_model,hf_revision),"created_unix":int(time.time())}; data=(json.dumps(payload,sort_keys=True,indent=2)+"\n").encode()
    try:fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError: assert_no_local_create_intent(fingerprint); raise
    try:
        with os.fdopen(fd,"wb",closefd=True) as f:f.write(data);f.flush();os.fsync(f.fileno())
        _fsync_dir(directory)
    except BaseException:
        try:os.unlink(path)
        except OSError:pass
        raise
    return path
def update_create_intent(path,status,job_id=None,error_class=None):
    payload=json.loads(Path(path).read_text()); payload["status"]=status; payload["updated_unix"]=int(time.time())
    if job_id is not None:payload["job_id"]=str(job_id)
    if error_class is not None:payload["error_class"]=str(error_class)
    tmp=Path(str(path)+f".tmp.{os.getpid()}"); fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb",closefd=True) as f:f.write((json.dumps(payload,sort_keys=True,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
        os.replace(tmp,path);_fsync_dir(Path(path).parent)
    finally:
        try:tmp.unlink()
        except OSError:pass
def new_zero_retry_create_client(together_cls): return together_cls(max_retries=0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--create",action="store_true");ap.add_argument("--instruct-ablation",action="store_true");args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    template=resolve_template();hf_model,hf_revision=resolve_hf_source(args.instruct_ablation);run_local_checks();fingerprint=campaign_fingerprint(hf_model,hf_revision);suffix=campaign_suffix(fingerprint)
    from together import Together
    client=Together();limits=client.fine_tuning.model_limits(model_name=template)
    if not getattr(limits,"supports_full_training",False):raise SystemExit(f"Template is not full-FT capable: {template}")
    if args.create:require_create_confirmation(fingerprint);assert_no_local_create_intent(fingerprint);assert_no_duplicate_campaign(client,hf_model,template,suffix)
    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True);valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True);wait_file(client,train_file.id);wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(training_file=train_file.id,validation_file=valid_file.id,model=template,n_epochs=EPOCHS,n_evals=EVALS,training_method={"method":"sft","train_on_inputs":"auto"},training_type={"type":"Full"});price=float(estimate.estimated_total_price)
    report={"mode":"preflight" if not args.create else "create","campaign_fingerprint":fingerprint,"campaign_suffix":suffix,"from_hf_model":hf_model,"hf_model_revision":hf_revision,"template_model":template,"epochs":EPOCHS,"evals":EVALS,"estimated_usd":price,"allowed_to_proceed":bool(estimate.allowed_to_proceed),"price_detail":objdict(estimate),"template_admission_status":"MODEL_LIMITS_FULL_FT_ACCEPTED","byom_compatibility_status":"UNPROVEN_UNTIL_CREATE_ACCEPTS_FROM_HF_MODEL_AND_TRAINING_STARTS"};print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed:raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD:raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} for the exact create");return
    assert_no_local_create_intent(fingerprint);assert_no_duplicate_campaign(client,hf_model,template,suffix);intent_path=arm_create_intent(fingerprint,hf_model,hf_revision,suffix);create_client=new_zero_retry_create_client(Together)
    try:job=create_client.fine_tuning.create(training_file=train_file.id,validation_file=valid_file.id,model=template,from_hf_model=hf_model,hf_model_revision=hf_revision,n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,train_on_inputs="auto",lora=False,suffix=suffix)
    except Exception as exc:update_create_intent(intent_path,"UNKNOWN_REMOTE_CREATE",error_class=type(exc).__name__);raise SystemExit("CREATE_OUTCOME_UNKNOWN local intent retained; do not retry create until exact provider reconciliation: "+type(exc).__name__) from exc
    update_create_intent(intent_path,"JOB_KNOWN",job_id=job.id);print(json.dumps({"job_id":job.id,"campaign_fingerprint":fingerprint,"campaign_suffix":suffix,"from_hf_model":hf_model,"hf_model_revision":hf_revision,"template_model":template,"full_fine_tune":True,"estimated_usd":price,"local_create_intent":str(intent_path),"byom_compatibility_status":"CREATE_ACCEPTED_TRAINING_START_STILL_REQUIRED_FOR_PROMOTION","next":"retrieve this exact job; never blind-retry create after an ambiguous transport outcome"},indent=2))
if __name__=="__main__":main()
