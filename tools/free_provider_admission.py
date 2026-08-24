#!/usr/bin/env python3
"""Typed pre-secret provider admission for the EntityOS/HCU FREE_ONLY swarm.

The production admission object is bound to the active supervisor epoch/steering.
Environment attestations, credentials, provider names, previous HTTP success, and
fields inside an arbitrary external JSON object cannot mint FREE authority.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
CONTROL_PLANE = "ENTITYOS_HCU_CONTROL_PLANE"
KNOWN_PROVIDERS = ("groq", "mistral", "nvidia")
VALID_COST_CLASSES = {"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
CANONICAL_ADMISSION = Path(os.getenv("CLAY_PROVIDER_ADMISSION_FILE", "/artifacts/clay-entityos-swarm/provider-admission.json"))


class ProviderAdmissionError(ValueError):
    """Fail-closed provider admission error raised before secret/network access."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProviderAdmissionError(f"{label}_unavailable:{exc.__class__.__name__}") from exc
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderAdmissionError(f"{label}_invalid_json") from exc
    if not isinstance(obj, dict):
        raise ProviderAdmissionError(f"{label}_not_object")
    return obj


def load_admission(path: Path = CANONICAL_ADMISSION) -> dict[str, Any]:
    return _read_json(Path(path), "admission")


def active_supervisor_binding(path: Path = SUPERVISOR_INBOX) -> tuple[str, str]:
    inbox = _read_json(path, "supervisor_inbox")
    epoch = str(inbox.get("schema_version", "")).strip()
    steering = str(inbox.get("steering", "")).strip()
    if not epoch:
        raise ProviderAdmissionError("supervisor_epoch_missing")
    if not steering:
        raise ProviderAdmissionError("supervisor_steering_missing")
    return epoch, steering


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ProviderAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ProviderAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _validate_free_evidence(provider: str, item: dict[str, Any]) -> None:
    evidence = item.get("cost_evidence")
    if not isinstance(evidence, dict):
        raise ProviderAdmissionError(f"provider_free_evidence_missing:{provider}")
    if not isinstance(evidence.get("evidence_ref"), str) or not evidence["evidence_ref"].strip():
        raise ProviderAdmissionError(f"provider_free_evidence_ref_missing:{provider}")
    if not isinstance(evidence.get("checked_at"), str) or not evidence["checked_at"].strip():
        raise ProviderAdmissionError(f"provider_free_evidence_checked_at_missing:{provider}")
    if evidence.get("claim") != "ZERO_MONETARY_COST_FOR_BOUND_PROVIDER_SCOPE":
        raise ProviderAdmissionError(f"provider_free_evidence_claim_invalid:{provider}")
    if evidence.get("scope") != provider:
        raise ProviderAdmissionError(f"provider_free_evidence_scope_mismatch:{provider}")
    _sha256(evidence.get("evidence_sha256"), f"provider_free_evidence_sha256:{provider}")


def validate_document(
    obj: dict[str, Any],
    *,
    supervisor_binding: tuple[str, str] | None = None,
) -> dict[str, Any]:
    if obj.get("schema") != SCHEMA:
        raise ProviderAdmissionError("admission_wrong_schema")
    if obj.get("source") != CONTROL_PLANE:
        raise ProviderAdmissionError("admission_wrong_source")
    if obj.get("free_only") is not True:
        raise ProviderAdmissionError("admission_global_free_only_missing")

    expected_epoch, expected_steering = supervisor_binding or active_supervisor_binding()
    if str(obj.get("authority_epoch", "")).strip() != expected_epoch:
        raise ProviderAdmissionError("admission_stale_or_wrong_authority_epoch")
    if str(obj.get("supervisor_steering", "")).strip() != expected_steering:
        raise ProviderAdmissionError("admission_wrong_supervisor_steering")

    providers = obj.get("providers")
    if not isinstance(providers, dict):
        raise ProviderAdmissionError("admission_providers_not_object")
    extra = sorted(set(providers) - set(KNOWN_PROVIDERS))
    if extra:
        raise ProviderAdmissionError("unknown_provider_entries:" + ",".join(extra))
    return providers


