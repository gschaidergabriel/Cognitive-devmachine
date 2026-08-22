#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, check an explicitly selected
same-architecture/same-size Together training template, upload/validate files, and print
a server price estimate. A billed training job is created only with --create after all
gates pass.

Together's documented --from-hf-model contract requires the Hugging Face checkpoint to
match the selected base model's architecture and size. The campaign therefore has NO
7B fallback/default for a 0.5B checkpoint. Until Together exposes or accepts a compatible
0.5B Qwen2/Qwen2.5 training template, compatibility remains OPEN/BLOCKED rather than being
papered over with a larger same-family model.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE","").strip()
TEMPLATE_ARCH=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE_ARCH","").strip().lower()
TEMPLATE_PARAMS_B=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B","").strip()
EXPECTED_ARCH="qwen2"
EXPECTED_PARAMS_B=0.5
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))


def run_local_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v1.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(VALID)],check=True)


def require_compatible_template_claim():
    """Fail before any Together upload when no 0.5B Qwen2 template is explicitly bound.

    This is an operator-side admission fence, not proof of Together compatibility. The
    authenticated Together API remains authoritative and may still reject the BYOM pair.
    """
    if not TEMPLATE:
        raise SystemExit(
            "BYOM_COMPATIBILITY_OPEN: set CLAYCOG_TOGETHER_TEMPLATE only after identifying "
            "a Together fine-tuning base/template compatible with Qwen2 architecture at 0.5B; "
            "the former Qwen2.5-7B-Instruct-Turbo default is intentionally forbidden"
        )
    if not TEMPLATE_ARCH or not TEMPLATE_PARAMS_B:
        raise SystemExit(
            "TEMPLATE_METADATA_REQUIRED: set CLAYCOG_TOGETHER_TEMPLATE_ARCH=qwen2 and "
            "CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B=0.5 from current Together model metadata"
        )
    try:
        params_b=float(TEMPLATE_PARAMS_B)
    except ValueError:
        raise SystemExit("CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B must be numeric")
    if TEMPLATE_ARCH != EXPECTED_ARCH or abs(params_b-EXPECTED_PARAMS_B) > 1e-9:
        raise SystemExit(
            f"BYOM_TEMPLATE_MISMATCH: checkpoint={EXPECTED_ARCH}/{EXPECTED_PARAMS_B}B "
            f"template_claim={TEMPLATE_ARCH}/{params_b}B template={TEMPLATE}"
        )


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
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL

    run_local_checks()
    require_compatible_template_claim()
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
        "template_model":TEMPLATE,
        "template_arch_claim":TEMPLATE_ARCH,
        "template_params_b_claim":float(TEMPLATE_PARAMS_B),
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
        "template_model":TEMPLATE,
        "full_fine_tune":True,
        "estimated_usd":price,
        "next":"retrieve job; do not retry create blindly",
    },indent=2))


if __name__=="__main__": main()
