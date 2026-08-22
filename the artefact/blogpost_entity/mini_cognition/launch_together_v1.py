#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, upload/validate files, check an
explicit Together template, and print a server price estimate. A billed training job is
created only with --create after all gates pass.

Together's current fine-tuning supported-model table (checked 2026-08-22) exposes no
Qwen2/Qwen2.5 training template. Qwen/Qwen2.5-7B-Instruct-Turbo remains visible for
inference but is therefore no longer a safe default fine-tuning template assumption.
The launcher consequently has NO implicit Together template. A caller must supply a
Qwen2-compatible template explicitly after current Together API/docs verification.

The HF checkpoint itself is revision-pinned. Together's estimate-price endpoint does not
accept from_hf_model, so a successful estimate is a budget/template/data gate only; it
must never be reported as BYOM checkpoint acceptance. Actual BYOM compatibility remains
unproven until Together accepts the create request/checkpoint.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","").strip()
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
HF_REVISION=os.environ.get("CLAYCOG_HF_REVISION","").strip()
PINNED_REVISIONS={
    "Qwen/Qwen2.5-0.5B":"285c998059f3e217fe1f05e241d55b5c5eef5bd3",
    "Qwen/Qwen2.5-0.5B-Instruct":"7ae557604adf67be50417f59c2c2f167def9a775",
}


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


def resolve_template(cli_template):
    template=(cli_template or TEMPLATE).strip()
    if not template:
        raise SystemExit(
            "TOGETHER_TEMPLATE_BLOCKED: no implicit template is safe. The 2026-08-22 "
            "Together fine-tuning table lists no Qwen2/Qwen2.5 base. Supply --template "
            "or CLAYCOG_TOGETHER_TEMPLATE only after current Together verification of a "
            "Qwen2-compatible training template."
        )
    # Qwen2.5 checkpoints are Qwen2ForCausalLM. Do not silently substitute the currently
    # documented Qwen3.x fine-tuning bases merely because they are small and branded Qwen.
    if "qwen3" in template.lower():
        raise SystemExit(
            f"ARCHITECTURE_ABORT: {template} is a Qwen3-family template; the target "
            "checkpoint is Qwen2/Qwen2.5. BYOM requires architecture compatibility."
        )
    return template


def resolve_revision(hf_model,cli_revision):
    revision=(cli_revision or HF_REVISION or PINNED_REVISIONS.get(hf_model,"")).strip()
    if not revision:
        raise SystemExit(
            f"HF_REVISION_REQUIRED: no pinned revision is known for {hf_model}; set "
            "--hf-revision or CLAYCOG_HF_REVISION. Mutable HF main is not admitted."
        )
    return revision


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    ap.add_argument("--template",default="",help="explicit Together Qwen2-compatible fine-tuning template")
    ap.add_argument("--hf-revision",default="",help="exact Hugging Face checkpoint revision")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    hf_revision=resolve_revision(hf_model,args.hf_revision)
    template=resolve_template(args.template)

    run_local_checks()
    client=Together()
    limits=client.fine_tuning.model_limits(model_name=template)
    if not getattr(limits,"supports_full_training",False):
        raise SystemExit(f"Template is not full-FT capable: {template}")

    train_file=client.files.upload(file=str(TRAIN),purpose="fine-tune",check=True)
    valid_file=client.files.upload(file=str(VALID),purpose="fine-tune",check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)

    # Together's current estimate-price schema does not expose from_hf_model. Therefore
    # this estimate proves budget/data/template admission only, never BYOM checkpoint
    # compatibility. The create request below is the first checkpoint-acceptance gate.
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
        "mode":"preflight" if not args.create else "create",
        "from_hf_model":hf_model,
        "hf_model_revision":hf_revision,
        "template_model":template,
        "epochs":EPOCHS,
        "evals":EVALS,
        "estimated_usd":price,
        "allowed_to_proceed":bool(estimate.allowed_to_proceed),
        "price_detail":objdict(estimate),
        "compatibility_status":"BYOM_UNPROVEN_PRICE_ENDPOINT_HAS_NO_FROM_HF_MODEL",
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this template job")
    if price>MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created; BYOM checkpoint compatibility remains unproven")
        return

    job=client.fine_tuning.create(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=template,
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
        "template_model":template,
        "full_fine_tune":True,
        "estimated_usd":price,
        "next":"retrieve job; do not retry create blindly",
    },indent=2))


if __name__=="__main__": main()