def provider_decision(
    obj: dict[str, Any],
    provider: str,
    *,
    supervisor_binding: tuple[str, str] | None = None,
) -> tuple[bool, str]:
    provider = str(provider).strip().lower()
    if provider not in KNOWN_PROVIDERS:
        return False, f"provider_unknown:{provider or 'EMPTY'}"
    providers = validate_document(obj, supervisor_binding=supervisor_binding)
    item = providers.get(provider)
    if item is None:
        return False, f"provider_missing:{provider}"
    if not isinstance(item, dict):
        return False, f"provider_not_object:{provider}"
    raw_class = item.get("cost_class", "UNKNOWN")
    if not isinstance(raw_class, str):
        return False, f"provider_cost_class_invalid:{provider}:NON_STRING"
    cost_class = raw_class.strip().upper() or "UNKNOWN"
    if cost_class not in VALID_COST_CLASSES:
        return False, f"provider_cost_class_invalid:{provider}:{cost_class}"
    if cost_class != "FREE":
        if item.get("admitted") is True:
            return False, f"provider_nonfree_cannot_be_admitted:{provider}:{cost_class}"
        return False, f"provider_cost_class_denied:{provider}:{cost_class}"
    if item.get("admitted") is not True:
        return False, f"provider_not_admitted:{provider}"
    _validate_free_evidence(provider, item)
    return True, "FREE"


def admitted_providers(
    obj: dict[str, Any],
    *,
    supervisor_binding: tuple[str, str] | None = None,
) -> tuple[str, ...]:
    validate_document(obj, supervisor_binding=supervisor_binding)
    admitted: list[str] = []
    for provider in KNOWN_PROVIDERS:
        allowed, _reason = provider_decision(obj, provider, supervisor_binding=supervisor_binding)
        if allowed:
            admitted.append(provider)
    return tuple(admitted)


def validate_admission(
    obj: dict[str, Any],
    require_all: bool = False,
    *,
    supervisor_binding: tuple[str, str] | None = None,
) -> tuple[str, ...]:
    providers = validate_document(obj, supervisor_binding=supervisor_binding)
    if require_all:
        for provider in KNOWN_PROVIDERS:
            if provider not in providers:
                raise ProviderAdmissionError(f"provider_missing:{provider}")
    admitted = admitted_providers(obj, supervisor_binding=supervisor_binding)
    if require_all and admitted != KNOWN_PROVIDERS:
        missing = [p for p in KNOWN_PROVIDERS if p not in admitted]
        raise ProviderAdmissionError("all_provider_free_admission_required:" + ",".join(missing))
    if not admitted:
        raise ProviderAdmissionError("no_provider_admitted")
    return admitted


def require_provider_admitted(provider: str, *, path: Path = CANONICAL_ADMISSION) -> None:
    obj = load_admission(path)
    allowed, reason = provider_decision(obj, provider)
    if not allowed:
        raise ProviderAdmissionError(reason)


def admitted_providers_from_path(path: Path = CANONICAL_ADMISSION) -> tuple[str, ...]:
    admitted = admitted_providers(load_admission(path))
    if not admitted:
        raise ProviderAdmissionError("no_provider_admitted")
    return admitted


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed EntityOS/HCU FREE_ONLY provider admission")
    parser.add_argument("path", nargs="?", type=Path, default=CANONICAL_ADMISSION)
    parser.add_argument("--provider", choices=KNOWN_PROVIDERS)
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        obj = load_admission(args.path)
        if args.provider:
            allowed, reason = provider_decision(obj, args.provider)
            if not allowed:
                raise ProviderAdmissionError(reason)
            admitted = (args.provider,)
        else:
            admitted = validate_admission(obj, require_all=args.require_all)
    except ProviderAdmissionError as exc:
        if args.json:
            print(json.dumps({"schema": "FREE_PROVIDER_ADMISSION_CHECK/v2", "allowed": False, "reason": str(exc)}, sort_keys=True))
        else:
            print(f"DENY:{exc}", file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps({"schema": "FREE_PROVIDER_ADMISSION_CHECK/v2", "allowed": True, "providers": admitted}, sort_keys=True))
    else:
        print(",".join(admitted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
