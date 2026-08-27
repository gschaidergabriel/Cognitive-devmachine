#!/usr/bin/env python3
"""Physical GRID10 S1 fabric: real multi-process SQLite/WAL shared cognitive workspace.

Adapts the single-process protocol proven in
tools/xeno_self_organizing_fabric_acceptance_v1.py (E1-E9, LOCAL_DETERMINISTIC_FABRIC_COMPONENT)
to genuine cross-process concurrency: multiple independent OS processes open the SAME
sqlite file concurrently (WAL mode, busy_timeout, BEGIN IMMEDIATE for writers).

Authority law (unchanged from the deterministic reference):
- ordinary Xeno nodes never write S1directly; they may only emit ephemeral NODE_RESULT/v1
  and submit it to a currently-leased coordinator process (which itself still goes through
  the same CAS-checked coordinator_commit path -- no shortcut).
- coordinator S1 write authority is temporary, scoped, epoch-bound, generation-bound and
  revocable; a lease can be revoked immediately (checked on every commit, not on a timer).
- coordinator writes never mint S0/canonical truth or trigger real external effects.
- this module owns its own sandboxed sqlite file; it is never pointed at Zero's live
  production EntityOS/ClayVerse S1 (eos-*, clayverse-* systemd services are untouched).
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "GRID10_PHYSICAL_FABRIC/v1"
RESULT_SCHEMA = "NODE_RESULT/v1"
SUMMARY_SCHEMA = "COORDINATOR_SUMMARY/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v2"
LEASE_TTL_SECONDS = 8.0


class FabricError(ValueError):
    pass


def cj(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dg(v: Any) -> str:
    return hashlib.sha256(cj(v).encode()).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    epoch: int
    generation: int
    state_digest: str
    tasks: tuple[dict[str, Any], ...]
    scopes: tuple[dict[str, Any], ...]
    leases: tuple[dict[str, Any], ...]
    nodes: tuple[dict[str, Any], ...]


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS nodes(
          node_id TEXT PRIMARY KEY,
          capability TEXT NOT NULL,
          healthy INTEGER NOT NULL,
          pid INTEGER NOT NULL,
          joined_epoch INTEGER NOT NULL,
          last_seen_ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks(
          task_id TEXT PRIMARY KEY,
          scope TEXT NOT NULL,
          priority INTEGER NOT NULL,
          capability TEXT NOT NULL,
          status TEXT NOT NULL,
          claimed_by TEXT,
          payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scopes(
          scope TEXT PRIMARY KEY,
          summary_json TEXT NOT NULL,
          evidence_count INTEGER NOT NULL,
          last_writer_lease_id TEXT,
          last_result_digest TEXT,
          state_epoch INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS leases(
          lease_id TEXT PRIMARY KEY,
          node_id TEXT NOT NULL,
          scope TEXT NOT NULL,
          generation INTEGER NOT NULL,
          token_digest TEXT NOT NULL,
          granted_epoch INTEGER NOT NULL,
          granted_ts REAL NOT NULL,
          valid INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admitted_results(
          result_digest TEXT PRIMARY KEY,
          source_node_id TEXT NOT NULL,
          coordinator_lease_id TEXT NOT NULL,
          scope TEXT NOT NULL,
          admitted_epoch INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS s0_effect_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          actor TEXT NOT NULL,
          attempted_write TEXT NOT NULL,
          rejected INTEGER NOT NULL,
          ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS outbox(
          packet_digest TEXT PRIMARY KEY,
          scope TEXT NOT NULL,
          packet_json TEXT NOT NULL,
          consumed INTEGER NOT NULL DEFAULT 0,
          submitted_ts REAL NOT NULL
        );
        """
    )
    if con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone() is None:
        con.execute("INSERT INTO meta VALUES('epoch','1')")
    if con.execute("SELECT v FROM meta WHERE k='generation'").fetchone() is None:
        con.execute("INSERT INTO meta VALUES('generation','1')")


