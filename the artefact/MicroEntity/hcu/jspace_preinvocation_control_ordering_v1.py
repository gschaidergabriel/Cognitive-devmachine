#!/usr/bin/env python3
"""Canonical pre-invocation ordering evidence for EntityOS/HCU J-Space control.

This module closes one narrow temporal-evidence gap without creating a second state,
truth, effect, model, executor, or dataset authority.

It records, inside the caller-supplied canonical MiniUnifiedDB, that:

1. one predecessor model invocation was already admitted;
2. one distinct controlled model invocation was not yet admitted;
3. a predecessor TrainingTrace / Vector-Control packet identity and the exact prepared
   input digest/size were fixed while that ordering held.

The transaction uses ``BEGIN IMMEDIATE`` so model-execution admission and this ordering
claim serialize through the same SQLite writer lock. If the controlled invocation already
exists, the claim fails closed. Replaying this write after the controlled invocation is
also forbidden; later readers must use ``read_preinvocation_control_ordering``.

This primitive proves admitted ordering only. It does not prove that the packet bytes are
actually present in the executor input, that the predecessor TrainingTrace semantically
matches the packet, that the model used the control internally, or that training/effects
are valid. Those remain separate existing HCU/J-Space validation gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize

SCHEMA = "HCU_JSPACE_PREINVOCATION_CONTROL_ORDERING/v1"
MAX_INPUT_BYTES = 64 * 1024 * 1024


class JSpacePreInvocationControlOrderingError(ValueError):
    pass


@dataclass(frozen=True)
class PreInvocationControlOrdering:
    schema: str
    canonicalization_schema: str
    generation: int
    predecessor_model_execution_observation_sha256: str
    predecessor_executor_id: str
    predecessor_invocation_id: str
    predecessor_training_trace_sha256: str
    vector_control_packet_sha256: str
    controlled_executor_id: str
    controlled_invocation_id: str
    prepared_input_sha256: str
    prepared_input_size: int
    ordering_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise JSpacePreInvocationControlOrderingError(message)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
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
        type(value) is int and 0 <= value <= 9_007_199_254_740_991,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _input_size(value: Any) -> int:
    _need(
        type(value) is int and 1 <= value <= MAX_INPUT_BYTES,
        "prepared_input_size:SIZE_OUT_OF_RANGE",
    )
    return value


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise JSpacePreInvocationControlOrderingError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _generation(row[0], "entity_state.generation")


def _foreign_keys_enabled(db: sqlite3.Connection) -> None:
    row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(
        row is not None and int(row[0]) == 1,
        "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION",
    )


def _execution_tables_present(db: sqlite3.Connection) -> bool:
    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name IN ('hcu_model_execution_observations','hcu_model_execution_invocations')"
    ).fetchall()
    return {str(row[0]) for row in rows} == {
        "hcu_model_execution_observations",
        "hcu_model_execution_invocations",
    }


def _read_execution(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> tuple[int, str] | None:
    if not _execution_tables_present(db):
        return None
    rows = db.execute(
        "SELECT entity_generation,observation_sha256 "
        "FROM hcu_model_execution_invocations "
        "WHERE executor_id=? AND invocation_id=?",
        (executor_id, invocation_id),
    ).fetchall()
    _need(len(rows) <= 1, "MODEL_EXECUTION_INVOCATION_AMBIGUOUS")
    if not rows:
        return None
    generation, observation_sha256 = rows[0]
    return (
        _generation(generation, "model_execution.entity_generation"),
        _sha256(str(observation_sha256), "model_execution.observation_sha256"),
    )


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    _foreign_keys_enabled(db)
    _need(_execution_tables_present(db), "MODEL_EXECUTION_ADMISSION_STORE_REQUIRED")
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_jspace_preinvocation_control_orderings(
          ordering_sha256 TEXT PRIMARY KEY,
          ordering_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          predecessor_model_execution_observation_sha256 TEXT NOT NULL,
          predecessor_executor_id TEXT NOT NULL,
          predecessor_invocation_id TEXT NOT NULL,
          predecessor_training_trace_sha256 TEXT NOT NULL,
          vector_control_packet_sha256 TEXT NOT NULL,
          controlled_executor_id TEXT NOT NULL,
          controlled_invocation_id TEXT NOT NULL,
          prepared_input_sha256 TEXT NOT NULL,
          prepared_input_size INTEGER NOT NULL,
          UNIQUE(controlled_executor_id, controlled_invocation_id),
          FOREIGN KEY(predecessor_model_execution_observation_sha256)
            REFERENCES hcu_model_execution_observations(observation_sha256)
        )"""
    )


def _material(ordering: PreInvocationControlOrdering) -> dict[str, Any]:
    data = asdict(ordering)
    data.pop("ordering_sha256", None)
    return data


