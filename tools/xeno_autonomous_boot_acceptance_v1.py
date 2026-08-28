#!/usr/bin/env python3
"""Executable acceptance harness for the current Xeno/HCU GO target.

Scope: AUTONOMOUS_BOOT component only.

Tests A1-A8 establish that a newly connected Xeno can reconstruct shared state,
select useful unclaimed work without a preassigned cognitive role, replan on state
change, idle safely, reject stale state, rejoin after restart, remain role-flexible,
and never gain S1 write authority merely by model self-declaration.

This harness is deterministic and local. It does not call a model/provider/network.
A PASS is component evidence only, not physical GRID10/HCU acceptance.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "XENO_AUTONOMOUS_BOOT_ACCEPTANCE/v1"
SELECTION_SCHEMA = "XENO_WORK_SELECTION/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"


class BootError(ValueError):
    pass


def cj(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dg(v: Any) -> str:
    return hashlib.sha256(cj(v).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    epoch: int
    state_digest: str
    generation: int
    tasks: tuple[dict[str, Any], ...]
    leases: tuple[dict[str, Any], ...]


class SharedState:
    """Deterministic S1 fixture with runtime-enforced writer capability.

    Ordinary nodes receive only read_snapshot(). Mutation requires a valid runtime
    lease token and is intentionally unavailable through the ordinary-node API.
    """

    def __init__(self, path: Path):
        self.con = sqlite3.connect(path, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE tasks(
              task_id TEXT PRIMARY KEY,
              priority INTEGER NOT NULL,
              required_capability TEXT NOT NULL,
              status TEXT NOT NULL,
              claimed_by TEXT,
              payload_digest TEXT NOT NULL
            );
            CREATE TABLE coordinator_leases(
              lease_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              scope TEXT NOT NULL,
              state_epoch_start INTEGER NOT NULL,
              generation INTEGER NOT NULL,
              lease_token_digest TEXT NOT NULL,
              valid INTEGER NOT NULL
            );
            """
        )
        self._set_meta("epoch", "1")
        self._set_meta("generation", "1")

    def close(self) -> None:
        self.con.close()

    def _set_meta(self, k: str, v: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))

    def _meta_int(self, k: str) -> int:
        r = self.con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        if r is None:
            raise BootError(f"MISSING_META:{k}")
        return int(r["v"])

    def seed_task(self, task_id: str, priority: int, capability: str, payload: Any) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO tasks VALUES(?,?,?,?,?,?)",
            (task_id, priority, capability, "OPEN", None, dg(payload)),
        )

    def set_claim(self, task_id: str, node_id: str | None) -> None:
        status = "CLAIMED" if node_id else "OPEN"
        self.con.execute(
            "UPDATE tasks SET status=?, claimed_by=? WHERE task_id=?",
            (status, node_id, task_id),
        )
        self.bump_epoch()

    def complete(self, task_id: str) -> None:
        self.con.execute("UPDATE tasks SET status='DONE' WHERE task_id=?", (task_id,))
        self.bump_epoch()

    def bump_epoch(self) -> int:
        e = self._meta_int("epoch") + 1
        self._set_meta("epoch", str(e))
        return e

    def read_snapshot(self) -> Snapshot:
        epoch = self._meta_int("epoch")
        generation = self._meta_int("generation")
        tasks = tuple(dict(r) for r in self.con.execute("SELECT * FROM tasks ORDER BY task_id"))
        leases = tuple(
            dict(r)
            for r in self.con.execute(
                "SELECT lease_id,node_id,scope,state_epoch_start,generation,valid FROM coordinator_leases ORDER BY lease_id"
            )
        )
        state_digest = dg(
            {"epoch": epoch, "generation": generation, "tasks": tasks, "leases": leases}
        )
        return Snapshot(epoch, state_digest, generation, tasks, leases)

    def grant_lease(self, node_id: str, scope: str) -> tuple[dict[str, Any], str]:
        snap = self.read_snapshot()
        token = dg({"node": node_id, "scope": scope, "epoch": snap.epoch, "generation": snap.generation})
        lease_id = "lease-" + token[:20]
        self.con.execute(
            "INSERT OR REPLACE INTO coordinator_leases VALUES(?,?,?,?,?,?,1)",
            (lease_id, node_id, scope, snap.epoch, snap.generation, dg(token)),
        )
        self.bump_epoch()
        lease = {
            "schema": LEASE_SCHEMA,
            "lease_id": lease_id,
            "node_id": node_id,
            "scope": scope,
            "state_epoch_start": snap.epoch,
            "generation": snap.generation,
        }
        return lease, token

    def coordinator_write(self, node_id: str, lease: dict[str, Any] | None, token: str | None, op: str) -> None:
        if not lease or lease.get("schema") != LEASE_SCHEMA or not token:
            raise BootError("S1_WRITE_REQUIRES_VALID_COORDINATOR_LEASE")
        r = self.con.execute(
            "SELECT * FROM coordinator_leases WHERE lease_id=?", (lease.get("lease_id"),)
        ).fetchone()
        if r is None or not int(r["valid"]):
            raise BootError("COORDINATOR_LEASE_INVALID")
        if r["node_id"] != node_id or r["lease_token_digest"] != dg(token):
            raise BootError("COORDINATOR_LEASE_BINDING_INVALID")
        if int(r["generation"]) != self._meta_int("generation"):
            raise BootError("COORDINATOR_LEASE_STALE_GENERATION")
        # Fixture mutation proving authority path; no S0/canonical truth is touched.
        self._set_meta("last_s1_op", op)
        self.bump_epoch()


