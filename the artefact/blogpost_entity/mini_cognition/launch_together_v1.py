#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, upload/validate files, check the
Together template, and print a server price estimate. A billed training job is created
only with --create after all gates pass and the operator binds create authorization to
the exact deterministic campaign fingerprint.

Together's regular catalog has no native 0.5B Qwen entry. We therefore use BYOM with
Qwen/Qwen2.5-0.5B and a configurable Qwen2.5-family catalog-template candidate.
Template model_limits and price estimation do NOT prove BYOM compatibility because they
do not validate from_hf_model. BYOM compatibility remains open until Together accepts
(and subsequently starts) the requested HF checkpoint under the selected template.

Billed-create safety is deliberately stricter than ordinary API use. The CREATE call is
made through a zero-retry SDK client and is preceded by an atomic local campaign intent
record. If the remote outcome is ambiguous, the local record becomes
UNKNOWN_REMOTE_CREATE and subsequent --create attempts fail closed until an operator
reconciles the exact campaign against the provider account. Account-list duplicate
checks remain defense in depth; they are not treated as an exactly-once authority.
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV="CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT_STATUSES={"pending","queued","running","compressing","uploading","cancel_requested","cancelled","error","completed"}

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v1.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(VALID)],check=True)

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
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def campaign_descriptor(hf_model):
    return {
        "schema":"claycog-05b-together-campaign/v1",
        "from_hf_model":hf_model,
        "template_model":TEMPLATE,
        "training_sha256":sha256_file(TRAIN),
        "validation_sha256":sha256_file(VALID),
        "epochs":EPOCHS,
        "evals":EVALS,
        "training_method":"sft",
        "training_type":"Full",
        "train_on_inputs":"auto",
        "learning_rate":1e-5,
        "warmup_ratio":0.03,
        "n_checkpoints":1,
    }

def campaign_fingerprint(hf_model):
    raw=json.dumps(campaign_descriptor(hf_model),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def campaign_suffix(fingerprint):
    # 96 bits of the campaign digest are enough for collision-resistant account lookup,
    # while the full 256-bit digest remains the operator confirmation value.
    return "claycog05b-"+fingerprint[:24]

def _items(x):
    if x is None: return []
    if hasattr(x,"data"): return list(x.data or [])
    if isinstance(x,dict): return list(x.get("data") or [])
    return list(x) if isinstance(x,(list,tuple)) else []

def _field(x,name,default=None):
    if isinstance(x,dict): return x.get(name,default)
    return getattr(x,name,default)

def matching_campaign_jobs(client,hf_model,template,suffix):
    """Return account jobs that appear to carry this deterministic campaign suffix.

    The suffix is derived from exact local dataset digests + training configuration.
    Where Together exposes model/from_hf_model, those fields must also match. Missing
    optional fields are tolerated so the guard remains useful across response versions.
    """
    matches=[]
    for job in _items(client.fine_tuning.list()):
        status=str(_field(job,"status","")).lower()
        if status and status not in ACTIVE_OR_SPENT_STATUSES:
            continue
        output_name=str(_field(job,"model_output_name","") or "")
        if suffix not in output_name:
            continue
        model=_field(job,"model",None)
        from_hf=_field(job,"from_hf_model",None)
        if model not in (None,"",template):
            continue
        if from_hf not in (None,"",hf_model):
            continue
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
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to the exact preflight fingerprint {fingerprint}"
        )

def create_ledger_dir():
    configured=os.environ.get(CREATE_LEDGER_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home()/".local"/"state"/"claycog"/"training"

def create_ledger_path(fingerprint):
    return create_ledger_dir()/(fingerprint+".json")

def read_create_ledger(fingerprint):
    path=create_ledger_path(fingerprint)
    if not path.exists(): return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"CREATE_LEDGER_UNREADABLE {path}: {exc}")

def assert_no_local_create_intent(fingerprint):
    existing=read_create_ledger(fingerprint)
    if existing is None: return
    status=str(existing.get("status","UNKNOWN"))
    job_id=existing.get("job_id")
    suffix=f" job_id={job_id}" if job_id else ""
    raise SystemExit(
        f"LOCAL_CREATE_INTENT_ABORT fingerprint={fingerprint} status={status}{suffix}; "
        "reconcile exact provider state before any new billed create"
    )

