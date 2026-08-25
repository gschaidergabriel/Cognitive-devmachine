#!/usr/bin/env python3
"""Trigger-2 fused physical GRID10 + membership + atomic cohort acceptance candidate.

This file is deliberately a single exact-source composition discriminator. It fuses the
current noncanonical donor mechanisms that were previously proven only in separate fixtures:

1. ten simultaneously-live independent OS processes;
2. each child holds the exact read-only SQLite transaction that produced its NODE_RESULT;
3. parent-observed O_RDONLY attachment to the exact isolated S1 file at the common barrier;
4. exact consumed-snapshot/read-receipt identity bound to producer PID, task and payload;
5. deterministic monotonic node-membership admission identity outside model cognition;
6. exactly the barrier cohort packet set enters coordinator fan-in (no fresh-process splice);
7. one coordinator-authorized atomic cohort transaction advances S1 exactly once;
8. original NODE_RESULT packet digests remain immutable; membership/process authority lives
   in a separate proof-carrying envelope;
9. canonical cohort ordering is independent of transport arrival order;
10. replay is idempotent and stale/tampered/membership-invalid paths fail closed.

Research/source acceptance candidate only. Source presence or a local PASS mints ZERO
physical GRID10 runtime, HCU, EntityOS, J-Space, training, canonical-truth or effect-authority
credit. Current FreeSwarm emergency-stop authority must not be bypassed to execute this file.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any

from trigger2_node_membership_admission_acceptance_v1 import MembershipBoundFabric
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, cj, dg

SCHEMA = "TRIGGER2_GRID10_FUSED_PHYSICAL_MEMBERSHIP_COHORT_ACCEPTANCE/v1"
ENVELOPE_SCHEMA = "PROOF_CARRYING_NODE_RESULT/v1"
COHORT_SCHEMA = "GRID10_FUSED_ATOMIC_COHORT/v1"
SUMMARY_SCHEMA = "GRID10_FUSED_COHORT_SUMMARY/v1"
N = 10
SCOPE = "GLOBAL"


class HeldSnapshot(dict[str, Any]):
    """Snapshot payload owning the exact read-only transaction that produced it."""

    def __init__(self, data: dict[str, Any], con: sqlite3.Connection):
        super().__init__(data)
        self._con = con

    @property
    def transaction_open(self) -> bool:
        return bool(self._con.in_transaction)

    def close(self) -> None:
        if self._con.in_transaction:
            self._con.rollback()
        self._con.close()


def snapshot_identity(snapshot: Any) -> tuple[int, int, str]:
    return (
        int(snapshot.generation if hasattr(snapshot, "generation") else snapshot["generation"]),
        int(snapshot.epoch if hasattr(snapshot, "epoch") else snapshot["epoch"]),
        str(snapshot.state_digest if hasattr(snapshot, "state_digest") else snapshot["state_digest"]),
    )


def read_held_snapshot(path: Path) -> HeldSnapshot:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute("BEGIN")
        epoch = int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
        generation = int(con.execute("SELECT v FROM meta WHERE k='generation'").fetchone()[0])
        tasks = tuple(dict(r) for r in con.execute("SELECT * FROM tasks ORDER BY task_id"))
        scopes = tuple(dict(r) for r in con.execute("SELECT * FROM scopes ORDER BY scope"))
        leases = tuple(
            dict(r)
            for r in con.execute(
                "SELECT lease_id,node_id,scope,generation,granted_epoch,valid "
                "FROM leases ORDER BY lease_id"
            )
        )
        state_digest = dg(
            {
                "epoch": epoch,
                "generation": generation,
                "tasks": tasks,
                "scopes": scopes,
                "leases": leases,
            }
        )
        return HeldSnapshot(
            {
                "epoch": epoch,
                "generation": generation,
                "state_digest": state_digest,
                "tasks": tasks,
                "scopes": scopes,
                "leases": leases,
            },
            con,
        )
    except Exception:
        con.close()
        raise


def node_slot(node_id: str, width: int) -> int:
    digits = "".join(ch for ch in node_id if ch.isdigit())
    if digits:
        return (int(digits) - 1) % max(width, 1)
    return int(dg(node_id)[:8], 16) % max(width, 1)


def build_result(snapshot: dict[str, Any], node_id: str) -> dict[str, Any]:
    eligible = [
        task
        for task in snapshot["tasks"]
        if task["status"] == "OPEN"
        and task["claimed_by"] is None
        and task["capability"] == "reason"
        and task["scope"] == SCOPE
    ]
    eligible.sort(key=lambda task: (-int(task["priority"]), task["task_id"]))
    task = eligible[node_slot(node_id, len(eligible))] if eligible else None
    pid = os.getpid()
    payload = {
        "node": node_id,
        "process_pid": pid,
        "task_id": None if task is None else task["task_id"],
        "observation": f"result:{node_id}",
        "useful": task is not None,
    }
    task_digest = dg(task) if task is not None else dg(None)
    receipt_core = {
        "producer_pid": pid,
        "source_node_id": node_id,
        "consumed_state_epoch": snapshot["epoch"],
        "consumed_state_digest": snapshot["state_digest"],
        "consumed_generation": snapshot["generation"],
        "consumed_task_digest": task_digest,
        "payload_digest": dg(payload),
    }
    core = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node_id,
        "scope": SCOPE,
        "generation": snapshot["generation"],
        "state_epoch": snapshot["epoch"],
        "state_digest": snapshot["state_digest"],
        "producer_pid": pid,
        "consumed_state_epoch": snapshot["epoch"],
        "consumed_state_digest": snapshot["state_digest"],
        "consumed_generation": snapshot["generation"],
        "consumed_task_digest": task_digest,
        "read_receipt_digest": dg(receipt_core),
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def child_mode(
    db: Path,
    node_id: str,
    ready_dir: Path,
    release_file: Path,
) -> int:
    started_ns = time.time_ns()
    snapshot = read_held_snapshot(db)
    try:
        packet = build_result(snapshot, node_id)
        ready_ns = time.time_ns()
        marker = {
            "node_id": node_id,
            "pid": packet["producer_pid"],
            "started_ns": started_ns,
            "ready_ns": ready_ns,
            "generation": packet["generation"],
            "state_epoch": packet["state_epoch"],
            "state_digest": packet["state_digest"],
            "read_receipt_digest": packet["read_receipt_digest"],
            "transaction_bounded": True,
            "transaction_open_at_ready": snapshot.transaction_open,
            "db_path": str(db.resolve()),
        }
        tmp = ready_dir / f".{node_id}.{packet['producer_pid']}.tmp"
        dst = ready_dir / f"{node_id}.json"
        tmp.write_text(cj(marker), encoding="utf-8")
        tmp.replace(dst)

        deadline = time.monotonic() + 20.0
        while not release_file.exists():
            if time.monotonic() >= deadline:
                raise SystemExit("BARRIER_RELEASE_TIMEOUT")
            time.sleep(0.01)

        print(cj(packet), flush=True)
        return 0
    finally:
        snapshot.close()


def procfs_readonly_db_fds(pid: int, db: Path) -> list[int]:
    proc_fd = Path("/proc") / str(pid) / "fd"
    proc_fdinfo = Path("/proc") / str(pid) / "fdinfo"
    if not proc_fd.is_dir() or not proc_fdinfo.is_dir():
        return []
    wanted = db.resolve()
    found: list[int] = []
    for fd_path in proc_fd.iterdir():
        try:
            target_text = os.readlink(fd_path)
            if target_text.endswith(" (deleted)"):
                target_text = target_text[: -len(" (deleted)")]
            target = Path(target_text)
            target = target.resolve() if target.is_absolute() else (fd_path.parent / target).resolve()
            if target != wanted:
                continue
            flags_text = None
            for line in (proc_fdinfo / fd_path.name).read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                if line.startswith("flags:"):
                    flags_text = line.split(":", 1)[1].strip()
                    break
            if flags_text is None:
                continue
            flags = int(flags_text, 8)
            if (flags & os.O_ACCMODE) == os.O_RDONLY:
                found.append(int(fd_path.name))
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
    return sorted(found)


def spawn_held_cohort(
    fabric: MembershipBoundFabric,
    script: Path,
    db: Path,
    node_ids: list[str],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ready_dir = root / "ready"
    ready_dir.mkdir(parents=True, exist_ok=False)
    release_file = root / "release"
    procs: list[subprocess.Popen[str]] = []
    parent_launch_ns: dict[str, int] = {}

    if fabric.con.in_transaction:
        raise FabricError("UNEXPECTED_PARENT_TRANSACTION_BEFORE_FREEZE")
    fabric.con.execute("BEGIN IMMEDIATE")
    freeze_before = snapshot_identity(fabric.snapshot())
    try:
        for node_id in node_ids:
            parent_launch_ns[node_id] = time.time_ns()
            procs.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(script),
                        "--node",
                        node_id,
                        "--db",
                        str(db),
                        "--ready-dir",
                        str(ready_dir),
                        "--release-file",
                        str(release_file),
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )

        deadline = time.monotonic() + 15.0
        markers: dict[str, dict[str, Any]] = {}
        while time.monotonic() < deadline and len(markers) < len(node_ids):
            for node_id in node_ids:
                path = ready_dir / f"{node_id}.json"
                if node_id not in markers and path.exists():
                    markers[node_id] = json.loads(path.read_text(encoding="utf-8"))
            if any(proc.poll() is not None for proc in procs):
                raise FabricError("CHILD_EXITED_BEFORE_ALL_LIVE_BARRIER")
            if len(markers) < len(node_ids):
                time.sleep(0.01)
        if len(markers) != len(node_ids):
            raise FabricError("BARRIER_READY_TIMEOUT")

        observed_pids = [int(markers[node_id]["pid"]) for node_id in node_ids]
        parent_pids = [int(proc.pid) for proc in procs]
        readonly_fds = {
            node_id: procfs_readonly_db_fds(int(proc.pid), db)
            for node_id, proc in zip(node_ids, procs, strict=True)
        }
        freeze_at_barrier = snapshot_identity(fabric.snapshot())
        observer = read_held_snapshot(db)
        try:
            independent_at_barrier = snapshot_identity(observer)
        finally:
            observer.close()

        released_ns = time.time_ns()
        release_file.write_text(str(released_ns), encoding="utf-8")
        packets: list[dict[str, Any]] = []
        exit_ns: dict[str, int] = {}
        for node_id, proc in zip(node_ids, procs, strict=True):
            out, err = proc.communicate(timeout=20)
            exit_ns[node_id] = time.time_ns()
            if proc.returncode != 0:
                raise FabricError(
                    f"CHILD_FAILED:{node_id}:rc={proc.returncode}:stderr={err.strip()}"
                )
            packet = json.loads(out.strip().splitlines()[-1])
            marker = markers[node_id]
            if (
                int(packet["producer_pid"]) != int(marker["pid"])
                or packet["state_epoch"] != marker["state_epoch"]
                or packet["state_digest"] != marker["state_digest"]
                or packet["generation"] != marker["generation"]
                or packet["read_receipt_digest"] != marker["read_receipt_digest"]
            ):
                raise FabricError(f"MARKER_PACKET_BINDING_MISMATCH:{node_id}")
            packets.append(packet)

        freeze_after = snapshot_identity(fabric.snapshot())
        identity_stable = freeze_before == freeze_at_barrier == independent_at_barrier == freeze_after
        proof = {
            "all_alive_at_barrier": True,
            "distinct_os_pids": len(set(observed_pids)),
            "parent_child_pid_binding": set(observed_pids) == set(parent_pids),
            "same_snapshot_identity": len(
                {
                    (
                        int(markers[node_id]["generation"]),
                        int(markers[node_id]["state_epoch"]),
                        str(markers[node_id]["state_digest"]),
                    )
                    for node_id in node_ids
                }
            ) == 1,
            "all_transactions_open_at_barrier": all(
                markers[node_id].get("transaction_open_at_ready") is True
                for node_id in node_ids
            ),
            "all_hold_readonly_s1_fd_at_barrier": Path("/proc").is_dir()
            and all(readonly_fds[node_id] for node_id in node_ids),
            "writer_free_identity_stable": identity_stable,
            "process_intervals_overlap_release": all(
                int(markers[node_id]["started_ns"])
                <= released_ns
                <= exit_ns[node_id]
                for node_id in node_ids
            ),
            "ready_by_node": markers,
            "readonly_s1_fd_binding": readonly_fds,
            "freeze_identity_before": freeze_before,
            "freeze_identity_at_barrier": freeze_at_barrier,
            "independent_identity_at_barrier": independent_at_barrier,
            "freeze_identity_after": freeze_after,
            "observed_pids": sorted(observed_pids),
            "parent_launch_ns": parent_launch_ns,
            "released_ns": released_ns,
            "parent_observed_exit_ns": exit_ns,
        }
        return packets, proof
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
                try:
                    proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
        if fabric.con.in_transaction:
            fabric.con.execute("COMMIT")


class FusedFabric(MembershipBoundFabric):
    """Membership-bound exact-snapshot fabric with one atomic cohort admission path."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.con.executescript(
            """
            CREATE TABLE fused_cohort_admissions(
              cohort_id TEXT PRIMARY KEY,
              scope TEXT NOT NULL,
              coordinator_lease_id TEXT NOT NULL,
              start_generation INTEGER NOT NULL,
              start_epoch INTEGER NOT NULL,
              start_digest TEXT NOT NULL,
              start_membership_digest TEXT NOT NULL,
              member_count INTEGER NOT NULL,
              node_result_digests_json TEXT NOT NULL,
              envelope_digests_json TEXT NOT NULL,
              resulting_epoch INTEGER NOT NULL,
              summary_digest TEXT NOT NULL
            );
            CREATE TABLE fused_cohort_members(
              cohort_id TEXT NOT NULL,
              source_node_id TEXT NOT NULL,
              source_membership_id TEXT NOT NULL,
              producer_pid INTEGER NOT NULL,
              node_result_digest TEXT NOT NULL,
              envelope_digest TEXT NOT NULL,
              PRIMARY KEY(cohort_id,node_result_digest),
              UNIQUE(cohort_id,source_node_id),
              UNIQUE(cohort_id,source_membership_id),
              UNIQUE(cohort_id,producer_pid)
            );
            """
        )

    def membership_snapshot(self) -> dict[str, Any]:
        rows = tuple(
            dict(row)
            for row in self.con.execute(
                "SELECT membership_id,node_id,capability,generation,serial,valid,healthy "
                "FROM node_memberships WHERE valid=1 ORDER BY node_id,membership_id"
            )
        )
        return {"rows": rows, "digest": dg({"active_memberships": rows})}

    def make_envelope(
        self,
        packet: dict[str, Any],
        membership_id: str,
    ) -> dict[str, Any]:
        membership = self.con.execute(
            "SELECT membership_id,node_id,capability,generation,serial,valid,healthy "
            "FROM node_memberships WHERE membership_id=?",
            (membership_id,),
        ).fetchone()
        if membership is None:
            membership_receipt = None
        else:
            membership_receipt = dict(membership)
        core = {
            "schema": ENVELOPE_SCHEMA,
            "node_result_digest": packet["packet_digest"],
            "node_result": packet,
            "source_membership_id": membership_id,
            "membership_receipt": membership_receipt,
            "producer_pid": packet.get("producer_pid"),
        }
        return {**core, "envelope_digest": dg(core)}

    def _verify_node_result(
        self,
        packet: dict[str, Any],
        *,
        expected_identity: tuple[int, int, str],
        current_snapshot: Any,
    ) -> None:
        if packet.get("schema") != "NODE_RESULT/v1":
            raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
        if packet.get("source_kind") != "ORDINARY_NODE":
            raise FabricError("COHORT_SOURCE_KIND_INVALID")
        if packet.get("scope") != SCOPE:
            raise FabricError("COHORT_SCOPE_INVALID")
        if packet.get("s1_write_intent") is not False:
            raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")
        if (
            int(packet.get("generation", -1)),
            int(packet.get("state_epoch", -1)),
            str(packet.get("state_digest")),
        ) != expected_identity:
            raise FabricError("COHORT_MEMBER_SNAPSHOT_MISMATCH")
        if (
            int(packet.get("consumed_generation", -1)),
            int(packet.get("consumed_state_epoch", -1)),
            str(packet.get("consumed_state_digest")),
        ) != expected_identity:
            raise FabricError("CONSUMED_DECLARED_STATE_MISMATCH")
        core = {
            key: packet[key]
            for key in packet
            if key not in ("packet_digest", "s1_write_intent")
        }
        if packet.get("packet_digest") != dg(core):
            raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")

        payload = packet.get("payload")
        if not isinstance(payload, dict):
            raise FabricError("COHORT_PAYLOAD_INVALID")
        if int(packet.get("producer_pid", -1)) != int(payload.get("process_pid", -2)):
            raise FabricError("PRODUCER_PID_PAYLOAD_MISMATCH")
        task_id = payload.get("task_id")
        task = next(
            (task for task in current_snapshot.tasks if task["task_id"] == task_id),
            None,
        )
        task_digest = dg(task) if task is not None else dg(None)
        if packet.get("consumed_task_digest") != task_digest:
            raise FabricError("CONSUMED_TASK_DIGEST_MISMATCH")
        receipt_core = {
            "producer_pid": packet["producer_pid"],
            "source_node_id": packet["source_node_id"],
            "consumed_state_epoch": packet["consumed_state_epoch"],
            "consumed_state_digest": packet["consumed_state_digest"],
            "consumed_generation": packet["consumed_generation"],
            "consumed_task_digest": packet["consumed_task_digest"],
            "payload_digest": dg(payload),
        }
        if packet.get("read_receipt_digest") != dg(receipt_core):
            raise FabricError("READ_RECEIPT_DIGEST_MISMATCH")

    def _verify_envelope(
        self,
        envelope: dict[str, Any],
        *,
        expected_identity: tuple[int, int, str],
        current_snapshot: Any,
        proof: dict[str, Any],
    ) -> dict[str, Any]:
        if envelope.get("schema") != ENVELOPE_SCHEMA:
            raise FabricError("PROOF_ENVELOPE_SCHEMA_INVALID")
        packet = envelope.get("node_result")
        if not isinstance(packet, dict):
            raise FabricError("PROOF_ENVELOPE_PACKET_MISSING")
        if envelope.get("node_result_digest") != packet.get("packet_digest"):
            raise FabricError("PROOF_ENVELOPE_RESULT_DIGEST_MISMATCH")
        core = {
            key: envelope[key]
            for key in envelope
            if key != "envelope_digest"
        }
        if envelope.get("envelope_digest") != dg(core):
            raise FabricError("PROOF_ENVELOPE_DIGEST_MISMATCH")

        self._verify_node_result(
            packet,
            expected_identity=expected_identity,
            current_snapshot=current_snapshot,
        )
        membership_id = envelope.get("source_membership_id")
        membership_receipt = envelope.get("membership_receipt")
        if not isinstance(membership_id, str) or not membership_id:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_REQUIRED")
        if not isinstance(membership_receipt, dict):
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_UNKNOWN")
        if membership_receipt.get("membership_id") != membership_id:
            raise FabricError("MEMBERSHIP_RECEIPT_ID_MISMATCH")
        if membership_receipt.get("node_id") != packet.get("source_node_id"):
            raise FabricError("MEMBERSHIP_RECEIPT_NODE_MISMATCH")

        # Reuse the current monotonic membership authority gate without mutating the
        # original observation packet or its packet_digest.
        membership_probe = {
            "schema": "NODE_RESULT/v1",
            "source_node_id": packet["source_node_id"],
            "source_membership_id": membership_id,
        }
        self._verify_result_membership(membership_probe)
        active = self.active_membership(packet["source_node_id"])
        if any(
            membership_receipt.get(field) != active.get(field)
            for field in (
                "membership_id",
                "node_id",
                "capability",
                "generation",
                "serial",
                "valid",
                "healthy",
            )
        ):
            raise FabricError("MEMBERSHIP_RECEIPT_NOT_CURRENT")

        node_id = str(packet["source_node_id"])
        marker = proof["ready_by_node"].get(node_id)
        if marker is None:
            raise FabricError("COHORT_READY_BINDING_MISSING")
        if int(packet["producer_pid"]) != int(marker["pid"]):
            raise FabricError("COHORT_PID_PACKET_BINDING_MISMATCH")
        if packet["read_receipt_digest"] != marker["read_receipt_digest"]:
            raise FabricError("COHORT_READ_RECEIPT_MARKER_MISMATCH")
        marker_identity = (
            int(marker["generation"]),
            int(marker["state_epoch"]),
            str(marker["state_digest"]),
        )
        if marker_identity != expected_identity:
            raise FabricError("COHORT_READY_PACKET_SNAPSHOT_MISMATCH")
        return {
            "source_node_id": node_id,
            "source_membership_id": membership_id,
            "producer_pid": int(packet["producer_pid"]),
            "node_result_digest": str(packet["packet_digest"]),
            "envelope_digest": str(envelope["envelope_digest"]),
        }

    def derive_cohort_id(
        self,
        members: list[dict[str, Any]],
        *,
        lease: dict[str, Any],
        expected_identity: tuple[int, int, str],
        membership_digest: str,
    ) -> str:
        canonical = sorted(
            members,
            key=lambda member: (
                member["source_node_id"],
                member["node_result_digest"],
                member["source_membership_id"],
            ),
        )
        return "cohort-" + dg(
            {
                "schema": COHORT_SCHEMA,
                "scope": SCOPE,
                "coordinator_lease_id": lease["lease_id"],
                "starting_snapshot": expected_identity,
                "starting_membership_digest": membership_digest,
                "members": canonical,
            }
        )[:32]

    def atomic_fused_cohort_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        envelopes: list[dict[str, Any]],
        proof: dict[str, Any],
        expected_generation: int,
        expected_epoch: int,
        expected_digest: str,
        expected_membership_digest: str,
        expected_cohort_id: str,
    ) -> dict[str, Any]:
        if len(envelopes) != N:
            raise FabricError("COHORT_PACKET_COUNT_INVALID")
        required_proof = {
            "all_alive_at_barrier": proof.get("all_alive_at_barrier") is True,
            "ten_distinct_os_pids": proof.get("distinct_os_pids") == N,
            "parent_child_pid_binding": proof.get("parent_child_pid_binding") is True,
            "same_snapshot_identity": proof.get("same_snapshot_identity") is True,
            "all_transactions_open_at_barrier": proof.get("all_transactions_open_at_barrier") is True,
            "all_hold_readonly_s1_fd_at_barrier": proof.get("all_hold_readonly_s1_fd_at_barrier") is True,
            "writer_free_identity_stable": proof.get("writer_free_identity_stable") is True,
            "process_intervals_overlap_release": proof.get("process_intervals_overlap_release") is True,
        }
        failed_proof = [name for name, passed in required_proof.items() if not passed]
        if failed_proof:
            raise FabricError("PHYSICAL_COHORT_PROOF_FAILED:" + ",".join(sorted(failed_proof)))

        expected_identity = (expected_generation, expected_epoch, expected_digest)
        current_snapshot = self.snapshot()
        current_membership = self.membership_snapshot()

        members = [
            self._verify_envelope(
                envelope,
                expected_identity=expected_identity,
                current_snapshot=current_snapshot,
                proof=proof,
            )
            for envelope in envelopes
        ]
        if len({member["source_node_id"] for member in members}) != N:
            raise FabricError("COHORT_DUPLICATE_NODE_ID")
        if len({member["source_membership_id"] for member in members}) != N:
            raise FabricError("COHORT_DUPLICATE_MEMBERSHIP_ID")
        if len({member["producer_pid"] for member in members}) != N:
            raise FabricError("COHORT_DUPLICATE_PROCESS_IDENTITY")
        if len({member["node_result_digest"] for member in members}) != N:
            raise FabricError("COHORT_DUPLICATE_PACKET")
        if current_membership["digest"] != expected_membership_digest:
            raise FabricError("MEMBERSHIP_START_IDENTITY_STALE")

        cohort_id = self.derive_cohort_id(
            members,
            lease=lease,
            expected_identity=expected_identity,
            membership_digest=expected_membership_digest,
        )
        if cohort_id != expected_cohort_id:
            raise FabricError("COHORT_ID_BINDING_MISMATCH")

        canonical_members = sorted(
            members,
            key=lambda member: (
                member["source_node_id"],
                member["node_result_digest"],
                member["source_membership_id"],
            ),
        )
        existing = self.con.execute(
            "SELECT * FROM fused_cohort_admissions WHERE cohort_id=?",
            (cohort_id,),
        ).fetchone()
        if existing is not None:
            if (
                int(existing["start_generation"]) != expected_generation
                or int(existing["start_epoch"]) != expected_epoch
                or str(existing["start_digest"]) != expected_digest
                or str(existing["start_membership_digest"]) != expected_membership_digest
                or json.loads(existing["node_result_digests_json"])
                != [member["node_result_digest"] for member in canonical_members]
                or json.loads(existing["envelope_digests_json"])
                != [member["envelope_digest"] for member in canonical_members]
            ):
                raise FabricError("COHORT_REPLAY_BINDING_MISMATCH")
            return {
                "cohort_id": cohort_id,
                "replay": True,
                "state_delta": 0,
                "resulting_epoch": int(existing["resulting_epoch"]),
            }

        if snapshot_identity(current_snapshot) != expected_identity:
            raise FabricError("COHORT_START_SNAPSHOT_STALE")
        self._lease_row(lease, token, SCOPE)

        summary_payload = {
            "schema": SUMMARY_SCHEMA,
            "cohort_id": cohort_id,
            "member_count": N,
            "starting_snapshot": {
                "generation": expected_generation,
                "epoch": expected_epoch,
                "state_digest": expected_digest,
            },
            "starting_membership_digest": expected_membership_digest,
            "ordered_node_result_digests": [
                member["node_result_digest"] for member in canonical_members
            ],
            "ordered_envelope_digests": [
                member["envelope_digest"] for member in canonical_members
            ],
            "observation_relabelled_as_current": False,
            "transport_arrival_order_authority": False,
        }
        summary_digest = dg(summary_payload)

        self.con.execute("BEGIN IMMEDIATE")
        try:
            inside = self.snapshot()
            inside_membership = self.membership_snapshot()
            if snapshot_identity(inside) != expected_identity:
                raise FabricError("COHORT_CAS_FAILED")
            if inside_membership["digest"] != expected_membership_digest:
                raise FabricError("MEMBERSHIP_CAS_FAILED")
            self._lease_row(lease, token, SCOPE)

            scope_row = self.con.execute(
                "SELECT * FROM scopes WHERE scope=?", (SCOPE,)
            ).fetchone()
            if scope_row is None:
                raise FabricError("UNKNOWN_SCOPE")
            for member in canonical_members:
                if self.con.execute(
                    "SELECT 1 FROM admitted_results WHERE result_digest=?",
                    (member["node_result_digest"],),
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
            for member in canonical_members:
                self.con.execute(
                    "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                    (
                        member["node_result_digest"],
                        member["source_node_id"],
                        lease["lease_id"],
                        SCOPE,
                        new_epoch,
                    ),
                )
                self.con.execute(
                    "INSERT INTO fused_cohort_members VALUES(?,?,?,?,?,?)",
                    (
                        cohort_id,
                        member["source_node_id"],
                        member["source_membership_id"],
                        member["producer_pid"],
                        member["node_result_digest"],
                        member["envelope_digest"],
                    ),
                )
            self.con.execute(
                "INSERT INTO fused_cohort_admissions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    cohort_id,
                    SCOPE,
                    lease["lease_id"],
                    expected_generation,
                    expected_epoch,
                    expected_digest,
                    expected_membership_digest,
                    N,
                    cj([member["node_result_digest"] for member in canonical_members]),
                    cj([member["envelope_digest"] for member in canonical_members]),
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
            "canonical_truth": False,
            "effect_authority": False,
        }


