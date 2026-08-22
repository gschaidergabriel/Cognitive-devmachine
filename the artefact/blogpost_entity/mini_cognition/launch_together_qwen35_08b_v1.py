#!/usr/bin/env python3
"""Fail-closed direct Together Full-FT launcher for ~1B ClayCode cognition."""

import argparse
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAUNCHER = Path(__file__).resolve()
TRAIN = HERE / "train_v2.jsonl"
VALID = HERE / "validation_v2.jsonl"
EXPECTED_MODEL = "Qwen/Qwen3.5-0.8B"
MODEL = os.environ.get("CLAYCOG_08B_MODEL", EXPECTED_MODEL)
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
RANDOM_SEED = int(os.environ.get("CLAYCOG_RANDOM_SEED", "3407"))
LEARNING_RATE = float(os.environ.get("CLAYCOG_LEARNING_RATE", "1e-5"))
WARMUP_RATIO = float(os.environ.get("CLAYCOG_WARMUP_RATIO", "0.03"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
FILE_WAIT_SECONDS = int(os.environ.get("CLAYCOG_FILE_WAIT_SECONDS", "600"))
CREATE_CONFIRM_ENV = "CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV = "CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT = {
    "pending",
    "queued",
    "running",
    "compressing",
    "uploading",
    "cancel_requested",
    "cancelled",
    "error",
    "completed",
}


def validate_static_contract():
    if MODEL != EXPECTED_MODEL:
        raise SystemExit(f"MODEL_OVERRIDE_REJECTED expected {EXPECTED_MODEL!r}, got {MODEL!r}")
    if not 1 <= EPOCHS <= 20 or not 0 <= EVALS <= 20:
        raise SystemExit("TRAINING_COUNT_OUT_OF_RANGE")
    if RANDOM_SEED < 0 or not 0 < LEARNING_RATE <= 1 or not 0 <= WARMUP_RATIO <= 1:
        raise SystemExit("HYPERPARAMETER_OUT_OF_RANGE")
    if not 0 < MAX_USD <= 18:
        raise SystemExit("BUDGET_GATE_OUT_OF_RANGE")


def local_checks():
    subprocess.run([sys.executable, str(HERE / "generate_sft_v2.py")], check=True)
    subprocess.run(
        [sys.executable, str(HERE / "validate_sft_v2.py"), str(TRAIN), "--against", str(VALID)],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(HERE / "validate_sft_v2.py"), str(VALID), "--against", str(TRAIN)],
        check=True,
    )


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def training_method():
    """REST/estimate semantic representation."""
    return {"method": "sft", "train_on_inputs": "auto"}


def training_type():
    """REST/estimate semantic representation."""
    return {"type": "Full"}


def campaign_descriptor():
    return {
        "schema": "claycog-08b-together-direct-campaign/v3",
        "model": MODEL,
        "launcher_sha256": sha256_file(LAUNCHER),
        "training_sha256": sha256_file(TRAIN),
        "validation_sha256": sha256_file(VALID),
        "epochs": EPOCHS,
        "evals": EVALS,
        "random_seed": RANDOM_SEED,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "training_method": training_method(),
        "training_type": training_type(),
        "n_checkpoints": 1,
    }


def campaign_fingerprint():
    return hashlib.sha256(
        json.dumps(campaign_descriptor(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def campaign_suffix(fp):
    return "claycog08b-v3-" + fp[:24]


def objdict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, dict):
        return value
    return str(value)


def _field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def get_full_training_limits(client):
    limits = client.fine_tuning.model_limits(model_name=MODEL)
    if not getattr(limits, "supports_full_training", False) or getattr(limits, "full_training", None) is None:
        raise SystemExit(f"MODEL_LIMITS_REJECT full fine-tuning not supported for {MODEL}")
    return limits


def wait_file(client, file_id, timeout_seconds=FILE_WAIT_SECONDS):
    deadline = time.monotonic() + timeout_seconds
    while True:
        meta = client.files.retrieve(file_id)
        if getattr(meta, "processed", None) is True or str(
            getattr(meta, "processing_status", "") or ""
        ).upper() == "COMPLETED":
            return meta
        status = str(getattr(meta, "processing_status", "") or "").upper()
        if status in {"INVALID_FORMAT", "FAILED", "ERROR"}:
            raise RuntimeError(f"Together rejected {file_id}: {status}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Together file processing: {file_id}")
        time.sleep(5)


def estimate_price(client, train_id, valid_id):
    return client.fine_tuning.estimate_price(
        training_file=train_id,
        validation_file=valid_id,
        model=MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method=training_method(),
        training_type=training_type(),
    )


def create_payload(train_id, valid_id, suffix, model_limits=None):
    """High-level together-py FineTuningResource.create() kwargs.

    together-py converts these SDK kwargs into the nested REST training_type/training_method
    request internally. Do not pass the REST estimate dictionaries directly to create().
    """
    payload = {
        "training_file": train_id,
        "validation_file": valid_id,
        "model": MODEL,
        "n_epochs": EPOCHS,
        "n_evals": EVALS,
        "n_checkpoints": 1,
        "random_seed": RANDOM_SEED,
        "learning_rate": LEARNING_RATE,
        "warmup_ratio": WARMUP_RATIO,
        "suffix": suffix,
        "lora": False,
        "train_on_inputs": "auto",
        "training_method": "sft",
    }
    if model_limits is not None:
        payload["model_limits"] = model_limits
    return payload


def assert_sdk_create_signature(create_callable, payload):
    """Reject a local SDK call-shape mismatch before the durable create-intent is armed."""
    try:
        inspect.signature(create_callable).bind(**payload)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"SDK_CREATE_SIGNATURE_REJECT {exc}") from exc


def _items(value):
    if value is None:
        return []
    if hasattr(value, "data"):
        return list(value.data or [])
    if isinstance(value, dict):
        return list(value.get("data") or [])
    return list(value) if isinstance(value, (list, tuple)) else []


def matching_campaign_jobs(client, suffix):
    out = []
    for job in _items(client.fine_tuning.list()):
        status = str(_field(job, "status", "")).lower()
        name = str(_field(job, "model_output_name", "") or "")
        if status and status not in ACTIVE_OR_SPENT:
            continue
        if suffix not in name or _field(job, "model", None) not in (None, "", MODEL):
            continue
        out.append(job)
    return out


def assert_no_duplicate_campaign(client, suffix):
    matches = matching_campaign_jobs(client, suffix)
    if matches:
        raise SystemExit(
            "DUPLICATE_CREATE_ABORT existing campaign job(s): "
            + ",".join(str(_field(item, "id", "UNKNOWN")) for item in matches)
        )


def require_create_confirmation(fp):
    if os.environ.get(CREATE_CONFIRM_ENV, "") != fp:
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to exact preflight fingerprint {fp}"
        )


def create_ledger_dir():
    if os.environ.get(CREATE_LEDGER_DIR_ENV):
        return Path(os.environ[CREATE_LEDGER_DIR_ENV]).expanduser()
    return Path.home() / ".local" / "state" / "claycog" / "training"


def create_ledger_path(fp):
    return create_ledger_dir() / (fp + ".json")


def read_create_ledger(fp):
    path = create_ledger_path(fp)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"CREATE_LEDGER_UNREADABLE {path}: {exc}") from exc


