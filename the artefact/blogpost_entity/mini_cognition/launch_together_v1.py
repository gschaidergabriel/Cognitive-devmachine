#!/usr/bin/env python3
"""Together BYOM launcher for the 0.5B ClayCode cognition campaign.

Default mode is preflight: regenerate/validate the corpus, validate/upload files,
check current full-training limits, and obtain a server price estimate. A billed
fine-tuning job is created only with --create after all preflight gates pass.

The launcher targets the Together Python SDK v2 surface used by current Together
documentation. The default training template is the exact Hugging Face checkpoint
itself. If Together does not expose limits for that model, preflight fails closed.
A different template may be supplied explicitly, but it is never guessed from a
larger model: Together documents that --from-hf-model should be as close as possible
to the base model in architecture and size.
"""
import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN = HERE / "train_v1.jsonl"
VALID = HERE / "validation_v1.jsonl"
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-0.5B"
DEFAULT_HF_INSTRUCT = "Qwen/Qwen2.5-0.5B-Instruct"
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
FILE_WAIT_SECONDS = int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS", "600"))


def run_local_checks():
    subprocess.run([sys.executable, str(HERE / "generate_sft_v1.py")], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(TRAIN)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(VALID)], check=True)


def together_sdk_version():
    try:
        return importlib.metadata.version("together")
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def require_sdk_v2():
    version = together_sdk_version()
    if version == "NOT_INSTALLED":
        raise SystemExit("Together SDK missing: install current together>=2")
    try:
        major = int(version.split(".", 1)[0])
    except ValueError:
        raise SystemExit(f"Cannot parse Together SDK version: {version}")
    if major < 2:
        raise SystemExit(f"Together SDK v2 required; found {version}")
    return version


def resolve_models(instruct_ablation=False, template_override=None, hf_override=None):
    hf_model = hf_override or (
        DEFAULT_HF_INSTRUCT if instruct_ablation else os.environ.get("CLAYCOG_HF_MODEL", DEFAULT_HF_MODEL)
    )
    explicit_template = template_override or os.environ.get("CLAYCOG_TOGETHER_TEMPLATE")
    template = explicit_template or hf_model
    return hf_model, template, bool(explicit_template)


def get_full_training_limits(client, template):
    """Use the current Together SDK v2 model-limits surface and fail closed."""
    limits = client.fine_tuning.get_model_limits(model=template)
    if getattr(limits, "full_training", None) is None:
        raise SystemExit(f"Template is not full-FT capable: {template}")
    return limits


def wait_file(client, file_id, timeout_seconds=FILE_WAIT_SECONDS):
    """Wait for server-side file processing across current and legacy response shapes."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        meta = client.files.retrieve(file_id)
        processed = getattr(meta, "processed", None)
        if processed is True:
            return meta

        # Compatibility with older response objects. Current SDK v2 uses `processed`.
        status = str(getattr(meta, "processing_status", "") or "").upper()
        if status == "COMPLETED":
            return meta
        if status in ("INVALID_FORMAT", "FAILED", "ERROR"):
            raise RuntimeError(
                f"Together rejected {file_id}: {status} "
                f"{getattr(meta, 'validation_report', None)}"
            )
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)


def objdict(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return str(x)


def estimate_full_sft_price(client, train_file_id, valid_file_id, template):
    """Current SDK v2 estimate-price contract: string training_type/method values."""
    return client.fine_tuning.estimate_price(
        training_file=train_file_id,
        validation_file=valid_file_id,
        model=template,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method="sft",
        training_type="full",
    )


def create_full_sft_job(client, train_file_id, valid_file_id, template, hf_model):
    """Single billed transition. Caller must have passed preflight and budget gates."""
    return client.fine_tuning.create(
        training_file=train_file_id,
        validation_file=valid_file_id,
        model=template,
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true", help="create one billed fine-tuning job after preflight")
    ap.add_argument("--instruct-ablation", action="store_true", help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    ap.add_argument("--hf-model", help="explicit Hugging Face model override")
    ap.add_argument("--template", help="explicit Together base/template override; must remain architecture/size compatible")
    args = ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    sdk_version = require_sdk_v2()
    hf_model, template, explicit_template = resolve_models(
        instruct_ablation=args.instruct_ablation,
        template_override=args.template,
        hf_override=args.hf_model,
    )

    run_local_checks()

    # Import only after version/key checks so local contract tests can import this module
    # without requiring the network SDK.
    from together import Together

    client = Together()
    limits = get_full_training_limits(client, template)

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    estimate = estimate_full_sft_price(client, train_file.id, valid_file.id, template)
    price = float(estimate.estimated_total_price)
    allowed = bool(estimate.allowed_to_proceed)

    report = {
        "schema": "CLAYCOG_05B_TOGETHER_PREFLIGHT/v2",
        "mode": "preflight" if not args.create else "create",
        "sdk_version": sdk_version,
        "from_hf_model": hf_model,
        "template_model": template,
        "template_source": "explicit_override" if explicit_template else "exact_hf_model_default",
        "template_full_training": getattr(limits, "full_training", None) is not None,
        "epochs": EPOCHS,
        "evals": EVALS,
        "estimated_usd": price,
        "allowed_to_proceed": allowed,
        "price_detail": objdict(estimate),
        "compatibility_status": "UNPROVEN_UNTIL_TOGETHER_ACCEPTS_BYOM_JOB",
        "compatibility_note": (
            "preflight proves dataset processing, template limits and budget only; "
            "Together BYOM checkpoint acceptance occurs at job creation"
        ),
    }
    print(json.dumps(report, indent=2, default=str))

    if not allowed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created")
        return

    job = create_full_sft_job(client, train_file.id, valid_file.id, template, hf_model)
    print(
        json.dumps(
            {
                "schema": "CLAYCOG_05B_TRAINING_CREATE/v2",
                "job_id": job.id,
                "from_hf_model": hf_model,
                "template_model": template,
                "full_fine_tune": True,
                "estimated_usd": price,
                "next": "retrieve this exact job id; do not retry create blindly",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
