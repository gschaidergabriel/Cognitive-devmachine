from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _collect(runtime: ProfilePipelineRuntime, entity_db: Path, profile: dict, cursors: dict) -> dict:
    return runtime._pipeline_collect(
        {
            "entity_db": str(entity_db),
            "source_db": str(entity_db),
            "profile": profile,
            "previous": {"cursors": dict(cursors)},
        }
    )


def _single_cursor_value(cursors: dict) -> int:
    """Keep this regression neutral to the concrete namespaced cursor-map encoding."""
    assert len(cursors) == 1
    return int(next(iter(cursors.values())))


def test_incomplete_jsonl_tail_is_not_consumed_before_record_completion(tmp_path: Path) -> None:
    """Source-identity repair must preserve the already-correct partial-tail boundary."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)})["ok"] is True

    first_record = (json.dumps({"event_id": 1}, separators=(",", ":")) + "\n").encode()
    second_record = json.dumps({"event_id": 2}, separators=(",", ":")).encode()
    split = max(1, len(second_record) // 2)
    event_path = tmp_path / "events.jsonl"
    event_path.write_bytes(first_record + second_record[:split])

    profile = {
        "sources": [
            {
                "kind": "events",
                "source_namespace": "logical-events",
                "adapter": "jsonl_cursor",
                "path": "events.jsonl",
                "limit": 10,
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
    }

    first = _collect(runtime, entity_db, profile, {})
    assert first["sources"]["events"]["ok"] is True
    assert [row["event_id"] for row in first["sources"]["events"]["rows"]] == [1]
    assert _single_cursor_value(first["next_cursors"]) == len(first_record)

    with event_path.open("ab") as handle:
        handle.write(second_record[split:] + b"\n")

    second = _collect(runtime, entity_db, profile, first["next_cursors"])
    assert second["sources"]["events"]["ok"] is True
    assert [row["event_id"] for row in second["sources"]["events"]["rows"]] == [2]
    assert _single_cursor_value(second["next_cursors"]) == len(first_record) + len(second_record) + 1
