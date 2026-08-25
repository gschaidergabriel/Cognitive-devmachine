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


def test_backfill_prompt_does_not_hardcode_exhaustive_true(monkeypatch) -> None:
    monkeypatch.setattr(
        scheduler,
        "_reserve",
        lambda serial: {
            "historical_source_event_id": "event-1",
            "historical_chunk_id": "chunk-1",
            "extraction_pass": 3,
        },
    )
    base = _Base()
    scheduler.install(base)
    prompt = base.worker_prompt("p", "r", "t", "s", 1)
    assert '"exhaustive":<true|false>' in prompt
    assert '"exhaustive":true,"deltas"' not in prompt
    assert "if you emit 8 deltas" in prompt
    assert "exhaustive MUST be false" in prompt
