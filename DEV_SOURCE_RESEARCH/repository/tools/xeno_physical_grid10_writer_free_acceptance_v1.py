#!/usr/bin/env python3
"""Observed writer-free barrier proof for physical GRID10 v2.

This supplemental fail-closed harness closes one evidence-quality gap in
xeno_physical_grid10_acceptance_v2.py: v2 currently reports writer_free_interval=True
as a literal. Here the property is derived from authoritative S1 identities observed
before child launch and after all ten children have reached the release barrier.

A deterministic negative control mutates S1 while all children are held at the barrier
and must make the same stability discriminator fail. A local PASS is component evidence
only and does not mint repository-bound runtime, HCU, EntityOS, J-Space, training,
canonical-truth, or effect-authority credit.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

from xeno_physical_grid10_acceptance_v2 import ExactSnapshotFabric, N, cj

SCHEMA = "XENO_PHYSICAL_GRID10_WRITER_FREE_ACCEPTANCE/v1"


def snap_id(s: Any) -> tuple[int, int, str]:
    return (int(s.generation), int(s.epoch), str(s.state_digest))


def row_id(r: dict[str, Any]) -> tuple[int, int, str]:
    return (int(r["generation"]), int(r["state_epoch"]), str(r["state_digest"]))


def seed(fabric: ExactSnapshotFabric) -> tuple[list[str], list[str]]:
    ids = [f"x{i:02d}" for i in range(1, N + 1)]
    scopes = ["branch:a" if i % 2 == 0 else "branch:b" for i in range(N)]
    for node_id in ids:
        fabric.runtime_register_node(node_id, "reason")
    for scope in ("branch:a", "branch:b", "GLOBAL"):
        fabric.seed_scope(scope)
    for i, scope in enumerate(scopes):
        fabric.seed_task(f"t{i:02d}", scope, 100 - i, "reason", {"q": i})
    return ids, scopes


def launch(
    child_script: Path,
    db: Path,
    ids: list[str],
    scopes: list[str],
    barrier: Path,
) -> list[subprocess.Popen[str]]:
    (barrier / "ready").mkdir(parents=True, exist_ok=True)
    procs: list[subprocess.Popen[str]] = []
    for node_id, scope in zip(ids, scopes, strict=True):
        procs.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(child_script),
                    "--node",
                    node_id,
                    "--scope",
                    scope,
                    "--db",
                    str(db),
                    "--barrier-dir",
                    str(barrier),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
    return procs


def wait_ready(
    barrier: Path,
    procs: list[subprocess.Popen[str]],
    expected: int,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + 20.0
    while True:
        files = sorted((barrier / "ready").glob("*.json"))
        if len(files) == expected:
            return [json.loads(p.read_text(encoding="utf-8")) for p in files]
        dead = [p.pid for p in procs if p.poll() is not None]
        if dead:
            raise RuntimeError(f"node exited before barrier release: {dead}")
        if time.monotonic() >= deadline:
            raise TimeoutError("not all GRID10 nodes reached writer-free barrier")
        time.sleep(0.01)


def release_and_collect(
    barrier: Path,
    ids: list[str],
    procs: list[subprocess.Popen[str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    release_ns = time.time_ns()
    (barrier / "release").write_text(str(release_ns), encoding="utf-8")
    packets: list[dict[str, Any]] = []
    finished: dict[str, int] = {}
    for node_id, proc in zip(ids, procs, strict=True):
        out, err = proc.communicate(timeout=20)
        finished[node_id] = time.time_ns()
        if proc.returncode != 0:
            raise RuntimeError(f"{node_id} rc={proc.returncode} stderr={err.strip()}")
        packets.append(json.loads(out.strip().splitlines()[-1]))
    return packets, finished


def process_proof(
    ids: list[str],
    procs: list[subprocess.Popen[str]],
    ready: list[dict[str, Any]],
) -> dict[str, Any]:
    parent = {node_id: int(proc.pid) for node_id, proc in zip(ids, procs, strict=True)}
    child = {str(r["node_id"]): int(r["pid"]) for r in ready}
    pids = list(parent.values())
    return {
        "distinct_os_pids": len(set(pids)),
        "all_alive_at_ready_barrier": all(proc.poll() is None for proc in procs),
        "parent_child_pid_binding_ok": parent == child,
        "pids": pids,
    }


def stable_identity(
    pre: tuple[int, int, str],
    ready: list[dict[str, Any]],
    barrier: tuple[int, int, str],
) -> bool:
    return pre == barrier and all(row_id(r) == pre for r in ready)


def one_probe(root: Path, *, interfere: bool) -> dict[str, Any]:
    db = root / "grid10.sqlite"
    barrier = root / "barrier"
    child_script = Path(__file__).with_name("xeno_physical_grid10_acceptance_v2.py")
    fabric = ExactSnapshotFabric(db)
    try:
        ids, scopes = seed(fabric)
        pre = snap_id(fabric.snapshot())
        procs = launch(child_script, db, ids, scopes, barrier)
        ready = wait_ready(barrier, procs, N)
        proof = process_proof(ids, procs, ready)
        before_interference = snap_id(fabric.snapshot())

        interference: dict[str, Any] | None = None
        if interfere:
            fabric.runtime_set_health("x10", False)
            after_interference = snap_id(fabric.snapshot())
            interference = {
                "writer": "runtime_set_health",
                "target": "x10",
                "before": before_interference,
                "after": after_interference,
                "identity_changed": before_interference != after_interference,
            }
            barrier_identity = after_interference
        else:
            barrier_identity = before_interference

        observed_stable = stable_identity(pre, ready, barrier_identity)
        packets, finished = release_and_collect(barrier, ids, procs)
        return {
            "pre_identity": pre,
            "ready_identities": sorted({row_id(r) for r in ready}),
            "barrier_identity": barrier_identity,
            "observed_writer_free": observed_stable,
            "process_proof": proof,
            "packets": len(packets),
            "finished_ns": finished,
            "interference": interference,
        }
    finally:
        fabric.close()


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-writer-free-positive-") as td:
        positive = one_probe(Path(td), interfere=False)
    tests["P1_TEN_DISTINCT_OS_PIDS"] = positive["process_proof"]["distinct_os_pids"] == N
    tests["P1_ALL_TEN_LIVE_AT_READY_BARRIER"] = bool(
        positive["process_proof"]["all_alive_at_ready_barrier"]
    )
    tests["P1_PARENT_CHILD_PID_BINDING"] = bool(
        positive["process_proof"]["parent_child_pid_binding_ok"]
    )
    tests["P2_OBSERVED_WRITER_FREE_IDENTITY_STABLE"] = bool(positive["observed_writer_free"])
    tests["P2_ONE_READY_IDENTITY"] = len(positive["ready_identities"]) == 1
    tests["P2_READY_MATCHES_PRE_AND_BARRIER"] = (
        positive["pre_identity"] == positive["barrier_identity"]
        and positive["ready_identities"] == [tuple(positive["pre_identity"])]
    )

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-writer-free-negative-") as td:
        negative = one_probe(Path(td), interfere=True)
    tests["N1_WRITER_INTERFERENCE_CHANGES_IDENTITY"] = bool(
        negative["interference"] and negative["interference"]["identity_changed"]
    )
    tests["N1_STABILITY_DISCRIMINATOR_REJECTS_WRITER"] = not bool(
        negative["observed_writer_free"]
    )
    tests["N1_PROCESS_PROOF_REMAINS_REAL"] = (
        negative["process_proof"]["distinct_os_pids"] == N
        and bool(negative["process_proof"]["all_alive_at_ready_barrier"])
        and bool(negative["process_proof"]["parent_child_pid_binding_ok"])
    )

    passed = all(tests.values())
    return {
        "schema": SCHEMA,
        "pass": passed,
        "tests": tests,
        "positive": positive,
        "negative_control": negative,
        "metrics": {"elapsed_ms": (time.perf_counter() - t0) * 1000.0},
        "claim": {
            "writer_free_is_observed_not_constant": True,
            "discriminator_is_self_falsifying": True,
            "negative_control_writer_must_be_detected": True,
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


def main() -> int:
    result = run()
    print(cj(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
