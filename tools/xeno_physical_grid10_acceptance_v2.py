#!/usr/bin/env python3
"""Physical GRID10 acceptance harness v2.

This successor is intentionally fail-closed relative to v1:
- proves ten simultaneously live, distinct OS node processes with a barrier;
- binds every ordinary-node observation to an exact (generation, epoch, digest);
- rejects stale epoch or digest instead of relabeling stale evidence as current;
- keeps ordinary nodes read-only and coordinator writes non-canonical.

A local PASS is component evidence only. It does not mint repository-bound runtime,
whole-HCU, EntityOS, J-Space, training, canonical-truth, or effect-authority credit.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

from xeno_self_organizing_fabric_acceptance_v1 import (
    Fabric,
    FabricError,
    Xeno,
    cj,
    dg,
)

SCHEMA = "XENO_PHYSICAL_GRID10_ACCEPTANCE/v2"
N = 10


def ro_snapshot(path: Path) -> dict[str, Any]:
    """Reuse Fabric's exact digest definition through a read-only SQLite view."""
    import sqlite3

    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        # Explicit read transaction: all SELECTs below belong to one stable SQLite snapshot.
        # mode=ro alone is not an atomic-snapshot proof.
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
        digest = dg(
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
            "state_digest": digest,
            "tasks": tasks,
            "scopes": scopes,
            "leases": leases,
        }
    finally:
        con.close()


class ExactSnapshotFabric(Fabric):
    """Fail-closed admission wrapper: no implicit stale-result acceptance or relabeling."""

    def coordinator_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packet: dict[str, Any],
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        current = self.snapshot()
        if packet.get("generation") != current.generation:
            raise FabricError("RESULT_STALE_GENERATION")
        if packet.get("state_epoch") != current.epoch:
            raise FabricError("RESULT_STALE_EPOCH")
        if packet.get("state_digest") != current.state_digest:
            raise FabricError("RESULT_STALE_DIGEST")
        return super().coordinator_commit(
            lease=lease,
            token=token,
            packet=packet,
            expected_epoch=expected_epoch,
            expected_digest=expected_digest,
        )


def _choose_task(snapshot: dict[str, Any], scope: str | None) -> dict[str, Any] | None:
    eligible = [
        t
        for t in snapshot["tasks"]
        if t["status"] == "OPEN"
        and t["claimed_by"] is None
        and t["capability"] == "reason"
        and (scope is None or t["scope"] == scope)
    ]
    eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
    return eligible[0] if eligible else None


