#!/usr/bin/env python3
"""Atomic model-execution admission inside the existing canonical MiniUnifiedDB.

This module closes the source-level trust split between an actual model-executor observation
and ``verify_model_execution`` without creating a second truth/state authority.  The caller
supplies the already-canonical MiniUnifiedDB ``sqlite3.Connection``; this module installs only
execution-evidence admission tables inside that same database.

The write path is intentionally stronger than a caller-supplied Mapping:

1. acquire ``BEGIN IMMEDIATE`` on MiniUnifiedDB;
2. require the exact live entity generation;
3. persist the RFC8785/JCS canonical observation bytes under their exact SHA-256;
4. claim the executor-scoped invocation key exactly once;
5. reject a later byte-distinct observation for the same invocation key;
6. call the existing pure ``verify_model_execution`` only from the admitted rows;
7. commit only after verification succeeds, otherwise roll back the whole admission.

These rows are provenance/replay fences for model execution.  They do not make model output
true, do not grant capabilities/effects, and do not create a second canonical product/state
store.  Source construction alone grants zero model/runtime credit; positive credit still
requires this path to be used by the real admitted model-executor boundary at exact identity.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import canonicalize
    from .model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        VerifiedModelExecution,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
        model_execution_observation_sha256,
        verify_model_execution,
    )
except ImportError:
    from entry_canonicalization_v1 import canonicalize
    from model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        VerifiedModelExecution,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
        model_execution_observation_sha256,
        verify_model_execution,
    )

SCHEMA = "HCU_MODEL_EXECUTION_ADMISSION_STORE/v1"


class ModelExecutionAdmissionStoreError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ModelExecutionAdmissionStoreError(message)


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise ModelExecutionAdmissionStoreError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def _install_schema_in_current_transaction(db: sqlite3.Connection) -> None:
    """Install replay-fence tables without opening, committing, or replacing a database."""
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    fk_row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk_row is not None and int(fk_row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_model_execution_observations(
          observation_sha256 TEXT PRIMARY KEY,
          observation_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_model_execution_invocations(
          invocation_binding_key TEXT PRIMARY KEY,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          observation_sha256 TEXT NOT NULL,
          FOREIGN KEY(observation_sha256)
            REFERENCES hcu_model_execution_observations(observation_sha256)
        )"""
    )


def _admit_observation(
    db: sqlite3.Connection,
    observation: ModelExecutionObservation,
) -> tuple[str, dict[str, Any]]:
    record = model_execution_observation_record(observation)
    observation_sha256 = model_execution_observation_sha256(observation)
    canonical_bytes = canonicalize(record)

    row = db.execute(
        "SELECT observation_jcs,entity_generation,executor_id,invocation_id "
        "FROM hcu_model_execution_observations WHERE observation_sha256=?",
        (observation_sha256,),
    ).fetchone()
    expected_identity = (
        record["entity_generation"],
        record["executor_id"],
        record["invocation_id"],
    )
    if row is None:
        db.execute(
            "INSERT INTO hcu_model_execution_observations "
            "(observation_sha256,observation_jcs,entity_generation,executor_id,invocation_id) "
            "VALUES(?,?,?,?,?)",
            (observation_sha256, canonical_bytes, *expected_identity),
        )
    else:
        stored_bytes = bytes(row[0])
        _need(stored_bytes == canonical_bytes, "MODEL_EXECUTION_OBSERVATION_DIGEST_COLLISION")
        _need(tuple(row[1:]) == expected_identity, "MODEL_EXECUTION_OBSERVATION_IDENTITY_MISMATCH")

    return observation_sha256, record


def _admit_invocation(
    db: sqlite3.Connection,
    observation: ModelExecutionObservation,
    observation_sha256: str,
) -> str:
    invocation_key = model_execution_invocation_binding_key(observation)
    record = model_execution_observation_record(observation)
    row = db.execute(
        "SELECT executor_id,invocation_id,entity_generation,observation_sha256 "
        "FROM hcu_model_execution_invocations WHERE invocation_binding_key=?",
        (invocation_key,),
    ).fetchone()
    expected = (
        record["executor_id"],
        record["invocation_id"],
        record["entity_generation"],
        observation_sha256,
    )
    if row is None:
        db.execute(
            "INSERT INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            (invocation_key, *expected),
        )
    else:
        # executor_id + invocation_id is globally immutable for this executor identity.
        # A generation change therefore does not silently permit the invocation label to be
        # reused with new bytes; executor incarnation belongs in executor_id if needed.
        _need(tuple(row) == expected, "MODEL_EXECUTION_INVOCATION_REPLAY_DIVERGENCE")
    return invocation_key


def _read_admitted_observation(db: sqlite3.Connection, observation_sha256: str) -> dict[str, Any]:
    row = db.execute(
        "SELECT observation_jcs FROM hcu_model_execution_observations WHERE observation_sha256=?",
        (observation_sha256,),
    ).fetchone()
    _need(row is not None, "MODEL_EXECUTION_OBSERVATION_ADMISSION_LOST")
    raw = bytes(row[0])
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelExecutionAdmissionStoreError("MODEL_EXECUTION_OBSERVATION_STORED_BYTES_INVALID") from exc
    _need(isinstance(value, dict), "MODEL_EXECUTION_OBSERVATION_STORED_OBJECT_REQUIRED")
    _need(canonicalize(value) == raw, "MODEL_EXECUTION_OBSERVATION_STORED_JCS_MISMATCH")
    return value


def admit_and_verify_model_execution(
    db: sqlite3.Connection,
    grid_plan: Any,
    verified_engine_load: Any,
    observation: ModelExecutionObservation,
    *,
    current_generation: int,
) -> VerifiedModelExecution:
    """Atomically admit one executor invocation and return its verified execution receipt.

    The function owns the transaction because ``BEGIN IMMEDIATE`` is the concurrency primitive.
    Callers must not wrap it in a weaker/nested transaction.  On every failure the transaction
    is rolled back, so an invalid observation cannot leave behind a partial invocation claim.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _need(type(current_generation) is int and current_generation >= 0, "CURRENT_GENERATION_INVALID")

    try:
        db.execute("BEGIN IMMEDIATE")
        live_generation = _current_generation(db)
        _need(live_generation == current_generation, "STALE_MODEL_EXECUTION_ADMISSION_GENERATION")
        _install_schema_in_current_transaction(db)

        observation_sha256, observation_record = _admit_observation(db, observation)
        invocation_key = _admit_invocation(db, observation, observation_sha256)

        persisted_observation = _read_admitted_observation(db, observation_sha256)
        invocation_row = db.execute(
            "SELECT observation_sha256 FROM hcu_model_execution_invocations "
            "WHERE invocation_binding_key=?",
            (invocation_key,),
        ).fetchone()
        _need(invocation_row is not None, "MODEL_EXECUTION_INVOCATION_ADMISSION_LOST")
        admitted_observation_sha256 = str(invocation_row[0])

        # Registry views are constructed only from rows read back under the same locked
        # MiniUnifiedDB transaction; callers cannot substitute a free-standing Mapping here.
        verified = verify_model_execution(
            grid_plan,
            verified_engine_load,
            observation,
            admitted_model_execution_observations={observation_sha256: persisted_observation},
            admitted_model_execution_invocations={invocation_key: admitted_observation_sha256},
            current_generation=current_generation,
        )
        _need(
            persisted_observation == observation_record,
            "MODEL_EXECUTION_OBSERVATION_POST_ADMISSION_MISMATCH",
        )
        db.commit()
        return verified
    except (ModelExecutionAdmissionStoreError, ModelExecutionReceiptError, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise
