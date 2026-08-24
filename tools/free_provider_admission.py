#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission resolved before secrets or provider network I/O.

This module intentionally reads only canonical repository control-plane files. It does
not inspect API-key environment variables, provider responses, billing endpoints, or
credential files. Those surfaces are downstream of admission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
BOOTSTRAP_PATH = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
ALLOWED_PROVIDERS = frozenset({"groq", "mistral", "nvidia"})


class ProviderAdmissionError(RuntimeError):
    pass


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderAdmissionError(f"{label}_UNAVAILABLE_OR_INVALID:{exc.__class__.__name__}") from exc
    if not isinstance(payload, dict):
        raise ProviderAdmissionError(f"{label}_OBJECT_REQUIRED")
    return payload


def load_provider_admission(path: Path | None = None, *, bootstrap_path: Path | None = None) -> dict[str, Any]:
    """Load canonical admission without touching any provider secret or network surface."""
    target = path or ADMISSION_PATH
    bootstrap = _read_json(bootstrap_path or BOOTSTRAP_PATH, "BOOTSTRAP")
    payload = _read_json(target, "PROVIDER_ADMISSION")

    if payload.get("schema") != SCHEMA:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_SCHEMA_UNSUPPORTED")
    if payload.get("mode") != "FREE_ONLY":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_MODE_NOT_FREE_ONLY")
    if payload.get("product") != "EntityOS" or payload.get("compute_architecture") != "HCU":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PRODUCT_AUTHORITY_MISMATCH")
    if payload.get("source") != "ENTITYOS_HCU_CONTROL_PLANE":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_CONTROL_PLANE_SOURCE_REQUIRED")

    epoch = str(payload.get("authority_epoch") or "")
    bootstrap_epoch = str(bootstrap.get("schema_version") or "")
    if not epoch or epoch != bootstrap_epoch:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_AUTHORITY_EPOCH_MISMATCH")

    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PROVIDERS_OBJECT_REQUIRED")
    unknown_names = set(providers) - ALLOWED_PROVIDERS
    if unknown_names:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_UNKNOWN_PROVIDER")

    for name in ALLOWED_PROVIDERS:
        record = providers.get(name)
        if not isinstance(record, dict):
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_RECORD_REQUIRED:{name}")
        cost_class = record.get("cost_class")
        if cost_class not in {"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}:
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_COST_CLASS_INVALID:{name}")
        if not isinstance(record.get("admitted"), bool):
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_BOOLEAN_REQUIRED:{name}")
        if record.get("admitted") is True and cost_class != "FREE":
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_NONFREE_CANNOT_BE_ADMITTED:{name}")
        evidence_ref = record.get("evidence_ref")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_EVIDENCE_REQUIRED:{name}")
    return payload


def provider_is_admitted_free(provider: str, admission: dict[str, Any] | None = None) -> bool:
    if provider not in ALLOWED_PROVIDERS:
        return False
    try:
        payload = admission if admission is not None else load_provider_admission()
        record = payload["providers"][provider]
    except (ProviderAdmissionError, KeyError, TypeError):
        return False
    return record.get("admitted") is True and record.get("cost_class") == "FREE"


def admitted_provider_names(admission: dict[str, Any] | None = None) -> tuple[str, ...]:
    try:
        payload = admission if admission is not None else load_provider_admission()
    except ProviderAdmissionError:
        return ()
    return tuple(sorted(name for name in ALLOWED_PROVIDERS if provider_is_admitted_free(name, payload)))


def admission_snapshot() -> dict[str, Any]:
    try:
        payload = load_provider_admission()
    except ProviderAdmissionError as exc:
        return {
            "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1",
            "ok": False,
            "admitted_free_providers": [],
            "status": str(exc),
        }
    return {
        "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1",
        "ok": True,
        "authority_epoch": payload["authority_epoch"],
        "admitted_free_providers": list(admitted_provider_names(payload)),
        "providers": {
            name: {
                "admitted": bool(payload["providers"][name]["admitted"]),
                "cost_class": payload["providers"][name]["cost_class"],
                "evidence_ref": payload["providers"][name]["evidence_ref"],
            }
            for name in sorted(ALLOWED_PROVIDERS)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read canonical EntityOS/HCU FREE provider admission")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    snapshot = admission_snapshot()
    if args.json or not args.provider:
        print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))
    if args.provider:
        if not snapshot.get("ok"):
            return 4
        return 0 if args.provider in snapshot.get("admitted_free_providers", []) else 3
    return 0 if snapshot.get("ok") else 4


if __name__ == "__main__":
    raise SystemExit(main())
