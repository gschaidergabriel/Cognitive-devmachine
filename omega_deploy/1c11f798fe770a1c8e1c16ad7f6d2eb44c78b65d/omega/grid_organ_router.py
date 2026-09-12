from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .router import DynamicOrganRouter, OrganTelemetry, TaskRequest


def _telemetry_from_dict(organ_id: str, raw: dict[str, Any]) -> OrganTelemetry:
    return OrganTelemetry(
        organ_id=organ_id,
        observed_at=str(raw["observed_at"]),
        health=str(raw.get("health", "UNKNOWN")),
        capabilities=frozenset(raw.get("capabilities", ())),
        data_domains=frozenset(raw.get("data_domains", ())),
        cpu_load=raw.get("cpu_load"),
        ram_load=raw.get("ram_load"),
        gpu_load=raw.get("gpu_load"),
        bridge_health=float(raw.get("bridge_health", 1.0)),
        information_gain=float(raw.get("information_gain", 0.5)),
        independence=float(raw.get("independence", 0.5)),
        latency_score=float(raw.get("latency_score", 0.5)),
    )


def route_grid_task(
    router: DynamicOrganRouter,
    task: dict[str, Any],
    telemetry_by_organ: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Choose execution organ(s) inside the GRID layer.

    The returned route is an execution proposal only. It grants no effect authority.
    """
    request = TaskRequest(
        task_id=str(task.get("task_id") or "grid-" + uuid.uuid4().hex),
        required_capabilities=frozenset(task.get("required_capabilities", ())),
        preferred_data_domains=frozenset(task.get("preferred_data_domains", ())),
        heavy=bool(task.get("heavy", False)),
        high_risk_effect=bool(task.get("high_risk_effect", False)),
        wants_independent_falsifier=bool(task.get("wants_independent_falsifier", False)),
        max_organs=max(1, int(task.get("max_organs", 1))),
    )
    telemetry = [
        _telemetry_from_dict(organ_id, raw)
        for organ_id, raw in telemetry_by_organ.items()
        if isinstance(raw, dict) and raw.get("observed_at")
    ]
    decision = router.choose(request, telemetry)
    return asdict(decision)


def emit_bound_grid_intents(
    *,
    frame_id: str,
    task: dict[str, Any],
    route: dict[str, Any],
    outbox: str | Path,
) -> list[Path]:
    """Emit one target-bound intent per GRID-selected organ.

    A relay must preserve the selected ``organ_id`` and may only authorize/execute or
    block the exact request; it is not allowed to silently choose a different organ.
    """
    out = Path(outbox)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for organ_id in route.get("selected_organs", ()):
        item = {
            "schema": "OMEGA_GRID_EFFECT_INTENT/v1",
            "effect_id": "effect_" + uuid.uuid4().hex,
            "frame_id": frame_id,
            "organ_id": organ_id,
            "task": task,
            "route": route,
            "effect_state": "PROPOSED",
            "authority": "NOT_YET_GRANTED",
        }
        path = out / f"{item['effect_id']}.json"
        path.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)
    return written
