import unittest
from dataclasses import replace

from grid10_scheduler_v1 import ExecutionClass, HCUMode, RuntimeCapacity, compile_plan
from reactive_event_router_v1 import EngineAdmission, route_event
from scheduled_inference_receipt_v2 import ScheduledInferenceReceiptError, make_scheduled_inference_receipt
from test_inference_receipt_v1 import ENGINE_SHA256, OUTPUT_SHA256, engine_admission_receipt, engine_load_lease
from xeno_entry_fabric_v1 import CANONICALIZATION_SCHEMA, admit_entry, to_hcu_reactive_event

CAPABILITY_BINDING_SHA256 = "b" * 64


def fixture():
    raw = {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:scheduled:1",
        "causal_id": "causal:scheduled:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:55:00+07:00",
        "received_time": "2026-08-23T23:55:01+07:00",
        "provenance_ref": "unifieddb:source:scheduled:1",
        "provenance_sha256": "c" * 64,
        "capabilities": ["hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:scheduled",
        "budget": {"max_model_calls": 3, "max_tokens": 2048, "max_wall_ms": 2500},
        "payload_ref": "unifieddb:payload:scheduled:1",
        "payload_sha256": "e" * 64,
    }
    packet = admit_entry(
        raw,
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("hcu.route",),
        admitted_budget=raw["budget"],
    )
    router_bindings = {
        packet.admission_sha256: {
            "schema": "ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/v2",
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "event_sha256": packet.event_sha256,
        }
    }
    legacy_consumer_bindings = {packet.admission_sha256: packet.event_sha256}
    artifacts = {"hcu_local_08b": ENGINE_SHA256}
    event = to_hcu_reactive_event(packet, novelty=0.8)
    event["requested_internal_provider"] = "hcu"
    decision = route_event(
        event,
        current_generation=7,
        engine_admission=EngineAdmission("hcu", "hcu_local_08b", "LOCAL_SHARED_WEIGHT_08B", ENGINE_SHA256),
        admitted_engine_artifacts=artifacts,
        admitted_entry_bindings=router_bindings,
    )
    return packet, decision, legacy_consumer_bindings, artifacts


def plan(packet, decision, bindings, *, receipt, physical):
    capacity = RuntimeCapacity("runtime:test:scheduled", receipt, 10, physical)
    value = compile_plan(
        packet,
        decision=decision,
        mode=HCUMode.GRID10,
        capacity=capacity,
        current_generation=7,
        admitted_entry_bindings=bindings,
        admitted_capacity_receipts={receipt: {"profile_id": capacity.profile_id, "max_logical_cells": 10, "physical_decoder_limit": physical}},
    )
    model_cell = next(cell.cell_id for cell in value.cells if cell.execution_class is ExecutionClass.MODEL)
    return value, model_cell


def common(packet, decision, bindings, artifacts):
    receipt = engine_admission_receipt()
    lease = engine_load_lease(engine_receipt=receipt)
    return {
        "current_generation": 7,
        "admitted_route_generations": {decision.decision_sha256: 7},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": bindings,
        "admitted_engine_artifacts": artifacts,
        "engine_admission_receipt_sha256": receipt["receipt_sha256"],
        "admitted_engine_admission_receipts": {receipt["receipt_sha256"]: receipt},
        "engine_load_lease_sha256": lease["lease_sha256"],
        "admitted_engine_load_leases": {lease["lease_sha256"]: lease},
        "model_call_id": "model-call:scheduled:1",
        "output_ref": "unifieddb:candidate-output:scheduled:1",
        "output_sha256": OUTPUT_SHA256,
        "output_size": 128,
    }


class ScheduledInferenceReceiptTests(unittest.TestCase):
    def test_distinct_admitted_grid_plans_produce_distinct_receipts(self):
        packet, decision, bindings, artifacts = fixture()
        a, cell_a = plan(packet, decision, bindings, receipt="5" * 64, physical=1)
        b, cell_b = plan(packet, decision, bindings, receipt="6" * 64, physical=2)
        kwargs = common(packet, decision, bindings, artifacts)
        ra = make_scheduled_inference_receipt(decision, grid_plan=a, admitted_grid_plans={a.plan_sha256: decision.decision_sha256}, grid_cell_id=cell_a, **kwargs)
        rb = make_scheduled_inference_receipt(decision, grid_plan=b, admitted_grid_plans={b.plan_sha256: decision.decision_sha256}, grid_cell_id=cell_b, **kwargs)
        self.assertNotEqual(a.plan_sha256, b.plan_sha256)
        self.assertNotEqual(ra.receipt_sha256, rb.receipt_sha256)
        self.assertEqual(ra.engine_load_lease_sha256, kwargs["engine_load_lease_sha256"])

    def test_unadmitted_plan_fails_closed(self):
        packet, decision, bindings, artifacts = fixture()
        grid_plan, cell = plan(packet, decision, bindings, receipt="5" * 64, physical=1)
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_NOT_ADMITTED"):
            make_scheduled_inference_receipt(decision, grid_plan=grid_plan, admitted_grid_plans={}, grid_cell_id=cell, **common(packet, decision, bindings, artifacts))

    def test_plan_route_binding_mismatch_fails_closed(self):
        packet, decision, bindings, artifacts = fixture()
        grid_plan, cell = plan(packet, decision, bindings, receipt="5" * 64, physical=1)
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_ROUTE_BINDING_MISMATCH"):
            make_scheduled_inference_receipt(decision, grid_plan=grid_plan, admitted_grid_plans={grid_plan.plan_sha256: "9" * 64}, grid_cell_id=cell, **common(packet, decision, bindings, artifacts))

    def test_script_cell_cannot_claim_model_output(self):
        packet, decision, bindings, artifacts = fixture()
        grid_plan, _ = plan(packet, decision, bindings, receipt="5" * 64, physical=1)
        script_cell = next(cell.cell_id for cell in grid_plan.cells if cell.execution_class is ExecutionClass.SCRIPT)
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_CELL_NOT_MODEL_EXECUTION"):
            make_scheduled_inference_receipt(decision, grid_plan=grid_plan, admitted_grid_plans={grid_plan.plan_sha256: decision.decision_sha256}, grid_cell_id=script_cell, **common(packet, decision, bindings, artifacts))

    def test_plan_engine_alias_fails_closed(self):
        packet, decision, bindings, artifacts = fixture()
        grid_plan, cell = plan(packet, decision, bindings, receipt="5" * 64, physical=1)
        poisoned = replace(grid_plan, engine_identity_sha256="9" * 64)
        with self.assertRaisesRegex(ScheduledInferenceReceiptError, "GRID_PLAN_ENGINE_IDENTITY_MISMATCH"):
            make_scheduled_inference_receipt(decision, grid_plan=poisoned, admitted_grid_plans={poisoned.plan_sha256: decision.decision_sha256}, grid_cell_id=cell, **common(packet, decision, bindings, artifacts))


if __name__ == "__main__":
    unittest.main()