def _fsync_dir(path):
    fd=os.open(str(path),os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def arm_create_intent(fingerprint,hf_model,suffix):
    """Atomically reserve this exact paid campaign locally before the remote POST.

    O_EXCL makes concurrent local launchers mutually exclusive. The record intentionally
    contains no API key/token. A process crash after this point therefore fails closed:
    the next invocation sees CREATE_ARMED rather than guessing that no remote effect ran.
    """
    directory=create_ledger_dir()
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    try: os.chmod(directory,0o700)
    except OSError: pass
    path=create_ledger_path(fingerprint)
    payload={
        "schema":"claycog-together-create-intent/v1",
        "fingerprint":fingerprint,
        "campaign_suffix":suffix,
        "status":"CREATE_ARMED",
        "campaign":campaign_descriptor(hf_model),
        "created_unix":int(time.time()),
    }
    data=(json.dumps(payload,sort_keys=True,indent=2)+"\n").encode("utf-8")
    try:
        fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        assert_no_local_create_intent(fingerprint)
        raise
    try:
        with os.fdopen(fd,"wb",closefd=True) as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        _fsync_dir(directory)
    except BaseException:
        try: os.unlink(path)
        except OSError: pass
        raise
    return path

def update_create_intent(path,status,job_id=None,error_class=None):
    """Durably advance the local intent without ever erasing ambiguity."""
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    payload["status"]=status
    payload["updated_unix"]=int(time.time())
    if job_id is not None: payload["job_id"]=str(job_id)
    if error_class is not None: payload["error_class"]=str(error_class)
    tmp=Path(str(path)+f".tmp.{os.getpid()}")
    data=(json.dumps(payload,sort_keys=True,indent=2)+"\n").encode("utf-8")
    fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb",closefd=True) as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
        _fsync_dir(Path(path).parent)
    finally:
        try: tmp.unlink()
        except OSError: pass

def new_zero_retry_create_client(together_cls):
    """A billed non-idempotent CREATE must not inherit SDK automatic retries."""
    return together_cls(max_retries=0)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after exact-fingerprint preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL

    run_local_checks()
    fingerprint=campaign_fingerprint(hf_model)
    suffix=campaign_suffix(fingerprint)

    # Keep Together import behind the credential/local-validation boundary so pure safety
    # tests can execute without the SDK and no network-capable object exists before checks.
    from together import Together
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    # On create, bind human/operator intent to exact deterministic bytes before remote
    # uploads, then check both local and account ledgers before allocating remote files.
    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_local_create_intent(fingerprint)
        assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)

    estimate=client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TEMPLATE,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method":"sft","train_on_inputs":"auto"},
        training_type={"type":"Full"},
    )
    price=float(estimate.estimated_total_price)
    report={
        "mode":"preflight" if not args.create else "create",
        "campaign_fingerprint":fingerprint,
        "campaign_suffix":suffix,
        "from_hf_model":hf_model,
        "template_model":TEMPLATE,
        "epochs":EPOCHS,
        "evals":EVALS,
        "estimated_usd":price,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),
        "template_admission_status":"MODEL_LIMITS_FULL_FT_ACCEPTED",
        "byom_compatibility_status":"UNPROVEN_UNTIL_CREATE_ACCEPTS_FROM_HF_MODEL_AND_TRAINING_STARTS",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} for the exact create")
        return

    # Close the check/use window, then reserve the exact paid campaign locally immediately
    # before the non-idempotent remote POST. Any crash/timeout after arming stays unknown.
    assert_no_local_create_intent(fingerprint)
    assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)
    intent_path=arm_create_intent(fingerprint,hf_model,suffix)
    create_client=new_zero_retry_create_client(Together)
    try:
        job=create_client.fine_tuning.create(
            training_file=train_file.id,
            validation_file=valid_file.id,
            model=TEMPLATE,
            from_hf_model=hf_model,
            n_epochs=EPOCHS,
            n_evals=EVALS,
            n_checkpoints=1,
            learning_rate=1e-5,
            warmup_ratio=0.03,
            train_on_inputs="auto",
            lora=False,
            suffix=suffix,
        )
    except Exception as exc:
        update_create_intent(intent_path,"UNKNOWN_REMOTE_CREATE",error_class=type(exc).__name__)
        raise SystemExit(
            "CREATE_OUTCOME_UNKNOWN local intent retained; do not retry create until exact provider reconciliation: "
            +type(exc).__name__
        ) from exc
    update_create_intent(intent_path,"JOB_KNOWN",job_id=job.id)
    print(json.dumps({
        "job_id":job.id,
        "campaign_fingerprint":fingerprint,
        "campaign_suffix":suffix,
        "from_hf_model":hf_model,
        "template_model":TEMPLATE,
        "full_fine_tune":True,
        "estimated_usd":price,
        "local_create_intent":str(intent_path),
        "byom_compatibility_status":"CREATE_ACCEPTED_TRAINING_START_STILL_REQUIRED_FOR_PROMOTION",
        "next":"retrieve this exact job; never blind-retry create after an ambiguous transport outcome",
    },indent=2))

if __name__=="__main__": main()
