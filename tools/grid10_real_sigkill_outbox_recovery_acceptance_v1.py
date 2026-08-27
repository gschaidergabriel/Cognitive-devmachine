#!/usr/bin/env python3
"""Real multi-process SIGKILL acceptance for GRID10 outbox crash recovery.

This is intentionally stronger than the retained unit/integration test: the old
coordinator is a separate OS process. It commits the NODE_RESULT into S1 and
`admitted_results`, signals the parent that admission is durable, and then blocks.
The parent sends SIGKILL before any outbox ACK can occur. A replacement coordinator
must then converge via the decode-safe retained wrapper to exactly one admission,
`outbox.consumed=1`, unchanged S1 during recovery, and identical replay +0.

No provider/network/secret/effect path is used. The database is a temporary sandbox.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import signal
import tempfile
import time
from pathlib import Path
from typing import Any

from grid10_fabric import Fabric, connect, result_packet
from grid10_decode_safe_node_wrapper_v1 import DecodeSafeFabric

SCHEMA = "GRID10_REAL_SIGKILL_OUTBOX_RECOVERY_ACCEPTANCE/v1"


def _old_coordinator(db: str, lease: dict[str, Any], token: str, packet: dict[str, Any], conn) -> None:
    fabric = Fabric(Path(db))
    snap = fabric.snapshot()
    fabric.coordinator_commit(
        lease=lease,
        token=token,
        packet=packet,
        expected_epoch=snap.epoch,
        expected_digest=snap.state_digest,
    )
    conn.send({"phase": "POST_ADMISSION_PRE_ACK", "packet_digest": packet["packet_digest"]})
    conn.close()
    # Deliberately remain alive in the exact crash window. The parent must SIGKILL us;
    # this process never calls coordinator_drain_and_commit and therefore never ACKs.
    while True:
        time.sleep(60)


def _db_state(db: Path, packet_digest: str) -> dict[str, Any]:
    con = connect(db)
    try:
        outbox = con.execute(
            "SELECT consumed,scope FROM outbox WHERE packet_digest=?", (packet_digest,)
        ).fetchone()
        admitted = con.execute(
            "SELECT COUNT(*) AS n, MIN(scope) AS scope FROM admitted_results WHERE result_digest=?",
            (packet_digest,),
        ).fetchone()
        return {
            "consumed": None if outbox is None else int(outbox["consumed"]),
            "outbox_scope": None if outbox is None else str(outbox["scope"]),
            "admitted_count": int(admitted["n"]),
            "admitted_scope": admitted["scope"],
        }
    finally:
        con.close()


def run_acceptance(root: Path) -> dict[str, Any]:
    db = root / "fabric.sqlite"
    fabric = Fabric(db)
    fabric.seed_scope("A")
    fabric.runtime_join("worker", "general", os.getpid())
    fabric.runtime_join("coord-old", "general", os.getpid() + 100001)
    fabric.runtime_join("coord-new", "general", os.getpid() + 100002)

    packet = result_packet("worker", fabric.snapshot(), "A", {"task_id": "sigkill-t1", "value": 7})
    fabric.emit_node_result(packet)
    elected = fabric.elect_coordinator("A", ["coord-old"])
    if elected is None:
        raise RuntimeError("OLD_COORDINATOR_ELECTION_FAILED")
    old_lease, old_token = elected

    parent_conn, child_conn = mp.Pipe(duplex=False)
    proc = mp.Process(
        target=_old_coordinator,
        args=(str(db), old_lease, old_token, packet, child_conn),
        name="grid10-old-coordinator-crash-window",
    )
    proc.start()
    child_conn.close()
    try:
        if not parent_conn.poll(20.0):
            proc.kill()
            proc.join(5.0)
            raise RuntimeError("OLD_COORDINATOR_DID_NOT_REACH_CRASH_WINDOW")
        marker = parent_conn.recv()
    finally:
        parent_conn.close()

    if marker.get("phase") != "POST_ADMISSION_PRE_ACK":
        proc.kill()
        proc.join(5.0)
        raise RuntimeError("INVALID_CRASH_WINDOW_MARKER")

    os.kill(proc.pid, signal.SIGKILL)
    proc.join(10.0)
    if proc.is_alive():
        raise RuntimeError("SIGKILL_DID_NOT_TERMINATE_OLD_COORDINATOR")

    crash_state = _db_state(db, packet["packet_digest"])
    crash_window_proven = (
        crash_state["admitted_count"] == 1
        and crash_state["consumed"] == 0
        and crash_state["outbox_scope"] == "A"
        and crash_state["admitted_scope"] == "A"
    )
    if not crash_window_proven:
        raise RuntimeError(f"CRASH_WINDOW_NOT_PROVEN:{crash_state}")

    fabric.revoke_lease(old_lease["lease_id"])
    elected2 = fabric.elect_coordinator("A", ["coord-new"])
    if elected2 is None:
        raise RuntimeError("REPLACEMENT_COORDINATOR_ELECTION_FAILED")
    new_lease, new_token = elected2

    safe = DecodeSafeFabric(db)
    recovery_before = safe.snapshot()
    drained = safe.coordinator_drain_and_commit("A", new_lease, new_token)
    recovery_after = safe.snapshot()
    receipt = safe.last_outbox_recovery_receipt()
    recovered_state = _db_state(db, packet["packet_digest"])

    replay_before = safe.snapshot()
    replay = safe.coordinator_drain_and_commit("A", new_lease, new_token)
    replay_after = safe.snapshot()

    checks = {
        "real_separate_coordinator_process": proc.pid is not None and proc.pid != os.getpid(),
        "old_coordinator_sigkilled": proc.exitcode == -signal.SIGKILL,
        "post_admission_pre_ack_window_proven": crash_window_proven,
        "replacement_recovery_drain_is_empty": drained == [],
        "recovery_receipt_pass": bool(receipt and receipt.get("pass") is True),
        "recovery_repaired_exact_packet": bool(receipt and receipt.get("repaired") == [packet["packet_digest"]]),
        "exactly_one_admission_after_recovery": recovered_state["admitted_count"] == 1,
        "outbox_consumed_after_recovery": recovered_state["consumed"] == 1,
        "recovery_does_not_move_s1_epoch": recovery_after.epoch == recovery_before.epoch,
        "recovery_does_not_change_s1_digest": recovery_after.state_digest == recovery_before.state_digest,
        "identical_replay_empty": replay == [],
        "identical_replay_plus_zero_epoch": replay_after.epoch == replay_before.epoch,
        "identical_replay_plus_zero_digest": replay_after.state_digest == replay_before.state_digest,
    }
    passed = all(checks.values())
    return {
        "schema": SCHEMA,
        "pass": passed,
        "checks": checks,
        "packet_digest": packet["packet_digest"],
        "old_coordinator_pid": proc.pid,
        "old_coordinator_exitcode": proc.exitcode,
        "crash_state": crash_state,
        "recovered_state": recovered_state,
        "recovery_receipt": receipt,
        "provider_calls": 0,
        "secret_lookups": 0,
        "canonical_truth_authority": False,
        "effect_authority": False,
        "credit_scope": "GRID10_CRASH_RECOVERY_COMPONENT_ONLY",
        "whole_hcu_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", type=Path)
    args = ap.parse_args()
    if args.workdir is not None:
        args.workdir.mkdir(parents=True, exist_ok=True)
        result = run_acceptance(args.workdir)
    else:
        with tempfile.TemporaryDirectory(prefix="grid10-real-sigkill-") as td:
            result = run_acceptance(Path(td))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
