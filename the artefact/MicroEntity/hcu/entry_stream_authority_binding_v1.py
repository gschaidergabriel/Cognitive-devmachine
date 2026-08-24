#!/usr/bin/env python3
"""External stream-authority binding for EntityOS/HCU Typed Entry.

This primitive closes one narrow authority gap: ``EntryPacket.stream_id`` is data carried by
an admitted event, not authority to declare a recurrent executor/J-Space stream.  A stream
used for causal sequence work must therefore be matched against an independently supplied
canonical control-plane/ingress authority binding.

The constructor deliberately does NOT accept an EntryPacket.  Its inputs are authority-side
values.  The data-plane packet is consumed only by the verifier.  This module does not create
a second truth/state/effect store, does not assign sequence ordinals, and grants no runtime,
model, causal, or training credit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from xeno_entry_fabric_v1 import EntryPacket

STREAM_AUTHORITY_SCHEMA = "ENTITYOS_HCU_ENTRY_STREAM_AUTHORITY_BINDING/v1"
STREAM_AUTHORITY_KINDS = frozenset({
    "CANONICAL_STREAM_REGISTRY",
    "CANONICAL_INGRESS_CONTROL_PLANE",
})
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class EntryStreamAuthorityBindingError(ValueError):
    pass


@dataclass(frozen=True)
class EntryStreamAuthorityBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    source_kind: str
    source_id: str
    stream_id: str
    authority_kind: str
    authority_ref: str
    authority_binding_sha256: str
    binding_sha256: str


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise EntryStreamAuthorityBindingError(code)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    _need(
        len(normalized) == 64
        and normalized.lower() == normalized
        and all(ch in "0123456789abcdef" for ch in normalized)
        and normalized not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return normalized


def _generation(value: Any, field: str = "generation") -> int:
    _need(
        not isinstance(value, bool)
        and isinstance(value, int)
        and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _material(binding: EntryStreamAuthorityBinding) -> dict[str, Any]:
    value = asdict(binding)
    value.pop("binding_sha256", None)
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise EntryStreamAuthorityBindingError(f"{field}:CANONICALIZATION_FAILED") from exc


def bind_external_stream_authority(
    *,
    generation: int,
    source_kind: str,
    source_id: str,
    authorized_stream_id: str,
    authority_kind: str,
    authority_ref: str,
    authority_binding_sha256: str,
) -> EntryStreamAuthorityBinding:
    """Bind an authority-side stream assignment without reading an EntryPacket.

    ``authority_binding_sha256`` must come from the caller's canonical deterministic
    control-plane/ingress authority.  Deriving it, the stream id, or the source tuple from an
    untrusted Entry payload would violate this API's authority boundary.
    """
    authority_kind = _text(authority_kind, "authority_kind", 128)
    _need(authority_kind in STREAM_AUTHORITY_KINDS, "STREAM_AUTHORITY_KIND_UNSUPPORTED")
    material = {
        "schema": STREAM_AUTHORITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(generation),
        "source_kind": _text(source_kind, "source_kind", 128),
        "source_id": _text(source_id, "source_id"),
        "stream_id": _text(authorized_stream_id, "authorized_stream_id"),
        "authority_kind": authority_kind,
        "authority_ref": _text(authority_ref, "authority_ref", 1024),
        "authority_binding_sha256": _sha256(authority_binding_sha256, "authority_binding_sha256"),
    }
    provisional = EntryStreamAuthorityBinding(**material, binding_sha256="1" * 64)
    return EntryStreamAuthorityBinding(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "ENTRY_STREAM_AUTHORITY_BINDING"),
    )


def validate_entry_stream_authority_binding(
    binding: EntryStreamAuthorityBinding,
    packet: EntryPacket,
    *,
    expected_authority_binding_sha256: str,
) -> None:
    """Require an admitted Entry stream label to match independent authority evidence."""
    _need(isinstance(binding, EntryStreamAuthorityBinding), "ENTRY_STREAM_AUTHORITY_BINDING_REQUIRED")
    _need(isinstance(packet, EntryPacket), "ENTRY_PACKET_REQUIRED")
    _need(binding.schema == STREAM_AUTHORITY_SCHEMA, "ENTRY_STREAM_AUTHORITY_SCHEMA_UNSUPPORTED")
    _need(
        binding.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "ENTRY_STREAM_AUTHORITY_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _need(binding.authority_kind in STREAM_AUTHORITY_KINDS, "STREAM_AUTHORITY_KIND_UNSUPPORTED")

    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_material(binding), "ENTRY_STREAM_AUTHORITY_BINDING")
    _need(observed == expected, "ENTRY_STREAM_AUTHORITY_BINDING_DIGEST_MISMATCH")

    canonical_authority = _sha256(
        expected_authority_binding_sha256,
        "expected_authority_binding_sha256",
    )
    _need(
        binding.authority_binding_sha256 == canonical_authority,
        "ENTRY_STREAM_EXTERNAL_AUTHORITY_BINDING_MISMATCH",
    )
    _need(packet.stream_id is not None, "ENTRY_STREAM_ID_REQUIRED")
    for left, right, code in (
        (binding.generation, packet.entity_generation, "ENTRY_STREAM_AUTHORITY_GENERATION_MISMATCH"),
        (binding.source_kind, packet.source_kind, "ENTRY_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH"),
        (binding.source_id, packet.source_id, "ENTRY_STREAM_AUTHORITY_SOURCE_ID_MISMATCH"),
        (binding.stream_id, packet.stream_id, "ENTRY_STREAM_AUTHORITY_STREAM_ID_MISMATCH"),
    ):
        _need(left == right, code)


def binding_dict(
    binding: EntryStreamAuthorityBinding,
    packet: EntryPacket,
    *,
    expected_authority_binding_sha256: str,
) -> dict[str, Any]:
    validate_entry_stream_authority_binding(
        binding,
        packet,
        expected_authority_binding_sha256=expected_authority_binding_sha256,
    )
    return asdict(binding)
