#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission resolved before secrets or provider network I/O.

This module reads only canonical repository control-plane files. It does not
inspect API-key environment variables, provider responses, billing endpoints,
or credential files. Those surfaces are downstream of admission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
SUPERVISOR_INBOX_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
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


def _active_supervisor_epoch(supervisor_path: Path | None = None) -> str:
    supervisor = _read_json(supervisor_path or SUPERVISOR_INBOX_PATH, "SUPERVISOR_INBOX")
    if supervisor.get("active_program") != "ENTITYOS_HCU":
        raise ProviderAdmissionError("SUPERVISOR_PROGRAM_MISMATCH")
    if supervisor.get("product") != "EntityOS":
        raise ProviderAdmissionError("SUPERVISOR_PRODUCT_MISMATCH")
    if supervisor.get("integrated_cognition_compute_architecture") != "HCU":
        raise ProviderAdmissionError("SUPERVISOR_ARCHITECTURE_MISMATCH")
    free_only = supervisor.get("free_only")
    if not isinstance(free_only, dict) or free_only.get("enabled") is not True:
        raise ProviderAdmissionError("SUPERVISOR_NOT_FREE_ONLY")
    if free_only.get("provider_execution_requires_typed_explicit_free_classification") is not True:
        raise ProviderAdmissionError("SUPERVISOR_TYPED_FREE_ADMISSION_NOT_REQUIRED")
    epoch = str(supervisor.get("schema_version") or "").strip()
    if not epoch:
        raise ProviderAdmissionError("SUPERVISOR_EPOCH_MISSING")
    return epoch


def load_provider_admission(
    path: Path | None = None,
    *,
    supervisor_path: Path | None = None,
) -> dict[str, Any]:
    """Load canonical admission without touching any provider secret or network surface."""
    payload = _read_json(path or ADMISSION_PATH, "PROVIDER_ADMISSION")

    if payload.get("schema") != SCHEMA:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_SCHEMA_UNSUPPORTED")
    if payload.get("mode") != "FREE_ONLY":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_MODE_NOT_FREE_ONLY")
    if payload.get("product") != "EntityOS" or payload.get("compute_architecture") != "HCU":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PRODUCT_AUTHORITY_MISMATCH")
    if payload.get("source") != "ENTITYOS_HCU_CONTROL_PLANE":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_CONTROL_PLANE_SOURCE_REQUIRED")

    epoch = str(payload.get("authority_epoch") or "")
    supervisor_epoch = _active_supervisor_epoch(supervisor_path)
    if not epoch or epoch != supervisor_epoch:
        raise ProviderAdmissionError(
            f"PROVIDER_ADMISSION_AUTHORITY_EPOCH_MISMATCH:admission={epoch or 'MISSING'}:supervisor={supervisor_epoch}"
        )

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
        if record.get("admitted") is True:
            # A repository toggle is not account evidence. Positive admission must
            # bind the exact provider account/execution class to a durable receipt
            # proving that monetary overage cannot occur. Public free-tier docs,
            # credential presence, HTTP status, or an env attestation are insufficient.
            if record.get("account_scope_verified") is not True:
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_ACCOUNT_SCOPE_UNVERIFIED:{name}")
            if record.get("billable_overage_possible") is not False:
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_BILLABLE_OVERAGE_NOT_FALSE:{name}")
            if record.get("evidence_kind") != "ACCOUNT_SPECIFIC_NONBILLABLE_EXECUTION_EVIDENCE":
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_EVIDENCE_KIND_INVALID:{name}")
            if not evidence_ref.startswith("research_entity/continuity/receipts/"):
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_RECEIPT_REF_REQUIRED:{name}")
            if not isinstance(record.get("account_scope_id"), str) or not record["account_scope_id"].strip():
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_ACCOUNT_SCOPE_ID_REQUIRED:{name}")
            if not isinstance(record.get("verified_at"), str) or not record["verified_at"].strip():
                raise ProviderAdmissionError(f"PROVIDER_ADMISSION_VERIFIED_AT_REQUIRED:{name}")
    return payload


def provider_is_admitted_free(
    provider: str,
    admission: dict[str, Any] | None = None,
    *,
    path: Path | None = None,
    supervisor_path: Path | None = None,
) -> bool:
    if provider not in ALLOWED_PROVIDERS:
        return False
    try:
        payload = admission if admission is not None else load_provider_admission(path, supervisor_path=supervisor_path)
        record = payload["providers"][provider]
    except (ProviderAdmissionError, KeyError, TypeError):
        return False
    return record.get("admitted") is True and record.get("cost_class") == "FREE"


def admitted_provider_names(
    admission: dict[str, Any] | None = None,
    *,
    path: Path | None = None,
    supervisor_path: Path | None = None,
) -> tuple[str, ...]:
    try:
        payload = admission if admission is not None else load_provider_admission(path, supervisor_path=supervisor_path)
    except ProviderAdmissionError:
        return ()
    return tuple(sorted(
        name for name in ALLOWED_PROVIDERS
        if provider_is_admitted_free(name, payload)
    ))


def admission_snapshot(
    path: Path | None = None,
    *,
    supervisor_path: Path | None = None,
) -> dict[str, Any]:
    try:
        payload = load_provider_admission(path, supervisor_path=supervisor_path)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read canonical EntityOS/HCU FREE provider admission")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-free", action="store_true")
    parser.add_argument("--any-free", action="store_true")
    parser.add_argument("--admission", type=Path, default=None, help="explicit deterministic test/admin path")
    parser.add_argument("--supervisor", type=Path, default=None, help="explicit deterministic test/admin path")
    args = parser.parse_args(argv)
    snapshot = admission_snapshot(args.admission, supervisor_path=args.supervisor)
    admitted = snapshot.get("admitted_free_providers", []) if snapshot.get("ok") else []

    if args.list_free:
        print("\n".join(admitted))
    elif args.json or (not args.provider and not args.any_free):
        print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))

    if args.provider:
        if not snapshot.get("ok"):
            return 4
        return 0 if args.provider in admitted else 3
    if args.any_free:
        return 0 if admitted else 3
    return 0 if snapshot.get("ok") else 4


if __name__ == "__main__":
    raise SystemExit(main())
