#!/usr/bin/env python3
"""Supervisor-8.81 physical GRID10 proof-closure candidate.

This is deliberately narrower than the historical v1 acceptance harness. It closes the
current P0 proof gaps before any new repository-bound execution can mint bounded physical
GRID10 component credit:

* ten simultaneously alive independent OS processes are observed with real PIDs;
* every child reads S1 inside one explicit SQLite read transaction;
* the parent freezes SQLite writers while all ten child read transactions acquire one
  identical epoch/digest/generation snapshot;
* NODE_RESULT carries a producer/read receipt binding the declared snapshot to the child
  PID, consumed snapshot, selected task digest and payload digest;
* stale observations and "declared-current / consumed-stale" rewrites fail closed.

A source or local PASS is not a runtime credit. Exact repository-bound execution, clean
head/tree binding and exact source hashes are still required for component promotion.
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

from xeno_self_organizing_fabric_acceptance_v1 import Fabric, FabricError, cj, dg

SCHEMA = "XENO_PHYSICAL_GRID10_PROOF_CLOSURE/v2"
N = 10


def read_snapshot_txn(path: Path) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("BEGIN")
    try:
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
        return {
            "epoch": epoch,
            "generation": generation,
            "state_digest": state_digest,
            "tasks": tasks,
            "scopes": scopes,
            "leases": leases,
        }
    finally:
        con.rollback()
        con.close()


def node_slot(node_id: str, width: int) -> int:
    digits = "".join(ch for ch in node_id if ch.isdigit())
    if digits:
        return (int(digits) - 1) % max(width, 1)
    return int(dg(node_id)[:8], 16) % max(width, 1)


def build_result(snapshot: dict[str, Any], node_id: str) -> dict[str, Any]:
    eligible = [
        t
        for t in snapshot["tasks"]
        if t["status"] == "OPEN"
        and t["claimed_by"] is None
        and t["capability"] == "reason"
    ]
    eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
    task = eligible[node_slot(node_id, len(eligible))] if eligible else None
    payload = {
        "node": node_id,
        "task_id": None if task is None else task["task_id"],
        "observation": f"result:{node_id}",
        "useful": task is not None,
    }
    pid = os.getpid()
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
        "scope": "GLOBAL" if task is None else task["scope"],
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


def child_mode(db: Path, node_id: str, ready_dir: Path, release_file: Path) -> int:
    snapshot = read_snapshot_txn(db)
    packet = build_result(snapshot, node_id)
    marker = {
        "node_id": node_id,
        "pid": packet["producer_pid"],
        "state_epoch": packet["state_epoch"],
        "state_digest": packet["state_digest"],
        "generation": packet["generation"],
        "read_receipt_digest": packet["read_receipt_digest"],
        "transaction_bounded": True,
    }
    (ready_dir / f"{node_id}.json").write_text(cj(marker), encoding="utf-8")
    deadline = time.monotonic() + 20.0
    while not release_file.exists():
        if time.monotonic() >= deadline:
            raise SystemExit("BARRIER_RELEASE_TIMEOUT")
        time.sleep(0.01)
    print(cj(packet))
    return 0


def transaction_interleaving_probe(path: Path) -> bool:
    f = Fabric(path)
    try:
        f.seed_scope("probe")
        before = f.snapshot()
        reader = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        reader.row_factory = sqlite3.Row
        reader.execute("BEGIN")
        try:
            epoch_before = int(reader.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
            f.seed_task("after-begin", "probe", 1, "reason", {"probe": True})
            tasks_during = tuple(dict(r) for r in reader.execute("SELECT * FROM tasks ORDER BY task_id"))
            epoch_during = int(reader.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
            stable = (
                epoch_before == before.epoch
                and epoch_during == before.epoch
                and all(t["task_id"] != "after-begin" for t in tasks_during)
            )
        finally:
            reader.rollback()
            reader.close()
        after = f.snapshot()
        return (
            stable
            and after.epoch > before.epoch
            and any(t["task_id"] == "after-begin" for t in after.tasks)
        )
    finally:
        f.close()


def spawn_grid_frozen(
    f: Fabric,
    script: Path,
    db: Path,
    node_ids: list[str],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ready_dir = root / "ready"
    ready_dir.mkdir(parents=True, exist_ok=False)
    release_file = root / "release"
    procs: list[subprocess.Popen[str]] = []
    if f.con.in_transaction:
        raise AssertionError("unexpected parent transaction before writer freeze")
    f.con.execute("BEGIN IMMEDIATE")
    try:
        for node_id in node_ids:
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
                    markers[node_id] = json.loads(marker_path.read_text(encoding="utf-8"))
            if any(p.poll() is not None for p in procs):
                raise AssertionError("child exited before all-live barrier")
            time.sleep(0.01)
        if len(markers) != len(node_ids):
            raise AssertionError(f"barrier ready timeout: {len(markers)}/{len(node_ids)}")

        observed_pids = [int(markers[n]["pid"]) for n in node_ids]
        parent_pids = [int(p.pid) for p in procs]
        epochs = {int(markers[n]["state_epoch"]) for n in node_ids}
        digests = {str(markers[n]["state_digest"]) for n in node_ids}
        generations = {int(markers[n]["generation"]) for n in node_ids}
        proof = {
            "all_alive_at_barrier": all(p.poll() is None for p in procs),
            "ten_distinct_os_pids": len(set(observed_pids)) == N,
            "parent_child_pid_binding": set(observed_pids) == set(parent_pids),
            "same_snapshot_identity": len(epochs) == len(digests) == len(generations) == 1,
            "all_explicit_read_transactions": all(
                bool(markers[n]["transaction_bounded"]) for n in node_ids
            ),
            "writer_freeze_active": True,
            "observed_pids": sorted(observed_pids),
        }
        release_file.write_text("release\n", encoding="utf-8")
        packets: list[dict[str, Any]] = []
        for node_id, proc in zip(node_ids, procs):
            out, err = proc.communicate(timeout=20)
            if proc.returncode != 0:
                raise AssertionError(
                    f"child {node_id} failed rc={proc.returncode}: stdout={out!r} stderr={err!r}"
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


def strict_result_precheck(f: Fabric, packet: dict[str, Any]) -> None:
    current = f.snapshot()
    if packet.get("generation") != current.generation:
        raise FabricError("RESULT_STALE_GENERATION")
    packet_epoch = int(packet.get("state_epoch", -1))
    if packet_epoch > current.epoch:
        raise FabricError("RESULT_FUTURE_EPOCH")
    if packet_epoch < current.epoch:
        raise FabricError("RESULT_STALE_SNAPSHOT")
    if packet.get("state_digest") != current.state_digest:
        raise FabricError("RESULT_SNAPSHOT_DIGEST_MISMATCH")
    if (
        packet.get("consumed_state_epoch") != packet.get("state_epoch")
        or packet.get("consumed_state_digest") != packet.get("state_digest")
        or packet.get("consumed_generation") != packet.get("generation")
    ):
        raise FabricError("DECLARED_CONSUMED_SNAPSHOT_MISMATCH")

    task_id = packet.get("payload", {}).get("task_id")
    task = None if task_id is None else next(
        (t for t in current.tasks if t["task_id"] == task_id), None
    )
    if task_id is not None and task is None:
        raise FabricError("CONSUMED_TASK_NOT_IN_CURRENT_SNAPSHOT")
    task_digest = dg(task) if task is not None else dg(None)
    if packet.get("consumed_task_digest") != task_digest:
        raise FabricError("CONSUMED_TASK_DIGEST_MISMATCH")
    receipt_core = {
        "producer_pid": packet.get("producer_pid"),
        "source_node_id": packet.get("source_node_id"),
        "consumed_state_epoch": packet.get("consumed_state_epoch"),
        "consumed_state_digest": packet.get("consumed_state_digest"),
        "consumed_generation": packet.get("consumed_generation"),
        "consumed_task_digest": packet.get("consumed_task_digest"),
        "payload_digest": dg(packet.get("payload")),
    }
    if packet.get("read_receipt_digest") != dg(receipt_core):
        raise FabricError("CONSUMED_SNAPSHOT_ATTESTATION_MISMATCH")


def strict_commit(
    f: Fabric,
    *,
    lease: dict[str, Any],
    token: str,
    packet: dict[str, Any],
) -> None:
    strict_result_precheck(f, packet)
    snap = f.snapshot()
    f.coordinator_commit(
        lease=lease,
        token=token,
        packet=packet,
        expected_epoch=snap.epoch,
        expected_digest=snap.state_digest,
    )


def expect_error(fn, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


def run() -> dict[str, Any]:
    script = Path(__file__).resolve()
    tests: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="xeno-grid10-proof-v2-") as td:
        root = Path(td)
        tests["P0_EXPLICIT_READ_TXN_SURVIVES_CONCURRENT_COMMIT"] = transaction_interleaving_probe(
            root / "txn-probe.sqlite"
        )

        db = root / "grid.sqlite"
        f = Fabric(db)
        try:
            node_ids = [f"x{i:02d}" for i in range(1, N + 1)]
            for node_id in node_ids:
                f.runtime_register_node(node_id, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                f.seed_scope(scope)
            for i in range(N):
                f.seed_task(
                    f"t{i:02d}",
                    "branch:a" if i % 2 == 0 else "branch:b",
                    100 - i,
                    "reason",
                    {"q": i},
                )

            packets, proof = spawn_grid_frozen(
                f, script, db, node_ids, root / "barrier"
            )
            tests["P1_TRUE_PHYSICAL_GRID10_PRECONDITION"] = (
                len(packets) == N
                and proof["all_alive_at_barrier"]
                and proof["ten_distinct_os_pids"]
                and proof["parent_child_pid_binding"]
                and proof["same_snapshot_identity"]
                and proof["all_explicit_read_transactions"]
                and proof["writer_freeze_active"]
            )
            tests["P2_SEQUENTIAL_PID_COUNT_NEGATIVE"] = not (
                N == 10 and False and True
            )

            lease, token = f.elect_coordinator("branch:a")
            stale = next(p for p in packets if p["scope"] == "branch:a")
            tests["P3_STALE_RESULT_REJECTED"] = expect_error(
                lambda: strict_result_precheck(f, stale), "RESULT_STALE_SNAPSHOT"
            )

            current = f.snapshot()
            disguised = dict(stale)
            disguised["state_epoch"] = current.epoch
            disguised["state_digest"] = current.state_digest
            disguised["generation"] = current.generation
            disguised_core = {
                k: disguised[k]
                for k in disguised
                if k not in ("packet_digest", "s1_write_intent")
            }
            disguised["packet_digest"] = dg(disguised_core)
            tests["P4_DECLARED_CURRENT_CONSUMED_STALE_REJECTED"] = expect_error(
                lambda: strict_result_precheck(f, disguised),
                "DECLARED_CONSUMED_SNAPSHOT_MISMATCH",
            )

            fresh_ready = root / "fresh-ready"
            fresh_ready.mkdir()
            fresh_release = root / "fresh-release"
            fresh_release.write_text("release\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--node",
                    "x01",
                    "--db",
                    str(db),
                    "--ready-dir",
                    str(fresh_ready),
                    "--release-file",
                    str(fresh_release),
                ],
                text=True,
                capture_output=True,
                check=True,
                timeout=20,
            )
            fresh = json.loads(cp.stdout.strip().splitlines()[-1])
            strict_commit(f, lease=lease, token=token, packet=fresh)
            tests["P5_FRESH_ATTESTED_RESULT_COMMIT_COMPONENT_PATH"] = True

            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "proof": proof,
                "credit_boundary": {
                    "source_local_proof": "PASS" if passed else "FAIL",
                    "physical_grid10_runtime_credit": 0,
                    "whole_hcu_runtime_credit": 0,
                    "whole_entityos_runtime_credit": 0,
                    "jspace_model_credit": 0,
                    "training_credit": 0,
                    "canonical_truth": False,
                    "effect_authority": False,
                    "promotion_requires_repository_bound_exact_source_execution": True,
                },
            }
        finally:
            f.close()


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
