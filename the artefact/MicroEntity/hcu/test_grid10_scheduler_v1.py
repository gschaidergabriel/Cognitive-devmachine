import unittest

from xeno_entry_fabric_v1 import admit_entry
from grid10_scheduler_v1 import (
    ExecutionClass,
    GridScheduleError,
    HCUMode,
    RoutingSignals,
    RuntimeCapacity,
    choose_mode,
    compile_plan,
)


CAPABILITY_BINDING_SHA256 = "2" * 64
ADMITTED_CAPABILITIES = ("hcu.route",)


def packet(*, max_model_calls=2, max_tokens=2048):
    entry = {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:grid",
        "causal_id": "causal:test:grid",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:40:00+07:00",
        "received_time": "2026-08-23T23:40:01+07:00",
        "provenance_ref": "unifieddb:source:test:grid",
        "provenance_sha256": "1" * 64,
        "capabilities": ["hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:test:grid",
        "budget": {
            "max_model_calls": max_model_calls,
            "max_tokens": max_tokens,
            "max_wall_ms": 5000,
        },
        "payload_ref": "unifieddb:payload:test:grid",
        "payload_sha256": "3" * 64,
    }
    return admit_entry(
        entry,
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=ADMITTED_CAPABILITIES,
        admitted_budget={
            "max_model_calls": max_model_calls,
            "max_tokens": max_tokens,
            "max_wall_ms": 5000,
        },
    )


def capacity(*, logical=10, physical=1, receipt="4" * 64):
    return RuntimeCapacity(
        profile_id="runtime:kvm4:test",
        capacity_receipt_sha256=receipt,
        max_logical_cells=logical,
        physical_decoder_limit=physical,
    )


class Grid10SchedulerTests(unittest.TestCase):
    def test_grid10_separates_logical_model_and_physical_counts(self):
        plan = compile_plan(packet(), mode=HCUMode.GRID10, capacity=capacity(physical=1))
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(plan.model_call_count, 2)
        self.assertEqual(plan.physical_decoder_limit, 1)
        self.assertEqual(len(plan.cells), 10)
        model_cells = [cell for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
        self.assertEqual(len(model_cells), 2)
        self.assertEqual({cell.physical_decoder_lane for cell in model_cells}, {0})

    def test_grid10_can_time_slice_two_model_cells_over_two_decoders(self):
        plan = compile_plan(packet(), mode=HCUMode.GRID10, capacity=capacity(physical=2))
        lanes = [cell.physical_decoder_lane for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
        self.assertEqual(lanes, [0, 1])

    def test_plan_is_deterministic_and_bound_to_capacity_receipt(self):
        p = packet()
        a = compile_plan(p, mode=HCUMode.GRID10, capacity=capacity(receipt="4" * 64))
        b = compile_plan(p, mode=HCUMode.GRID10, capacity=capacity(receipt="4" * 64))
        c = compile_plan(p, mode=HCUMode.GRID10, capacity=capacity(receipt="5" * 64))
        self.assertEqual(a.plan_sha256, b.plan_sha256)
        self.assertNotEqual(a.plan_sha256, c.plan_sha256)

    def test_logical_capacity_fails_closed(self):
        with self.assertRaisesRegex(GridScheduleError, "LOGICAL_CELL_CAPACITY_EXCEEDED"):
            compile_plan(packet(), mode=HCUMode.GRID10, capacity=capacity(logical=9))

    def test_cogsim_respects_entry_model_call_budget(self):
        with self.assertRaisesRegex(GridScheduleError, "MODEL_CALL_BUDGET_EXCEEDED"):
            compile_plan(packet(max_model_calls=2), mode=HCUMode.COGSIM10, capacity=capacity())
        plan = compile_plan(packet(max_model_calls=4), mode=HCUMode.COGSIM10, capacity=capacity(physical=2))
        self.assertEqual(plan.model_call_count, 4)
        self.assertEqual(plan.physical_decoder_limit, 2)

    def test_model_token_budget_fails_closed(self):
        with self.assertRaisesRegex(GridScheduleError, "MODEL_TOKEN_BUDGET_TOO_SMALL"):
            compile_plan(packet(max_model_calls=4, max_tokens=3), mode=HCUMode.COGSIM10, capacity=capacity())

    def test_nested_mode_requires_cheaper_modes_exhausted(self):
        base = RoutingSignals(
            ambiguity=1.0,
            reasoning_horizon=0.9,
            environment_dynamics=0.9,
            value_of_information=0.9,
            cheaper_modes_exhausted=False,
        )
        self.assertEqual(choose_mode(base), HCUMode.WM_TEST)
        admitted = RoutingSignals(
            ambiguity=1.0,
            reasoning_horizon=0.9,
            environment_dynamics=0.9,
            value_of_information=0.9,
            cheaper_modes_exhausted=True,
        )
        self.assertEqual(choose_mode(admitted), HCUMode.NESTED_SIM)

    def test_scaleout_requires_separate_admitted_profile(self):
        with self.assertRaisesRegex(GridScheduleError, "SEPARATE_ADMITTED_SCALE_PROFILE"):
            compile_plan(packet(), mode=HCUMode.SCALEOUT, capacity=capacity())

    def test_capacity_identity_is_typed(self):
        with self.assertRaisesRegex(GridScheduleError, "LOWERCASE_SHA256_REQUIRED"):
            compile_plan(packet(), mode=HCUMode.GRID10, capacity=capacity(receipt="not-a-digest"))

    def test_direct_is_script_only_and_needs_no_model_call(self):
        plan = compile_plan(packet(max_model_calls=0, max_tokens=0), mode=HCUMode.DIRECT, capacity=capacity(logical=1))
        self.assertEqual(plan.logical_cell_count, 1)
        self.assertEqual(plan.model_call_count, 0)
        self.assertEqual(plan.physical_decoder_limit, 0)
        self.assertIsNone(plan.cells[0].physical_decoder_lane)


if __name__ == "__main__":
    unittest.main()
