import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from global_jspace_gwt_v1 import CellContribution, step
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
    validate_grid_plan_identity,
)
from inference_receipt_v1 import (
    SCHEMA as INFERENCE_RECEIPT_SCHEMA,
    STATUS as INFERENCE_RECEIPT_STATUS,
)
from jspace_inference_binding_v1 import (
    JSpaceInferenceBinding,
    SCHEMA as JSPACE_BINDING_SCHEMA,
    validate_binding as validate_jspace_binding,
)
from jspace_training_trace_v1 import TRACE_SCHEMA, build_training_trace
from model_execution_receipt_v1 import (
    ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
    OBSERVATION_SCHEMA,
    ModelExecutionObservation,
    model_execution_invocation_binding_key,
    model_execution_observation_record,
    model_execution_observation_sha256,
)
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from jspace_vector_control_v1 import packet_bytes
from preinvocation_control_admission_store_v1 import (
    PreInvocationControlAdmissionError,
    prepare_preinvocation_control,
    read_preinvocation_control_preparation,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA


GENERATION = 7
BASIS_SHA256 = "1" * 64


def h(n: int) -> str:
    return f"{n:064x}"


class PreInvocationControlAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "miniunified.db"
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (GENERATION,))
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
              observation_sha256 TEXT NOT NULL,
              FOREIGN KEY(observation_sha256)
                REFERENCES hcu_model_execution_observations(observation_sha256)
            )"""
        )
        self.db.commit()
        self.admitted_inference_receipts = {}

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def predecessor_trace(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        proto = step(cells, generation=GENERATION, basis_id="basis:7", basis_sha256=BASIS_SHA256)
        trace = build_training_trace(
            proto,
            proto.control_packet,
            trace_id="trace:episode-1:step-0",
            trace_family_id="episode:1",
            entry_event_sha256=h(2),
            entry_admission_sha256=h(3),
            route_decision_sha256=h(4),
            grid_plan_sha256=h(5),
            jspace_input_vector_ref="unifieddb:jspace-input:0",
            local_workspace_state_ref="unifieddb:workspace:0",
            global_jspace_slice_ref="unifieddb:jspace-slice:0",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        return proto, trace

    def _rehash_binding(self, binding, **changes):
        updated = replace(binding, **changes)
        material = asdict(updated)
        material.pop("binding_sha256", None)
        updated = replace(
            updated,
            binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
        )
        validate_jspace_binding(updated)
        return updated

    def _canonical_predecessor_observation(self, binding):
        return ModelExecutionObservation(
            schema=OBSERVATION_SCHEMA,
            evidence_source=ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
            entity_generation=binding.generation,
            executor_id=binding.model_execution_executor_id,
            invocation_id=binding.model_execution_invocation_id,
            engine_load_consumption_receipt_sha256=binding.engine_load_consumption_receipt_sha256,
            grid_plan_sha256=binding.grid_plan_sha256,
            output_producing_cell_id=binding.output_producing_cell_id,
            role=binding.model_execution_role,
            input_sha256=binding.input_sha256,
            input_size=binding.input_size,
            output_ref=binding.output_ref,
            output_sha256=binding.output_sha256,
            output_size=binding.output_size,
        )

    def _admit_canonical_predecessor(self, binding):
        observation = self._canonical_predecessor_observation(binding)
        observation_sha256 = model_execution_observation_sha256(observation)
        binding = self._rehash_binding(
            binding,
            model_execution_observation_sha256=observation_sha256,
        )
        observation_jcs = canonicalize(model_execution_observation_record(observation))
        self.db.execute(
            "INSERT OR IGNORE INTO hcu_model_execution_observations "
            "(observation_sha256,observation_jcs,entity_generation,executor_id,invocation_id) "
            "VALUES(?,?,?,?,?)",
            (
                observation_sha256,
                observation_jcs,
                observation.entity_generation,
                observation.executor_id,
                observation.invocation_id,
            ),
        )
        self.db.execute(
            "INSERT OR IGNORE INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            (
                model_execution_invocation_binding_key(observation),
                observation.executor_id,
                observation.invocation_id,
                observation.entity_generation,
                observation_sha256,
            ),
        )
        self.db.commit()
        return binding

    def _inference_parent_record(self, binding):
        record = {
            "schema": INFERENCE_RECEIPT_SCHEMA,
            "status": INFERENCE_RECEIPT_STATUS,
            "hash_serialization_schema": CANONICALIZATION_SCHEMA,
            "entry_binding_schema": ENTRY_BINDING_SCHEMA,
            "entity_generation": binding.generation,
            "entry_admission_sha256": binding.entry_admission_sha256,
            "event_sha256": binding.entry_event_sha256,
            "decision_sha256": binding.route_decision_sha256,
            "router_policy_sha256": h(21),
            "engine_identity_sha256": binding.engine_identity_sha256,
            "resolved_engine_identity": binding.resolved_engine_identity,
            "resolved_engine_class": binding.resolved_engine_class,
            "resolved_engine_artifact_sha256": binding.resolved_engine_artifact_sha256,
            "engine_admission_receipt_sha256": binding.engine_admission_receipt_sha256,
            "engine_load_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "engine_load_loader_binding_sha256": binding.engine_load_loader_binding_sha256,
            "engine_load_lease_sha256": binding.engine_load_lease_sha256,
            "engine_load_consumption_receipt_sha256": binding.engine_load_consumption_receipt_sha256,
            "engine_load_loader_id": binding.engine_load_loader_id,
            "model_execution_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "model_execution_receipt_sha256": binding.model_execution_receipt_sha256,
            "model_execution_observation_sha256": binding.model_execution_observation_sha256,
            "model_execution_executor_id": binding.model_execution_executor_id,
            "model_execution_invocation_id": binding.model_execution_invocation_id,
            "grid_plan_sha256": binding.grid_plan_sha256,
            "output_producing_cell_id": binding.output_producing_cell_id,
            "model_execution_role": binding.model_execution_role,
            "input_sha256": binding.input_sha256,
            "input_size": binding.input_size,
            "model_call_id": binding.model_call_id,
            "output_ref": binding.output_ref,
            "output_sha256": binding.output_sha256,
            "output_size": binding.output_size,
            "model_lanes": [binding.role],
        }
        record["receipt_sha256"] = hashlib.sha256(canonicalize(record)).hexdigest()
        return record

    def _admit_inference_parent(self, binding):
        parent = self._inference_parent_record(binding)
        binding = self._rehash_binding(
            binding,
            inference_receipt_sha256=parent["receipt_sha256"],
        )
        self.admitted_inference_receipts[parent["receipt_sha256"]] = parent
        return binding

    def predecessor_binding(
        self,
        trace,
        *,
        invocation_id="invocation:episode-1:step-0",
        admit_canonical_parent=True,
        admit_inference_parent=True,
    ):
        material = {
            "schema": JSPACE_BINDING_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "training_trace_schema": TRACE_SCHEMA,
            "training_trace_sha256": trace.trace_sha256,
            "prototype_trace_sha256": trace.prototype_trace_sha256,
            "generation": GENERATION,
            "entry_event_sha256": trace.entry_event_sha256,
            "entry_admission_sha256": trace.entry_admission_sha256,
            "route_decision_sha256": trace.route_decision_sha256,
            "grid_plan_sha256": trace.grid_plan_sha256,
            "cell_id": trace.cell_id,
            "role": trace.role,
            "vector_control_packet_sha256": trace.vector_control_packet_sha256,
            "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
            "inference_receipt_sha256": h(10),
            "engine_identity_sha256": h(11),
            "resolved_engine_identity": "hcu_local_08b",
            "resolved_engine_class": "LOCAL_SHARED_WEIGHT_08B",
            "resolved_engine_artifact_sha256": h(12),
            "engine_admission_receipt_sha256": h(13),
            "engine_load_loader_binding_sha256": h(14),
            "engine_load_lease_sha256": h(15),
            "engine_load_consumption_receipt_sha256": h(16),
            "engine_load_loader_id": "loader:local:0",
            "model_execution_receipt_sha256": h(17),
            "model_execution_observation_sha256": h(18),
            "model_execution_executor_id": "local-qwen-executor:v1",
            "model_execution_invocation_id": invocation_id,
            "output_producing_cell_id": trace.cell_id,
            "model_execution_role": trace.role,
            "input_sha256": h(19),
            "input_size": 123,
            "model_call_id": invocation_id,
            "output_ref": "unifieddb:model-output:0",
            "output_sha256": h(20),
            "output_size": 17,
        }
        binding_sha = hashlib.sha256(canonicalize(material)).hexdigest()
        binding = JSpaceInferenceBinding(**material, binding_sha256=binding_sha)
        validate_jspace_binding(binding)
        observation = self._canonical_predecessor_observation(binding)
        binding = self._rehash_binding(
            binding,
            model_execution_observation_sha256=model_execution_observation_sha256(observation),
        )
        if admit_canonical_parent:
            binding = self._admit_canonical_predecessor(binding)
        if admit_inference_parent:
            binding = self._admit_inference_parent(binding)
        return binding

    def controlled_plan(self):
        cells = (CellLease("critic.1", "MODEL:critic", ExecutionClass.MODEL, 256, 0),)
        provisional = GridPlan(
            schema=PLAN_SCHEMA,
            canonicalization_schema=CANONICALIZATION_SCHEMA,
            entry_binding_schema=ENTRY_BINDING_SCHEMA,
            plan_sha256=h(30),
            ingress_id="ingress:episode-1:step-1",
            causal_id="causal:episode-1:step-1",
            entity_generation=GENERATION,
            entry_event_sha256=h(31),
            entry_admission_sha256=h(32),
            route_event_sha256=h(33),
            route_decision_sha256=h(34),
            router_policy_sha256=h(35),
            engine_identity_sha256=h(36),
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=h(37),
            capacity_receipt_sha256=h(38),
            runtime_profile_id="runtime:preinvocation:test",
            mode=HCUMode.GRID10,
            logical_cell_count=1,
            model_call_count=1,
            physical_decoder_limit=1,
            max_wall_ms=1000,
            cells=cells,
        )
        plan = replace(
            provisional,
            plan_sha256=hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest(),
        )
        validate_grid_plan_identity(plan)
        return plan

    def controlled_input(self, proto, plan, *, invocation_id="invocation:episode-1:step-1", packet=None):
        packet = packet or proto.control_packet
        consumed = b'{"system":"hcu"}\n' + packet_bytes(packet) + b'\n{"prompt":"solve"}'
        binding = bind_direct_unique_packet_input(
            packet,
            consumed,
            generation=GENERATION,
            entry_event_sha256=plan.entry_event_sha256,
            entry_admission_sha256=plan.entry_admission_sha256,
            route_decision_sha256=plan.route_decision_sha256,
            grid_plan_sha256=plan.plan_sha256,
            cell_id="critic.1",
            role="critic",
            executor_id="local-qwen-executor:v1",
            invocation_id=invocation_id,
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        return binding, consumed

    def sources(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace)
        plan = self.controlled_plan()
        input_binding, consumed = self.controlled_input(proto, plan)
        return proto, trace, predecessor_binding, plan, input_binding, consumed

    def prepare(self, trace, predecessor_binding, input_binding, consumed, plan):
        return prepare_preinvocation_control(
            self.db,
            trace,
            predecessor_binding,
            input_binding,
            consumed,
            plan,
            admitted_inference_receipts=self.admitted_inference_receipts,
            current_generation=GENERATION,
        )

    def test_predecessor_is_committed_before_distinct_controlled_invocation_admission(self):
        _, trace, predecessor_binding, plan, input_binding, consumed = self.sources()
        preparation = self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertEqual(preparation.predecessor_training_trace_sha256, trace.trace_sha256)
        self.assertEqual(preparation.controlled_invocation_id, input_binding.invocation_id)
        self.assertNotEqual(
            preparation.predecessor_model_invocation_id,
            preparation.controlled_invocation_id,
        )
        reread = read_preinvocation_control_preparation(
            self.db,
            executor_id=input_binding.executor_id,
            invocation_id=input_binding.invocation_id,
        )
        self.assertEqual(reread, preparation)
        replay = self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertEqual(replay, preparation)
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_preinvocation_control_preparations").fetchone()[0],
            1,
        )

    def test_self_consistent_predecessor_without_canonical_execution_fails_zero_write(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace, admit_canonical_parent=False)
        plan = self.controlled_plan()
        input_binding, consumed = self.controlled_input(proto, plan)
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "PREDECESSOR_CANONICAL_EXECUTION_REJECTED:"
            "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_NOT_UNIQUELY_ADMITTED",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='hcu_preinvocation_control_preparations'"
            ).fetchone()
        )

    def test_canonical_predecessor_without_admitted_inference_parent_fails_zero_write(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace, admit_inference_parent=False)
        plan = self.controlled_plan()
        input_binding, consumed = self.controlled_input(proto, plan)
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "PREDECESSOR_INFERENCE_PARENT_REJECTED:INFERENCE_RECEIPT_PARENT_NOT_ADMITTED",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='hcu_preinvocation_control_preparations'"
            ).fetchone()
        )

    def test_digest_valid_tampered_inference_parent_fails_before_write(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace)
        plan = self.controlled_plan()
        input_binding, consumed = self.controlled_input(proto, plan)

        admitted = dict(self.admitted_inference_receipts[predecessor_binding.inference_receipt_sha256])
        admitted.pop("receipt_sha256")
        admitted["grid_plan_sha256"] = h(62)
        tampered_sha = hashlib.sha256(canonicalize(admitted)).hexdigest()
        admitted["receipt_sha256"] = tampered_sha
        predecessor_binding = self._rehash_binding(
            predecessor_binding,
            inference_receipt_sha256=tampered_sha,
        )
        self.admitted_inference_receipts = {tampered_sha: admitted}

        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "PREDECESSOR_INFERENCE_PARENT_REJECTED:"
            "INFERENCE_RECEIPT_PARENT_BINDING_MISMATCH:grid_plan_sha256",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='hcu_preinvocation_control_preparations'"
            ).fetchone()
        )

    def test_same_invocation_posthoc_control_is_rejected(self):
        proto, trace = self.predecessor_trace()
        plan = self.controlled_plan()
        input_binding, consumed = self.controlled_input(proto, plan)
        predecessor_binding = self.predecessor_binding(
            trace,
            invocation_id=input_binding.invocation_id,
        )
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "SAME_INVOCATION_POSTHOC_CONTROL_FORBIDDEN",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)

    def test_existing_controlled_model_execution_admission_blocks_posthoc_preparation(self):
        _, trace, predecessor_binding, plan, input_binding, consumed = self.sources()
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations VALUES(?,?,?,?,?)",
            (
                h(50),
                input_binding.executor_id,
                input_binding.invocation_id,
                GENERATION,
                predecessor_binding.model_execution_observation_sha256,
            ),
        )
        self.db.commit()
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_POSTHOC_PREPARATION_FORBIDDEN",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='hcu_preinvocation_control_preparations'"
            ).fetchone()
        )

    def test_same_controlled_invocation_cannot_be_rebound_to_different_predecessor(self):
        _, trace, predecessor_binding, plan, input_binding, consumed = self.sources()
        first = self.prepare(trace, predecessor_binding, input_binding, consumed, plan)
        other_predecessor = self.predecessor_binding(
            trace,
            invocation_id="invocation:episode-0:other-predecessor",
        )
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "PREINVOCATION_CONTROL_INVOCATION_REPLAY_DIVERGENCE",
        ):
            self.prepare(trace, other_predecessor, input_binding, consumed, plan)
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_preinvocation_control_preparations").fetchone()[0],
            1,
        )
        reread = read_preinvocation_control_preparation(
            self.db,
            executor_id=input_binding.executor_id,
            invocation_id=input_binding.invocation_id,
        )
        self.assertEqual(reread, first)

    def test_predecessor_packet_must_be_exact_packet_in_controlled_input(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace)
        plan = self.controlled_plan()
        from jspace_vector_control_v1 import encode_vector

        other = encode_vector(
            tuple(reversed(proto.global_vector)),
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition=proto.control_condition,
        )
        input_binding, consumed = self.controlled_input(proto, plan, packet=other)
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionError,
            "PREDECESSOR_CONTROL_PACKET_IDENTITY_MISMATCH",
        ):
            self.prepare(trace, predecessor_binding, input_binding, consumed, plan)


if __name__ == "__main__":
    unittest.main()
