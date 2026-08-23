import copy
import unittest

from entry_fabric_v1 import TrustedCapabilitySnapshot, admit_ingress
from grid10_scheduler_v1 import Grid10SchedulingError, schedule_grid10


PAYLOAD_A = "a" * 64
PAYLOAD_B = "b" * 64
AUTH = "1" * 64


def ingress(payload_sha256=PAYLOAD_A, *, max_cells=10, received_at=210, payload_ref="unifieddb:event:grid10"):
    raw = {
        "schema": "XENO_INGRESS_PACKET/v1",
        "causal_id": "cause-grid10",
        "entity_generation": 9,
        "source": "intrinsic_system_event",
        "provenance": {"kind": "test", "ref": "same-threshold-shape"},
        "modality": "json",
        "observed_at_ns": 200,
        "received_at_ns": received_at,
        "permissions": ["state.read"],
        "capability_scope": [],
        "resource_budget": {
            "max_wall_ms": 1000,
            "max_model_calls": 4,
            "max_context_tokens": 4096,
            "max_logical_cells": max_cells,
        },
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
    }
    return admit_ingress(
        raw,
        current_generation=9,
        trusted_capability_snapshot=TrustedCapabilitySnapshot(
            permissions=("state.read",),
            capability_scope=(),
            authority_binding_sha256=AUTH,
        ),
    )


class Grid10SchedulerTests(unittest.TestCase):
    def test_grid_has_exactly_ten_logical_cells(self):
        plan = schedule_grid10(ingress(), ["world", "critic", "hypothesis"], current_generation=9)
        self.assertEqual(len(plan.cells), 10)
        self.assertEqual(plan.active_cells, 3)
        self.assertEqual(sum(cell.active for cell in plan.cells), 3)
        self.assertTrue(all(cell.function == "IDLE" for cell in plan.cells[3:]))
        self.assertIsNone(plan.physical_decode_concurrency_claimed)

    def test_same_admission_and_functions_replay_deterministically(self):
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

    def test_same_event_different_transport_preserves_semantic_plan_but_not_execution_plan(self):
        a_packet = ingress()
        b_packet = ingress(received_at=999, payload_ref="cache-copy:event:grid10")
        self.assertEqual(a_packet.event_sha256, b_packet.event_sha256)
        self.assertNotEqual(a_packet.admission_sha256, b_packet.admission_sha256)
        a = schedule_grid10(a_packet, ["world", "critic"], current_generation=9)
        b = schedule_grid10(b_packet, ["world", "critic"], current_generation=9)
        self.assertEqual(a.semantic_plan_sha256, b.semantic_plan_sha256)
        self.assertNotEqual(a.plan_id, b.plan_id)
        self.assertNotEqual(a.cells[0].task_id, b.cells[0].task_id)

    def test_existing_event_alias_poison_regression_different_event_does_not_alias(self):
        # Regression of the already-consumed unusual discriminator; this is not a new experiment.
        a = schedule_grid10(ingress(PAYLOAD_A), ["world", "critic"], current_generation=9)
        b = schedule_grid10(ingress(PAYLOAD_B), ["world", "critic"], current_generation=9)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.semantic_plan_sha256, b.semantic_plan_sha256)
        self.assertNotEqual(a.plan_id, b.plan_id)
        self.assertNotEqual(a.cells[0].task_id, b.cells[0].task_id)


if __name__ == "__main__":
    unittest.main()
