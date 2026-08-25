from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "free swarm" / "go_collective_metrics_freshness.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def seed_repo(repo: Path, *, minute: int = 0, total_tokens: int = 100) -> None:
    write_json(repo / "free swarm/LIVE_METRICS.json", {
        "generated_at": f"2026-08-25T02:{minute:02d}:01+00:00",
        "total_tokens": total_tokens,
    })
    write_json(repo / "free swarm/FORGE_LIVE.json", {
        "generated_at": f"2026-08-25T02:{minute:02d}:02+00:00",
        "evaluated": 70,
        "accepted": 55,
    })
    write_json(repo / "free swarm/DISTILLERY_LIVE.json", {
        "generated_at": f"2026-08-25T02:{minute:02d}:03+00:00",
        "accepted_dataset_tokens": 0,
    })
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "selected": {"schema_version": "8.77", "source": "SUPERVISOR_STEERING_8_77.json"},
    })


def base_result() -> dict:
    return {
        "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
        "generated_at": "2026-08-25T02:59:00+00:00",
        "aggregate": {"worker_records": 1},
        "runtime_credit_added": 0,
    }


def test_same_bounded_inputs_have_same_snapshot_and_result_digest(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    one = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:00:00+00:00")
    two = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T04:00:00+00:00")
    assert one["freshness_gate"]["source_snapshot_id"] == two["freshness_gate"]["source_snapshot_id"]
    assert one["freshness_gate"]["result_digest"] == two["freshness_gate"]["result_digest"]
    assert one["live_projection"]["source_snapshot_id"] == one["freshness_gate"]["source_snapshot_id"]


def test_newer_live_input_changes_snapshot_and_result_digest(tmp_path: Path) -> None:
    seed_repo(tmp_path, minute=0, total_tokens=100)
    old = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:00:00+00:00")
    seed_repo(tmp_path, minute=1, total_tokens=101)
    new = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:01:00+00:00")
    assert old["freshness_gate"]["source_snapshot_id"] != new["freshness_gate"]["source_snapshot_id"]
    assert old["freshness_gate"]["result_digest"] != new["freshness_gate"]["result_digest"]
    assert new["free_swarm_tokens"] == 101


def test_older_writer_cannot_overwrite_newer_publication(tmp_path: Path) -> None:
    out_json = tmp_path / "published/GO_COLLECTIVE_METRICS.json"
    out_md = tmp_path / "published/GO_COLLECTIVE_METRICS.md"

    seed_repo(tmp_path, minute=2, total_tokens=102)
    newer = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:02:00+00:00")
    fresh.publish_fail_closed(out_json, out_md, newer, "new\n")

    seed_repo(tmp_path, minute=1, total_tokens=101)
    older = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:03:00+00:00")
    with pytest.raises(fresh.FreshnessError, match="OUT_OF_ORDER_SOURCE_SNAPSHOT"):
        fresh.publish_fail_closed(out_json, out_md, older, "old\n")

    published = json.loads(out_json.read_text(encoding="utf-8"))
    assert published["free_swarm_tokens"] == 102
    assert out_md.read_text(encoding="utf-8") == "new\n"


def test_same_max_time_but_different_snapshot_fails_closed(tmp_path: Path) -> None:
    seed_repo(tmp_path, minute=2, total_tokens=102)
    first = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:02:00+00:00")
    out_json = tmp_path / "published.json"
    out_md = tmp_path / "published.md"
    fresh.publish_fail_closed(out_json, out_md, first, "first\n")

    # Change content without changing generated_at: ambiguous writer state must not win.
    write_json(tmp_path / "free swarm/LIVE_METRICS.json", {
        "generated_at": "2026-08-25T02:02:01+00:00",
        "total_tokens": 999,
    })
    second = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:03:00+00:00")
    with pytest.raises(fresh.FreshnessError, match="AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT"):
        fresh.publish_fail_closed(out_json, out_md, second, "second\n")


def test_missing_source_or_timestamp_fails_closed(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    (tmp_path / "free swarm/FORGE_LIVE.json").unlink()
    with pytest.raises(fresh.FreshnessError, match="SOURCE_MISSING"):
        fresh.bind_freshness(base_result(), tmp_path)

    seed_repo(tmp_path)
    write_json(tmp_path / "free swarm/FORGE_LIVE.json", {"evaluated": 1, "accepted": 1})
    with pytest.raises(fresh.FreshnessError, match="SOURCE_GENERATED_AT_REQUIRED"):
        fresh.bind_freshness(base_result(), tmp_path)


def test_older_authority_epoch_fails_closed_even_if_live_timestamp_is_newer(tmp_path: Path) -> None:
    seed_repo(tmp_path, minute=1)
    existing = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:01:00+00:00")

    seed_repo(tmp_path, minute=2)
    write_json(tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "selected": {"schema_version": "8.76", "source": "SUPERVISOR_STEERING_8_76.json"},
    })
    candidate = fresh.bind_freshness(base_result(), tmp_path, published_at="2026-08-25T03:02:00+00:00")
    with pytest.raises(fresh.FreshnessError, match="OUT_OF_ORDER_AUTHORITY_EPOCH"):
        fresh.assert_not_older(existing, candidate)


def test_one_source_can_advance_without_exceeding_another_sources_max_time(tmp_path: Path) -> None:
    # Existing snapshot: Distillery is newest at 02:10; Swarm lags at 02:01.
    write_json(tmp_path / "free swarm/LIVE_METRICS.json", {
        "generated_at": "2026-08-25T02:01:00+00:00", "total_tokens": 100,
    })
    write_json(tmp_path / "free swarm/FORGE_LIVE.json", {
        "generated_at": "2026-08-25T02:09:00+00:00", "evaluated": 70, "accepted": 55,
    })
    write_json(tmp_path / "free swarm/DISTILLERY_LIVE.json", {
        "generated_at": "2026-08-25T02:10:00+00:00", "accepted_dataset_tokens": 0,
    })
    write_json(tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "selected": {"schema_version": "8.77", "source": "SUPERVISOR_STEERING_8_77.json"},
    })
    existing = fresh.bind_freshness(base_result(), tmp_path)

    # Swarm catches up to 02:08. The global max is still 02:10, but this is a valid advance.
    write_json(tmp_path / "free swarm/LIVE_METRICS.json", {
        "generated_at": "2026-08-25T02:08:00+00:00", "total_tokens": 110,
    })
    candidate = fresh.bind_freshness(base_result(), tmp_path)
    fresh.assert_not_older(existing, candidate)
    assert candidate["free_swarm_tokens"] == 110
