#!/usr/bin/env python3
"""Together BYOM launcher for the generic 0.5B ClayCode cognition campaign.

Default mode is preflight. A billed create requires all of:
- exact deterministic local corpus validation;
- an explicitly selected current Together template (no stale hard-coded fallback);
- an architecture claim compatible with Qwen2/Qwen2.5;
- exact Hugging Face checkpoint revision binding;
- server file validation and price estimate under the owner budget ceiling;
- exact campaign-fingerprint confirmation;
- no already-observed account job carrying the same campaign fingerprint.

Together's price/model-limit endpoints validate the template and dataset, not the
`from_hf_model` checkpoint pair. BYOM compatibility therefore remains OPEN until
Together accepts the exact create pair; training start/completion are later evidence.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
PRIMARY_HF_MODEL="Qwen/Qwen2.5-0.5B"
PRIMARY_HF_REVISION="060db6499f32faf8b98477b0a26969ef7d8b9987"
INSTRUCT_HF_MODEL="Qwen/Qwen2.5-0.5B-Instruct"
INSTRUCT_HF_REVISION="7ae557604adf67be50417f59c2c2f167def9a775"
EXPECTED_ARCH="qwen2"
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","").strip()
TEMPLATE_ARCH=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE_ARCH","").strip().lower()
TEMPLATE_PARAMS_B=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B","").strip()
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"
SEEN_JOB_STATUSES={"pending","queued","running","compressing","uploading","cancel_requested","cancelled","canceled","error","failed","completed","done","succeeded"}

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v1.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/"generate_eval_ood_v1.py")],check=True)

def exact_revision(model, revision_env, default_model, default_revision):
    revision=os.environ.get(revision_env,"").strip()
    if not revision:
        if model!=default_model:
            raise SystemExit(f"{revision_env} is required when overriding {default_model} with {model}")
        revision=default_revision
    if not re.fullmatch(r"[0-9a-fA-F]{40}",revision):
        raise SystemExit(f"{revision_env} must be an exact 40-hex Hugging Face commit SHA")
    return revision.lower()

def resolve_hf_source(instruct_ablation):
    if instruct_ablation:
        model=os.environ.get("CLAYCOG_INSTRUCT_HF_MODEL",INSTRUCT_HF_MODEL).strip()
        revision=exact_revision(model,"CLAYCOG_INSTRUCT_HF_REVISION",INSTRUCT_HF_MODEL,INSTRUCT_HF_REVISION)
    else:
        model=os.environ.get("CLAYCOG_HF_MODEL",PRIMARY_HF_MODEL).strip()
        revision=exact_revision(model,"CLAYCOG_HF_REVISION",PRIMARY_HF_MODEL,PRIMARY_HF_REVISION)
    return model,revision

def require_template_claim():
    """Fail before remote upload if current template selection is not explicit.

    The metadata is an operator-side admission assertion, not proof. Together's authenticated
    API remains authoritative and can still reject the BYOM pair.
    """
    if not TEMPLATE:
        raise SystemExit("BYOM_TEMPLATE_UNRESOLVED: set CLAYCOG_TOGETHER_TEMPLATE after current Together catalog/API review; the former hard-coded Qwen2.5-7B fallback is disabled")
    if not TEMPLATE_ARCH:
        raise SystemExit("TEMPLATE_ARCH_REQUIRED: set CLAYCOG_TOGETHER_TEMPLATE_ARCH from current template metadata")
    if TEMPLATE_ARCH!=EXPECTED_ARCH:
        raise SystemExit(f"BYOM_ARCH_MISMATCH: checkpoint={EXPECTED_ARCH} template_claim={TEMPLATE_ARCH} template={TEMPLATE}")
    if not TEMPLATE_PARAMS_B:
        raise SystemExit("TEMPLATE_SIZE_REQUIRED: set CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B from current template metadata")
    try: params=float(TEMPLATE_PARAMS_B)
    except ValueError: raise SystemExit("CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B must be numeric")
    if params<=0: raise SystemExit("CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B must be > 0")
    return params

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

def campaign_descriptor(hf_model,hf_revision,template_params_b):
    return {
        "schema":"claycog-05b-together-campaign/v2",
        "from_hf_model":hf_model,"hf_model_revision":hf_revision,
        "template_model":TEMPLATE,"template_arch_claim":TEMPLATE_ARCH,
        "template_params_b_claim":template_params_b,
        "training_sha256":sha256_file(TRAIN),"validation_sha256":sha256_file(VALID),
        "epochs":EPOCHS,"evals":EVALS,"training_method":"sft","training_type":"Full",
        "train_on_inputs":"auto","learning_rate":1e-5,"warmup_ratio":0.03,"n_checkpoints":1,
    }

def campaign_fingerprint(hf_model,hf_revision,template_params_b):
    raw=json.dumps(campaign_descriptor(hf_model,hf_revision,template_params_b),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
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
        if status and status not in SEEN_JOB_STATUSES:
            pass
        output_name=str(_field(job,"model_output_name","") or "")
        job_suffix=str(_field(job,"suffix","") or "")
        if suffix not in output_name and suffix!=job_suffix: continue
        model=_field(job,"model",None); from_hf=_field(job,"from_hf_model",None)
        if model not in (None,"",template): continue
        if from_hf not in (None,"",hf_model): continue
        matches.append(job)
    return matches

def assert_no_duplicate_campaign(client,hf_model,template,suffix):
    matches=matching_campaign_jobs(client,hf_model,template,suffix)
    if matches:
        ids=[str(_field(x,"id","UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing same-fingerprint job(s): "+",".join(ids))

def require_create_confirmation(fingerprint):
    supplied=os.environ.get(CREATE_CONFIRM_ENV,"").strip()
    if supplied!=fingerprint:
        raise SystemExit(f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV}={fingerprint} after reviewing this exact preflight")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after exact-fingerprint preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model,hf_revision=resolve_hf_source(args.instruct_ablation)
    run_local_checks()
    template_params_b=require_template_claim()
    fingerprint=campaign_fingerprint(hf_model,hf_revision,template_params_b)
    suffix=campaign_suffix(fingerprint)

    from together import Together
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")
    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(
        training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,
        n_epochs=EPOCHS,n_evals=EVALS,
        training_method={"method":"sft","train_on_inputs":"auto"},training_type={"type":"Full"})
    price=float(estimate.estimated_total_price)
    report={
        "mode":"preflight" if not args.create else "create","campaign_fingerprint":fingerprint,
        "campaign_suffix":suffix,"from_hf_model":hf_model,"hf_model_revision":hf_revision,
        "template_model":TEMPLATE,"template_arch_claim":TEMPLATE_ARCH,"template_params_b_claim":template_params_b,
        "epochs":EPOCHS,"evals":EVALS,"estimated_usd":price,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),"price_detail":objdict(estimate),
        "template_admission_status":"MODEL_LIMITS_FULL_FT_ACCEPTED",
        "byom_compatibility_status":"UNPROVEN_PRICE_ESTIMATE_DOES_NOT_BIND_FROM_HF_MODEL",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD: raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} only after reviewing template compatibility and price")
        return
    assert_no_duplicate_campaign(client,hf_model,TEMPLATE,suffix)
    job=client.fine_tuning.create(
        training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,
        from_hf_model=hf_model,hf_model_revision=hf_revision,
        n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,
        train_on_inputs="auto",lora=False,suffix=suffix)
    print(json.dumps({
        "job_id":job.id,"campaign_fingerprint":fingerprint,"campaign_suffix":suffix,
        "from_hf_model":hf_model,"hf_model_revision":hf_revision,"template_model":TEMPLATE,
        "full_fine_tune":True,"estimated_usd":price,
        "byom_compatibility_status":"CREATE_ACCEPTED_TRAINING_START_STILL_REQUIRED",
        "next":"retrieve this exact job; never blind-retry create after ambiguous transport outcome",
    },indent=2))

if __name__=="__main__": main()
