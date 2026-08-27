from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

scheduler = importlib.import_module("free_swarm_backfill_scheduler")


def _base():
    def original(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        return f"ORIGINAL:{protocol}:{role}:{task}:{state_context}:{serial}"

    return SimpleNamespace(worker_prompt=original), original


def _packet() -> dict[str, object]:
    return {
        "historical_source_event_id": "event-1",
        "historical_chunk_id": "chunk-1",
        "extraction_pass": 1,
        "chunk_text": "historical candidate source",
    }


def test_install_rebinds_exact_active_v5_frozen_prompt(monkeypatch) -> None:
    base, original = _base()
    v5 = SimpleNamespace(base=base, _ORIGINAL_WORKER_PROMPT=original)
    monkeypatch.setitem(sys.modules, "run_6000_free_swarm_v5", v5)
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: _packet())

    scheduler.install(base)

    # The active v5 path captured the pre-install predecessor during import. The
    # scheduler must replace exactly that reference with its canonical wrapper so
    # v5 Stage-1 prompt construction cannot bypass historical conversion.
    assert v5._ORIGINAL_WORKER_PROMPT is base.worker_prompt
    prompt = v5._ORIGINAL_WORKER_PROMPT("P", "R", "T", "S", 7)
    assert prompt.startswith("ORIGINAL:P:R:T:S:7")
    assert "HISTORICAL FREE-SWARM BACKFILL OVERRIDE" in prompt
    assert '"historical_chunk_id":"chunk-1"' in prompt


def test_install_does_not_overwrite_unknown_v5_prompt_authority(monkeypatch) -> None:
    base, _original = _base()

    def successor(*args, **kwargs):
        return "SUCCESSOR"

    v5 = SimpleNamespace(base=base, _ORIGINAL_WORKER_PROMPT=successor)
    monkeypatch.setitem(sys.modules, "run_6000_free_swarm_v5", v5)
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: _packet())

    scheduler.install(base)

    # Fail closed on successor drift: install() may own base.worker_prompt, but it
    # must not silently overwrite a v5 reference it did not capture as predecessor.
    assert v5._ORIGINAL_WORKER_PROMPT is successor


def test_rebound_v5_path_holds_instead_of_leaking_raw_when_packets_are_leased(monkeypatch) -> None:
    base, original = _base()
    v5 = SimpleNamespace(base=base, _ORIGINAL_WORKER_PROMPT=original)
    monkeypatch.setitem(sys.modules, "run_6000_free_swarm_v5", v5)
    monkeypatch.setattr(scheduler, "_reserve", lambda serial: None)
    monkeypatch.setattr(scheduler, "_packets", lambda: [_packet()])

    scheduler.install(base)
    prompt = v5._ORIGINAL_WORKER_PROMPT("P", "R", "T", "S", 9)

    assert "HISTORICAL FREE-SWARM BACKFILL HOLD" in prompt
    assert "NO_DELTA=HISTORICAL_BACKFILL_LEASE_BUSY" in prompt
    assert "Do NOT perform the ordinary research task" in prompt
