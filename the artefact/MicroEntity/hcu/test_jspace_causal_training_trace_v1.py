import hashlib
import unittest
from dataclasses import replace

from global_jspace_gwt_v1 import CellContribution, step
from grid10_scheduler_v1 import HCUMode, RuntimeCapacity, compile_plan
from inference_receipt_v1 import make_inference_receipt
from jspace_causal_training_trace_v1 import (
    AUTHORITY,
    TRACE_SCHEMA,
    CausalTrainingTraceError,
    bind_causal_training_trace,
)
from reactive_event_router_v1 import route_event
from test_grid10_scheduler_v1 import entry_bindings, packet
from test_inference_receipt_v1 import (
    OUTPUT_SHA256,
    verified_engine_admission,
    verified_engine_load,
    verified_load_receipt,
)
from xeno_entry_fabric_v1 import to_hcu_reactive_event


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def chain():
    entry = packet(max_model_calls=3, max_tokens=2048)
    bindings = entry_bindings(entry)
    verified = verified_engine_admission(generation=7)
    engine_artifacts = {verified.admission.engine_identity: verified.engine_artifact_sha256}
    event = to_hcu_reactive_event(entry, contradiction=0.8, uncertainty=0.7)
    route = route_event(
        event,
        current_generation=7,
        engine_admission=verified.admission,
        admitted_engine_artifacts=engine_artifacts,
        admitted_entry_bindings=bindings,
    )
    load = verified_engine_load(verified, generation=7)
    inference = make_inference_receipt(
        route,
        current_generation=7,
        admitted_route_generations={route.decision_sha256: 7},
        entry_admission_sha256=entry.admission_sha256,
        admitted_entry_bindings=bindings,
        admitted_engine_artifacts=engine_artifacts,
        verified_engine_admission=verified,
        admitted_engine_admission_receipts={verified.receipt_sha256: verified.receipt()},
        verified_engine_load=load,
        admitted_verified_engine_loads={load.consumption_receipt_sha256: verified_load_receipt(load)},
        model_call_id="model-call:jspace-causal:1",
        output_ref="unifieddb:candidate-output:jspace-causal:1",
        output_sha256=OUTPUT_SHA256,
        output_size=128,
    )
    capacity = RuntimeCapacity("runtime:jspace-causal:test", digest("capacity"), 10, 1)
    grid = compile_plan(
        entry,
        decision=route,
        mode=HCUMode.GRID10,
        capacity=capacity,
        current_generation=7,
        admitted_entry_bindings=bindings,
        admitted_capacity_receipts={
            capacity.capacity_receipt_sha256: {
                "profile_id": capacity.profile_id,
                "max_logical_cells": capacity.max_logical_cells,
                "physical_decoder_limit": capacity.physical_decoder_limit,
            }
        },
    )
    a, b = grid.cells[0], grid.cells[1]
    jspace = step(
        [
            CellContribution(a.cell_id, a.function, (0.8, 0.2), 0.9, 0.2, 0.3, 0.8, 0.1),
            CellContribution(b.cell_id, b.function, (-0.2, 0.7), 0.2, 0.8, 0.6, 0.1, 0.1),
        ],
        generation=7,
        basis_id="basis:jspace-causal:test",
        basis_sha256=digest("jspace-basis"),
    )
    return entry, route, grid, inference, jspace


def bind(entry, route, grid, inference, jspace):
    return bind_causal_training_trace(
        entry,
        route,
        grid,
        inference,
        jspace,
        local_workspace_state_ref="unifieddb:workspace:jspace-causal:1",
        jspace_input_vector_ref="unifieddb:jspace-input:jspace-causal:1",
        requested_action_class="CANDIDATE_INFERENCE",
        expected_structured_model_output={"schema": "TEST_OUTPUT/v1", "decision": "CANDIDATE"},
        observed_downstream_outcome={
            "status": "UNVERIFIED_CANDIDATE",
            "output_sha256": inference.output_sha256,
        },
        falsifier_or_lesion_condition="LESION_SELECTED_CELL_AND_COMPARE_DOWNSTREAM_OUTCOME",
        evidence_class="SOURCE_COMPONENT_FIXTURE_ONLY",
        credit_label="NO_RUNTIME_CREDIT",
    )


class JSpaceCausalTrainingTraceTests(unittest.TestCase):
    def test_trace_cross_binds_current_causal_compute_spine(self):
        entry, route, grid, inference, jspace = chain()
        trace = bind(entry, route, grid, inference, jspace)
        self.assertEqual(trace["schema"], TRACE_SCHEMA)
        self.assertEqual(trace["authority"], AUTHORITY)
        self.assertEqual(trace["entry_event_sha256"], entry.event_sha256)
        self.assertEqual(trace["entry_admission_sha256"], entry.admission_sha256)
        self.assertEqual(trace["route_decision_sha256"], route.decision_sha256)
        self.assertEqual(trace["grid_plan_sha256"], grid.plan_sha256)
        self.assertEqual(trace["inference_receipt_sha256"], inference.receipt_sha256)
        self.assertEqual(trace["jspace_trace_sha256"], jspace.trace_sha256)
        self.assertEqual(trace["credit_label"], "NO_RUNTIME_CREDIT")
        self.assertEqual(len(trace["trace_id"]), 64)

    def test_stale_generation_and_wrong_route_receipt_fail_closed(self):
        entry, route, grid, inference, jspace = chain()
        with self.assertRaisesRegex(CausalTrainingTraceError, "CAUSAL_GENERATION_MISMATCH"):
            bind(entry, route, grid, replace(inference, entity_generation=8), jspace)
        with self.assertRaisesRegex(CausalTrainingTraceError, "INFERENCE_ROUTE_DECISION_MISMATCH"):
            bind(entry, route, grid, replace(inference, decision_sha256=digest("foreign-route")), jspace)

    def test_jspace_competition_must_be_inside_bound_grid(self):
        entry, route, grid, inference, jspace = chain()
        foreign = step(
            [CellContribution("foreign-cell", "critic", (0.1, 0.9), 0.9, 0.9, 0.9, 0.2, 0.1)],
            generation=7,
            basis_id=jspace.basis_id,
            basis_sha256=jspace.basis_sha256,
        )
        with self.assertRaisesRegex(CausalTrainingTraceError, "JSPACE_WINNER_NOT_IN_GRID_PLAN"):
            bind(entry, route, grid, inference, foreign)

    def test_unusual_cross_episode_grid_plan_splice_fails_closed(self):
        """This go's single unusual experiment: transplant a foreign causal GRID spine."""
        entry, route, grid, inference, jspace = chain()
        spliced = replace(
            grid,
            plan_sha256=digest("foreign-grid-plan"),
            entry_event_sha256=digest("foreign-entry-event"),
            entry_admission_sha256=digest("foreign-entry-admission"),
        )
        with self.assertRaisesRegex(CausalTrainingTraceError, "GRID_ENTRY_EVENT_MISMATCH"):
            bind(entry, route, spliced, inference, jspace)


if __name__ == "__main__":
    unittest.main()
