#!/usr/bin/env python3
"""Authority-backed pre-invocation control admission for EntityOS/HCU J-Space.

This is a successor source candidate to ``preinvocation_control_admission_store_v1``.  v1
already proves a canonically admitted predecessor ModelExecution, predecessor
JSpaceInferenceBinding/TrainingTrace packet ancestry, exact successor input bytes, and that
the successor ModelExecution has not yet been admitted.  The remaining source trust gap is
that cross-event recurrence must not rely on a stream label that is merely self-consistent
inside Typed Entry.

v2 therefore additionally requires ``HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE_BINDING/v2``.
That object obtains its stream authority by canonical MiniUnifiedDB readback of an externally
admitted stream decision.  The authorized lane is revalidated *inside the same BEGIN
IMMEDIATE transaction* that checks predecessor execution, successor-execution absence and
writes the preparation.  Thus a preparation cannot earn v2 source credit from a caller-only
stream label or a post-hoc lane object.

This module reuses the existing canonical MiniUnifiedDB connection and creates only a
successor-version subordinate evidence table.  It is not a second truth/effect authority and
is not current release authority until explicit selection.  It still does NOT prove actual
physical call ordering, executor sequence adjacency, hidden-state use, counterfactual causal
influence, model runtime or training benefit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any

try:
    from .authorized_executor_sequence_lane_binding_v2 import (
        AUTHORIZED_LANE_SCHEMA,
        AuthorizedExecutorSequenceLaneBindingV2,
        AuthorizedExecutorSequenceLaneBindingV2Error,
        bind_authorized_executor_sequence_lane_v2,
        validate_authorized_executor_sequence_lane_v2,
    )
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .entry_stream_authority_binding_v1 import EntryStreamAuthorityBinding
    from .grid10_scheduler_v1 import GridPlan
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding
    from .jspace_training_trace_v1 import TrainingTrace
    from .model_input_control_binding_v1 import ModelInputControlBinding
    from .preinvocation_canonical_predecessor_guard_v1 import (
        PreInvocationCanonicalPredecessorError,
        require_canonical_predecessor_execution,
    )
    from .preinvocation_control_admission_store_v1 import (
        PreInvocationControlAdmissionError as V1PreInvocationError,
        _controlled_execution_already_admitted as v1_controlled_execution_already_admitted,
        _validate_sources as validate_v1_preinvocation_sources,
    )
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from authorized_executor_sequence_lane_binding_v2 import (
        AUTHORIZED_LANE_SCHEMA,
        AuthorizedExecutorSequenceLaneBindingV2,
        AuthorizedExecutorSequenceLaneBindingV2Error,
        bind_authorized_executor_sequence_lane_v2,
        validate_authorized_executor_sequence_lane_v2,
    )
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from entry_stream_authority_binding_v1 import EntryStreamAuthorityBinding
    from grid10_scheduler_v1 import GridPlan
    from jspace_inference_binding_v1 import JSpaceInferenceBinding
    from jspace_training_trace_v1 import TrainingTrace
    from model_input_control_binding_v1 import ModelInputControlBinding
    from preinvocation_canonical_predecessor_guard_v1 import (
        PreInvocationCanonicalPredecessorError,
        require_canonical_predecessor_execution,
    )
    from preinvocation_control_admission_store_v1 import (
        PreInvocationControlAdmissionError as V1PreInvocationError,
        _controlled_execution_already_admitted as v1_controlled_execution_already_admitted,
        _validate_sources as validate_v1_preinvocation_sources,
    )
    from xeno_entry_fabric_v1 import EntryPacket

STORE_SCHEMA = "HCU_PREINVOCATION_CONTROL_ADMISSION_STORE/v2"
PREPARATION_SCHEMA = "HCU_PREINVOCATION_CONTROL_PREPARATION/v2"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class PreInvocationControlAdmissionV2Error(ValueError):
    pass


@dataclass(frozen=True)
class PreInvocationControlPreparationV2:
    schema: str
    canonicalization_schema: str
    generation: int
    predecessor_jspace_binding_sha256: str
    predecessor_training_trace_sha256: str
    predecessor_model_execution_observation_sha256: str
    predecessor_model_executor_id: str
    predecessor_model_invocation_id: str
    predecessor_vector_control_packet_sha256: str
    authorized_lane_schema: str
    authorized_lane_binding_sha256: str
    sequence_lane_sha256: str
    stream_authority_binding_sha256: str
    stream_authority_admission_sha256: str
    stream_authority_decision_sha256: str
    controlled_entry_event_sha256: str
    controlled_entry_admission_sha256: str
    controlled_grid_plan_sha256: str
    model_input_control_binding_sha256: str
    controlled_executor_id: str
    controlled_invocation_id: str
    controlled_input_sha256: str
    controlled_input_size: int
    preparation_sha256: str


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise PreInvocationControlAdmissionV2Error(code)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
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


def _safe_int(value: Any, field: str) -> int:
    _need(
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonicalize(value)).hexdigest()


def _material(preparation: PreInvocationControlPreparationV2) -> dict[str, Any]:
    value = asdict(preparation)
    value.pop("preparation_sha256", None)
    return value


def _invocation_key(executor_id: str, invocation_id: str) -> str:
    return _canonical_sha256(
        {
            "schema": "HCU_PREINVOCATION_CONTROL_INVOCATION_KEY/v2",
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "executor_id": _text(executor_id, "executor_id", 256),
            "invocation_id": _text(invocation_id, "invocation_id", 256),
        }
    )


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise PreInvocationControlAdmissionV2Error("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _safe_int(row[0], "entity_state.generation")


def _foreign_keys_enabled(db: sqlite3.Connection) -> None:
    row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(row is not None and int(row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    _foreign_keys_enabled(db)
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_preinvocation_control_preparations_v2(
          preparation_sha256 TEXT PRIMARY KEY,
          preparation_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          controlled_executor_id TEXT NOT NULL,
          controlled_invocation_id TEXT NOT NULL,
          predecessor_training_trace_sha256 TEXT NOT NULL,
          predecessor_jspace_binding_sha256 TEXT NOT NULL,
          authorized_lane_binding_sha256 TEXT NOT NULL,
          stream_authority_admission_sha256 TEXT NOT NULL,
          model_input_control_binding_sha256 TEXT NOT NULL,
          UNIQUE(controlled_executor_id, controlled_invocation_id)
        )"""
    )


