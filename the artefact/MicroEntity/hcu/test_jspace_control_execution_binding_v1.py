import hashlib
import sqlite3
import unittest
from dataclasses import asdict, replace

import jspace_control_execution_binding_v1 as module
from entry_canonicalization_v1 import canonicalize
from global_jspace_gwt_v1 import CellContribution, step
from jspace_control_execution_binding_v1 import (
    JSpaceControlExecutionBindingError,
    bind_control_packet_to_verified_execution,
    validate_control_execution_binding,
)
from jspace_training_trace_v1 import build_training_trace
from jspace_vector_control_v1 import packet_bytes
from model_execution_admission_store_v1 import admit_and_verify_model_execution
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from test_model_execution_receipt_v1 import grid_plan, observation, verified_load


BASIS_SHA256 = "1" * 64


def open_db(generation: int = 7) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute(
        "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
    )
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


def receipt_rehash(value):
    material = asdict(value)
    material.pop("receipt_sha256", None)
    return replace(value, receipt_sha256=hashlib.sha256(canonicalize(material)).hexdigest())


class ControlExecutionBindingTests(unittest.TestCase):
    def setUp(self):
        self.db = open_db()
        self.plan = grid_plan()
        self.load = verified_load(self.plan)
        cells = [
            CellContribution("cell-00", "RETRIEVAL", (0.1, 0.0, 0.0), 0.1, 0.1, 0.1, 0.1, 0.1),
            CellContribution("cell-02", "ANALYZE", (0.9, 0.4, -0.2), 0.9, 0.9, 0.8, 0.7, 0.6),
        ]
        self.proto = step(
            cells,
            generation=self.plan.entity_generation,
            basis_id="basis:control-execution:1",
            basis_sha256=BASIS_SHA256,
        )
        self.trace = build_training_trace(
            self.proto,
            self.proto.control_packet,
            trace_id="trace:control-execution:1",
            trace_family_id="family:control-execution:1",
            entry_event_sha256=self.plan.entry_event_sha256,
            entry_admission_sha256=self.plan.entry_admission_sha256,
            route_decision_sha256=self.plan.route_decision_sha256,
            grid_plan_sha256=self.plan.plan_sha256,
            jspace_input_vector_ref="unifieddb:jspace-input:control-execution:1",
            local_workspace_state_ref="unifieddb:workspace:control-execution:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:control-execution:1",
            hyperposition_branch_ids=("branch:control-execution:1",),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        self.consumed = (
            b'{"system":"entityos-hcu"}\n'
            + packet_bytes(self.proto.control_packet)
            + b'\n{"prompt":"analyze"}'
        )
        base_observation = observation(self.plan, self.load)
        self.observation = replace(
            base_observation,
            executor_id="entityos:hcu:model-executor:control-execution:1",
            invocation_id="invocation:control-execution:1",
            input_sha256=hashlib.sha256(self.consumed).hexdigest(),
            input_size=len(self.consumed),
        )
        self.verified = admit_and_verify_model_execution(
            self.db,
            self.plan,
            self.load,
            self.observation,
            current_generation=self.plan.entity_generation,
        )
        self.input_binding = bind_direct_unique_packet_input(
            self.proto.control_packet,
            self.consumed,
            generation=self.plan.entity_generation,
            entry_event_sha256=self.plan.entry_event_sha256,
            entry_admission_sha256=self.plan.entry_admission_sha256,
            route_decision_sha256=self.plan.route_decision_sha256,
            grid_plan_sha256=self.plan.plan_sha256,
            cell_id=self.trace.cell_id,
            role=self.trace.role,
            executor_id=self.verified.executor_id,
            invocation_id=self.verified.invocation_id,
            executor_observed_input_sha256=hashlib.sha256(self.consumed).hexdigest(),
            executor_observed_input_size=len(self.consumed),
        )

    def tearDown(self):
        self.db.close()

    def bind(self, *, trace=None, input_binding=None, verified=None, db=None):
        return bind_control_packet_to_verified_execution(
            trace or self.trace,
            input_binding or self.input_binding,
            verified or self.verified,
            self.consumed,
            db or self.db,
        )

    def test_exact_canonical_admission_binds_deterministically_without_temporal_labels(self):
        a = self.bind()
        b = self.bind()
        self.assertEqual(a, b)
        self.assertTrue(a.canonical_execution_admission_verified)
        self.assertFalse(hasattr(a, "predecessor_step_index"))
        self.assertFalse(hasattr(a, "controlled_step_index"))
        self.assertEqual(a.invocation_id, self.verified.invocation_id)
        self.assertEqual(a.verified_model_execution_receipt_sha256, self.verified.receipt_sha256)
        validate_control_execution_binding(
            a,
            self.trace,
            self.input_binding,
            self.verified,
            self.consumed,
            self.db,
        )

    def test_self_consistent_verified_execution_not_matching_canonical_observation_fails(self):
        forged = receipt_rehash(
            replace(self.verified, output_sha256=hashlib.sha256(b"forged-output").hexdigest())
        )
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "VERIFIED_EXECUTION_DOES_NOT_MATCH_CANONICAL_OBSERVATION",
        ):
            self.bind(verified=forged)

    def test_missing_canonical_observation_fails_even_with_valid_receipt(self):
        self.db.execute("DELETE FROM hcu_model_execution_invocations")
        self.db.execute("DELETE FROM hcu_model_execution_observations")
        self.db.commit()
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "MODEL_EXECUTION_OBSERVATION_NOT_CANONICALLY_ADMITTED",
        ):
            self.bind()

    def test_missing_unique_invocation_claim_fails_closed(self):
        self.db.execute("DELETE FROM hcu_model_execution_invocations")
        self.db.commit()
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "CANONICAL_MODEL_EXECUTION_INVOCATION_NOT_UNIQUE",
        ):
            self.bind()

    def test_live_generation_change_invalidates_old_execution_admission(self):
        self.db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        self.db.commit()
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "STALE_CANONICAL_MODEL_EXECUTION_ADMISSION_GENERATION",
        ):
            self.bind()

    def test_exact_executor_input_bytes_remain_part_of_the_evidence_chain(self):
        binding = self.bind()
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "MODEL_INPUT_CONTROL_BINDING_REJECTED",
        ):
            validate_control_execution_binding(
                binding,
                self.trace,
                self.input_binding,
                self.verified,
                self.consumed + b"!",
                self.db,
            )

    def test_input_binding_cannot_relabel_executor_invocation(self):
        forged = replace(
            self.input_binding,
            invocation_id="invocation:forged",
            binding_sha256="1" * 64,
        )
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "MODEL_INPUT_CONTROL_BINDING_REJECTED",
        ):
            self.bind(input_binding=forged)

    def test_persisted_binding_cannot_be_self_consistently_relabelled(self):
        binding = self.bind()
        tampered = replace(binding, executor_id="entityos:hcu:model-executor:forged")
        resigned = replace(
            tampered,
            binding_sha256=module._canonical_sha256(
                module._material(tampered),
                "TEST_SELF_CONSISTENT_FORGERY",
            ),
        )
        with self.assertRaisesRegex(
            JSpaceControlExecutionBindingError,
            "JSPACE_CONTROL_EXECUTION_SOURCE_REVALIDATION_MISMATCH",
        ):
            validate_control_execution_binding(
                resigned,
                self.trace,
                self.input_binding,
                self.verified,
                self.consumed,
                self.db,
            )


if __name__ == "__main__":
    unittest.main()
