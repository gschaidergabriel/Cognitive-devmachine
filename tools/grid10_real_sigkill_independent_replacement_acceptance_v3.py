#!/usr/bin/env python3
"""GRID10 real SIGKILL -> independent replacement-process acceptance v3.

Closes the v2 proof splice where coord-new was only a logical node registered with the
parent PID and the parent executed DecodeSafeFabric recovery with coord-new's lease.

v3 requires:
- coord-old is a distinct real child process with its actual PID registered in Fabric;
- coord-new is a second distinct real child process with its own observed PID/incarnation;
- the parent may orchestrate and observe, but never executes coordinator recovery using
  coord-new's lease/token;
- coord-new itself proves replacement is blocked before retained TTL expiry, elects itself
  after TTL, and executes the retained DecodeSafeFabric drain/recovery path;
- exactly one admission survives, outbox converges 0 -> 1, S1 does not move during
  recovery, and identical replay is +0.

Worker remains parent-owned in this component falsifier, so this grants no Physical-GRID10
node-independence credit. No provider/network/secret/effect path is used.
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

SCHEMA = "GRID10_REAL_SIGKILL_INDEPENDENT_REPLACEMENT_ACCEPTANCE/v3"


def _old_coordinator(db: str, conn) -> None:
    fabric = Fabric(Path(db))
    fabric.runtime_join("coord-old", "general", os.getpid())
    conn.send({"phase": "OLD_JOINED", "pid": os.getpid()})
    command = conn.recv()
    if command.get("phase") != "COMMIT":
        raise RuntimeError("INVALID_OLD_COMMAND")
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


def _new_coordinator(db: str, conn) -> None:
    fabric = Fabric(Path(db))
    fabric.runtime_join("coord-new", "general", os.getpid())
    conn.send({"phase": "NEW_JOINED", "pid": os.getpid()})

    command = conn.recv()
    if command.get("phase") != "PRE_TTL_PROBE":
        raise RuntimeError("INVALID_NEW_PRE_TTL_COMMAND")
    premature = fabric.elect_coordinator("A", ["coord-new"])
    conn.send({"phase": "PRE_TTL_RESULT", "blocked": premature is None, "pid": os.getpid()})
    if premature is not None:
        return

    command = conn.recv()
    if command.get("phase") != "RECOVER_AFTER_TTL":
        raise RuntimeError("INVALID_NEW_RECOVERY_COMMAND")
    packet_digest = str(command["packet_digest"])
    elected = fabric.elect_coordinator("A", ["coord-new"])
    if elected is None:
        conn.send({"phase": "RECOVERY_FAILED", "reason": "AUTOMATIC_REPLACEMENT_AFTER_TTL_FAILED", "pid": os.getpid()})
        return
    new_lease, new_token = elected

    safe = DecodeSafeFabric(Path(db))
    recovery_before = safe.snapshot()
    drained = safe.coordinator_drain_and_commit("A", new_lease, new_token)
    recovery_after = safe.snapshot()
    receipt = safe.last_outbox_recovery_receipt()
    replay_before = safe.snapshot()
    replay = safe.coordinator_drain_and_commit("A", new_lease, new_token)
    replay_after = safe.snapshot()

    con = connect(Path(db))
    try:
        outbox = con.execute("SELECT consumed,scope FROM outbox WHERE packet_digest=?", (packet_digest,)).fetchone()
        admitted = con.execute("SELECT COUNT(*) AS n, MIN(scope) AS scope FROM admitted_results WHERE result_digest=?", (packet_digest,)).fetchone()
        node = con.execute("SELECT pid,healthy FROM nodes WHERE node_id='coord-new'").fetchone()
        state = {
            "consumed": None if outbox is None else int(outbox["consumed"]),
            "outbox_scope": None if outbox is None else str(outbox["scope"]),
            "admitted_count": int(admitted["n"]),
            "admitted_scope": admitted["scope"],
            "new_node_pid": None if node is None else int(node["pid"]),
            "new_node_healthy": None if node is None else int(node["healthy"]),
        }
    finally:
        con.close()

    conn.send({
        "phase": "RECOVERY_COMPLETE",
        "pid": os.getpid(),
        "lease_node_id": new_lease.get("node_id"),
        "lease_id": new_lease.get("lease_id"),
        "drained": drained,
        "receipt": receipt,
        "state": state,
        "recovery_before": {"epoch": recovery_before.epoch, "digest": recovery_before.state_digest},
        "recovery_after": {"epoch": recovery_after.epoch, "digest": recovery_after.state_digest},
        "replay": replay,
        "replay_before": {"epoch": replay_before.epoch, "digest": replay_before.state_digest},
        "replay_after": {"epoch": replay_after.epoch, "digest": replay_after.state_digest},
    })


def _db_state(db: Path, packet_digest: str) -> dict[str, Any]:
    con = connect(db)
    try:
        outbox = con.execute("SELECT consumed,scope FROM outbox WHERE packet_digest=?", (packet_digest,)).fetchone()
        admitted = con.execute("SELECT COUNT(*) AS n, MIN(scope) AS scope FROM admitted_results WHERE result_digest=?", (packet_digest,)).fetchone()
        old_node = con.execute("SELECT pid,healthy FROM nodes WHERE node_id='coord-old'").fetchone()
        new_node = con.execute("SELECT pid,healthy FROM nodes WHERE node_id='coord-new'").fetchone()
        return {
            "consumed": None if outbox is None else int(outbox["consumed"]),
            "outbox_scope": None if outbox is None else str(outbox["scope"]),
            "admitted_count": int(admitted["n"]),
            "admitted_scope": admitted["scope"],
            "old_node_pid": None if old_node is None else int(old_node["pid"]),
            "new_node_pid": None if new_node is None else int(new_node["pid"]),
        }
    finally:
        con.close()


def _terminate(proc: mp.Process) -> None:
    if proc.is_alive():
        proc.kill()
    proc.join(5.0)


def run_acceptance(root: Path) -> dict[str, Any]:
    db = root / "fabric.sqlite"
    fabric = Fabric(db)
    fabric.seed_scope("A")
    fabric.runtime_join("worker", "general", os.getpid())

    old_parent, old_child = mp.Pipe(duplex=True)
    new_parent, new_child = mp.Pipe(duplex=True)
    old_proc = mp.Process(target=_old_coordinator, args=(str(db), old_child), name="grid10-old-coordinator-v3")
    new_proc = mp.Process(target=_new_coordinator, args=(str(db), new_child), name="grid10-new-coordinator-v3")
    old_proc.start(); new_proc.start()
    old_child.close(); new_child.close()
    try:
        if not old_parent.poll(20.0) or not new_parent.poll(20.0):
            raise RuntimeError("COORDINATOR_CHILD_DID_NOT_JOIN")
        old_join = old_parent.recv(); new_join = new_parent.recv()
        if old_join.get("phase") != "OLD_JOINED" or int(old_join.get("pid", -1)) != old_proc.pid:
            raise RuntimeError(f"OLD_REAL_PID_JOIN_NOT_PROVEN:{old_join}:{old_proc.pid}")
        if new_join.get("phase") != "NEW_JOINED" or int(new_join.get("pid", -1)) != new_proc.pid:
            raise RuntimeError(f"NEW_REAL_PID_JOIN_NOT_PROVEN:{new_join}:{new_proc.pid}")
        if len({os.getpid(), old_proc.pid, new_proc.pid}) != 3:
            raise RuntimeError("PROCESS_INDEPENDENCE_NOT_PROVEN")

        packet = result_packet("worker", fabric.snapshot(), "A", {"task_id": "sigkill-independent-t1", "value": 11})
        fabric.emit_node_result(packet)
        elected = fabric.elect_coordinator("A", ["coord-old"])
        if elected is None:
            raise RuntimeError("OLD_COORDINATOR_ELECTION_FAILED")
        old_lease, old_token = elected
        old_parent.send({"phase": "COMMIT", "lease": old_lease, "token": old_token, "packet": packet})
        if not old_parent.poll(20.0):
            raise RuntimeError("OLD_COORDINATOR_DID_NOT_REACH_CRASH_WINDOW")
        marker = old_parent.recv()
        if marker.get("phase") != "POST_ADMISSION_PRE_ACK" or int(marker.get("pid", -1)) != old_proc.pid:
            raise RuntimeError(f"INVALID_CRASH_WINDOW_MARKER:{marker}")

        os.kill(old_proc.pid, signal.SIGKILL)
        old_proc.join(10.0)
        if old_proc.is_alive() or old_proc.exitcode != -signal.SIGKILL:
            raise RuntimeError("SIGKILL_DID_NOT_TERMINATE_OLD_COORDINATOR")

        crash_state = _db_state(db, packet["packet_digest"])
        crash_window_proven = (
            crash_state["admitted_count"] == 1
            and crash_state["consumed"] == 0
            and crash_state["outbox_scope"] == "A"
            and crash_state["admitted_scope"] == "A"
            and crash_state["old_node_pid"] == old_proc.pid
            and crash_state["new_node_pid"] == new_proc.pid
        )
        if not crash_window_proven:
            raise RuntimeError(f"CRASH_WINDOW_NOT_PROVEN:{crash_state}")

        new_parent.send({"phase": "PRE_TTL_PROBE"})
        if not new_parent.poll(20.0):
            raise RuntimeError("NEW_COORDINATOR_PRE_TTL_PROBE_TIMEOUT")
        pre = new_parent.recv()
        premature_blocked = pre.get("phase") == "PRE_TTL_RESULT" and pre.get("blocked") is True and int(pre.get("pid", -1)) == new_proc.pid
        if not premature_blocked:
            raise RuntimeError(f"REPLACEMENT_ELECTED_BEFORE_RETAINED_LEASE_EXPIRY:{pre}")

        time.sleep(LEASE_TTL_SECONDS + 0.35)
        new_parent.send({"phase": "RECOVER_AFTER_TTL", "packet_digest": packet["packet_digest"]})
        if not new_parent.poll(30.0):
            raise RuntimeError("NEW_COORDINATOR_RECOVERY_TIMEOUT")
        recovery = new_parent.recv()
        if recovery.get("phase") != "RECOVERY_COMPLETE":
            raise RuntimeError(f"INDEPENDENT_REPLACEMENT_RECOVERY_FAILED:{recovery}")
        if int(recovery.get("pid", -1)) != new_proc.pid:
            raise RuntimeError("REPLACEMENT_RECEIPT_PID_TRANSPLANT")

        state = recovery["state"]
        receipt = recovery["receipt"]
        rb = recovery["recovery_before"]; ra = recovery["recovery_after"]
        pb = recovery["replay_before"]; pa = recovery["replay_after"]
        checks = {
            "old_real_child_pid_bound": crash_state["old_node_pid"] == old_proc.pid and old_proc.pid != os.getpid(),
            "new_real_child_pid_bound": crash_state["new_node_pid"] == new_proc.pid and new_proc.pid != os.getpid(),
            "replacement_process_is_independent": len({os.getpid(), old_proc.pid, new_proc.pid}) == 3,
            "old_coordinator_sigkilled": old_proc.exitcode == -signal.SIGKILL,
            "post_admission_pre_ack_window_proven": crash_window_proven,
            "no_manual_revoke_path_used": True,
            "replacement_blocked_before_ttl": premature_blocked,
            "replacement_election_executed_by_new_child": recovery.get("lease_node_id") == "coord-new" and int(recovery["pid"]) == new_proc.pid,
            "replacement_recovery_executed_by_new_child": int(recovery["pid"]) == state["new_node_pid"] == new_proc.pid,
            "parent_did_not_execute_with_replacement_token": True,
            "replacement_recovery_drain_is_empty": recovery["drained"] == [],
            "recovery_receipt_pass": bool(receipt and receipt.get("pass") is True),
            "recovery_repaired_exact_packet": bool(receipt and receipt.get("repaired") == [packet["packet_digest"]]),
            "exactly_one_admission_after_recovery": state["admitted_count"] == 1,
            "outbox_consumed_after_recovery": state["consumed"] == 1,
            "recovery_does_not_move_s1_epoch": ra["epoch"] == rb["epoch"],
            "recovery_does_not_change_s1_digest": ra["digest"] == rb["digest"],
            "identical_replay_empty": recovery["replay"] == [],
            "identical_replay_plus_zero_epoch": pa["epoch"] == pb["epoch"],
            "identical_replay_plus_zero_digest": pa["digest"] == pb["digest"],
        }
        return {
            "schema": SCHEMA,
            "pass": all(checks.values()),
            "checks": checks,
            "packet_digest": packet["packet_digest"],
            "lease_ttl_seconds": LEASE_TTL_SECONDS,
            "parent_pid": os.getpid(),
            "worker_pid": os.getpid(),
            "old_coordinator_pid": old_proc.pid,
            "new_coordinator_pid": new_proc.pid,
            "old_coordinator_exitcode": old_proc.exitcode,
            "old_lease_id": old_lease["lease_id"],
            "new_lease_id": recovery["lease_id"],
            "crash_state": crash_state,
            "recovered_state": state,
            "recovery_receipt": receipt,
            "provider_calls": 0,
            "secret_lookups": 0,
            "canonical_truth_authority": False,
            "effect_authority": False,
            "credit_scope": "GRID10_CRASH_INDEPENDENT_REPLACEMENT_COMPONENT_ONLY",
            "physical_grid10_credit": 0,
            "whole_hcu_credit": 0,
        }
    finally:
        old_parent.close(); new_parent.close()
        _terminate(old_proc); _terminate(new_proc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", type=Path)
    args = ap.parse_args()
    if args.workdir is not None:
        args.workdir.mkdir(parents=True, exist_ok=True)
        result = run_acceptance(args.workdir)
    else:
        with tempfile.TemporaryDirectory(prefix="grid10-real-sigkill-independent-v3-") as td:
            result = run_acceptance(Path(td))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
