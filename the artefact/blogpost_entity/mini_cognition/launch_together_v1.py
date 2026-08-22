#!/usr/bin/env python3
"""Budget- and provenance-gated Together BYOM launcher for ClayCog 0.5B.

Preflight validates/regenerates corpus, uploads with server validation, checks template
full-training capability, and requests a server price estimate. The estimate is a
budget gate only: Together's estimate endpoint does not bind ``from_hf_model`` or
``hf_model_revision``, so it cannot prove BYOM checkpoint compatibility.

A billed create additionally requires an exact 40-hex Hugging Face commit revision,
uses a deterministic campaign fingerprint/suffix, and checks Together's job ledger
for a previous job with the same suffix before creating anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TRAIN = HERE / "train_v1.jsonl"
VALID = HERE / "validation_v1.jsonl"
HF_MODEL = os.environ.get("CLAYCOG_HF_MODEL", "Qwen/Qwen2.5-0.5B")
TEMPLATE = os.environ.get("CLAYCOG_TOGETHER_TEMPLATE", "Qwen/Qwen2.5-7B-Instruct-Turbo")
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
WARMUP_RATIO = float(os.environ.get("CLAYCOG_WARMUP_RATIO", "0.03"))
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
ACTIVE_OR_FINAL_STATUSES = {
    "pending", "queued", "running", "compressing", "uploading",
    "cancel_requested", "completed",
}
RETRYABLE_TERMINAL_STATUSES = {"error", "cancelled"}


def run_local_checks() -> None:
    subprocess.run([sys.executable, str(HERE / "generate_sft_v1.py")], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(TRAIN)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(VALID)], check=True)


def wait_file(client: Any, file_id: str) -> Any:
    while True:
        meta = client.files.retrieve(file_id)
        status = str(meta.processing_status)
        if status == "COMPLETED":
            return meta
        if status in ("INVALID_FORMAT", "FAILED"):
            raise RuntimeError(
                f"Together rejected {file_id}: {status} "
                f"{getattr(meta, 'validation_report', None)}"
            )
        time.sleep(5)


def objdict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_revision(raw: str | None) -> str | None:
    if raw is None or raw == "":
        return None
    value = raw.strip().lower()
    if not REVISION_RE.fullmatch(value):
        raise ValueError("Hugging Face revision must be an exact 40-hex commit hash")
    return value


def revision_for(ablation: bool) -> tuple[str, str | None]:
    env_name = "CLAYCOG_HF_INSTRUCT_REVISION" if ablation else "CLAYCOG_HF_REVISION"
    return env_name, normalize_revision(os.environ.get(env_name))


def campaign_descriptor(
    *,
    hf_model: str,
    hf_revision: str | None,
    template: str,
    train_sha256: str,
    validation_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": "claycog-together-campaign/v2",
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision or "UNPINNED_PREFLIGHT_ONLY",
        "template_model": template,
        "train_sha256": train_sha256,
        "validation_sha256": validation_sha256,
        "n_epochs": EPOCHS,
        "n_evals": EVALS,
        "n_checkpoints": 1,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "train_on_inputs": "auto",
        "training_method": "sft",
        "training_type": "Full",
        "lora": False,
    }


def campaign_fingerprint(descriptor: dict[str, Any]) -> str:
    encoded = json.dumps(
        descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def campaign_suffix(fingerprint: str) -> str:
    return f"claycog05b-{fingerprint[:16]}"


def _job_data(response: Any) -> list[Any]:
    data = getattr(response, "data", response)
    if data is None:
        return []
    return list(data)


def find_same_campaign_jobs(client: Any, suffix: str) -> list[Any]:
    return [
        job for job in _job_data(client.fine_tuning.list())
        if str(getattr(job, "suffix", "")) == suffix
    ]


def duplicate_create_gate(
    jobs: list[Any], *, suffix: str, retry_job_id: str | None
) -> dict[str, Any] | None:
    if not jobs:
        if retry_job_id:
            raise RuntimeError(
                "RETRY_ABORT: --retry-job-id supplied but no same-campaign job exists"
            )
        return None

    normalized = [
        {
            "id": str(getattr(job, "id", "")),
            "status": str(getattr(job, "status", "unknown")),
            "suffix": str(getattr(job, "suffix", "")),
        }
        for job in jobs
    ]

    for job in normalized:
        if job["status"] in ACTIVE_OR_FINAL_STATUSES:
            raise RuntimeError(
                "DUPLICATE_ABORT: same campaign already exists in Together "
                f"({job['id']} status={job['status']} suffix={suffix})"
            )

    if retry_job_id is None:
        detail = ", ".join(f"{j['id']}:{j['status']}" for j in normalized)
        raise RuntimeError(
            "DUPLICATE_ABORT: prior same-campaign terminal job(s) exist; inspect first "
            f"and retry explicitly with --retry-job-id. jobs={detail}"
        )

    matched = [job for job in normalized if job["id"] == retry_job_id]
    if len(matched) != 1:
        raise RuntimeError(
            "RETRY_ABORT: --retry-job-id must identify exactly one same-campaign job"
        )
    if matched[0]["status"] not in RETRYABLE_TERMINAL_STATUSES:
        raise RuntimeError(
            "RETRY_ABORT: explicit retry is allowed only after error/cancelled status"
        )
    return matched[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--create", action="store_true",
        help="create billed fine-tuning job after all preflight and replay gates pass",
    )
    ap.add_argument(
        "--instruct-ablation", action="store_true",
        help="use Qwen/Qwen2.5-0.5B-Instruct BYOM checkpoint",
    )
    ap.add_argument(
        "--retry-job-id",
        help="explicitly authorize one retry only when the same campaign job is error/cancelled",
    )
    args = ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")
    if args.retry_job_id and not args.create:
        raise SystemExit("--retry-job-id is valid only with --create")

    hf_model = "Qwen/Qwen2.5-0.5B-Instruct" if args.instruct_ablation else HF_MODEL
    revision_env, hf_revision = revision_for(args.instruct_ablation)
    if args.create and hf_revision is None:
        raise SystemExit(
            f"BILLED_CREATE_ABORT: set {revision_env} to the exact 40-hex Hugging Face commit"
        )

    run_local_checks()

    # Lazy import keeps deterministic safety helpers unit-testable without Together installed.
    from together import Together

    client = Together()
    limits = client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits, "supports_full_training", False):
        raise SystemExit(f"Template is not full-FT capable: {TEMPLATE}")

    train_sha = sha256_file(TRAIN)
    validation_sha = sha256_file(VALID)
    descriptor = campaign_descriptor(
        hf_model=hf_model,
        hf_revision=hf_revision,
        template=TEMPLATE,
        train_sha256=train_sha,
        validation_sha256=validation_sha,
    )
    fingerprint = campaign_fingerprint(descriptor)
    suffix = campaign_suffix(fingerprint)

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
        "hf_model_revision": hf_revision,
        "revision_env": revision_env,
        "template_model": TEMPLATE,
        "epochs": EPOCHS,
        "evals": EVALS,
        "train_sha256": train_sha,
        "validation_sha256": validation_sha,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "estimated_usd": price,
        "allowed_to_proceed": bool(estimate.allowed_to_proceed),
        "price_detail": objdict(estimate),
        "estimate_scope": "DATASET_PLUS_TEMPLATE_BUDGET_ONLY",
        "compatibility_status": "UNPROVEN_UNTIL_CREATE_VALIDATES_BYOM_CHECKPOINT",
    }
    print(json.dumps(report, indent=2, default=str))

    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print("PREFLIGHT_ONLY: no billed fine-tuning job created")
        return

    prior = find_same_campaign_jobs(client, suffix)
    try:
        retry_of = duplicate_create_gate(
            prior, suffix=suffix, retry_job_id=args.retry_job_id
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None

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
        warmup_ratio=WARMUP_RATIO,
        train_on_inputs="auto",
        lora=False,
        suffix=suffix,
    )
    print(json.dumps({
        "job_id": job.id,
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision,
        "template_model": TEMPLATE,
        "full_fine_tune": True,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "estimated_usd": price,
        "explicit_retry_of": retry_of,
        "next": "retrieve/list events; do not create another job blindly",
    }, indent=2))


if __name__ == "__main__":
    main()
