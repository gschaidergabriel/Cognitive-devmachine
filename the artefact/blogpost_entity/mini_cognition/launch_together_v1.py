#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, upload/validate files, check the
Together template, and request a BYOM-bound server price estimate. A billed training job
is created only with --create after all gates pass.

The Hugging Face checkpoint is revision-pinned so a later Hub update cannot silently change
the trained weights. The estimate and create requests share the same identity/training core.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
PRIMARY_MODEL="Qwen/Qwen2.5-0.5B"
PRIMARY_REVISION="060db6499f32faf8b98477b0a26969ef7d8b9987"
INSTRUCT_MODEL="Qwen/Qwen2.5-0.5B-Instruct"
INSTRUCT_REVISION="7ae557604adf67be50417f59c2c2f167def9a775"
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
LEARNING_RATE=float(os.environ.get("CLAYCOG_LEARNING_RATE","1e-5"))
WARMUP_RATIO=float(os.environ.get("CLAYCOG_WARMUP_RATIO","0.03"))
RANDOM_SEED=int(os.environ.get("CLAYCOG_RANDOM_SEED","20260822"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
SUFFIX=os.environ.get("CLAYCOG_SUFFIX","claycog_05b_v1")

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v1.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/"generate_eval_ood_v1.py")],check=True)

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
    return str(x)

def resolve_hf_checkpoint(instruct_ablation=False):
    if instruct_ablation:
        model=INSTRUCT_MODEL
        revision=os.environ.get("CLAYCOG_HF_INSTRUCT_REVISION",INSTRUCT_REVISION)
    else:
        model=os.environ.get("CLAYCOG_HF_MODEL",PRIMARY_MODEL)
        if model==PRIMARY_MODEL:
            revision=os.environ.get("CLAYCOG_HF_REVISION",PRIMARY_REVISION)
        else:
            revision=os.environ.get("CLAYCOG_HF_REVISION")
            if not revision:
                raise SystemExit("Custom CLAYCOG_HF_MODEL requires explicit CLAYCOG_HF_REVISION")
    if len(revision)!=40 or any(c not in "0123456789abcdefABCDEF" for c in revision):
        raise SystemExit("HF model revision must be an exact 40-hex commit SHA")
    return model,revision.lower()

def request_core(train_file_id,valid_file_id,hf_model,hf_revision):
    return {
        "training_file":train_file_id,
        "validation_file":valid_file_id,
        "model":TEMPLATE,
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "n_epochs":EPOCHS,
        "n_evals":EVALS,
        "learning_rate":LEARNING_RATE,
        "warmup_ratio":WARMUP_RATIO,
        "random_seed":RANDOM_SEED,
        "training_method":{"method":"sft","train_on_inputs":"auto"},
        "training_type":{"type":"Full"},
    }

def estimate_kwargs(core):
    return dict(core)

def create_kwargs(core):
    out=dict(core)
    out.update({"n_checkpoints":1,"suffix":SUFFIX})
    return out

def verify_created_job(meta,core):
    checks={
        "training_file":core["training_file"],
        "validation_file":core["validation_file"],
        "model":core["model"],
        "from_hf_model":core["from_hf_model"],
        "hf_model_revision":core["hf_model_revision"],
    }
    mismatches={}
    for key,want in checks.items():
        got=getattr(meta,key,None)
        if got!=want: mismatches[key]={"expected":want,"observed":got}
    return mismatches

def status_report(client,job_id):
    meta=client.fine_tuning.retrieve(id=job_id)
    keys=("id","status","model","from_hf_model","hf_model_revision","training_file","validation_file","n_epochs","n_evals","random_seed","total_price","model_output_name")
    return {k:getattr(meta,k,None) for k in keys}

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument("--create",action="store_true",help="create billed fine-tuning job after preflight")
    mode.add_argument("--status",metavar="JOB_ID",help="retrieve an existing job; never creates a duplicate")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    from together import Together
    client=Together()
    if args.status:
        print(json.dumps(status_report(client,args.status),indent=2,default=str))
        return

    hf_model,hf_revision=resolve_hf_checkpoint(args.instruct_ablation)
    run_local_checks()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    core=request_core(train_file.id,valid_file.id,hf_model,hf_revision)

    estimate=client.fine_tuning.estimate_price(**estimate_kwargs(core))
    price=float(estimate.estimated_total_price)
    report={
        "mode":"preflight" if not args.create else "create",
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":TEMPLATE,
        "epochs":EPOCHS,
        "evals":EVALS,
        "learning_rate":LEARNING_RATE,
        "warmup_ratio":WARMUP_RATIO,
        "random_seed":RANDOM_SEED,
        "estimated_usd":price,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),
        "compatibility_status":"BYOM_BOUND_ESTIMATE_ACCEPTED_TRAINING_COMPATIBILITY_NOT_YET_PROVEN",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this exact BYOM request")
    if price>MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created")
        return

    job=client.fine_tuning.create(**create_kwargs(core))
    meta=client.fine_tuning.retrieve(id=job.id)
    mismatches=verify_created_job(meta,core)
    created={
        "job_id":job.id,
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":TEMPLATE,
        "full_fine_tune":True,
        "random_seed":RANDOM_SEED,
        "estimated_usd":price,
        "created_job_identity_mismatches":mismatches,
        "next":"retrieve this exact job id; do not retry create blindly",
    }
    print(json.dumps(created,indent=2,default=str))
    if mismatches:
        raise SystemExit("CREATED_JOB_IDENTITY_MISMATCH: job exists; inspect it, do not create a replacement blindly")

if __name__=="__main__": main()
