#!/usr/bin/env python3
"""Canonical control-plane capability projection for EntityOS/HCU Typed Entry.

This module is an adapter, not a second permission authority. It derives one bounded
Typed-Entry capability view from canonical session/generation state while binding the
existing EffectGate capability surface as control-plane context. Effect capabilities are
never copied into Typed Entry: real-effect authority remains exclusively EffectGate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

SCHEMA = "ENTITYOS_HCU_CONTROL_PLANE_CAPABILITY_BINDING/v1"
POLICY_SCHEMA = "ENTITYOS_HCU_CONTROL_PLANE_CAPABILITY_POLICY/v1"
INTERNAL_POLICY_CAPABILITIES = ("hcu.route", "memory.read")
FORBIDDEN_EFFECT_CAPABILITIES = frozenset({"process.exec"})


class CapabilityBindingError(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityAuthorityView:
    schema: str
    canonicalization_schema: str
    policy_sha256: str
    user_id: str
    session_id: str
    entity_generation: int
    internal_capabilities: tuple[str, ...]
    effect_capabilities: tuple[str, ...]
    admitted_capabilities: tuple[str, ...]
    binding_sha256: str


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CapabilityBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 512:
        raise CapabilityBindingError(f"{field}:TOO_LONG")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CapabilityBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise CapabilityBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _capabilities(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise CapabilityBindingError(f"{field}:SEQUENCE_REQUIRED")
    normalized = tuple(sorted(_text(item, field) for item in value))
    if len(normalized) != len(set(normalized)):
        raise CapabilityBindingError(f"{field}:DUPLICATE_FORBIDDEN")
    return normalized


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise CapabilityBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _session_row(canonical_db: Any, user_id: str, session_id: str) -> tuple[str, int]:
    sql = getattr(canonical_db, "db", None)
    if sql is None or not hasattr(sql, "execute"):
        raise CapabilityBindingError("CANONICAL_DB_SQL_INTERFACE_REQUIRED")
    row = sql.execute(
        "SELECT user_id,generation FROM sessions WHERE session_id=?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise CapabilityBindingError("CANONICAL_SESSION_NOT_FOUND")
    try:
        row_user_id = row["user_id"]
        row_generation = row["generation"]
    except (TypeError, KeyError, IndexError):
        row_user_id, row_generation = row[0], row[1]
    row_user_id = _text(row_user_id, "CANONICAL_SESSION_USER_ID")
    generation = _generation(row_generation, "CANONICAL_SESSION_GENERATION")
    if row_user_id != user_id:
        raise CapabilityBindingError("CANONICAL_SESSION_OWNER_MISMATCH")
    assert_live_generation = getattr(canonical_db, "assert_live_generation", None)
    if not callable(assert_live_generation):
        raise CapabilityBindingError("CANONICAL_GENERATION_AUTHORITY_REQUIRED")
    assert_live_generation(session_id, generation)
    return row_user_id, generation


def snapshot_capability_authority(
    canonical_db: Any,
    effect_gate: Any,
    *,
    user_id: str,
    session_id: str,
) -> CapabilityAuthorityView:
    """Project canonical control-plane state without creating new permission authority."""
    user_id = _text(user_id, "user_id")
    session_id = _text(session_id, "session_id")
    if getattr(effect_gate, "db", None) is not canonical_db:
        raise CapabilityBindingError("EFFECT_GATE_CANONICAL_DB_MISMATCH")
    _, generation = _session_row(canonical_db, user_id, session_id)

    available_capabilities = getattr(effect_gate, "available_capabilities", None)
    if not callable(available_capabilities):
        raise CapabilityBindingError("EFFECT_GATE_CAPABILITY_SURFACE_REQUIRED")
    effect_capabilities = _capabilities(
        tuple(available_capabilities()),
        "EFFECT_GATE_CAPABILITIES",
    )
    forbidden = sorted(set(effect_capabilities) & FORBIDDEN_EFFECT_CAPABILITIES)
    if forbidden:
        raise CapabilityBindingError(
            "FORBIDDEN_EFFECT_CAPABILITY_EXPOSED:" + ",".join(forbidden)
        )

    internal_capabilities = _capabilities(
        INTERNAL_POLICY_CAPABILITIES,
        "INTERNAL_POLICY_CAPABILITIES",
    )
    admitted_capabilities = internal_capabilities
    policy_material = {
        "schema": POLICY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "typed_entry_capabilities": list(internal_capabilities),
        "effect_capability_source": "EffectGate.available_capabilities",
        "effect_capabilities_are_entry_authority": False,
        "forbidden_effect_capabilities": sorted(FORBIDDEN_EFFECT_CAPABILITIES),
    }
    policy_sha256 = _canonical_sha256(policy_material, "CAPABILITY_POLICY")
    binding_material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "policy_sha256": policy_sha256,
        "user_id": user_id,
        "session_id": session_id,
        "entity_generation": generation,
        "internal_capabilities": list(internal_capabilities),
        "effect_capabilities_observed": list(effect_capabilities),
        "admitted_capabilities": list(admitted_capabilities),
    }
    binding_sha256 = _canonical_sha256(binding_material, "CAPABILITY_BINDING")
    return CapabilityAuthorityView(
        schema=SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        policy_sha256=policy_sha256,
        user_id=user_id,
        session_id=session_id,
        entity_generation=generation,
        internal_capabilities=internal_capabilities,
        effect_capabilities=effect_capabilities,
        admitted_capabilities=admitted_capabilities,
        binding_sha256=binding_sha256,
    )


def admit_entry_with_control_plane(
    entry: Mapping[str, Any],
    *,
    canonical_db: Any,
    effect_gate: Any,
    user_id: str,
    session_id: str,
    admitted_budget: Mapping[str, Any],
) -> Any:
    """Admit one Entry against a freshly derived canonical capability snapshot."""
    try:
        from .xeno_entry_fabric_v1 import admit_entry
    except ImportError:
        from xeno_entry_fabric_v1 import admit_entry

    view = snapshot_capability_authority(
        canonical_db,
        effect_gate,
        user_id=user_id,
        session_id=session_id,
    )
    return admit_entry(
        entry,
        current_generation=view.entity_generation,
        expected_capability_binding_sha256=view.binding_sha256,
        admitted_capabilities=view.admitted_capabilities,
        admitted_budget=admitted_budget,
    )
