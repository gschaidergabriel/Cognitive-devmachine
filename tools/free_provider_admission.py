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
SUPERVISOR_INBOX_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
ALLOWED_PROVIDERS = frozenset({"groq", "mistral", "nvidia", "openrouter"})


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


def _alias_program(payload: dict[str, Any], label: str) -> str:
    active = str(payload.get("active_program") or "").strip()
    program = str(payload.get("program") or "").strip()
    if active and program and active != program:
        raise ProviderAdmissionError(f"{label}_PROGRAM_ALIAS_CONFLICT")
    return active or program


def _coalesce_authority(
    inbox: dict[str, Any],
    steering: dict[str, Any],
    key: str,
    *,
    label: str,
) -> str:
    """Resolve an authority value while rejecting any explicit disagreement.

    Current SUPERVISOR_INBOX records may carry product/program identity while their
    referenced historical steering delta deliberately omits those repeated fields.
    Omission is not disagreement. If both surfaces state a value, however, they must
    be byte-equal after string normalization or provider admission fails closed.
    """
    left = str(inbox.get(key) or "").strip()
    right = str(steering.get(key) or "").strip()
    if left and right and left != right:
        raise ProviderAdmissionError(f"SUPERVISOR_{label}_CONFLICT")
    return right or left


def _resolve_current_supervisor(*, inbox_path: Path | None = None, root: Path | None = None) -> tuple[str, str]:
    """Resolve current supervisor authority from inbox + referenced steering.

    The inbox is the successor-dynamic pointer. The referenced steering record must
    match its authority epoch. Program/product/architecture fields may be stated on
    either surface; omission is allowed, but explicit conflicts fail closed.
    """
    repo_root = (root or ROOT).resolve()
    inbox = _read_json(inbox_path or SUPERVISOR_INBOX_PATH, "SUPERVISOR_INBOX")
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_ref = inbox.get("steering")
    if not epoch:
        raise ProviderAdmissionError("SUPERVISOR_EPOCH_REQUIRED")
    if not isinstance(steering_ref, str) or not steering_ref.strip():
        raise ProviderAdmissionError("SUPERVISOR_STEERING_REF_REQUIRED")
    rel = Path(steering_ref)
    if rel.is_absolute() or ".." in rel.parts:
        raise ProviderAdmissionError("SUPERVISOR_STEERING_REF_INVALID")
    steering_path = (repo_root / rel).resolve()
    try:
        steering_path.relative_to(repo_root)
    except ValueError as exc:
        raise ProviderAdmissionError("SUPERVISOR_STEERING_REF_OUTSIDE_REPO") from exc
    steering = _read_json(steering_path, "SUPERVISOR_STEERING")
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise ProviderAdmissionError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")

    inbox_program = _alias_program(inbox, "SUPERVISOR_INBOX")
    steering_program = _alias_program(steering, "SUPERVISOR_STEERING")
    if inbox_program and steering_program and inbox_program != steering_program:
        raise ProviderAdmissionError("SUPERVISOR_PROGRAM_AUTHORITY_CONFLICT")
    resolved_program = steering_program or inbox_program
    product = _coalesce_authority(inbox, steering, "product", label="PRODUCT_AUTHORITY")
    architecture = _coalesce_authority(
        inbox,
        steering,
        "integrated_cognition_compute_architecture",
        label="COMPUTE_ARCHITECTURE_AUTHORITY",
    )
    if resolved_program != "ENTITYOS_HCU" or product != "EntityOS" or architecture != "HCU":
        raise ProviderAdmissionError("SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH")
    return epoch, steering_ref


def load_provider_admission(
    path: Path | None = None,
    *,
    supervisor_inbox_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Load canonical admission without touching any provider secret or network surface."""
    repo_root = (root or ROOT).resolve()
    target = path or (repo_root / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
    epoch, _ = _resolve_current_supervisor(inbox_path=supervisor_inbox_path, root=repo_root)
    payload = _read_json(target, "PROVIDER_ADMISSION")

    if payload.get("schema") != SCHEMA:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_SCHEMA_UNSUPPORTED")
    if payload.get("mode") != "FREE_ONLY":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_MODE_NOT_FREE_ONLY")
    if payload.get("product") != "EntityOS" or payload.get("compute_architecture") != "HCU":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PRODUCT_AUTHORITY_MISMATCH")
    if payload.get("source") != "ENTITYOS_HCU_CONTROL_PLANE":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_CONTROL_PLANE_SOURCE_REQUIRED")

    admission_epoch = str(payload.get("authority_epoch") or "").strip()
    if not admission_epoch or admission_epoch != epoch:
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


def _provider_record_is_admitted_free(payload: dict[str, Any], provider: str) -> bool:
    """Inspect a payload that has already passed ``load_provider_admission`` validation."""
    try:
        record = payload["providers"][provider]
    except (KeyError, TypeError):
        return False
    return record.get("admitted") is True and record.get("cost_class") == "FREE"


def provider_is_admitted_free(provider: str, admission: dict[str, Any] | None = None) -> bool:
    """Resolve FREE admission only from canonical control-plane state.

    ``admission`` is retained for caller compatibility but deliberately ignored. A
    caller-supplied dictionary is untrusted input and must never self-grant provider
    authority. Callers that already hold a validated payload should keep inspection
    internal to this module rather than treating that payload as a capability token.
    """
    del admission
    if provider not in ALLOWED_PROVIDERS:
        return False
    try:
        payload = load_provider_admission()
    except ProviderAdmissionError:
        return False
    return _provider_record_is_admitted_free(payload, provider)


def admitted_provider_names(admission: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Return canonically admitted FREE providers; caller payloads are never authority."""
    del admission
    try:
        payload = load_provider_admission()
    except ProviderAdmissionError:
        return ()
    return tuple(sorted(name for name in ALLOWED_PROVIDERS if _provider_record_is_admitted_free(payload, name)))


def admission_snapshot() -> dict[str, Any]:
    try:
        epoch, steering_ref = _resolve_current_supervisor()
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
        "authority_epoch": epoch,
        "steering": steering_ref,
        "admitted_free_providers": [
            name for name in sorted(ALLOWED_PROVIDERS)
            if _provider_record_is_admitted_free(payload, name)
        ],
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
