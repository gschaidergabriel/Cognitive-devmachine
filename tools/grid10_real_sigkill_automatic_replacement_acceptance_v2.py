#!/usr/bin/env python3
"""GRID10 real-PID SIGKILL -> automatic lease-expiry replacement acceptance v2.

Strengthens v1 by closing two proof-splices:
1. the crashed coordinator registers its *actual child PID* in the shared Fabric;
2. the parent never manually revokes the crashed coordinator lease. Replacement must
   become electable only through the retained Fabric's own lease-expiry semantics.

The old coordinator durably admits exactly one NODE_RESULT, signals the exact
POST_ADMISSION_PRE_ACK window, and is then killed with real SIGKILL. After the retained
lease TTL expires, a different admitted node must be elected and the retained
DecodeSafeFabric recovery must converge to outbox.consumed=1 without a second S1 write.

No provider/network/secret/effect path is used. Temporary SQLite/WAL only.
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

from grid10_fabric import Fabric, LEASE_TTL_SECONDS, connect, result_packet
from grid10_decode_safe_node_wrapper_v1 import DecodeSafeFabric

SCHEMA = "GRID10_REAL_SIGKILL_AUTOMATIC_REPLACEMENT_ACCEPTANCE/v2"


def _old_coordinator(db: str, conn) -> None:
    fabric = Fabric(Path(db))
    fabric.runtime_join("coord-old", "general", os.getpid())
    conn.send({"phase": "CHILD_JOINED", "pid": os.getpid()})
    command = conn.recv()
    if command.get("phase") != "COMMIT":
        raise RuntimeError("INVALID_PARENT_COMMAND")
    packet = command["packet"]
    snap = fabric.snapshot()
    fabric.coordinator_commit(
        lease=command["lease"],
        token=command["token"],
        packet=packet,
        expected_epoch=snap.epoch,
        expected_digest=snap.state_digest,
    )
    conn.send({"phase": "POST_ADMISSION_PRE_ACK", "packet_digest": packet["packet_digest"], "pid": os.getpid()})
    while True:
        time.sleep(60)


def _db_state(db: Path, packet_digest: str) -> dict[str, Any]:
    con = connect(db)
    try:
        outbox = con.execute("SELECT consumed,scope FROM outbox WHERE packet_digest=?", (packet_digest,)).fetchone()
        admitted = con.execute(
            "SELECT COUNT(*) AS n, MIN(scope) AS scope FROM admitted_results WHERE result_digest=?",
            (packet_digest,),
        ).fetchone()
        node = con.execute("SELECT pid,healthy FROM nodes WHERE node_id='coord-old'").fetchone()
        return {
            "consumed": None if outbox is None else int(outbox["consumed"]),
            "outbox_scope": None if outbox is None else str(outbox["scope"]),
            "admitted_count": int(admitted["n"]),
            "admitted_scope": admitted["scope"],
            "old_node_pid": None if node is None else int(node["pid"]),
            "old_node_healthy": None if node is None else int(node["healthy"]),
        }
    finally:
        con.close()


def run_acceptance(root: Path) -> dict[str, Any]:
    db = root / "fabric.sqlite"
    fabric = Fabric(db)
    fabric.seed_scope("A")
    fabric.runtime_join("worker", "general", os.getpid())
    fabric.runtime_join("coord-new", "general", os.getpid())

    parent_conn, child_conn = mp.Pipe(duplex=True)
    proc = mp.Process(target=_old_coordinator, args=(str(db), child_conn), name="grid10-old-coordinator-real-pid")
    proc.start()
    child_conn.close()
    if not parent_conn.poll(20.0):
        proc.kill(); proc.join(5.0)
        raise RuntimeError("OLD_COORDINATOR_DID_NOT_JOIN")
    joined = parent_conn.recv()
    if joined.get("phase") != "CHILD_JOINED" or int(joined.get("pid", -1)) != proc.pid:
        proc.kill(); proc.join(5.0)
        raise RuntimeError(f"REAL_PID_JOIN_NOT_PROVEN:{joined}:{proc.pid}")

    packet = result_packet("worker", fabric.snapshot(), "A", {"task_id": "sigkill-auto-t1", "value": 11})
    fabric.emit_node_result(packet)
    elected = fabric.elect_coordinator("A", ["coord-old"])
    if elected is None:
        proc.kill(); proc.join(5.0)
        raise RuntimeError("OLD_COORDINATOR_ELECTION_FAILED")
    old_lease, old_token = elected
    parent_conn.send({"phase": "COMMIT", "lease": old_lease, "token": old_token, "packet": packet})

    if not parent_conn.poll(20.0):
        proc.kill(); proc.join(5.0)
        raise RuntimeError("OLD_COORDINATOR_DID_NOT_REACH_CRASH_WINDOW")
    marker = parent_conn.recv()
    parent_conn.close()
    if marker.get("phase") != "POST_ADMISSION_PRE_ACK" or int(marker.get("pid", -1)) != proc.pid:
        proc.kill(); proc.join(5.0)
        raise RuntimeError(f"INVALID_CRASH_WINDOW_MARKER:{marker}")

    os.kill(proc.pid, signal.SIGKILL)
    proc.join(10.0)
    if proc.is_alive() or proc.exitcode != -signal.SIGKILL:
        raise RuntimeError("SIGKILL_DID_NOT_TERMINATE_OLD_COORDINATOR")

    crash_state = _db_state(db, packet["packet_digest"])
    crash_window_proven = (
        crash_state["admitted_count"] == 1
        and crash_state["consumed"] == 0
        and crash_state["outbox_scope"] == "A"
        and crash_state["admitted_scope"] == "A"
        and crash_state["old_node_pid"] == proc.pid
    )
    if not crash_window_proven:
        raise RuntimeError(f"CRASH_WINDOW_NOT_PROVEN:{crash_state}")

    # Critical v2 invariant: NO manual revoke_lease(). Before TTL expiry, replacement
    # election must back off because the crashed lease still exists and is valid.
    premature = fabric.elect_coordinator("A", ["coord-new"])
    premature_blocked = premature is None
    if not premature_blocked:
        raise RuntimeError("REPLACEMENT_ELECTED_BEFORE_RETAINED_LEASE_EXPIRY")

    time.sleep(LEASE_TTL_SECONDS + 0.35)
    elected2 = fabric.elect_coordinator("A", ["coord-new"])
    if elected2 is None:
        raise RuntimeError("AUTOMATIC_REPLACEMENT_AFTER_TTL_FAILED")
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
        "real_child_pid_bound_in_fabric": crash_state["old_node_pid"] == proc.pid and proc.pid != os.getpid(),
        "old_coordinator_sigkilled": proc.exitcode == -signal.SIGKILL,
        "post_admission_pre_ack_window_proven": crash_window_proven,
        "no_manual_revoke_path_used": True,
        "replacement_blocked_before_ttl": premature_blocked,
        "replacement_elected_after_retained_ttl": new_lease.get("node_id") == "coord-new",
        "replacement_is_different_node": new_lease.get("node_id") != old_lease.get("node_id"),
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
    return {
        "schema": SCHEMA,
        "pass": all(checks.values()),
        "checks": checks,
        "packet_digest": packet["packet_digest"],
        "lease_ttl_seconds": LEASE_TTL_SECONDS,
        "old_coordinator_pid": proc.pid,
        "old_coordinator_exitcode": proc.exitcode,
        "old_lease_id": old_lease["lease_id"],
        "new_lease_id": new_lease["lease_id"],
        "crash_state": crash_state,
        "recovered_state": recovered_state,
        "recovery_receipt": receipt,
        "provider_calls": 0,
        "secret_lookups": 0,
        "canonical_truth_authority": False,
        "effect_authority": False,
        "credit_scope": "GRID10_CRASH_AUTOMATIC_REPLACEMENT_COMPONENT_ONLY",
        "physical_grid10_credit": 0,
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
        with tempfile.TemporaryDirectory(prefix="grid10-real-sigkill-auto-v2-") as td:
            result = run_acceptance(Path(td))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