def _validate_static_sources(
    controlled_entry: EntryPacket,
    predecessor_trace: TrainingTrace,
    predecessor_jspace_binding: JSpaceInferenceBinding,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    controlled_grid_plan: GridPlan,
    *,
    current_generation: int,
) -> None:
    _need(isinstance(controlled_entry, EntryPacket), "CONTROLLED_ENTRY_PACKET_REQUIRED")
    try:
        validate_v1_preinvocation_sources(
            predecessor_trace,
            predecessor_jspace_binding,
            input_binding,
            consumed_input_bytes,
            controlled_grid_plan,
            current_generation=current_generation,
        )
    except V1PreInvocationError as exc:
        raise PreInvocationControlAdmissionV2Error(f"PREINVOCATION_V1_SOURCE_REJECTED:{exc}") from exc
    for left, right, code in (
        (controlled_entry.entity_generation, current_generation, "CONTROLLED_ENTRY_GENERATION_MISMATCH"),
        (controlled_entry.event_sha256, input_binding.entry_event_sha256, "CONTROLLED_ENTRY_EVENT_MISMATCH"),
        (controlled_entry.admission_sha256, input_binding.entry_admission_sha256, "CONTROLLED_ENTRY_ADMISSION_MISMATCH"),
        (controlled_entry.event_sha256, controlled_grid_plan.entry_event_sha256, "CONTROLLED_ENTRY_GRID_EVENT_MISMATCH"),
        (controlled_entry.admission_sha256, controlled_grid_plan.entry_admission_sha256, "CONTROLLED_ENTRY_GRID_ADMISSION_MISMATCH"),
    ):
        _need(left == right, code)


def _bind_authorized_lane(
    db: sqlite3.Connection,
    controlled_entry: EntryPacket,
    controlled_grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    current_generation: int,
) -> AuthorizedExecutorSequenceLaneBindingV2:
    try:
        lane = bind_authorized_executor_sequence_lane_v2(
            db,
            controlled_entry,
            controlled_grid_plan,
            input_binding,
            consumed_input_bytes,
            stream_authority,
            current_generation=current_generation,
        )
        validate_authorized_executor_sequence_lane_v2(
            db,
            lane,
            controlled_entry,
            controlled_grid_plan,
            input_binding,
            consumed_input_bytes,
            stream_authority,
            current_generation=current_generation,
        )
    except AuthorizedExecutorSequenceLaneBindingV2Error as exc:
        raise PreInvocationControlAdmissionV2Error(f"AUTHORIZED_SEQUENCE_LANE_REJECTED:{exc}") from exc
    _need(lane.entry_event_sha256 == input_binding.entry_event_sha256, "AUTHORIZED_LANE_ENTRY_EVENT_MISMATCH")
    _need(lane.entry_admission_sha256 == input_binding.entry_admission_sha256, "AUTHORIZED_LANE_ENTRY_ADMISSION_MISMATCH")
    _need(lane.executor_id == input_binding.executor_id, "AUTHORIZED_LANE_EXECUTOR_MISMATCH")
    _need(lane.invocation_id == input_binding.invocation_id, "AUTHORIZED_LANE_INVOCATION_MISMATCH")
    return lane


