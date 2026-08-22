#!/usr/bin/env python3
"""Fail-closed direct Together launcher for the ~1B ClayCode cognition lane.

This lane intentionally uses Together's native fine-tuning model
`Qwen/Qwen3.5-0.8B` rather than the unresolved Qwen2.5-0.5B BYOM path.

Safety properties:
- canonical leakage-free SFT v2 is regenerated and validated before provider contact;
- model id is fixed into the campaign fingerprint;
- full fine-tuning support is checked through model_limits;
- price is estimated before any billed CREATE and capped below the EUR 20 owner ceiling;
- billed CREATE requires the exact preflight fingerprint in an environment variable;
- account-side duplicate jobs are rejected;
- a 0600 local create-intent ledger is armed before the zero-retry billed request;
- ambiguous transport outcomes become UNKNOWN_REMOTE_CREATE and must be reconciled,
  never blindly retried.

No secret is read until main() and no paid job is created without --create.
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
MODEL = os.environ.get("CLAYCOG_08B_MODEL", "Qwen/Qwen3.5-0.8B")
EXPECTED_MODEL = "Qwen/Qwen3.5-0.8B"
EPOCHS = int(os.environ.get("CLAYCOG_EPOCHS", "3"))
EVALS = int(os.environ.get("CLAYCOG_EVALS", "2"))
MAX_USD = float(os.environ.get("CLAYCOG_MAX_JOB_USD", "18.00"))
CREATE_CONFIRM_ENV = "CLAYCOG_CREATE_FINGERPRINT"
CREATE_LEDGER_DIR_ENV = "CLAYCOG_CREATE_LEDGER_DIR"
ACTIVE_OR_SPENT_STATUSES = {
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
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def campaign_descriptor():
    return {
        "schema": "claycog-08b-together-direct-campaign/v1",
        "model": MODEL,
        "training_sha256": sha256_file(TRAIN),
        "validation_sha256": sha256_file(VALID),
        "epochs": EPOCHS,
        "evals": EVALS,
        "training_method": "sft",
        "training_type": "Full",
        "train_on_inputs": "auto",
        "learning_rate": 1e-5,
        "warmup_ratio": 0.03,
        "n_checkpoints": 1,
    }


def campaign_fingerprint():
    raw = json.dumps(
        campaign_descriptor(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def campaign_suffix(fingerprint):
    return "claycog08b-v1-" + fingerprint[:24]


def objdict(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    if isinstance(x, dict):
        return x
    return str(x)


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


def matching_campaign_jobs(client, suffix):
    matches = []
    for job in _items(client.fine_tuning.list()):
        status = str(_field(job, "status", "")).lower()
        if status and status not in ACTIVE_OR_SPENT_STATUSES:
            continue
        output_name = str(_field(job, "model_output_name", "") or "")
        if suffix not in output_name:
            continue
        model = _field(job, "model", None)
        if model not in (None, "", MODEL):
            continue
        matches.append(job)
    return matches


def assert_no_duplicate_campaign(client, suffix):
    matches = matching_campaign_jobs(client, suffix)
    if matches:
        ids = [str(_field(x, "id", "UNKNOWN")) for x in matches]
        raise SystemExit("DUPLICATE_CREATE_ABORT existing campaign job(s): " + ",".join(ids))


def require_create_confirmation(fingerprint):
    supplied = os.environ.get(CREATE_CONFIRM_ENV, "")
    if supplied != fingerprint:
        raise SystemExit(
            f"CREATE_CONFIRMATION_REQUIRED set {CREATE_CONFIRM_ENV} to exact preflight fingerprint {fingerprint}"
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
        raise SystemExit(f"CREATE_LEDGER_UNREADABLE {path}: {exc}") from exc


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


def arm_create_intent(fingerprint, suffix):
    directory = create_ledger_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    path = create_ledger_path(fingerprint)
    payload = {
        "schema": "claycog-together-create-intent/v1",
        "fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "status": "CREATE_ARMED",
        "campaign": campaign_descriptor(),
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


def new_zero_retry_create_client(together_cls):
    return together_cls(max_retries=0)


def validate_static_contract():
    if MODEL != EXPECTED_MODEL:
        raise SystemExit(
            f"MODEL_OVERRIDE_REJECTED expected {EXPECTED_MODEL!r}, got {MODEL!r}; "
            "create a separately reviewed lane for another paid base"
        )
    if not 1 <= EPOCHS <= 20:
        raise SystemExit("EPOCHS_OUT_OF_RANGE")
    if not 0 <= EVALS <= 20:
        raise SystemExit("EVALS_OUT_OF_RANGE")
    if not 0 < MAX_USD <= 18.0:
        raise SystemExit("BUDGET_GATE_OUT_OF_RANGE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--create",
        action="store_true",
        help="create billed job only after exact-fingerprint preflight",
    )
    args = ap.parse_args()

    validate_static_contract()
    local_checks()
    if not os.environ.get("TOGETHER_API_KEY"):
        raise SystemExit("TOGETHER_API_KEY must exist only in the execution environment")

    from together import Together

    client = Together()
    limits = client.fine_tuning.model_limits(model_name=MODEL)
    if not getattr(limits, "supports_full_training", False):
        raise SystemExit(f"MODEL_LIMITS_REJECT full fine-tuning not supported for {MODEL}")

    fingerprint = campaign_fingerprint()
    suffix = campaign_suffix(fingerprint)

    if args.create:
        require_create_confirmation(fingerprint)
        assert_no_local_create_intent(fingerprint)
        assert_no_duplicate_campaign(client, suffix)

    train_file = client.files.upload(file=str(TRAIN), purpose="fine-tune", check=True)
    valid_file = client.files.upload(file=str(VALID), purpose="fine-tune", check=True)
    wait_file(client, train_file.id)
    wait_file(client, valid_file.id)

    estimate = client.fine_tuning.estimate_price(
        training_file=train_file.id,
        validation_file=valid_file.id,
        model=MODEL,
        n_epochs=EPOCHS,
        n_evals=EVALS,
        training_method={"method": "sft", "train_on_inputs": "auto"},
        training_type={"type": "Full"},
    )
    price = float(estimate.estimated_total_price)
    report = {
        "mode": "create" if args.create else "preflight",
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": suffix,
        "model": MODEL,
        "epochs": EPOCHS,
        "evals": EVALS,
        "training_type": "Full",
        "estimated_usd": price,
        "allowed_to_proceed": bool(estimate.allowed_to_proceed),
        "price_detail": objdict(estimate),
        "model_limits_full_ft": True,
    }
    print(json.dumps(report, indent=2, default=str))

    if not estimate.allowed_to_proceed:
        raise SystemExit("Together price/admission endpoint does not allow this job")
    if price > MAX_USD:
        raise SystemExit(f"BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}")
    if not args.create:
        print(
            f"PREFLIGHT_ONLY: no billed job created; bind {CREATE_CONFIRM_ENV}={fingerprint} "
            "for this exact create"
        )
        return

    # Repeat both local and account-side fences immediately before the billed request.
    assert_no_local_create_intent(fingerprint)
    assert_no_duplicate_campaign(client, suffix)
    intent_path = arm_create_intent(fingerprint, suffix)
    create_client = new_zero_retry_create_client(Together)
    try:
        job = create_client.fine_tuning.create(
            training_file=train_file.id,
            validation_file=valid_file.id,
            model=MODEL,
            n_epochs=EPOCHS,
            n_evals=EVALS,
            n_checkpoints=1,
            learning_rate=1e-5,
            warmup_ratio=0.03,
            train_on_inputs="auto",
            lora=False,
            suffix=suffix,
        )
    except Exception as exc:
        update_create_intent(
            intent_path, "UNKNOWN_REMOTE_CREATE", error_class=type(exc).__name__
        )
        raise SystemExit(
            "CREATE_OUTCOME_UNKNOWN local intent retained; do not retry create until exact "
            "provider reconciliation: " + type(exc).__name__
        ) from exc

    update_create_intent(intent_path, "JOB_KNOWN", job_id=job.id)
    print(
        json.dumps(
            {
                "job_id": job.id,
                "campaign_fingerprint": fingerprint,
                "campaign_suffix": suffix,
                "model": MODEL,
                "full_fine_tune": True,
                "estimated_usd": price,
                "local_create_intent": str(intent_path),
                "next": "retrieve this exact job; never blind-retry create after an ambiguous transport outcome",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