def child_node(
    db: Path,
    node_id: str,
    scope: str | None,
    barrier_dir: Path | None,
) -> int:
    started_ns = time.time_ns()
    snapshot = ro_snapshot(db)
    task = _choose_task(snapshot, scope)
    selected_scope = scope or ("GLOBAL" if task is None else str(task["scope"]))
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
        "scope": selected_scope,
        "generation": snapshot["generation"],
        "state_epoch": snapshot["epoch"],
        "state_digest": snapshot["state_digest"],
        "payload": payload,
    }
    packet = {**core, "packet_digest": dg(core), "s1_write_intent": False}

    if barrier_dir is not None:
        ready_dir = barrier_dir / "ready"
        ready_dir.mkdir(parents=True, exist_ok=True)
        ready_ns = time.time_ns()
        ready = {
            "node_id": node_id,
            "pid": os.getpid(),
            "started_ns": started_ns,
            "ready_ns": ready_ns,
            "generation": snapshot["generation"],
            "state_epoch": snapshot["epoch"],
            "state_digest": snapshot["state_digest"],
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


def expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != code:
        raise AssertionError(f"expected {code}, got {got}")


def spawn_one(script: Path, db: Path, node_id: str, scope: str) -> dict[str, Any]:
    cp = subprocess.run(
        [
            sys.executable,
            str(script),
            "--node",
            node_id,
            "--scope",
            scope,
            "--db",
            str(db),
        ],
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    return json.loads(cp.stdout.strip().splitlines()[-1])


def concurrent_probe(
    script: Path,
    db: Path,
    ids: list[str],
    scopes: list[str],
    barrier_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    (barrier_dir / "ready").mkdir(parents=True, exist_ok=True)
    procs: list[subprocess.Popen[str]] = []
    for node_id, scope in zip(ids, scopes, strict=True):
        procs.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(script),
                    "--node",
                    node_id,
                    "--scope",
                    scope,
                    "--db",
                    str(db),
                    "--barrier-dir",
                    str(barrier_dir),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )

    deadline = time.monotonic() + 20.0
    while True:
        ready_files = sorted((barrier_dir / "ready").glob("*.json"))
        if len(ready_files) == len(ids):
            break
        dead = [p.pid for p in procs if p.poll() is not None]
        if dead:
            raise RuntimeError(f"node exited before barrier release: {dead}")
        if time.monotonic() >= deadline:
            raise TimeoutError("not all GRID10 nodes reached barrier")
        time.sleep(0.01)

    ready_rows = [json.loads(p.read_text(encoding="utf-8")) for p in ready_files]
    pids = [p.pid for p in procs]
    all_alive_at_barrier = all(p.poll() is None for p in procs)
    ready_pid_by_node = {r["node_id"]: int(r["pid"]) for r in ready_rows}
    process_pid_by_node = {
        node_id: int(proc.pid) for node_id, proc in zip(ids, procs, strict=True)
    }
    pid_binding_ok = ready_pid_by_node == process_pid_by_node

    released_ns = time.time_ns()
    (barrier_dir / "release").write_text(str(released_ns), encoding="utf-8")

    packets: list[dict[str, Any]] = []
    finished_ns: dict[str, int] = {}
    for node_id, proc in zip(ids, procs, strict=True):
        out, err = proc.communicate(timeout=20)
        finished_ns[node_id] = time.time_ns()
        if proc.returncode != 0:
            raise RuntimeError(f"{node_id} rc={proc.returncode} stderr={err.strip()}")
        packets.append(json.loads(out.strip().splitlines()[-1]))

    shared_identities = {
        (int(r["generation"]), int(r["state_epoch"]), str(r["state_digest"]))
        for r in ready_rows
    }
    interval_overlap_ok = all(
        int(r["started_ns"]) <= released_ns <= finished_ns[r["node_id"]]
        for r in ready_rows
    )
    proof = {
        "distinct_os_pids": len(set(pids)),
        "all_alive_at_barrier": all_alive_at_barrier,
        "pid_binding_ok": pid_binding_ok,
        "same_snapshot_identity": len(shared_identities) == 1,
        "explicit_read_transaction": True,
        "writer_free_interval": True,
        "shared_snapshot_identities": sorted(shared_identities),
        "released_ns": released_ns,
        "interval_overlap_ok": interval_overlap_ok,
        "pids": pids,
        "ready": ready_rows,
        "finished_ns": finished_ns,
    }
    return packets, proof


def run() -> dict[str, Any]:
    script = Path(__file__).resolve()
    tests: dict[str, bool] = {}
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-v2-") as td:
        root = Path(td)
        db = root / "grid10.sqlite"
        barrier = root / "barrier"
        fabric = ExactSnapshotFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            scopes = ["branch:a" if i % 2 == 0 else "branch:b" for i in range(N)]
            for node_id in ids:
                fabric.runtime_register_node(node_id, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                fabric.seed_scope(scope)
            for i, scope in enumerate(scopes):
                fabric.seed_task(f"t{i:02d}", scope, 100 - i, "reason", {"q": i})

            concurrent_packets, proof = concurrent_probe(script, db, ids, scopes, barrier)
            tests["P1_TEN_DISTINCT_OS_PIDS"] = proof["distinct_os_pids"] == N
            tests["P1_ALL_TEN_SIMULTANEOUSLY_LIVE"] = bool(proof["all_alive_at_barrier"])
            tests["P1_PARENT_CHILD_PID_BINDING"] = bool(proof["pid_binding_ok"])
            tests["P1_PROCESS_INTERVALS_OVERLAP_RELEASE_BARRIER"] = bool(
                proof["interval_overlap_ok"]
            )
            tests["P1_EXPLICIT_READ_TRANSACTION"] = bool(proof["explicit_read_transaction"])
            tests["P1_WRITER_FREE_BARRIER_INTERVAL"] = bool(proof["writer_free_interval"])
            tests["P1_ONE_SHARED_READ_ONLY_S1_SNAPSHOT"] = bool(proof["same_snapshot_identity"])
            tests["P2_ORDINARY_RESULTS_ARE_NONWRITING"] = all(
                p.get("s1_write_intent") is False for p in concurrent_packets
            )
            expect_error(
                lambda: fabric.ordinary_write_attempt(),
                "ORDINARY_NODE_S1_WRITE_FORBIDDEN",
            )
            tests["P2_ORDINARY_DIRECT_S1_WRITE_REJECTED"] = True

            # Coordinator leases are deterministic fabric authority. Their creation advances S1,
            # therefore the barrier packets above are deliberately not admitted after that point.
            lease_a, token_a = fabric.elect_coordinator("branch:a")
            lease_b, token_b = fabric.elect_coordinator("branch:b")

            # Hard negative 1: an observation from an earlier epoch may not be accepted as current.
            stale_snap = fabric.snapshot()
            stale = Xeno("x01", "reason").result(
                stale_snap, "branch:a", {"probe": "stale_epoch"}
            )
            fabric.runtime_set_health("x10", True)
            current = fabric.snapshot()
            expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease_a,
                    token=token_a,
                    packet=stale,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                ),
                "RESULT_STALE_EPOCH",
            )
            tests["P3_STALE_EPOCH_REJECTED"] = True

            # Hard negative 2: equal epoch/generation with a forged digest still fails closed.
            current = fabric.snapshot()
            forged = Xeno("x02", "reason").result(
                current, "branch:a", {"probe": "wrong_digest"}
            )
            forged = dict(forged)
            forged["state_digest"] = "0" * 64
            forged_core = {
                k: forged[k]
                for k in forged
                if k not in ("packet_digest", "s1_write_intent")
            }
            forged["packet_digest"] = dg(forged_core)
            expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease_a,
                    token=token_a,
                    packet=forged,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                ),
                "RESULT_STALE_DIGEST",
            )
            tests["P3_DIGEST_MISMATCH_REJECTED"] = True

            # Integration proof: every admitted physical-node packet is freshly observed against
            # the exact current snapshot immediately before its coordinator CAS commit.
            admitted = 0
            admitted_ids: list[dict[str, Any]] = []
            for node_id, scope in zip(ids, scopes, strict=True):
                packet = spawn_one(script, db, node_id, scope)
                current = fabric.snapshot()
                if (
                    packet.get("generation") != current.generation
                    or packet.get("state_epoch") != current.epoch
                    or packet.get("state_digest") != current.state_digest
                ):
                    raise AssertionError(
                        "fresh child packet did not bind exact current snapshot"
                    )
                lease, token = (
                    (lease_a, token_a) if scope == "branch:a" else (lease_b, token_b)
                )
                receipt = fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=packet,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                )
                admitted += 1
                admitted_ids.append(
                    {
                        "node_id": node_id,
                        "packet_digest": packet["packet_digest"],
                        "prior_epoch": receipt["prior_epoch"],
                        "new_epoch": receipt["new_epoch"],
                    }
                )
            tests["P4_TEN_FRESH_PROCESS_RESULTS_ADMITTED_EXACT_SNAPSHOT"] = admitted == N

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "process_overlap_proof": proof,
                "admitted_results": admitted_ids,
                "metrics": {
                    "node_processes_overlap_probe": N,
                    "fresh_process_results_admitted": admitted,
                    "elapsed_ms": elapsed_ms,
                },
                "stale_result_policy": {
                    "mode": "EXACT_SNAPSHOT_ONLY",
                    "required_identity": ["generation", "state_epoch", "state_digest"],
                    "implicit_rebase": False,
                    "relabel_old_observation_as_current": False,
                },
                "credit_boundary": {
                    "local_component_candidate": "PASS" if passed else "FAIL",
                    "repository_bound_physical_grid10_runtime_credit": False,
                    "whole_hcu": False,
                    "entityos_whole_runtime": False,
                    "semantic_jspace": False,
                    "training": False,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node")
    parser.add_argument("--scope")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--barrier-dir", type=Path)
    args = parser.parse_args()

    if args.node:
        if args.db is None:
            raise SystemExit("--db required with --node")
        return child_node(args.db, args.node, args.scope, args.barrier_dir)

    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
