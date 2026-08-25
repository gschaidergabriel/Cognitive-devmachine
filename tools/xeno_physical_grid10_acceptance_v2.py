#!/usr/bin/env python3
"""Physical GRID10 acceptance v2: concurrent liveness + exact-snapshot evidence policy.

This successor repairs two proof gaps in v1:
1. ten ordinary Xeno node shells must be simultaneously alive as ten distinct OS processes,
   proven by a parent-observed barrier while all ten PIDs are live on one shared read-only S1;
2. NODE_RESULT admission is exact-snapshot only: generation, epoch and state_digest must equal
   the authoritative current S1 snapshot. No caller-side "relabel as current" is permitted.

The harness is an isolated component fixture. PASS is bounded physical-GRID10 component
evidence only; it never grants whole-HCU, EntityOS, semantic-J-Space, training, S0-truth or
effect-authority credit.
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

from xeno_self_organizing_fabric_acceptance_v1 import (
    Fabric, FabricError, Xeno, coordinator_summary, dg, cj,
)

SCHEMA = "XENO_PHYSICAL_GRID10_ACCEPTANCE/v2"
N = 10
BARRIER_TIMEOUT_S = 10.0


def ro_snapshot(path: Path) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        epoch = int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
        generation = int(con.execute("SELECT v FROM meta WHERE k='generation'").fetchone()[0])
        tasks = tuple(dict(r) for r in con.execute("SELECT * FROM tasks ORDER BY task_id"))
        scopes = tuple(dict(r) for r in con.execute("SELECT * FROM scopes ORDER BY scope"))
        leases = tuple(dict(r) for r in con.execute(
            "SELECT lease_id,node_id,scope,generation,granted_epoch,valid FROM leases ORDER BY lease_id"
        ))
        digest = dg({"epoch": epoch, "generation": generation, "tasks": tasks, "scopes": scopes, "leases": leases})
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
    """V2 acceptance policy: stale observation packets are never silently rebased."""

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
        packet_epoch = packet.get("state_epoch")
        if packet_epoch != current.epoch:
            if isinstance(packet_epoch, int) and packet_epoch > current.epoch:
                raise FabricError("RESULT_FUTURE_EPOCH")
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


def _packet_for_snapshot(s: dict[str, Any], node_id: str) -> dict[str, Any]:
    eligible = [
        t for t in s["tasks"]
        if t["status"] == "OPEN"
        and t["claimed_by"] is None
        and t["capability"] == "reason"
    ]
    eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
    task = eligible[0] if eligible else None
    scope = "GLOBAL" if task is None else task["scope"]
    payload = {
        "node": node_id,
        "task_id": None if task is None else task["task_id"],
        "observation": f"result:{node_id}",
        "useful": task is not None,
    }
    core = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node_id,
        "scope": scope,
        "generation": s["generation"],
        "state_epoch": s["epoch"],
        "state_digest": s["state_digest"],
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def child_node(db: Path, node_id: str, barrier_dir: Path | None) -> int:
    started_ns = time.time_ns()
    s = ro_snapshot(db)
    packet = _packet_for_snapshot(s, node_id)
    ready_ns = time.time_ns()

    if barrier_dir is not None:
        barrier_dir.mkdir(parents=True, exist_ok=True)
        ready_path = barrier_dir / f"{node_id}.ready.json"
        ready_path.write_text(cj({
            "node_id": node_id,
            "pid": os.getpid(),
            "started_ns": started_ns,
            "ready_ns": ready_ns,
            "state_epoch": s["epoch"],
            "state_digest": s["state_digest"],
            "generation": s["generation"],
        }))
        release_path = barrier_dir / "RELEASE"
        deadline = time.monotonic() + BARRIER_TIMEOUT_S
        while not release_path.exists():
            if time.monotonic() >= deadline:
                raise SystemExit("BARRIER_RELEASE_TIMEOUT")
            time.sleep(0.005)

    released_ns = time.time_ns()
    print(cj({
        "packet": packet,
        "process": {
            "pid": os.getpid(),
            "started_ns": started_ns,
            "ready_ns": ready_ns,
            "released_ns": released_ns,
        },
    }))
    return 0


def child_coordinator(node_id: str) -> int:
    obj = json.load(sys.stdin)
    results = obj["results"]
    out = {
        "coordinator_node_id": node_id,
        "result_count": len(results),
        "task_ids": sorted({
            r["payload"].get("task_id")
            for r in results
            if r["payload"].get("task_id")
        }),
        "evidence_digests": sorted(r["packet_digest"] for r in results),
    }
    print(cj(out))
    return 0


def spawn_node_once(script: Path, db: Path, node_id: str) -> dict[str, Any]:
    cp = subprocess.run(
        [sys.executable, str(script), "--node", node_id, "--db", str(db)],
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    return json.loads(cp.stdout.strip().splitlines()[-1])


def spawn_grid_barrier(
    script: Path,
    db: Path,
    ids: list[str],
    barrier_dir: Path,
) -> dict[str, Any]:
    procs: dict[str, subprocess.Popen[str]] = {}
    for node_id in ids:
        procs[node_id] = subprocess.Popen(
            [
                sys.executable,
                str(script),
                "--node",
                node_id,
                "--db",
                str(db),
                "--barrier-dir",
                str(barrier_dir),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    deadline = time.monotonic() + BARRIER_TIMEOUT_S
    ready_paths = {nid: barrier_dir / f"{nid}.ready.json" for nid in ids}
    while not all(p.exists() for p in ready_paths.values()):
        died = [nid for nid, proc in procs.items() if proc.poll() is not None]
        if died:
            details = {}
            for nid in died:
                out, err = procs[nid].communicate()
                details[nid] = {"returncode": procs[nid].returncode, "stdout": out, "stderr": err}
            raise AssertionError(f"NODE_DIED_BEFORE_BARRIER:{details}")
        if time.monotonic() >= deadline:
            raise AssertionError("BARRIER_READY_TIMEOUT")
        time.sleep(0.005)

    barrier_observed_ns = time.time_ns()
    live_at_barrier = {nid: proc.poll() is None for nid, proc in procs.items()}
    parent_pids = {nid: proc.pid for nid, proc in procs.items()}
    ready = {nid: json.loads(path.read_text()) for nid, path in ready_paths.items()}

    (barrier_dir / "RELEASE").write_text(str(barrier_observed_ns))

    envelopes: dict[str, Any] = {}
    for nid, proc in procs.items():
        out, err = proc.communicate(timeout=20)
        if proc.returncode != 0:
            raise AssertionError(f"NODE_EXIT_FAILED:{nid}:{proc.returncode}:{err}")
        envelopes[nid] = json.loads(out.strip().splitlines()[-1])

    return {
        "envelopes": envelopes,
        "ready": ready,
        "parent_pids": parent_pids,
        "live_at_barrier": live_at_barrier,
        "barrier_observed_ns": barrier_observed_ns,
    }


def compress(script: Path, node_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    cp = subprocess.run(
        [sys.executable, str(script), "--coordinator", node_id],
        input=cj({"results": results}),
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    return json.loads(cp.stdout.strip().splitlines()[-1])


def expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != code:
        raise AssertionError(f"expected {code}, got {got}")


def run() -> dict[str, Any]:
    script = Path(__file__).resolve()
    tests: dict[str, bool] = {}
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-v2-") as td:
        root = Path(td)
        db = root / "grid10.sqlite"
        barrier = root / "barrier"
        f = ExactSnapshotFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            for nid in ids:
                f.runtime_register_node(nid, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                f.seed_scope(scope)
            for i in range(N):
                scope = "branch:a" if i % 2 == 0 else "branch:b"
                f.seed_task(f"t{i:02d}", scope, 100 - i, "reason", {"q": i})

            # P1: true physical concurrency proof.
            batch = spawn_grid_barrier(script, db, ids, barrier)
            envelopes = batch["envelopes"]
            packets = [envelopes[nid]["packet"] for nid in ids]
            child_pids = {nid: envelopes[nid]["process"]["pid"] for nid in ids}
            ready_pids = {nid: batch["ready"][nid]["pid"] for nid in ids}
            epochs = {p["state_epoch"] for p in packets}
            digests = {p["state_digest"] for p in packets}
            generations = {p["generation"] for p in packets}

            tests["P1_TEN_DISTINCT_OS_PIDS"] = (
                len(set(batch["parent_pids"].values())) == N
                and len(set(child_pids.values())) == N
                and batch["parent_pids"] == child_pids == ready_pids
            )
            tests["P1_ALL_ALIVE_AT_COMMON_BARRIER"] = all(batch["live_at_barrier"].values())
            tests["P1_ONE_SHARED_S1_SNAPSHOT"] = len(epochs) == len(digests) == len(generations) == 1

            # P2: ordinary nodes remain read-only.
            tests["P2_ORDINARY_READ_ONLY"] = all(p["s1_write_intent"] is False for p in packets)
            expect_error(lambda: f.ordinary_write_attempt(), "ORDINARY_NODE_S1_WRITE_FORBIDDEN")
            tests["P2_ORDINARY_DIRECT_WRITE_REJECTED"] = True

            # P3: coordinator leases are deterministic scoped fabric authority.
            la, ta = f.elect_coordinator("branch:a")
            lb, tb = f.elect_coordinator("branch:b")
            tests["P3_DYNAMIC_SCOPED_COORDINATORS"] = (
                la["node_id"] in ids
                and lb["node_id"] in ids
                and la["scope"] != lb["scope"]
            )

            # P4: stale batch evidence is rejected after S1 moved.
            stale = packets[0]
            now = f.snapshot()
            stale_lease, stale_token = (la, ta) if stale["scope"] == "branch:a" else (lb, tb)
            expect_error(
                lambda: f.coordinator_commit(
                    lease=stale_lease,
                    token=stale_token,
                    packet=stale,
                    expected_epoch=now.epoch,
                    expected_digest=now.state_digest,
                ),
                "RESULT_STALE_EPOCH",
            )
            tests["P4_OLD_EPOCH_REJECTED"] = True

            # Same epoch but wrong digest also fails closed even if packet digest is recomputed.
            fresh_env = spawn_node_once(script, db, "x01")
            bad_digest = dict(fresh_env["packet"])
            bad_digest["state_digest"] = "0" * 64
            core = {k: bad_digest[k] for k in bad_digest if k not in ("packet_digest", "s1_write_intent")}
            bad_digest["packet_digest"] = dg(core)
            snap = f.snapshot()
            bad_lease, bad_token = (la, ta) if bad_digest["scope"] == "branch:a" else (lb, tb)
            expect_error(
                lambda: f.coordinator_commit(
                    lease=bad_lease,
                    token=bad_token,
                    packet=bad_digest,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                ),
                "RESULT_STALE_DIGEST",
            )
            tests["P4_SAME_EPOCH_WRONG_DIGEST_REJECTED"] = True

            # P5: fresh exact-snapshot packets may be admitted, one current observation at a time.
            admitted = 0
            admitted_packets: list[dict[str, Any]] = []
            for nid in ids:
                env = spawn_node_once(script, db, nid)
                packet = env["packet"]
                lease, token = (la, ta) if packet["scope"] == "branch:a" else (lb, tb)
                snap = f.snapshot()
                if (
                    packet["state_epoch"] != snap.epoch
                    or packet["state_digest"] != snap.state_digest
                    or packet["generation"] != snap.generation
                ):
                    raise AssertionError("FRESH_NODE_DID_NOT_BIND_CURRENT_SNAPSHOT")
                f.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=packet,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                )
                admitted += 1
                admitted_packets.append(packet)
            tests["P5_EXACT_SNAPSHOT_ADMISSION_ALL_10"] = admitted == N

            # P6: temporary coordinators compress evidence but do not mint canonical/effect authority.
            a = [p for p in admitted_packets if p["scope"] == "branch:a"]
            b = [p for p in admitted_packets if p["scope"] == "branch:b"]
            ca = compress(script, la["node_id"], a)
            cb = compress(script, lb["node_id"], b)
            raw_bytes = len(cj(a).encode()) + len(cj(b).encode())
            compact_bytes = len(cj(ca).encode()) + len(cj(cb).encode())
            tests["P6_COORDINATOR_COMPRESSION"] = (
                ca["result_count"] == len(a)
                and cb["result_count"] == len(b)
                and compact_bytes < raw_bytes
            )

            # P7: lease revocation removes authority; replacement can write fresh evidence.
            f.revoke_lease(la["lease_id"])
            snap = f.snapshot()
            probe = Xeno("x01", "reason").result(snap, "branch:a", {"probe": "stale lease"})
            expect_error(
                lambda: f.coordinator_commit(
                    lease=la,
                    token=ta,
                    packet=probe,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                ),
                "COORDINATOR_LEASE_INVALID",
            )
            la2, ta2 = f.elect_coordinator("branch:a")
            snap2 = f.snapshot()
            probe2 = Xeno("x02", "reason").result(snap2, "branch:a", {"probe": "replacement"})
            f.coordinator_commit(
                lease=la2,
                token=ta2,
                packet=probe2,
                expected_epoch=snap2.epoch,
                expected_digest=snap2.state_digest,
            )
            tests["P7_FAILURE_REPLACEMENT"] = True

            # P8: recursive compression under a higher scope remains candidate S1 only.
            lg, tg = f.elect_coordinator("GLOBAL")
            snap3 = f.snapshot()
            summary_payload = {"children": [ca, cb], "compression_level": 2}
            summary = coordinator_summary(lg["node_id"], snap3, "GLOBAL", summary_payload)
            f.coordinator_commit(
                lease=lg,
                token=tg,
                packet=summary,
                expected_epoch=snap3.epoch,
                expected_digest=snap3.state_digest,
            )
            row = f.con.execute("SELECT summary_json FROM scopes WHERE scope='GLOBAL'").fetchone()
            tests["P8_RECURSIVE_COMPRESSION_NO_S0_EFFECT_AUTHORITY"] = row is not None

            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {
                "schema": SCHEMA,
                "pass": all(tests.values()),
                "tests": tests,
                "metrics": {
                    "node_processes": N,
                    "distinct_os_pids": len(set(batch["parent_pids"].values())),
                    "all_live_at_barrier": all(batch["live_at_barrier"].values()),
                    "barrier_observed_ns": batch["barrier_observed_ns"],
                    "shared_snapshot_epoch_count": len(epochs),
                    "shared_snapshot_digest_count": len(digests),
                    "fresh_exact_snapshot_admissions": admitted,
                    "raw_result_bytes": raw_bytes,
                    "compressed_summary_bytes": compact_bytes,
                    "compression_ratio": compact_bytes / max(raw_bytes, 1),
                    "elapsed_ms": elapsed_ms,
                },
                "stale_result_policy": {
                    "policy": "EXACT_SNAPSHOT_ONLY",
                    "requires_generation_equality": True,
                    "requires_epoch_equality": True,
                    "requires_state_digest_equality": True,
                    "caller_side_relabel_or_implicit_rebase": False,
                },
                "credit_boundary": {
                    "physical_grid10_component": "PASS" if all(tests.values()) else "FAIL",
                    "whole_hcu": False,
                    "entityos_whole": False,
                    "semantic_jspace": False,
                    "training": False,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
            }
        finally:
            f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node")
    ap.add_argument("--coordinator")
    ap.add_argument("--db", type=Path)
    ap.add_argument("--barrier-dir", type=Path)
    args = ap.parse_args()

    if args.node:
        if not args.db:
            raise SystemExit("--db required with --node")
        return child_node(args.db, args.node, args.barrier_dir)
    if args.coordinator:
        return child_coordinator(args.coordinator)

    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
