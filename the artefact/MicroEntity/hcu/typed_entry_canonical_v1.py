#!/usr/bin/env python3
"""Compatibility adapter for the main-selected EntityOS/HCU causal canonicalizer.

Historical versions of this module implemented the bounded
`ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1` encoder. Current main authority selects
`RFC8785_JCS_IJSON/v1` in `entry_canonicalization_v1.py` for new Entry + HCU causal
identities. This compatibility filename remains so existing imports converge on that one
encoder instead of retaining a second active canonicalization path.

Historical CBOR hashes remain valid only at their original schema/source scope. They are
never silently rehashed or reinterpreted as RFC 8785/JCS identities.
"""
from __future__ import annotations

from typing import Any

try:
    from .entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
except ImportError:
    from entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )

LEGACY_CANONICALIZATION_SCHEMA = "ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1"
ADAPTER_SCHEMA = "ENTITYOS_HCU_ENTRY_CANONICAL_ADAPTER/v2"


class CanonicalEncodingError(ValueError):
    """Compatibility exception for callers of the historical module API."""


def encode_canonical(value: Any) -> bytes:
    """Encode through the single main-selected RFC 8785/JCS implementation."""
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise CanonicalEncodingError(str(exc)) from exc
