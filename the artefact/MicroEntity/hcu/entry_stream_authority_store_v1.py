#!/usr/bin/env python3
"""Independent stream-authority admission for Typed Entry / executor sequencing.

Typed Entry hashes ``stream_id`` into replay-stable event identity, but integrity alone does
not prove that the original stream label was assigned by an independent transport/control
plane.  This module closes that trust split without creating a second state authority:

* an external deterministic control-plane registry must already admit the exact authority
  decision bytes;
* the decision is then persisted in the caller-supplied canonical MiniUnifiedDB under the
  current entity generation using one ``BEGIN IMMEDIATE`` transaction;
* downstream sequence-lane derivation can read the admission back from that same canonical
  database instead of trusting ``EntryPacket.stream_id`` by itself.

Building a ``StreamAuthorityDecision`` here grants ZERO authority.  The decision receives
positive source-level authority only when the exact decision digest and canonical record are
present in the separately supplied admitted-decision registry and the canonical DB write
succeeds.  Runtime/model/J-Space/training/effect credit remains zero.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

DECISION_SCHEMA = "HCU_ENTRY_STREAM_AUTHORITY_DECISION/v1"
ADMISSION_SCHEMA = "HCU_ENTRY_STREAM_AUTHORITY_ADMISSION/v1"
STORE_SCHEMA = "HCU_ENTRY_STREAM_AUTHORITY_STORE/v1"
ADMITTED_STATUS = "ADMITTED"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class EntryStreamAuthorityError(ValueError):
    pass


@dataclass(frozen=True)
class StreamAuthorityDecision:
    schema: str
    canonicalization_schema: str
    generation: int
    authority_namespace: str
    authority_decision_id: str
    source_kind: str
    source_id: str
    stream_id: str
    status: str
    decision_sha256: str


@dataclass(frozen=True)
class EntryStreamAuthorityAdmission:
    schema: str
    canonicalization_schema: str
    decision_schema: str
    decision_sha256: str
    generation: int
    authority_namespace: str
    authority_decision_id: str
    source_kind: str
    source_id: str
    stream_id: str
    status: str
    admission_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise EntryStreamAuthorityError(message)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str), f"{field}:STRING_REQUIRED")
    normalized = value.strip()
    _need(bool(normalized), f"{field}:NONEMPTY_STRING_REQUIRED")
    _need(normalized == value, f"{field}:NONCANONICAL_TEXT")
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
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise EntryStreamAuthorityError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _decision_material(decision: StreamAuthorityDecision) -> dict[str, Any]:
    data = asdict(decision)
    data.pop("decision_sha256", None)
    return data


def _admission_material(admission: EntryStreamAuthorityAdmission) -> dict[str, Any]:
    data = asdict(admission)
    data.pop("admission_sha256", None)
    return data


def decision_record(decision: StreamAuthorityDecision) -> dict[str, Any]:
    validate_stream_authority_decision(decision)
    data = _decision_material(decision)
    data["decision_sha256"] = decision.decision_sha256
    return data


def build_stream_authority_decision(
    *,
    generation: int,
    authority_namespace: str,
    authority_decision_id: str,
    source_kind: str,
    source_id: str,
    stream_id: str,
) -> StreamAuthorityDecision:
    """Build canonical decision bytes only; this function does NOT grant authority."""
    material = {
        "schema": DECISION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(generation),
        "authority_namespace": _text(authority_namespace, "authority_namespace", 256),
        "authority_decision_id": _text(authority_decision_id, "authority_decision_id", 512),
        "source_kind": _text(source_kind, "source_kind", 128),
        "source_id": _text(source_id, "source_id", 512),
        "stream_id": _text(stream_id, "stream_id", 512),
        "status": ADMITTED_STATUS,
    }
    return StreamAuthorityDecision(
        **material,
        decision_sha256=_canonical_sha256(material, "ENTRY_STREAM_AUTHORITY_DECISION"),
    )


def validate_stream_authority_decision(decision: StreamAuthorityDecision) -> None:
    if not isinstance(decision, StreamAuthorityDecision):
        raise EntryStreamAuthorityError("STREAM_AUTHORITY_DECISION_REQUIRED")
    _need(decision.schema == DECISION_SCHEMA, "STREAM_AUTHORITY_DECISION_SCHEMA_UNSUPPORTED")
    _need(
        decision.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "STREAM_AUTHORITY_DECISION_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _generation(decision.generation)
    for field, max_len in (
        ("authority_namespace", 256),
        ("authority_decision_id", 512),
        ("source_kind", 128),
        ("source_id", 512),
        ("stream_id", 512),
    ):
        _text(getattr(decision, field), field, max_len)
    _need(decision.status == ADMITTED_STATUS, "STREAM_AUTHORITY_DECISION_NOT_ADMITTED_STATUS")
    observed = _sha256(decision.decision_sha256, "decision_sha256")
    expected = _canonical_sha256(_decision_material(decision), "ENTRY_STREAM_AUTHORITY_DECISION")
    _need(observed == expected, "STREAM_AUTHORITY_DECISION_DIGEST_MISMATCH")


def validate_entry_stream_authority_admission(admission: EntryStreamAuthorityAdmission) -> None:
    if not isinstance(admission, EntryStreamAuthorityAdmission):
        raise EntryStreamAuthorityError("ENTRY_STREAM_AUTHORITY_ADMISSION_REQUIRED")
    _need(admission.schema == ADMISSION_SCHEMA, "ENTRY_STREAM_AUTHORITY_ADMISSION_SCHEMA_UNSUPPORTED")
    _need(
        admission.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "ENTRY_STREAM_AUTHORITY_ADMISSION_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _need(admission.decision_schema == DECISION_SCHEMA, "ENTRY_STREAM_AUTHORITY_DECISION_SCHEMA_MISMATCH")
    _generation(admission.generation)
    for field, max_len in (
        ("authority_namespace", 256),
        ("authority_decision_id", 512),
        ("source_kind", 128),
        ("source_id", 512),
        ("stream_id", 512),
    ):
        _text(getattr(admission, field), field, max_len)
    _need(admission.status == ADMITTED_STATUS, "ENTRY_STREAM_AUTHORITY_ADMISSION_STATUS_INVALID")
    _sha256(admission.decision_sha256, "decision_sha256")
    observed = _sha256(admission.admission_sha256, "admission_sha256")
    expected = _canonical_sha256(_admission_material(admission), "ENTRY_STREAM_AUTHORITY_ADMISSION")
    _need(observed == expected, "ENTRY_STREAM_AUTHORITY_ADMISSION_DIGEST_MISMATCH")


def _foreign_keys_enabled(db: sqlite3.Connection) -> None:
    row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(row is not None and int(row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise EntryStreamAuthorityError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _generation(row[0], "entity_state.generation")


def _scope_key(*, generation: int, source_kind: str, source_id: str, stream_id: str) -> str:
    return _canonical_sha256(
        {
            "schema": "HCU_ENTRY_STREAM_AUTHORITY_SCOPE/v1",
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "generation": _generation(generation),
            "source_kind": _text(source_kind, "source_kind", 128),
            "source_id": _text(source_id, "source_id", 512),
            "stream_id": _text(stream_id, "stream_id", 512),
        },
        "ENTRY_STREAM_AUTHORITY_SCOPE",
    )


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    _foreign_keys_enabled(db)
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_entry_stream_authority_admissions(
          stream_scope_sha256 TEXT PRIMARY KEY,
          admission_sha256 TEXT NOT NULL UNIQUE,
          admission_jcs BLOB NOT NULL,
          decision_sha256 TEXT NOT NULL UNIQUE,
          decision_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          authority_namespace TEXT NOT NULL,
          authority_decision_id TEXT NOT NULL,
          source_kind TEXT NOT NULL,
          source_id TEXT NOT NULL,
          stream_id TEXT NOT NULL,
          status TEXT NOT NULL,
          UNIQUE(entity_generation, source_kind, source_id, stream_id)
        )"""
    )


