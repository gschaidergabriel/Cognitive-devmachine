from __future__ import annotations

import json
from pathlib import Path

from tools.tool_version_index_generate import build_index, serialize
from tools.tool_version_index_lint import lint_root


def _write(path: Path, text: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path):
    _write(tmp_path / "tools" / "demo_v1.py", "print('old')\n")
    _write(tmp_path / "tools" / "demo_v2.py", "print('new')\n")
    _write(tmp_path / ".github" / "workflows" / "use.yml", "run: python tools/demo_v1.py\n")
    index = build_index(tmp_path)
    index_path = tmp_path / "research_entity" / "tooling" / "TOOL_VERSION_INDEX.json"
    _write(index_path, serialize(index))
    allow_path = tmp_path / "research_entity" / "tooling" / "TOOL_VERSION_HISTORICAL_ALLOWLIST.json"
    _write(allow_path, json.dumps({"schema":"TOOL_VERSION_HISTORICAL_ALLOWLIST/v1","entries":[]}, indent=2)+"\n")
    return index, index_path, allow_path


def test_highest_numeric_version_is_live(tmp_path: Path):
    index, _, _ = _fixture(tmp_path)
    rows = {row["path"]: row["status"] for row in index["tools"]}
    assert rows["tools/demo_v1.py"] == "SUPERSEDED"
    assert rows["tools/demo_v2.py"] == "LIVE"


def test_generation_is_byte_deterministic(tmp_path: Path):
    first = serialize(build_index(tmp_path))
    second = serialize(build_index(tmp_path))
    assert first == second


def test_synthetic_active_superseded_reference_fails(tmp_path: Path):
    _, index_path, allow_path = _fixture(tmp_path)
    result = lint_root(tmp_path, index_path, allow_path)
    assert result["ok"] is False
    assert result["stale_references"] == [
        {"referrer": ".github/workflows/use.yml", "tool": "tools/demo_v1.py"}
    ]


def test_reasoned_exact_allowlist_clears_historical_reference(tmp_path: Path):
    _, index_path, allow_path = _fixture(tmp_path)
    _write(
        allow_path,
        json.dumps(
            {
                "schema": "TOOL_VERSION_HISTORICAL_ALLOWLIST/v1",
                "entries": [
                    {
                        "referrer": ".github/workflows/use.yml",
                        "tool": "tools/demo_v1.py",
                        "reason": "fixture intentionally exercises the historical implementation",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
    )
    result = lint_root(tmp_path, index_path, allow_path)
    assert result["ok"] is True
    assert len(result["allowed_references"]) == 1


def test_allowlist_requires_reason(tmp_path: Path):
    _, index_path, allow_path = _fixture(tmp_path)
    _write(
        allow_path,
        json.dumps(
            {
                "schema": "TOOL_VERSION_HISTORICAL_ALLOWLIST/v1",
                "entries": [
                    {
                        "referrer": ".github/workflows/use.yml",
                        "tool": "tools/demo_v1.py",
                        "reason": "",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
    )
    result = lint_root(tmp_path, index_path, allow_path)
    assert result["ok"] is False
    assert any("missing_reason" in e for e in result["errors"])
