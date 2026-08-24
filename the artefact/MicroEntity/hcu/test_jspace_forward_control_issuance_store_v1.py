import sqlite3
import unittest

from global_jspace_gwt_v1 import CellContribution, step
from jspace_forward_control_issuance_store_v1 import (
    JSpaceForwardControlIssuanceError,
    issue_forward_control,
    require_forward_control_for_model_input,
    validate_forward_control_issuance,
)
from jspace_training_trace_v1 import build_training_trace
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input


BASIS_SHA256 = "1" * 64


class ForwardControlIssuanceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        # These are the canonical parent-store table names. The temporal issuance store does
        # not mint ModelExecution rows; tests only need the existing authority surface.
        self.db.execute(
            """CREATE TABLE hcu_model_execution_observations(
              observation_sha256 TEXT PRIMARY KEY,
              observation_jcs BLOB NOT NULL,
              entity_generation INTEGER NOT NULL,
              executor_id TEXT NOT NULL,
              invocation_id TEXT NOT NULL
            )"""
        )
        self.db.execute(
            """CREATE TABLE hcu_model_execution_invocations(
              invocation_binding_key TEXT PRIMARY KEY,
              executor_id TEXT NOT NULL,
              invocation_id TEXT NOT NULL,
              entity_generation INTEGER NOT NULL,
              observation_sha256 TEXT NOT NULL
            )"""
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def prototype(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=7, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def trace_and_packet(self, *, trace_id="trace:episode-1:step-1"):
        proto = self.prototype()
        packet = encode_vector(
            proto.global_vector,
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition="BASELINE",
        )
        trace = build_training_trace(
            proto,
            packet,
            trace_id=trace_id,
            trace_family_id="episode:1",
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            jspace_input_vector_ref="unifieddb:jspace-input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        return trace, packet

    def issue(self, *, trace_id="trace:episode-1:step-1", invocation_id="invoke:t+1"):
        trace, packet = self.trace_and_packet(trace_id=trace_id)
        issuance = issue_forward_control(
            self.db,
            trace,
            controlled_executor_id="executor:local-08b",
            controlled_invocation_id=invocation_id,
            current_generation=7,
        )
        return issuance, trace, packet

    def add_execution(self, invocation_id="invoke:t+1"):
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            ("key:" + invocation_id, "executor:local-08b", invocation_id, 7, "9" * 64),
        )
        self.db.commit()

    def binding(self, packet, invocation_id="invoke:t+1"):
        raw = b"prefix\n" + packet_bytes(packet) + b"\nsuffix"
        binding = bind_direct_unique_packet_input(
            packet,
            raw,
            generation=7,
            entry_event_sha256="a" * 64,
            entry_admission_sha256="b" * 64,
            route_decision_sha256="c" * 64,
            grid_plan_sha256="d" * 64,
            cell_id="model.0",
            role=packet.role,
            executor_id="executor:local-08b",
            invocation_id=invocation_id,
            executor_observed_input_sha256=__import__("hashlib").sha256(raw).hexdigest(),
            executor_observed_input_size=len(raw),
        )
        return binding, raw

    def test_pre_invocation_issue_is_self_authenticating_and_durable(self):
        issuance, _, _ = self.issue()
        validate_forward_control_issuance(issuance)
        row = self.db.execute(
            "SELECT issuance_sha256 FROM hcu_jspace_forward_control_issuances "
            "WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            ("executor:local-08b", "invoke:t+1"),
        ).fetchone()
        self.assertEqual(row, (issuance.issuance_sha256,))

    def test_late_post_hoc_issue_after_same_invocation_is_rejected(self):
        self.add_execution()
        trace, _ = self.trace_and_packet()
        with self.assertRaisesRegex(
            JSpaceForwardControlIssuanceError,
            "CONTROLLED_INVOCATION_ALREADY_ADMITTED",
        ):
            issue_forward_control(
                self.db,
                trace,
                controlled_executor_id="executor:local-08b",
                controlled_invocation_id="invoke:t+1",
                current_generation=7,
            )

    def test_exact_replay_remains_idempotent_after_successor_execution(self):
        first, trace, _ = self.issue()
        self.add_execution()
        replay = issue_forward_control(
            self.db,
            trace,
            controlled_executor_id="executor:local-08b",
            controlled_invocation_id="invoke:t+1",
            current_generation=7,
        )
        self.assertEqual(replay, first)

    def test_different_predecessor_trace_cannot_rebind_reserved_invocation(self):
        self.issue()
        trace2, _ = self.trace_and_packet(trace_id="trace:episode-1:step-other")
        with self.assertRaisesRegex(
            JSpaceForwardControlIssuanceError,
            "FORWARD_CONTROL_INVOCATION_REPLAY_DIVERGENCE",
        ):
            issue_forward_control(
                self.db,
                trace2,
                controlled_executor_id="executor:local-08b",
                controlled_invocation_id="invoke:t+1",
                current_generation=7,
            )

    def test_stale_generation_fails_before_issuance_write(self):
        trace, _ = self.trace_and_packet()
        with self.assertRaisesRegex(
            JSpaceForwardControlIssuanceError,
            "PREDECESSOR_TRACE_GENERATION_MISMATCH",
        ):
            issue_forward_control(
                self.db,
                trace,
                controlled_executor_id="executor:local-08b",
                controlled_invocation_id="invoke:t+1",
                current_generation=8,
            )
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hcu_jspace_forward_control_issuances'"
            ).fetchone()
        )

    def test_exact_issued_packet_can_bind_future_executor_input(self):
        issuance, _, packet = self.issue()
        binding, raw = self.binding(packet)
        observed = require_forward_control_for_model_input(self.db, binding, raw)
        self.assertEqual(observed, issuance)
        self.assertEqual(observed.predecessor_vector_control_packet_sha256, binding.vector_control_packet_sha256)

    def test_different_real_packet_in_input_cannot_launder_predecessor_identity(self):
        self.issue()
        proto = self.prototype()
        different_packet = encode_vector(
            tuple(reversed(proto.global_vector)),
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition="BASELINE",
        )
        binding, raw = self.binding(different_packet)
        with self.assertRaisesRegex(
            JSpaceForwardControlIssuanceError,
            "FORWARD_CONTROL_MODEL_INPUT_MISMATCH:vector_control_packet_sha256",
        ):
            require_forward_control_for_model_input(self.db, binding, raw)

    def test_temporal_trigger_is_revalidated_not_assumed(self):
        _, _, packet = self.issue()
        binding, raw = self.binding(packet)
        self.db.execute("DROP TRIGGER hcu_jspace_forward_control_no_late_issue")
        self.db.commit()
        with self.assertRaisesRegex(
            JSpaceForwardControlIssuanceError,
            "FORWARD_CONTROL_TEMPORAL_TRIGGER_REQUIRED",
        ):
            require_forward_control_for_model_input(self.db, binding, raw)


if __name__ == "__main__":
    unittest.main()
