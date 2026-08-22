#!/usr/bin/env python3
import json, os, subprocess, time
from pathlib import Path
from together import Together

TARGET_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
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

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    # Price estimation is deliberately first. If Together does not currently
    # accept this exact 0.5B target for fine-tuning, this step must fail before
    # any billed fine-tune create call.
    estimate = client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TARGET_MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
    )
    price = float(estimate.estimated_total_price)
    print(json.dumps({
        "target_hf_model": TARGET_MODEL,
        "estimated_total_price": price,
        "allowed_to_proceed": estimate.allowed_to_proceed,
    }, indent=2))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price endpoint did not authorize this exact 0.5B Full-SFT configuration")
    if price > MAX_USD:
        raise SystemExit(f"ABORT budget gate: estimated ${price:.2f} > configured ${MAX_USD:.2f}")

    # Together documents `from_hf_model` for starting from a Hugging Face Hub
    # repository. Supplying the exact 0.5B repo keeps the target unambiguous.
    # If the service rejects architecture/model admission, the call fails and
    # no successful training job is claimed.
    job = client.fine_tuning.create(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TARGET_MODEL,
        from_hf_model=TARGET_MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=1e-5,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        lora=False,
        suffix="claycog_generic_05b_v0",
    )
    print(json.dumps({
        "job_id": job.id,
        "target_hf_model": TARGET_MODEL,
        "parameter_class": "0.49B",
        "full_fine_tune": True,
        "training_file_id": train_file.id,
        "validation_file_id": valid_file.id,
        "estimated_usd": price,
    }, indent=2))

if __name__ == "__main__":
    main()
