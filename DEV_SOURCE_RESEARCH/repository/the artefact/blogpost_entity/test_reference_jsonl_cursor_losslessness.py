from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _jsonl_reference_active() -> bool:
    if not RUNTIME_PATH.is_file():
        return False
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    return "def _pipeline_profile_read" in source and '"jsonl_cursor"' in source


def _load_runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _collect(runtime, entity_db: Path, profile: dict, cursors: dict) -> dict:
    return runtime._pipeline_collect(
        {
            "entity_db": str(entity_db),
            "source_db": str(entity_db),
            "profile": profile,
            "previous": {"cursors": dict(cursors)},
        }
    )


@pytest.mark.skipif(
    not _jsonl_reference_active(),
    reason="activates only when DB-profile reference convergence owns jsonl_cursor",
)
def test_jsonl_cursor_limit_never_skips_unprocessed_complete_records(tmp_path: Path) -> None:
    """Batch limit bounds work; it must never advance past records not yet returned.

    Reading the whole suffix, processing only ``parts[:limit]``, then advancing the cursor
    to the end of the whole suffix would silently drop every complete record after the
    limit. The cursor therefore has to advance exactly through the records admitted into
    this batch (while an incomplete trailing record remains unconsumed).
    """

    runtime_module = _load_runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    initialized = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert initialized.get("ok") is True

    records = [
        {"event_id": index, "text": f"event-{index}"}
        for index in range(1, 6)
    ]
    encoded = [
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for record in records
    ]
    event_path = tmp_path / "events.jsonl"
    event_path.write_bytes(b"".join(encoded))

    after_two = len(b"".join(encoded[:2]))
    after_four = len(b"".join(encoded[:4]))
    after_five = len(b"".join(encoded))

    profile = {
        "sources": [
            {
                "kind": "events",
                "adapter": "jsonl_cursor",
                "path": "events.jsonl",
                "limit": 2,
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
    }

    first = _collect(runtime, entity_db, profile, {})
    assert first.get("ok") is True
    assert first["sources"]["events"]["ok"] is True
    assert [row["event_id"] for row in first["sources"]["events"]["rows"]] == [1, 2]
    assert first["next_cursors"]["events"] == after_two, (
        "jsonl cursor advanced beyond records actually admitted into the first limited batch"
    )

    second = _collect(runtime, entity_db, profile, first["next_cursors"])
    assert second["sources"]["events"]["ok"] is True
    assert [row["event_id"] for row in second["sources"]["events"]["rows"]] == [3, 4]
    assert second["next_cursors"]["events"] == after_four

    third = _collect(runtime, entity_db, profile, second["next_cursors"])
    assert third["sources"]["events"]["ok"] is True
    assert [row["event_id"] for row in third["sources"]["events"]["rows"]] == [5]
    assert third["next_cursors"]["events"] == after_five

    observed = [
        row["event_id"]
        for batch in (first, second, third)
        for row in batch["sources"]["events"]["rows"]
    ]
    assert observed == [1, 2, 3, 4, 5], (
        "limited jsonl batching lost, duplicated, or reordered source records"
    )
