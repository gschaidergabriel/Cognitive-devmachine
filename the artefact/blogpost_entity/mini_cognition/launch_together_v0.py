#!/usr/bin/env python3
import json, os, subprocess, time
from pathlib import Path
from together import Together

BASE_MODEL = "Qwen/Qwen3.5-0.8B"
EPOCHS = 3
EVALS = 2
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
HERE = Path(__file__).resolve().parent
TRAIN = HERE / "train_v0.jsonl"
VALID = HERE / "validation_v0.jsonl"


def run_local_checks():
    subprocess.run(["python3", str(HERE / "generate_sft_v0.py")], check=True)
    subprocess.run(["python3", str(HERE / "validate_sft_v0.py"), str(TRAIN)], check=True)
    subprocess.run(["python3", str(HERE / "validate_sft_v0.py"), str(VALID)], check=True)


def wait_file(client, file_id):
    while True:
        meta = client.files.retrieve(file_id)
        status = meta.processing_status
        if status == "COMPLETED": return meta
        if status in ("INVALID_FORMAT", "FAILED"):
            raise RuntimeError(f"Together rejected {file_id}: {status} {meta.validation_report}")
        time.sleep(5)


def main():
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY is required in the runtime environment; never commit it")
    run_local_checks()
    client = Together()
    limits = client.fine_tuning.model_limits(model_name=BASE_MODEL)
    if not limits.supports_full_training:
        raise SystemExit(f"Current Together limits say {BASE_MODEL} is not full-FT capable")

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id); wait_file(client, valid_file.id)

    estimate = client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=BASE_MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
    )
    price = float(estimate.estimated_total_price)
    print(json.dumps({"estimated_total_price": price, "allowed_to_proceed": estimate.allowed_to_proceed}, indent=2))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price endpoint says this account/job is not allowed to proceed")
    if price > MAX_USD:
        raise SystemExit(f"ABORT budget gate: estimated ${price:.2f} > configured ${MAX_USD:.2f}")

    job = client.fine_tuning.create(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=BASE_MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=1e-5,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        lora=False,
        suffix="claycog_generic_v0",
    )
    print(json.dumps({"job_id": job.id, "base_model": BASE_MODEL, "full_fine_tune": True, "training_file_id": train_file.id, "validation_file_id": valid_file.id, "estimated_usd": price}, indent=2))

if __name__ == "__main__": main()
