#!/usr/bin/env python3
"""Model-level health, circuit breaking, and weighted routing for the 6000 FREE swarm.

This layer is intentionally below canonical truth/effect authority. It only changes
which already-admitted exact FREE model route receives a research shard. The epoch
8.71 credential+route gate in ``run_6000_free_swarm_v3`` remains the final network
authority and cannot be bypassed by model health scores.

Goals:
- stop wasting calls on deterministic model-specific 4xx failures;
- quarantine repeated 5xx/network faults at model scope instead of collapsing an
  otherwise healthy provider;
- allocate work by measured success x latency x delta/Forge yield;
- seed health and last healthy provider concurrency from append-only runtime
  artifacts so a supervisor restart does not forget everything it just learned.
"""
from __future__ import annotations

import collections
import json
import math
import os
from pathlib import Path
import threading
import time
from typing import Any

ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
HARD_4XX_THRESHOLD = max(2, int(os.getenv("CLAY_MODEL_HARD_4XX_THRESHOLD", "3")))
TRANSIENT_5XX_THRESHOLD = max(2, int(os.getenv("CLAY_MODEL_5XX_COOLDOWN_THRESHOLD", "3")))
MODEL_MIN_EXPLORATION = max(1, int(os.getenv("CLAY_MODEL_MIN_EXPLORATION", "3")))
_LOCK = threading.RLock()
_HEALTH: dict[tuple[str, str], dict[str, Any]] = {}
_SEEDED = False
_FORGE_MTIME_NS = -1
_LAST_FORGE_REFRESH = 0.0


def _blank() -> dict[str, Any]:
    return {
        "total": 0,
        "success": 0,
        "hard_4xx": 0,
        "transient_5xx": 0,
        "network_errors": 0,
        "rate_429": 0,
        "delta_markers": 0,
        "accepted_deltas": 0,
        "latency_ema_s": None,
        "consecutive_hard": 0,
        "consecutive_transient": 0,
        "cooldown_until": 0.0,
        "disabled": False,
        "disabled_reason": None,
    }


def _health(provider: str, model: str) -> dict[str, Any]:
    return _HEALTH.setdefault((provider, model), _blank())


def _status_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _update_latency(row: dict[str, Any], elapsed_s: float | None) -> None:
    if elapsed_s is None or elapsed_s <= 0:
        return
    old = row.get("latency_ema_s")
    row["latency_ema_s"] = float(elapsed_s) if old is None else 0.82 * float(old) + 0.18 * float(elapsed_s)


def _record_result(
    provider: str,
    model: str,
    status: Any,
    elapsed_s: float | None = None,
    *,
    delta_marker: bool = False,
    historical: bool = False,
) -> dict[str, Any]:
    """Record one exact model result without ever looking at credential values."""
    code = _status_int(status)
    now = time.monotonic()
    with _LOCK:
        row = _health(provider, model)
        row["total"] += 1
        _update_latency(row, elapsed_s)
        if code is not None and 200 <= code < 300:
            row["success"] += 1
            row["consecutive_hard"] = 0
            row["consecutive_transient"] = 0
            if delta_marker:
                row["delta_markers"] += 1
        elif code == 429:
            row["rate_429"] += 1
            row["consecutive_hard"] = 0
        elif code is not None and 500 <= code < 600:
            row["transient_5xx"] += 1
            row["consecutive_transient"] += 1
            row["consecutive_hard"] = 0
            if not historical and row["consecutive_transient"] >= TRANSIENT_5XX_THRESHOLD:
                exponent = min(4, row["consecutive_transient"] - TRANSIENT_5XX_THRESHOLD)
                row["cooldown_until"] = max(row["cooldown_until"], now + min(300.0, 30.0 * (2 ** exponent)))
        elif status == "NETWORK_EXCEPTION":
            row["network_errors"] += 1
            row["consecutive_transient"] += 1
            row["consecutive_hard"] = 0
            if not historical and row["consecutive_transient"] >= TRANSIENT_5XX_THRESHOLD:
                row["cooldown_until"] = max(row["cooldown_until"], now + 30.0)
        elif code is not None and 400 <= code < 500 and code not in {401, 402, 403, 404, 409, 429, 460}:
            row["hard_4xx"] += 1
            row["consecutive_hard"] += 1
            row["consecutive_transient"] = 0
            # Three deterministic request-shape/model failures with zero success are
            # enough to quarantine the exact model. Provider/key siblings stay live.
            if row["success"] == 0 and (
                row["hard_4xx"] >= HARD_4XX_THRESHOLD
                or row["consecutive_hard"] >= HARD_4XX_THRESHOLD
            ):
                row["disabled"] = True
                row["disabled_reason"] = f"MODEL_HARD_4XX_CIRCUIT:{code}"
        return dict(row)


