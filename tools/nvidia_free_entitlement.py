#!/usr/bin/env python3
"""Fail-closed NVIDIA credential-level FREE hosted-NIM entitlement admission.

This module does not discover credentials and does not contact NVIDIA. It only
validates a canonical, source-controlled receipt set produced from provider-side
entitlement observations. A provider-global documentation statement can never
satisfy this gate.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT_SET_PATH = ROOT / "research_entity/claycode/autonomous/NVIDIA_CREDENTIAL_FREE_ENTITLEMENTS.json"
SET_SCHEMA = "ENTITYOS_HCU_NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_SET/v1"
RECEIPT_SCHEMA = "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT/v1"
NVIDIA_HOST = "integrate.api.nvidia.com"
ENTITLEMENT_CLASS = "NVIDIA_DEVELOPER_PROGRAM_FREE_HOSTED_NIM_PROTOTYPING"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _git_object_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    return len(text) in {40, 64} and all(ch in "0123456789abcdef" for ch in text)


def _evidence_safe(evidence: Any) -> bool:
    if not isinstance(evidence, dict):
        return False
    allowed = {
        "observation_kind",
        "entitlement_class",
        "provider_subject_ref",
        "source_locator",
        "provider_observed_at",
    }
    if set(evidence) - allowed:
        return False
    required = {
        "observation_kind",
        "entitlement_class",
        "provider_subject_ref",
        "source_locator",
        "provider_observed_at",
    }
    if not required.issubset(evidence):
        return False
    if evidence.get("entitlement_class") != ENTITLEMENT_CLASS:
        return False
    for key in required:
        if not isinstance(evidence.get(key), str) or not evidence[key].strip():
            return False
    return _parse_time(evidence.get("provider_observed_at")) is not None


def resolve_nvidia_free_entitlement(
    *,
    credential_fingerprint: str,
    endpoint_host: str,
    typed_admission_epoch: str,
    typed_admission_digest: str,
    receipt_set_path: Path = DEFAULT_RECEIPT_SET_PATH,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Resolve one current credential-bound NVIDIA free entitlement receipt."""
    if not credential_fingerprint or endpoint_host.lower() != NVIDIA_HOST:
        return {"ok": False, "reason": "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND"}
    try:
        raw = receipt_set_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "reason": "NVIDIA_ENTITLEMENT_RECEIPT_SET_INVALID"}
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "NVIDIA_ENTITLEMENT_RECEIPT_SET_INVALID"}
    if (
        payload.get("schema") != SET_SCHEMA
        or payload.get("mode") != "FREE_ONLY"
        or str(payload.get("authority_epoch") or "") != str(typed_admission_epoch)
    ):
        return {"ok": False, "reason": "NVIDIA_ENTITLEMENT_RECEIPT_SET_AUTHORITY_MISMATCH"}
    receipts = payload.get("receipts")
    if not isinstance(receipts, list):
        return {"ok": False, "reason": "NVIDIA_ENTITLEMENT_RECEIPT_SET_INVALID"}

    now_utc = now or dt.datetime.now(dt.timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=dt.timezone.utc)
    now_utc = now_utc.astimezone(dt.timezone.utc)

    valid: list[tuple[dt.datetime, dict[str, Any], dict[str, Any]]] = []
    saw_fingerprint = False
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        if receipt.get("credential_fingerprint") != credential_fingerprint:
            continue
        saw_fingerprint = True
        if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("provider") != "nvidia":
            continue
        if receipt.get("endpoint_host") != NVIDIA_HOST:
            continue
        if str(receipt.get("typed_admission_epoch") or "") != str(typed_admission_epoch):
            continue
        if receipt.get("typed_admission_digest") != typed_admission_digest:
            continue
        source = receipt.get("source_commit_and_tree")
        if (
            not isinstance(source, dict)
            or not _git_object_id(source.get("commit"))
            or not _git_object_id(source.get("tree"))
        ):
            continue
        observed = _parse_time(receipt.get("entitlement_observed_at"))
        if observed is None or observed > now_utc:
            continue
        expires_raw = receipt.get("expires_at")
        if expires_raw is not None:
            expires = _parse_time(expires_raw)
            if expires is None or expires <= now_utc:
                continue
        evidence = receipt.get(
            "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"
        )
        if not _evidence_safe(evidence):
            continue
        if receipt.get("entitlement_evidence_digest") != _digest(evidence):
            continue
        valid.append((observed, receipt, evidence))

    if not valid:
        return {
            "ok": False,
            "reason": (
                "NVIDIA_CREDENTIAL_ENTITLEMENT_RECEIPT_INVALID_OR_STALE"
                if saw_fingerprint
                else "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_NOT_BOUND"
            ),
        }

    _, receipt, evidence = max(valid, key=lambda item: item[0])
    return {
        "ok": True,
        "kind": RECEIPT_SCHEMA,
        "credential_fingerprint": credential_fingerprint,
        "endpoint_host": NVIDIA_HOST,
        "entitlement_observed_at": receipt.get("entitlement_observed_at"),
        "entitlement_evidence_digest": receipt.get("entitlement_evidence_digest"),
        "receipt_digest": _digest(receipt),
        "source_commit_and_tree": receipt.get("source_commit_and_tree"),
        "provider_observation": {
            "observation_kind": evidence.get("observation_kind"),
            "entitlement_class": evidence.get("entitlement_class"),
            "provider_subject_ref": evidence.get("provider_subject_ref"),
            "source_locator": evidence.get("source_locator"),
            "provider_observed_at": evidence.get("provider_observed_at"),
        },
        "assertion": "BOUND_CREDENTIAL_NVIDIA_DEVELOPER_FREE_NIM_PROTOTYPING_ONLY",
    }
