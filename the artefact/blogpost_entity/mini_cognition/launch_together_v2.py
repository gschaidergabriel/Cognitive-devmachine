#!/usr/bin/env python3
"""Together BYOM launcher v2 for the 0.5B ClayCode cognition campaign.

Local corpus/OOD/gate checks are always runnable without Together credentials or SDK.
Network preflight begins only after those deterministic checks pass. A billed create
still requires explicit --create and the configured price gate.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN = HERE / "train_v2.jsonl"
VALID = HERE / "validation_v2.jsonl"
MANIFEST = HERE / "corpus_manifest_v2.json"
HF_MODEL = os.environ.get("CLAYCOG_HF_MODEL", "Qwen/Qwen2.5-0.5B")
TEMPLATE = os.environ.get("CLAYCOG_TOGETHER_TEMPLATE", "Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))


def run(cmd):
    subprocess.run(cmd, check=True)


def run_local_checks():
    run([sys.executable, str(HERE / "generate_sft_v2.py")])
    run([sys.executable, str(HERE / "validate_sft_v1.py"), str(TRAIN)])
    run([sys.executable, str(HERE / "validate_sft_v1.py"), str(VALID)])
    run([sys.executable, str(HERE / "validate_gate_coverage_v2.py"), str(TRAIN), str(VALID)])
    run([sys.executable, str(HERE / "generate_eval_ood_v2.py")])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = {
        "stage": "LOCAL_DATA_GATES_PASS",
        "schema": manifest["schema"],
        "examples": manifest["examples"],
        "train": manifest["train"],
        "validation": manifest["validation"],
        "train_sha256": manifest["train_sha256"],
        "validation_sha256": manifest["validation_sha256"],
        "ood_spec": "eval_ood_v2.jsonl",
        "network_used": False,
        "billed_job_created": False,
    }
    print(json.dumps(report, indent=2))
    return report


def wait_file(client, file_id):
    while True:
        meta = client.files.retrieve(file_id)
        status = str(meta.processing_status)
        if status == "COMPLETED":
            return meta
        if status in ("INVALID_FORMAT", "FAILED"):
            raise RuntimeError(
                f"Together rejected {file_id}: {status} {getattr(meta, 'validation_report', None)}"
            )
        time.sleep(5)


def objdict(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-only", action="store_true", help="run deterministic local data gates only")
    ap.add_argument("--create", action="store_true", help="create billed fine-tuning job after preflight")
    ap.add_argument(
        "--instruct-ablation",
        action="store_true",
        help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint",
    )
    args = ap.parse_args()
    if args.local_only and args.create:
        raise SystemExit("--local-only and --create are mutually exclusive")

    local = run_local_checks()
    if args.local_only:
        print("LOCAL_ONLY: Together API not contacted")
        return

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit(
            "LOCAL_DATA_GATES_PASS; TOGETHER_API_KEY is absent, so network preflight was not attempted"
        )

    # Lazy import preserves fully offline validation on machines without the Together SDK.
    from together import Together

    hf_model = "Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    client = Together()

    # BYOM template compatibility is empirical. The current public fine-tuning table does not
    # itself prove this Qwen2.5 inference model is an admissible full-FT template.
    limits = client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits, "supports_full_training", False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    estimate = client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TEMPLATE,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
    )
    price = float(estimate.estimated_total_price)
    report = {
        "mode": "preflight" if not args.create else "create",
        "from_hf_model": hf_model,
        "template_model": TEMPLATE,
        "epochs": EPOCHS,
        "evals": EVALS,
        "estimated_usd": price,
        "max_job_usd": MAX_USD,
        "allowed_to_proceed": bool(estimate.allowed_to_proceed),
        "price_detail": objdict(estimate),
        "compatibility_status": "UNPROVEN_UNTIL_TOGETHER_ACCEPTS_BYOM_CHECKPOINT",
        "corpus": local,
    }
    print(json.dumps(report, indent=2, default=str))

    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created")
        return

    job = client.fine_tuning.create(
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
        suffix="claycog_05b_v2",
    )
    print(
        json.dumps(
            {
                "job_id": job.id,
                "from_hf_model": hf_model,
                "template_model": TEMPLATE,
                "full_fine_tune": True,
                "estimated_usd": price,
                "next": "retrieve job; do not retry create blindly",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
