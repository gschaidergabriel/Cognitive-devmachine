#!/usr/bin/env python3
"""Spend-safe Together BYOM launcher for the generic 0.5B ClayCode cognition campaign.

The default mode is preflight. It regenerates and validates the selected corpus, binds
an immutable Hugging Face revision, checks Together's full-training surface, validates
remote files, and requests a server-side price/admission estimate. Billed CREATE is
possible only after exact campaign-fingerprint confirmation.

Safety boundary:
- default template/base is the exact 0.5B Hugging Face model id, never a silently guessed
  1.5B/7B surrogate;
- an explicit different template may be inspected in preflight, but billed create is
  fail-closed while template != from_hf_model;
- each paid campaign has an atomic local create-intent ledger;
- the non-idempotent CREATE uses a zero-retry SDK client;
- ambiguous CREATE outcomes stay UNKNOWN_REMOTE_CREATE and block blind retry;
- model-limits/price/create acceptance are not model-quality or runtime-RSS evidence.
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
TRAIN = HERE / "train_v1.jsonl"   # compatibility default for v1 safety tests
VALID = HERE / "validation_v1.jsonl"
HF_MODEL = os.environ.get("CLAYCOG_HF_MODEL", "Qwen/Qwen2.5-0.5B")
HF_MODEL_INSTRUCT = "Qwen/Qwen2.5-0.5B-Instruct"
HF_REVISION = os.environ.get(
    "CLAYCOG_HF_REVISION", "060db6499f32faf8b98477b0a26969ef7d8b9987"
)
HF_REVISION_INSTRUCT = os.environ.get(
    "CLAYCOG_HF_REVISION_INSTRUCT", "7ae557604adf67be50417f59c2c2f167def9a775"
)
# Exact same model is the spend-safe default. An explicit override is preflight-only
# until a separate evidence-backed compatibility rule is admitted.
TEMPLATE = os.environ.get("CLAYCOG_TOGETHER_TEMPLATE", HF_MODEL)
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
RANDOM_SEED = int(os.environ.get("CLAYCOG_TRAIN_SEED", "20260822"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
FILE_WAIT_SECONDS = int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS", "600"))
CREATE_CONFIRM_ENV = "CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV = "CLAYCOG_CREATE_LEDGER_DIR"
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


def require_sdk_v2():
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


def assert_immutable_revision(revision):
    value = str(revision or "").strip()
    if value.lower() in {"", "main", "master", "latest", "head"}:
        raise SystemExit("HF_REVISION_ABORT: pin an immutable Hugging Face revision")
    return value


def assert_create_template_safe(hf_model, template):
    if template != hf_model:
        raise SystemExit(
            "TEMPLATE_COMPATIBILITY_ABORT billed create requires template == from_hf_model; "
            f"got template={template!r}, from_hf_model={hf_model!r}. "
            "Inspect alternate templates in preflight only until an evidence-backed compatibility rule is admitted."
        )


def corpus_paths(corpus_version):
    if corpus_version not in {"v1", "v2"}:
        raise ValueError(f"unsupported corpus version: {corpus_version}")
    return HERE / f"train_{corpus_version}.jsonl", HERE / f"validation_{corpus_version}.jsonl"


def run_local_checks(corpus_version="v2"):
    generator = HERE / f"generate_sft_{corpus_version}.py"
    train, valid = corpus_paths(corpus_version)
    subprocess.run([sys.executable, str(generator)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(train)], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_sft_v1.py"), str(valid)], check=True)
    return train, valid


def get_full_training_limits(client, template):
    """Support current SDK v2 plus the immediately older model-limits method; fail closed."""
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
                f"Together rejected {file_id}: {status} {getattr(meta, 'validation_report', None)}"
            )
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)


def estimate_full_sft_price(client, training_file_id, validation_file_id, template):
    return client.fine_tuning.estimate_price(
        training_file=training_file_id,
        validation_file=validation_file_id,
        model=template,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method="sft",
        training_type="full",
    )


def campaign_descriptor(
    hf_model,
    *,
    hf_revision=None,
    template=None,
    train=None,
    valid=None,
    corpus_version="v1",
):
    """Deterministic paid-campaign identity. Defaults preserve v1 safety-test API."""
    train = Path(train or TRAIN)
    valid = Path(valid or VALID)
    hf_revision = hf_revision or HF_REVISION
    template = template or TEMPLATE
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


def campaign_fingerprint(hf_model, **kwargs):
    raw = json.dumps(
        campaign_descriptor(hf_model, **kwargs),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def campaign_suffix(fingerprint):
    return "claycog05b-" + fingerprint[:24]


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


def matching_campaign_jobs(client, hf_model, template, suffix, hf_revision=None):
    """Account-side duplicate defense; local create-intent ledger remains stronger."""
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
        if hf_revision is not None and revision not in (None, "", hf_revision):
            continue
        matches.append(job)
    return matches


def assert_no_duplicate_campaign(client, hf_model, template, suffix, hf_revision=None):
    matches = matching_campaign_jobs(client, hf_model, template, suffix, hf_revision)
    if matches:
        ids = [str(_field(x, "id", "UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): " + ",".join(ids))


def require_create_confirmation(fingerprint):
    supplied = os.environ.get(CREATE_CONFIRM_ENV, "")
    if supplied != fingerprint:
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to the exact preflight fingerprint {fingerprint}"
        )


def create_ledger_dir():
    configured = os.environ.get(CREATE_LEDGER_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "state" / "claycog" / "training"


def create_ledger_path(fingerprint):
    return create_ledger_dir() / (fingerprint + ".json")


def read_create_ledger(fingerprint):
    path = create_ledger_path(fingerprint)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"CREATE_LEDGER_UNREADABLE {path}: {exc}")


def assert_no_local_create_intent(fingerprint):
    existing = read_create_ledger(fingerprint)
    if existing is None:
        return
    status = str(existing.get("status", "UNKNOWN"))
    job_id = existing.get("job_id")
    suffix = f" job_id={job_id}" if job_id else ""
    raise SystemExit(
        f"LOCAL_CREATE_INTENT_ABORT fingerprint={fingerprint} status={status}{suffix}; "
        "reconcile exact provider state before any new billed create"
    )


def _fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def arm_create_intent(fingerprint, hf_model, suffix, campaign=None):
    """Atomically reserve one paid campaign before the non-idempotent remote POST."""
    directory = create_ledger_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    path = create_ledger_path(fingerprint)
    payload = {
        "schema": "claycog-together-create-intent/v2",
        "fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "status": "CREATE_ARMED",
        "campaign": campaign if campaign is not None else campaign_descriptor(hf_model),
        "created_unix": int(time.time()),
    }
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        assert_no_local_create_intent(fingerprint)
        raise
    try:
        with os.fdopen(fd, "wb", closefd=True) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        _fsync_dir(directory)
    except BaseException:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path


def update_create_intent(path, status, job_id=None, error_class=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload["status"] = status
    payload["updated_unix"] = int(time.time())
    if job_id is not None:
        payload["job_id"] = str(job_id)
    if error_class is not None:
        payload["error_class"] = str(error_class)
    tmp = Path(str(path) + f".tmp.{os.getpid()}")
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        _fsync_dir(Path(path).parent)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def new_zero_retry_create_client(together_cls):
    return together_cls(max_retries=0)


def create_full_sft_job(client, *, training_file_id, validation_file_id, template, hf_model, hf_revision, suffix):
    return client.fine_tuning.create(
        training_file=training_file_id,
        validation_file=validation_file_id,
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
    ap.add_argument("--instruct-ablation", action="store_true", help="use Qwen2.5-0.5B-Instruct")
    ap.add_argument("--corpus", choices=("v1", "v2"), default="v2", help="default: compositional v2")
    ap.add_argument("--hf-model", help="explicit Hugging Face model override")
    ap.add_argument("--hf-revision", help="immutable Hugging Face revision override")
    ap.add_argument("--template", help="Together template override; billed create requires exact model id")
    args = ap.parse_args()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    sdk_version = require_sdk_v2()
    if args.instruct_ablation:
        hf_model = args.hf_model or HF_MODEL_INSTRUCT
        hf_revision = args.hf_revision or HF_REVISION_INSTRUCT
    else:
        hf_model = args.hf_model or HF_MODEL
        hf_revision = args.hf_revision or HF_REVISION
    hf_revision = assert_immutable_revision(hf_revision)
    explicit_template = args.template or os.environ.get("CLAYCOG_TOGETHER_TEMPLATE")
    template = explicit_template or hf_model
    if args.create:
        assert_create_template_safe(hf_model, template)

    train, valid = run_local_checks(args.corpus)
    campaign = campaign_descriptor(
        hf_model,
        hf_revision=hf_revision,
        template=template,
        train=train,
        valid=valid,
        corpus_version=args.corpus,
    )
    fingerprint = campaign_fingerprint(
        hf_model,
        hf_revision=hf_revision,
        template=template,
        train=train,
        valid=valid,
        corpus_version=args.corpus,
    )
    suffix = campaign_suffix(fingerprint)

    from together import Together
    client = Together()
    _, limits_surface = get_full_training_limits(client, template)

    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_local_create_intent(fingerprint)
        assert_no_duplicate_campaign(client, hf_model, template, suffix, hf_revision)

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
        "campaign": campaign,
        "template_source": "explicit_override" if explicit_template else "exact_hf_model_default",
        "template_create_safe": template == hf_model,
        "model_limits_surface": limits_surface,
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

    assert_no_local_create_intent(fingerprint)
    assert_no_duplicate_campaign(client, hf_model, template, suffix, hf_revision)
    intent_path = arm_create_intent(fingerprint, hf_model, suffix, campaign=campaign)
    create_client = new_zero_retry_create_client(Together)
    try:
        job = create_full_sft_job(
            create_client,
            training_file_id=train_file.id,
            validation_file_id=valid_file.id,
            template=template,
            hf_model=hf_model,
            hf_revision=hf_revision,
            suffix=suffix,
        )
    except Exception as exc:
        update_create_intent(intent_path, "UNKNOWN_REMOTE_CREATE", error_class=type(exc).__name__)
        raise SystemExit(
            "CREATE_OUTCOME_UNKNOWN local intent retained; do not retry create until exact provider reconciliation: "
            + type(exc).__name__
        ) from exc

    update_create_intent(intent_path, "JOB_KNOWN", job_id=job.id)
    print(json.dumps({
        "schema": "CLAYCOG_05B_TRAINING_CREATE/v3",
        "job_id": job.id,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "from_hf_model": hf_model,
        "hf_model_revision": hf_revision,
        "template_model": template,
        "full_fine_tune": True,
        "estimated_usd": price,
        "local_create_intent": str(intent_path),
        "create_status": str(getattr(job, "status", "UNKNOWN")),
        "byom_compatibility": "CREATE_ACCEPTED_CHECKPOINT_LOAD_OR_TRAINING_STILL_UNVERIFIED",
        "next": "retrieve this exact job id; never blind-retry after an ambiguous create outcome",
    }, indent=2))


if __name__ == "__main__":
    main()
