#!/usr/bin/env python3
"""Process-persistent S1 CAS adapter for the EntityOS/HCU Xeno boot primitive.

This is an L1/L2 development adapter, not a physical-grid datastore. It persists the
noncanonical S1 cognitive workspace in SQLite so multiple local processes can observe
one epoch/digest and so coordinator writes are compare-and-swap fenced. It deliberately
reuses the exact validation/digest path from ``xeno_shared_state_boot_v1`` rather than
creating another S1 canonicalizer.

Ordinary nodes never write this store. Their ``NODE_RESULT/v1`` packets are ingested only
by a coordinator holding a current lease. S0 truth/effect/security authority remains
outside this module.
"""
from __future__ import annotations

import copy
import json
import sqlite3
from typing import Any, Mapping

from xeno_shared_state_boot_v1 import (
    COORDINATOR_LEASE_SCHEMA,
    NODE_RESULT_SCHEMA,
    CoordinatorLease,
    NodeResult,
    S1_SCHEMA,
    S1StateFabric,
    SharedStateError,
    SharedStateSnapshot,
    FORBIDDEN_S1_ROOTS,
    _canonical_bytes,
)

STORE_SCHEMA = "ENTITYOS_HCU_S1_SQLITE_CAS/v1"
RESULT_STORE_SCHEMA = "ENTITYOS_HCU_NODE_RESULT_INGEST/v1"


class S1StoreError(SharedStateError):
    pass


def _require_idle(db: sqlite3.Connection) -> None:
    if not isinstance(db, sqlite3.Connection):
        raise S1StoreError("db:SQLITE_CONNECTION_REQUIRED")
    if db.in_transaction:
        raise S1StoreError("OUTER_TRANSACTION_FORBIDDEN")


