#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate corpus, validate the local BYOM/template
pair, upload/validate files, check the Together template, and print a server price
estimate. A billed training job is created only with --create after all gates pass.

Together's CLI documentation says --from-hf-model should match the base model's
architecture *and size*. Therefore a convenient same-family 7B catalog model is NOT a
valid default template for the required 0.5B checkpoint. The default template is the
exact 0.5B base id. If Together does not expose that id as a trainable template, the
campaign remains OPEN/BLOCKED until Together provides a compatible ~0.5B Qwen2/Qwen2.5
training template; the launcher must not silently spend against a 7B surrogate.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/"train_v1.jsonl"
VALID=HERE/"validation_v1.jsonl"
HF_MODEL=os.environ.get("CLAYCOG_HF_MODEL","Qwen/Qwen2.5-0.5B")
TEMPLATE=os.environ.get("CLAYCOG_TOGETHER_TEMPLATE",HF_MODEL)
EPOCHS=int(os.environ.get("CLAYCOG_EPOCHS","3"))
EVALS=int(os.environ.get("CLAYCOG_EVALS","2"))
MAX_USD=float(os.environ.get("CLAYCOG_MAX_JOB_USD","18.00"))
EXPECTED_ARCH="qwen2"
EXPECTED_PARAM_B=0.49
MAX_SIZE_RATIO=1.30


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


def model_arch(name):
    low=name.lower()
    if "qwen2.5" in low or "qwen2" in low:
        return "qwen2"
    return os.environ.get("CLAYCOG_TEMPLATE_ARCH","").strip().lower() or None


def model_size_b(name):
    # Parse common Hugging Face/catalog names such as 0.5B, 1.5B, 7B, 14B.
    m=re.search(r"(?:^|[-_/])([0-9]+(?:\.[0-9]+)?)B(?:[-_/]|$)",name,re.IGNORECASE)
    if m:
        return float(m.group(1))
    raw=os.environ.get("CLAYCOG_TEMPLATE_PARAM_B","").strip()
    return float(raw) if raw else None


def static_byom_template_gate(hf_model,template):
    """Fail before any upload if the BYOM/template pair violates documented size/arch law."""
    hf_arch=model_arch(hf_model)
    template_arch=model_arch(template)
    if hf_arch!=EXPECTED_ARCH:
        raise SystemExit(f"BYOM_ARCH_ABORT expected {EXPECTED_ARCH}, got {hf_arch!r} for {hf_model}")
    if template_arch!=hf_arch:
        raise SystemExit(
            f"BYOM_ARCH_ABORT template architecture {template_arch!r} != {hf_arch!r}: {template}"
        )
    template_b=model_size_b(template)
    if template_b is None:
        raise SystemExit(
            "BYOM_SIZE_UNKNOWN: set CLAYCOG_TEMPLATE_PARAM_B only from authoritative template metadata"
        )
    ratio=max(template_b,EXPECTED_PARAM_B)/min(template_b,EXPECTED_PARAM_B)
    if ratio>MAX_SIZE_RATIO:
        raise SystemExit(
            f"BYOM_SIZE_ABORT template={template_b:g}B vs required={EXPECTED_PARAM_B:g}B "
            f"ratio={ratio:.2f} exceeds {MAX_SIZE_RATIO:.2f}; do not use a larger surrogate"
        )
    return {"architecture":hf_arch,"required_param_b":EXPECTED_PARAM_B,"template_param_b":template_b,"size_ratio":ratio}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create",action="store_true",help="create billed fine-tuning job after preflight")
    ap.add_argument("--instruct-ablation",action="store_true",help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    args=ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    hf_model="Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL

    # Deliberately runs before corpus upload and before any billed create.
    pair_gate=static_byom_template_gate(hf_model,TEMPLATE)
    run_local_checks()
    client=Together()
    try:
        limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    except Exception as exc:
        raise SystemExit(
            f"TOGETHER_TEMPLATE_UNAVAILABLE: {TEMPLATE}. Required next step is a Together-provided "
            f"~0.5B Qwen2/Qwen2.5 full-training template, not a 7B fallback. Detail: {exc}"
        ) from exc
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
        "static_byom_pair_gate":pair_gate,
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
