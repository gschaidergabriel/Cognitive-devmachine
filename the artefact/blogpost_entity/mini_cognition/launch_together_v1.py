#!/usr/bin/env python3
"""Together BYOM launcher for the generic 0.5B ClayCode cognition campaign.

Default mode is preflight. It regenerates/validates the selected corpus, uploads and
validates files, checks the Together template's full-FT limits, asks Together for a
server-side price/admission estimate, and writes a local receipt. A billed training job
is created only with --create.

Important boundary: the price/model-limit preflight does NOT prove that Together can
load the exact BYOM checkpoint. `from_hf_model` compatibility is only credited when the
create endpoint actually accepts the pinned HF model/revision. The script therefore
reports that state explicitly instead of calling template admission BYOM compatibility.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from together import Together

HERE = Path(__file__).resolve().parent
HF_MODEL_DEFAULT = os.environ.get("CLAYCOG_HF_MODEL", "Qwen/Qwen2.5-0.5B")
HF_REV_DEFAULT = os.environ.get("CLAYCOG_HF_REVISION", "060db64")
HF_REV_INSTRUCT = os.environ.get("CLAYCOG_HF_REVISION_INSTRUCT", "7ae5576")
TEMPLATE = os.environ.get("CLAYCOG_TOGETHER_TEMPLATE", "Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
RANDOM_SEED = int(os.environ.get("CLAYCOG_TRAIN_SEED", "20260822"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def objdict(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return str(x)


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


def run_local_checks(corpus_version):
    suffix = "v2" if corpus_version == "v2" else "v1"
    generator = HERE / f"generate_sft_{suffix}.py"
    train = HERE / f"train_{suffix}.jsonl"
    valid = HERE / f"validation_{suffix}.jsonl"
    subprocess.run([sys.executable, str(generator)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(train)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(valid)], check=True)
    return train, valid


def campaign_identity(*, hf_model, hf_revision, train, valid, corpus_version):
    payload = {
        "schema": "claycog-together-campaign/v2",
        "hf_model": hf_model,
        "hf_revision": hf_revision,
        "template": TEMPLATE,
        "training_sha256": sha256(train),
        "validation_sha256": sha256(valid),
        "corpus_version": corpus_version,
        "epochs": EPOCHS,
        "evals": EVALS,
        "learning_rate": LEARNING_RATE,
        "random_seed": RANDOM_SEED,
        "training_type": "Full",
        "training_method": "sft",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload, digest


def find_existing_job(client, suffix):
    """Fail closed against blind duplicate create when the SDK exposes job suffixes."""
    try:
        listing = client.fine_tuning.list()
        rows = getattr(listing, "data", listing)
        if rows is None:
            return None
        for job in rows:
            if getattr(job, "suffix", None) == suffix:
                return job
    except Exception as exc:
        raise RuntimeError(f"cannot prove duplicate-create safety: {exc}") from exc
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true", help="create billed fine-tuning job after all preflight gates")
    ap.add_argument("--instruct-ablation", action="store_true", help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint")
    ap.add_argument("--corpus", choices=("v1", "v2"), default="v2", help="dataset generation to train; default v2 compositional")
    ap.add_argument("--hf-revision", default=None, help="pin HF revision; create requires a non-floating revision")
    args = ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    hf_model = "Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL_DEFAULT
    hf_revision = args.hf_revision or (HF_REV_INSTRUCT if args.instruct_ablation else HF_REV_DEFAULT)
    if args.create and hf_revision in ("", "main", "master"):
        raise SystemExit("CREATE_ABORT: pin CLAYCOG_HF_REVISION/--hf-revision to an immutable HF revision")

    train, valid = run_local_checks(args.corpus)
    campaign, campaign_sha = campaign_identity(
        hf_model=hf_model,
        hf_revision=hf_revision,
        train=train,
        valid=valid,
        corpus_version=args.corpus,
    )
    suffix = f"claycog05b-{args.corpus}-{campaign_sha[:12]}"

    client = Together()
    limits = client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits, "supports_full_training", False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    train_file = client.files.upload(file=str(train), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(valid), purpose="fine-tune", check=True)
    train_meta = wait_file(client, train_file.id)
    valid_meta = wait_file(client, valid_file.id)

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
        "schema": "claycog-together-preflight/v2",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "mode": "create" if args.create else "preflight",
        "campaign_sha256": campaign_sha,
        "suffix": suffix,
        "campaign": campaign,
        "training_file_id": train_file.id,
        "validation_file_id": valid_file.id,
        "training_file_status": str(getattr(train_meta, "processing_status", "UNKNOWN")),
        "validation_file_status": str(getattr(valid_meta, "processing_status", "UNKNOWN")),
        "estimated_usd": price,
        "max_job_usd": MAX_USD,
        "allowed_to_proceed": bool(estimate.allowed_to_proceed),
        "template_full_training": bool(getattr(limits, "supports_full_training", False)),
        "price_detail": objdict(estimate),
        "byom_compatibility": "UNPROVEN_UNTIL_CREATE_ACCEPTS_PINNED_FROM_HF_MODEL",
        "job_started": False,
    }
    receipt_path = HERE / "together_preflight_latest.json"
    receipt_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))

    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created; BYOM compatibility remains unproven")
        return

    existing = find_existing_job(client, suffix)
    if existing is not None:
        raise SystemExit(
            f"DUPLICATE_CREATE_ABORT existing job id={getattr(existing, 'id', 'UNKNOWN')} "
            f"status={getattr(existing, 'status', 'UNKNOWN')} suffix={suffix}"
        )

    job = client.fine_tuning.create(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=TEMPLATE,
        from_hf_model=hf_model,
        hf_model_revision=hf_revision,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=LEARNING_RATE,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
        random_seed=RANDOM_SEED,
        suffix=suffix,
    )
    created = {
        "schema": "claycog-together-create/v2",
        "campaign_sha256": campaign_sha,
        "job_id": job.id,
        "status": str(getattr(job, "status", "UNKNOWN")),
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision,
        "template_model": TEMPLATE,
        "full_fine_tune": True,
        "estimated_usd": price,
        "byom_compatibility": "CREATE_ENDPOINT_ACCEPTED_PINNED_CHECKPOINT",
        "next": "retrieve this job id; do not retry create blindly",
    }
    receipt_path.write_text(json.dumps({**report, **created, "job_started": True}, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(created, indent=2, default=str))


if __name__ == "__main__":
    main()
