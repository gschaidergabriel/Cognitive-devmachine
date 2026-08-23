from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(RUNTIME))

from entry_fabric_v1 import EntryAdmissionError, ResourceBudget, admit_payload
from grid10_runtime_v1 import Grid10Scheduler


def packet(**overrides):
    kwargs = dict(
        payload={"prompt": "compare two hypotheses"},
        causal_id="causal-001",
        generation=7,
        source="human:gabriel",
        provenance={"channel": "test", "source_event": "evt-1"},
        modality="text",
        observed_at="2026-08-23T15:00:00Z",
        received_at="2026-08-23T15:00:01Z",
        permissions=("candidate", "read"),
        capability_scope=("mode:grid10",),
        resource_budget=ResourceBudget(max_cells=10, max_tokens=2048, max_wall_ms=10000),
    )
    kwargs.update(overrides)
    return admit_payload(**kwargs)


def test_grid10_is_ten_logical_cells_but_worker_budget_is_separate():
    d = Grid10Scheduler(current_generation=7, physical_worker_budget=2).route(packet())
    assert d.mode == "XENO_GRID10"
    assert len(d.selected_cells) == 10
    assert len(set(d.selected_cells)) == 10
    assert d.physical_worker_budget == 2


def test_stale_generation_fails_before_route():
    with pytest.raises(EntryAdmissionError, match="stale generation"):
        Grid10Scheduler(current_generation=8).route(packet(generation=7))


def test_same_event_transport_replay_preserves_event_and_route_identity():
    p1 = packet(received_at="2026-08-23T15:00:01Z")
    p2 = packet(received_at="2026-08-23T15:05:01Z")
    assert p1.event_sha256 == p2.event_sha256
    assert p1.ingress_id != p2.ingress_id
    s = Grid10Scheduler(current_generation=7)
    assert s.route(p1).decision_sha256 == s.route(p2).decision_sha256


def test_materially_different_event_cannot_alias_route_decision():
    p1 = packet(payload={"prompt": "A"}, provenance={"source_event": "evt-A"})
    p2 = packet(payload={"prompt": "B"}, provenance={"source_event": "evt-B"})
    s = Grid10Scheduler(current_generation=7)
    d1, d2 = s.route(p1), s.route(p2)
    assert d1.mode == d2.mode == "XENO_GRID10"
    assert d1.selected_cells == d2.selected_cells
    assert p1.event_sha256 != p2.event_sha256
    assert d1.decision_sha256 != d2.decision_sha256


def test_provenance_change_is_part_of_event_identity():
    p1 = packet(provenance={"sensor": "a", "receipt": "1"})
    p2 = packet(provenance={"sensor": "b", "receipt": "1"})
    assert p1.payload_sha256 == p2.payload_sha256
    assert p1.event_sha256 != p2.event_sha256


def test_effect_request_without_explicit_capability_fails_closed():
    with pytest.raises(EntryAdmissionError, match="explicit capability"):
        Grid10Scheduler(current_generation=7).route(
            packet(permissions=("effect_request", "read"), capability_scope=())
        )


def test_budget_can_bound_grid_below_ten_without_changing_physical_worker_claim():
    p = packet(resource_budget=ResourceBudget(max_cells=4, max_tokens=1024, max_wall_ms=5000))
    d = Grid10Scheduler(current_generation=7, physical_worker_budget=1).route(p)
    assert d.mode == "XENO_GRID10"
    assert len(d.selected_cells) == 4
    assert d.physical_worker_budget == 1


def test_unusual_provenance_collision_lesion_discriminates_weak_identity():
    """Exactly-one unusual experiment for this go macrocycle."""
    p1 = packet(payload={"value": 42}, provenance={"sensor": "left"})
    p2 = packet(payload={"value": 42}, provenance={"sensor": "right"})

    def weak_payload_only_digest(p):
        raw = json.dumps({"payload_sha256": p.payload_sha256}, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    assert weak_payload_only_digest(p1) == weak_payload_only_digest(p2)
    assert p1.event_sha256 != p2.event_sha256


def test_cli_is_a_real_typed_new_data_entrypoint():
    request = {
        "payload": {"prompt": "new data"},
        "causal_id": "causal-cli-1",
        "generation": 7,
        "source": "human:andreas",
        "provenance": {"channel": "stdin", "source_event": "cli-1"},
        "modality": "text",
        "observed_at": "2026-08-23T15:00:00Z",
        "received_at": "2026-08-23T15:00:01Z",
        "permissions": ["read", "candidate"],
        "capability_scope": ["mode:grid10"],
        "resource_budget": {"max_cells": 10, "max_tokens": 1000, "max_wall_ms": 5000},
    }
    proc = subprocess.run(
        [sys.executable, str(RUNTIME / "xeno_cli_v1.py"), "--generation", "7", "--physical-workers", "2"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["ok"] is True
    assert out["result"]["logical_cell_count"] == 10
    assert out["result"]["physical_worker_budget"] == 2
    assert out["result"]["effect_authority"] == "NONE_CANDIDATE_ONLY"


def test_cli_stale_generation_exits_fail_closed():
    request = {
        "payload": {"prompt": "stale"},
        "causal_id": "causal-cli-2",
        "generation": 6,
        "source": "tool:test",
        "provenance": {"receipt": "r-1"},
        "modality": "tool_result",
        "observed_at": "2026-08-23T15:00:00Z",
        "received_at": "2026-08-23T15:00:01Z",
        "permissions": ["read", "candidate"],
        "capability_scope": ["mode:grid10"],
    }
    proc = subprocess.run(
        [sys.executable, str(RUNTIME / "xeno_cli_v1.py"), "--generation", "7"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "stale generation" in proc.stderr
