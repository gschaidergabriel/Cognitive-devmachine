#!/usr/bin/env python3
"""Drop-in decode-safe GRID10 node wrapper.

Purpose
-------
The retained ``grid10_node.node_loop`` heartbeats only between loop iterations.  A
healthy Xeno can therefore look dead while it is blocked inside a long local model
decode.  ``grid10_liveness_heartbeat_v1`` already provides an epoch-neutral
background heartbeat, but until this wrapper it was not attached to the real node
construction path.

This module installs a small ``Fabric`` subclass into ``grid10_node`` before invoking
its real ``node_loop``.  The subclass starts ``HeartbeatPump`` immediately after a
successful deterministic ``runtime_join``.  The pump updates only runtime liveness
metadata and never advances the cognitive S1 epoch.  It is stopped automatically at
process exit.

This is intentionally a wrapper rather than a fork of ``grid10_node``: the actual task
claiming, NODE_RESULT emission, dynamic coordinator leases, coordinator-only S1 writes,
regulators, Hyperposition handling and result semantics remain the retained code path.

No provider/network calls are introduced by this module.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import grid10_node as retained_node
from grid10_fabric import Fabric as RetainedFabric
from grid10_liveness_heartbeat_v1 import HeartbeatPump


DEFAULT_HEARTBEAT_INTERVAL_S = 0.5


class DecodeSafeFabric(RetainedFabric):
    """Retained Fabric plus an epoch-neutral liveness pump after admission."""

    def __init__(self, *args: Any, heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if heartbeat_interval_s <= 0:
            raise ValueError("heartbeat_interval_s must be > 0")
        self._decode_safe_heartbeat_interval_s = float(heartbeat_interval_s)
        self._decode_safe_pumps: dict[str, HeartbeatPump] = {}
        self._decode_safe_registered_atexit = False

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
    """Install a parameterized Fabric subclass into the retained node module."""
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
    """Run the real retained node loop with decode-safe liveness enabled."""
    install_decode_safe_fabric(heartbeat_interval_s=heartbeat_interval_s)
    retained_node.node_loop(**node_loop_kwargs)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run retained GRID10 node_loop with epoch-neutral decode heartbeat")
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
