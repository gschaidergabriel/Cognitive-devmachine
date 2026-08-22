#!/usr/bin/env python3
"""Together BYOM launcher for the generic 0.5B ClayCode cognition campaign.

Default mode is preflight. Billed create is bound to an exact campaign fingerprint,
an account-side deterministic suffix, and a local exclusive create-intent ledger.
BYOM compatibility remains OPEN until Together accepts the exact from_hf_model pair
and the resulting job reaches training.
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v2.jsonl"
VALID=HERE/"validation_v2.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV="CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT_STATUSES={"pending","queued","running","compressing","uploading","cancel_requested","cancelled","error","completed"}


def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/"corpus_split_gate_v2.py"),str(TRAIN),str(VALID)],check=True)


def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id)
        status=str(meta.processing_status)
        if status=="COMPLETED": return meta
        if status in ("INVALID_FORMAT","FAILED"):
            raise RuntimeError(f"Together rejected {file_id}: {status} {getattr(meta,'validation_report',None)}")
        time.sleep(5)


def objdict(x):
    if hasattr(x,"model_dump"): return x.model_dump()
    if hasattr(x,"dict"): return x.dict()
    if isinstance(x,dict): return x
    return str(x)


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def campaign_descriptor(hf_model):
    return {
        "schema":"claycog-05b-together-campaign/v2",
        "from_hf_model":hf_model,
        "template_model":TEMPLATE,
        "training_sha256":sha256_file(TRAIN),
        "validation_sha256":sha256_file(VALID),
        "epochs":EPOCHS,"evals":EVALS,
        "training_method":"sft","training_type":"Full","train_on_inputs":"auto",
        "learning_rate":1e-5,"warmup_ratio":0.03,"n_checkpoints":1,
    }


def campaign_fingerprint(hf_model):
    raw=json.dumps(campaign_descriptor(hf_model),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def campaign_suffix(fingerprint): return "claycog05b-"+fingerprint[:24]


def _items(x):
    if x is None: return []
    if hasattr(x,"data"): return list(x.data or [])
    if isinstance(x,dict): return list(x.get("data") or [])
    return list(x) if isinstance(x,(list,tuple)) else []


def _field(x,name,default=None):
    if isinstance(x,dict): return x.get(name,default)
    return getattr(x,name,default)


def matching_campaign_jobs(client,hf_model,template,suffix):
    matches=[]
    for job in _items(client.fine_tuning.list()):
        status=str(_field(job,"status","")).lower()
        if status and status not in ACTIVE_OR_SPENT_STATUSES: continue
        output_name=str(_field(job,"model_output_name","") or "")
        if suffix not in output_name: continue
        model=_field(job,"model",None); from_hf=_field(job,"from_hf_model",None)
        if model not in (None,"",template): continue
        if from_hf not in (None,"",hf_model): continue
        matches.append(job)
    return matches


def assert_no_duplicate_campaign(client,hf_model,template,suffix):
    matches=matching_campaign_jobs(client,hf_model,template,suffix)
    if matches:
        ids=[str(_field(x,"id","UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): "+",".join(ids))


def require_create_confirmation(fingerprint):
    supplied=os.environ.get(CREATE_CONFIRM_ENV,"")
    if supplied!=fingerprint:
        raise SystemExit(f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to exact preflight fingerprint {fingerprint}")


def ledger_dir():
    root=Path(os.environ.get(CREATE_LEDGER_DIR_ENV,str(Path.home()/".claycog"/"together_create_ledger")))
    root.mkdir(parents=True,exist_ok=True)
    try: root.chmod(0o700)
    except OSError: pass
    return root


def ledger_path(fingerprint): return ledger_dir()/(fingerprint+".json")


def read_create_ledger(fingerprint):
    path=ledger_path(fingerprint)
    if not path.exists(): return None
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_local_create_intent(fingerprint):
    payload=read_create_ledger(fingerprint)
    if payload is not None:
        raise SystemExit(
            "LOCAL_CREATE_INTENT_BLOCK status="+str(payload.get("status"))+"; reconcile exact provider state before any retry: "+str(ledger_path(fingerprint))
        )


def _write_ledger_fd(fd,payload):
    raw=(json.dumps(payload,indent=2,sort_keys=True)+"\n").encode("utf-8")
    with os.fdopen(fd,"wb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())


def arm_create_intent(fingerprint,hf_model,suffix):
    path=ledger_path(fingerprint)
    payload={
        "schema":"claycog-together-create-intent/v1",
        "fingerprint":fingerprint,
        "campaign_suffix":suffix,
        "from_hf_model":hf_model,
        "template_model":TEMPLATE,
        "status":"CREATE_ARMED",
        "training_sha256":sha256_file(TRAIN),
        "validation_sha256":sha256_file(VALID),
        "rule":"Never remove this ledger merely to retry. Reconcile exact Together account state first.",
    }
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    try: fd=os.open(path,flags,0o600)
    except FileExistsError:
        raise SystemExit("LOCAL_CREATE_INTENT_EXISTS: "+str(path))
    _write_ledger_fd(fd,payload)
    return path


def update_create_intent(path,status,job_id=None,error_class=None):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    payload["status"]=status
    if job_id is not None: payload["job_id"]=str(job_id)
    if error_class is not None: payload["error_class"]=str(error_class)
    tmp=Path(str(path)+".tmp")
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    _write_ledger_fd(fd,payload); os.replace(tmp,path)
    return payload


def new_zero_retry_create_client(constructor): return constructor(max_retries=0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create one billed fine-tuning job after exact-fingerprint preflight")
    ap.add_argument("--instruct-ablation",action="store_true")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL

    run_local_checks()
    fingerprint=campaign_fingerprint(hf_model); suffix=campaign_suffix(fingerprint)
    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_local_create_intent(fingerprint)

    from together import Together
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")
    if args.create: assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(
        training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,n_epochs=EPOCHS,n_evals=EVALS,
        training_method={"method":"sft","train_on_inputs":"auto"},training_type={"type":"Full"},
    )
    price=float(estimate.estimated_total_price)
    report={
        "mode":"preflight" if not args.create else "create","campaign_fingerprint":fingerprint,"campaign_suffix":suffix,
        "from_hf_model":hf_model,"template_model":TEMPLATE,"corpus_schema":"claycog-sft/v2",
        "training_sha256":sha256_file(TRAIN),"validation_sha256":sha256_file(VALID),
        "epochs":EPOCHS,"evals":EVALS,"estimated_usd":price,"allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),"template_admission_status":"MODEL_LIMITS_FULL_FT_ACCEPTED",
        "byom_compatibility_status":"UNPROVEN_UNTIL_CREATE_ACCEPTS_FROM_HF_MODEL_AND_TRAINING_STARTS",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD: raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} for the exact create")
        return

    assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)
    assert_no_local_create_intent(fingerprint)
    intent=arm_create_intent(fingerprint,hf_model,suffix)
    create_client=new_zero_retry_create_client(Together)
    try:
        job=create_client.fine_tuning.create(
            training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,from_hf_model=hf_model,
            n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,
            train_on_inputs="auto",lora=False,suffix=suffix,
        )
        job_id=getattr(job,"id",None)
        if not job_id:
            update_create_intent(intent,"UNKNOWN_REMOTE_CREATE",error_class="MissingJobId")
            raise RuntimeError("Together create returned no job id; reconcile provider state before retry")
        update_create_intent(intent,"JOB_KNOWN",job_id=job_id)
    except BaseException as exc:
        current=read_create_ledger(fingerprint) or {}
        if current.get("status")=="CREATE_ARMED": update_create_intent(intent,"UNKNOWN_REMOTE_CREATE",error_class=type(exc).__name__)
        raise
    print(json.dumps({
        "job_id":job_id,"campaign_fingerprint":fingerprint,"campaign_suffix":suffix,"from_hf_model":hf_model,
        "template_model":TEMPLATE,"full_fine_tune":True,"estimated_usd":price,
        "byom_compatibility_status":"CREATE_ACCEPTED_TRAINING_START_STILL_REQUIRED_FOR_PROMOTION",
        "local_create_ledger":str(intent),"next":"retrieve exact job; never blind-retry create",
    },indent=2))

if __name__=="__main__": main()
