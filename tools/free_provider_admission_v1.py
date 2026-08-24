#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission gate.

This module is deliberately secret-blind. It resolves provider cost/admission
from a typed control-plane document before any caller is allowed to inspect
provider credential variables or perform provider network I/O.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADMISSION_PATH = ROOT / "research_entity/continuity/FREE_PROVIDER_ADMISSIONS.json"
SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
PRODUCT = "EntityOS"
ARCHITECTURE = "HCU"
MODE = "FREE_ONLY"
PROVIDERS = ("groq", "mistral", "nvidia")
COST_CLASSES = {"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}


def admission_path() -> Path:
    # Canonical control-plane path only. Environment variables must not be able
    # to self-grant provider authority by redirecting admission to attacker- or
    # worker-controlled JSON.
    return DEFAULT_ADMISSION_PATH


def _parse_time(raw: Any) -> dt.datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def load_document(path: Path | None = None) -> tuple[dict[str, Any] | None, str]:
    target = path or admission_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "ADMISSION_FILE_MISSING"
    except (OSError, json.JSONDecodeError):
        return None, "ADMISSION_FILE_INVALID"
    if not isinstance(payload, dict):
        return None, "ADMISSION_DOCUMENT_NOT_OBJECT"
    if payload.get("schema") != SCHEMA:
        return None, "ADMISSION_SCHEMA_MISMATCH"
    if payload.get("product") != PRODUCT:
        return None, "ADMISSION_PRODUCT_MISMATCH"
    if payload.get("compute_architecture") != ARCHITECTURE:
        return None, "ADMISSION_ARCHITECTURE_MISMATCH"
    if payload.get("mode") != MODE:
        return None, "ADMISSION_MODE_MISMATCH"
    authority_epoch = payload.get("authority_epoch")
    if not isinstance(authority_epoch, str) or not authority_epoch.strip():
        return None, "ADMISSION_AUTHORITY_EPOCH_MISSING"
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        return None, "ADMISSION_PROVIDERS_MISSING"
    return payload, "DOCUMENT_VALID"


def provider_decision(provider: str, path: Path | None = None, now: dt.datetime | None = None) -> dict[str, Any]:
    name = provider.strip().lower()
    decision: dict[str, Any] = {
        "schema": "ENTITYOS_HCU_PROVIDER_ADMISSION_DECISION/v1",
        "provider": name,
        "admitted": False,
        "cost_class": "UNKNOWN",
        "secret_lookup_allowed": False,
        "network_io_allowed": False,
        "reason": "UNKNOWN_PROVIDER",
        "admission_id": None,
        "authority_epoch": None,
    }
    if name not in PROVIDERS:
        return decision
    payload, status = load_document(path)
    if payload is None:
        decision["reason"] = status
        return decision
    decision["authority_epoch"] = payload.get("authority_epoch")
    row = payload["providers"].get(name)
    if not isinstance(row, dict):
        decision["reason"] = "PROVIDER_ADMISSION_MISSING"
        return decision
    cost_class = str(row.get("cost_class", "UNKNOWN")).upper()
    if cost_class not in COST_CLASSES:
        decision["reason"] = "INVALID_COST_CLASS"
        return decision
    decision["cost_class"] = cost_class
    decision["admission_id"] = row.get("admission_id")
    if cost_class != "FREE":
        decision["reason"] = f"COST_CLASS_{cost_class}_FAIL_CLOSED"
        return decision
    if row.get("admitted") is not True:
        decision["reason"] = "FREE_NOT_EXPLICITLY_ADMITTED"
        return decision
    if row.get("secret_lookup_allowed") is not True or row.get("network_io_allowed") is not True:
        decision["reason"] = "FREE_CAPABILITY_FLAGS_NOT_EXPLICIT"
        return decision
    admission_id = row.get("admission_id")
    if not isinstance(admission_id, str) or not admission_id.strip():
        decision["reason"] = "ADMISSION_ID_MISSING"
        return decision
    expires_at_raw = row.get("expires_at")
    if expires_at_raw is not None:
        expires_at = _parse_time(expires_at_raw)
        if expires_at is None:
            decision["reason"] = "ADMISSION_EXPIRY_INVALID"
            return decision
        current = now or dt.datetime.now(dt.timezone.utc)
        if current.astimezone(dt.timezone.utc) >= expires_at:
            decision["reason"] = "ADMISSION_EXPIRED"
            return decision
    decision.update({
        "admitted": True,
        "secret_lookup_allowed": True,
        "network_io_allowed": True,
        "reason": "EXPLICIT_TYPED_FREE_ADMISSION",
    })
    return decision


def provider_is_free(provider: str, path: Path | None = None) -> bool:
    return bool(provider_decision(provider, path).get("admitted"))


def free_providers(path: Path | None = None) -> list[str]:
    return [name for name in PROVIDERS if provider_is_free(name, path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve typed EntityOS/HCU FREE_ONLY provider admission without reading provider secrets.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--provider", choices=PROVIDERS)
    group.add_argument("--list-free", action="store_true")
    parser.add_argument("--check", action="store_true", help="with --provider: exit 0 only for explicit typed FREE admission")
    parser.add_argument("--json", action="store_true", help="emit the admission decision as JSON")
    args = parser.parse_args(argv)
    if args.list_free:
        print(" ".join(free_providers()))
        return 0
    decision = provider_decision(args.provider)
    if args.json:
        print(json.dumps(decision, sort_keys=True))
    elif not args.check:
        print(decision["reason"])
    return 0 if decision["admitted"] else 10


if __name__ == "__main__":
    raise SystemExit(main())
