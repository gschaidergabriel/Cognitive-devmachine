from __future__ import annotations

import concurrent.futures
import json
import os
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

from .unified_store import now

NO_AUTOMATIC_SUBMIT_STATES = frozenset({"DISPATCHING", "COMPLETED", "BLOCKED", "UNKNOWN", "FAILED"})


class RelayLike(Protocol):
    runtime_root: Path
    store: Any

    def process_intent(self, path: Path) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class RelayCandidate:
    path: Path
    effect_id: str
    organ_id: str


@dataclass(slots=True)
class InflightEffect:
    effect_id: str
    organ_id: str
    started_at: str
    started_monotonic: float
    future: concurrent.futures.Future[Any]


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def choose_submit_candidates(
    candidates: Iterable[RelayCandidate],
    *,
    inflight_organs: Iterable[str],
    per_organ_limit: int,
    capacity: int,
) -> list[RelayCandidate]:
    """Bound fan-out without letting one stalled organ monopolize the relay."""
    limit = max(1, int(per_organ_limit))
    remaining = max(0, int(capacity))
    counts = Counter(str(x) for x in inflight_organs)
    selected: list[RelayCandidate] = []
    for candidate in candidates:
        if remaining <= 0:
            break
        if counts[candidate.organ_id] >= limit:
            continue
        selected.append(candidate)
        counts[candidate.organ_id] += 1
        remaining -= 1
    return selected


class NonBlockingRelay:
    """Bounded scheduler around the canonical OMEGA Relay.

    Effect authority, binding, host attribution, receipt verification, UnifiedDB state
    and UNKNOWN/no-replay remain entirely inside ``Relay.process_intent``. This layer
    only prevents receipt latency on one organ from freezing unrelated organs.
    """

    def __init__(
        self,
        relay: RelayLike,
        *,
        interval: float = 0.5,
        max_workers: int = 4,
        per_organ_limit: int = 1,
        long_running_seconds: float = 15.0,
    ) -> None:
        self.relay = relay
        self.interval = max(0.1, float(interval))
        self.max_workers = max(1, min(32, int(max_workers)))
        self.per_organ_limit = max(1, min(8, int(per_organ_limit)))
        self.long_running_seconds = max(1.0, float(long_running_seconds))
        self.inflight: dict[str, InflightEffect] = {}
        self.last_progress_at = now()
        self.status_path = relay.runtime_root / "RELAY_STATUS.json"
        self.error_path = relay.runtime_root / "relay_results" / "LAST_RELAY_SCHEDULER_ERROR.json"

    def _ledger_states(self) -> dict[str, str]:
        with self.relay.store.connect() as con:
            rows = con.execute("SELECT effect_id,state FROM relay_ledger").fetchall()
        return {str(row[0]): str(row[1]) for row in rows}

    def discover(self) -> list[RelayCandidate]:
        ledger = self._ledger_states()
        found: list[RelayCandidate] = []
        for path in sorted((self.relay.runtime_root / "outbox").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if payload.get("schema") != "OMEGA_GRID_EFFECT_INTENT/v1":
                continue
            effect_id = str(payload.get("effect_id", ""))
            organ_id = str(payload.get("organ_id", ""))
            if not effect_id or not organ_id or effect_id in self.inflight:
                continue
            if ledger.get(effect_id) in NO_AUTOMATIC_SUBMIT_STATES:
                continue
            found.append(RelayCandidate(path=path, effect_id=effect_id, organ_id=organ_id))
        return found

    def reap(self) -> list[dict[str, Any]]:
        completed: list[dict[str, Any]] = []
        for effect_id, item in list(self.inflight.items()):
            if not item.future.done():
                continue
            try:
                result = item.future.result()
                completed.append({"effect_id": effect_id, "organ_id": item.organ_id, "result": result})
            except Exception as exc:
                error = {
                    "at": now(),
                    "effect_id": effect_id,
                    "organ_id": item.organ_id,
                    "error": f"{type(exc).__name__}:{exc}",
                }
                _atomic_json(self.error_path, error)
                completed.append({**error, "result": None})
            del self.inflight[effect_id]
            self.last_progress_at = now()
        return completed

    def submit(self, pool: concurrent.futures.Executor, candidates: list[RelayCandidate]) -> list[str]:
        selected = choose_submit_candidates(
            candidates,
            inflight_organs=(item.organ_id for item in self.inflight.values()),
            per_organ_limit=self.per_organ_limit,
            capacity=self.max_workers - len(self.inflight),
        )
        submitted: list[str] = []
        for candidate in selected:
            started_at = now()
            future = pool.submit(self.relay.process_intent, candidate.path)
            self.inflight[candidate.effect_id] = InflightEffect(
                effect_id=candidate.effect_id,
                organ_id=candidate.organ_id,
                started_at=started_at,
                started_monotonic=time.monotonic(),
                future=future,
            )
            submitted.append(candidate.effect_id)
        if submitted:
            self.last_progress_at = now()
        return submitted

    def snapshot(self, *, queued: int, submitted: list[str], completed: list[dict[str, Any]]) -> dict[str, Any]:
        current = time.monotonic()
        inflight: list[dict[str, Any]] = []
        long_running: list[dict[str, Any]] = []
        for item in self.inflight.values():
            age = max(0.0, current - item.started_monotonic)
            row = {
                "effect_id": item.effect_id,
                "organ_id": item.organ_id,
                "started_at": item.started_at,
                "age_seconds": round(age, 3),
            }
            inflight.append(row)
            if age >= self.long_running_seconds:
                long_running.append(row)
        payload = {
            "schema": "OMEGA_RELAY_STATUS/v2",
            "mode": "BOUNDED_NONBLOCKING",
            "updated_at": now(),
            "last_progress_at": self.last_progress_at,
            "pid": os.getpid(),
            "max_workers": self.max_workers,
            "per_organ_limit": self.per_organ_limit,
            "queued_eligible": int(queued),
            "submitted_effect_ids": submitted,
            "completed_count": len(completed),
            "inflight": sorted(inflight, key=lambda x: (x["organ_id"], x["effect_id"])),
            "long_running": sorted(long_running, key=lambda x: (x["organ_id"], x["effect_id"])),
        }
        _atomic_json(self.status_path, payload)
        return payload

    def step(self, pool: concurrent.futures.Executor) -> dict[str, Any]:
        completed = self.reap()
        candidates = self.discover()
        submitted = self.submit(pool, candidates)
        return self.snapshot(queued=len(candidates), submitted=submitted, completed=completed)

    def run_forever(self) -> None:
        pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="omega-relay",
        )
        try:
            while True:
                try:
                    self.step(pool)
                except Exception as exc:
                    _atomic_json(
                        self.error_path,
                        {"at": now(), "error": f"{type(exc).__name__}:{exc}"},
                    )
                time.sleep(self.interval)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)


__all__ = [
    "InflightEffect",
    "NonBlockingRelay",
    "NO_AUTOMATIC_SUBMIT_STATES",
    "RelayCandidate",
    "choose_submit_candidates",
]
