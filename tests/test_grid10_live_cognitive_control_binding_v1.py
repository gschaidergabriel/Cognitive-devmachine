from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from frankenstein2_cognitive_control_plane_v1 import ControlMode
from grid10_live_cognitive_control_binding_v1 import (
    LiveControlledCognitiveLoop,
    grid_cell_map,
)


def _patch(loop: LiveControlledCognitiveLoop, patch_id: str, changes: dict[str, object]) -> None:
    base = loop.controls.snapshot()
    patch = loop.controls.build_patch(
        patch_id=patch_id,
        writer="test",
        writer_kind="EXPERIMENT",
        reason="deterministic binding regression",
        changes=changes,
        base=base,
    )
    receipt = loop.controls.apply_patch(patch)
    assert receipt.accepted is True


def test_idle_cycle_consumes_latched_live_pulse_cadence(tmp_path: Path):
    db = tmp_path / "unified.sqlite"
    loop = LiveControlledCognitiveLoop(db, tmp_path / "frames.jsonl")
    _patch(
        loop,
        "cadence-1",
        {
            "pulse.active_interval_seconds": 2.0,
            "pulse.hold_interval_seconds": 7.0,
            "pulse.idle_interval_seconds": 11.0,
        },
    )

    result = loop.cycle_once(cycle_id="idle-controlled", now_ts=100.0)
    assert result.control_epoch == 1
    assert result.scheduler["status"] == "HOLD_NO_ACTIVE_GOAL"
    assert result.scheduler["next_tick_not_before"] == 111.0
    assert result.external_effect_executed is False
    assert result.provider_calls == 0


def test_snapshot_is_immutable_for_already_latched_cycle_view(tmp_path: Path):
    loop = LiveControlledCognitiveLoop(tmp_path / "unified.sqlite", tmp_path / "frames.jsonl")
    old_view = loop.latch()
    old_digest = old_view.snapshot_digest
    _patch(loop, "gain-after-latch", {"grid.goal.gain": 2.5})
    new_view = loop.latch()

    assert old_view.snapshot_digest == old_digest
    assert old_view.control_epoch == 0
    assert grid_cell_map(old_view)["goal"].gain == 1.0
    assert new_view.control_epoch == 1
    assert new_view.snapshot_digest != old_digest
    assert grid_cell_map(new_view)["goal"].gain == 2.5


def test_grid_modes_are_mechanically_distinct(tmp_path: Path):
    loop = LiveControlledCognitiveLoop(tmp_path / "unified.sqlite", tmp_path / "frames.jsonl")
    _patch(
        loop,
        "modes-1",
        {
            "grid.orientation.mode": ControlMode.COMPUTE_OFF.value,
            "grid.goal.mode": ControlMode.OUTPUT_OFF.value,
            "grid.epistemic.mode": ControlMode.MEMORY_OFF.value,
            "grid.hypothesis.gain": 0.0,
        },
    )
    cells = grid_cell_map(loop.latch())

    compute_off = cells["orientation"]
    assert compute_off.compute_allowed is False
    assert compute_off.downstream_output_allowed is False
    assert compute_off.durable_memory_write_allowed is False
    assert compute_off.result_state == "NOT_COMPUTED"

    output_off = cells["goal"]
    assert output_off.compute_allowed is True
    assert output_off.downstream_output_allowed is False
    assert output_off.durable_memory_write_allowed is True
    assert output_off.result_state == "LOCAL_ONLY_OUTPUT_WITHHELD"

    memory_off = cells["epistemic"]
    assert memory_off.compute_allowed is True
    assert memory_off.downstream_output_allowed is True
    assert memory_off.durable_memory_write_allowed is False
    assert memory_off.result_state == "EPHEMERAL_NO_DURABLE_MEMORY"

    zero_gain = cells["hypothesis"]
    assert zero_gain.mode == ControlMode.ON.value
    assert zero_gain.compute_allowed is True
    assert zero_gain.gain == 0.0
    assert zero_gain.result_state == "ACTIVE"


def test_control_plane_and_scheduler_share_one_sqlite_path(tmp_path: Path):
    db = tmp_path / "unified.sqlite"
    loop = LiveControlledCognitiveLoop(db, tmp_path / "frames.jsonl")
    view = loop.latch()
    scheduler = loop._scheduler_for(view)

    assert loop.controls.path.resolve() == db.resolve()
    assert Path(scheduler.fabric.path).resolve() == db.resolve()
    assert Path(scheduler.heartbeat_store.path).resolve() == db.resolve()
    assert Path(scheduler.agency.path).resolve() == db.resolve()