def prepare_preinvocation_control_v2(
    db: sqlite3.Connection,
    controlled_entry: EntryPacket,
    predecessor_trace: TrainingTrace,
    predecessor_jspace_binding: JSpaceInferenceBinding,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    controlled_grid_plan: GridPlan,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    current_generation: int,
) -> PreInvocationControlPreparationV2:
    """Atomically admit predecessor control only through an independently authorized stream lane."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _foreign_keys_enabled(db)
    current_generation = _safe_int(current_generation, "current_generation")
    _validate_static_sources(
        controlled_entry,
        predecessor_trace,
        predecessor_jspace_binding,
        input_binding,
        consumed_input_bytes,
        controlled_grid_plan,
        current_generation=current_generation,
    )

    # Early read-only discriminator: fail before a v2 table can exist if stream authority is absent.
    lane = _bind_authorized_lane(
        db,
        controlled_entry,
        controlled_grid_plan,
        input_binding,
        consumed_input_bytes,
        stream_authority,
        current_generation=current_generation,
    )

    try:
        db.execute("BEGIN IMMEDIATE")
        _need(_current_generation(db) == current_generation, "STALE_PREINVOCATION_CONTROL_V2_GENERATION")

        # Revalidate the authorized lane under the same canonical writer lock as preparation.
        lane = _bind_authorized_lane(
            db,
            controlled_entry,
            controlled_grid_plan,
            input_binding,
            consumed_input_bytes,
            stream_authority,
            current_generation=current_generation,
        )
        try:
            predecessor_observation_sha256 = require_canonical_predecessor_execution(
                db,
                predecessor_jspace_binding,
                current_generation=current_generation,
            )
        except PreInvocationCanonicalPredecessorError as exc:
            raise PreInvocationControlAdmissionV2Error(
                f"PREDECESSOR_CANONICAL_EXECUTION_REJECTED:{exc}"
            ) from exc
        _need(
            predecessor_observation_sha256 == predecessor_jspace_binding.model_execution_observation_sha256,
            "PREDECESSOR_CANONICAL_EXECUTION_OBSERVATION_MISMATCH",
        )
        try:
            already_admitted = v1_controlled_execution_already_admitted(
                db,
                executor_id=input_binding.executor_id,
                invocation_id=input_binding.invocation_id,
            )
        except V1PreInvocationError as exc:
            raise PreInvocationControlAdmissionV2Error(f"CONTROLLED_EXECUTION_LOOKUP_REJECTED:{exc}") from exc
        _need(
            not already_admitted,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_POSTHOC_PREPARATION_FORBIDDEN",
        )

        material = {
            "schema": PREPARATION_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "generation": current_generation,
            "predecessor_jspace_binding_sha256": _sha256(predecessor_jspace_binding.binding_sha256, "predecessor_jspace_binding_sha256"),
            "predecessor_training_trace_sha256": _sha256(predecessor_trace.trace_sha256, "predecessor_training_trace_sha256"),
            "predecessor_model_execution_observation_sha256": _sha256(predecessor_observation_sha256, "predecessor_model_execution_observation_sha256"),
            "predecessor_model_executor_id": _text(predecessor_jspace_binding.model_execution_executor_id, "predecessor_model_executor_id", 256),
            "predecessor_model_invocation_id": _text(predecessor_jspace_binding.model_execution_invocation_id, "predecessor_model_invocation_id", 256),
            "predecessor_vector_control_packet_sha256": _sha256(predecessor_trace.vector_control_packet_sha256, "predecessor_vector_control_packet_sha256"),
            "authorized_lane_schema": AUTHORIZED_LANE_SCHEMA,
            "authorized_lane_binding_sha256": _sha256(lane.binding_sha256, "authorized_lane_binding_sha256"),
            "sequence_lane_sha256": _sha256(lane.sequence_lane_sha256, "sequence_lane_sha256"),
            "stream_authority_binding_sha256": _sha256(lane.stream_authority_binding_sha256, "stream_authority_binding_sha256"),
            "stream_authority_admission_sha256": _sha256(lane.stream_authority_admission_sha256, "stream_authority_admission_sha256"),
            "stream_authority_decision_sha256": _sha256(lane.stream_authority_decision_sha256, "stream_authority_decision_sha256"),
            "controlled_entry_event_sha256": _sha256(input_binding.entry_event_sha256, "controlled_entry_event_sha256"),
            "controlled_entry_admission_sha256": _sha256(input_binding.entry_admission_sha256, "controlled_entry_admission_sha256"),
            "controlled_grid_plan_sha256": _sha256(controlled_grid_plan.plan_sha256, "controlled_grid_plan_sha256"),
            "model_input_control_binding_sha256": _sha256(input_binding.binding_sha256, "model_input_control_binding_sha256"),
            "controlled_executor_id": _text(input_binding.executor_id, "controlled_executor_id", 256),
            "controlled_invocation_id": _text(input_binding.invocation_id, "controlled_invocation_id", 256),
            "controlled_input_sha256": _sha256(input_binding.input_sha256, "controlled_input_sha256"),
            "controlled_input_size": _safe_int(input_binding.input_size, "controlled_input_size"),
        }
        preparation = PreInvocationControlPreparationV2(
            **material,
            preparation_sha256=_canonical_sha256(material),
        )
        raw = canonicalize(asdict(preparation))
        _install_schema(db)
        key = _invocation_key(preparation.controlled_executor_id, preparation.controlled_invocation_id)
        existing = db.execute(
            "SELECT preparation_sha256,preparation_jcs FROM hcu_preinvocation_control_preparations_v2 "
            "WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            (preparation.controlled_executor_id, preparation.controlled_invocation_id),
        ).fetchone()
        if existing is None:
            db.execute(
                "INSERT INTO hcu_preinvocation_control_preparations_v2 "
                "(preparation_sha256,preparation_jcs,entity_generation,controlled_executor_id,controlled_invocation_id,"
                "predecessor_training_trace_sha256,predecessor_jspace_binding_sha256,authorized_lane_binding_sha256,"
                "stream_authority_admission_sha256,model_input_control_binding_sha256) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    preparation.preparation_sha256,
                    raw,
                    preparation.generation,
                    preparation.controlled_executor_id,
                    preparation.controlled_invocation_id,
                    preparation.predecessor_training_trace_sha256,
                    preparation.predecessor_jspace_binding_sha256,
                    preparation.authorized_lane_binding_sha256,
                    preparation.stream_authority_admission_sha256,
                    preparation.model_input_control_binding_sha256,
                ),
            )
        else:
            _need(
                str(existing[0]) == preparation.preparation_sha256 and bytes(existing[1]) == raw,
                "PREINVOCATION_CONTROL_V2_REPLAY_DIVERGENCE",
            )
        # Key is recomputed and intentionally not stored as an extra authority column; the unique
        # executor/invocation pair above is the canonical replay fence.
        _need(bool(key), "PREINVOCATION_CONTROL_V2_INVOCATION_KEY_REQUIRED")
        db.commit()
        return preparation
    except (PreInvocationControlAdmissionV2Error, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise


def read_preinvocation_control_preparation_v2(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> PreInvocationControlPreparationV2:
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    try:
        row = db.execute(
            "SELECT preparation_jcs FROM hcu_preinvocation_control_preparations_v2 "
            "WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            (_text(executor_id, "executor_id", 256), _text(invocation_id, "invocation_id", 256)),
        ).fetchone()
    except sqlite3.Error as exc:
        raise PreInvocationControlAdmissionV2Error("PREINVOCATION_CONTROL_V2_STORE_REQUIRED") from exc
    _need(row is not None, "PREINVOCATION_CONTROL_V2_PREPARATION_NOT_ADMITTED")
    raw = bytes(row[0])
    try:
        value = json.loads(raw.decode("utf-8"))
        preparation = PreInvocationControlPreparationV2(**value)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise PreInvocationControlAdmissionV2Error("PREINVOCATION_CONTROL_V2_STORED_BYTES_INVALID") from exc
    _need(canonicalize(value) == raw, "PREINVOCATION_CONTROL_V2_STORED_JCS_MISMATCH")
    _need(_canonical_sha256(_material(preparation)) == preparation.preparation_sha256, "PREINVOCATION_CONTROL_V2_DIGEST_MISMATCH")
    _need(preparation.controlled_executor_id == executor_id, "PREINVOCATION_CONTROL_V2_EXECUTOR_MISMATCH")
    _need(preparation.controlled_invocation_id == invocation_id, "PREINVOCATION_CONTROL_V2_INVOCATION_MISMATCH")
    return preparation


__all__ = [
    "STORE_SCHEMA",
    "PREPARATION_SCHEMA",
    "PreInvocationControlAdmissionV2Error",
    "PreInvocationControlPreparationV2",
    "prepare_preinvocation_control_v2",
    "read_preinvocation_control_preparation_v2",
]
