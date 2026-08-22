#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, upload/validate files, check the
Together template, and print a server price estimate. A billed training job is created
only with --create after all gates pass.

Together's current regular fine-tuning catalog has no native 0.5B Qwen entry. We therefore
use BYOM with Qwen/Qwen2.5-0.5B and a configurable Qwen2.5-family template candidate.
Compatibility is an empirical API gate; a template/checkpoint mismatch must fail closed.
We do not silently fall back to Qwen3.5 because the current Qwen3.5 checkpoints expose a
different architecture family from Qwen2.5.

BYOM source revisions are pinned to exact Hugging Face commit SHAs. A custom model override
must provide its own explicit 40-hex revision; a moving repository main is never admitted
for a billed create.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
PRIMARY_HF_MODEL="Qwen/Qwen2.5-0.5B"
PRIMARY_HF_REVISION="060db6499f32faf8b98477b0a26969ef7d8b9987"
INSTRUCT_HF_MODEL="Qwen/Qwen2.5-0.5B-Instruct"
INSTRUCT_HF_REVISION="7ae557604adf67be50417f59c2c2f167def9a775"
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))

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
    return str(x)

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
        model=os.environ.get("CLAYCOG_INSTRUCT_HF_MODEL",INSTRUCT_HF_MODEL)
        revision=exact_revision(model,"CLAYCOG_INSTRUCT_HF_REVISION",INSTRUCT_HF_MODEL,INSTRUCT_HF_REVISION)
    else:
        model=os.environ.get("CLAYCOG_HF_MODEL",PRIMARY_HF_MODEL)
        revision=exact_revision(model,"CLAYCOG_HF_REVISION",PRIMARY_HF_MODEL,PRIMARY_HF_REVISION)
    return model,revision

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model,hf_revision=resolve_hf_source(args.instruct_ablation)

    run_local_checks()
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

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
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":TEMPLATE,
        "epochs":EPOCHS,
        "evals":EVALS,
        "estimated_usd":price,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),
        "compatibility_status":"UNPROVEN_UNTIL_TOGETHER_ACCEPTS_BYOM_CHECKPOINT",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created")
        return

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
        suffix="claycog_05b_v1",
    )
    print(json.dumps({
        "job_id":job.id,
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":TEMPLATE,
        "full_fine_tune":True,
        "estimated_usd":price,
        "next":"retrieve job; do not retry create blindly",
    },indent=2))

if __name__=="__main__": main()
