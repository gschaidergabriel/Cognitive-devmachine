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


def _runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _write_jsonl(path: Path, label: str) -> None:
    rows = [
        {"event_id": f"{label}-1", "text": f"{label}-first"},
        {"event_id": f"{label}-2", "text": f"{label}-second"},
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _profile(path: Path, namespace: str) -> dict:
    return {
        "sources": [
            {
                "kind": "events",
                "source_namespace": namespace,
                "adapter": "jsonl_cursor",
                "path": str(path),
                "limit": 1,
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
    }


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
def test_jsonl_cursor_identity_is_source_stable_not_kind_or_profile_bound(tmp_path: Path) -> None:
    """Cursor identity follows the logical source namespace across replaceable profiles.

    The consumed-row Exactly-Once contract already rejects `(kind,id)` aliasing and
    profile-id-keyed re-consumption. Cursor state is the streaming form of the same durable
    source identity: two logical sources may share a local `kind`, while one logical source
    must resume after a profile swap. The cursor map is treated as opaque here; only the
    externally visible source behavior is constrained.
    """
    runtime_module = _runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)}).get("ok") is True

    source_a = tmp_path / "a.jsonl"
    source_b = tmp_path / "b.jsonl"
    _write_jsonl(source_a, "A")
    _write_jsonl(source_b, "B")

    first_a = _collect(runtime, entity_db, _profile(source_a, "logical-A"), {})
    assert [row["event_id"] for row in first_a["sources"]["events"]["rows"]] == ["A-1"]

    first_b = _collect(
        runtime,
        entity_db,
        _profile(source_b, "logical-B"),
        first_a["next_cursors"],
    )
    assert [row["event_id"] for row in first_b["sources"]["events"]["rows"]] == ["B-1"], (
        "distinct logical jsonl sources sharing one kind inherited each other's cursor"
    )

    second_a = _collect(
        runtime,
        entity_db,
        _profile(source_a, "logical-A"),
        first_b["next_cursors"],
    )
    assert [row["event_id"] for row in second_a["sources"]["events"]["rows"]] == ["A-2"], (
        "the same logical jsonl source failed to resume after an intervening profile/source swap"
    )