class Fabric:
    """Thin wrapper: every mutating call opens its own short-lived connection so that
    real OS-level file locking / WAL concurrency is exercised across processes (no
    single long-lived connection held by one process pretending to be many)."""

    def __init__(self, path: Path):
        self.path = path
        con = connect(path)
        try:
            init_schema(con)
        finally:
            con.close()

    def _int(self, con: sqlite3.Connection, k: str) -> int:
        r = con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        if r is None:
            raise FabricError(f"MISSING_META:{k}")
        return int(r["v"])

    def _bump(self, con: sqlite3.Connection) -> int:
        e = self._int(con, "epoch") + 1
        con.execute("UPDATE meta SET v=? WHERE k='epoch'", (str(e),))
        return e

    # ---- runtime/deterministic membership (fabric authority, not model cognition) ----
    def runtime_join(self, node_id: str, capability: str, pid: int) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            epoch = self._int(con, "epoch")
            con.execute(
                "INSERT OR REPLACE INTO nodes VALUES(?,?,1,?,?,?)",
                (node_id, capability, pid, epoch, time.time()),
            )
            self._bump(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def runtime_heartbeat(self, node_id: str, healthy: bool = True) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "UPDATE nodes SET healthy=?,last_seen_ts=? WHERE node_id=?",
                (1 if healthy else 0, time.time(), node_id),
            )
            self._bump(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def seed_scope(self, scope: str) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            epoch = self._int(con, "epoch")
            con.execute(
                "INSERT OR REPLACE INTO scopes VALUES(?,?,?,?,?,?)",
                (scope, cj({"status": "open"}), 0, None, None, epoch),
            )
            self._bump(con)
            con.execute("COMMIT")
        finally:
            con.close()

    def seed_task(self, task_id: str, scope: str, priority: int, capability: str, payload: Any) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT OR REPLACE INTO tasks VALUES(?,?,?,?,?,?,?)",
                (task_id, scope, priority, capability, "OPEN", None, cj(payload)),
            )
            self._bump(con)
            con.execute("COMMIT")
        finally:
            con.close()

    def snapshot(self) -> Snapshot:
        con = connect(self.path)
        try:
            epoch = self._int(con, "epoch")
            generation = self._int(con, "generation")
            tasks = tuple(dict(r) for r in con.execute("SELECT * FROM tasks ORDER BY task_id"))
            scopes = tuple(dict(r) for r in con.execute("SELECT * FROM scopes ORDER BY scope"))
            leases = tuple(
                dict(r)
                for r in con.execute(
                    "SELECT lease_id,node_id,scope,generation,granted_epoch,granted_ts,valid FROM leases ORDER BY lease_id"
                )
            )
            nodes = tuple(dict(r) for r in con.execute("SELECT node_id,capability,healthy FROM nodes ORDER BY node_id"))
            state_digest = dg({"epoch": epoch, "generation": generation, "tasks": tasks, "scopes": scopes, "leases": leases})
            return Snapshot(epoch, generation, state_digest, tasks, scopes, leases, nodes)
        finally:
            con.close()

    def runtime_claim_task(self, task_id: str, node_id: str, *, expected_epoch: int) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            if self._int(con, "epoch") != expected_epoch:
                raise FabricError("TASK_CLAIM_CAS_FAILED")
            row = con.execute("SELECT status,claimed_by FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None or row["status"] != "OPEN" or row["claimed_by"] is not None:
                raise FabricError("TASK_NOT_CLAIMABLE")
            con.execute("UPDATE tasks SET status='CLAIMED',claimed_by=? WHERE task_id=?", (node_id, task_id))
            self._bump(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def runtime_reclaim_stale_claims(self, reclaiming_node_id: str, *, stale_after_seconds: float = 15.0) -> list[str]:
        """Found empirically 2026-08-27 (GRID10 use-case-1 research): a task claimed
        via runtime_claim_task() but never completed (the claiming node died or
        stalled before ever calling emit_node_result()) is stuck FOREVER -- no code
        path anywhere previously reset status='CLAIMED' back to 'OPEN'. This directly
        contradicts the assumed 'a crashed node never causes lost/stuck work' property
        for ordinary (non-coordinator) task claims -- coordinator LEASES already had a
        TTL+renewal story (see grid10_node.py's COORDINATOR_LEASE_SELF_RENEW_AFTER_EXPIRY
        fix), but plain task claims had no equivalent at all until this method.

        A task is eligible for reclaim only if BOTH:
        (a) its status is 'CLAIMED' AND its claiming node is either not present in the
            `nodes` table at all, OR present with healthy=0, OR present with
            healthy=1 but a last_seen_ts older than `stale_after_seconds` -- a hard
            SIGKILL never gets a chance to call runtime_heartbeat(healthy=False), so a
            stale last_seen_ts on an otherwise 'healthy=1' row is the ONLY real signal
            for that specific, realistic failure mode.
        (b) no packet in `outbox` currently references this task_id in its decoded
            payload (payload.task_id) -- if a result was already emitted and is only
            waiting for a coordinator to drain it, reclaiming would be wrong (duplicate
            work, and a race against the coordinator committing the real result).

        Runs as a single connect()+BEGIN IMMEDIATE transaction (read tasks+nodes+
        outbox, decide, write) so this is race-safe against another node running the
        same reclaim scan concurrently, matching every other mutating method here.
        Returns the list of task_ids that were reclaimed (empty list if none)."""
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            now = time.time()
            claimed_rows = con.execute(
                "SELECT task_id, claimed_by FROM tasks WHERE status='CLAIMED' AND claimed_by IS NOT NULL"
            ).fetchall()
            if not claimed_rows:
                con.execute("COMMIT")
                return []

            node_status: dict[str, sqlite3.Row] = {
                r["node_id"]: r for r in con.execute("SELECT node_id, healthy, last_seen_ts FROM nodes")
            }
            pending_task_ids: set[str] = set()
            for r in con.execute("SELECT packet_json FROM outbox WHERE consumed=0"):
                try:
                    payload = json.loads(r["packet_json"]).get("payload") or {}
                    tid = payload.get("task_id")
                    if tid:
                        pending_task_ids.add(tid)
                except (ValueError, TypeError):
                    continue

            reclaimed: list[str] = []
            for row in claimed_rows:
                task_id, claimer = row["task_id"], row["claimed_by"]
                if task_id in pending_task_ids:
                    continue  # result already in flight -- do not race the coordinator
                node = node_status.get(claimer)
                is_stale = (
                    node is None
                    or int(node["healthy"]) == 0
                    or (now - float(node["last_seen_ts"])) > stale_after_seconds
                )
                if is_stale:
                    reclaimed.append(task_id)

            if reclaimed:
                con.executemany(
                    "UPDATE tasks SET status='OPEN', claimed_by=NULL WHERE task_id=?",
                    [(tid,) for tid in reclaimed],
                )
                self._bump(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()
        return reclaimed

    # ---- Result Channel: ordinary nodes may ALWAYS write here (this is the explicit
    # "NODE_RESULT to Result-Channel" path, distinct from S1 canonical `scopes` state,
    # which stays commit-gated to a leased coordinator below). ----
    def emit_node_result(self, packet: dict[str, Any]) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT OR IGNORE INTO outbox(packet_digest,scope,packet_json,consumed,submitted_ts) VALUES(?,?,?,0,?)",
                (packet["packet_digest"], packet["scope"], cj(packet), time.time()),
            )
            con.execute("COMMIT")
        finally:
            con.close()

    def outbox_pending_scopes(self) -> list[str]:
        con = connect(self.path)
        try:
            rows = con.execute("SELECT DISTINCT scope FROM outbox WHERE consumed=0").fetchall()
            return [r["scope"] for r in rows]
        finally:
            con.close()

    def coordinator_drain_and_commit(
        self, scope: str, lease: dict[str, Any], token: str
    ) -> list[dict[str, Any]]:
        """Coordinator reads pending Result-Channel packets for its scope and folds each
        into canonical S1 via the same CAS-checked coordinator_commit path used for
        directly-passed packets -- no shortcut for the drain path."""
        con = connect(self.path)
        try:
            rows = con.execute(
                "SELECT packet_digest,packet_json FROM outbox WHERE scope=? AND consumed=0 ORDER BY submitted_ts",
                (scope,),
            ).fetchall()
        finally:
            con.close()
        committed = []
        for row in rows:
            packet = json.loads(row["packet_json"])
            snap = self.snapshot()
            try:
                delta = self.coordinator_commit(
                    lease=lease, token=token, packet=packet, expected_epoch=snap.epoch, expected_digest=snap.state_digest
                )
            except FabricError as exc:
                committed.append({"packet_digest": row["packet_digest"], "commit_error": str(exc)})
                continue
            con2 = connect(self.path)
            try:
                con2.execute("BEGIN IMMEDIATE")
                con2.execute("UPDATE outbox SET consumed=1 WHERE packet_digest=?", (row["packet_digest"],))
                con2.execute("COMMIT")
            finally:
                con2.close()
            committed.append({"packet_digest": row["packet_digest"], **delta})
        return committed

    def ordinary_write_attempt(self, actor: str, *_: Any, **__: Any) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO s0_effect_log(actor,attempted_write,rejected,ts) VALUES(?,?,1,?)",
                (actor, "ORDINARY_S1_WRITE_ATTEMPT", time.time()),
            )
            con.execute("COMMIT")
        finally:
            con.close()
        raise FabricError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")

    def elect_coordinator(self, scope: str, candidate_node_ids: list[str]) -> tuple[dict[str, Any], str] | None:
        """Deterministic election among candidates; returns None if scope already has a
        valid, non-expired lease (caller should treat that as 'someone else is
        coordinator, back off').

        Real gap found+fixed 2026-08-27 (GRID10 use-case-2 edge-resilience
        experiment): this method previously only checked `valid=1`, never whether an
        existing lease had actually expired via LEASE_TTL_SECONDS. coordinator_commit()
        already enforces the TTL for COMMITS, and grid10_node.py's own coordinator
        self-detects and revokes its OWN expired lease on a failed commit -- but neither
        of those helps when the coordinator process is outright KILLED (not just left
        idle past its TTL while still alive): a dead coordinator's lease stayed
        `valid=1` in the DB forever, and this method's old check meant NO OTHER node
        could ever be elected for that scope again. Confirmed empirically: a mass
        SIGKILL that happened to include an active coordinator left that scope's
        remaining tasks permanently stuck past a 40s recovery bound. Fix: treat a
        TTL-expired lease as equivalent to invalid for election purposes too, and
        explicitly revoke it here before proceeding (symmetric with the commit-time
        check, same LEASE_TTL_SECONDS constant, same race-safety since this all runs
        inside the same BEGIN IMMEDIATE transaction as the rest of this method)."""
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            old = con.execute(
                "SELECT lease_id, granted_ts FROM leases WHERE scope=? AND valid=1", (scope,)
            ).fetchone()
            if old is not None:
                if (time.time() - float(old["granted_ts"])) > LEASE_TTL_SECONDS:
                    con.execute("UPDATE leases SET valid=0 WHERE lease_id=?", (old["lease_id"],))
                    old = None
                else:
                    con.execute("ROLLBACK")
                    return None
            epoch = self._int(con, "epoch")
            generation = self._int(con, "generation")
            healthy_rows = con.execute(
                "SELECT node_id FROM nodes WHERE healthy=1 AND node_id IN ({})".format(
                    ",".join("?" * len(candidate_node_ids))
                ),
                candidate_node_ids,
            ).fetchall() if candidate_node_ids else []
            if not healthy_rows:
                con.execute("ROLLBACK")
                raise FabricError("NO_HEALTHY_COORDINATOR_CANDIDATE")
            ranked = sorted(
                (dg({"scope": scope, "epoch": epoch, "generation": generation, "node_id": r["node_id"]}), r["node_id"])
                for r in healthy_rows
            )
            node_id = ranked[0][1]
            token = dg({"scope": scope, "node_id": node_id, "epoch": epoch, "generation": generation})
            lease_id = "lease-" + dg(token)[:24]
            con.execute(
                "INSERT INTO leases VALUES(?,?,?,?,?,?,?,1)",
                (lease_id, node_id, scope, generation, dg(token), epoch, time.time()),
            )
            self._bump(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()
        return (
            {
                "schema": LEASE_SCHEMA,
                "lease_id": lease_id,
                "node_id": node_id,
                "scope": scope,
                "generation": generation,
                "granted_epoch": epoch,
            },
            token,
        )

    def revoke_lease(self, lease_id: str) -> None:
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute("UPDATE leases SET valid=0 WHERE lease_id=?", (lease_id,))
            self._bump(con)
            con.execute("COMMIT")
        finally:
            con.close()

    def coordinator_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packet: dict[str, Any],
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        scope = str(packet.get("scope"))
        con = connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            lrow = con.execute("SELECT * FROM leases WHERE lease_id=?", (lease.get("lease_id"),)).fetchone()
            if lrow is None or int(lrow["valid"]) != 1:
                raise FabricError("COORDINATOR_LEASE_INVALID")
            if lrow["node_id"] != lease.get("node_id") or lrow["token_digest"] != dg(token):
                raise FabricError("COORDINATOR_LEASE_BINDING_INVALID")
            if lrow["scope"] != scope:
                raise FabricError("COORDINATOR_SCOPE_VIOLATION")
            if int(lrow["generation"]) != self._int(con, "generation"):
                raise FabricError("COORDINATOR_LEASE_STALE_GENERATION")
            if (time.time() - float(lrow["granted_ts"])) > LEASE_TTL_SECONDS:
                raise FabricError("COORDINATOR_LEASE_EXPIRED")

            current_epoch = self._int(con, "epoch")
            current_generation = self._int(con, "generation")
            if expected_epoch != current_epoch:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            if packet.get("generation") != current_generation:
                raise FabricError("RESULT_STALE_GENERATION")
            if packet.get("state_epoch", -1) > current_epoch:
                raise FabricError("RESULT_FUTURE_EPOCH")

            schema = packet.get("schema")
            if schema not in (RESULT_SCHEMA, SUMMARY_SCHEMA):
                raise FabricError("PACKET_SCHEMA_INVALID")
            if schema == RESULT_SCHEMA and packet.get("source_kind") != "ORDINARY_NODE":
                raise FabricError("ORDINARY_RESULT_SOURCE_KIND_INVALID")
            if schema == SUMMARY_SCHEMA and packet.get("source_kind") != "COORDINATOR":
                raise FabricError("COORDINATOR_SUMMARY_SOURCE_KIND_INVALID")

            core = {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}
            if packet.get("packet_digest") != dg(core):
                raise FabricError("PACKET_DIGEST_MISMATCH")
            if packet.get("s1_write_intent") is not False:
                raise FabricError("SOURCE_PACKET_MUST_NOT_SELF_WRITE")
            if con.execute(
                "SELECT 1 FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)
            ).fetchone():
                raise FabricError("DUPLICATE_RESULT_REJECTED")

            row = con.execute("SELECT * FROM scopes WHERE scope=?", (scope,)).fetchone()
            if row is None:
                raise FabricError("UNKNOWN_SCOPE")
            merged = {"previous": json.loads(row["summary_json"]), "latest": packet["payload"], "source_schema": schema}
            new_epoch = current_epoch + 1
            con.execute(
                "UPDATE scopes SET summary_json=?,evidence_count=evidence_count+1,last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE scope=?",
                (cj(merged), lease["lease_id"], packet["packet_digest"], new_epoch, scope),
            )
            con.execute(
                "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                (packet["packet_digest"], packet["source_node_id"], lease["lease_id"], scope, new_epoch),
            )
            con.execute("UPDATE meta SET v=? WHERE k='epoch'", (str(new_epoch),))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()
        return {
            "scope": scope,
            "prior_epoch": expected_epoch,
            "new_epoch": new_epoch,
            "coordinator_lease_id": lease["lease_id"],
            "canonical_truth": False,
            "effect_authority": False,
        }


def result_packet(node_id: str, snap: Snapshot, scope: str, payload: Any) -> dict[str, Any]:
    core = {
        "schema": RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node_id,
        "scope": scope,
        "generation": snap.generation,
        "state_epoch": snap.epoch,
        "state_digest": snap.state_digest,
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def summary_packet(node_id: str, snap: Snapshot, scope: str, payload: Any) -> dict[str, Any]:
    core = {
        "schema": SUMMARY_SCHEMA,
        "source_kind": "COORDINATOR",
        "source_node_id": node_id,
        "scope": scope,
        "generation": snap.generation,
        "state_epoch": snap.epoch,
        "state_digest": snap.state_digest,
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}