def _install_schema(db: sqlite3.Connection) -> None:
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_s1_state(
          slot INTEGER PRIMARY KEY CHECK(slot=1),
          store_schema TEXT NOT NULL,
          state_schema TEXT NOT NULL,
          epoch INTEGER NOT NULL CHECK(epoch>=0),
          digest TEXT NOT NULL,
          state_json TEXT NOT NULL
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_s1_node_results(
          result_id TEXT PRIMARY KEY,
          ingest_schema TEXT NOT NULL,
          result_schema TEXT NOT NULL,
          node_id TEXT NOT NULL,
          task_id TEXT NOT NULL,
          state_epoch INTEGER NOT NULL,
          state_digest TEXT NOT NULL,
          payload_ref TEXT NOT NULL,
          payload_sha256 TEXT NOT NULL,
          ingested_by TEXT NOT NULL
        )"""
    )


def _state_json(state: Mapping[str, Any]) -> str:
    return _canonical_bytes(dict(state)).decode("utf-8")


def _decode_state(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise S1StoreError("S1_STATE_JSON_TEXT_REQUIRED")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise S1StoreError("S1_STATE_JSON_INVALID") from exc
    if not isinstance(value, Mapping):
        raise S1StoreError("S1_STATE_MAPPING_REQUIRED")
    return S1StateFabric._validated_state(value)


def _load_snapshot_locked(db: sqlite3.Connection) -> SharedStateSnapshot:
    row = db.execute(
        "SELECT store_schema,state_schema,epoch,digest,state_json FROM hcu_s1_state WHERE slot=1"
    ).fetchone()
    if row is None:
        raise S1StoreError("S1_STORE_UNINITIALIZED")
    store_schema, state_schema, epoch, digest, raw_state = row
    if store_schema != STORE_SCHEMA:
        raise S1StoreError("S1_STORE_SCHEMA_MISMATCH")
    if state_schema != S1_SCHEMA:
        raise S1StoreError("S1_STATE_SCHEMA_MISMATCH")
    if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
        raise S1StoreError("S1_EPOCH_INVALID")
    if not isinstance(digest, str) or not digest:
        raise S1StoreError("S1_DIGEST_INVALID")
    state = _decode_state(raw_state)
    expected = S1StateFabric._state_digest(epoch, state)
    if expected != digest:
        raise S1StoreError("S1_PERSISTED_DIGEST_MISMATCH")
    return SharedStateSnapshot(S1_SCHEMA, epoch, digest, state)


def open_or_initialize(db: sqlite3.Connection, *, genesis_state: Mapping[str, Any] | None = None) -> SharedStateSnapshot:
    """Open an existing S1 store or atomically create epoch 0 from explicit genesis."""
    _require_idle(db)
    try:
        db.execute("BEGIN IMMEDIATE")
        _install_schema(db)
        row = db.execute("SELECT 1 FROM hcu_s1_state WHERE slot=1").fetchone()
        if row is None:
            if genesis_state is None:
                raise S1StoreError("S1_GENESIS_REQUIRED")
            snap = S1StateFabric(genesis_state).read_snapshot()
            db.execute(
                "INSERT INTO hcu_s1_state(slot,store_schema,state_schema,epoch,digest,state_json) VALUES(1,?,?,?,?,?)",
                (STORE_SCHEMA, S1_SCHEMA, snap.epoch, snap.digest, _state_json(snap.state)),
            )
        snap = _load_snapshot_locked(db)
        db.commit()
        return snap
    except Exception:
        db.rollback()
        raise


def read_snapshot(db: sqlite3.Connection) -> SharedStateSnapshot:
    """Read and revalidate the persisted epoch/digest; never trust stored digest blindly."""
    if not isinstance(db, sqlite3.Connection):
        raise S1StoreError("db:SQLITE_CONNECTION_REQUIRED")
    _install_schema(db)
    return _load_snapshot_locked(db)


def _require_current_lease(current: SharedStateSnapshot, lease: CoordinatorLease, node_id: str) -> None:
    if not isinstance(lease, CoordinatorLease):
        raise S1StoreError("COORDINATOR_LEASE_REQUIRED")
    if lease.schema != COORDINATOR_LEASE_SCHEMA:
        raise S1StoreError("COORDINATOR_LEASE_SCHEMA_UNSUPPORTED")
    if not isinstance(node_id, str) or not node_id.strip():
        raise S1StoreError("node_id:NONEMPTY_STRING_REQUIRED")
    node_id = node_id.strip()
    if lease.node_id != node_id:
        raise S1StoreError("COORDINATOR_LEASE_NODE_MISMATCH")
    if lease.state_epoch != current.epoch or lease.state_digest != current.digest:
        raise S1StoreError("STALE_COORDINATOR_LEASE")


def publish_delta(
    db: sqlite3.Connection,
    lease: CoordinatorLease,
    *,
    node_id: str,
    delta: Mapping[str, Any],
) -> SharedStateSnapshot:
    """Atomically publish one coordinator-scoped S1 delta using epoch+digest CAS."""
    _require_idle(db)
    try:
        db.execute("BEGIN IMMEDIATE")
        _install_schema(db)
        current = _load_snapshot_locked(db)
        _require_current_lease(current, lease, node_id)
        if not isinstance(delta, Mapping) or not delta:
            raise S1StoreError("delta:NONEMPTY_MAPPING_REQUIRED")
        roots = set(delta)
        if roots & FORBIDDEN_S1_ROOTS:
            raise S1StoreError("S1_DELTA_ATTEMPTS_S0_AUTHORITY")
        unauthorized = roots - set(lease.scope)
        if unauthorized:
            raise S1StoreError(f"S1_DELTA_OUT_OF_SCOPE:{','.join(sorted(unauthorized))}")

        next_state = copy.deepcopy(dict(current.state))
        for key, value in delta.items():
            next_state[key] = copy.deepcopy(value)
        next_state = S1StateFabric._validated_state(next_state)
        next_epoch = current.epoch + 1
        next_digest = S1StateFabric._state_digest(next_epoch, next_state)
        cursor = db.execute(
            """UPDATE hcu_s1_state
                  SET epoch=?,digest=?,state_json=?
                WHERE slot=1 AND store_schema=? AND state_schema=? AND epoch=? AND digest=?""",
            (
                next_epoch,
                next_digest,
                _state_json(next_state),
                STORE_SCHEMA,
                S1_SCHEMA,
                current.epoch,
                current.digest,
            ),
        )
        if cursor.rowcount != 1:
            raise S1StoreError("S1_CAS_LOST")
        after = _load_snapshot_locked(db)
        db.commit()
        return after
    except Exception:
        db.rollback()
        raise


def ingest_node_result(
    db: sqlite3.Connection,
    lease: CoordinatorLease,
    *,
    coordinator_node_id: str,
    result: NodeResult,
) -> dict[str, Any]:
    """Coordinator-only durable ingestion of an ephemeral ordinary-node result packet."""
    _require_idle(db)
    try:
        db.execute("BEGIN IMMEDIATE")
        _install_schema(db)
        current = _load_snapshot_locked(db)
        _require_current_lease(current, lease, coordinator_node_id)
        if not isinstance(result, NodeResult) or result.schema != NODE_RESULT_SCHEMA:
            raise S1StoreError("NODE_RESULT_SCHEMA_UNSUPPORTED")
        if result.state_epoch != current.epoch or result.state_digest != current.digest:
            raise S1StoreError("STALE_NODE_RESULT")
        task_ids = {
            str(task.get("task_id"))
            for task in current.state.get("tasks", [])
            if isinstance(task, Mapping)
        }
        if result.task_id not in task_ids:
            raise S1StoreError("NODE_RESULT_TASK_UNKNOWN")

        record = (
            RESULT_STORE_SCHEMA,
            result.schema,
            result.node_id,
            result.task_id,
            result.state_epoch,
            result.state_digest,
            result.payload_ref,
            result.payload_sha256,
            coordinator_node_id.strip(),
        )
        prior = db.execute(
            """SELECT ingest_schema,result_schema,node_id,task_id,state_epoch,state_digest,
                      payload_ref,payload_sha256,ingested_by
                 FROM hcu_s1_node_results WHERE result_id=?""",
            (result.result_id,),
        ).fetchone()
        if prior is not None:
            if tuple(prior) != record:
                raise S1StoreError("NODE_RESULT_ID_COLLISION")
            db.commit()
            return {"ok": True, "idempotent": True, "result_id": result.result_id}
        db.execute(
            "INSERT INTO hcu_s1_node_results VALUES(?,?,?,?,?,?,?,?,?,?)",
            (result.result_id, *record),
        )
        db.commit()
        return {"ok": True, "idempotent": False, "result_id": result.result_id}
    except Exception:
        db.rollback()
        raise


def list_ingested_results(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read-only deterministic result listing for coordinator compression/integration."""
    if not isinstance(db, sqlite3.Connection):
        raise S1StoreError("db:SQLITE_CONNECTION_REQUIRED")
    _install_schema(db)
    rows = db.execute(
        """SELECT result_id,result_schema,node_id,task_id,state_epoch,state_digest,
                  payload_ref,payload_sha256,ingested_by
             FROM hcu_s1_node_results ORDER BY result_id"""
    ).fetchall()
    names = (
        "result_id",
        "schema",
        "node_id",
        "task_id",
        "state_epoch",
        "state_digest",
        "payload_ref",
        "payload_sha256",
        "ingested_by",
    )
    return [dict(zip(names, row)) for row in rows]
