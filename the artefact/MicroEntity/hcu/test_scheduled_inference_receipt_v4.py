import unittest
from dataclasses import replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA
from grid10_scheduler_v1 import ExecutionClass, HCUMode, RuntimeCapacity, compile_plan
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, route_event
from scheduled_inference_receipt_v4 import (
    GRID_PLAN_BINDING_SCHEMA,
    SCHEMA,
    ScheduledInferenceReceiptError,
    make_scheduled_inference_receipt,
)
from test_inference_receipt_v1 import (
    CAPABILITY_BINDING_SHA256,
    ENGINE_SHA256,
    OUTPUT_SHA256,
    digest,
    verified_engine_admission,
    verified_engine_load,
    verified_load_receipt,
)
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event

GENERATION = 7
CAPACITY_RECEIPT_SHA256 = digest("scheduled-capacity")


def packet():
    budget = {"max_model_calls": 3, "max_tokens": 2048, "max_wall_ms": 5000}
    raw = {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:scheduled:v4",
        "causal_id": "causal:test:scheduled:v4",
        "entity_generation": GENERATION,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:57:00+07:00",
        "received_time": "2026-08-23T23:57:01+07:00",
        "provenance_ref": "unifieddb:source:test:scheduled:v4",
        "provenance_sha256": digest("scheduled-provenance"),
        "capabilities": ["hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:test:scheduled:v4",
        "budget": budget,
        "payload_ref": "unifieddb:payload:test:scheduled:v4",
        "payload_sha256": digest("scheduled-payload"),
    }
    return admit_entry(
        raw,
        current_generation=GENERATION,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("hcu.route",),
        admitted_budget=budget,
    )


def entry_bindings(p):
    return {
        p.admission_sha256: {
            "schema": ENTRY_BINDING_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "event_sha256": p.event_sha256,
        }
    }


def fixture(*, physical_decoders=2):
    p = packet()
    verified = verified_engine_admission()
    event = to_hcu_reactive_event(p, contradiction=0.8, uncertainty=0.7)
    event["requested_internal_provider"] = "hcu"
    bindings = entry_bindings(p)
    artifacts = {"hcu_local_08b": ENGINE_SHA256}
    decision = route_event(
        event,
        current_generation=GENERATION,
        engine_admission=verified.admission,
        admitted_engine_artifacts=artifacts,
        admitted_entry_bindings=bindings,
    )
    capacity = RuntimeCapacity(
        "runtime:test:scheduled:v4",
        CAPACITY_RECEIPT_SHA256,
        10,
        physical_decoders,
    )
    plan = compile_plan(
        p,
        decision=decision,
        mode=HCUMode.GRID10,
        capacity=capacity,
        current_generation=GENERATION,
        admitted_entry_bindings=bindings,
        admitted_capacity_receipts={
            CAPACITY_RECEIPT_SHA256: {
                "profile_id": capacity.profile_id,
                "max_logical_cells": capacity.max_logical_cells,
                "physical_decoder_limit": capacity.physical_decoder_limit,
            }
        },
    )
    load = verified_engine_load(verified)
    inner_kwargs = {
        "current_generation": GENERATION,
        "admitted_route_generations": {decision.decision_sha256: GENERATION},
        "entry_admission_sha256": p.admission_sha256,
        "admitted_entry_bindings": bindings,
        "admitted_engine_artifacts": artifacts,
        "verified_engine_admission": verified,
        "admitted_engine_admission_receipts": {verified.receipt_sha256: verified.receipt()},
        "verified_engine_load": load,
        "admitted_verified_engine_loads": {
            load.consumption_receipt_sha256: verified_load_receipt(load)
        },
        "model_call_id": "model-call:scheduled:v4:1",
        "output_ref": "unifieddb:candidate-output:scheduled:v4:1",
        "output_sha256": OUTPUT_SHA256,
        "output_size": 128,
    }
    return p, decision, plan, inner_kwargs


def plan_binding(plan):
    return {
        "schema": GRID_PLAN_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "grid_plan_schema": plan.schema,
        "grid_plan_sha256": plan.plan_sha256,
        "route_decision_sha256": plan.route_decision_sha256,
        "entity_generation": plan.entity_generation,
        "capacity_receipt_sha256": plan.capacity_receipt_sha256,
    }


def call(decision, plan, kwargs, *, bindings=None, cell_id=None, lane=None):
    model_cell = next(c for c in plan.cells if c.execution_class is ExecutionClass.MODEL)
    model_lane = model_cell.function.split("MODEL:", 1)[1]
    return make_scheduled_inference_receipt(
        decision,
        grid_plan=plan,
        admitted_grid_plan_bindings=(
            {plan.plan_sha256: plan_binding(plan)} if bindings is None else bindings
        ),
        grid_cell_id=model_cell.cell_id if cell_id is None else cell_id,
        model_lane=model_lane if lane is None else lane,
        **kwargs,
    )


class ScheduledInferenceReceiptTests(unittest.TestCase):
    def test_current_grid_plan_and_inference_v3_are_bound_into_v4(self):
        _p, decision, plan, kwargs = fixture()
        receipt = call(decision, plan, kwargs)
        self.assertEqual(receipt.schema, SCHEMA)
        self.assertEqual(receipt.inner_receipt_schema, "HCU_INFERENCE_RECEIPT/v3")
        self.assertEqual(receipt.canonicalization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(receipt.entry_binding_schema, ENTRY_BINDING_SCHEMA)
        self.assertEqual(receipt.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(receipt.capacity_receipt_sha256, plan.capacity_receipt_sha256)
        self.assertGreater(receipt.model_token_budget, 0)
        self.assertLess(receipt.physical_decoder_lane, plan.physical_decoder_limit)
        self.assertEqual(len(receipt.receipt_sha256), 64)

    def test_same_inputs_are_deterministic(self):
        _p, decision, plan, kwargs = fixture()
        self.assertEqual(call(decision, plan, kwargs), call(decision, plan, kwargs))

    def test_grid_plan_must_be_externally_admitted(self):
        _p, decision, plan, kwargs = fixture()
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_NOT_ADMITTED"):
            call(decision, plan, kwargs, bindings={})

    def test_plan_digest_tamper_fails_closed(self):
        _p, decision, plan, kwargs = fixture()
        poisoned = replace(plan, plan_sha256=digest("tampered-plan"))
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_DIGEST_MISMATCH"):
            call(decision, poisoned, kwargs)

    def test_capacity_binding_mismatch_fails_closed(self):
        _p, decision, plan, kwargs = fixture()
        binding = plan_binding(plan)
        binding["capacity_receipt_sha256"] = digest("other-capacity")
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_BINDING_CAPACITY_MISMATCH"):
            call(decision, plan, kwargs, bindings={plan.plan_sha256: binding})

    def test_script_cell_cannot_claim_model_output(self):
        _p, decision, plan, kwargs = fixture()
        script = next(c for c in plan.cells if c.execution_class is ExecutionClass.SCRIPT)
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_CELL_NOT_MODEL_EXECUTION"):
            call(decision, plan, kwargs, cell_id=script.cell_id)

    def test_model_cell_must_match_explicit_route_lane(self):
        _p, decision, plan, kwargs = fixture()
        models = [c for c in plan.cells if c.execution_class is ExecutionClass.MODEL]
        if len(models) < 2:
            self.skipTest("route emitted fewer than two model lanes")
        wrong_lane = models[1].function.split("MODEL:", 1)[1]
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_CELL_MODEL_LANE_MISMATCH"):
            call(decision, plan, kwargs, cell_id=models[0].cell_id, lane=wrong_lane)

    def test_plan_route_mismatch_fails_closed_before_inner_receipt(self):
        _p, decision, plan, kwargs = fixture()
        poisoned = replace(plan, route_decision_sha256=digest("other-route"))
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_DIGEST_MISMATCH"):
            call(decision, poisoned, kwargs)


if __name__ == "__main__":
    unittest.main()
