#!/usr/bin/env python3
"""Fail-closed Together BYOM launcher for the 0.5B ClayCode cognition campaign.

The canonical training corpus is ClayCog SFT v2. Default mode is preflight only.
A billed job can be created only with --create after all local corpus gates, the
Together Full-FT template gate, server-side file validation, and the USD budget gate pass.

The owner-required checkpoint remains Qwen/Qwen2.5-0.5B. A Together training template
must be architecture-compatible with that checkpoint. Never silently switch the research
question to a different base architecture merely because another model is trainable.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v2.jsonl"
VALID=HERE/"validation_v2.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
DEFAULT_TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))


def emit(report):
    print(json.dumps(report,indent=2,sort_keys=True,default=str))


def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_corpus_v2.py"),str(TRAIN),str(VALID)],check=True)


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


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create exactly one billed fine-tuning job after all preflight gates")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    ap.add_argument("--template",default=DEFAULT_TEMPLATE,help="Together Full-FT template candidate; must be Qwen2-compatible")
    args=ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        emit({
            "phase":"secret_admission",
            "status":"BLOCKED_NO_SECRET",
            "job_started":False,
            "uploads_started":False,
            "instruction":"Mount TOGETHER_API_KEY in the execution environment only; never commit it.",
        })
        raise SystemExit(2)

    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    template=args.template

    # Local deterministic gates execute before any remote upload or billable create.
    run_local_checks()
    client=Together()

    # The Together training-template gate is intentionally before file upload. A catalog
    # model that is inference-capable but not Full-FT-capable must not consume campaign effort.
    try:
        limits=client.fine_tuning.model_limits(model_name=template)
    except Exception as exc:
        emit({
            "phase":"template_full_ft_gate",
            "status":"API_CHECK_ERROR",
            "from_hf_model":hf_model,
            "template_model":template,
            "uploads_started":False,
            "job_started":False,
            "error_type":type(exc).__name__,
            "error":str(exc),
        })
        raise

    supports_full=bool(getattr(limits,"supports_full_training",False))
    if not supports_full:
        emit({
            "phase":"template_full_ft_gate",
            "status":"BLOCKED_TEMPLATE_NOT_FULL_FT",
            "from_hf_model":hf_model,
            "template_model":template,
            "supports_full_training":False,
            "uploads_started":False,
            "job_started":False,
            "next":"Use a Together-documented Qwen2-compatible Full-FT template if one becomes available, or move the same 0.5B full-SFT campaign to another owner-admitted full-FT runner. Do not silently change the base architecture.",
        })
        raise SystemExit(3)

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)

    estimate=client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=template,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method":"sft","train_on_inputs":"auto"},
        training_type={"type":"Full"},
    )
    price=float(estimate.estimated_total_price)
    report={
        "phase":"server_preflight",
        "mode":"preflight" if not args.create else "create_requested",
        "corpus_schema":"claycog-sft/v2",
        "training_file_id":train_file.id,
        "validation_file_id":valid_file.id,
        "from_hf_model":hf_model,
        "template_model":template,
        "template_supports_full_training":supports_full,
        "epochs":EPOCHS,
        "evals":EVALS,
        "estimated_usd":price,
        "max_job_usd":MAX_USD,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),
        "compatibility_status":"TEMPLATE_FULL_FT_ACCEPTED_BY_API; BYOM_JOB_COMPATIBILITY_STILL_UNPROVEN_UNTIL_CREATE_ACCEPTS_CHECKPOINT",
        "job_started":False,
    }
    emit(report)
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
        model=template,
        from_hf_model=hf_model,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=1e-5,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        lora=False,
        suffix="claycog_05b_v2",
    )
    emit({
        "phase":"create",
        "job_id":job.id,
        "from_hf_model":hf_model,
        "template_model":template,
        "corpus_schema":"claycog-sft/v2",
        "full_fine_tune":True,
        "estimated_usd":price,
        "job_started":True,
        "next":"Retrieve this exact job id; never retry create blindly.",
    })


if __name__=="__main__": main()
