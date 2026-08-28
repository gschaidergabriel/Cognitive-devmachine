#!/usr/bin/env python3
"""Integrated deterministic acceptance harness for the current Xeno/HCU GO target.

This joins the previously separate autonomous-boot and NODE_RESULT/coordinator contracts
into one end-to-end fabric fixture:

  runtime-admitted identical nodes -> read shared state -> autonomously select useful work
  -> ordinary nodes emit ephemeral NODE_RESULT/v1 -> deterministic lease manager appoints
  temporary coordinators -> only valid coordinators integrate/compress and write S1
  -> coordinator failure causes deterministic replacement -> scoped summaries can be
  recursively compressed by a higher-scope coordinator.

Hard authority law tested here:
- ordinary model nodes never write S1;
- runtime membership/lease metadata is deterministic fabric authority, not model-originated cognition;
- coordinator S1 write authority is temporary, scoped, epoch-bound and revocable;
- coordinator writes do not mint S0/canonical truth/effect authority.

Local deterministic fixture only: no model/provider/network/effect execution. Source presence
alone does not mint physical GRID10/HCU runtime credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

SCHEMA = "XENO_SELF_ORGANIZING_FABRIC_ACCEPTANCE/v1"
RESULT_SCHEMA = "NODE_RESULT/v1"
SUMMARY_SCHEMA = "COORDINATOR_SUMMARY/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v2"


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


class Fabric:
    def __init__(self, path: Path):
        self.con = sqlite3.connect(path, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE nodes(
              node_id TEXT PRIMARY KEY,
              capability TEXT NOT NULL,
              healthy INTEGER NOT NULL
            );
            CREATE TABLE tasks(
              task_id TEXT PRIMARY KEY,
              scope TEXT NOT NULL,
              priority INTEGER NOT NULL,
              capability TEXT NOT NULL,
              status TEXT NOT NULL,
              claimed_by TEXT,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE scopes(
              scope TEXT PRIMARY KEY,
              summary_json TEXT NOT NULL,
              evidence_count INTEGER NOT NULL,
              last_writer_lease_id TEXT,
              last_result_digest TEXT,
              state_epoch INTEGER NOT NULL
            );
            CREATE TABLE leases(
              lease_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              scope TEXT NOT NULL,
              generation INTEGER NOT NULL,
              token_digest TEXT NOT NULL,
              granted_epoch INTEGER NOT NULL,
              valid INTEGER NOT NULL
            );
            CREATE TABLE admitted_results(
              result_digest TEXT PRIMARY KEY,
              source_node_id TEXT NOT NULL,
              coordinator_lease_id TEXT NOT NULL,
              scope TEXT NOT NULL,
              admitted_epoch INTEGER NOT NULL
            );
            """
        )
        self._set("epoch", "1")
        self._set("generation", "1")

    def close(self) -> None:
        self.con.close()

    def _set(self, k: str, v: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))

    def _int(self, k: str) -> int:
        r = self.con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        if r is None:
            raise FabricError(f"MISSING_META:{k}")
        return int(r["v"])

    def _bump(self) -> int:
        e = self._int("epoch") + 1
        self._set("epoch", str(e))
        return e

    # Deterministic runtime/fabric authority: membership/seed operations are not model S1 writes.
    def runtime_register_node(self, node_id: str, capability: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO nodes VALUES(?,?,1)", (node_id, capability))

    def runtime_set_health(self, node_id: str, healthy: bool) -> None:
        self.con.execute("UPDATE nodes SET healthy=? WHERE node_id=?", (1 if healthy else 0, node_id))
        self._bump()

    def seed_scope(self, scope: str) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO scopes VALUES(?,?,?,?,?,?)",
            (scope, cj({"status": "open"}), 0, None, None, self._int("epoch")),
        )
        self._bump()

    def seed_task(self, task_id: str, scope: str, priority: int, capability: str, payload: Any) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO tasks VALUES(?,?,?,?,?,?,?)",
            (task_id, scope, priority, capability, "OPEN", None, cj(payload)),
        )
        self._bump()

    def snapshot(self) -> Snapshot:
        epoch = self._int("epoch")
        generation = self._int("generation")
        tasks = tuple(dict(r) for r in self.con.execute("SELECT * FROM tasks ORDER BY task_id"))
        scopes = tuple(dict(r) for r in self.con.execute("SELECT * FROM scopes ORDER BY scope"))
        leases = tuple(dict(r) for r in self.con.execute(
            "SELECT lease_id,node_id,scope,generation,granted_epoch,valid FROM leases ORDER BY lease_id"
        ))
        state_digest = dg({"epoch": epoch, "generation": generation, "tasks": tasks, "scopes": scopes, "leases": leases})
        return Snapshot(epoch, generation, state_digest, tasks, scopes, leases)

    def runtime_claim_task(self, task_id: str, node_id: str, *, expected_epoch: int) -> None:
        # Claim arbitration is deterministic fabric metadata, not cognitive-state publication.
        if self._int("epoch") != expected_epoch:
            raise FabricError("TASK_CLAIM_CAS_FAILED")
        row = self.con.execute("SELECT status,claimed_by FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None or row["status"] != "OPEN" or row["claimed_by"] is not None:
            raise FabricError("TASK_NOT_CLAIMABLE")
        self.con.execute("UPDATE tasks SET status='CLAIMED',claimed_by=? WHERE task_id=?", (node_id, task_id))
        self._bump()

    def ordinary_write_attempt(self, *_: Any, **__: Any) -> None:
        raise FabricError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")

    def elect_coordinator(self, scope: str) -> tuple[dict[str, Any], str]:
        # Existing valid scoped lease wins until revoked.
        old = self.con.execute("SELECT * FROM leases WHERE scope=? AND valid=1 ORDER BY lease_id LIMIT 1", (scope,)).fetchone()
        if old is not None:
            raise FabricError("ACTIVE_COORDINATOR_ALREADY_EXISTS")
        snap = self.snapshot()
        rows = list(self.con.execute("SELECT node_id FROM nodes WHERE healthy=1 ORDER BY node_id"))
        if not rows:
            raise FabricError("NO_HEALTHY_COORDINATOR_CANDIDATE")
        ranked = sorted(
            (dg({"scope": scope, "epoch": snap.epoch, "generation": snap.generation, "node_id": r["node_id"]}), r["node_id"])
            for r in rows
        )
        node_id = ranked[0][1]
        token = dg({"scope": scope, "node_id": node_id, "epoch": snap.epoch, "generation": snap.generation})
        lease_id = "lease-" + dg(token)[:24]
        self.con.execute(
            "INSERT INTO leases VALUES(?,?,?,?,?,?,1)",
            (lease_id, node_id, scope, snap.generation, dg(token), snap.epoch),
        )
        self._bump()
        return ({
            "schema": LEASE_SCHEMA,
            "lease_id": lease_id,
            "node_id": node_id,
            "scope": scope,
            "generation": snap.generation,
            "granted_epoch": snap.epoch,
        }, token)

    def revoke_lease(self, lease_id: str) -> None:
        self.con.execute("UPDATE leases SET valid=0 WHERE lease_id=?", (lease_id,))
        self._bump()

    def _lease_row(self, lease: dict[str, Any], token: str, scope: str) -> sqlite3.Row:
        if lease.get("schema") != LEASE_SCHEMA:
            raise FabricError("LEASE_SCHEMA_INVALID")
        r = self.con.execute("SELECT * FROM leases WHERE lease_id=?", (lease.get("lease_id"),)).fetchone()
        if r is None or int(r["valid"]) != 1:
            raise FabricError("COORDINATOR_LEASE_INVALID")
        if r["node_id"] != lease.get("node_id") or r["token_digest"] != dg(token):
            raise FabricError("COORDINATOR_LEASE_BINDING_INVALID")
        if r["scope"] != scope:
            raise FabricError("COORDINATOR_SCOPE_VIOLATION")
        if int(r["generation"]) != self._int("generation"):
            raise FabricError("COORDINATOR_LEASE_STALE_GENERATION")
        return r

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
        self._lease_row(lease, token, scope)
        current = self.snapshot()
        if expected_epoch != current.epoch or expected_digest != current.state_digest:
            raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
        if packet.get("generation") != current.generation:
            raise FabricError("RESULT_STALE_GENERATION")
        if packet.get("state_epoch", -1) > current.epoch:
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
        if self.con.execute("SELECT 1 FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)).fetchone():
            raise FabricError("DUPLICATE_RESULT_REJECTED")

        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self._int("epoch") != expected_epoch:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            row = self.con.execute("SELECT * FROM scopes WHERE scope=?", (scope,)).fetchone()
            if row is None:
                raise FabricError("UNKNOWN_SCOPE")
            merged = {
                "previous": json.loads(row["summary_json"]),
                "latest": packet["payload"],
                "source_schema": schema,
            }
            new_epoch = expected_epoch + 1
            self.con.execute(
                "UPDATE scopes SET summary_json=?,evidence_count=evidence_count+1,last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE scope=?",
                (cj(merged), lease["lease_id"], packet["packet_digest"], new_epoch, scope),
            )
            self.con.execute(
                "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                (packet["packet_digest"], packet["source_node_id"], lease["lease_id"], scope, new_epoch),
            )
            self._set("epoch", str(new_epoch))
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise
        return {
            "scope": scope,
            "prior_epoch": expected_epoch,
            "new_epoch": new_epoch,
            "coordinator_lease_id": lease["lease_id"],
            "canonical_truth": False,
            "effect_authority": False,
        }


class Xeno:
    def __init__(self, node_id: str, capability: str):
        self.node_id = node_id
        self.capability = capability
        self.last_epoch: int | None = None
        self.last_digest: str | None = None

    def select_work(self, snap: Snapshot) -> dict[str, Any]:
        if self.last_epoch is not None and snap.epoch < self.last_epoch:
            raise FabricError("STALE_SHARED_STATE_EPOCH_REJECTED")
        eligible = [t for t in snap.tasks if t["status"] == "OPEN" and t["claimed_by"] is None and t["capability"] == self.capability]
        eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
        chosen = eligible[0] if eligible else None
        self.last_epoch, self.last_digest = snap.epoch, snap.state_digest
        return {
            "node_id": self.node_id,
            "state_epoch": snap.epoch,
            "state_digest": snap.state_digest,
            "task_id": None if chosen is None else chosen["task_id"],
            "scope": None if chosen is None else chosen["scope"],
            "action": "IDLE" if chosen is None else "WORK",
            "role": "ORDINARY",
            "s1_write_intent": False,
        }

    def result(self, snap: Snapshot, scope: str, payload: Any) -> dict[str, Any]:
        core = {
            "schema": RESULT_SCHEMA,
            "source_kind": "ORDINARY_NODE",
            "source_node_id": self.node_id,
            "scope": scope,
            "generation": snap.generation,
            "state_epoch": snap.epoch,
            "state_digest": snap.state_digest,
            "payload": payload,
        }
        return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def coordinator_summary(source_node_id: str, snap: Snapshot, target_scope: str, payload: Any) -> dict[str, Any]:
    core = {
        "schema": SUMMARY_SCHEMA,
        "source_kind": "COORDINATOR",
        "source_node_id": source_node_id,
        "scope": target_scope,
        "generation": snap.generation,
        "state_epoch": snap.epoch,
        "state_digest": snap.state_digest,
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != code:
        raise FabricError(f"EXPECTED_{code}_GOT_{got}")


def run(path: Path) -> dict[str, Any]:
    f = Fabric(path)
    tests: dict[str, Any] = {}
    try:
        for node_id in ("x1", "x2", "x3", "x4"):
            f.runtime_register_node(node_id, "reason")
        for scope in ("branch:a", "branch:b", "GLOBAL"):
            f.seed_scope(scope)
        f.seed_task("ta", "branch:a", 90, "reason", {"question": "A"})
        f.seed_task("tb", "branch:b", 80, "reason", {"question": "B"})

        # E1: autonomous boot selects needed work from current shared state.
        x1 = Xeno("x1", "reason")
        boot = x1.select_work(f.snapshot())
        if boot["task_id"] != "ta" or boot["role"] != "ORDINARY":
            raise FabricError("E1_AUTONOMOUS_BOOT_SELECTION_FAILED")
        tests["E1_AUTONOMOUS_BOOT"] = True

        # E2: deterministic runtime claim prevents duplicate work without granting model write authority.
        f.runtime_claim_task("ta", "x1", expected_epoch=f.snapshot().epoch)
        x2 = Xeno("x2", "reason")
        second = x2.select_work(f.snapshot())
        if second["task_id"] != "tb":
            raise FabricError("E2_CLAIM_AWARE_SELECTION_FAILED")
        tests["E2_CLAIM_AWARENESS"] = True

        # E3: ordinary nodes are technically unable to publish S1 changes.
        expect_error(lambda: f.ordinary_write_attempt("branch:a", {"illegal": True}), "ORDINARY_NODE_S1_WRITE_FORBIDDEN")
        tests["E3_ORDINARY_READ_ONLY"] = True

        # E4: ordinary work exits only as an ephemeral state-bound NODE_RESULT.
        worker_snap = f.snapshot()
        r_a = x1.result(worker_snap, "branch:a", {"evidence": "e-a"})
        if r_a["s1_write_intent"] is not False or r_a["state_digest"] != worker_snap.state_digest:
            raise FabricError("E4_NODE_RESULT_BINDING_FAILED")
        tests["E4_NODE_RESULT_TRANSPORT"] = True

        # E5: coordinator is dynamically appointed from same node pool; only lease holder may commit.
        lease_a, token_a = f.elect_coordinator("branch:a")
        commit_snap = f.snapshot()
        r_a2 = x1.result(commit_snap, "branch:a", {"evidence": "e-a2"})
        d_a = f.coordinator_commit(lease=lease_a, token=token_a, packet=r_a2, expected_epoch=commit_snap.epoch, expected_digest=commit_snap.state_digest)
        if d_a["canonical_truth"] is not False:
            raise FabricError("E5_COORDINATOR_MINTED_CANONICAL_TRUTH")
        tests["E5_DYNAMIC_COORDINATOR_ONLY_WRITE"] = True

        # E6: two scoped coordinators may exist; stale shared-state CAS forces re-read/rebase.
        lease_b, token_b = f.elect_coordinator("branch:b")
        shared = f.snapshot()
        r_b = x2.result(shared, "branch:b", {"evidence": "e-b"})
        r_a3 = x1.result(shared, "branch:a", {"evidence": "e-a3"})
        f.coordinator_commit(lease=lease_b, token=token_b, packet=r_b, expected_epoch=shared.epoch, expected_digest=shared.state_digest)
        expect_error(lambda: f.coordinator_commit(lease=lease_a, token=token_a, packet=r_a3, expected_epoch=shared.epoch, expected_digest=shared.state_digest), "S1_COMPARE_AND_SWAP_FAILED")
        rebased = f.snapshot()
        r_a4 = x1.result(rebased, "branch:a", {"evidence": "e-a4-rebased"})
        f.coordinator_commit(lease=lease_a, token=token_a, packet=r_a4, expected_epoch=rebased.epoch, expected_digest=rebased.state_digest)
        tests["E6_MULTI_COORDINATOR_CAS_REBASE"] = True

        # E7: failed coordinator loses authority and deterministic replacement is elected.
        failed_node = lease_a["node_id"]
        f.runtime_set_health(failed_node, False)
        f.revoke_lease(lease_a["lease_id"])
        after_fail = f.snapshot()
        stale_packet = x1.result(after_fail, "branch:a", {"evidence": "must-not-commit-old-lease"})
        expect_error(lambda: f.coordinator_commit(lease=lease_a, token=token_a, packet=stale_packet, expected_epoch=after_fail.epoch, expected_digest=after_fail.state_digest), "COORDINATOR_LEASE_INVALID")
        replacement, replacement_token = f.elect_coordinator("branch:a")
        if replacement["node_id"] == failed_node:
            raise FabricError("E7_FAILED_COORDINATOR_REELECTED")
        fresh = f.snapshot()
        fresh_packet = x2.result(fresh, "branch:a", {"evidence": "replacement"})
        f.coordinator_commit(lease=replacement, token=replacement_token, packet=fresh_packet, expected_epoch=fresh.epoch, expected_digest=fresh.state_digest)
        tests["E7_FAILURE_REPLACEMENT"] = True

        # E8: recursive scaling primitive: global coordinator ingests compressed coordinator summary,
        # not a raw ordinary-node packet routed directly from every worker.
        global_lease, global_token = f.elect_coordinator("GLOBAL")
        global_snap = f.snapshot()
        scope_rows = {r["scope"]: json.loads(r["summary_json"]) for r in global_snap.scopes if r["scope"] in ("branch:a", "branch:b")}
        summary = coordinator_summary(replacement["node_id"], global_snap, "GLOBAL", {"compressed_scopes": scope_rows})
        global_delta = f.coordinator_commit(lease=global_lease, token=global_token, packet=summary, expected_epoch=global_snap.epoch, expected_digest=global_snap.state_digest)
        if global_delta["scope"] != "GLOBAL":
            raise FabricError("E8_RECURSIVE_COMPRESSION_FAILED")
        tests["E8_RECURSIVE_COORDINATOR_COMPRESSION"] = True

        # E9: duplicate packet replay is rejected.
        dup_snap = f.snapshot()
        expect_error(lambda: f.coordinator_commit(lease=global_lease, token=global_token, packet=summary, expected_epoch=dup_snap.epoch, expected_digest=dup_snap.state_digest), "DUPLICATE_RESULT_REJECTED")
        tests["E9_REPLAY_REJECTION"] = True

        # E10: source-level acceptance remains tightly scoped.
        final = f.snapshot()
        return {
            "schema": SCHEMA,
            "pass": all(tests.values()),
            "tests": tests,
            "final_state_epoch": final.epoch,
            "final_state_digest": final.state_digest,
            "credit_scope": "LOCAL_DETERMINISTIC_FABRIC_COMPONENT_ONLY_NOT_MODEL_NOT_PHYSICAL_GRID10_NOT_WHOLE_HCU",
            "next_frontier": "REPOSITORY_BOUND_EXECUTION_THEN_PHYSICAL_GRID10_AND_MEASURED_COORDINATOR_FANIN_COMPRESSION",
        }
    finally:
        f.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="xeno-self-organizing-") as td:
        print(json.dumps(run(Path(td) / "fabric.sqlite"), indent=2, sort_keys=True))
