import unittest

from entry_fabric_v1 import admit_ingress
from grid10_scheduler_v1 import Grid10SchedulingError, schedule_grid10


PAYLOAD_A = "a" * 64
PAYLOAD_B = "b" * 64


def ingress(payload_sha256=PAYLOAD_A, *, max_cells=10):
    raw = {
        "schema": "XENO_INGRESS_PACKET/v1",
        "causal_id": "cause-grid10",
        "entity_generation": 9,
        "source": "intrinsic_system_event",
        "provenance": {"kind": "test", "ref": "same-threshold-shape"},
        "modality": "json",
        "observed_at_ns": 200,
        "received_at_ns": 210,
        "permissions": ["state.read"],
        "capability_scope": [],
        "resource_budget": {
            "max_wall_ms": 1000,
            "max_model_calls": 4,
            "max_context_tokens": 4096,
            "max_logical_cells": max_cells,
        },
        "payload_ref": "unifieddb:event:grid10",
        "payload_sha256": payload_sha256,
    }
    return admit_ingress(raw, current_generation=9)


class Grid10SchedulerTests(unittest.TestCase):
    def test_grid_has_exactly_ten_logical_cells(self):
        plan = schedule_grid10(ingress(), ["world", "critic", "hypothesis"], current_generation=9)
        self.assertEqual(len(plan.cells), 10)
        self.assertEqual(plan.active_cells, 3)
        self.assertEqual(sum(cell.active for cell in plan.cells), 3)
        self.assertTrue(all(cell.function == "IDLE" for cell in plan.cells[3:]))

    def test_same_ingress_and_functions_replay_deterministically(self):
        packet = ingress()
        a = schedule_grid10(packet, ["world", "critic"], current_generation=9)
        b = schedule_grid10(packet, ["world", "critic"], current_generation=9)
        self.assertEqual(a, b)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(Grid10SchedulingError, "STALE_ENTITY_GENERATION"):
            schedule_grid10(ingress(), ["world"], current_generation=10)

    def test_logical_cell_budget_is_enforced(self):
        with self.assertRaisesRegex(Grid10SchedulingError, "INGRESS_LOGICAL_CELL_BUDGET_EXCEEDED"):
            schedule_grid10(ingress(max_cells=1), ["world", "critic"], current_generation=9)

    def test_grid10_ceiling_is_enforced(self):
        with self.assertRaisesRegex(Grid10SchedulingError, "GRID10_CELL_LIMIT_EXCEEDED"):
            schedule_grid10(ingress(), [f"f{i}" for i in range(11)], current_generation=9)

    def test_event_alias_poison_same_route_shape_different_event_must_not_alias(self):
        # Unusual discriminator for this GO: preserve identical scheduling shape while
        # changing only immutable event payload identity. The plans must not alias.
        a = schedule_grid10(ingress(PAYLOAD_A), ["world", "critic"], current_generation=9)
        b = schedule_grid10(ingress(PAYLOAD_B), ["world", "critic"], current_generation=9)
        self.assertNotEqual(a.ingress_id, b.ingress_id)
        self.assertNotEqual(a.plan_id, b.plan_id)
        self.assertNotEqual(a.cells[0].task_id, b.cells[0].task_id)


if __name__ == "__main__":
    unittest.main()
