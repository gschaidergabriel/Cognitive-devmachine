#!/usr/bin/env python3
"""Trigger-2 test-only physical GRID10 atomic cohort + monotonic membership fusion.

Closes the current ATOMIC_COHORT_MONOTONIC_MEMBERSHIP_AUTHORITY_SPLICE candidate gap:

  deterministic membership admission M_j
    + ten simultaneously live OS producers
    + one exact read-only S1 snapshot S_k
    + exact barrier PID/packet binding
    -> immutable NODE_RESULT packets carrying source_membership_id
    -> one deterministic GLOBAL atomic cohort admission
    -> one S1 transition S_k -> S_k+1.

For a NEW active cohort, re-registration/revocation of any member after observation invalidates
that old member even when S1 cognitive snapshot identity itself did not change. Exact replay of
an ALREADY admitted cohort remains idempotent zero-delta and does not claim the historical
membership became current again.

This fixture is source/local deterministic evidence only. It performs no provider/model/network
execution and mints no physical GRID10 runtime, whole-HCU, EntityOS, J-Space, training,
canonical-truth, or effect-authority credit.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Any

from xeno_physical_grid10_acceptance_v2 import (
    ExactSnapshotFabric,
    N,
    _choose_task,
    concurrent_probe,
    open_ro_snapshot,
)
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, cj, dg

SCHEMA = "TRIGGER2_GRID10_ATOMIC_MEMBERSHIP_COHORT_ACCEPTANCE/v1"
MEMBERSHIP_SCHEMA = "GRID_NODE_MEMBERSHIP/v1"
COHORT_SCHEMA = "GRID10_ATOMIC_MEMBERSHIP_COHORT/v1"
SCOPE = "GLOBAL"


def snapshot_identity(snapshot: Any) -> tuple[int, int, str]:
    return (int(snapshot.generation), int(snapshot.epoch), str(snapshot.state_digest))


def packet_snapshot_identity(packet: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(packet["generation"]),
        int(packet["state_epoch"]),
        str(packet["state_digest"]),
    )


def packet_core(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }


def expect_error(fn: Any, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


class AtomicMembershipFabric(ExactSnapshotFabric):
    """Deterministic test fabric with separate monotonic node-membership authority."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.con.executescript(
            """
            CREATE TABLE node_memberships(
              membership_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              capability TEXT NOT NULL,
              generation INTEGER NOT NULL,
              serial INTEGER NOT NULL,
              valid INTEGER NOT NULL,
              healthy INTEGER NOT NULL
            );
            CREATE INDEX node_memberships_active
              ON node_memberships(node_id, valid, serial);

            CREATE TABLE cohort_admissions(
              cohort_id TEXT PRIMARY KEY,
              scope TEXT NOT NULL,
              coordinator_lease_id TEXT NOT NULL,
              start_generation INTEGER NOT NULL,
              start_epoch INTEGER NOT NULL,
              start_digest TEXT NOT NULL,
              member_count INTEGER NOT NULL,
              member_identity_json TEXT NOT NULL,
              resulting_epoch INTEGER NOT NULL,
              summary_digest TEXT NOT NULL
            );
            CREATE TABLE cohort_members(
              cohort_id TEXT NOT NULL,
              source_node_id TEXT NOT NULL,
              source_membership_id TEXT NOT NULL,
              producer_pid INTEGER NOT NULL,
              packet_digest TEXT NOT NULL,
              PRIMARY KEY(cohort_id, packet_digest),
              UNIQUE(cohort_id, source_node_id),
              UNIQUE(cohort_id, source_membership_id),
              UNIQUE(cohort_id, producer_pid)
            );
            """
        )

    def runtime_register_node(self, node_id: str, capability: str) -> dict[str, Any]:
        # Re-registration is a deterministic authority event separate from S1 cognitive state.
        super().runtime_register_node(node_id, capability)
        prior = self.con.execute(
            "SELECT COALESCE(MAX(serial),0) AS n FROM node_memberships"
        ).fetchone()
        serial = int(prior["n"]) + 1
        generation = self._int("generation")
        membership_id = "member-" + dg(
            {
                "schema": MEMBERSHIP_SCHEMA,
                "node_id": node_id,
                "capability": capability,
                "generation": generation,
                "serial": serial,
            }
        )[:24]
        self.con.execute(
            "UPDATE node_memberships SET valid=0 WHERE node_id=? AND valid=1",
            (node_id,),
        )
        self.con.execute(
            "INSERT INTO node_memberships VALUES(?,?,?,?,?,1,1)",
            (membership_id, node_id, capability, generation, serial),
        )
        return {
            "schema": MEMBERSHIP_SCHEMA,
            "membership_id": membership_id,
            "node_id": node_id,
            "capability": capability,
            "generation": generation,
            "serial": serial,
        }

    def runtime_set_health(self, node_id: str, healthy: bool) -> None:
        super().runtime_set_health(node_id, healthy)
        self.con.execute(
            "UPDATE node_memberships SET healthy=? WHERE node_id=? AND valid=1",
            (1 if healthy else 0, node_id),
        )

    def active_membership(self, node_id: str) -> dict[str, Any]:
        row = self.con.execute(
            "SELECT * FROM node_memberships WHERE node_id=? AND valid=1 "
            "ORDER BY serial DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        if row is None:
            raise FabricError("NODE_MEMBERSHIP_NOT_FOUND")
        return dict(row)

    def _validate_membership_packet(
        self,
        packet: dict[str, Any],
        ready_by_node: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        node_id = packet.get("source_node_id")
        membership_id = packet.get("source_membership_id")
        if not isinstance(node_id, str) or not node_id:
            raise FabricError("COHORT_SOURCE_NODE_ID_INVALID")
        if not isinstance(membership_id, str) or not membership_id:
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_REQUIRED")

        ready = ready_by_node.get(node_id)
        if ready is None:
            raise FabricError("COHORT_READY_BINDING_MISSING")
        if ready.get("source_membership_id") != membership_id:
            raise FabricError("COHORT_READY_MEMBERSHIP_BINDING_MISMATCH")

        packet_pid = int(packet["payload"]["process_pid"])
        if packet_pid != int(ready["pid"]):
            raise FabricError("COHORT_PID_PACKET_BINDING_MISMATCH")
        if packet_snapshot_identity(packet) != (
            int(ready["generation"]),
            int(ready["state_epoch"]),
            str(ready["state_digest"]),
        ):
            raise FabricError("COHORT_READY_PACKET_SNAPSHOT_MISMATCH")

        row = self.con.execute(
            "SELECT * FROM node_memberships WHERE membership_id=?",
            (membership_id,),
        ).fetchone()
        if row is None:
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_UNKNOWN")
        if row["node_id"] != node_id or int(row["valid"]) != 1:
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_INVALID")
        if int(row["healthy"]) != 1:
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_UNHEALTHY")
        if int(row["generation"]) != self._int("generation"):
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_STALE_GENERATION")
        if row["capability"] != "reason":
            raise FabricError("COHORT_SOURCE_MEMBERSHIP_CAPABILITY_INVALID")

        node = self.con.execute(
            "SELECT capability,healthy FROM nodes WHERE node_id=?",
            (node_id,),
        ).fetchone()
        if node is None or int(node["healthy"]) != 1:
            raise FabricError("COHORT_SOURCE_NODE_NOT_CURRENT_HEALTHY")
        if node["capability"] != row["capability"]:
            raise FabricError("COHORT_NODE_MEMBERSHIP_CAPABILITY_MISMATCH")

        return {
            "source_node_id": node_id,
            "source_membership_id": membership_id,
            "membership_serial": int(row["serial"]),
            "membership_generation": int(row["generation"]),
            "producer_pid": packet_pid,
            "packet_digest": str(packet["packet_digest"]),
            "generation": int(packet["generation"]),
            "state_epoch": int(packet["state_epoch"]),
            "state_digest": str(packet["state_digest"]),
        }

    def _canonical_members(
        self,
        packets: list[dict[str, Any]],
        proof: dict[str, Any],
        *,
        require_current_membership: bool,
    ) -> list[dict[str, Any]]:
        ready_rows = proof.get("ready")
        if not isinstance(ready_rows, list) or len(ready_rows) != N:
            raise FabricError("COHORT_READY_PROOF_INVALID")
        ready_by_node = {str(row["node_id"]): row for row in ready_rows}
        if len(ready_by_node) != N:
            raise FabricError("COHORT_READY_NODE_ID_DUPLICATE")

        members: list[dict[str, Any]] = []
        for packet in packets:
            node_id = str(packet.get("source_node_id"))
            membership_id = packet.get("source_membership_id")
            ready = ready_by_node.get(node_id)
            if ready is None:
                raise FabricError("COHORT_READY_BINDING_MISSING")
            if ready.get("source_membership_id") != membership_id:
                raise FabricError("COHORT_READY_MEMBERSHIP_BINDING_MISMATCH")
            if int(packet["payload"]["process_pid"]) != int(ready["pid"]):
                raise FabricError("COHORT_PID_PACKET_BINDING_MISMATCH")
            if packet_snapshot_identity(packet) != (
                int(ready["generation"]),
                int(ready["state_epoch"]),
                str(ready["state_digest"]),
            ):
                raise FabricError("COHORT_READY_PACKET_SNAPSHOT_MISMATCH")

            if require_current_membership:
                member = self._validate_membership_packet(packet, ready_by_node)
            else:
                member = {
                    "source_node_id": node_id,
                    "source_membership_id": str(membership_id),
                    "membership_serial": int(packet["source_membership_serial"]),
                    "membership_generation": int(packet["source_membership_generation"]),
                    "producer_pid": int(packet["payload"]["process_pid"]),
                    "packet_digest": str(packet["packet_digest"]),
                    "generation": int(packet["generation"]),
                    "state_epoch": int(packet["state_epoch"]),
                    "state_digest": str(packet["state_digest"]),
                }
            members.append(member)

        ordered = sorted(
            members,
            key=lambda row: (
                row["source_node_id"],
                row["source_membership_id"],
                row["producer_pid"],
                row["packet_digest"],
            ),
        )
        if len({m["source_node_id"] for m in ordered}) != N:
            raise FabricError("COHORT_DUPLICATE_NODE_ID")
        if len({m["source_membership_id"] for m in ordered}) != N:
            raise FabricError("COHORT_DUPLICATE_MEMBERSHIP_ID")
        if len({m["producer_pid"] for m in ordered}) != N:
            raise FabricError("COHORT_DUPLICATE_PROCESS_IDENTITY")
        if len({m["packet_digest"] for m in ordered}) != N:
            raise FabricError("COHORT_DUPLICATE_PACKET")
        return ordered

    def derive_cohort_id(
        self,
        packets: list[dict[str, Any]],
        proof: dict[str, Any],
        lease: dict[str, Any],
        *,
        require_current_membership: bool,
    ) -> tuple[str, list[dict[str, Any]]]:
        members = self._canonical_members(
            packets,
            proof,
            require_current_membership=require_current_membership,
        )
        first = members[0]
        start_identity = (
            first["generation"],
            first["state_epoch"],
            first["state_digest"],
        )
        if any(
            (m["generation"], m["state_epoch"], m["state_digest"])
            != start_identity
            for m in members
        ):
            raise FabricError("COHORT_MIXED_SNAPSHOT")
        cohort_id = "cohort-" + dg(
            {
                "schema": COHORT_SCHEMA,
                "scope": SCOPE,
                "coordinator_lease_id": lease["lease_id"],
                "start_identity": start_identity,
                "members": members,
            }
        )[:32]
        return cohort_id, members

    def atomic_membership_cohort_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packets: list[dict[str, Any]],
        proof: dict[str, Any],
        expected_cohort_id: str,
        expected_generation: int,
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        if len(packets) != N:
            raise FabricError("COHORT_PACKET_COUNT_INVALID")
        if proof.get("distinct_os_pids") != N:
            raise FabricError("COHORT_PHYSICAL_PID_COUNT_INVALID")
        if not proof.get("all_alive_at_barrier"):
            raise FabricError("COHORT_ALL_LIVE_PROOF_MISSING")
        if not proof.get("pid_binding_ok") or not proof.get("packet_pid_binding_ok"):
            raise FabricError("COHORT_PID_BINDING_INVALID")
        if not proof.get("same_snapshot_identity"):
            raise FabricError("COHORT_MIXED_SNAPSHOT")
        if not proof.get("explicit_read_transaction"):
            raise FabricError("COHORT_READ_TRANSACTION_PROOF_MISSING")
        if not proof.get("all_hold_readonly_s1_fd_at_barrier"):
            raise FabricError("COHORT_READONLY_S1_FD_PROOF_MISSING")
        if not proof.get("writer_free_full_probe"):
            raise FabricError("COHORT_WRITER_FREE_PROOF_MISSING")

        expected_identity = (expected_generation, expected_epoch, expected_digest)
        for packet in packets:
            if packet.get("schema") != "NODE_RESULT/v1":
                raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
            if packet.get("source_kind") != "ORDINARY_NODE":
                raise FabricError("COHORT_SOURCE_KIND_INVALID")
            if packet.get("scope") != SCOPE:
                raise FabricError("COHORT_MIXED_SCOPE")
            if packet.get("s1_write_intent") is not False:
                raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")
            if packet_snapshot_identity(packet) != expected_identity:
                raise FabricError("COHORT_MEMBER_SNAPSHOT_MISMATCH")
            if packet.get("packet_digest") != dg(packet_core(packet)):
                raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")

        # First derive the immutable historical identity without requiring that membership is
        # still current. This allows an exact ALREADY-ADMITTED replay to remain idempotent.
        replay_cohort_id, historical_members = self.derive_cohort_id(
            packets,
            proof,
            lease,
            require_current_membership=False,
        )
        if replay_cohort_id != expected_cohort_id:
            raise FabricError("COHORT_ID_BINDING_MISMATCH")
        existing = self.con.execute(
            "SELECT * FROM cohort_admissions WHERE cohort_id=?",
            (replay_cohort_id,),
        ).fetchone()
        if existing is not None:
            if (
                int(existing["start_generation"]) != expected_generation
                or int(existing["start_epoch"]) != expected_epoch
                or str(existing["start_digest"]) != expected_digest
                or int(existing["member_count"]) != N
                or json.loads(existing["member_identity_json"]) != historical_members
            ):
                raise FabricError("COHORT_REPLAY_BINDING_MISMATCH")
            return {
                "cohort_id": replay_cohort_id,
                "replay": True,
                "state_delta": 0,
                "resulting_epoch": int(existing["resulting_epoch"]),
                "membership_revalidated_as_current": False,
                "historical_provenance_preserved": True,
            }

        # NEW active cohort: every exact producer membership must still be the current admitted
        # membership. Re-registration/revocation invalidates the old producer realization.
        cohort_id, members = self.derive_cohort_id(
            packets,
            proof,
            lease,
            require_current_membership=True,
        )
        if cohort_id != expected_cohort_id:
            raise FabricError("COHORT_ID_BINDING_MISMATCH")

        current = self.snapshot()
        if snapshot_identity(current) != expected_identity:
            raise FabricError("COHORT_START_SNAPSHOT_STALE")
        self._lease_row(lease, token, SCOPE)

        ordered_packet_digests = [member["packet_digest"] for member in members]
        summary_payload = {
            "schema": "GRID10_ATOMIC_MEMBERSHIP_COHORT_SUMMARY/v1",
            "cohort_id": cohort_id,
            "member_count": N,
            "ordered_members": members,
            "starting_snapshot": {
                "generation": expected_generation,
                "epoch": expected_epoch,
                "state_digest": expected_digest,
            },
            "observation_relabelled_as_current": False,
            "membership_relabelled_as_current_after_replay": False,
        }
        summary_digest = dg(summary_payload)

        self.con.execute("BEGIN IMMEDIATE")
        try:
            inside = self.snapshot()
            if snapshot_identity(inside) != expected_identity:
                raise FabricError("COHORT_CAS_FAILED")
            self._lease_row(lease, token, SCOPE)

            # Revalidate membership inside the writer transaction to close TOCTOU between
            # preflight and S1 mutation.
            ready_by_node = {
                str(row["node_id"]): row for row in proof.get("ready", [])
            }
            for packet in packets:
                self._validate_membership_packet(packet, ready_by_node)

            scope_row = self.con.execute(
                "SELECT * FROM scopes WHERE scope=?", (SCOPE,)
            ).fetchone()
            if scope_row is None:
                raise FabricError("UNKNOWN_SCOPE")
            for packet_digest in ordered_packet_digests:
                if self.con.execute(
                    "SELECT 1 FROM admitted_results WHERE result_digest=?",
                    (packet_digest,),
                ).fetchone():
                    raise FabricError("COHORT_MEMBER_ALREADY_ADMITTED")

            new_epoch = expected_epoch + 1
            merged = {
                "previous": json.loads(scope_row["summary_json"]),
                "latest": summary_payload,
                "source_schema": COHORT_SCHEMA,
            }
            self.con.execute(
                "UPDATE scopes SET summary_json=?,evidence_count=evidence_count+?,"
                "last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE scope=?",
                (
                    cj(merged),
                    N,
                    lease["lease_id"],
                    summary_digest,
                    new_epoch,
                    SCOPE,
                ),
            )
            packet_by_digest = {str(p["packet_digest"]): p for p in packets}
            for member in members:
                packet = packet_by_digest[member["packet_digest"]]
                self.con.execute(
                    "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                    (
                        packet["packet_digest"],
                        packet["source_node_id"],
                        lease["lease_id"],
                        SCOPE,
                        new_epoch,
                    ),
                )
                self.con.execute(
                    "INSERT INTO cohort_members VALUES(?,?,?,?,?)",
                    (
                        cohort_id,
                        member["source_node_id"],
                        member["source_membership_id"],
                        member["producer_pid"],
                        member["packet_digest"],
                    ),
                )
            self.con.execute(
                "INSERT INTO cohort_admissions VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    cohort_id,
                    SCOPE,
                    lease["lease_id"],
                    expected_generation,
                    expected_epoch,
                    expected_digest,
                    N,
                    cj(members),
                    new_epoch,
                    summary_digest,
                ),
            )
            self._set("epoch", str(new_epoch))
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise

        return {
            "cohort_id": cohort_id,
            "replay": False,
            "state_delta": 1,
            "prior_epoch": expected_epoch,
            "resulting_epoch": new_epoch,
            "member_count": N,
            "summary_digest": summary_digest,
            "membership_revalidated_as_current": True,
            "canonical_truth": False,
            "effect_authority": False,
        }


