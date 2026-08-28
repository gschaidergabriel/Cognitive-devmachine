#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from frankenstein2_cognitive_control_plane_v1 import ControlMode
from grid10_cognitive_controlled_runtime_v1 import build_controlled_grid_runtime_v1
from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes


class ControlledGridRuntimeV1Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"
        _, _, self.agency, self.control, self.runtime, _ = build_controlled_grid_runtime_v1(self.db)

    def tearDown(self):
        self.td.cleanup()

    def patch(self, patch_id: str, **changes):
        base = self.control.snapshot()
        patch = self.control.build_patch(
            patch_id=patch_id,
            writer="test",
            writer_kind="HUMAN",
            reason="deterministic Triggerword-4 integration test",
            changes=changes,
            base=base,
        )
        receipt = self.control.apply_patch(patch)
        self.assertTrue(receipt.accepted, receipt)
        return receipt

    def test_latched_snapshot_drives_cadence_modes_gain_gwt_and_memory_feed(self):
        self.patch(
            "controls-1",
            **{
                "pulse.active_interval_seconds": 2.5,
                "pulse.hold_interval_seconds": 7.0,
                "grid.orientation.mode": ControlMode.COMPUTE_OFF.value,
                "grid.goal.mode": ControlMode.OUTPUT_OFF.value,
                "grid.epistemic.mode": ControlMode.MEMORY_OFF.value,
                "grid.hypothesis.gain": 0.2,
                "grid.workspace_ignition_threshold": 0.5,
            },
        )
        calls = []

        def runner(cell, gain, basis):
            calls.append((cell, gain, basis["control_snapshot_digest"]))
            return {"cell": cell, "gain": gain}

        result = self.runtime.tick_once(
            tick_id="controlled-1",
            now_ts=10.0,
            trusted_axes=_trusted_normal_axes(),
            cell_runner=runner,
        )
        by_cell = {row.cell: row for row in result.cells}
        gwt_cells = {row["cell"] for row in result.gwt_feed}
        memory_cells = {row["cell"] for row in result.memory_feed}
        called_cells = {row[0] for row in calls}

        self.assertEqual(result.assurance_mode, "NORMAL")
        self.assertEqual(result.next_tick_not_before, 12.5)
        self.assertEqual(result.active_interval_seconds, 2.5)
        self.assertEqual(result.hold_interval_seconds, 7.0)

        self.assertNotIn("orientation", called_cells)
        self.assertFalse(by_cell["orientation"].computed)
        self.assertFalse(by_cell["orientation"].emitted_to_gwt)
        self.assertFalse(by_cell["orientation"].eligible_for_memory_feed)

        self.assertIn("goal", called_cells)
        self.assertTrue(by_cell["goal"].computed)
        self.assertNotIn("goal", gwt_cells)
        self.assertIn("goal", memory_cells)

        self.assertIn("epistemic", called_cells)
        self.assertIn("epistemic", gwt_cells)
        self.assertNotIn("epistemic", memory_cells)

        self.assertIn("hypothesis", called_cells)
        self.assertFalse(by_cell["hypothesis"].emitted_to_gwt)
        self.assertNotIn("hypothesis", gwt_cells)
        self.assertIn("hypothesis", memory_cells)

        self.assertTrue(all(digest == result.control_snapshot_digest for _, _, digest in calls))
        self.assertFalse(result.control_changed_during_cycle)

        con = sqlite3.connect(str(self.db))
        try:
            row = con.execute(
                "SELECT control_snapshot_digest,control_changed_during_cycle,receipt_digest FROM grid10_controlled_cycle_receipts WHERE tick_id=?",
                (result.tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], result.control_snapshot_digest)
        self.assertEqual(row[1], 0)
        self.assertEqual(row[2], result.receipt_digest)

    def test_control_patch_mid_cycle_does_not_change_latched_current_cycle(self):
        first_calls = []
        patched = False

        def first_runner(cell, gain, basis):
            nonlocal patched
            first_calls.append(cell)
            if cell == "orientation" and not patched:
                self.patch("mid-cycle-disable-goal", **{"grid.goal.mode": ControlMode.COMPUTE_OFF.value})
                patched = True
            return {"cell": cell, "basis": basis["control_snapshot_digest"]}

        first = self.runtime.tick_once(
            tick_id="latched-first",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
            cell_runner=first_runner,
        )
        self.assertTrue(first.control_changed_during_cycle)
        self.assertIn("goal", first_calls)
        self.assertTrue({r.cell: r for r in first.cells}["goal"].computed)

        second_calls = []

        def second_runner(cell, gain, basis):
            second_calls.append(cell)
            return {"cell": cell}

        second = self.runtime.tick_once(
            tick_id="latched-second",
            now_ts=first.next_tick_not_before,
            trusted_axes=_trusted_normal_axes(),
            cell_runner=second_runner,
        )
        self.assertNotEqual(second.control_snapshot_digest, first.control_snapshot_digest)
        self.assertNotIn("goal", second_calls)
        self.assertFalse({r.cell: r for r in second.cells}["goal"].computed)

    def test_hold_cycle_uses_latched_hold_cadence(self):
        self.patch("hold-cadence", **{"pulse.hold_interval_seconds": 11.0})
        result = self.runtime.tick_once(
            tick_id="controlled-hold",
            now_ts=200.0,
            cell_runner=lambda cell, gain, basis: {"cell": cell},
        )
        self.assertEqual(result.assurance_mode, "HOLD")
        self.assertEqual(result.next_action, "HOLD")
        self.assertEqual(result.next_tick_not_before, 211.0)

    def test_missing_runner_never_mints_gwt_or_memory_candidates(self):
        result = self.runtime.tick_once(
            tick_id="no-runner",
            now_ts=300.0,
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertEqual(result.gwt_feed, ())
        self.assertEqual(result.memory_feed, ())
        self.assertTrue(all(not row.computed for row in result.cells))
        self.assertTrue(all(row.error == "NO_CELL_RUNNER" for row in result.cells))


if __name__ == "__main__":
    unittest.main()