def _externally_admitted_decision(
    decision: StreamAuthorityDecision,
    admitted_stream_authority_decisions: Mapping[str, Any],
) -> None:
    """Require exact canonical decision bytes from authority external to the Entry packet."""
    _need(
        isinstance(admitted_stream_authority_decisions, Mapping),
        "ADMITTED_STREAM_AUTHORITY_DECISION_REGISTRY_REQUIRED",
    )
    expected_record = decision_record(decision)
    external = admitted_stream_authority_decisions.get(decision.decision_sha256)
    _need(isinstance(external, Mapping), "STREAM_AUTHORITY_DECISION_NOT_EXTERNALLY_ADMITTED")
    _need(dict(external) == expected_record, "STREAM_AUTHORITY_EXTERNAL_REGISTRY_MISMATCH")


def admit_entry_stream_authority(
    db: sqlite3.Connection,
    decision: StreamAuthorityDecision,
    *,
    admitted_stream_authority_decisions: Mapping[str, Any],
    current_generation: int,
) -> EntryStreamAuthorityAdmission:
    """Persist one externally admitted stream decision into the canonical MiniUnifiedDB."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _foreign_keys_enabled(db)
    current_generation = _generation(current_generation, "current_generation")
    validate_stream_authority_decision(decision)
    _need(decision.generation == current_generation, "STREAM_AUTHORITY_DECISION_GENERATION_MISMATCH")

    # External authority must resolve BEFORE any DB/table write.  A caller cannot make an
    # attacker-chosen Entry stream authoritative merely by asking this store to persist it.
    _externally_admitted_decision(decision, admitted_stream_authority_decisions)

    material = {
        "schema": ADMISSION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "decision_schema": DECISION_SCHEMA,
        "decision_sha256": decision.decision_sha256,
        "generation": decision.generation,
        "authority_namespace": decision.authority_namespace,
        "authority_decision_id": decision.authority_decision_id,
        "source_kind": decision.source_kind,
        "source_id": decision.source_id,
        "stream_id": decision.stream_id,
        "status": ADMITTED_STATUS,
    }
    admission = EntryStreamAuthorityAdmission(
        **material,
        admission_sha256=_canonical_sha256(material, "ENTRY_STREAM_AUTHORITY_ADMISSION"),
    )
    validate_entry_stream_authority_admission(admission)
    decision_jcs = canonicalize(decision_record(decision))
    admission_record = _admission_material(admission)
    admission_record["admission_sha256"] = admission.admission_sha256
    admission_jcs = canonicalize(admission_record)
    scope_key = _scope_key(
        generation=decision.generation,
        source_kind=decision.source_kind,
        source_id=decision.source_id,
        stream_id=decision.stream_id,
    )

    try:
        db.execute("BEGIN IMMEDIATE")
        _need(_current_generation(db) == current_generation, "STALE_STREAM_AUTHORITY_ADMISSION_GENERATION")
        _install_schema(db)
        row = db.execute(
            "SELECT admission_sha256,admission_jcs,decision_sha256,decision_jcs,entity_generation,"
            "authority_namespace,authority_decision_id,source_kind,source_id,stream_id,status "
            "FROM hcu_entry_stream_authority_admissions WHERE stream_scope_sha256=?",
            (scope_key,),
        ).fetchone()
        expected = (
            admission.admission_sha256,
            admission_jcs,
            decision.decision_sha256,
            decision_jcs,
            decision.generation,
            decision.authority_namespace,
            decision.authority_decision_id,
            decision.source_kind,
            decision.source_id,
            decision.stream_id,
            ADMITTED_STATUS,
        )
        if row is None:
            db.execute(
                "INSERT INTO hcu_entry_stream_authority_admissions "
                "(stream_scope_sha256,admission_sha256,admission_jcs,decision_sha256,decision_jcs,"
                "entity_generation,authority_namespace,authority_decision_id,source_kind,source_id,stream_id,status) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (scope_key, *expected),
            )
        else:
            stored = (str(row[0]), bytes(row[1]), str(row[2]), bytes(row[3]), *row[4:])
            _need(stored == expected, "STREAM_AUTHORITY_ADMISSION_REPLAY_DIVERGENCE")
        db.commit()
        return admission
    except (EntryStreamAuthorityError, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise


def read_entry_stream_authority_admission(
    db: sqlite3.Connection,
    *,
    current_generation: int,
    source_kind: str,
    source_id: str,
    stream_id: str,
) -> EntryStreamAuthorityAdmission:
    """Read/revalidate independent stream authority from the canonical DB.

    The Entry packet itself is intentionally not accepted by this function.  The lookup key
    is derived from the expected stream scope and must resolve to already persisted canonical
    authority bytes.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    source_kind = _text(source_kind, "source_kind", 128)
    source_id = _text(source_id, "source_id", 512)
    stream_id = _text(stream_id, "stream_id", 512)
    _need(_current_generation(db) == current_generation, "STALE_STREAM_AUTHORITY_READ_GENERATION")
    scope_key = _scope_key(
        generation=current_generation,
        source_kind=source_kind,
        source_id=source_id,
        stream_id=stream_id,
    )
    try:
        row = db.execute(
            "SELECT admission_jcs,decision_jcs FROM hcu_entry_stream_authority_admissions "
            "WHERE stream_scope_sha256=?",
            (scope_key,),
        ).fetchone()
    except sqlite3.Error as exc:
        raise EntryStreamAuthorityError("STREAM_AUTHORITY_ADMISSION_STORE_REQUIRED") from exc
    _need(row is not None, "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE")

    try:
        admission_raw = bytes(row[0])
        decision_raw = bytes(row[1])
        admission_data = json.loads(admission_raw.decode("utf-8"))
        decision_data = json.loads(decision_raw.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EntryStreamAuthorityError("STREAM_AUTHORITY_STORED_BYTES_INVALID") from exc
    _need(isinstance(admission_data, dict), "STREAM_AUTHORITY_STORED_ADMISSION_OBJECT_REQUIRED")
    _need(isinstance(decision_data, dict), "STREAM_AUTHORITY_STORED_DECISION_OBJECT_REQUIRED")
    _need(canonicalize(admission_data) == admission_raw, "STREAM_AUTHORITY_STORED_ADMISSION_JCS_MISMATCH")
    _need(canonicalize(decision_data) == decision_raw, "STREAM_AUTHORITY_STORED_DECISION_JCS_MISMATCH")

    try:
        admission = EntryStreamAuthorityAdmission(**admission_data)
        decision = StreamAuthorityDecision(**decision_data)
    except TypeError as exc:
        raise EntryStreamAuthorityError("STREAM_AUTHORITY_STORED_SCHEMA_INVALID") from exc
    validate_entry_stream_authority_admission(admission)
    validate_stream_authority_decision(decision)
    _need(admission.decision_sha256 == decision.decision_sha256, "STREAM_AUTHORITY_DECISION_ADMISSION_MISMATCH")
    for field in (
        "generation",
        "authority_namespace",
        "authority_decision_id",
        "source_kind",
        "source_id",
        "stream_id",
        "status",
    ):
        _need(getattr(admission, field) == getattr(decision, field), f"STREAM_AUTHORITY_STORED_CROSS_BIND_MISMATCH:{field}")
    _need(admission.generation == current_generation, "STREAM_AUTHORITY_ADMISSION_GENERATION_MISMATCH")
    _need(admission.source_kind == source_kind, "STREAM_AUTHORITY_SOURCE_KIND_MISMATCH")
    _need(admission.source_id == source_id, "STREAM_AUTHORITY_SOURCE_ID_MISMATCH")
    _need(admission.stream_id == stream_id, "STREAM_AUTHORITY_STREAM_ID_MISMATCH")
    return admission


__all__ = [
    "DECISION_SCHEMA",
    "ADMISSION_SCHEMA",
    "STORE_SCHEMA",
    "ADMITTED_STATUS",
    "EntryStreamAuthorityError",
    "StreamAuthorityDecision",
    "EntryStreamAuthorityAdmission",
    "build_stream_authority_decision",
    "decision_record",
    "validate_stream_authority_decision",
    "validate_entry_stream_authority_admission",
    "admit_entry_stream_authority",
    "read_entry_stream_authority_admission",
]
