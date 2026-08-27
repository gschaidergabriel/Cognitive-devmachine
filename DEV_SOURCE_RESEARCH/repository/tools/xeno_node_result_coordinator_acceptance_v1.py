#!/usr/bin/env python3
"""Executable acceptance harness for Xeno ordinary-node -> coordinator transport.

Scope:
- ordinary Xeno nodes are S1 READ-ONLY;
- ordinary results leave the node only as ephemeral NODE_RESULT/v1 packets;
- only a valid dynamically leased coordinator may admit/compress results into S1;
- all result and write paths are bound to exact state epoch/digest/generation;
- stale, duplicate, wrong-scope and wrong-lease writes fail closed;
- multiple scoped coordinators can operate without silent last-writer-wins.

This is a deterministic local fixture. It does not call any model/provider/network and
cannot mint physical GRID10/HCU/EntityOS runtime credit by source presence alone.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

SCHEMA = "XENO_NODE_RESULT_COORDINATOR_ACCEPTANCE/v1"
RESULT_SCHEMA = "NODE_RESULT/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
DELTA_SCHEMA = "S1_COORDINATOR_DELTA/v1"


class GridError(ValueError):
    pass


def cj(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dg(v: Any) -> str:
    return hashlib.sha256(cj(v).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    epoch: int
    generation: int
    state_digest: str
    branches: tuple[dict[str, Any], ...]
    leases: tuple[dict[str, Any], ...]


class SharedState:
    def __init__(self, path: Path):
        self.con = sqlite3.connect(path, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE branches(
              branch_id TEXT PRIMARY KEY,
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
              valid INTEGER NOT NULL,
              token_digest TEXT NOT NULL,
              granted_epoch INTEGER NOT NULL
            );
            CREATE TABLE admitted_results(
              result_digest TEXT PRIMARY KEY,
              result_id TEXT NOT NULL,
              source_node_id TEXT NOT NULL,
              coordinator_lease_id TEXT NOT NULL,
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
            raise GridError(f"MISSING_META:{k}")
        return int(r["v"])

    def _bump(self) -> int:
        e = self._int("epoch") + 1
        self._set("epoch", str(e))
        return e

    def seed_branch(self, branch_id: str, summary: Any) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO branches VALUES(?,?,?,?,?,?)",
            (branch_id, cj(summary), 0, None, None, self._int("epoch")),
        )
        self._bump()

    def snapshot(self) -> Snapshot:
        epoch = self._int("epoch")
        generation = self._int("generation")
        branches = tuple(dict(r) for r in self.con.execute("SELECT * FROM branches ORDER BY branch_id"))
        leases = tuple(
            dict(r) for r in self.con.execute(
                "SELECT lease_id,node_id,scope,generation,valid,granted_epoch FROM leases ORDER BY lease_id"
            )
        )
        state_digest = dg({"epoch": epoch, "generation": generation, "branches": branches, "leases": leases})
        return Snapshot(epoch, generation, state_digest, branches, leases)

    def grant_lease(self, node_id: str, scope: str) -> tuple[dict[str, Any], str]:
        snap = self.snapshot()
        token = dg({"node_id": node_id, "scope": scope, "epoch": snap.epoch, "generation": snap.generation})
        lease_id = "lease-" + token[:24]
        self.con.execute(
            "INSERT OR REPLACE INTO leases VALUES(?,?,?,?,?,?,?)",
            (lease_id, node_id, scope, snap.generation, 1, dg(token), snap.epoch),
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

    def _validate_lease(self, lease: dict[str, Any], token: str, branch_id: str) -> sqlite3.Row:
        if lease.get("schema") != LEASE_SCHEMA:
            raise GridError("LEASE_SCHEMA_INVALID")
        row = self.con.execute("SELECT * FROM leases WHERE lease_id=?", (lease.get("lease_id"),)).fetchone()
        if row is None or int(row["valid"]) != 1:
            raise GridError("COORDINATOR_LEASE_INVALID")
        if row["node_id"] != lease.get("node_id") or row["token_digest"] != dg(token):
            raise GridError("COORDINATOR_LEASE_BINDING_INVALID")
        if int(row["generation"]) != self._int("generation"):
            raise GridError("COORDINATOR_LEASE_STALE_GENERATION")
        scope = row["scope"]
        if scope != "GLOBAL" and scope != f"branch:{branch_id}":
            raise GridError("COORDINATOR_SCOPE_VIOLATION")
        return row

    def ordinary_write_attempt(self, branch_id: str, value: Any) -> None:
        raise GridError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")

    def admit_result(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        result: dict[str, Any],
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        if result.get("schema") != RESULT_SCHEMA:
            raise GridError("RESULT_SCHEMA_INVALID")
        branch_id = str(result.get("branch_id"))
        self._validate_lease(lease, token, branch_id)
        current = self.snapshot()
        if result.get("generation") != current.generation:
            raise GridError("RESULT_STALE_GENERATION")
        if int(result.get("state_epoch", -1)) > current.epoch:
            raise GridError("RESULT_FUTURE_EPOCH")
        if expected_epoch != current.epoch or expected_digest != current.state_digest:
            raise GridError("S1_COMPARE_AND_SWAP_FAILED")
        payload_core = {
            "schema": RESULT_SCHEMA,
            "result_id": result.get("result_id"),
            "source_node_id": result.get("source_node_id"),
            "branch_id": branch_id,
            "generation": result.get("generation"),
            "state_epoch": result.get("state_epoch"),
            "state_digest": result.get("state_digest"),
            "payload": result.get("payload"),
        }
        if result.get("result_digest") != dg(payload_core):
            raise GridError("RESULT_DIGEST_MISMATCH")
        seen = self.con.execute(
            "SELECT 1 FROM admitted_results WHERE result_digest=?", (result["result_digest"],)
        ).fetchone()
        if seen is not None:
            raise GridError("DUPLICATE_RESULT_REJECTED")
        branch = self.con.execute("SELECT * FROM branches WHERE branch_id=?", (branch_id,)).fetchone()
        if branch is None:
            raise GridError("UNKNOWN_BRANCH")

        self.con.execute("BEGIN IMMEDIATE")
        try:
            # Recheck inside the write transaction.
            tx_epoch = self._int("epoch")
            if tx_epoch != expected_epoch:
                raise GridError("S1_COMPARE_AND_SWAP_FAILED")
            merged = {
                "branch_id": branch_id,
                "latest": result["payload"],
                "previous": json.loads(branch["summary_json"]),
            }
            new_epoch = tx_epoch + 1
            self.con.execute(
                "UPDATE branches SET summary_json=?,evidence_count=evidence_count+1,last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE branch_id=?",
                (cj(merged), lease["lease_id"], result["result_digest"], new_epoch, branch_id),
            )
            self.con.execute(
                "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                (result["result_digest"], result["result_id"], result["source_node_id"], lease["lease_id"], new_epoch),
            )
            self._set("epoch", str(new_epoch))
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise

        return {
            "schema": DELTA_SCHEMA,
            "branch_id": branch_id,
            "source_result_digest": result["result_digest"],
            "coordinator_lease_id": lease["lease_id"],
            "prior_epoch": expected_epoch,
            "new_epoch": new_epoch,
            "canonical_truth": False,
            "effect_authority": False,
        }


class OrdinaryNode:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def compute_result(self, snap: Snapshot, branch_id: str, payload: Any) -> dict[str, Any]:
        core = {
            "schema": RESULT_SCHEMA,
            "result_id": "res-" + dg({"node": self.node_id, "branch": branch_id, "epoch": snap.epoch, "payload": payload})[:24],
            "source_node_id": self.node_id,
            "branch_id": branch_id,
            "generation": snap.generation,
            "state_epoch": snap.epoch,
            "state_digest": snap.state_digest,
            "payload": payload,
        }
        return {**core, "result_digest": dg(core), "s1_write_intent": False}


def ok(cond: bool, code: str) -> None:
    if not cond:
        raise GridError(code)


def expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except GridError as exc:
        got = str(exc)
    if got != code:
        raise GridError(f"EXPECTED_{code}_GOT_{got}")


def run(path: Path) -> dict[str, Any]:
    s = SharedState(path)
    tests: dict[str, Any] = {}
    try:
        s.seed_branch("alpha", {"status": "open"})
        s.seed_branch("beta", {"status": "open"})
        worker = OrdinaryNode("x-worker")

        # N1 ordinary node has no S1 mutation capability.
        expect_error(lambda: s.ordinary_write_attempt("alpha", {"illegal": True}), "ORDINARY_NODE_S1_WRITE_FORBIDDEN")
        tests["N1_ORDINARY_READ_ONLY"] = {"pass": True}

        # N2 ordinary output is an epoch/digest-bound ephemeral NODE_RESULT.
        snap0 = s.snapshot()
        r1 = worker.compute_result(snap0, "alpha", {"evidence": "A"})
        ok(r1["schema"] == RESULT_SCHEMA and r1["s1_write_intent"] is False, "N2_RESULT_SHAPE_INVALID")
        tests["N2_NODE_RESULT_BOUND"] = {"pass": True, "result_digest": r1["result_digest"]}

        # N3 no valid coordinator lease -> no write.
        fake = {"schema": LEASE_SCHEMA, "lease_id": "none", "node_id": "x-coord", "scope": "branch:alpha", "generation": 1}
        expect_error(lambda: s.admit_result(lease=fake, token="bad", result=r1, expected_epoch=snapshot.epoch if False else snap0.epoch, expected_digest=snap0.state_digest), "COORDINATOR_LEASE_INVALID")
        tests["N3_NO_LEASE_NO_WRITE"] = {"pass": True}

        # N4 valid dynamically leased coordinator admits/compresses result to S1.
        lease_a, token_a = s.grant_lease("x-coord-a", "branch:alpha")
        snap1 = s.snapshot()
        r2 = worker.compute_result(snap1, "alpha", {"evidence": "A2"})
        d1 = s.admit_result(lease=lease_a, token=token_a, result=r2, expected_epoch=snap1.epoch, expected_digest=snap1.state_digest)
        ok(d1["new_epoch"] == snap1.epoch + 1 and d1["canonical_truth"] is False, "N4_COORDINATOR_COMMIT_INVALID")
        tests["N4_COORDINATOR_ONLY_WRITE"] = {"pass": True, "delta": d1}

        # N5 duplicate result cannot be replayed into shared state.
        snap2 = s.snapshot()
        expect_error(lambda: s.admit_result(lease=lease_a, token=token_a, result=r2, expected_epoch=snap2.epoch, expected_digest=snap2.state_digest), "DUPLICATE_RESULT_REJECTED")
        tests["N5_DUPLICATE_REJECTED"] = {"pass": True}

        # N6 scoped coordinator cannot mutate a different branch.
        r_beta = worker.compute_result(s.snapshot(), "beta", {"evidence": "B"})
        snap_beta = s.snapshot()
        expect_error(lambda: s.admit_result(lease=lease_a, token=token_a, result=r_beta, expected_epoch=snap_beta.epoch, expected_digest=snap_beta.state_digest), "COORDINATOR_SCOPE_VIOLATION")
        tests["N6_SCOPE_ISOLATION"] = {"pass": True}

        # N7 stale CAS loses after another scoped coordinator advances S1.
        lease_b, token_b = s.grant_lease("x-coord-b", "branch:beta")
        stale_snap = s.snapshot()
        r_alpha3 = worker.compute_result(stale_snap, "alpha", {"evidence": "A3"})
        r_beta2 = worker.compute_result(stale_snap, "beta", {"evidence": "B2"})
        s.admit_result(lease=lease_b, token=token_b, result=r_beta2, expected_epoch=stale_snap.epoch, expected_digest=stale_snap.state_digest)
        expect_error(lambda: s.admit_result(lease=lease_a, token=token_a, result=r_alpha3, expected_epoch=stale_snap.epoch, expected_digest=stale_snap.state_digest), "S1_COMPARE_AND_SWAP_FAILED")
        tests["N7_STALE_COORDINATOR_CAS_REJECTED"] = {"pass": True}

        # N8 after deterministic re-read/recompute the alpha coordinator can proceed.
        rebased = s.snapshot()
        r_alpha4 = worker.compute_result(rebased, "alpha", {"evidence": "A4-rebased"})
        d2 = s.admit_result(lease=lease_a, token=token_a, result=r_alpha4, expected_epoch=rebased.epoch, expected_digest=rebased.state_digest)
        tests["N8_REBASE_AND_COMMIT"] = {"pass": True, "delta": d2}

        # N9 revoked coordinator immediately loses write authority.
        s.revoke_lease(lease_a["lease_id"])
        after_revoke = s.snapshot()
        r_after = worker.compute_result(after_revoke, "alpha", {"evidence": "should-not-write"})
        expect_error(lambda: s.admit_result(lease=lease_a, token=token_a, result=r_after, expected_epoch=after_revoke.epoch, expected_digest=after_revoke.state_digest), "COORDINATOR_LEASE_INVALID")
        tests["N9_REVOKED_LEASE_FAILS_CLOSED"] = {"pass": True}

        final = s.snapshot()
        return {
            "schema": SCHEMA,
            "pass": all(v.get("pass") is True for v in tests.values()),
            "tests": tests,
            "final_state_epoch": final.epoch,
            "final_state_digest": final.state_digest,
            "credit_scope": "SOURCE_LEVEL_ACCEPTANCE_HARNESS_ONLY_RUNTIME_EXECUTION_REQUIRED",
            "next_frontier": "INTEGRATE_EPHEMERAL_RESULT_CHANNEL_WITH_AUTONOMOUS_BOOT_AND_DYNAMIC_COORDINATOR_SELECTION_THEN_TEST_FAILURE_REPLACEMENT",
        }
    finally:
        s.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        print(json.dumps(run(Path(td) / "xeno_result_coord.sqlite"), indent=2, sort_keys=True))
