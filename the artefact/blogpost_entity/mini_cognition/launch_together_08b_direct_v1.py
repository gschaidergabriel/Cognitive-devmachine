#!/usr/bin/env python3
"""Direct Together Full-FT launcher for generic 0.8B ClayCode cognition.

This deliberately removes the old Qwen2.5-0.5B BYOM template/from_hf_model pair.
The exact provider base is Qwen/Qwen3.5-0.8B, currently listed by Together for Full FT.
No billed create occurs without exact fingerprint confirmation and a durable local intent.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN = HERE / "train_v2.jsonl"
VALID = HERE / "validation_v2.jsonl"
BASE_MODEL = "Qwen/Qwen3.5-0.8B"
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
RANDOM_SEED = int(os.environ.get("CLAYCOG_RANDOM_SEED", "3407"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
WARMUP_RATIO = float(os.environ.get("CLAYCOG_WARMUP_RATIO", "0.03"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
FILE_WAIT_SECONDS = int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS", "600"))
CREATE_CONFIRM_ENV = "CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV = "CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT = {"pending", "queued", "running", "compressing", "uploading", "cancel_requested", "cancelled", "error", "completed"}


def run_local_checks():
    subprocess.run([sys.executable, str(HERE / "generate_sft_v2.py")], check=True)
    subprocess.run([sys.executable, str(HERE / "validate_corpus_v2.py"), str(TRAIN), str(VALID)], check=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def campaign_descriptor():
    return {
        "schema": "claycog-08b-together-direct/v1",
        "model": BASE_MODEL,
        "training_sha256": sha256_file(TRAIN),
        "validation_sha256": sha256_file(VALID),
        "epochs": EPOCHS,
        "evals": EVALS,
        "random_seed": RANDOM_SEED,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "training_method": {"method": "sft", "train_on_inputs": "auto"},
        "training_type": {"type": "Full"},
        "n_checkpoints": 1,
    }


def campaign_fingerprint():
    raw = json.dumps(campaign_descriptor(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def campaign_suffix(fingerprint):
    return "claycog08b-" + fingerprint[:24]


def get_full_training_limits(client):
    getter = getattr(client.fine_tuning, "get_model_limits", None)
    if getter is None:
        raise SystemExit("TOGETHER_SDK_V2_REQUIRED: fine_tuning.get_model_limits unavailable")
    limits = getter(model=BASE_MODEL)
    if getattr(limits, "full_training", None) is None:
        raise SystemExit(f"DIRECT_MODEL_NOT_FULL_FT_ADMITTED: {BASE_MODEL}")
    return limits


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
            raise RuntimeError(f"Together rejected {file_id}: {status} {getattr(meta, 'validation_report', None)}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)


def estimate_price(client, train_file_id, valid_file_id):
    return client.fine_tuning.estimate_price(
        training_file=train_file_id,
        validation_file=valid_file_id,
        model=BASE_MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        random_seed=RANDOM_SEED,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
    )


def _items(x):
    if x is None:
        return []
    if hasattr(x, "data"):
        return list(x.data or [])
    if isinstance(x, dict):
        return list(x.get("data") or [])
    return list(x) if isinstance(x, (list, tuple)) else []


def _field(x, name, default=None):
    return x.get(name, default) if isinstance(x, dict) else getattr(x, name, default)


def assert_no_duplicate_campaign(client, suffix):
    matches = []
    for job in _items(client.fine_tuning.list()):
        status = str(_field(job, "status", "")).lower()
        output_name = str(_field(job, "model_output_name", "") or "")
        if status and status not in ACTIVE_OR_SPENT:
            continue
        if suffix not in output_name:
            continue
        if _field(job, "model", None) not in (None, "", BASE_MODEL):
            continue
        matches.append(job)
    if matches:
        ids = ",".join(str(_field(x, "id", "UNKNOWN")) for x in matches)
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): " + ids)


def require_create_confirmation(fingerprint):
    if os.environ.get(CREATE_CONFIRM_ENV, "") != fingerprint:
        raise SystemExit(f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV}={fingerprint}")


def create_ledger_dir():
    if os.environ.get(CREATE_LEDGER_DIR_ENV):
        return Path(os.environ[CREATE_LEDGER_DIR_ENV]).expanduser()
    return Path.home() / ".local" / "state" / "claycog" / "training"


def create_ledger_path(fingerprint):
    return create_ledger_dir() / (fingerprint + ".json")


def assert_no_local_create_intent(fingerprint):
    path = create_ledger_path(fingerprint)
    if path.exists():
        raise SystemExit(f"LOCAL_CREATE_INTENT_ABORT fingerprint={fingerprint}; reconcile provider state before any new billed create")


def _fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def arm_create_intent(fingerprint, suffix):
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
        "campaign": campaign_descriptor(),
        "created_unix": int(time.time()),
    }
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb", closefd=True) as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    _fsync_dir(directory)
    return path


def update_create_intent(path, status, job_id=None, error_class=None):
    payload = json.loads(Path(path).read_text())
    payload["status"] = status
    payload["updated_unix"] = int(time.time())
    if job_id is not None:
        payload["job_id"] = str(job_id)
    if error_class is not None:
        payload["error_class"] = str(error_class)
    tmp = Path(str(path) + f".tmp.{os.getpid()}")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as f:
            f.write((json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        _fsync_dir(Path(path).parent)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def create_payload(train_file_id, valid_file_id, suffix):
    return {
        "training_file": train_file_id,
        "validation_file": valid_file_id,
        "model": BASE_MODEL,
        "n_epochs": EPOCHS,
        "n_evals": EVALS,
        "n_checkpoints": 1,
        "random_seed": RANDOM_SEED,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "suffix": suffix,
        "training_method": {"method": "sft", "train_on_inputs": "auto"},
        "training_type": {"type": "Full"},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true")
    args = ap.parse_args()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    run_local_checks()
    fingerprint = campaign_fingerprint()
    suffix = campaign_suffix(fingerprint)

    from together import Together
    client = Together()
    get_full_training_limits(client)

    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_local_create_intent(fingerprint)
        assert_no_duplicate_campaign(client, suffix)

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    estimate = estimate_price(client, train_file.id, valid_file.id)
    price = float(estimate.estimated_total_price)
    report = {
        "schema": "CLAYCOG_08B_TOGETHER_DIRECT_PREFLIGHT/v1",
        "mode": "create" if args.create else "preflight",
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "model": BASE_MODEL,
        "epochs": EPOCHS,
        "evals": EVALS,
        "random_seed": RANDOM_SEED,
        "estimated_usd": price,
        "allowed_to_proceed": bool(estimate.allowed_to_proceed),
        "provider_admission": "DIRECT_MODEL_LIMITS_FULL_FT_ACCEPTED",
        "byom_fields": "ABSENT_BY_DESIGN",
    }
    print(json.dumps(report, indent=2, default=str))
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} for exact create")
        return

    assert_no_local_create_intent(fingerprint)
    assert_no_duplicate_campaign(client, suffix)
    intent_path = arm_create_intent(fingerprint, suffix)
    create_client = Together(max_retries=0)
    try:
        job = create_client.fine_tuning.create(**create_payload(train_file.id, valid_file.id, suffix))
    except Exception as exc:
        update_create_intent(intent_path, "UNKNOWN_REMOTE_CREATE", error_class=type(exc).__name__)
        raise SystemExit("CREATE_OUTCOME_UNKNOWN: do not retry until provider state is reconciled") from exc
    update_create_intent(intent_path, "JOB_KNOWN", job_id=job.id)
    print(json.dumps({"job_id": job.id, "campaign_fingerprint": fingerprint, "model": BASE_MODEL, "estimated_usd": price, "local_create_intent": str(intent_path)}, indent=2))


if __name__ == "__main__":
    main()
