#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
SOURCE = "ENTITYOS_HCU_CONTROL_PLANE"
PRODUCT = "EntityOS"
ARCHITECTURE = "HCU"
MODE = "FREE_ONLY"
MIN_AUTHORITY_EPOCH = (8, 67)
SUPPORTED_PROVIDERS = ("groq", "mistral", "nvidia", "openrouter")
FORBIDDEN_COST_CLASSES = {"PAID", "SUBSCRIPTION", "UNKNOWN"}

class ProviderAdmissionError(RuntimeError):
    pass

@dataclass(frozen=True)
class ProviderAdmission:
    authority_epoch: str
    admission_set_id: str
    expires_at: str
    providers: tuple[str, ...]
    source_path: str


def _epoch_tuple(raw: Any) -> tuple[int, ...]:
    try:
        parts = tuple(int(x) for x in str(raw).split("."))
    except ValueError as exc:
        raise ProviderAdmissionError("AUTHORITY_EPOCH_INVALID") from exc
    if not parts:
        raise ProviderAdmissionError("AUTHORITY_EPOCH_INVALID")
    return parts


def _parse_time(raw: Any) -> dt.datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ProviderAdmissionError("EXPIRES_AT_REQUIRED")
    value = raw.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProviderAdmissionError("EXPIRES_AT_INVALID") from exc
    if parsed.tzinfo is None:
        raise ProviderAdmissionError("EXPIRES_AT_TIMEZONE_REQUIRED")
    return parsed.astimezone(dt.timezone.utc)


def load_provider_admission(path: str | os.PathLike[str], *, now: dt.datetime | None = None) -> ProviderAdmission:
    p = Path(path)
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProviderAdmissionError("ADMISSION_FILE_MISSING") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderAdmissionError("ADMISSION_FILE_UNREADABLE_OR_INVALID_JSON") from exc
    if not isinstance(payload, dict):
        raise ProviderAdmissionError("ADMISSION_OBJECT_REQUIRED")
    required = {
        "schema": SCHEMA,
        "source": SOURCE,
        "product": PRODUCT,
        "compute_architecture": ARCHITECTURE,
        "mode": MODE,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise ProviderAdmissionError(f"{key.upper()}_MISMATCH")
    if _epoch_tuple(payload.get("authority_epoch")) < MIN_AUTHORITY_EPOCH:
        raise ProviderAdmissionError("AUTHORITY_EPOCH_STALE")
    admission_set_id = payload.get("admission_set_id")
    if not isinstance(admission_set_id, str) or not admission_set_id.strip():
        raise ProviderAdmissionError("ADMISSION_SET_ID_REQUIRED")
    expires = _parse_time(payload.get("expires_at"))
    current = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    if expires <= current:
        raise ProviderAdmissionError("ADMISSION_EXPIRED")
    rows = payload.get("providers")
    if not isinstance(rows, list):
        raise ProviderAdmissionError("PROVIDERS_LIST_REQUIRED")
    seen: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ProviderAdmissionError("PROVIDER_ROW_OBJECT_REQUIRED")
        name = row.get("name")
        cost_class = row.get("cost_class")
        admission_id = row.get("admission_id")
        if name not in SUPPORTED_PROVIDERS:
            raise ProviderAdmissionError("PROVIDER_UNSUPPORTED")
        if name in seen:
            raise ProviderAdmissionError("PROVIDER_DUPLICATE")
        if cost_class in FORBIDDEN_COST_CLASSES:
            raise ProviderAdmissionError(f"PROVIDER_{name.upper()}_{cost_class}_FORBIDDEN")
        if cost_class != "FREE":
            raise ProviderAdmissionError(f"PROVIDER_{name.upper()}_COST_CLASS_NOT_FREE")
        if not isinstance(admission_id, str) or not admission_id.strip():
            raise ProviderAdmissionError(f"PROVIDER_{name.upper()}_ADMISSION_ID_REQUIRED")
        seen[name] = admission_id.strip()
    # The current supervisor pools generic provider secret sources. Therefore every
    # supported provider must be explicitly FREE before *any* pooled secret source
    # is read. This is intentionally stricter than per-provider admission.
    if set(seen) != set(SUPPORTED_PROVIDERS):
        raise ProviderAdmissionError("ALL_SUPPORTED_PROVIDERS_REQUIRE_EXPLICIT_FREE_ADMISSION")
    return ProviderAdmission(
        authority_epoch=str(payload["authority_epoch"]),
        admission_set_id=admission_set_id.strip(),
        expires_at=expires.isoformat(),
        providers=tuple(SUPPORTED_PROVIDERS),
        source_path=str(p),
    )


def shell_exports(admission: ProviderAdmission) -> str:
    values = {
        "CLAY_TYPED_PROVIDER_ADMISSION_VERIFIED": "1",
        "CLAY_PROVIDER_ADMISSION_FILE": admission.source_path,
        "CLAY_PROVIDER_ADMISSION_SET_ID": admission.admission_set_id,
        "CLAY_PROVIDER_ADMISSION_AUTHORITY_EPOCH": admission.authority_epoch,
        "CLAY_FREE_ONLY_ATTESTED": "1",
        "CLAY_GROQ_FREE_ATTESTED": "1",
        "CLAY_MISTRAL_FREE_ATTESTED": "1",
        "CLAY_NVIDIA_FREE_ATTESTED": "1",
        "CLAY_OPENROUTER_FREE_ATTESTED": "1",
    }
    return "\n".join(f"export {k}={shlex.quote(v)}" for k, v in values.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--emit-shell", action="store_true")
    args = ap.parse_args()
    try:
        admission = load_provider_admission(args.file)
    except ProviderAdmissionError as exc:
        print(json.dumps({"schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1", "ok": False,
                          "status": str(exc), "secret_lookup_count": 0, "network_attempt_count": 0}))
        return 78
    if args.emit_shell:
        print(shell_exports(admission))
    else:
        print(json.dumps({"schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1", "ok": True,
                          "status": "TYPED_FREE_PROVIDER_ADMISSION_VERIFIED_PRE_SIDE_EFFECT",
                          "authority_epoch": admission.authority_epoch,
                          "admission_set_id": admission.admission_set_id,
                          "providers": list(admission.providers),
                          "secret_lookup_count": 0, "network_attempt_count": 0}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
