#!/usr/bin/env python3
"""Spend-safe Together BYOM launcher for the generic 0.5B ClayCode cognition campaign.

Default mode is preflight. It regenerates and validates the selected corpus, requires an
immutable Hugging Face revision, checks the Together full-training surface, validates
uploaded datasets, obtains the server-side price/admission estimate, and prints a bounded
receipt. A billed job is created only with --create after exact campaign fingerprint
confirmation and duplicate-job checks.

Evidence boundary:
- the default Together template is the exact Hugging Face model identifier, never a
  guessed larger checkpoint;
- an explicit different template can be inspected in preflight, but billed create is
  fail-closed unless template == from_hf_model;
- model-limit and price endpoints do not prove BYOM weight loading;
- create acceptance does not prove training completion or model quality;
- an ambiguous create outcome must be reconciled against the account job ledger before
  any new create attempt.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-0.5B"
DEFAULT_HF_INSTRUCT = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_HF_REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"
DEFAULT_HF_INSTRUCT_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
RANDOM_SEED = int(os.environ.get("CLAYCOG_TRAIN_SEED", "20260822"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
FILE_WAIT_SECONDS = int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS", "600"))
CREATE_CONFIRM_ENV = "CLAYCOG_CREATE_FINGERPRINT"
ACTIVE_OR_SPENT_STATUSES = {
    "pending", "queued", "running", "compressing", "uploading",
    "cancel_requested", "cancelled", "error", "completed",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def objdict(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    if isinstance(x, dict):
        return x
    return str(x)


def together_sdk_version():
    try:
        return importlib.metadata.version("together")
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def require_sdk():
    version = together_sdk_version()
    if version == "NOT_INSTALLED":
        raise SystemExit("Together SDK missing: install current together>=2")
    try:
        major = int(version.split(".", 1)[0])
    except ValueError:
        raise SystemExit(f"Cannot parse Together SDK version: {version}")
    if major < 2:
        raise SystemExit(f"Together SDK v2+ required; found {version}")
    return version


def resolve_models(*, instruct_ablation=False, hf_override=None, revision_override=None, template_override=None):
    if instruct_ablation:
        hf_model = hf_override or DEFAULT_HF_INSTRUCT
        revision = revision_override or DEFAULT_HF_INSTRUCT_REVISION
    else:
        hf_model = hf_override or os.environ.get("CLAYCOG_HF_MODEL", DEFAULT_HF_MODEL)
        revision = revision_override or os.environ.get("CLAYCOG_HF_REVISION", DEFAULT_HF_REVISION)
    explicit_template = template_override or os.environ.get("CLAYCOG_TOGETHER_TEMPLATE")
    template = explicit_template or hf_model
    return hf_model, revision, template, bool(explicit_template)


def assert_immutable_revision(revision):
    value = (revision or "").strip()
    if value.lower() in {"", "main", "master", "latest", "head"}:
        raise SystemExit("HF_REVISION_ABORT: pin an immutable Hugging Face revision")
    return value


def assert_create_template_safe(hf_model, template):
    if template != hf_model:
        raise SystemExit(
            "TEMPLATE_COMPATIBILITY_ABORT billed create requires template == from_hf_model; "
            f"got template={template!r}, from_hf_model={hf_model!r}. "
            "Use preflight only until Together exposes a size/architecture-matched base."
        )


def run_local_checks(corpus_version):
    suffix = "v2" if corpus_version == "v2" else "v1"
    generator = HERE / f"generate_sft_{suffix}.py"
    train = HERE / f"train_{suffix}.jsonl"
    valid = HERE / f"validation_{suffix}.jsonl"
    subprocess.run([sys.executable, str(generator)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(train)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(valid)], check=True)
    return train, valid


def get_full_training_limits(client, template):
    """Read full-training limits across current SDK v2 and the immediately older surface."""
    ft = client.fine_tuning
    if hasattr(ft, "get_model_limits"):
        limits = ft.get_model_limits(model=template)
        supported = getattr(limits, "full_training", None) is not None
        surface = "get_model_limits"
    elif hasattr(ft, "model_limits"):
        limits = ft.model_limits(model_name=template)
        supported = bool(getattr(limits, "supports_full_training", False))
        surface = "model_limits"
    else:
        raise SystemExit("Together SDK exposes no recognized fine-tuning model-limits surface")
    if not supported:
        raise SystemExit(f"Template is not full-FT capable/admitted: {template}")
    return limits, surface


def wait_file(client, file_id, timeout_seconds=FILE_WAIT_SECONDS):
    deadline = time.monotonic() + timeout_seconds
    while True:
        meta = client.files.retrieve(file_id)
        if getattr(meta, "processed", None) is True:
            return meta
        status = str(getattr(meta, "processing_status", "") or "").upper()
        if status == "COMPLETED":
            return meta
        if status in {"INVALID_FORMAT", "FAILED", "ERROR"}:
            raise RuntimeError(
                f"Together rejected {file_id}: {status} "
                f"{getattr(meta, 'validation_report', None)}"
            )
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)


def estimate_full_sft_price(client, train_file_id, valid_file_id, template):
    return client.fine_tuning.estimate_price(
        training_file=train_file_id,
        validation_file=valid_file_id,
        model=template,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method="sft",
        training_type="full",
    )


def campaign_descriptor(*, hf_model, hf_revision, template, train, valid, corpus_version):
    return {
        "schema": "claycog-05b-together-campaign/v3",
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision,
        "template_model": template,
        "training_sha256": sha256_file(train),
        "validation_sha256": sha256_file(valid),
        "corpus_version": corpus_version,
        "epochs": EPOCHS,
        "evals": EVALS,
        "training_method": "sft",
        "training_type": "full",
        "train_on_inputs": "auto",
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": 0.03,
        "random_seed": RANDOM_SEED,
        "n_checkpoints": 1,
    }


def campaign_fingerprint(**kwargs):
    raw = json.dumps(
        campaign_descriptor(**kwargs),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def campaign_suffix(fingerprint):
    return "claycog05b-" + fingerprint[:24]


def require_create_confirmation(fingerprint):
    supplied = os.environ.get(CREATE_CONFIRM_ENV, "")
    if supplied != fingerprint:
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} "
            f"to the exact preflight fingerprint {fingerprint}"
        )


def _items(x):
    if x is None:
        return []
    if hasattr(x, "data"):
        return list(x.data or [])
    if isinstance(x, dict):
        return list(x.get("data") or [])
    if isinstance(x, (list, tuple)):
        return list(x)
    return []


def _field(x, name, default=None):
    if isinstance(x, dict):
        return x.get(name, default)
    return getattr(x, name, default)


def _job_suffix(job):
    direct = str(_field(job, "suffix", "") or "")
    if direct:
        return direct
    return str(_field(job, "model_output_name", "") or "")


def matching_campaign_jobs(client, *, hf_model, hf_revision, template, suffix):
    matches = []
    for job in _items(client.fine_tuning.list()):
        status = str(_field(job, "status", "") or "").lower()
        if status and status not in ACTIVE_OR_SPENT_STATUSES:
            continue
        if suffix not in _job_suffix(job):
            continue
        model = _field(job, "model", None)
        from_hf = _field(job, "from_hf_model", None)
        revision = _field(job, "hf_model_revision", None)
        if model not in (None, "", template):
            continue
        if from_hf not in (None, "", hf_model):
            continue
        if revision not in (None, "", hf_revision):
            continue
        matches.append(job)
    return matches


def assert_no_duplicate_campaign(client, **kwargs):
    matches = matching_campaign_jobs(client, **kwargs)
    if matches:
        ids = [str(_field(x, "id", "UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): " + ",".join(ids))


def create_full_sft_job(client, *, train_file_id, valid_file_id, template, hf_model, hf_revision, suffix):
    return client.fine_tuning.create(
        training_file=train_file_id,
        validation_file=valid_file_id,
        model=template,
        from_hf_model=hf_model,
        hf_model_revision=hf_revision,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        n_checkpoints=1,
        learning_rate=LEARNING_RATE,
        warmup_ratio=0.03,
        train_on_inputs="auto",
        training_method="sft",
        training_type="full",
        random_seed=RANDOM_SEED,
        suffix=suffix,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true", help="create one billed fine-tuning job after all exact gates")
    ap.add_argument("--instruct-ablation", action="store_true", help="use Qwen2.5-0.5B-Instruct BYOM checkpoint")
    ap.add_argument("--corpus", choices=("v1", "v2"), default="v2", help="dataset generation; default v2 compositional")
    ap.add_argument("--hf-model", help="explicit Hugging Face model override")
    ap.add_argument("--hf-revision", help="immutable Hugging Face revision override")
    ap.add_argument("--template", help="Together base/template override; create requires exact model identity")
    args = ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    sdk_version = require_sdk()
    hf_model, hf_revision, template, explicit_template = resolve_models(
        instruct_ablation=args.instruct_ablation,
        hf_override=args.hf_model,
        revision_override=args.hf_revision,
        template_override=args.template,
    )
    hf_revision = assert_immutable_revision(hf_revision)
    if args.create:
        assert_create_template_safe(hf_model, template)

    train, valid = run_local_checks(args.corpus)
    descriptor_kwargs = dict(
        hf_model=hf_model,
        hf_revision=hf_revision,
        template=template,
        train=train,
        valid=valid,
        corpus_version=args.corpus,
    )
    fingerprint = campaign_fingerprint(**descriptor_kwargs)
    suffix = campaign_suffix(fingerprint)

    from together import Together
    client = Together()
    limits, limits_surface = get_full_training_limits(client, template)

    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_duplicate_campaign(
            client, hf_model=hf_model, hf_revision=hf_revision, template=template, suffix=suffix
        )

    train_file = client.files.upload(file=str(train), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(valid), purpose="fine-tune", check=True)
    train_meta = wait_file(client, train_file.id)
    valid_meta = wait_file(client, valid_file.id)

    estimate = estimate_full_sft_price(client, train_file.id, valid_file.id, template)
    price = float(estimate.estimated_total_price)
    allowed = bool(estimate.allowed_to_proceed)

    report = {
        "schema": "CLAYCOG_05B_TOGETHER_PREFLIGHT/v3",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "mode": "create" if args.create else "preflight",
        "sdk_version": sdk_version,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "campaign": campaign_descriptor(**descriptor_kwargs),
        "template_source": "explicit_override" if explicit_template else "exact_hf_model_default",
        "template_create_safe": template == hf_model,
        "model_limits_surface": limits_surface,
        "template_full_training": True,
        "training_file_id": train_file.id,
        "validation_file_id": valid_file.id,
        "training_file_status": str(getattr(train_meta, "processing_status", getattr(train_meta, "processed", "UNKNOWN"))),
        "validation_file_status": str(getattr(valid_meta, "processing_status", getattr(valid_meta, "processed", "UNKNOWN"))),
        "estimated_usd": price,
        "max_job_usd": MAX_USD,
        "allowed_to_proceed": allowed,
        "price_detail": objdict(estimate),
        "byom_compatibility": "UNPROVEN_UNTIL_CREATE_ACCEPTS_PINNED_FROM_HF_MODEL",
        "job_started": False,
    }
    print(json.dumps(report, indent=2, default=str))

    if not allowed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(
            "PREFLIGHT_ONLY: no billed job created; "
            f"bind {CREATE_CONFIRM_ENV}={fingerprint} only after reviewing this exact receipt"
        )
        return

    assert_no_duplicate_campaign(
        client, hf_model=hf_model, hf_revision=hf_revision, template=template, suffix=suffix
    )
    try:
        job = create_full_sft_job(
            client,
            train_file_id=train_file.id,
            valid_file_id=valid_file.id,
            template=template,
            hf_model=hf_model,
            hf_revision=hf_revision,
            suffix=suffix,
        )
    except Exception:
        print(
            "CREATE_OUTCOME_UNKNOWN: reconcile account fine-tuning jobs for campaign suffix "
            f"{suffix} before any retry",
            file=sys.stderr,
        )
        raise

    created = {
        "schema": "CLAYCOG_05B_TRAINING_CREATE/v3",
        "job_id": job.id,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision,
        "template_model": template,
        "full_fine_tune": True,
        "estimated_usd": price,
        "create_status": str(getattr(job, "status", "UNKNOWN")),
        "byom_compatibility": "CREATE_ENDPOINT_ACCEPTED_PINNED_CHECKPOINT_LOAD_OR_TRAINING_STILL_UNVERIFIED",
        "next": "retrieve this exact job id; never blind-retry create after an ambiguous outcome",
    }
    print(json.dumps(created, indent=2))


if __name__ == "__main__":
    main()
