#!/usr/bin/env python3
"""Drop-in decode-safe + crash-recovering GRID10 node wrapper.

Purpose
-------
The retained ``grid10_node.node_loop`` heartbeats only between loop iterations. A
healthy Xeno can therefore look dead while it is blocked inside a long local model
decode. ``grid10_liveness_heartbeat_v1`` provides an epoch-neutral background
heartbeat; this wrapper attaches it to the real retained node construction path.

A second real failure window exists in the retained coordinator drain path:
``coordinator_commit()`` admits a NODE_RESULT into S1/admitted_results and only in a
second SQLite transaction marks the corresponding outbox row ``consumed=1``. A hard
crash between those transactions leaves an already-admitted packet pending forever;
a replacement coordinator then sees ``DUPLICATE_RESULT_REJECTED`` on each retry.

This wrapper now also invokes the deterministic ``grid10_outbox_recovery_v1``
reconciliation immediately before every retained coordinator drain. Recovery may only
mark a pending outbox row consumed when the same packet digest is already present in
``admitted_results`` for the same scope. It never changes S1 epoch/content and grants
no ordinary-node write authority.

This remains intentionally a wrapper rather than a fork of ``grid10_node``: task
claiming, NODE_RESULT emission, dynamic coordinator leases, coordinator-only S1 writes,
regulators, Hyperposition handling and commit semantics remain the retained code path.

No provider/network calls are introduced by this module.
"""
from __future__ import annotations

import argparse
import atexit
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import grid10_node as retained_node
from grid10_fabric import Fabric as RetainedFabric, FabricError
from grid10_liveness_heartbeat_v1 import HeartbeatPump
from grid10_outbox_recovery_v1 import reconcile_admitted_outbox


DEFAULT_HEARTBEAT_INTERVAL_S = 0.5


class DecodeSafeFabric(RetainedFabric):
    """Retained Fabric plus epoch-neutral liveness and coordinator crash recovery."""

    def __init__(self, *args: Any, heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if heartbeat_interval_s <= 0:
            raise ValueError("heartbeat_interval_s must be > 0")
        self._decode_safe_heartbeat_interval_s = float(heartbeat_interval_s)
        self._decode_safe_pumps: dict[str, HeartbeatPump] = {}
        self._decode_safe_registered_atexit = False
        self._last_outbox_recovery: dict[str, Any] | None = None

    def runtime_join(self, node_id: str, capability: str, pid: int):  # type: ignore[override]
        result = super().runtime_join(node_id, capability, pid)
        if node_id not in self._decode_safe_pumps:
            pump = HeartbeatPump(
                self,
                node_id,
                interval_s=self._decode_safe_heartbeat_interval_s,
            ).start()
            self._decode_safe_pumps[node_id] = pump
            if not self._decode_safe_registered_atexit:
                atexit.register(self.stop_decode_safe_heartbeats)
                self._decode_safe_registered_atexit = True
        return result

    def coordinator_drain_and_commit(self, scope: str, lease: dict[str, Any], token: str):  # type: ignore[override]
        """Recover post-admission/pre-consumed crash residue, then use retained drain.

        The reconciliation is deliberately before the retained drain so a replacement
        coordinator does not repeatedly hit DUPLICATE_RESULT_REJECTED for a packet that
        was already admitted by the coordinator that died. Any scope/provenance conflict
        fails closed and prevents further coordinator work for this call.
        """
        recovery = reconcile_admitted_outbox(self.path, scope=scope)
        self._last_outbox_recovery = recovery
        if not recovery.get("pass"):
            raise FabricError("OUTBOX_CRASH_RECOVERY_CONFLICT")
        return super().coordinator_drain_and_commit(scope, lease, token)

    def last_outbox_recovery_receipt(self) -> dict[str, Any] | None:
        return self._last_outbox_recovery

    def stop_decode_safe_heartbeats(self) -> dict[str, dict[str, Any]]:
        """Stop all pumps and return observable stats without changing S1 authority."""
        report: dict[str, dict[str, Any]] = {}
        for node_id, pump in list(self._decode_safe_pumps.items()):
            stats = pump.stop(mark_unhealthy=False)
            report[node_id] = {
                "attempts": stats.attempts,
                "successes": stats.successes,
                "failures": stats.failures,
                "last_success_ts": stats.last_success_ts,
                "last_error": stats.last_error,
            }
        self._decode_safe_pumps.clear()
        return report


def install_decode_safe_fabric(*, heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S):
    """Install a parameterized crash-safe Fabric subclass into retained node module."""
    if heartbeat_interval_s <= 0:
        raise ValueError("heartbeat_interval_s must be > 0")

    class ConfiguredDecodeSafeFabric(DecodeSafeFabric):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("heartbeat_interval_s", heartbeat_interval_s)
            super().__init__(*args, **kwargs)

    ConfiguredDecodeSafeFabric.__name__ = "ConfiguredDecodeSafeFabric"
    retained_node.Fabric = ConfiguredDecodeSafeFabric
    return ConfiguredDecodeSafeFabric


def run_retained_node_loop(*, heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S, **node_loop_kwargs: Any) -> None:
    """Run the retained node loop with decode-safe liveness and crash recovery."""
    install_decode_safe_fabric(heartbeat_interval_s=heartbeat_interval_s)
    retained_node.node_loop(**node_loop_kwargs)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run retained GRID10 node_loop with decode heartbeat and crash recovery")
    p.add_argument("--node-id", required=True)
    p.add_argument("--capability", required=True)
    p.add_argument("--fabric-path", required=True)
    p.add_argument("--model-path", required=True)
    p.add_argument("--out-evidence", required=True)
    p.add_argument("--max-iters", type=int, default=6)
    p.add_argument("--poll-sleep", type=float, default=0.15)
    p.add_argument("--heartbeat-interval-s", type=float, default=DEFAULT_HEARTBEAT_INTERVAL_S)
    p.add_argument("--task-reclaim-stale-after-seconds", type=float, default=20.0)
    p.add_argument("--scenario", default="default")
    p.add_argument("--no-coordinator", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    run_retained_node_loop(
        heartbeat_interval_s=args.heartbeat_interval_s,
        node_id=args.node_id,
        capability=args.capability,
        fabric_path=args.fabric_path,
        model_path=args.model_path,
        out_evidence=args.out_evidence,
        max_iters=args.max_iters,
        poll_sleep=args.poll_sleep,
        become_coordinator_candidate=not args.no_coordinator,
        scenario=args.scenario,
        task_reclaim_stale_after_seconds=args.task_reclaim_stale_after_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
