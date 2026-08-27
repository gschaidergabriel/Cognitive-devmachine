#!/usr/bin/env python3
"""Fused physical GRID10 acceptance candidate v1.

One exact executable joins the previously separate proof boundaries:
- ten simultaneously-live distinct OS child processes;
- each child holds one explicit read-only SQLite S1 transaction through a barrier;
- parent-observed PID is bound to deterministic per-node membership admission/revision;
- parent creates a deterministic process witness for that exact PID without changing S1;
- child packet digest includes membership + process-witness authority fields;
- the exact barrier packet/PID/snapshot set is the set consumed by coordinator fan-in;
- one valid coordinator lease atomically admits the whole cohort and advances S1 once;
- ordinary Xenos remain S1 read-only and coordinator publication remains noncanonical.

This is source/component evidence only until an exact clean repository-bound runtime receipt
exists. It mints no whole-HCU, EntityOS, J-Space, training, truth, or effect credit.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any

from xeno_self_organizing_fabric_acceptance_v1 import FabricError, cj, dg
from trigger2_grid10_per_node_membership_fanin_acceptance_v2 import (
    PerNodeMembershipCohortFabric,
)

SCHEMA = "XENO_PHYSICAL_GRID10_FUSED_ACCEPTANCE/v1"
N = 10
SCOPE = "GLOBAL"


def _ro_snapshot(con: sqlite3.Connection) -> dict[str, Any]:
    epoch = int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
    generation = int(con.execute("SELECT v FROM meta WHERE k='generation'").fetchone()[0])
    tasks = tuple(dict(r) for r in con.execute("SELECT * FROM tasks ORDER BY task_id"))
    scopes = tuple(dict(r) for r in con.execute("SELECT * FROM scopes ORDER BY scope"))
    leases = tuple(
        dict(r)
        for r in con.execute(
            "SELECT lease_id,node_id,scope,generation,granted_epoch,valid FROM leases ORDER BY lease_id"
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
    }


def _packet_core(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        k: packet[k]
        for k in packet
        if k not in ("packet_digest", "s1_write_intent")
    }


def child_main(args: argparse.Namespace) -> int:
    db = Path(args.db)
    barrier = Path(args.barrier_dir)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("BEGIN")
    try:
        snap = _ro_snapshot(con)
        eligible = [
            t
            for t in snap["tasks"]
            if t["status"] == "OPEN"
            and t["claimed_by"] is None
            and t["capability"] == "reason"
            and t["scope"] == SCOPE
        ]
        eligible.sort(key=lambda t: (-int(t["priority"]), t["task_id"]))
        task = eligible[0] if eligible else None
        payload = {
            "node": args.node,
            "task_id": None if task is None else task["task_id"],
            "selected_task_digest": None if task is None else dg(task),
            "observation": f"result:{args.node}",
            "process_pid": os.getpid(),
        }
        payload_digest = dg(payload)
        ready = {
            "node_id": args.node,
            "pid": os.getpid(),
            "generation": snap["generation"],
            "state_epoch": snap["epoch"],
            "state_digest": snap["state_digest"],
            "source_node_admission_id": args.admission_id,
            "source_node_admission_revision": int(args.admission_revision),
            "payload_digest": payload_digest,
            "ro_transaction_open": bool(con.in_transaction),
            "started_ns": time.time_ns(),
        }
        ready_dir = barrier / "ready"
        ready_dir.mkdir(parents=True, exist_ok=True)
        (ready_dir / f"{args.node}.json").write_text(cj(ready), encoding="utf-8")

        authority_file = barrier / "authority" / f"{args.node}.json"
        deadline = time.monotonic() + 20.0
        while not authority_file.exists():
            if time.monotonic() >= deadline:
                raise SystemExit("AUTHORITY_ENVELOPE_TIMEOUT")
            time.sleep(0.01)
        authority = json.loads(authority_file.read_text(encoding="utf-8"))
        if authority["pid"] != os.getpid():
            raise SystemExit("AUTHORITY_PID_MISMATCH")
        if authority["admission_id"] != args.admission_id:
            raise SystemExit("AUTHORITY_ADMISSION_MISMATCH")

        core = {
            "schema": "NODE_RESULT/v1",
            "source_kind": "ORDINARY_NODE",
            "source_node_id": args.node,
            "source_node_admission_id": args.admission_id,
            "source_node_admission_revision": int(args.admission_revision),
            "source_process_witness_id": authority["witness_id"],
            "scope": SCOPE,
            "generation": snap["generation"],
            "state_epoch": snap["epoch"],
            "state_digest": snap["state_digest"],
            "payload": payload,
        }
        packet = {**core, "packet_digest": dg(core), "s1_write_intent": False}
        packet_file = barrier / "packets" / f"{args.node}.json"
        packet_file.parent.mkdir(parents=True, exist_ok=True)
        packet_file.write_text(cj(packet), encoding="utf-8")

        release = barrier / "release"
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


class FusedFabric(PerNodeMembershipCohortFabric):
    def coordinator_commit_physical_cohort(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packets: list[dict[str, Any]],
        expected_epoch: int,
        expected_digest: str,
        expected_authority_vector: tuple[tuple[str, str, int, str | None], ...],
        cohort_manifest: dict[str, Any],
    ) -> dict[str, Any]:
        if cohort_manifest.get("schema") != "GRID10_FUSED_COHORT_MANIFEST/v1":
            raise FabricError("PHYSICAL_COHORT_MANIFEST_SCHEMA_INVALID")
        manifest_core = {k: cohort_manifest[k] for k in cohort_manifest if k != "manifest_digest"}
        if cohort_manifest.get("manifest_digest") != dg(manifest_core):
            raise FabricError("PHYSICAL_COHORT_MANIFEST_DIGEST_INVALID")
        if len(packets) != N or int(cohort_manifest.get("member_count", -1)) != N:
            raise FabricError("PHYSICAL_COHORT_MEMBER_COUNT_INVALID")
        if cohort_manifest.get("all_alive_at_barrier") is not True:
            raise FabricError("PHYSICAL_COHORT_NOT_SIMULTANEOUSLY_LIVE")
        members = cohort_manifest["members"]
        if len({int(m["pid"]) for m in members}) != N:
            raise FabricError("PHYSICAL_COHORT_PID_CARDINALITY_INVALID")
        expected_packet_digests = sorted(str(m["packet_digest"]) for m in members)
        actual_packet_digests = sorted(str(p.get("packet_digest")) for p in packets)
        if actual_packet_digests != expected_packet_digests:
            raise FabricError("PHYSICAL_COHORT_PACKET_SET_MISMATCH")
        member_by_node = {str(m["node_id"]): m for m in members}
        for packet in packets:
            node_id = str(packet["source_node_id"])
            member = member_by_node.get(node_id)
            if member is None:
                raise FabricError("PHYSICAL_COHORT_SOURCE_NOT_IN_MANIFEST")
            if int(packet["payload"]["process_pid"]) != int(member["pid"]):
                raise FabricError("PHYSICAL_COHORT_PID_PACKET_MISMATCH")
            if str(packet["source_process_witness_id"]) != str(member["process_witness_id"]):
                raise FabricError("PHYSICAL_COHORT_PROCESS_WITNESS_MISMATCH")
            if str(packet["source_node_admission_id"]) != str(member["admission_id"]):
                raise FabricError("PHYSICAL_COHORT_MEMBERSHIP_MISMATCH")
        return self.coordinator_commit_cohort(
            lease=lease,
            token=token,
            packets=packets,
            expected_epoch=expected_epoch,
            expected_digest=expected_digest,
            expected_authority_vector=expected_authority_vector,
            require_process_witness=True,
        )


def expect_error(fn: Any, expected: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == expected
    return False


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    started = time.perf_counter()
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="xeno-grid10-fused-") as td:
        root = Path(td)
        db = root / "grid.sqlite"
        barrier = root / "barrier"
        (barrier / "authority").mkdir(parents=True)
        fabric = FusedFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            memberships = {
                node_id: fabric.runtime_register_node(node_id, "reason")
                for node_id in ids
            }
            fabric.seed_scope(SCOPE)
            for i, node_id in enumerate(ids):
                fabric.seed_task(f"t{i:02d}", SCOPE, 100 - i, "reason", {"q": i})
            lease, token = fabric.elect_coordinator(SCOPE)
            starting = fabric.snapshot()

            procs: dict[str, subprocess.Popen[str]] = {}
            for node_id in ids:
                m = memberships[node_id]
                procs[node_id] = subprocess.Popen(
                    [
                        sys.executable,
                        str(script),
                        "--node", node_id,
                        "--db", str(db),
                        "--barrier-dir", str(barrier),
                        "--admission-id", str(m["admission_id"]),
                        "--admission-revision", str(m["revision"]),
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            deadline = time.monotonic() + 20.0
            while len(list((barrier / "ready").glob("*.json"))) != N:
                dead = [node for node, proc in procs.items() if proc.poll() is not None]
                if dead:
                    raise RuntimeError(f"children exited before barrier: {dead}")
                if time.monotonic() >= deadline:
                    raise TimeoutError("GRID10 ready barrier timeout")
                time.sleep(0.01)

            ready = {
                p.stem: json.loads(p.read_text(encoding="utf-8"))
                for p in (barrier / "ready").glob("*.json")
            }
            all_alive = all(proc.poll() is None for proc in procs.values())
            distinct_pids = len({int(proc.pid) for proc in procs.values()})
            tests["P1_TEN_SIMULTANEOUSLY_LIVE_DISTINCT_PIDS"] = all_alive and distinct_pids == N
            tests["P1_PARENT_CHILD_PID_BINDING"] = all(
                int(ready[node]["pid"]) == int(procs[node].pid) for node in ids
            )
            tests["P1_ONE_SHARED_SNAPSHOT"] = len(
                {
                    (
                        int(r["generation"]),
                        int(r["state_epoch"]),
                        str(r["state_digest"]),
                    )
                    for r in ready.values()
                }
            ) == 1
            tests["P1_READ_TRANSACTION_HELD"] = all(
                r.get("ro_transaction_open") is True for r in ready.values()
            )

            # Deterministic fabric binds the already-running OS PID to current membership.
            witnesses: dict[str, dict[str, Any]] = {}
            for node_id in ids:
                m = memberships[node_id]
                witness = fabric.runtime_bind_process(
                    node_id=node_id,
                    admission_id=str(m["admission_id"]),
                    pid=int(procs[node_id].pid),
                )
                witnesses[node_id] = witness
                (barrier / "authority" / f"{node_id}.json").write_text(
                    cj(
                        {
                            "node_id": node_id,
                            "pid": int(procs[node_id].pid),
                            "admission_id": m["admission_id"],
                            "witness_id": witness["witness_id"],
                        }
                    ),
                    encoding="utf-8",
                )

            while len(list((barrier / "packets").glob("*.json"))) != N:
                if time.monotonic() >= deadline:
                    raise TimeoutError("GRID10 packet barrier timeout")
                time.sleep(0.01)
            packets = [
                json.loads((barrier / "packets" / f"{node}.json").read_text(encoding="utf-8"))
                for node in ids
            ]
            manifest_core = {
                "schema": "GRID10_FUSED_COHORT_MANIFEST/v1",
                "member_count": N,
                "starting_snapshot": {
                    "generation": starting.generation,
                    "epoch": starting.epoch,
                    "state_digest": starting.state_digest,
                },
                "members": sorted(
                    [
                        {
                            "node_id": node,
                            "pid": int(procs[node].pid),
                            "admission_id": memberships[node]["admission_id"],
                            "admission_revision": int(memberships[node]["revision"]),
                            "process_witness_id": witnesses[node]["witness_id"],
                            "packet_digest": next(
                                p["packet_digest"] for p in packets if p["source_node_id"] == node
                            ),
                            "payload_digest": ready[node]["payload_digest"],
                        }
                        for node in ids
                    ],
                    key=lambda m: m["node_id"],
                ),
                "all_alive_at_barrier": all(proc.poll() is None for proc in procs.values()),
            }
            manifest = {**manifest_core, "manifest_digest": dg(manifest_core)}
            (barrier / "release").write_text(str(time.time_ns()), encoding="utf-8")
            for node, proc in procs.items():
                out, err = proc.communicate(timeout=20)
                if proc.returncode != 0:
                    raise RuntimeError(f"{node} rc={proc.returncode}: {err.strip()}")
                emitted = json.loads(out.strip().splitlines()[-1])
                if emitted["packet_digest"] != next(
                    p["packet_digest"] for p in packets if p["source_node_id"] == node
                ):
                    raise RuntimeError("emitted packet differs from barrier packet")

            tests["P2_ORDINARY_RESULTS_NONWRITING"] = all(
                p.get("s1_write_intent") is False for p in packets
            )
            tests["P2_PACKET_MEMBERSHIP_PROCESS_BINDING"] = all(
                p["source_node_admission_id"] == memberships[p["source_node_id"]]["admission_id"]
                and p["source_process_witness_id"] == witnesses[p["source_node_id"]]["witness_id"]
                and int(p["payload"]["process_pid"]) == int(procs[p["source_node_id"]].pid)
                for p in packets
            )

            vector = fabric._authority_vector(packets)

            # Exact-set negatives happen before any mutation.
            omitted = packets[:-1]
            tests["N1_OMITTED_MEMBER_REJECTED"] = expect_error(
                lambda: fabric.coordinator_commit_physical_cohort(
                    lease=lease, token=token, packets=omitted,
                    expected_epoch=starting.epoch, expected_digest=starting.state_digest,
                    expected_authority_vector=fabric._authority_vector(omitted),
                    cohort_manifest=manifest,
                ),
                "PHYSICAL_COHORT_MEMBER_COUNT_INVALID",
            )
            tampered = copy.deepcopy(packets)
            tampered[0]["payload"]["observation"] = "tampered"
            tampered[0]["packet_digest"] = dg(_packet_core(tampered[0]))
            tests["N2_PACKET_TAMPER_REJECTED"] = expect_error(
                lambda: fabric.coordinator_commit_physical_cohort(
                    lease=lease, token=token, packets=tampered,
                    expected_epoch=starting.epoch, expected_digest=starting.state_digest,
                    expected_authority_vector=fabric._authority_vector(tampered),
                    cohort_manifest=manifest,
                ),
                "PHYSICAL_COHORT_PACKET_SET_MISMATCH",
            )
            disjoint = copy.deepcopy(packets)
            disjoint[0]["payload"]["process_pid"] = int(disjoint[0]["payload"]["process_pid"]) + 100000
            disjoint[0]["packet_digest"] = dg(_packet_core(disjoint[0]))
            tests["N3_DISJOINT_PROCESS_SUBSTITUTION_REJECTED"] = expect_error(
                lambda: fabric.coordinator_commit_physical_cohort(
                    lease=lease, token=token, packets=disjoint,
                    expected_epoch=starting.epoch, expected_digest=starting.state_digest,
                    expected_authority_vector=fabric._authority_vector(disjoint),
                    cohort_manifest=manifest,
                ),
                "PHYSICAL_COHORT_PACKET_SET_MISMATCH",
            )

            receipt = fabric.coordinator_commit_physical_cohort(
                lease=lease,
                token=token,
                packets=packets,
                expected_epoch=starting.epoch,
                expected_digest=starting.state_digest,
                expected_authority_vector=vector,
                cohort_manifest=manifest,
            )
            tests["P3_EXACT_BARRIER_PACKET_SET_ATOMICALLY_ADMITTED"] = (
                set(receipt["packet_digests"]) == {p["packet_digest"] for p in packets}
            )
            tests["P3_SINGLE_S1_EPOCH_ADVANCE"] = receipt["new_epoch"] == starting.epoch + 1
            tests["P3_NONCANONICAL_COORDINATOR_WRITE"] = (
                receipt["canonical_truth"] is False and receipt["effect_authority"] is False
            )

            # Replay must fail closed through admitted-result deduplication.
            after = fabric.snapshot()
            tests["N4_REPLAY_REJECTED"] = expect_error(
                lambda: fabric.coordinator_commit_physical_cohort(
                    lease=lease, token=token, packets=packets,
                    expected_epoch=after.epoch, expected_digest=after.state_digest,
                    expected_authority_vector=vector,
                    cohort_manifest=manifest,
                ),
                "COHORT_STALE_EPOCH",
            ) or expect_error(
                lambda: fabric.coordinator_commit_physical_cohort(
                    lease=lease, token=token, packets=packets,
                    expected_epoch=starting.epoch, expected_digest=starting.state_digest,
                    expected_authority_vector=vector,
                    cohort_manifest=manifest,
                ),
                "S1_COMPARE_AND_SWAP_FAILED",
            )

            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "cohort_manifest": manifest,
                "receipt": receipt,
                "metrics": {
                    "simultaneously_live_os_processes": N,
                    "exact_cohort_packets_admitted": N,
                    "s1_epoch_advances": 1,
                    "elapsed_ms": (time.perf_counter() - started) * 1000.0,
                },
                "authority_boundary": {
                    "ordinary_node_s1_write": False,
                    "membership_process_snapshot_authority": "DETERMINISTIC_FABRIC",
                    "coordinator_only_s1_write": True,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
                "credit_boundary": {
                    "local_source_component_candidate": "PASS" if passed else "FAIL",
                    "repository_bound_physical_grid10_runtime_credit": False,
                    "whole_hcu": False,
                    "whole_entityos": False,
                    "jspace_model": False,
                    "training": False,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node")
    ap.add_argument("--db")
    ap.add_argument("--barrier-dir")
    ap.add_argument("--admission-id")
    ap.add_argument("--admission-revision", type=int)
    args = ap.parse_args()
    if args.node:
        if not all((args.db, args.barrier_dir, args.admission_id, args.admission_revision)):
            raise SystemExit("child mode requires db/barrier/admission fields")
        return child_main(args)
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
