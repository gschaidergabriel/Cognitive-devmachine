from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_backfill_scheduler as scheduler


class _Base:
    @staticmethod
    def worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        return "ORIGINAL"


def _packet() -> dict:
    return {
        "historical_source_event_id": "event-1",
        "historical_chunk_id": "chunk-1",
        "extraction_pass": 3,
    }


def test_backfill_prompt_does_not_hardcode_exhaustive_true(monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: _packet())
    base = _Base()
    scheduler.install(base)
    prompt = base.worker_prompt("p", "r", "t", "s", 1)
    assert '"exhaustive":<true|false>' in prompt
    assert '"exhaustive":true,"deltas"' not in prompt
    assert "if you emit 8 deltas" in prompt
    assert "exhaustive MUST be false" in prompt


def test_every_reservable_slot_is_conversion_while_backlog_exists(monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: _packet())
    base = _Base()
    scheduler.install(base)
    # Serial values divisible by four used to bypass extraction and create new raw
    # research. They must now stay on the historical conversion transport as well.
    for serial in range(8):
        prompt = base.worker_prompt("p", "r", "t", "s", serial)
        assert "HISTORICAL FREE-SWARM BACKFILL OVERRIDE" in prompt


def test_lease_saturation_holds_instead_of_resuming_raw_prompt(monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: None)
    monkeypatch.setattr(scheduler, "_packets", lambda: [_packet()])
    base = _Base()
    scheduler.install(base)
    prompt = base.worker_prompt("p", "r", "t", "s", 0)
    assert prompt != "ORIGINAL"
    assert "HISTORICAL FREE-SWARM BACKFILL LEASE-SATURATION HOLD" in prompt
    assert "NO_DELTA: HISTORICAL_BACKFILL_LEASE_SATURATED" in prompt
    assert "ARCHITECTURE_DELTA_JSON" not in prompt


def test_raw_prompt_resumes_only_when_backfill_queue_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: None)
    monkeypatch.setattr(scheduler, "_packets", lambda: [])
    base = _Base()
    scheduler.install(base)
    assert base.worker_prompt("p", "r", "t", "s", 0) == "ORIGINAL"
