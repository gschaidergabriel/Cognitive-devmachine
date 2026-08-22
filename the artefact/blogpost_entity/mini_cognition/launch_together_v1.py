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
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
HF_REVISIONS={
    "Qwen/Qwen2.5-0.5B":os.environ.get("CLAYCOG_HF_REVISION","060db6499f32faf8b98477b0a26969ef7d8b9987"),
    "Qwen/Qwen2.5-0.5B-Instruct":os.environ.get("CLAYCOG_HF_INSTRUCT_REVISION","7ae557604adf67be50417f59c2c2f167def9a775"),
}
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
CREATE_CONFIRM_ENV="CLAYCOG_CREATE_FINGERPRINT"
HEX40=re.compile(r"^[0-9a-f]{40}$")
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

def hf_revision_for(hf_model):
    revision=str(HF_REVISIONS.get(hf_model,os.environ.get("CLAYCOG_HF_REVISION",""))).strip().lower()
    if not HEX40.fullmatch(revision):
        raise SystemExit(
            f"HF_REVISION_ABORT exact 40-hex revision required for {hf_model}; "
            "set CLAYCOG_HF_REVISION or CLAYCOG_HF_INSTRUCT_REVISION"
        )
    return revision

def campaign_descriptor(hf_model,hf_revision=None):
    if hf_revision is None: hf_revision=hf_revision_for(hf_model)
    return {
        "schema":"claycog-05b-together-campaign/v2",
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
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

def campaign_fingerprint(hf_model,hf_revision=None):
    raw=json.dumps(campaign_descriptor(hf_model,hf_revision),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
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

def matching_campaign_jobs(client,hf_model,hf_revision,template,suffix):
    """Return account jobs that appear to carry this deterministic campaign suffix.

    The suffix is derived from exact local dataset digests + HF revision + training
    configuration. Where Together exposes model/from_hf_model/revision, those fields
    must also match. Missing optional fields are tolerated across response versions.
    """
    matches=[]
    for job in _items(client.fine_tuning.list()):
        status=str(_field(job,"status","")).lower()
        if status and status not in ACTIVE_OR_SPENT_STATUSES:
            continue
        direct_suffix=str(_field(job,"suffix","") or "")
        output_name=str(_field(job,"model_output_name","") or "")
        if direct_suffix!=suffix and suffix not in output_name:
            continue
        model=_field(job,"model",None)
        from_hf=_field(job,"from_hf_model",None)
        revision=_field(job,"hf_model_revision",None)
        if model not in (None,"",template):
            continue
        if from_hf not in (None,"",hf_model):
            continue
        if revision not in (None,"",hf_revision):
            continue
        matches.append(job)
    return matches

def assert_no_duplicate_campaign(client,hf_model,hf_revision,template,suffix):
    matches=matching_campaign_jobs(client,hf_model,hf_revision,template,suffix)
    if matches:
        ids=[str(_field(x,"id","UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): "+",".join(ids))

def require_create_confirmation(fingerprint):
    supplied=os.environ.get(CREATE_CONFIRM_ENV,"")
    if supplied!=fingerprint:
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to the exact preflight fingerprint {fingerprint}"
        )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after exact-fingerprint preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    hf_revision=hf_revision_for(hf_model)

    run_local_checks()
    fingerprint=campaign_fingerprint(hf_model,hf_revision)
    suffix=campaign_suffix(fingerprint)

    # Keep Together import behind the credential/local-validation boundary so pure safety
    # tests can execute without the SDK and no network-capable object exists before checks.
    from together import Together
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    # On create, bind human/operator intent to exact deterministic bytes before remote
    # uploads, then check the account ledger before allocating new remote file objects.
    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_duplicate_campaign(client,hf_model,hf_revision,TEMPLATE,suffix)

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
        "hf_model_revision":hf_revision,
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

    # Close the check/use window: another process may have created this exact campaign
    # while files were being validated or price estimation was running.
    assert_no_duplicate_campaign(client,hf_model,hf_revision,TEMPLATE,suffix)

    job=client.fine_tuning.create(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TEMPLATE,
        from_hf_model=hf_model,
        hf_model_revision=hf_revision,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=1e-5,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        lora=False,
        suffix=suffix,
    )
    print(json.dumps({
        "job_id":job.id,
        "campaign_fingerprint":fingerprint,
        "campaign_suffix":suffix,
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":TEMPLATE,
        "full_fine_tune":True,
        "estimated_usd":price,
        "byom_compatibility_status":"CREATE_ACCEPTED_TRAINING_START_STILL_REQUIRED_FOR_PROMOTION",
        "next":"retrieve this exact job; never blind-retry create after an ambiguous transport outcome",
    },indent=2))

if __name__=="__main__": main()
