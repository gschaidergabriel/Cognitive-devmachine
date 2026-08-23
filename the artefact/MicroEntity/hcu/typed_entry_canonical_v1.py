#!/usr/bin/env python3
"""Compatibility adapter for the selected EntityOS/HCU causal canonicalizer.

Historical versions of this module implemented the bounded
`ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1` encoder. Current authority selects
`ENTITYOS_HCU_TYPED_CANONICAL/v1` in `hcu_causal_canonical_v1.py` for new Entry + HCU
causal identities. This compatibility filename remains so existing imports do not create
a second encoder path while the surrounding source is migrated.

Historical CBOR hashes remain valid only at their original schema/source scope. They are
never silently rehashed or reinterpreted as the selected schema.
"""
from __future__ import annotations

from typing import Any

try:
    from .hcu_causal_canonical_v1 import (
        CANONICALIZATION_SCHEMA,
        HCUCanonicalizationError,
        canonical_bytes,
    )
except ImportError:
    from hcu_causal_canonical_v1 import (
        CANONICALIZATION_SCHEMA,
        HCUCanonicalizationError,
        canonical_bytes,
    )

LEGACY_CANONICALIZATION_SCHEMA = "ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1"
ADAPTER_SCHEMA = "ENTITYOS_HCU_ENTRY_CANONICAL_ADAPTER/v1"
SAFE_INTEGER_MAX = 9_007_199_254_740_991


class CanonicalEncodingError(ValueError):
    """Compatibility exception for callers of the historical module API."""


def encode_canonical(value: Any) -> bytes:
    """Encode through the sole selected causal canonicalization implementation.

    This function deliberately contains no independent serialization logic. Any value
    outside the selected canonicalizer's admitted domain fails closed.
    """
    try:
        return canonical_bytes(value)
    except HCUCanonicalizationError as exc:
        raise CanonicalEncodingError(str(exc)) from exc
