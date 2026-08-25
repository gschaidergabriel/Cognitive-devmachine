#!/usr/bin/env python3
"""Backlog scheduler for historical Free-Swarm output re-evaluation.

When the Forge historical-extraction queue is non-empty, logical research calls
are repurposed as bounded extraction passes over old worker outputs. This preserves
the 6000 fabric as the extraction transport while preventing new raw-research scale
from competing with the historical conversion backlog. Once no extraction packet is
available, the ordinary prompt path resumes automatically.

This changes allocation, not evidence authority: extracted deltas remain noncanonical
and still traverse the same Forge validation path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any

import free_swarm_historical_backfill as historical_backfill_core
from free_swarm_backfill_exhaustiveness_878 import install as install_exhaustiveness

# Keep producer-side packet scheduling on the same completion semantics as the
# backlog-first Forge consumer. This changes no evidence authority.
install_exhaustiveness(historical_backfill_core)
load_backfill_packets = historical_backfill_core.load_backfill_packets

ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
FORGE_DB = ARTIFACT_ROOT / "forge/forge.sqlite3"
CACHE_SECONDS = 3.0
LEASE_SECONDS = 240.0
MAX_PACKET_CACHE = 2048

_lock = threading.Lock()
_cache_at = 0.0
_cache: list[dict[str, Any]] = []
_leases: dict[str, float] = {}


def _packets() -> list[dict[str, Any]]:
    global _cache_at, _cache
    now = time.monotonic()
    with _lock:
        if now - _cache_at < CACHE_SECONDS:
            return list(_cache)
    rows = load_backfill_packets(FORGE_DB, limit=MAX_PACKET_CACHE)
    with _lock:
        _cache_at = now
        _cache = rows
    return list(rows)


def _reserve(serial: int) -> dict[str, Any] | None:
    now = time.monotonic()
    rows = _packets()
    if not rows:
        return None
    with _lock:
        expired = [key for key, until in _leases.items() if until <= now]
        for key in expired:
            _leases.pop(key, None)
        start = serial % len(rows)
        for offset in range(len(rows)):
            row = rows[(start + offset) % len(rows)]
            chunk_id = str(row.get("historical_chunk_id") or "")
            if not chunk_id or _leases.get(chunk_id, 0.0) > now:
                continue
            _leases[chunk_id] = now + LEASE_SECONDS
            return row
    return None


def install(base: Any) -> None:
    previous = base.worker_prompt

    def backlog_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        original = previous(protocol, role, task, state_context, serial)
        # Liveness rule: the same fabric carries historical extraction, therefore
        # keep it alive and devote every reservable slot to conversion while the
        # historical queue is non-empty. Ordinary raw research resumes only when
        # the queue itself is empty, not merely when all visible chunks are leased.
        packet = _reserve(serial)
        if packet is None:
            if _packets():
                return original + """

HISTORICAL FREE-SWARM BACKFILL HOLD
- Historical extraction backlog still exists, but all currently visible chunks are leased to sibling calls.
- Do NOT perform the ordinary research task and do NOT emit ARCHITECTURE_DELTA_JSON.
- Emit exactly NO_DELTA=HISTORICAL_BACKFILL_LEASE_BUSY, then OPEN_RESEARCH_QUESTIONS_JSON=[] .
- This hold is allocation control only and grants zero evidence or acceptance credit.
"""
            return original
        payload = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
        return original + f"""

HISTORICAL FREE-SWARM BACKFILL OVERRIDE
{payload}

BACKFILL LAW
- This is an old successful worker-output chunk, not current truth and not execution authority.
- Re-read the complete supplied chunk. Extract EVERY materially distinct EntityOS/HCU architecture delta
  actually supported by its text. Do not collapse distinct mechanisms merely because they share a topic.
- Do not invent missing source bytes, measurements, patches, or PASS states.
- A candidate without an executable patch is still useful: emit it with ready_for_forge=false so it enters
  the implementation queue instead of being discarded.
- Dedupe against known_concept_ids conceptually; do not emit paraphrase-only duplicates.
- Preserve counterhypotheses as separate candidates only when they imply a different executable discriminator.
- Return at most 8 deltas in this pass.
- Set exhaustive=false whenever more materially distinct deltas may remain. In particular, if you emit 8 deltas,
  exhaustive MUST be false unless the supplied chunk unambiguously contains no ninth distinct delta.
- Set exhaustive=true only after you have inspected the complete supplied chunk and can affirm that this pass
  exhausted every materially distinct delta not already covered by known_concept_ids.
- A zero-delta pass is not enough to close a chunk. SATURATED requires two consecutive zero-novel passes
  whose envelopes both explicitly assert exhaustive=true.
- This extraction pass grants ZERO acceptance credit. Every emitted delta still goes through the one canonical Forge.

For this call, replace the ordinary single ARCHITECTURE_DELTA_JSON line with exactly:
ARCHITECTURE_DELTA_BATCH_JSON={{"historical_source_event_id":"{packet.get('historical_source_event_id')}","historical_chunk_id":"{packet.get('historical_chunk_id')}","extraction_pass":{int(packet.get('extraction_pass') or 1)},"exhaustive":<true|false>,"deltas":[<0..8 normal architecture-delta objects>]}}
Then emit the normal OPEN_RESEARCH_QUESTIONS_JSON line.
Each delta object must use the normal schema and include the same historical_source_event_id,
historical_chunk_id and extraction_pass fields. Use ready_for_forge=true only with a real unified diff,
declared target_files and bounded test_commands.
"""
    base.worker_prompt = backlog_prompt

    # Current v5 captures base.worker_prompt during import, before this scheduler
    # is installed by run_6000_free_swarm_fast.py. Rebind only that exact captured
    # predecessor so the final v5 proposal path actually traverses the canonical
    # backlog wrapper. If v5 has evolved away from the frozen reference, leave it
    # untouched rather than creating a second prompt authority.
    v5 = sys.modules.get("run_6000_free_swarm_v5")
    if v5 is not None and getattr(v5, "base", None) is base:
        if getattr(v5, "_ORIGINAL_WORKER_PROMPT", None) is previous:
            v5._ORIGINAL_WORKER_PROMPT = backlog_prompt