class XenoNode:
    def __init__(self, node_id: str, capabilities: Iterable[str]):
        self.node_id = node_id
        self.capabilities = frozenset(capabilities)
        self.last_seen_epoch: int | None = None
        self.last_seen_digest: str | None = None
        self.selected_task: str | None = None
        self.role = "ORDINARY"

    def boot_and_select(self, snap: Snapshot) -> dict[str, Any]:
        if self.last_seen_epoch is not None and snap.epoch < self.last_seen_epoch:
            raise BootError("STALE_SHARED_STATE_EPOCH_REJECTED")
        if self.last_seen_epoch == snap.epoch and self.last_seen_digest not in (None, snap.state_digest):
            raise BootError("SAME_EPOCH_DIGEST_CONFLICT")

        eligible = [
            t for t in snap.tasks
            if t["status"] == "OPEN" and t["claimed_by"] is None and t["required_capability"] in self.capabilities
        ]
        eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
        chosen = eligible[0]["task_id"] if eligible else None

        self.last_seen_epoch = snap.epoch
        self.last_seen_digest = snap.state_digest
        self.selected_task = chosen
        self.role = "ORDINARY"
        return {
            "schema": SELECTION_SCHEMA,
            "node_id": self.node_id,
            "state_epoch": snap.epoch,
            "state_digest": snap.state_digest,
            "generation": snap.generation,
            "selected_task_id": chosen,
            "action": "WORK" if chosen else "IDLE",
            "role": self.role,
            "s1_write_intent": False,
        }

    def accept_coordinator_lease(self, lease: dict[str, Any], snap: Snapshot) -> None:
        if lease.get("schema") != LEASE_SCHEMA or lease.get("node_id") != self.node_id:
            raise BootError("LEASE_NOT_BOUND_TO_NODE")
        if int(lease.get("generation", -1)) != snap.generation:
            raise BootError("LEASE_STALE_GENERATION")
        self.role = "COORDINATOR"


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise BootError(msg)


