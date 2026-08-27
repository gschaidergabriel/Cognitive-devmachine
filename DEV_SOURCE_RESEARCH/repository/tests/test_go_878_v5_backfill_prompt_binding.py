from __future__ import annotations

import sys
from types import SimpleNamespace

import free_swarm_backfill_scheduler as scheduler


def _ordinary_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    return "ORDINARY"


def test_install_rebinds_current_v5_frozen_prompt_through_backfill(monkeypatch):
    base = SimpleNamespace(worker_prompt=_ordinary_prompt)
    v5 = SimpleNamespace(base=base, _ORIGINAL_WORKER_PROMPT=_ordinary_prompt)
    monkeypatch.setitem(sys.modules, "run_6000_free_swarm_v5", v5)
    monkeypatch.setattr(
        scheduler,
        "_reserve",
        lambda serial: {
            "historical_source_event_id": "event-1",
            "historical_chunk_id": "chunk-1",
            "extraction_pass": 1,
        },
    )

    scheduler.install(base)

    # The current v5 proposal path uses its captured reference, so installation
    # must rebind that exact predecessor to the one canonical backlog wrapper.
    assert v5._ORIGINAL_WORKER_PROMPT is base.worker_prompt
    prompt = v5._ORIGINAL_WORKER_PROMPT("protocol", "role", "task", "state", 1)
    assert prompt.startswith("ORDINARY")
    assert "HISTORICAL FREE-SWARM BACKFILL OVERRIDE" in prompt
    assert '"historical_chunk_id":"chunk-1"' in prompt


def test_install_does_not_manufacture_v5_prompt_authority_after_successor_change(monkeypatch):
    base = SimpleNamespace(worker_prompt=_ordinary_prompt)

    def successor_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        return "SUCCESSOR"

    v5 = SimpleNamespace(base=base, _ORIGINAL_WORKER_PROMPT=successor_prompt)
    monkeypatch.setitem(sys.modules, "run_6000_free_swarm_v5", v5)
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: None)
    monkeypatch.setattr(scheduler, "_packets", lambda: [])

    scheduler.install(base)

    assert base.worker_prompt is not _ordinary_prompt
    assert v5._ORIGINAL_WORKER_PROMPT is successor_prompt