def _quality_weight(row: dict[str, Any]) -> float:
    total = int(row.get("total") or 0)
    success = int(row.get("success") or 0)
    hard = int(row.get("hard_4xx") or 0)
    transient = int(row.get("transient_5xx") or 0) + int(row.get("network_errors") or 0)
    markers = int(row.get("delta_markers") or 0)
    accepted = int(row.get("accepted_deltas") or 0)
    if row.get("disabled"):
        return 0.0
    if float(row.get("cooldown_until") or 0.0) > time.monotonic():
        return 0.0
    if total < MODEL_MIN_EXPLORATION:
        return 4.0 / (1.0 + total)

    # Bayesian smoothing prevents one lucky request from monopolizing the fabric.
    reliability = (success + 2.0) / (total + 4.0)
    marker_rate = (markers + 0.25) / (success + 1.0)
    accepted_rate = (accepted + 0.10) / (success + 1.0)
    latency = max(0.25, float(row.get("latency_ema_s") or 12.0))
    error_penalty = 1.0 / (1.0 + 0.45 * hard + 0.12 * transient)
    # sqrt latency keeps slower high-yield reasoning models competitive while still
    # rewarding fast models. Accepted Forge deltas outweigh mere marker volume.
    value = reliability * (1.0 + 2.0 * marker_rate + 5.0 * accepted_rate)
    return max(0.001, value * error_penalty / math.sqrt(latency))


