from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .bridge_relay import Relay
from .nonblocking_relay import NonBlockingRelay
from .spool_bridge_relay import SpoolTransport


def build_relay(args: argparse.Namespace) -> Relay:
    relay = Relay(
        runtime_root=Path(args.runtime_root),
        repo_root=Path(args.repo_root),
        db_path=Path(args.db),
        carrier_repo=Path(args.carrier_repo),
        policy_path=Path(args.policy),
        router_path=Path(args.router),
    )
    relay.transport = SpoolTransport(
        Path(args.spool_root),
        poll_seconds=min(2.0, max(0.25, args.interval)),
    )
    return relay


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/oMEGA"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--carrier-repo", default=os.getenv("OMEGA_CARRIER_REPO", "/workspace/clay-global-research-entity"))
    ap.add_argument("--policy", default=os.getenv("OMEGA_AUTONOMY_POLICY", "/workspace/oMEGA/config/autonomy_policy.json"))
    ap.add_argument("--router", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/oMEGA/config/organ_router.json"))
    ap.add_argument("--spool-root", default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_RELAY_INTERVAL", "0.5")))
    ap.add_argument("--max-workers", type=int, default=int(os.getenv("OMEGA_RELAY_MAX_WORKERS", "4")))
    ap.add_argument("--per-organ-limit", type=int, default=int(os.getenv("OMEGA_RELAY_PER_ORGAN_LIMIT", "1")))
    ap.add_argument("--long-running-seconds", type=float, default=float(os.getenv("OMEGA_RELAY_LONG_RUNNING_SECONDS", "15")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    relay = build_relay(args)
    if args.once:
        print(json.dumps(relay.run_once(), ensure_ascii=False, indent=2))
        return 0

    NonBlockingRelay(
        relay,
        interval=args.interval,
        max_workers=args.max_workers,
        per_organ_limit=args.per_organ_limit,
        long_running_seconds=args.long_running_seconds,
    ).run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
