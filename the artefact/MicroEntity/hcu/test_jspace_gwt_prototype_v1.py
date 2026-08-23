import unittest
from dataclasses import replace

from grid10_scheduler_v1 import HCUMode, RuntimeCapacity, compile_plan
from jspace_gwt_prototype_v1 import (
    GWTCompetitor,
    JSpaceGWTError,
    make_transition_trace,
    select_gwt,
    validate_transition_trace,
)
from jspace_vector_control_v1 import encode_vector
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, EngineAdmission, route_event
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event

GENERATION = 91
CAPABILITY_BINDING_SHA256 = "2" * 64
ENGINE_SHA256 = "a" * 64
BASIS_ID = "basis:test:gwt:42"
BASIS_SHA256 = "b" * 64


def _entry_binding(event_sha256):
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA
    return {
        "schema": ENTRY_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": event_sha256,
    }


def _path():
    entry = {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:jspace",
        "causal_id": "causal:test:jspace",
        "entity_generation": GENERATION,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-24T00:20:00+07:00",
        "received_time": "2026-08-24T00:20:01+07:00",
        "provenance_ref": "entityos:source:test:jspace",
        "provenance_sha256": "1" * 64,
        "capabilities": ["hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:test:jspace",
        "budget": {"max_model_calls": 4, "max_tokens": 2400, "max_wall_ms": 5000},
        "payload_ref": "entityos:payload:test:jspace",
        "payload_sha256": "3" * 64,
    }
    packet = admit_entry(
        entry,
        current_generation=GENERATION,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("hcu.route",),
        admitted_budget=entry["budget"],
    )
    bindings = {packet.admission_sha256: _entry_binding(packet.event_sha256)}
    event = to_hcu_reactive_event(packet, contradiction=0.8, uncertainty=0.7)
    decision = route_event(
        event,
        current_generation=GENERATION,
        engine_admission=EngineAdmission(
            "hcu", "hcu_local_08b", "LOCAL_SHARED_WEIGHT_08B", ENGINE_SHA256
        ),
        admitted_engine_artifacts={"hcu_local_08b": ENGINE_SHA256},
        admitted_entry_bindings=bindings,
    )
    capacity = RuntimeCapacity("runtime:test:jspace", "4" * 64, 10, 1)
    plan = compile_plan(
        packet,
        decision=decision,
        mode=HCUMode.GRID10,
        capacity=capacity,
        current_generation=GENERATION,
        admitted_entry_bindings=bindings,
        admitted_capacity_receipts={
            capacity.capacity_receipt_sha256: {
                "profile_id": capacity.profile_id,
                "max_logical_cells": capacity.max_logical_cells,
                "physical_decoder_limit": capacity.physical_decoder_limit,
            }
        },
    )
    model_cell = next(cell for cell in plan.cells if cell.function == "MODEL:critic")
    return packet, decision, plan, model_cell


def _competitors():
    return (
        GWTCompetitor("cand:critic", "critic", 9000, 5000, 9000, 9000, "evidence:critic", "5" * 64),
        GWTCompetitor("cand:world", "world", 7000, 8000, 3000, 8000, "evidence:world", "6" * 64),
        GWTCompetitor("cand:hyp", "hypothesis", 6500, 6000, 7000, 6000, "evidence:hyp", "7" * 64),
        GWTCompetitor("cand:noise", "critic", 1000, 1000, 1000, 1000, "evidence:noise", "8" * 64),
    )


def _trace(*, control_condition="BASELINE", vector=None, trace_id="trace:test:1", role="critic", budget=None):
    packet, decision, plan, cell = _path()
    vector_packet = encode_vector(
        vector or (0.25, -0.5, 1.0, 0.125),
        basis_id=BASIS_ID,
        basis_sha256=BASIS_SHA256,
        generation=GENERATION,
        role=role,
        control_condition=control_condition,
    )
    return make_transition_trace(
        trace_id=trace_id,
        packet=packet,
        decision=decision,
        plan=plan,
        vector_packet=vector_packet,
        current_generation=GENERATION,
        cell_id=cell.cell_id,
        role="critic",
        local_workspace_state_ref="entityos:workspace:test:1",
        competitors=_competitors(),
        global_jspace_slice_ref="entityos:jspace:slice:test:1",
        hyperposition_branch_ids=("branch:a", "branch:b"),
        evidence_class="DETERMINISTIC_CONTROL",
        resource_budget=budget or {"model_tokens": cell.model_token_budget, "wall_ms": 2500},
        requested_action_class="STRUCTURED_HCU_CANDIDATE",
        expected_structured_model_output={"schema": "HCU_ROLE_OUTPUT/v1", "action": "ABSTAIN_OR_PROPOSE"},
        observed_downstream_outcome={"status": "OBSERVED", "accepted": False},
        credit_label="NEUTRAL",
    )


class JSpaceGWTPrototypeTests(unittest.TestCase):
    def test_selector_is_deterministic_bounded_and_not_majority_vote(self):
        first = select_gwt(_competitors(), max_slots=3)
        second = select_gwt(tuple(reversed(_competitors())), max_slots=3)
        self.assertEqual(first, second)
        self.assertEqual(first.winner_ids[0], "cand:critic")
        self.assertEqual(len(first.winner_ids), 3)
        self.assertTrue(first.broadcast_gate)

        high = GWTCompetitor("high", "critic", 10000, 10000, 10000, 10000, "e:high", "9" * 64)
        lows = tuple(
            GWTCompetitor(f"low:{i}", "world", 1000, 1000, 1000, 1000, f"e:low:{i}", f"{i+1:x}" * 64)
            for i in range(3)
        )
        majority_trap = select_gwt((high,) + lows, max_slots=1)
        self.assertEqual(majority_trap.winner_ids, ("high",))

    def test_transition_trace_binds_entry_route_grid_vector_and_required_training_fields(self):
        trace = _trace()
        validate_transition_trace(trace)
        self.assertEqual(trace.generation, GENERATION)
        self.assertEqual(trace.role, "critic")
        self.assertEqual(trace.jspace_basis_id, BASIS_ID)
        self.assertTrue(trace.jspace_input_vector_ref.startswith("sha256:"))
        self.assertEqual(trace.falsifier_lesion_condition, "BASELINE")
        self.assertEqual(dict(trace.resource_budget)["wall_ms"], 2500)
        self.assertEqual(len(trace.trace_sha256), 64)

    def test_matched_budget_null_lesion_is_distinct_without_changing_causal_authority(self):
        baseline = _trace(trace_id="trace:baseline")
        lesion = _trace(
            trace_id="trace:null-lesion",
            vector=(0.0, 0.0, 0.0, 0.0),
            control_condition="LESION",
        )
        self.assertEqual(baseline.entry_event_sha256, lesion.entry_event_sha256)
        self.assertEqual(baseline.route_decision_sha256, lesion.route_decision_sha256)
        self.assertEqual(baseline.grid_plan_sha256, lesion.grid_plan_sha256)
        self.assertEqual(baseline.resource_budget, lesion.resource_budget)
        self.assertNotEqual(baseline.jspace_input_vector_ref, lesion.jspace_input_vector_ref)
        self.assertNotEqual(baseline.trace_sha256, lesion.trace_sha256)
        self.assertEqual(lesion.falsifier_lesion_condition, "LESION")

    def test_role_swap_fails_against_grid_cell_role(self):
        with self.assertRaisesRegex(JSpaceGWTError, "JSPACE_ROLE_VECTOR_PACKET_MISMATCH"):
            _trace(role="world")

    def test_causal_path_tamper_fails_closed(self):
        packet, decision, plan, cell = _path()
        vector_packet = encode_vector(
            (0.25, -0.5, 1.0),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role="critic",
        )
        bad_plan = replace(plan, route_decision_sha256="f" * 64)
        with self.assertRaisesRegex(JSpaceGWTError, "CAUSAL_PATH_IDENTITY_MISMATCH:plan.route_decision_sha256"):
            make_transition_trace(
                trace_id="trace:bad:path", packet=packet, decision=decision, plan=bad_plan,
                vector_packet=vector_packet, current_generation=GENERATION, cell_id=cell.cell_id,
                role="critic", local_workspace_state_ref="entityos:workspace:test:1",
                competitors=_competitors(), global_jspace_slice_ref="entityos:jspace:slice:test:1",
                hyperposition_branch_ids=("branch:a",), evidence_class="DETERMINISTIC_CONTROL",
                resource_budget={"model_tokens": cell.model_token_budget, "wall_ms": 2500},
                requested_action_class="STRUCTURED_HCU_CANDIDATE",
                expected_structured_model_output={"schema":"HCU_ROLE_OUTPUT/v1"},
                observed_downstream_outcome={"status":"OBSERVED"}, credit_label="UNKNOWN",
            )

    def test_resource_budget_cannot_exceed_grid_cell_or_turn(self):
        packet, decision, plan, cell = _path()
        with self.assertRaisesRegex(JSpaceGWTError, "RESOURCE_BUDGET_MODEL_TOKENS_EXCEEDED"):
            _trace(budget={"model_tokens": cell.model_token_budget + 1, "wall_ms": 2500})
        with self.assertRaisesRegex(JSpaceGWTError, "RESOURCE_BUDGET_WALL_MS_EXCEEDED"):
            _trace(budget={"model_tokens": cell.model_token_budget, "wall_ms": plan.max_wall_ms + 1})


if __name__ == "__main__":
    unittest.main()
