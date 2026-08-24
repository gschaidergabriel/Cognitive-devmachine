#!/usr/bin/env python3
"""Canonical stream-authority projection for EntityOS/HCU Typed Entry.

This is an adapter over the existing canonical session/generation state, not a second truth
or stream database.  Its first deliberately narrow authority class is HUMAN_PROMPT: the
cross-event stream identity is the canonical session_id itself.  A caller-provided Entry
``stream_id`` is never promoted merely because it is hash-bound.

Other source kinds remain unsupported until they have an independent deterministic transport
or control-plane stream authority.  This module assigns no sequence position, no adjacency,
no model/J-Space causality and no runtime/training credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from xeno_entry_fabric_v1 import EntryPacket


SCHEMA = "ENTITYOS_HCU_CONTROL_PLANE_STREAM_AUTHORITY/v1"
POLICY_SCHEMA = "ENTITYOS_HCU_CONTROL_PLANE_STREAM_POLICY/v1"
HUMAN_PROMPT_SESSION_STREAM = "HUMAN_PROMPT_SESSION_STREAM"


class StreamAuthorityError(ValueError):
    pass


@dataclass(frozen=True)
class StreamAuthorityView:
    schema: str
    canonicalization_schema: str
    policy_sha256: str
    authority_class: str
    user_id: str
    session_id: str
    entity_generation: int
    source_kind: str
    source_id: str
    stream_id: str
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StreamAuthorityError(f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    if value != normalized:
        raise StreamAuthorityError(f"{field}:NONCANONICAL_TEXT")
    if len(normalized) > max_len:
        raise StreamAuthorityError(f"{field}:TOO_LONG")
    return normalized


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StreamAuthorityError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise StreamAuthorityError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise StreamAuthorityError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _session_row(canonical_db: Any, user_id: str, session_id: str) -> int:
    sql = getattr(canonical_db, "db", None)
    if sql is None or not hasattr(sql, "execute"):
        raise StreamAuthorityError("CANONICAL_DB_SQL_INTERFACE_REQUIRED")
    row = sql.execute(
        "SELECT user_id,generation FROM sessions WHERE session_id=?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise StreamAuthorityError("CANONICAL_SESSION_NOT_FOUND")
    try:
        row_user_id = row["user_id"]
        row_generation = row["generation"]
    except (TypeError, KeyError, IndexError):
        row_user_id, row_generation = row[0], row[1]
    if _text(row_user_id, "CANONICAL_SESSION_USER_ID") != user_id:
        raise StreamAuthorityError("CANONICAL_SESSION_OWNER_MISMATCH")
    generation = _generation(row_generation, "CANONICAL_SESSION_GENERATION")
    assert_live_generation = getattr(canonical_db, "assert_live_generation", None)
    if not callable(assert_live_generation):
        raise StreamAuthorityError("CANONICAL_GENERATION_AUTHORITY_REQUIRED")
    try:
        assert_live_generation(session_id, generation)
    except Exception as exc:
        raise StreamAuthorityError("CANONICAL_SESSION_GENERATION_NOT_LIVE") from exc
    return generation


def snapshot_human_prompt_stream_authority(
    canonical_db: Any,
    *,
    user_id: str,
    session_id: str,
    trusted_source_id: str,
) -> StreamAuthorityView:
    """Derive one cross-event HUMAN_PROMPT stream from canonical session identity.

    ``trusted_source_id`` is ingress context and cannot choose ``stream_id``.  The stream is
    always exactly the canonical ``session_id`` read back from the canonical session substrate.
    """
    user_id = _text(user_id, "user_id")
    session_id = _text(session_id, "session_id")
    trusted_source_id = _text(trusted_source_id, "trusted_source_id")
    generation = _session_row(canonical_db, user_id, session_id)

    policy_material = {
        "schema": POLICY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "authority_class": HUMAN_PROMPT_SESSION_STREAM,
        "source_kind": "HUMAN_PROMPT",
        "stream_rule": "STREAM_ID_EQUALS_CANONICAL_SESSION_ID",
        "caller_stream_labels_are_authority": False,
        "unsupported_source_kinds_fail_closed": True,
    }
    policy_sha256 = _canonical_sha256(policy_material, "STREAM_AUTHORITY_POLICY")
    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "policy_sha256": policy_sha256,
        "authority_class": HUMAN_PROMPT_SESSION_STREAM,
        "user_id": user_id,
        "session_id": session_id,
        "entity_generation": generation,
        "source_kind": "HUMAN_PROMPT",
        "source_id": trusted_source_id,
        "stream_id": session_id,
    }
    return StreamAuthorityView(
        **material,
        binding_sha256=_canonical_sha256(material, "STREAM_AUTHORITY_BINDING"),
    )


def validate_entry_stream_authority(packet: EntryPacket, view: StreamAuthorityView) -> str:
    """Require an admitted Entry to match an independently derived canonical stream view."""
    if not isinstance(packet, EntryPacket):
        raise StreamAuthorityError("ENTRY_PACKET_REQUIRED")
    if not isinstance(view, StreamAuthorityView):
        raise StreamAuthorityError("STREAM_AUTHORITY_VIEW_REQUIRED")
    if view.schema != SCHEMA or view.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise StreamAuthorityError("STREAM_AUTHORITY_VIEW_SCHEMA_UNSUPPORTED")
    if view.authority_class != HUMAN_PROMPT_SESSION_STREAM:
        raise StreamAuthorityError("STREAM_AUTHORITY_CLASS_UNSUPPORTED")

    expected = {
        "schema": view.schema,
        "canonicalization_schema": view.canonicalization_schema,
        "policy_sha256": view.policy_sha256,
        "authority_class": view.authority_class,
        "user_id": view.user_id,
        "session_id": view.session_id,
        "entity_generation": view.entity_generation,
        "source_kind": view.source_kind,
        "source_id": view.source_id,
        "stream_id": view.stream_id,
    }
    if _canonical_sha256(expected, "STREAM_AUTHORITY_BINDING") != view.binding_sha256:
        raise StreamAuthorityError("STREAM_AUTHORITY_BINDING_DIGEST_MISMATCH")
    if packet.source_kind != "HUMAN_PROMPT" or packet.source_kind != view.source_kind:
        raise StreamAuthorityError("EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH")
    if packet.source_id != view.source_id:
        raise StreamAuthorityError("EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_ID_MISMATCH")
    if packet.entity_generation != view.entity_generation:
        raise StreamAuthorityError("EXECUTOR_SEQUENCE_STREAM_AUTHORITY_GENERATION_MISMATCH")
    if packet.stream_id != view.stream_id:
        raise StreamAuthorityError("EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE")
    if packet.stream_id != view.session_id:
        raise StreamAuthorityError("EXECUTOR_SEQUENCE_STREAM_SESSION_ID_MISMATCH")
    return view.binding_sha256