def _build_ordering(
    *,
    generation: int,
    predecessor_observation_sha256: str,
    predecessor_executor_id: str,
    predecessor_invocation_id: str,
    predecessor_training_trace_sha256: str,
    vector_control_packet_sha256: str,
    controlled_executor_id: str,
    controlled_invocation_id: str,
    prepared_input_sha256: str,
    prepared_input_size: int,
) -> PreInvocationControlOrdering:
    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(generation),
        "predecessor_model_execution_observation_sha256": _sha256(
            predecessor_observation_sha256,
            "predecessor_model_execution_observation_sha256",
        ),
        "predecessor_executor_id": _text(
            predecessor_executor_id,
            "predecessor_executor_id",
            256,
        ),
        "predecessor_invocation_id": _text(
            predecessor_invocation_id,
            "predecessor_invocation_id",
            256,
        ),
        "predecessor_training_trace_sha256": _sha256(
            predecessor_training_trace_sha256,
            "predecessor_training_trace_sha256",
        ),
        "vector_control_packet_sha256": _sha256(
            vector_control_packet_sha256,
            "vector_control_packet_sha256",
        ),
        "controlled_executor_id": _text(
            controlled_executor_id,
            "controlled_executor_id",
            256,
        ),
        "controlled_invocation_id": _text(
            controlled_invocation_id,
            "controlled_invocation_id",
            256,
        ),
        "prepared_input_sha256": _sha256(
            prepared_input_sha256,
            "prepared_input_sha256",
        ),
        "prepared_input_size": _input_size(prepared_input_size),
    }
    ordering_sha256 = hashlib.sha256(canonicalize(material)).hexdigest()
    return PreInvocationControlOrdering(**material, ordering_sha256=ordering_sha256)


