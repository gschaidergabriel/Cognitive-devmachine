#!/usr/bin/env python3
"""Shared-state fabric for the autonomous Xeno/HCU target.

S1 is noncanonical cognitive workspace state. Ordinary nodes only read S1 and emit
an ephemeral NODE_RESULT/v1. Only a current scoped GRID_COORDINATOR_LEASE/v1 may
commit S1, and every commit is generation + epoch + digest CAS-bound. This module
creates no S0 truth/effect/security authority.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

FABRIC_SCHEMA = "ENTITYOS_HCU_SHARED_STATE_FABRIC/v1"
SNAPSHOT_SCHEMA = "ENTITYOS_HCU_S1_SNAPSHOT/v1"
BOOT_SCHEMA = "XENO_AUTONOMOUS_BOOT/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
COMMIT_SCHEMA = "ENTITYOS_HCU_S1_COORDINATOR_COMMIT/v1"


class SharedStateFabricError(ValueError):
    pass


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise SharedStateFabricError(message)


def _text(value: Any, field: str) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    _need(len(value) <= 512, f"{field}:TOO_LONG")
    return value


def _int(value: Any, field: str) -> int:
    _need(type(value) is int and value >= 0, f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _sha(value: Any, field: str) -> str:
    _need(isinstance(value, str), f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    _need(len(value) == 64 and value == value.lower() and all(c in "0123456789abcdef" for c in value),
          f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _digest(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise SharedStateFabricError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _state_digest(scope: str, generation: int, epoch: int, state: Mapping[str, Any]) -> str:
    return _digest({"schema": SNAPSHOT_SCHEMA, "scope": scope, "generation": generation,
                    "epoch": epoch, "state": state}, "S1_STATE")


def _state_json(state: Mapping[str, Any]) -> str:
    _digest(state, "S1_STATE")
    try:
        return json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SharedStateFabricError("S1_STATE:JSON_SERIALIZATION_FAILED") from exc


def install_schema(db: sqlite3.Connection) -> dict[str, Any]:
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    db.execute("""CREATE TABLE IF NOT EXISTS xeno_s1_scopes(
        scope TEXT PRIMARY KEY, generation INTEGER NOT NULL CHECK(generation>=0),
        epoch INTEGER NOT NULL CHECK(epoch>=0), state_json TEXT NOT NULL,
        state_sha256 TEXT NOT NULL CHECK(length(state_sha256)=64))""")
    db.execute("""CREATE TABLE IF NOT EXISTS xeno_node_admissions(
        node_id TEXT PRIMARY KEY, generation INTEGER NOT NULL CHECK(generation>=0),
        capability_binding_sha256 TEXT NOT NULL CHECK(length(capability_binding_sha256)=64),
        policy_binding_sha256 TEXT NOT NULL CHECK(length(policy_binding_sha256)=64),
        admitted INTEGER NOT NULL DEFAULT 1 CHECK(admitted IN(0,1)))""")
    db.execute("""CREATE TABLE IF NOT EXISTS xeno_coordinator_leases(
        lease_id TEXT PRIMARY KEY, schema TEXT NOT NULL, scope TEXT NOT NULL, node_id TEXT NOT NULL,
        generation INTEGER NOT NULL CHECK(generation>=0), bound_epoch INTEGER NOT NULL CHECK(bound_epoch>=0),
        bound_state_sha256 TEXT NOT NULL CHECK(length(bound_state_sha256)=64),
        eligibility_sha256 TEXT NOT NULL CHECK(length(eligibility_sha256)=64),
        policy_binding_sha256 TEXT NOT NULL CHECK(length(policy_binding_sha256)=64),
        issued_at_ns INTEGER NOT NULL CHECK(issued_at_ns>=0), expires_at_ns INTEGER NOT NULL,
        revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN(0,1)),
        CHECK(expires_at_ns>issued_at_ns), FOREIGN KEY(scope) REFERENCES xeno_s1_scopes(scope),
        FOREIGN KEY(node_id) REFERENCES xeno_node_admissions(node_id))""")
    return {"ok": True, "schema": FABRIC_SCHEMA, "ordinary_node_s1_write_api": False,
            "s0_authority_created": False, "effect_authority_created": False}


def controller_initialize_scope(db: sqlite3.Connection, *, scope: str, generation: int,
                                state: Mapping[str, Any]) -> dict[str, Any]:
    scope, generation = _text(scope, "scope"), _int(generation, "generation")
    _need(isinstance(state, Mapping), "state:MAPPING_REQUIRED")
    state = dict(state)
    digest = _state_digest(scope, generation, 0, state)
    try:
        db.execute("INSERT INTO xeno_s1_scopes VALUES(?,?,?,?,?)",
                   (scope, generation, 0, _state_json(state), digest))
    except sqlite3.IntegrityError as exc:
        raise SharedStateFabricError("S1_SCOPE_ALREADY_EXISTS") from exc
    return {"scope": scope, "generation": generation, "epoch": 0, "state_sha256": digest, "state": state}


def read_snapshot(db: sqlite3.Connection, *, scope: str, generation: int) -> dict[str, Any]:
    scope, generation = _text(scope, "scope"), _int(generation, "generation")
    row = db.execute("SELECT generation,epoch,state_json,state_sha256 FROM xeno_s1_scopes WHERE scope=?",
                     (scope,)).fetchone()
    _need(row is not None, "S1_SCOPE_NOT_FOUND")
    _need(row[0] == generation, "STALE_ENTITY_GENERATION")
    try:
        state = json.loads(row[2])
    except json.JSONDecodeError as exc:
        raise SharedStateFabricError("S1_STATE:CORRUPT_JSON") from exc
    _need(isinstance(state, Mapping), "S1_STATE:MAPPING_REQUIRED")
    _need(row[3] == _state_digest(scope, generation, row[1], state), "S1_DIGEST_MISMATCH")
    return {"scope": scope, "generation": generation, "epoch": row[1], "state_sha256": row[3], "state": state}


def controller_admit_node(db: sqlite3.Connection, *, node_id: str, generation: int,
                          capability_binding_sha256: str, policy_binding_sha256: str) -> None:
    node_id, generation = _text(node_id, "node_id"), _int(generation, "generation")
    cap, policy = _sha(capability_binding_sha256, "capability_binding_sha256"), _sha(policy_binding_sha256, "policy_binding_sha256")
    row = db.execute("SELECT generation,capability_binding_sha256,policy_binding_sha256,admitted FROM xeno_node_admissions WHERE node_id=?",
                     (node_id,)).fetchone()
    if row is not None:
        _need(tuple(row) == (generation, cap, policy, 1), "NODE_ID_ALREADY_BOUND_DIFFERENTLY")
        return
    db.execute("INSERT INTO xeno_node_admissions VALUES(?,?,?,?,1)", (node_id, generation, cap, policy))


def _active_lease(db: sqlite3.Connection, scope: str, now_ns: int) -> tuple[Any, ...] | None:
    rows = db.execute("SELECT lease_id,node_id,generation,bound_epoch,bound_state_sha256,expires_at_ns "
                      "FROM xeno_coordinator_leases WHERE scope=? AND revoked=0 AND issued_at_ns<=? AND expires_at_ns>? "
                      "ORDER BY lease_id", (scope, now_ns, now_ns)).fetchall()
    _need(len(rows) <= 1, "MULTIPLE_ACTIVE_COORDINATORS_SAME_SCOPE")
    return rows[0] if rows else None


def controller_grant_lease(db: sqlite3.Connection, *, lease_id: str, scope: str, node_id: str,
                           generation: int, expected_epoch: int, expected_state_sha256: str,
                           eligibility_sha256: str, policy_binding_sha256: str,
                           issued_at_ns: int, expires_at_ns: int) -> dict[str, Any]:
    lease_id, scope, node_id = _text(lease_id, "lease_id"), _text(scope, "scope"), _text(node_id, "node_id")
    generation, expected_epoch = _int(generation, "generation"), _int(expected_epoch, "expected_epoch")
    expected_state_sha256 = _sha(expected_state_sha256, "expected_state_sha256")
    eligibility_sha256, policy_binding_sha256 = _sha(eligibility_sha256, "eligibility_sha256"), _sha(policy_binding_sha256, "policy_binding_sha256")
    issued_at_ns, expires_at_ns = _int(issued_at_ns, "issued_at_ns"), _int(expires_at_ns, "expires_at_ns")
    _need(expires_at_ns > issued_at_ns, "LEASE_EXPIRY_MUST_FOLLOW_ISSUE")
    _need(not db.in_transaction, "COORDINATOR_LEASE_REQUIRES_TRANSACTION_BOUNDARY")
    db.execute("BEGIN IMMEDIATE")
    try:
        snap = read_snapshot(db, scope=scope, generation=generation)
        _need(snap["epoch"] == expected_epoch, "LEASE_STATE_EPOCH_MISMATCH")
        _need(snap["state_sha256"] == expected_state_sha256, "LEASE_STATE_DIGEST_MISMATCH")
        node = db.execute("SELECT generation,policy_binding_sha256,admitted FROM xeno_node_admissions WHERE node_id=?", (node_id,)).fetchone()
        _need(node is not None and node[2] == 1, "NODE_NOT_ADMITTED")
        _need(node[0] == generation and node[1] == policy_binding_sha256, "NODE_POLICY_OR_GENERATION_MISMATCH")
        _need(_active_lease(db, scope, issued_at_ns) is None, "ACTIVE_COORDINATOR_ALREADY_EXISTS")
        db.execute("INSERT INTO xeno_coordinator_leases VALUES(?,?,?,?,?,?,?,?,?,?,?,0)",
                   (lease_id, LEASE_SCHEMA, scope, node_id, generation, snap["epoch"], snap["state_sha256"],
                    eligibility_sha256, policy_binding_sha256, issued_at_ns, expires_at_ns))
        db.commit()
    except Exception:
        db.rollback(); raise
    return {"schema": LEASE_SCHEMA, "lease_id": lease_id, "scope": scope, "node_id": node_id,
            "bound_epoch": snap["epoch"], "bound_state_sha256": snap["state_sha256"],
            "authority": "S1_SCOPE_WRITE_ONLY_NOT_S0"}


def _work(state: Mapping[str, Any], capabilities: set[str]) -> tuple[str | None, str | None]:
    items = state.get("work_items", [])
    _need(isinstance(items, list), "S1_WORK_ITEMS_LIST_REQUIRED")
    choices = []
    for item in items:
        _need(isinstance(item, Mapping), "S1_WORK_ITEM_MAPPING_REQUIRED")
        if item.get("status") != "OPEN":
            continue
        req = item.get("required_capabilities", [])
        _need(isinstance(req, list), "WORK_CAPABILITIES_LIST_REQUIRED")
        if {_text(v, "required_capability") for v in req} <= capabilities:
            priority = item.get("priority", 0)
            _need(type(priority) is int, "WORK_PRIORITY_INTEGER_REQUIRED")
            choices.append((-priority, _text(item.get("work_id"), "work_id"), _text(item.get("payload_ref"), "payload_ref")))
    return (choices and sorted(choices)[0][1:]) or (None, None)


def autonomous_boot(db: sqlite3.Connection, *, node_id: str, generation: int,
                    capability_binding_sha256: str, policy_binding_sha256: str,
                    capabilities: Sequence[str], scope: str, now_ns: int) -> dict[str, Any]:
    node_id, scope = _text(node_id, "node_id"), _text(scope, "scope")
    generation, now_ns = _int(generation, "generation"), _int(now_ns, "now_ns")
    cap, policy = _sha(capability_binding_sha256, "capability_binding_sha256"), _sha(policy_binding_sha256, "policy_binding_sha256")
    _need(not isinstance(capabilities, (str, bytes)), "capabilities:SEQUENCE_REQUIRED")
    caps = {_text(v, "capability") for v in capabilities}
    node = db.execute("SELECT generation,capability_binding_sha256,policy_binding_sha256,admitted FROM xeno_node_admissions WHERE node_id=?", (node_id,)).fetchone()
    _need(node is not None and node[3] == 1, "NODE_NOT_ADMITTED")
    _need(tuple(node[:3]) == (generation, cap, policy), "NODE_BINDING_MISMATCH")
    snap = read_snapshot(db, scope=scope, generation=generation)
    work_id, payload_ref = _work(snap["state"], caps)
    lease = _active_lease(db, scope, now_ns)
    return {"schema": BOOT_SCHEMA, "node_id": node_id, "generation": generation, "scope": scope,
            "state_epoch": snap["epoch"], "state_sha256": snap["state_sha256"], "read_only_s1": True,
            "selected_work_id": work_id, "selected_work_payload_ref": payload_ref,
            "coordinator_lease_id": lease[0] if lease else None, "coordinator_node_id": lease[1] if lease else None}


def make_node_result(db: sqlite3.Connection, *, boot: Mapping[str, Any], result_id: str, work_id: str,
                     payload_ref: str, payload_sha256: str, now_ns: int) -> dict[str, Any]:
    _need(isinstance(boot, Mapping) and boot.get("schema") == BOOT_SCHEMA and boot.get("read_only_s1") is True, "READ_ONLY_BOOT_REQUIRED")
    now_ns = _int(now_ns, "now_ns")
    snap = read_snapshot(db, scope=boot["scope"], generation=boot["generation"])
    _need((snap["epoch"], snap["state_sha256"]) == (boot["state_epoch"], boot["state_sha256"]), "BOOT_STATE_STALE")
    lease = _active_lease(db, boot["scope"], now_ns)
    _need(lease is not None, "NO_VALID_COORDINATOR_ROUTE")
    _need((lease[2], lease[3], lease[4]) == (boot["generation"], snap["epoch"], snap["state_sha256"]), "COORDINATOR_LEASE_STALE")
    result = {"schema": NODE_RESULT_SCHEMA, "result_id": _text(result_id, "result_id"), "node_id": boot["node_id"],
              "generation": boot["generation"], "scope": boot["scope"], "work_id": _text(work_id, "work_id"),
              "state_epoch": snap["epoch"], "state_sha256": snap["state_sha256"], "coordinator_lease_id": lease[0],
              "coordinator_node_id": lease[1], "payload_ref": _text(payload_ref, "payload_ref"),
              "payload_sha256": _sha(payload_sha256, "payload_sha256")}
    result["result_sha256"] = _digest(result, "NODE_RESULT")
    return result


def validate_node_result(db: sqlite3.Connection, *, result: Mapping[str, Any], coordinator_node_id: str,
                         coordinator_lease_id: str, now_ns: int) -> dict[str, Any]:
    _need(isinstance(result, Mapping) and result.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_REQUIRED")
    coordinator_node_id, coordinator_lease_id = _text(coordinator_node_id, "coordinator_node_id"), _text(coordinator_lease_id, "coordinator_lease_id")
    _need((result.get("coordinator_node_id"), result.get("coordinator_lease_id")) == (coordinator_node_id, coordinator_lease_id), "NODE_RESULT_MISROUTED")
    snap = read_snapshot(db, scope=result["scope"], generation=result["generation"])
    _need(result.get("state_epoch") == snap["epoch"], "STALE_NODE_RESULT_EPOCH")
    _need(result.get("state_sha256") == snap["state_sha256"], "STALE_NODE_RESULT_DIGEST")
    lease = _active_lease(db, result["scope"], _int(now_ns, "now_ns"))
    _need(lease is not None and lease[0] == coordinator_lease_id and lease[1] == coordinator_node_id, "COORDINATOR_LEASE_MISMATCH")
    return snap


def coordinator_commit(db: sqlite3.Connection, *, coordinator_node_id: str, coordinator_lease_id: str,
                       scope: str, generation: int, expected_epoch: int, expected_state_sha256: str,
                       new_state: Mapping[str, Any], now_ns: int) -> dict[str, Any]:
    coordinator_node_id, coordinator_lease_id, scope = _text(coordinator_node_id, "coordinator_node_id"), _text(coordinator_lease_id, "coordinator_lease_id"), _text(scope, "scope")
    generation, expected_epoch, now_ns = _int(generation, "generation"), _int(expected_epoch, "expected_epoch"), _int(now_ns, "now_ns")
    expected_state_sha256 = _sha(expected_state_sha256, "expected_state_sha256")
    _need(isinstance(new_state, Mapping), "new_state:MAPPING_REQUIRED")
    _need(not db.in_transaction, "COORDINATOR_COMMIT_REQUIRES_TRANSACTION_BOUNDARY")
    db.execute("BEGIN IMMEDIATE")
    try:
        snap = read_snapshot(db, scope=scope, generation=generation)
        _need((snap["epoch"], snap["state_sha256"]) == (expected_epoch, expected_state_sha256), "S1_CAS_MISMATCH")
        lease = _active_lease(db, scope, now_ns)
        _need(lease is not None, "NO_VALID_COORDINATOR_LEASE")
        _need((lease[0], lease[1], lease[2], lease[3], lease[4]) ==
              (coordinator_lease_id, coordinator_node_id, generation, snap["epoch"], snap["state_sha256"]), "COORDINATOR_LEASE_STALE_OR_MISMATCHED")
        epoch = snap["epoch"] + 1
        state = dict(new_state)
        digest = _state_digest(scope, generation, epoch, state)
        cur = db.execute("UPDATE xeno_s1_scopes SET epoch=?,state_json=?,state_sha256=? WHERE scope=? AND generation=? AND epoch=? AND state_sha256=?",
                         (epoch, _state_json(state), digest, scope, generation, snap["epoch"], snap["state_sha256"]))
        _need(cur.rowcount == 1, "S1_CAS_WRITE_LOST")
        db.execute("UPDATE xeno_coordinator_leases SET bound_epoch=?,bound_state_sha256=? WHERE lease_id=?", (epoch, digest, coordinator_lease_id))
        db.commit()
    except Exception:
        db.rollback(); raise
    return {"schema": COMMIT_SCHEMA, "scope": scope, "generation": generation, "epoch": epoch,
            "state_sha256": digest, "coordinator_node_id": coordinator_node_id,
            "coordinator_lease_id": coordinator_lease_id, "authority": "S1_ONLY_NOT_S0_TRUTH_EFFECT_SECURITY"}
