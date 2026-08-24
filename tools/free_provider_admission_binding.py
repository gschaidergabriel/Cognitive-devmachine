#!/usr/bin/env python3
"""Exact identity binding for the canonical FREE provider-admission decision.

This module is not a second admission authority. It always delegates authority to
``free_provider_admission.load_provider_admission()`` and adds only a deterministic
content identity that callers can pin and re-check. A pin can narrow current
canonical authority, never broaden it.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

try:
    from . import free_provider_admission as admission
except ImportError:  # direct execution / tools-on-PYTHONPATH compatibility
    import free_provider_admission as admission

BINDING_SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_BINDING/v1"
DIGEST_DOMAIN = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_SEMANTIC_SHA256/v1"
CANONICALIZATION = "SORTED_COMPACT_UTF8_JSON_NO_NAN/v1"


def _validated_semantic_sha256(payload: dict[str, Any]) -> str:
    """Digest a payload only after its caller has obtained it from canonical validation."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    framed = DIGEST_DOMAIN.encode("utf-8") + b"\x00" + encoded
    return hashlib.sha256(framed).hexdigest()


def current_provider_admission_binding() -> dict[str, str]:
    """Return identity for the currently validated canonical admission payload."""
    payload = admission.load_provider_admission()
    epoch = str(payload.get("authority_epoch") or "").strip()
    if not epoch:
        raise admission.ProviderAdmissionError("PROVIDER_ADMISSION_BINDING_EPOCH_REQUIRED")
    return {
        "schema": BINDING_SCHEMA,
        "authority_epoch": epoch,
        "digest_domain": DIGEST_DOMAIN,
        "canonicalization": CANONICALIZATION,
        "admission_sha256": _validated_semantic_sha256(payload),
    }


def require_current_provider_admission_binding(expected: dict[str, Any]) -> dict[str, str]:
    """Fail closed unless ``expected`` still matches current canonical admission.

    ``expected`` is a constraint, not authority: current canonical admission is
    reloaded on every call before comparison. This preserves revocation while making
    the exact decision revision reproducible in downstream execution receipts.
    """
    if not isinstance(expected, dict) or expected.get("schema") != BINDING_SCHEMA:
        raise admission.ProviderAdmissionError("PROVIDER_ADMISSION_BINDING_SCHEMA_INVALID")
    expected_sha = expected.get("admission_sha256")
    if (
        not isinstance(expected_sha, str)
        or len(expected_sha) != 64
        or any(ch not in "0123456789abcdef" for ch in expected_sha)
    ):
        raise admission.ProviderAdmissionError("PROVIDER_ADMISSION_BINDING_DIGEST_INVALID")

    current = current_provider_admission_binding()
    if expected.get("authority_epoch") != current["authority_epoch"]:
        raise admission.ProviderAdmissionError("PROVIDER_ADMISSION_BINDING_EPOCH_CHANGED")
    if expected_sha != current["admission_sha256"]:
        raise admission.ProviderAdmissionError("PROVIDER_ADMISSION_BINDING_DIGEST_CHANGED")
    return current
