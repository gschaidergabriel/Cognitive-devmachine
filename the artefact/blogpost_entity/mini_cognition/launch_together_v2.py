#!/usr/bin/env python3
"""Fail-closed Together BYOM launcher for ClayCog 0.5B corpus v2.

No billed job is created without --create. This script deliberately has NO default Together
training template: the 2026-08-22 public fine-tuning catalog exposes Qwen3.5-0.8B as the
smallest Qwen entry and no Qwen2/Qwen2.5 template. BYOM requires compatible architecture,
so an operator must provide an empirically accepted Qwen2-compatible template explicitly.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from together import Together
HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v2.jsonl"; VALID=HERE/"validation_v2.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3")); EVALS=int(os.environ.get("CLAYCOG_EVALS","2")); MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))

def local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v2.py"),str(TRAIN),"--against",str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v2.py"),str(VALID),"--against",str(TRAIN)],check=True)

def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id); status=str(meta.processing_status)
        if status=="COMPLETED": return meta
        if status in ("INVALID_FORMAT","FAILED"): raise RuntimeError(f"Together rejected {file_id}: {status} {getattr(meta,'validation_report',None)}")
        time.sleep(5)

def objdict(x):
    if hasattr(x,"model_dump"): return x.model_dump()
    if hasattr(x,"dict"): return x.dict()
    return str(x)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--create",action="store_true"); ap.add_argument("--instruct-ablation",action="store_true"); args=ap.parse_args()
    local_checks()
    if not TEMPLATE:
        raise SystemExit("TOGETHER_TEMPLATE_REQUIRED: set CLAYCOG_TOGETHER_TEMPLATE only after a current Qwen2-compatible Together template is confirmed; public catalog currently has no Qwen2/Qwen2.5 entry")
    if not os.environ.get("TOGETHER_API_KEY"): raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    client=Together(); limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,"supports_full_training",False): raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")
    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True); valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,n_epochs=EPOCHS,n_evals=EVALS,training_method={"method":"sft","train_on_inputs":"auto"},training_type={"type":"Full"})
    price=float(estimate.estimated_total_price)
    report={"mode":"preflight" if not args.create else "create","from_hf_model":hf_model,"template_model":TEMPLATE,"epochs":EPOCHS,"evals":EVALS,"estimated_usd":price,"allowed_to_proceed":bool(estimate.allowed_to_proceed),"price_detail":objdict(estimate),"byom_architecture_status":"UNPROVEN_UNTIL_CREATE_ACCEPTS_FROM_HF_MODEL"}
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit("Together price/admission endpoint does not allow this job")
    if price>MAX_USD: raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create: print("PREFLIGHT_ONLY: no billed fine-tuning job created"); return
    job=client.fine_tuning.create(training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,from_hf_model=hf_model,n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,train_on_inputs="auto",lora=False,suffix="claycog_05b_v2")
    print(json.dumps({"job_id":job.id,"from_hf_model":hf_model,"template_model":TEMPLATE,"full_fine_tune":True,"estimated_usd":price,"next":"retrieve job; do not retry create blindly"},indent=2))

if __name__=="__main__": main()