def child_node(
    db: Path,
    node_id: str,
    scope: str,
    barrier_dir: Path,
) -> int:
    started_ns = time.time_ns()
    con, snapshot = open_ro_snapshot(db)
    try:
        membership = con.execute(
            "SELECT * FROM node_memberships WHERE node_id=? AND valid=1 "
            "ORDER BY serial DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        if membership is None:
            raise SystemExit("ACTIVE_MEMBERSHIP_REQUIRED")
        task = _choose_task(snapshot, scope)
        payload = {
            "node": node_id,
            "task_id": None if task is None else task["task_id"],
            "observation": f"result:{node_id}",
            "useful": task is not None,
            "process_pid": os.getpid(),
        }
        core = {
            "schema": "NODE_RESULT/v1",
            "source_kind": "ORDINARY_NODE",
            "source_node_id": node_id,
            "source_membership_id": str(membership["membership_id"]),
            "source_membership_serial": int(membership["serial"]),
            "source_membership_generation": int(membership["generation"]),
            "scope": scope,
            "generation": snapshot["generation"],
            "state_epoch": snapshot["epoch"],
            "state_digest": snapshot["state_digest"],
            "payload": payload,
        }
        packet = {**core, "packet_digest": dg(core), "s1_write_intent": False}

        ready_dir = barrier_dir / "ready"
        ready_dir.mkdir(parents=True, exist_ok=True)
        ready = {
            "node_id": node_id,
            "pid": os.getpid(),
            "started_ns": started_ns,
            "ready_ns": time.time_ns(),
            "generation": snapshot["generation"],
            "state_epoch": snapshot["epoch"],
            "state_digest": snapshot["state_digest"],
            "source_membership_id": str(membership["membership_id"]),
            "source_membership_serial": int(membership["serial"]),
            "source_membership_generation": int(membership["generation"]),
            "ro_transaction_open": bool(con.in_transaction),
            "db_path": str(db.resolve()),
        }
        tmp = ready_dir / f".{node_id}.{os.getpid()}.tmp"
        dst = ready_dir / f"{node_id}.json"
        tmp.write_text(cj(ready), encoding="utf-8")
        tmp.replace(dst)

        release = barrier_dir / "release"
        deadline = time.monotonic() + 20.0
        while not release.exists():
            if time.monotonic() >= deadline:
                raise SystemExit("BARRIER_RELEASE_TIMEOUT")
            time.sleep(0.01)
        print(cj(packet), flush=True)
        return 0
    finally:
        if con.in_transaction:
            con.rollback()
        con.close()


def make_fixture(
    root: Path,
    label: str,
) -> tuple[
    AtomicMembershipFabric,
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    str,
    Any,
    dict[str, dict[str, Any]],
]:
    db = root / f"{label}.sqlite"
    barrier = root / f"{label}-barrier"
    fabric = AtomicMembershipFabric(db)
    ids = [f"x{i:02d}" for i in range(1, N + 1)]
    memberships: dict[str, dict[str, Any]] = {}
    for node_id in ids:
        memberships[node_id] = fabric.runtime_register_node(node_id, "reason")
    fabric.seed_scope(SCOPE)
    for i in range(N):
        fabric.seed_task(f"t{i:02d}", SCOPE, 100 - i, "reason", {"q": i})
    lease, token = fabric.elect_coordinator(SCOPE)
    start = fabric.snapshot()
    packets, proof = concurrent_probe(
        Path(__file__).resolve(),
        db,
        ids,
        [SCOPE] * N,
        barrier,
    )
    return fabric, packets, proof, lease, token, start, memberships


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="trigger2-grid10-membership-cohort-") as td:
        root = Path(td)

        # Positive + replay-after-reregistration: historical replay is zero delta.
        fabric, packets, proof, lease, token, start, memberships = make_fixture(root, "positive")
        try:
            cohort_id, _ = fabric.derive_cohort_id(
                packets, proof, lease, require_current_membership=True
            )
            before_packets = cj(packets)
            receipt = fabric.atomic_membership_cohort_commit(
                lease=lease,
                token=token,
                packets=packets,
                proof=proof,
                expected_cohort_id=cohort_id,
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
            )
            after = fabric.snapshot()
            old_x01_membership = memberships["x01"]["membership_id"]
            successor = fabric.runtime_register_node("x01", "reason")
            replay = fabric.atomic_membership_cohort_commit(
                lease=lease,
                token=token,
                packets=packets,
                proof=proof,
                expected_cohort_id=cohort_id,
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
            )
            tests["A1_PHYSICAL_BARRIER_COHORT"] = bool(
                proof["distinct_os_pids"] == N
                and proof["all_alive_at_barrier"]
                and proof["same_snapshot_identity"]
                and proof["all_hold_readonly_s1_fd_at_barrier"]
                and proof["writer_free_full_probe"]
            )
            tests["A2_PACKET_MEMBERSHIP_IDS_MATCH_OBSERVATION_ADMISSIONS"] = all(
                packet["source_membership_id"]
                == memberships[packet["source_node_id"]]["membership_id"]
                for packet in packets
            )
            tests["A3_ONE_ATOMIC_BATCH_ONE_EPOCH_ADVANCE"] = bool(
                receipt["state_delta"] == 1
                and after.epoch == start.epoch + 1
            )
            tests["A4_ORIGINAL_PACKETS_IMMUTABLE"] = cj(packets) == before_packets
            tests["A5_REREGISTRATION_REVOKES_OLD_MEMBERSHIP_ID"] = bool(
                successor["membership_id"] != old_x01_membership
                and fabric.active_membership("x01")["membership_id"]
                == successor["membership_id"]
            )
            tests["A6_ALREADY_ADMITTED_REPLAY_AFTER_REREGISTRATION_ZERO_DELTA"] = bool(
                replay["replay"] is True
                and replay["state_delta"] == 0
                and fabric.snapshot().epoch == after.epoch
                and replay["membership_revalidated_as_current"] is False
            )
        finally:
            fabric.close()

        # Negative 1: re-register after observation but BEFORE the first commit. S1 cognitive
        # snapshot remains unchanged, yet the old producer membership must fail closed.
        fabric, packets, proof, lease, token, start, memberships = make_fixture(root, "reregister")
        try:
            cohort_id, _ = fabric.derive_cohort_id(
                packets, proof, lease, require_current_membership=True
            )
            before = fabric.snapshot()
            successor = fabric.runtime_register_node("x01", "reason")
            after_reregister = fabric.snapshot()
            tests["N1_REREGISTRATION_DOES_NOT_HIDE_INSIDE_S1_FRESHNESS"] = (
                snapshot_identity(before) == snapshot_identity(after_reregister)
                and successor["membership_id"] != memberships["x01"]["membership_id"]
            )
            tests["N2_REVOKED_OBSERVATION_MEMBERSHIP_REJECTED_BEFORE_FIRST_COMMIT"] = expect_error(
                lambda: fabric.atomic_membership_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=packets,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_SOURCE_MEMBERSHIP_INVALID",
            )
            tests["N3_REREGISTRATION_NEGATIVE_ZERO_S1_DELTA"] = (
                snapshot_identity(fabric.snapshot()) == snapshot_identity(after_reregister)
            )
        finally:
            fabric.close()

        # Negative 2: substitute the successor membership id into the old process packet.
        fabric, packets, proof, lease, token, start, _ = make_fixture(root, "substitution")
        try:
            original_cohort_id, _ = fabric.derive_cohort_id(
                packets, proof, lease, require_current_membership=True
            )
            successor = fabric.runtime_register_node("x01", "reason")
            forged = [dict(packet) for packet in packets]
            forged[0] = dict(forged[0])
            forged[0]["source_membership_id"] = successor["membership_id"]
            forged[0]["source_membership_serial"] = successor["serial"]
            forged[0]["source_membership_generation"] = successor["generation"]
            forged[0]["packet_digest"] = dg(packet_core(forged[0]))
            tests["N4_REPLACEMENT_MEMBERSHIP_CANNOT_REBIND_OLD_PROCESS_WITNESS"] = expect_error(
                lambda: fabric.atomic_membership_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=forged,
                    proof=proof,
                    expected_cohort_id=original_cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_READY_MEMBERSHIP_BINDING_MISMATCH",
            )
        finally:
            fabric.close()

        # Negative 3: ghost membership id is not fabric authority even with a recomputed packet hash.
        fabric, packets, proof, lease, token, start, _ = make_fixture(root, "ghost")
        try:
            cohort_id, _ = fabric.derive_cohort_id(
                packets, proof, lease, require_current_membership=True
            )
            ghost = [dict(packet) for packet in packets]
            ghost[0] = dict(ghost[0])
            ghost[0]["source_membership_id"] = "member-" + "0" * 24
            ghost[0]["packet_digest"] = dg(packet_core(ghost[0]))
            tests["N5_GHOST_MEMBERSHIP_REJECTED"] = expect_error(
                lambda: fabric.atomic_membership_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=ghost,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_READY_MEMBERSHIP_BINDING_MISMATCH",
            )
        finally:
            fabric.close()

        # Negative 4: current membership unhealthy is rejected as a membership authority failure.
        fabric, packets, proof, lease, token, start, _ = make_fixture(root, "unhealthy")
        try:
            cohort_id, _ = fabric.derive_cohort_id(
                packets, proof, lease, require_current_membership=True
            )
            fabric.runtime_set_health("x01", False)
            tests["N6_UNHEALTHY_MEMBERSHIP_REJECTED"] = expect_error(
                lambda: fabric.atomic_membership_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=packets,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_SOURCE_MEMBERSHIP_UNHEALTHY",
            )
        finally:
            fabric.close()

        passed = all(tests.values())
        return {
            "schema": SCHEMA,
            "pass": passed,
            "tests": tests,
            "contract_scope": "TEST_ONLY_PHYSICAL_GRID10_ATOMIC_COHORT_PLUS_MONOTONIC_MEMBERSHIP",
            "membership_policy": {
                "new_active_batch": "STRICT_CURRENT_MEMBERSHIP",
                "already_admitted_exact_replay": "HISTORICAL_IDEMPOTENT_ZERO_DELTA",
                "model_can_mint_membership": False,
                "membership_identity_is_s1_cognitive_state": False,
            },
            "remaining_gap": (
                "The child reads active membership from deterministic fabric state inside the same "
                "read-only database transaction and binds it to its packet/barrier PID. This still "
                "does not by itself prove a generic consumed-read attestation for every cognition-"
                "relevant input; the fabric-observed read-set/bypass discriminator remains separate."
            ),
            "promotion": "BLOCKED_NO_REPOSITORY_BOUND_EXECUTION_AND_CONSUMED_INPUT_GATE_OPEN",
            "credit_boundary": {
                "source_or_local_candidate_only": True,
                "physical_grid10_runtime_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
                "jspace_model_credit": 0,
                "accepted_dataset_tokens": 0,
                "training_credit": 0,
                "canonical_truth": False,
                "effect_authority": False,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node")
    parser.add_argument("--scope", default=SCOPE)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--barrier-dir", type=Path)
    args = parser.parse_args()
    if args.node:
        if args.db is None or args.barrier_dir is None:
            raise SystemExit("child mode requires --db and --barrier-dir")
        return child_node(args.db, args.node, args.scope, args.barrier_dir)
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
