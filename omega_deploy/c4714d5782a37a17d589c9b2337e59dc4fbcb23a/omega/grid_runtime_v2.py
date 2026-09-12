from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from .grid_organ_router import emit_bound_grid_intents, route_grid_task
from .grid_runtime import Runtime as BaseRuntime
from .router import DynamicOrganRouter


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Runtime(BaseRuntime):
    """Persistent GRID runtime with dynamic execution-organ selection."""

    def __init__(self, root: Path, interval: float, router_config: Path) -> None:
        super().__init__(root, interval)
        self.router = DynamicOrganRouter.from_path(router_config)

    def routing_telemetry(self) -> dict[str, dict[str, Any]]:
        observed = self.read_telemetry()
        # The central runtime is always a candidate for capabilities it actually has.
        central_cfg = self.router.organs[self.router.central]
        observed[self.router.central] = {
            "organ_id": self.router.central,
            "observed_at": _now(),
            "health": "GREEN",
            "capabilities": central_cfg.get("capabilities", []),
            "data_domains": ["omega-central"],
            "cpu_load": 0.30,
            "ram_load": 0.30,
            "bridge_health": 1.0,
            "information_gain": 0.60,
            "independence": 0.30,
            "latency_score": 1.0,
        }
        return observed

    def realize(self, selected: dict[str, Any], frame_id: str) -> dict[str, Any]:
        if selected["cell_id"] != "HOST_SCOUT":
            return super().realize(selected, frame_id)

        task = selected["payload"]["task"]
        try:
            route = route_grid_task(self.router, task, self.routing_telemetry())
        except Exception as exc:
            self.emit_outbox(
                "GRID_ROUTE_BLOCKED",
                {"frame_id": frame_id, "task": task, "error": f"{type(exc).__name__}:{exc}"},
            )
            return {"broadcast": "GRID organ selection blocked", "error": f"{type(exc).__name__}:{exc}"}

        paths = emit_bound_grid_intents(
            frame_id=frame_id,
            task=task,
            route=route,
            outbox=self.root / "outbox",
        )
        return {
            "broadcast": "GRID selected execution organ(s); effect authority still pending",
            "route": route,
            "intent_files": [str(p) for p in paths],
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_GRID_INTERVAL", "30")))
    ap.add_argument("--router-config", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/omega_runtime/config/organ_router.json"))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    runtime = Runtime(Path(args.root), args.interval, Path(args.router_config))
    if args.once:
        epoch = runtime.start_epoch()
        runtime.frame(epoch, "MANUAL_ONCE")
        return 0
    runtime.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