def validate_preinvocation_control_ordering(
    ordering: PreInvocationControlOrdering,
) -> None:
    if not isinstance(ordering, PreInvocationControlOrdering):
        raise JSpacePreInvocationControlOrderingError(
            "PREINVOCATION_CONTROL_ORDERING_REQUIRED"
        )
    _need(
        ordering.schema == SCHEMA,
        "PREINVOCATION_CONTROL_ORDERING_SCHEMA_UNSUPPORTED",
    )
    _need(
        ordering.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "PREINVOCATION_CONTROL_ORDERING_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _generation(ordering.generation)
    for field in (
        "predecessor_model_execution_observation_sha256",
        "predecessor_training_trace_sha256",
        "vector_control_packet_sha256",
        "prepared_input_sha256",
    ):
        _sha256(getattr(ordering, field), field)
    for field in (
        "predecessor_executor_id",
        "predecessor_invocation_id",
        "controlled_executor_id",
        "controlled_invocation_id",
    ):
        _text(getattr(ordering, field), field, 256)
    _input_size(ordering.prepared_input_size)
    _need(
        (ordering.predecessor_executor_id, ordering.predecessor_invocation_id)
        != (ordering.controlled_executor_id, ordering.controlled_invocation_id),
        "PREDECESSOR_AND_CONTROLLED_INVOCATION_MUST_BE_DISTINCT",
    )
    observed = _sha256(ordering.ordering_sha256, "ordering_sha256")
    expected = hashlib.sha256(canonicalize(_material(ordering))).hexdigest()
    _need(
        observed == expected,
        "PREINVOCATION_CONTROL_ORDERING_DIGEST_MISMATCH",
    )


def admit_preinvocation_control_ordering(
    db: sqlite3.Connection,
    *,
    current_generation: int,
    predecessor_executor_id: str,
    predecessor_invocation_id: str,
    predecessor_training_trace_sha256: str,
    vector_control_packet_sha256: str,
    controlled_executor_id: str,
    controlled_invocation_id: str,
    prepared_input_sha256: str,
    prepared_input_size: int,
) -> PreInvocationControlOrdering:
    """Atomically prove predecessor-admitted / controlled-not-yet-admitted ordering.

    The predecessor model execution identity is read from the canonical execution-admission
    tables rather than supplied as a caller digest. The controlled invocation must be absent
    while the same MiniUnifiedDB writer lock is held. This is an admission-order fact, not a
    wall-clock or caller step-number claim.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    current_generation = _generation(current_generation, "current_generation")
    predecessor_executor_id = _text(
        predecessor_executor_id,
        "predecessor_executor_id",
        256,
    )
    predecessor_invocation_id = _text(
        predecessor_invocation_id,
        "predecessor_invocation_id",
        256,
    )
    controlled_executor_id = _text(
        controlled_executor_id,
        "controlled_executor_id",
        256,
    )
    controlled_invocation_id = _text(
        controlled_invocation_id,
        "controlled_invocation_id",
        256,
    )
    _need(
        (predecessor_executor_id, predecessor_invocation_id)
        != (controlled_executor_id, controlled_invocation_id),
        "PREDECESSOR_AND_CONTROLLED_INVOCATION_MUST_BE_DISTINCT",
    )

    try:
        _foreign_keys_enabled(db)
        db.execute("BEGIN IMMEDIATE")
        live_generation = _current_generation(db)
        _need(
            live_generation == current_generation,
            "STALE_PREINVOCATION_CONTROL_ORDERING_GENERATION",
        )

        predecessor = _read_execution(
            db,
            executor_id=predecessor_executor_id,
            invocation_id=predecessor_invocation_id,
        )
        _need(
            predecessor is not None,
            "PREDECESSOR_MODEL_EXECUTION_NOT_ADMITTED",
        )
        predecessor_generation, predecessor_observation_sha256 = predecessor
        _need(
            predecessor_generation == current_generation,
            "PREDECESSOR_MODEL_EXECUTION_GENERATION_MISMATCH",
        )

        controlled = _read_execution(
            db,
            executor_id=controlled_executor_id,
            invocation_id=controlled_invocation_id,
        )
        _need(
            controlled is None,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_PREINVOCATION_REQUIRED",
        )

        ordering = _build_ordering(
            generation=current_generation,
            predecessor_observation_sha256=predecessor_observation_sha256,
            predecessor_executor_id=predecessor_executor_id,
            predecessor_invocation_id=predecessor_invocation_id,
            predecessor_training_trace_sha256=predecessor_training_trace_sha256,
            vector_control_packet_sha256=vector_control_packet_sha256,
            controlled_executor_id=controlled_executor_id,
            controlled_invocation_id=controlled_invocation_id,
            prepared_input_sha256=prepared_input_sha256,
            prepared_input_size=prepared_input_size,
        )
        validate_preinvocation_control_ordering(ordering)
        ordering_jcs = canonicalize(asdict(ordering))

        _install_schema(db)
        row = db.execute(
            "SELECT ordering_sha256,ordering_jcs FROM "
            "hcu_jspace_preinvocation_control_orderings "
            "WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            (controlled_executor_id, controlled_invocation_id),
        ).fetchone()
        if row is None:
            db.execute(
                "INSERT INTO hcu_jspace_preinvocation_control_orderings "
                "(ordering_sha256,ordering_jcs,entity_generation,"
                "predecessor_model_execution_observation_sha256,"
                "predecessor_executor_id,predecessor_invocation_id,"
                "predecessor_training_trace_sha256,vector_control_packet_sha256,"
                "controlled_executor_id,controlled_invocation_id,"
                "prepared_input_sha256,prepared_input_size) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    ordering.ordering_sha256,
                    ordering_jcs,
                    ordering.generation,
                    ordering.predecessor_model_execution_observation_sha256,
                    ordering.predecessor_executor_id,
                    ordering.predecessor_invocation_id,
                    ordering.predecessor_training_trace_sha256,
                    ordering.vector_control_packet_sha256,
                    ordering.controlled_executor_id,
                    ordering.controlled_invocation_id,
                    ordering.prepared_input_sha256,
                    ordering.prepared_input_size,
                ),
            )
        else:
            _need(
                str(row[0]) == ordering.ordering_sha256
                and bytes(row[1]) == ordering_jcs,
                "PREINVOCATION_CONTROL_ORDERING_REPLAY_DIVERGENCE",
            )

        db.commit()
        return ordering
    except (JSpacePreInvocationControlOrderingError, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise


def read_preinvocation_control_ordering(
    db: sqlite3.Connection,
    *,
    controlled_executor_id: str,
    controlled_invocation_id: str,
) -> PreInvocationControlOrdering:
    """Read/revalidate immutable predecessor ordering after execution may have occurred."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    controlled_executor_id = _text(
        controlled_executor_id,
        "controlled_executor_id",
        256,
    )
    controlled_invocation_id = _text(
        controlled_invocation_id,
        "controlled_invocation_id",
        256,
    )
    try:
        row = db.execute(
            "SELECT ordering_jcs FROM hcu_jspace_preinvocation_control_orderings "
            "WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            (controlled_executor_id, controlled_invocation_id),
        ).fetchone()
    except sqlite3.Error as exc:
        raise JSpacePreInvocationControlOrderingError(
            "PREINVOCATION_CONTROL_ORDERING_STORE_UNAVAILABLE"
        ) from exc
    _need(
        row is not None,
        "PREINVOCATION_CONTROL_ORDERING_NOT_ADMITTED",
    )
    raw = bytes(row[0])
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JSpacePreInvocationControlOrderingError(
            "PREINVOCATION_CONTROL_ORDERING_STORED_BYTES_INVALID"
        ) from exc
    _need(
        isinstance(value, dict),
        "PREINVOCATION_CONTROL_ORDERING_STORED_OBJECT_REQUIRED",
    )
    _need(
        canonicalize(value) == raw,
        "PREINVOCATION_CONTROL_ORDERING_STORED_JCS_MISMATCH",
    )
    try:
        ordering = PreInvocationControlOrdering(**value)
    except TypeError as exc:
        raise JSpacePreInvocationControlOrderingError(
            "PREINVOCATION_CONTROL_ORDERING_STORED_FIELDS_INVALID"
        ) from exc
    validate_preinvocation_control_ordering(ordering)
    _need(
        ordering.controlled_executor_id == controlled_executor_id
        and ordering.controlled_invocation_id == controlled_invocation_id,
        "PREINVOCATION_CONTROL_ORDERING_LOOKUP_IDENTITY_MISMATCH",
    )
    return ordering


__all__ = [
    "SCHEMA",
    "JSpacePreInvocationControlOrderingError",
    "PreInvocationControlOrdering",
    "admit_preinvocation_control_ordering",
    "read_preinvocation_control_ordering",
    "validate_preinvocation_control_ordering",
]
