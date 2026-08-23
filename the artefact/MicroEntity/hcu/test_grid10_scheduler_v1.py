import unittest
from dataclasses import replace

from grid10_scheduler_v1 import (
    CANONICALIZATION_SCHEMA,
    GRID_PLAN_SCHEMA,
    ExecutionClass,
    GridScheduleError,
    HCUMode,
    RuntimeCapacity,
    compile_plan,
)
from reactive_event_router_v1 import EngineAdmission, route_event
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event

CAPABILITY_BINDING_SHA256 = "2" * 64
ENGINE_SHA256 = "a" * 64


def packet(*, max_model_calls=3, max_tokens=2048, capabilities=("hcu.route",)):
    entry = {
        "schema": "XENO_ENTRY_PACKET/v1", "ingress_id": "ingress:test:grid", "causal_id": "causal:test:grid",
        "entity_generation": 7, "source_kind": "HUMAN_PROMPT", "source_id": "user:test", "modality": "TEXT",
        "observed_time": "2026-08-23T23:40:00+07:00", "received_time": "2026-08-23T23:40:01+07:00",
        "provenance_ref": "unifieddb:source:test:grid", "provenance_sha256": "1" * 64,
        "capabilities": list(capabilities), "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None, "stream_id": "stream:test:grid",
        "budget": {"max_model_calls": max_model_calls, "max_tokens": max_tokens, "max_wall_ms": 5000},
        "payload_ref": "unifieddb:payload:test:grid", "payload_sha256": "3" * 64,
    }
    return admit_entry(entry, current_generation=7, expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
                       admitted_capabilities=("hcu.route",), admitted_budget=entry["budget"])


def model_decision(p):
    event = to_hcu_reactive_event(p, contradiction=0.8, uncertainty=0.7)
    admission = EngineAdmission("hcu", "hcu_local_08b", "LOCAL_SHARED_WEIGHT_08B", ENGINE_SHA256)
    return route_event(event, current_generation=7, engine_admission=admission,
                       admitted_engine_artifacts={"hcu_local_08b": ENGINE_SHA256},
                       admitted_entry_bindings={p.admission_sha256: p.event_sha256})


def capacity(*, logical=10, physical=1, receipt="4" * 64):
    return RuntimeCapacity("runtime:kvm4:test", receipt, logical, physical)


def entry_bindings(p): return {p.admission_sha256: p.event_sha256}
def capacity_receipts(c):
    return {c.capacity_receipt_sha256: {"profile_id": c.profile_id, "max_logical_cells": c.max_logical_cells,
                                        "physical_decoder_limit": c.physical_decoder_limit}}
def compile(p, d, c, *, mode=HCUMode.GRID10, generation=7):
    return compile_plan(p, decision=d, mode=mode, capacity=c, current_generation=generation,
                        admitted_entry_bindings=entry_bindings(p), admitted_capacity_receipts=capacity_receipts(c))


