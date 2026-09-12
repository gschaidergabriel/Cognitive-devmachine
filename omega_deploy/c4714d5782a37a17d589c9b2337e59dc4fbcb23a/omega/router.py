from __future__ import annotations

import dataclasses
import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterable


@dataclasses.dataclass(frozen=True)
class OrganTelemetry:
    organ_id: str
    observed_at: str
    health: str = "UNKNOWN"
    capabilities: frozenset[str] = frozenset()
    data_domains: frozenset[str] = frozenset()
    cpu_load: float | None = None
    ram_load: float | None = None
    gpu_load: float | None = None
    bridge_health: float = 1.0
    information_gain: float = 0.5
    independence: float = 0.5
    latency_score: float = 0.5

    def age_seconds(self, now: dt.datetime | None = None) -> float:
        now = now or dt.datetime.now(dt.timezone.utc)
        observed = dt.datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        return max(0.0, (now - observed).total_seconds())

    @property
    def resource_headroom(self) -> float:
        values = [x for x in (self.cpu_load, self.ram_load, self.gpu_load) if x is not None]
        if not values:
            return 0.5
        peak = max(max(0.0, min(1.0, float(x))) for x in values)
        return 1.0 - peak


@dataclasses.dataclass(frozen=True)
class TaskRequest:
    task_id: str
    required_capabilities: frozenset[str] = frozenset()
    preferred_data_domains: frozenset[str] = frozenset()
    heavy: bool = False
    high_risk_effect: bool = False
    wants_independent_falsifier: bool = False
    max_organs: int = 1


@dataclasses.dataclass(frozen=True)
class RouteScore:
    organ_id: str
    score: float
    eligible: bool
    reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class RouteDecision:
    task_id: str
    selected_organs: tuple[str, ...]
    ranking: tuple[RouteScore, ...]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class DynamicOrganRouter:
    """GRID-facing organ selector.

    This router decides where a proposal should execute. It does NOT grant effect
    authority; the selected route must still cross OMEGA alignment/effect gates.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.organs = {o["organ_id"]: o for o in config["organs"]}
        self.weights = config.get("weights", {})
        self.max_age = float(config.get("telemetry_max_age_seconds", 180))
        self.central = str(config.get("central_organ", "omega-vps"))
        self.min_heavy_headroom = float(config.get("min_heavy_host_headroom", 0.10))

    @classmethod
    def from_path(cls, path: str | Path) -> "DynamicOrganRouter":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _score(self, task: TaskRequest, telem: OrganTelemetry) -> RouteScore:
        cfg = self.organs.get(telem.organ_id)
        if not cfg:
            return RouteScore(telem.organ_id, -1e9, False, ("unregistered organ",))

        available = set(cfg.get("capabilities", ())) | set(telem.capabilities)
        missing = set(task.required_capabilities) - available
        if missing:
            return RouteScore(
                telem.organ_id, -1e9, False,
                ("missing capabilities: " + ",".join(sorted(missing)),),
            )

        if telem.health.upper() == "RED":
            return RouteScore(telem.organ_id, -1e9, False, ("health RED",))

        is_external_host = cfg.get("kind") == "host_frankenstein"
        if task.heavy and is_external_host:
            if telem.age_seconds() > self.max_age:
                return RouteScore(telem.organ_id, -1e9, False, ("stale telemetry for heavy host fanout",))
            if telem.cpu_load is None or telem.ram_load is None:
                return RouteScore(telem.organ_id, -1e9, False, ("incomplete load telemetry for heavy host fanout",))
            if telem.resource_headroom < self.min_heavy_headroom:
                return RouteScore(telem.organ_id, -1e9, False, ("insufficient host resource headroom",))

        capability_fit = (
            1.0 if not task.required_capabilities
            else len(task.required_capabilities & available) / len(task.required_capabilities)
        )
        domains = set(telem.data_domains)
        data_locality = (
            0.0 if not task.preferred_data_domains
            else len(task.preferred_data_domains & domains) / len(task.preferred_data_domains)
        )
        freshness = max(
            0.0,
            1.0 - min(telem.age_seconds(), self.max_age * 2) / (self.max_age * 2),
        )
        effect_risk = 1.0 if task.high_risk_effect and is_external_host else 0.0

        metrics = {
            "capability_fit": capability_fit,
            "data_locality": data_locality,
            "state_freshness": freshness,
            "information_gain": telem.information_gain,
            "independence_for_falsification": telem.independence if task.wants_independent_falsifier else 0.0,
            "compute_availability": telem.resource_headroom,
            "latency": telem.latency_score,
            "bridge_health": telem.bridge_health,
            "host_resource_headroom": telem.resource_headroom,
            "effect_risk": effect_risk,
            "duplicate_work": 0.0,
        }
        score = sum(float(self.weights.get(k, 0.0)) * float(v) for k, v in metrics.items())
        reasons = tuple(
            f"{k}={v:.3f}" for k, v in metrics.items() if abs(float(v)) > 1e-9
        )
        return RouteScore(telem.organ_id, score, True, reasons)

    def choose(self, task: TaskRequest, telemetry: Iterable[OrganTelemetry]) -> RouteDecision:
        scores = [self._score(task, t) for t in telemetry]
        scores.sort(key=lambda x: (x.eligible, x.score), reverse=True)
        eligible = [x for x in scores if x.eligible]
        if not eligible:
            raise RuntimeError(f"no eligible organ for {task.task_id}")

        n = max(1, min(task.max_organs, len(eligible)))
        if task.wants_independent_falsifier and self.config.get("allow_multi_organ_coalitions", False):
            n = max(n, min(2, len(eligible)))
        selected = tuple(x.organ_id for x in eligible[:n])
        return RouteDecision(task.task_id, selected, tuple(scores))
