import unittest

from xeno_entry_fabric_v1 import EntryFabricError, admit_entry
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
ADMITTED_BUDGET = {
    "max_model_calls": 4,
    "max_tokens": 4096,
    "max_wall_ms": 10_000,
}


def packet(*, max_model_calls=2, max_tokens=2048, max_wall_ms=5000, admitted_budget=ADMITTED_BUDGET):
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
            "max_wall_ms": max_wall_ms,
        },
        "payload_ref": "unifieddb:payload:test:grid",
        "payload_sha256": "3" * 64,
    }
    return admit_entry(
        entry,
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=ADMITTED_CAPABILITIES,
        admitted_budget=admitted_budget,
    )


def capacity(*, logical=10, physical=1, receipt="4" * 64, profile="runtime:kvm4:test"):
    return RuntimeCapacity(
        profile_id=profile,
        capacity_receipt_sha256=receipt,
        max_logical_cells=logical,
        physical_decoder_limit=physical,
    )


def entry_bindings(p):
    return {p.admission_sha256: p.event_sha256}


def capacity_receipts(c):
    return {
        c.capacity_receipt_sha256: {
            "profile_id": c.profile_id,
            "max_logical_cells": c.max_logical_cells,
            "physical_decoder_limit": c.physical_decoder_limit,
        }
    }


def compile_admitted(p, *, mode, cap):
    return compile_plan(
        p,
        mode=mode,
        capacity=cap,
        admitted_entry_bindings=entry_bindings(p),
        admitted_capacity_receipts=capacity_receipts(cap),
    )