def expect_error(fn: Any, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


def make_fixture(root: Path, label: str) -> dict[str, Any]:
    db = root / f"{label}.sqlite"
    barrier_root = root / f"{label}-barrier"
    barrier_root.mkdir(parents=True, exist_ok=False)
    fabric = FusedFabric(db)
    ids = [f"x{i:02d}" for i in range(1, N + 1)]
    memberships: dict[str, dict[str, Any]] = {}
    for node_id in ids:
        memberships[node_id] = fabric.runtime_register_node(node_id, "reason")
    fabric.seed_scope(SCOPE)
    for i in range(N):
        fabric.seed_task(f"t{i:02d}", SCOPE, 100 - i, "reason", {"q": i})
    lease, token = fabric.elect_coordinator(SCOPE)
    start = fabric.snapshot()
    membership_start = fabric.membership_snapshot()
    packets, proof = spawn_held_cohort(
        fabric,
        Path(__file__),
        db,
        ids,
        barrier_root,
    )
    envelopes = [
        fabric.make_envelope(packet, memberships[packet["source_node_id"]]["membership_id"])
        for packet in packets
    ]
    structural_members = [
        {
            "source_node_id": envelope["node_result"]["source_node_id"],
            "source_membership_id": envelope["source_membership_id"],
            "producer_pid": int(envelope["node_result"]["producer_pid"]),
            "node_result_digest": envelope["node_result_digest"],
            "envelope_digest": envelope["envelope_digest"],
        }
        for envelope in envelopes
    ]
    cohort_id = fabric.derive_cohort_id(
        structural_members,
        lease=lease,
        expected_identity=snapshot_identity(start),
        membership_digest=membership_start["digest"],
    )
    return {
        "fabric": fabric,
        "ids": ids,
        "memberships": memberships,
        "lease": lease,
        "token": token,
        "start": start,
        "membership_start": membership_start,
        "packets": packets,
        "envelopes": envelopes,
        "proof": proof,
        "cohort_id": cohort_id,
    }


def commit_fixture(fx: dict[str, Any], envelopes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    start = fx["start"]
    return fx["fabric"].atomic_fused_cohort_commit(
        lease=fx["lease"],
        token=fx["token"],
        envelopes=fx["envelopes"] if envelopes is None else envelopes,
        proof=fx["proof"],
        expected_generation=start.generation,
        expected_epoch=start.epoch,
        expected_digest=start.state_digest,
        expected_membership_digest=fx["membership_start"]["digest"],
        expected_cohort_id=fx["cohort_id"],
    )


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="trigger2-fused-grid10-") as td:
        root = Path(td)

        # Positive fused path and exact replay.
        fx = make_fixture(root, "positive")
        fabric: FusedFabric = fx["fabric"]
        try:
            original_packet_bytes = cj(fx["packets"])
            receipt = commit_fixture(fx)
            after = fabric.snapshot()
            replay = commit_fixture(fx)
            tests["P1_TEN_SIMULTANEOUS_DISTINCT_OS_PROCESSES"] = (
                fx["proof"]["distinct_os_pids"] == N
                and fx["proof"]["all_alive_at_barrier"] is True
                and fx["proof"]["parent_child_pid_binding"] is True
            )
            tests["P2_HELD_READONLY_EXACT_S1_TRANSACTIONS"] = (
                fx["proof"]["all_transactions_open_at_barrier"] is True
                and fx["proof"]["all_hold_readonly_s1_fd_at_barrier"] is True
                and fx["proof"]["writer_free_identity_stable"] is True
            )
            tests["P3_SAME_PHYSICAL_COHORT_ATOMICALLY_ADMITTED"] = (
                receipt["member_count"] == N
                and receipt["state_delta"] == 1
                and receipt["resulting_epoch"] == fx["start"].epoch + 1
                and after.epoch == fx["start"].epoch + 1
            )
            tests["P4_ORIGINAL_NODE_RESULT_DIGESTS_IMMUTABLE"] = (
                cj(fx["packets"]) == original_packet_bytes
                and {
                    row[0]
                    for row in fabric.con.execute(
                        "SELECT result_digest FROM admitted_results"
                    )
                }
                == {packet["packet_digest"] for packet in fx["packets"]}
            )
            tests["P5_MEMBERSHIP_AUTHORITY_SEPARATE_FROM_NODE_RESULT"] = all(
                "source_membership_id" not in packet for packet in fx["packets"]
            ) and all(
                envelope["source_membership_id"]
                == fx["memberships"][envelope["node_result"]["source_node_id"]]["membership_id"]
                for envelope in fx["envelopes"]
            )
            tests["P6_REPLAY_IDEMPOTENT_ZERO_SECOND_DELTA"] = (
                replay["replay"] is True
                and replay["state_delta"] == 0
                and fabric.snapshot().epoch == after.epoch
            )

            forward_id = fx["cohort_id"]
            reverse_members = [
                {
                    "source_node_id": envelope["node_result"]["source_node_id"],
                    "source_membership_id": envelope["source_membership_id"],
                    "producer_pid": int(envelope["node_result"]["producer_pid"]),
                    "node_result_digest": envelope["node_result_digest"],
                    "envelope_digest": envelope["envelope_digest"],
                }
                for envelope in reversed(fx["envelopes"])
            ]
            reverse_id = fabric.derive_cohort_id(
                reverse_members,
                lease=fx["lease"],
                expected_identity=snapshot_identity(fx["start"]),
                membership_digest=fx["membership_start"]["digest"],
            )
            tests["P7_TRANSPORT_ARRIVAL_PERMUTATION_HAS_NO_AUTHORITY"] = forward_id == reverse_id
        finally:
            fabric.close()

        # Membership re-registration changes deterministic membership authority without
        # pretending the S1 observation changed. The old cohort must fail.
        fx = make_fixture(root, "membership-stale")
        fabric = fx["fabric"]
        try:
            s1_before = fabric.snapshot()
            fabric.runtime_register_node("x01", "reason")
            s1_after = fabric.snapshot()
            tests["N1_REREGISTRATION_ORTHOGONAL_TO_S1_IDENTITY"] = s1_before == s1_after
            tests["N2_SUPERSEDED_MEMBERSHIP_COHORT_REJECTED"] = expect_error(
                lambda: commit_fixture(fx),
                "RESULT_SOURCE_MEMBERSHIP_INVALID",
            )
        finally:
            fabric.close()

        # A packet can be syntactically rehashed after lying about consumed state; the
        # consumed/declaration equality and read receipt must still fail closed.
        fx = make_fixture(root, "consumed-stale")
        fabric = fx["fabric"]
        try:
            envelopes = [dict(envelope) for envelope in fx["envelopes"]]
            target = dict(envelopes[0])
            packet = dict(target["node_result"])
            packet["consumed_state_digest"] = "0" * 64
            payload = packet["payload"]
            receipt_core = {
                "producer_pid": packet["producer_pid"],
                "source_node_id": packet["source_node_id"],
                "consumed_state_epoch": packet["consumed_state_epoch"],
                "consumed_state_digest": packet["consumed_state_digest"],
                "consumed_generation": packet["consumed_generation"],
                "consumed_task_digest": packet["consumed_task_digest"],
                "payload_digest": dg(payload),
            }
            packet["read_receipt_digest"] = dg(receipt_core)
            packet_core = {
                key: packet[key]
                for key in packet
                if key not in ("packet_digest", "s1_write_intent")
            }
            packet["packet_digest"] = dg(packet_core)
            target["node_result"] = packet
            target["node_result_digest"] = packet["packet_digest"]
            envelope_core = {key: target[key] for key in target if key != "envelope_digest"}
            target["envelope_digest"] = dg(envelope_core)
            envelopes[0] = target
            tests["N3_DECLARED_CURRENT_CONSUMED_STALE_REJECTED"] = expect_error(
                lambda: commit_fixture(fx, envelopes),
                "CONSUMED_DECLARED_STATE_MISMATCH",
            )
        finally:
            fabric.close()

        # Membership-id tamper with a recomputed envelope digest must fail on authority,
        # not merely on JSON integrity.
        fx = make_fixture(root, "membership-tamper")
        fabric = fx["fabric"]
        try:
            envelopes = [dict(envelope) for envelope in fx["envelopes"]]
            target = dict(envelopes[0])
            target["source_membership_id"] = fx["memberships"]["x02"]["membership_id"]
            target["membership_receipt"] = dict(
                fabric.active_membership("x02")
            )
            envelope_core = {key: target[key] for key in target if key != "envelope_digest"}
            target["envelope_digest"] = dg(envelope_core)
            envelopes[0] = target
            tests["N4_MEMBERSHIP_SUBSTITUTION_REJECTED"] = expect_error(
                lambda: commit_fixture(fx, envelopes),
                "MEMBERSHIP_RECEIPT_NODE_MISMATCH",
            )
        finally:
            fabric.close()

        # Dropping a member cannot be hidden by a valid remaining packet set.
        fx = make_fixture(root, "omitted")
        fabric = fx["fabric"]
        try:
            tests["N5_OMITTED_COHORT_MEMBER_REJECTED"] = expect_error(
                lambda: commit_fixture(fx, fx["envelopes"][:-1]),
                "COHORT_PACKET_COUNT_INVALID",
            )
        finally:
            fabric.close()

        # S1 mutation after observation invalidates the whole immutable cohort.
        fx = make_fixture(root, "stale-s1")
        fabric = fx["fabric"]
        try:
            fabric.seed_task("late", SCOPE, 1, "reason", {"late": True})
            tests["N6_STALE_START_S1_REJECTED"] = expect_error(
                lambda: commit_fixture(fx),
                "COHORT_MEMBER_SNAPSHOT_MISMATCH",
            )
        finally:
            fabric.close()

        # Invalid coordinator token must not be rescued by otherwise correct cohort proof.
        fx = make_fixture(root, "lease-token")
        fabric = fx["fabric"]
        try:
            old_token = fx["token"]
            fx["token"] = old_token + "-tampered"
            tests["N7_COORDINATOR_LEASE_BINDING_REJECTED"] = expect_error(
                lambda: commit_fixture(fx),
                "COORDINATOR_LEASE_BINDING_INVALID",
            )
        finally:
            fabric.close()

    passed = all(tests.values())
    return {
        "schema": SCHEMA,
        "pass": passed,
        "tests": tests,
        "claim_scope": "FUSED_PHYSICAL_GRID10_COMPONENT_SOURCE_CANDIDATE_ONLY",
        "contract": {
            "physical_cohort": "EXACT_TEN_SIMULTANEOUS_HELD_READONLY_S1_PROCESSES",
            "observation_identity": "IMMUTABLE_NODE_RESULT_PACKET_DIGEST",
            "consumed_snapshot": "READ_RECEIPT_BOUND",
            "membership_authority": "MONOTONIC_FABRIC_MEMBERSHIP_ID_SEPARATE_ENVELOPE",
            "fanin": "ONE_ATOMIC_COHORT_TRANSACTION_ONE_EPOCH_ADVANCE",
            "arrival_order_authority": False,
            "implicit_rebase": False,
            "canonical_truth_from_model": False,
            "effect_authority_from_model": False,
        },
        "credit_boundary": {
            "source_or_local_pass_is_runtime_credit": False,
            "physical_grid10_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "jspace_model_credit": 0,
            "accepted_dataset_tokens": 0,
            "training_credit": 0,
            "canonical_truth_credit": 0,
            "effect_authority_credit": 0,
        },
        "execution_authority": {
            "freeswarm_emergency_stop_must_remain_respected": True,
            "provider_execution_requested": False,
            "paid_execution_allowed": False,
        },
        "next_gate": (
            "Source-review this fused contract against current main and donor invariants; "
            "only after exact-current source acceptance and current authority reentry may a "
            "separately admitted non-provider exact-source executor be considered."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--ready-dir", type=Path)
    parser.add_argument("--release-file", type=Path)
    args = parser.parse_args()

    if args.node:
        if not args.db or not args.ready_dir or not args.release_file:
            raise SystemExit("child mode requires --db --ready-dir --release-file")
        return child_mode(args.db, args.node, args.ready_dir, args.release_file)

    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