class Grid10SchedulerTests(unittest.TestCase):
    def test_grid10_binds_route_and_separates_logical_model_physical_counts(self):
        p=packet(); d=model_decision(p); c=capacity(physical=1); plan=compile(p,d,c)
        self.assertEqual(plan.schema,GRID_PLAN_SCHEMA); self.assertEqual(GRID_PLAN_SCHEMA,"ENTITYOS_HCU_GRID_PLAN/v2")
        self.assertEqual(plan.canonicalization_schema,CANONICALIZATION_SCHEMA); self.assertEqual(CANONICALIZATION_SCHEMA,"RFC8785_JCS_IJSON/v1")
        self.assertEqual(plan.logical_cell_count,10); self.assertEqual(plan.model_call_count,len(d.model_lanes)); self.assertEqual(plan.physical_decoder_limit,1)
        self.assertEqual(plan.route_decision_sha256,d.decision_sha256); self.assertEqual(plan.engine_identity_sha256,d.engine_identity_sha256)
        models=[x for x in plan.cells if x.execution_class is ExecutionClass.MODEL]
        self.assertEqual(sum(x.model_token_budget for x in models),2048)

    def test_two_physical_decoders_time_slice_route_lanes(self):
        p=packet(); d=model_decision(p); c=capacity(physical=2); plan=compile(p,d,c)
        lanes=[x.physical_decoder_lane for x in plan.cells if x.execution_class is ExecutionClass.MODEL]
        self.assertEqual(lanes,[i%2 for i in range(len(lanes))])

    def test_plan_identity_binds_route_engine_capacity(self):
        p=packet(); d=model_decision(p); c=capacity(); base=compile(p,d,c)
        route=compile(p,replace(d,decision_sha256="f"*64),c)
        engine=compile(p,replace(d,engine_identity_sha256="e"*64),c)
        c2=capacity(receipt="5"*64); cap=compile(p,d,c2)
        self.assertEqual(len({base.plan_sha256,route.plan_sha256,engine.plan_sha256,cap.plan_sha256}),4)

    def test_route_admission_mismatch_fails(self):
        p=packet(); d=replace(model_decision(p),entry_admission_sha256="e"*64); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"ROUTE_ENTRY_ADMISSION_MISMATCH"): compile(p,d,c)

    def test_external_entry_and_capacity_authorities_are_required(self):
        p=packet(); d=model_decision(p); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"ENTRY_ADMISSION_NOT_REGISTERED"):
            compile_plan(p,decision=d,mode=HCUMode.GRID10,capacity=c,current_generation=7,admitted_entry_bindings={},admitted_capacity_receipts=capacity_receipts(c))
        with self.assertRaisesRegex(GridScheduleError,"CAPACITY_RECEIPT_NOT_ADMITTED"):
            compile_plan(p,decision=d,mode=HCUMode.GRID10,capacity=c,current_generation=7,admitted_entry_bindings=entry_bindings(p),admitted_capacity_receipts={})

    def test_stale_generation_fails(self):
        p=packet(); d=model_decision(p); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"STALE_ENTITY_GENERATION"): compile(p,d,c,generation=8)

    def test_script_only_and_external_route_fail(self):
        p=packet(); e=to_hcu_reactive_event(p); script=route_event(e,current_generation=7,admitted_entry_bindings=entry_bindings(p)); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"GRID10_REQUIRES_SELECTIVE_MODEL_ROUTE"): compile(p,script,c)
        d=replace(model_decision(p),external_provider_dependency=True)
        with self.assertRaisesRegex(GridScheduleError,"EXTERNAL_PROVIDER_DEPENDENCY_FORBIDDEN"): compile(p,d,c)

    def test_route_lane_count_must_fit_entry_budget(self):
        p=packet(max_model_calls=1); d=model_decision(p); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"MODEL_CALL_BUDGET_EXCEEDED"): compile(p,d,c)
        p=packet(max_model_calls=3,max_tokens=2); d=model_decision(p)
        with self.assertRaisesRegex(GridScheduleError,"MODEL_TOKEN_BUDGET_TOO_SMALL"): compile(p,d,c)

    def test_logical_capacity_fails(self):
        p=packet(); d=model_decision(p); c=capacity(logical=9)
        with self.assertRaisesRegex(GridScheduleError,"LOGICAL_CELL_CAPACITY_EXCEEDED"): compile(p,d,c)

    def test_non_grid_modes_fail_until_separately_admitted(self):
        p=packet(); d=model_decision(p); c=capacity()
        for mode in (HCUMode.COGSIM10,HCUMode.WM_TEST,HCUMode.NESTED_SIM,HCUMode.SCALEOUT):
            with self.assertRaisesRegex(GridScheduleError,"MODE_REQUIRES_SEPARATE_ADMITTED_CONTROL_PROFILE"): compile(p,d,c,mode=mode)

    def test_exact_engine_identity_required(self):
        p=packet(); d=replace(model_decision(p),engine_identity_sha256=None); c=capacity()
        with self.assertRaisesRegex(GridScheduleError,"engine_identity_sha256"): compile(p,d,c)

if __name__ == '__main__': unittest.main()