class Grid10SchedulerTests(unittest.TestCase):
    def test_grid10_separates_logical_model_and_physical_counts(self):
        p, cap = packet(), capacity(physical=1)
        plan = compile_admitted(p, mode=HCUMode.GRID10, cap=cap)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(plan.model_call_count, 2)
        self.assertEqual(plan.physical_decoder_limit, 1)
        self.assertEqual(len(plan.cells), 10)
        model_cells = [cell for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
        self.assertEqual(len(model_cells), 2)
        self.assertEqual({cell.physical_decoder_lane for cell in model_cells}, {0})

    def test_grid10_can_time_slice_two_model_cells_over_two_decoders(self):
        p, cap = packet(), capacity(physical=2)
        plan = compile_admitted(p, mode=HCUMode.GRID10, cap=cap)
        lanes = [cell.physical_decoder_lane for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
        self.assertEqual(lanes, [0, 1])

    def test_plan_is_deterministic_and_bound_to_capacity_receipt(self):
        p = packet()
        cap_a = capacity(receipt="4" * 64)
        cap_b = capacity(receipt="5" * 64)
        a = compile_admitted(p, mode=HCUMode.GRID10, cap=cap_a)
        b = compile_admitted(p, mode=HCUMode.GRID10, cap=cap_a)
        c = compile_admitted(p, mode=HCUMode.GRID10, cap=cap_b)
        self.assertEqual(a.plan_sha256, b.plan_sha256)
        self.assertNotEqual(a.plan_sha256, c.plan_sha256)

    def test_entry_compute_budget_must_be_externally_admitted_before_grid(self):
        with self.assertRaisesRegex(EntryFabricError, "BUDGET_NOT_ADMITTED:max_model_calls"):
            packet(max_model_calls=ADMITTED_BUDGET["max_model_calls"] + 1)

    def test_entry_may_narrow_external_compute_budget_before_grid(self):
        p = packet(max_model_calls=2, max_tokens=1024, max_wall_ms=2000)
        self.assertEqual(dict(p.budget), {
            "max_model_calls": 2,
            "max_tokens": 1024,
            "max_wall_ms": 2000,
        })
        plan = compile_admitted(p, mode=HCUMode.GRID10, cap=capacity())
        self.assertEqual(plan.max_wall_ms, 2000)

    def test_entry_admission_binding_is_required_before_grid(self):
        p, cap = packet(), capacity()
        with self.assertRaisesRegex(GridScheduleError, "ENTRY_ADMISSION_NOT_REGISTERED"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=cap,
                admitted_entry_bindings={},
                admitted_capacity_receipts=capacity_receipts(cap),
            )

    def test_capacity_receipt_must_be_separately_admitted(self):
        p, cap = packet(), capacity()
        with self.assertRaisesRegex(GridScheduleError, "CAPACITY_RECEIPT_NOT_ADMITTED"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=cap,
                admitted_entry_bindings=entry_bindings(p),
                admitted_capacity_receipts={},
            )

    def test_same_receipt_cannot_self_grant_more_physical_decoders(self):
        p = packet()
        trusted = capacity(physical=1)
        inflated = capacity(physical=8, receipt=trusted.capacity_receipt_sha256)
        with self.assertRaisesRegex(GridScheduleError, "CAPACITY_PHYSICAL_DECODER_LIMIT_MISMATCH"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=inflated,
                admitted_entry_bindings=entry_bindings(p),
                admitted_capacity_receipts=capacity_receipts(trusted),
            )

    def test_same_receipt_cannot_self_grant_more_logical_cells(self):
        p = packet()
        trusted = capacity(logical=10)
        inflated = capacity(logical=100, receipt=trusted.capacity_receipt_sha256)
        with self.assertRaisesRegex(GridScheduleError, "CAPACITY_MAX_LOGICAL_CELLS_MISMATCH"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=inflated,
                admitted_entry_bindings=entry_bindings(p),
                admitted_capacity_receipts=capacity_receipts(trusted),
            )

    def test_same_receipt_cannot_switch_runtime_profile(self):
        p = packet()
        trusted = capacity(profile="runtime:kvm4:test")
        substituted = capacity(profile="runtime:other", receipt=trusted.capacity_receipt_sha256)
        with self.assertRaisesRegex(GridScheduleError, "CAPACITY_PROFILE_ID_MISMATCH"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=substituted,
                admitted_entry_bindings=entry_bindings(p),
                admitted_capacity_receipts=capacity_receipts(trusted),
            )

    def test_logical_capacity_fails_closed(self):
        p, cap = packet(), capacity(logical=9)
        with self.assertRaisesRegex(GridScheduleError, "LOGICAL_CELL_CAPACITY_EXCEEDED"):
            compile_admitted(p, mode=HCUMode.GRID10, cap=cap)

    def test_cogsim_respects_entry_model_call_budget(self):
        p, cap = packet(max_model_calls=2), capacity()
        with self.assertRaisesRegex(GridScheduleError, "MODEL_CALL_BUDGET_EXCEEDED"):
            compile_admitted(p, mode=HCUMode.COGSIM10, cap=cap)
        p, cap = packet(max_model_calls=4), capacity(physical=2)
        plan = compile_admitted(p, mode=HCUMode.COGSIM10, cap=cap)
        self.assertEqual(plan.model_call_count, 4)
        self.assertEqual(plan.physical_decoder_limit, 2)

    def test_model_token_budget_fails_closed(self):
        p, cap = packet(max_model_calls=4, max_tokens=3), capacity()
        with self.assertRaisesRegex(GridScheduleError, "MODEL_TOKEN_BUDGET_TOO_SMALL"):
            compile_admitted(p, mode=HCUMode.COGSIM10, cap=cap)

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
        p, cap = packet(), capacity()
        with self.assertRaisesRegex(GridScheduleError, "SEPARATE_ADMITTED_SCALE_PROFILE"):
            compile_admitted(p, mode=HCUMode.SCALEOUT, cap=cap)

    def test_capacity_identity_is_typed(self):
        p, cap = packet(), capacity(receipt="not-a-digest")
        with self.assertRaisesRegex(GridScheduleError, "LOWERCASE_SHA256_REQUIRED"):
            compile_plan(
                p,
                mode=HCUMode.GRID10,
                capacity=cap,
                admitted_entry_bindings=entry_bindings(p),
                admitted_capacity_receipts={},
            )

    def test_direct_is_script_only_and_needs_no_model_call(self):
        p, cap = packet(max_model_calls=0, max_tokens=0), capacity(logical=1)
        plan = compile_admitted(p, mode=HCUMode.DIRECT, cap=cap)
        self.assertEqual(plan.logical_cell_count, 1)
        self.assertEqual(plan.model_call_count, 0)
        self.assertEqual(plan.physical_decoder_limit, 0)
        self.assertIsNone(plan.cells[0].physical_decoder_lane)


if __name__ == "__main__":
    unittest.main()
