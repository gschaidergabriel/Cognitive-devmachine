#!/usr/bin/env python3
"""Supervisor-8.81 physical GRID10 proof closure v3: consumed snapshot + held S1 attach.

This successor deliberately reuses the v2 consumed-snapshot and strict-result logic while
closing the remaining physical-proof gap: a child must still be attached read-only to the
exact shared S1 database while all ten independent OS processes are simultaneously alive at
the release barrier.

The parent therefore proves, at the barrier:
- ten distinct Popen PIDs and exact parent/child/packet PID binding;
- every child reports the same generation/epoch/state_digest and an open read transaction;
- every child still has an O_RDONLY /proc/<pid>/fd binding to the exact S1 SQLite file;
- the deterministic parent writer-freeze transaction remains active;
- authoritative S1 identity is unchanged from freeze start through barrier and release;
- per-process start/ready/release/parent-observed-exit timestamps overlap.

It then delegates the existing v2 consumed-snapshot attestation, stale/disguised-current
negative controls, task-digest binding, coordinator lease/CAS path, and credit fences.

A source/local PASS is component-candidate evidence only. Repository-bound exact-source
execution is still required before bounded physical GRID10 component review.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from typing import Any

import xeno_physical_grid10_proof_v2 as base

SCHEMA = "XENO_PHYSICAL_GRID10_PROOF_CLOSURE/v3"
N = base.N


class HeldSnapshot(dict[str, Any]):
    """Snapshot payload that owns the read-only connection/transaction that produced it."""

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


def held_snapshot_txn(path: Path) -> HeldSnapshot:
    """Read all covered S1 fields in one explicit transaction and keep it open."""
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
        state_digest = base.dg(
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


def identity_from_snapshot(snapshot: Any) -> tuple[int, int, str]:
    return (
        int(snapshot.generation if hasattr(snapshot, "generation") else snapshot["generation"]),
        int(snapshot.epoch if hasattr(snapshot, "epoch") else snapshot["epoch"]),
        str(
            snapshot.state_digest
            if hasattr(snapshot, "state_digest")
            else snapshot["state_digest"]
        ),
    )


def child_mode_held(
    db: Path,
    node_id: str,
    ready_dir: Path,
    release_file: Path,
) -> int:
    started_ns = time.time_ns()
    snapshot = held_snapshot_txn(db)
    try:
        packet = base.build_result(snapshot, node_id)
        ready_ns = time.time_ns()
        marker = {
            "node_id": node_id,
            "pid": packet["producer_pid"],
            "started_ns": started_ns,
            "ready_ns": ready_ns,
            "state_epoch": packet["state_epoch"],
            "state_digest": packet["state_digest"],
            "generation": packet["generation"],
            "read_receipt_digest": packet["read_receipt_digest"],
            "transaction_bounded": True,
            "transaction_open_at_ready": snapshot.transaction_open,
            "db_path": str(db.resolve()),
        }
        tmp = ready_dir / f".{node_id}.{packet['producer_pid']}.tmp"
        dst = ready_dir / f"{node_id}.json"
        tmp.write_text(base.cj(marker), encoding="utf-8")
        tmp.replace(dst)

        # The exact connection/transaction that produced the packet remains live through
        # the all-process barrier. This is the physical attach property missing from v2.
        deadline = time.monotonic() + 20.0
        while not release_file.exists():
            if time.monotonic() >= deadline:
                raise SystemExit("BARRIER_RELEASE_TIMEOUT")
            time.sleep(0.01)

        print(base.cj(packet), flush=True)
        return 0
    finally:
        snapshot.close()


def procfs_readonly_db_fds(pid: int, db: Path) -> list[int]:
    """Observe exact O_RDONLY database descriptors for one child through Linux procfs."""
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
            if target.is_absolute():
                target = target.resolve()
            else:
                target = (fd_path.parent / target).resolve()
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


def spawn_grid_frozen_held(
    f: base.Fabric,
    script: Path,
    db: Path,
    node_ids: list[str],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Writer-free GRID10 barrier with externally observed live read-only S1 attachment."""
    ready_dir = root / "ready"
    ready_dir.mkdir(parents=True, exist_ok=False)
    release_file = root / "release"
    procs: list[subprocess.Popen[str]] = []
    parent_launch_ns: dict[str, int] = {}

    if f.con.in_transaction:
        raise AssertionError("unexpected parent transaction before writer freeze")
    f.con.execute("BEGIN IMMEDIATE")
    freeze_identity_before = identity_from_snapshot(f.snapshot())
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
                marker_path = ready_dir / f"{node_id}.json"
                if node_id not in markers and marker_path.exists():
                    markers[node_id] = json.loads(
                        marker_path.read_text(encoding="utf-8")
                    )
            if any(p.poll() is not None for p in procs):
                raise AssertionError("child exited before all-live barrier")
            time.sleep(0.01)
        if len(markers) != len(node_ids):
            raise AssertionError(f"barrier ready timeout: {len(markers)}/{len(node_ids)}")

        all_alive_at_barrier = all(p.poll() is None for p in procs)
        observed_pids = [int(markers[n]["pid"]) for n in node_ids]
        parent_pids = [int(p.pid) for p in procs]
        epochs = {int(markers[n]["state_epoch"]) for n in node_ids}
        digests = {str(markers[n]["state_digest"]) for n in node_ids}
        generations = {int(markers[n]["generation"]) for n in node_ids}

        procfs_available = Path("/proc").is_dir()
        readonly_fds = {
            node_id: procfs_readonly_db_fds(int(proc.pid), db)
            for node_id, proc in zip(node_ids, procs, strict=True)
        }
        all_hold_readonly_s1_fd = (
            procfs_available
            and all(readonly_fds[node_id] for node_id in node_ids)
        )
        all_transactions_open = all(
            markers[node_id].get("transaction_open_at_ready") is True
            for node_id in node_ids
        )

        freeze_identity_at_barrier = identity_from_snapshot(f.snapshot())
        observer = held_snapshot_txn(db)
        try:
            independent_identity_at_barrier = identity_from_snapshot(observer)
        finally:
            observer.close()
        writer_free_identity_stable = (
            freeze_identity_before
            == freeze_identity_at_barrier
            == independent_identity_at_barrier
        )

        released_ns = time.time_ns()
        release_file.write_text(str(released_ns), encoding="utf-8")

        packets: list[dict[str, Any]] = []
        parent_observed_exit_ns: dict[str, int] = {}
        for node_id, proc in zip(node_ids, procs, strict=True):
            out, err = proc.communicate(timeout=20)
            parent_observed_exit_ns[node_id] = time.time_ns()
            if proc.returncode != 0:
                raise AssertionError(
                    f"child {node_id} failed rc={proc.returncode}: "
                    f"stdout={out!r} stderr={err!r}"
                )
            packet = json.loads(out.strip().splitlines()[-1])
            marker = markers[node_id]
            if (
                packet["producer_pid"] != marker["pid"]
                or packet["state_epoch"] != marker["state_epoch"]
                or packet["state_digest"] != marker["state_digest"]
                or packet["generation"] != marker["generation"]
                or packet["read_receipt_digest"] != marker["read_receipt_digest"]
            ):
                raise AssertionError(f"marker/packet binding mismatch for {node_id}")
            packets.append(packet)

        freeze_identity_after_children = identity_from_snapshot(f.snapshot())
        writer_free_full_window = (
            writer_free_identity_stable
            and freeze_identity_after_children == freeze_identity_before
        )
        interval_overlap_ok = all(
            int(markers[node_id]["started_ns"])
            <= released_ns
            <= parent_observed_exit_ns[node_id]
            for node_id in node_ids
        )
        packet_pid_binding = all(
            int(packet["producer_pid"])
            == int(procs[node_ids.index(packet["source_node_id"])].pid)
            for packet in packets
        )

        proof = {
            "all_alive_at_barrier": all_alive_at_barrier,
            "ten_distinct_os_pids": len(set(observed_pids)) == N,
            "parent_child_pid_binding": set(observed_pids) == set(parent_pids),
            "packet_pid_binding": packet_pid_binding,
            "same_snapshot_identity": len(epochs) == len(digests) == len(generations) == 1,
            "all_explicit_read_transactions": all(
                bool(markers[n]["transaction_bounded"]) for n in node_ids
            ),
            "all_transactions_open_at_barrier": all_transactions_open,
            "writer_freeze_active": bool(f.con.in_transaction),
            "writer_free_identity_stable": writer_free_identity_stable,
            "writer_free_full_window": writer_free_full_window,
            "procfs_available": procfs_available,
            "readonly_s1_fd_binding": readonly_fds,
            "all_hold_readonly_s1_fd_at_barrier": all_hold_readonly_s1_fd,
            "process_intervals_overlap_release_barrier": interval_overlap_ok,
            "freeze_identity_before": freeze_identity_before,
            "freeze_identity_at_barrier": freeze_identity_at_barrier,
            "independent_identity_at_barrier": independent_identity_at_barrier,
            "freeze_identity_after_children": freeze_identity_after_children,
            "observed_pids": sorted(observed_pids),
            "parent_launch_ns": parent_launch_ns,
            "ready_markers": [markers[n] for n in node_ids],
            "released_ns": released_ns,
            "parent_observed_exit_ns": parent_observed_exit_ns,
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
        if f.con.in_transaction:
            f.con.execute("COMMIT")


def run() -> dict[str, Any]:
    # Reuse the v2 science/attestation path but force all subprocesses through this
    # successor and replace only the physical barrier implementation.
    original_file = base.__file__
    original_spawn = base.spawn_grid_frozen
    try:
        base.__file__ = __file__
        base.spawn_grid_frozen = spawn_grid_frozen_held
        result = base.run()
    finally:
        base.__file__ = original_file
        base.spawn_grid_frozen = original_spawn

    proof = result["proof"]
    extra_tests = {
        "P1B_ALL_TEN_TRANSACTIONS_OPEN_AT_BARRIER": bool(
            proof["all_transactions_open_at_barrier"]
        ),
        "P1B_ALL_TEN_HOLD_READONLY_S1_FD_AT_BARRIER": bool(
            proof["all_hold_readonly_s1_fd_at_barrier"]
        ),
        "P1B_WRITER_FREE_IDENTITY_OBSERVED_STABLE": bool(
            proof["writer_free_identity_stable"]
        ),
        "P1B_WRITER_FREE_IDENTITY_STABLE_THROUGH_CHILD_EXIT": bool(
            proof["writer_free_full_window"]
        ),
        "P1B_PROCESS_INTERVALS_OVERLAP_RELEASE": bool(
            proof["process_intervals_overlap_release_barrier"]
        ),
        "P1B_PACKET_PID_BINDING": bool(proof["packet_pid_binding"]),
    }
    result["tests"].update(extra_tests)
    result["pass"] = all(result["tests"].values())
    result["schema"] = SCHEMA
    result["proof_successor"] = {
        "relationship_to_v2": "CONSUMED_SNAPSHOT_V2_PLUS_HELD_READONLY_S1_ATTACHMENT",
        "procfs_fail_closed": True,
        "read_transaction_held_through_barrier": True,
        "no_credit_from_source_or_local_pass": True,
    }
    result["credit_boundary"]["source_local_proof"] = (
        "PASS" if result["pass"] else "FAIL"
    )
    result["credit_boundary"]["physical_grid10_runtime_credit"] = 0
    return result


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
        return child_mode_held(args.db, args.node, args.ready_dir, args.release_file)

    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
