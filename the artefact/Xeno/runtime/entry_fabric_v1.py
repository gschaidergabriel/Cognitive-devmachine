from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA_ID = "XENO_INGRESS_PACKET/v1"
ALLOWED_MODALITIES = {
    "text",
    "json",
    "tool_result",
    "sensor",
    "db_event",
    "intrinsic",
    "binary_ref",
}
ALLOWED_PERMISSION_CLASSES = {"read", "candidate", "effect_request"}


class EntryAdmissionError(ValueError):
    """Fail-closed admission error for malformed or stale ingress."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _iso8601_utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EntryAdmissionError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise EntryAdmissionError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_token(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EntryAdmissionError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class ResourceBudget:
    max_cells: int = 10
    max_tokens: int = 4096
    max_wall_ms: int = 30000

    def __post_init__(self) -> None:
        for name, value in (
            ("max_cells", self.max_cells),
            ("max_tokens", self.max_tokens),
            ("max_wall_ms", self.max_wall_ms),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise EntryAdmissionError(f"{name} must be a positive integer")
        if self.max_cells > 600:
            raise EntryAdmissionError("max_cells exceeds current bounded logical scale envelope")

    def as_dict(self) -> dict[str, int]:
        return {
            "max_cells": self.max_cells,
            "max_tokens": self.max_tokens,
            "max_wall_ms": self.max_wall_ms,
        }


@dataclass(frozen=True)
class XenoIngressPacket:
    causal_id: str
    generation: int
    source: str
    provenance: Mapping[str, Any]
    modality: str
    observed_at: str
    received_at: str
    permissions: Sequence[str]
    capability_scope: Sequence[str]
    resource_budget: ResourceBudget
    payload_ref: str
    payload_sha256: str
    parent_or_stream_id: str | None = None
    schema_id: str = field(default=SCHEMA_ID, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "causal_id", _require_token("causal_id", self.causal_id))
        object.__setattr__(self, "source", _require_token("source", self.source))
        object.__setattr__(self, "payload_ref", _require_token("payload_ref", self.payload_ref))
        if not isinstance(self.generation, int) or isinstance(self.generation, bool) or self.generation < 0:
            raise EntryAdmissionError("generation must be a non-negative integer")
        if self.modality not in ALLOWED_MODALITIES:
            raise EntryAdmissionError(f"unsupported modality: {self.modality!r}")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise EntryAdmissionError("provenance must be a non-empty mapping")
        try:
            _canonical_json(self.provenance)
        except (TypeError, ValueError) as exc:
            raise EntryAdmissionError("provenance must be canonical-json serializable") from exc

        observed = _iso8601_utc(self.observed_at)
        received = _iso8601_utc(self.received_at)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "received_at", received)

        perms = tuple(sorted(set(self.permissions)))
        if not perms or any(p not in ALLOWED_PERMISSION_CLASSES for p in perms):
            raise EntryAdmissionError("permissions contain an unsupported class")
        object.__setattr__(self, "permissions", perms)

        caps = tuple(sorted({_require_token("capability_scope item", c) for c in self.capability_scope}))
        object.__setattr__(self, "capability_scope", caps)

        if self.parent_or_stream_id is not None:
            object.__setattr__(
                self,
                "parent_or_stream_id",
                _require_token("parent_or_stream_id", self.parent_or_stream_id),
            )

        digest = self.payload_sha256.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise EntryAdmissionError("payload_sha256 must be lowercase 64-hex sha256")
        object.__setattr__(self, "payload_sha256", digest)

    def immutable_event_identity(self) -> dict[str, Any]:
        """Fields that must survive replay as one causal event identity.

        received_at is deliberately excluded: transport replay may be received later, while
        the same observed event must retain the same causal event digest.
        """
        return {
            "schema_id": self.schema_id,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "source": self.source,
            "provenance": self.provenance,
            "modality": self.modality,
            "observed_at": self.observed_at,
            "permissions": list(self.permissions),
            "capability_scope": list(self.capability_scope),
            "parent_or_stream_id": self.parent_or_stream_id,
            "resource_budget": self.resource_budget.as_dict(),
            "payload_ref": self.payload_ref,
            "payload_sha256": self.payload_sha256,
        }

    @property
    def event_sha256(self) -> str:
        return _sha256(self.immutable_event_identity())

    @property
    def ingress_id(self) -> str:
        return _sha256(
            {
                "event_sha256": self.event_sha256,
                "received_at": self.received_at,
            }
        )

    def assert_current_generation(self, current_generation: int) -> None:
        if self.generation != current_generation:
            raise EntryAdmissionError(
                f"stale generation: packet={self.generation} current={current_generation}"
            )


def admit_payload(
    *,
    payload: Any,
    causal_id: str,
    generation: int,
    source: str,
    provenance: Mapping[str, Any],
    modality: str,
    observed_at: str,
    received_at: str,
    permissions: Sequence[str],
    capability_scope: Sequence[str] = (),
    resource_budget: ResourceBudget | None = None,
    parent_or_stream_id: str | None = None,
    payload_ref: str | None = None,
) -> XenoIngressPacket:
    try:
        payload_bytes = _canonical_json(payload)
    except (TypeError, ValueError) as exc:
        raise EntryAdmissionError("payload must be canonical-json serializable") from exc
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    if payload_ref is None:
        payload_ref = f"sha256:{payload_sha256}"
    return XenoIngressPacket(
        causal_id=causal_id,
        generation=generation,
        source=source,
        provenance=provenance,
        modality=modality,
        observed_at=observed_at,
        received_at=received_at,
        permissions=permissions,
        capability_scope=capability_scope,
        resource_budget=resource_budget or ResourceBudget(),
        payload_ref=payload_ref,
        payload_sha256=payload_sha256,
        parent_or_stream_id=parent_or_stream_id,
    )