def run(path: Path) -> dict[str, Any]:
    s = SharedState(path)
    tests: dict[str, dict[str, Any]] = {}
    try:
        s.seed_task("t-low", 10, "reason", {"job": "low"})
        s.seed_task("t-high", 90, "reason", {"job": "high"})
        s.seed_task("t-code", 80, "code", {"job": "code"})

        # A1 autonomous join + useful work selection from shared state.
        n = XenoNode("x1", ["reason"])
        sel = n.boot_and_select(s.read_snapshot())
        assert_true(sel["selected_task_id"] == "t-high", "A1_DID_NOT_SELECT_HIGHEST_PRIORITY_NEEDED_WORK")
        tests["A1_AUTONOMOUS_JOIN_SELECT"] = {"pass": True, "selection": sel}

        # A2 claim-awareness: already claimed work is not duplicated.
        s.set_claim("t-high", "x-other")
        sel2 = n.boot_and_select(s.read_snapshot())
        assert_true(sel2["selected_task_id"] == "t-low", "A2_CLAIMED_WORK_NOT_AVOIDED")
        tests["A2_CLAIM_AWARENESS"] = {"pass": True, "selection": sel2}

        # A3 replan when shared state changes.
        s.complete("t-low")
        s.set_claim("t-high", None)
        sel3 = n.boot_and_select(s.read_snapshot())
        assert_true(sel3["selected_task_id"] == "t-high", "A3_STATE_CHANGE_DID_NOT_REPLAN")
        tests["A3_REPLAN_ON_STATE_CHANGE"] = {"pass": True, "selection": sel3}

        # A4 safe idle when no matching useful work exists.
        s.set_claim("t-high", "x-other")
        idle = n.boot_and_select(s.read_snapshot())
        assert_true(idle["action"] == "IDLE" and idle["selected_task_id"] is None, "A4_IDLE_FAILED")
        tests["A4_SAFE_IDLE"] = {"pass": True, "selection": idle}

        # A5 reject stale epoch after observing a newer state.
        fresh = s.read_snapshot()
        n.boot_and_select(fresh)
        stale = Snapshot(fresh.epoch - 1, fresh.state_digest, fresh.generation, fresh.tasks, fresh.leases)
        rejected = False
        try:
            n.boot_and_select(stale)
        except BootError as e:
            rejected = str(e) == "STALE_SHARED_STATE_EPOCH_REJECTED"
        assert_true(rejected, "A5_STALE_EPOCH_NOT_REJECTED")
        tests["A5_STALE_EPOCH_REJECTION"] = {"pass": True}

        # A6 restart/rejoin: fresh process reconstructs from S1, no local-role dependency.
        restarted = XenoNode("x1", ["reason"])
        rejoin = restarted.boot_and_select(s.read_snapshot())
        assert_true(rejoin["state_epoch"] == s.read_snapshot().epoch, "A6_REJOIN_EPOCH_MISMATCH")
        assert_true(rejoin["role"] == "ORDINARY", "A6_REJOIN_FIXED_ROLE_LEAK")
        tests["A6_RESTART_REJOIN"] = {"pass": True, "selection": rejoin}

        # A7 role flexibility: same node becomes coordinator only via a bound runtime lease.
        lease, token = s.grant_lease("x1", "branch:alpha")
        restarted.accept_coordinator_lease(lease, s.read_snapshot())
        assert_true(restarted.role == "COORDINATOR", "A7_VALID_LEASE_DID_NOT_CHANGE_ROLE")
        tests["A7_ROLE_FLEXIBILITY"] = {"pass": True, "lease_id": lease["lease_id"]}

        # A8 ordinary/self-declared coordinator cannot write; valid lease can.
        ordinary = XenoNode("x2", ["reason"])
        blocked_no_lease = False
        try:
            s.coordinator_write("x2", None, None, "self-declared-coordinator")
        except BootError as e:
            blocked_no_lease = str(e) == "S1_WRITE_REQUIRES_VALID_COORDINATOR_LEASE"
        assert_true(blocked_no_lease, "A8_ORDINARY_NODE_GAINED_S1_WRITE")
        s.coordinator_write("x1", lease, token, "accepted-coordinator-fixture-write")
        tests["A8_COORDINATOR_AUTHORITY_BOUNDARY"] = {
            "pass": True,
            "ordinary_write_rejected": True,
            "valid_lease_write_accepted": True,
        }

        final_snap = s.read_snapshot()
        return {
            "schema": SCHEMA,
            "pass": all(v.get("pass") is True for v in tests.values()),
            "tests": tests,
            "final_state_epoch": final_snap.epoch,
            "final_state_digest": final_snap.state_digest,
            "credit_scope": "AUTONOMOUS_BOOT_COMPONENT_ONLY_NOT_PHYSICAL_GRID10_OR_WHOLE_HCU",
            "next_frontier": "NODE_RESULT_TRANSPORT_AND_DYNAMIC_COORDINATOR_LEASE_RUNTIME_INTEGRATION",
        }
    finally:
        s.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        print(json.dumps(run(Path(td) / "xeno_boot.sqlite"), indent=2, sort_keys=True))