def assert_no_local_create_intent(fp):
    entry = read_create_ledger(fp)
    if entry is not None:
        raise SystemExit(
            f"LOCAL_CREATE_INTENT_ABORT fingerprint={fp} status={entry.get('status', 'UNKNOWN')}; "
            "reconcile provider state first"
        )


def _fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def arm_create_intent(fp, suffix):
    directory = create_ledger_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    path = create_ledger_path(fp)
    payload = {
        "schema": "claycog-together-create-intent/v3",
        "fingerprint": fp,
        "campaign_suffix": suffix,
        "status": "CREATE_ARMED",
        "campaign": campaign_descriptor(),
        "created_unix": int(time.time()),
    }
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        assert_no_local_create_intent(fp)
        raise
    with os.fdopen(fd, "wb", closefd=True) as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
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
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write((json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        _fsync_dir(Path(path).parent)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def new_zero_retry_create_client(cls):
    return cls(max_retries=0)


def created_job_identity_mismatches(meta, expected):
    out = {}
    for key, want in expected.items():
        got = _field(meta, key, None)
        if got != want:
            out[key] = {"expected": want, "observed": got}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    validate_static_contract()
    local_checks()

    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    from together import Together

    client = Together()
    limits = get_full_training_limits(client)
    fp = campaign_fingerprint()
    suffix = campaign_suffix(fp)

    if args.create:
        require_create_confirmation(fp)
        assert_no_local_create_intent(fp)
        assert_no_duplicate_campaign(client, suffix)

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    estimate = estimate_price(client, train_file.id, valid_file.id)
    price = float(estimate.estimated_total_price)
    print(
        json.dumps(
            {
                "schema": "CLAYCOG_08B_TOGETHER_DIRECT_PREFLIGHT/v3",
                "mode": "create" if args.create else "preflight",
                "campaign_fingerprint": fp,
                "campaign_suffix": suffix,
                "launcher_sha256": campaign_descriptor()["launcher_sha256"],
                "model": MODEL,
                "random_seed": RANDOM_SEED,
                "learning_rate": LEARNING_RATE,
                "warmup_ratio": WARMUP_RATIO,
                "training_type": training_type(),
                "estimated_usd": price,
                "allowed_to_proceed": bool(estimate.allowed_to_proceed),
                "price_detail": objdict(estimate),
                "model_limits_full_ft": True,
                "byom_fields": "ABSENT_BY_DESIGN",
            },
            indent=2,
            default=str,
        )
    )
    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(
            f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fp} for this exact create"
        )
        return

    # Recheck immediately before the effect boundary. The current high-level Together SDK
    # has a different Python call schema from the nested REST estimate schema. Verify the
    # exact callable shape before arming the durable create-intent so local schema drift
    # cannot masquerade as an ambiguous remote CREATE.
    assert_no_local_create_intent(fp)
    assert_no_duplicate_campaign(client, suffix)
    create_client = new_zero_retry_create_client(Together)
    sdk_payload = create_payload(train_file.id, valid_file.id, suffix, model_limits=limits)
    assert_sdk_create_signature(create_client.fine_tuning.create, sdk_payload)
    intent = arm_create_intent(fp, suffix)

    try:
        job = create_client.fine_tuning.create(**sdk_payload)
    except TypeError as exc:
        # Signature binding above makes an ordinary kwargs mismatch impossible on the same
        # callable. Preserve a distinct local-rejection state if deeper SDK code still raises
        # TypeError before a usable job identity is returned; never silently retry.
        update_create_intent(intent, "LOCAL_SDK_CREATE_REJECTED", error_class=type(exc).__name__)
        raise SystemExit("LOCAL_SDK_CREATE_REJECTED; inspect SDK contract; do not retry blindly") from exc
    except Exception as exc:
        update_create_intent(intent, "UNKNOWN_REMOTE_CREATE", error_class=type(exc).__name__)
        raise SystemExit("CREATE_OUTCOME_UNKNOWN; do not retry until exact provider reconciliation") from exc

    update_create_intent(intent, "JOB_KNOWN", job_id=job.id)
    expected = {
        "training_file": train_file.id,
        "validation_file": valid_file.id,
        "model": MODEL,
        "n_epochs": EPOCHS,
        "n_evals": EVALS,
        "random_seed": RANDOM_SEED,
    }
    try:
        meta = client.fine_tuning.retrieve(id=job.id)
    except Exception as exc:
        raise SystemExit(
            f"JOB_CREATED_IDENTITY_VERIFY_UNAVAILABLE job_id={job.id}; "
            f"inspect this exact job, do not create another: {type(exc).__name__}"
        ) from exc
    mismatches = created_job_identity_mismatches(meta, expected)
    if mismatches:
        raise SystemExit(
            "JOB_CREATED_IDENTITY_MISMATCH job_id="
            + str(job.id)
            + " "
            + json.dumps(mismatches, sort_keys=True, default=str)
        )
    print(
        json.dumps(
            {
                "job_id": job.id,
                "campaign_fingerprint": fp,
                "model": MODEL,
                "estimated_usd": price,
                "local_create_intent": str(intent),
                "created_job_identity": "VERIFIED",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