def _seed_from_workers() -> None:
    global _SEEDED
    with _LOCK:
        if _SEEDED:
            return
        _SEEDED = True
    try:
        runs = sorted(
            ARTIFACT_ROOT.glob("active-fabric6000-v2-*/workers.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:4]
    except OSError:
        return
    for path in reversed(runs):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= 9000:
                        break
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    provider = str(obj.get("provider") or "")
                    model = str(obj.get("model") or "")
                    if not provider or not model:
                        continue
                    conf = obj.get("conformance") or {}
                    _record_result(
                        provider,
                        model,
                        obj.get("http_status"),
                        float(obj.get("elapsed_s") or 0.0) or None,
                        delta_marker=bool(isinstance(conf, dict) and conf.get("architecture_delta_marker")),
                        historical=True,
                    )
        except OSError:
            continue


def _refresh_forge_acceptance(force: bool = False) -> None:
    global _FORGE_MTIME_NS, _LAST_FORGE_REFRESH
    now = time.monotonic()
    if not force and now - _LAST_FORGE_REFRESH < 30.0:
        return
    _LAST_FORGE_REFRESH = now
    path = ARTIFACT_ROOT / "forge/architecture_delta_evaluations.jsonl"
    try:
        stat = path.stat()
    except OSError:
        return
    if not force and stat.st_mtime_ns == _FORGE_MTIME_NS:
        return
    _FORGE_MTIME_NS = stat.st_mtime_ns
    accepted: collections.Counter[tuple[str, str]] = collections.Counter()
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict) and str(obj.get("status") or "").lower() == "accepted":
                    p = str(obj.get("provider") or "")
                    m = str(obj.get("model") or "")
                    if p and m:
                        accepted[(p, m)] += 1
    except OSError:
        return
    with _LOCK:
        for row in _HEALTH.values():
            row["accepted_deltas"] = 0
        for key, count in accepted.items():
            _health(*key)["accepted_deltas"] = int(count)


def _public_model_health(provider: str, model: str) -> dict[str, Any]:
    with _LOCK:
        row = dict(_health(provider, model))
    remaining = max(0.0, float(row.pop("cooldown_until", 0.0)) - time.monotonic())
    row["cooldown_seconds"] = round(remaining, 2)
    row["routing_weight"] = round(_quality_weight({**row, "cooldown_until": time.monotonic() + remaining if remaining else 0.0}), 6)
    return row


def _last_healthy_target(provider: str) -> int | None:
    try:
        statuses = sorted(
            ARTIFACT_ROOT.glob("active-fabric6000-v2-*/status.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:6]
    except OSError:
        return None
    for path in statuses:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            row = ((obj.get("providers") or {}).get(provider) or {})
            target = int(row.get("target_concurrency") or 0)
            active = int(row.get("active") or 0)
            success = int(row.get("successes") or 0)
            cooldown = float(row.get("cooldown_seconds") or 0.0)
        except Exception:
            continue
        if target > 0 and success >= 5 and cooldown <= 0.0 and active >= max(1, int(0.55 * target)):
            return target
    return None


def install_scheduler(fabric: Any) -> None:
    """Install before importing v3 so its economic gate wraps this selector."""
    _seed_from_workers()
    _refresh_forge_acceptance(force=True)
    cls = fabric.FastProviderRuntime
    if getattr(cls, "_model_health_v1_installed", False):
        return
    cls._model_health_v1_installed = True
    old_init = cls.__init__
    old_snapshot = cls.snapshot
    old_initial_target = fabric._initial_target

    def init(self, spec, keys, models, max_concurrency):
        old_init(self, spec, keys, models, max_concurrency)
        self._mh_key_cursor = 0
        self._mh_credit = {m: 0.0 for m in self.models}

    def next_key_model(self):
        _refresh_forge_acceptance()
        keys = self.enabled_keys()
        models = self.enabled_models()
        if not keys or not models:
            return None
        weighted: list[tuple[str, float]] = []
        total_weight = 0.0
        for model in models:
            with _LOCK:
                weight = _quality_weight(_health(self.spec.name, model))
            if weight <= 0:
                continue
            weighted.append((model, weight))
            total_weight += weight
            self._mh_credit[model] = self._mh_credit.get(model, 0.0) + weight
        if not weighted or total_weight <= 0:
            return None
        model = max(weighted, key=lambda pair: (self._mh_credit.get(pair[0], 0.0), pair[0]))[0]
        self._mh_credit[model] -= total_weight
        key = keys[self._mh_key_cursor % len(keys)]
        self._mh_key_cursor += 1
        return key, model

    async def isolated_transient(self):
        # Exact model cooldown is recorded by the request observer. Do not punish
        # every sibling model/provider slot for one model-specific 5xx.
        async with self._condition:
            self.errors += 1
            self.success_streak = 0
            self._condition.notify_all()

    def snapshot(self):
        out = old_snapshot(self)
        out["model_scheduler"] = "WEIGHTED_SUCCESS_LATENCY_DELTA_V1"
        out["model_hard_4xx_threshold"] = HARD_4XX_THRESHOLD
        out["model_health"] = {m: _public_model_health(self.spec.name, m) for m in self.models}
        return out

    def initial_target(runtime, shared):
        default = old_initial_target(runtime, shared)
        persisted = _last_healthy_target(runtime.spec.name)
        if persisted is None:
            return default
        return max(1, min(runtime.max_concurrency, persisted))

    cls.__init__ = init
    cls.next_key_model = next_key_model
    cls.on_transient_error = isolated_transient
    cls.snapshot = snapshot
    fabric._initial_target = initial_target


def bind_request_observer(v3: Any) -> None:
    """Install after v3 so observations wrap, never replace, its exact FREE gate."""
    target = v3.fabric
    current = target.base.request_chat
    if getattr(current, "_model_health_v1_observer", False):
        return

    def observed_request(spec, key, model, prompt, max_tokens, timeout):
        started = time.monotonic()
        try:
            status, headers, payload = current(spec, key, model, prompt, max_tokens, timeout)
        except Exception:
            _record_result(spec.name, model, "NETWORK_EXCEPTION", time.monotonic() - started)
            raise
        elapsed = time.monotonic() - started
        delta = False
        if isinstance(status, int) and 200 <= status < 300:
            try:
                delta = "ARCHITECTURE_DELTA_JSON=" in target.base.extract_text(payload)
            except Exception:
                delta = False
        _record_result(spec.name, model, status, elapsed, delta_marker=delta)
        return status, headers, payload

    observed_request._model_health_v1_observer = True
    target.base.request_chat = observed_request


def health_snapshot() -> dict[str, Any]:
    _refresh_forge_acceptance()
    with _LOCK:
        keys = sorted(_HEALTH)
    return {
        "schema": "CLAY_FREE_SWARM_MODEL_HEALTH/v1",
        "generated_at_monotonic": time.monotonic(),
        "models": {
            f"{provider}:{model}": _public_model_health(provider, model)
            for provider, model in keys
        },
    }
