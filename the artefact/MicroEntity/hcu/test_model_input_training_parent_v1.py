import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import model_input_training_parent_v1 as parent_module
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
    validate_grid_plan_identity,
)
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_execution_receipt_v1 import (
    ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
    OBSERVATION_SCHEMA,
    ModelExecutionObservation,
    model_execution_invocation_binding_key,
    model_execution_observation_record,
    model_execution_observation_sha256,
)
from model_input_control_admission_store_v1 import admit_model_input_control_binding
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from model_input_training_parent_v1 import (
    ModelInputTrainingParentError,
    require_admitted_model_input_training_parent,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA


GENERATION = 7
BASIS_SHA256 = "1" * 64


def h(n: int) -> str:
    return f"{n:064x}"


class ModelInputTrainingParentTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = sqlite3.connect(Path(self.tempdir.name) / "miniunified.db")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
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

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def plan(self) -> GridPlan:
        cells = (
            CellLease("critic.0", "MODEL:critic", ExecutionClass.MODEL, 256, 0),
        )
        provisional = GridPlan(
            schema=PLAN_SCHEMA,
            canonicalization_schema=CANONICALIZATION_SCHEMA,
            entry_binding_schema=ENTRY_BINDING_SCHEMA,
            plan_sha256=h(5),
            ingress_id="ingress:model-input-training-parent:1",
            causal_id="causal:model-input-training-parent:1",
            entity_generation=GENERATION,
            entry_event_sha256=h(2),
            entry_admission_sha256=h(3),
            route_event_sha256=h(40),
            route_decision_sha256=h(4),
            router_policy_sha256=h(41),
            engine_identity_sha256=h(42),
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=h(43),
            capacity_receipt_sha256=h(44),
            runtime_profile_id="runtime:model-input-training-parent:test",
            mode=HCUMode.GRID10,
            logical_cell_count=1,
            model_call_count=1,
            physical_decoder_limit=1,
            max_wall_ms=1000,
            cells=cells,
        )
        plan_sha256 = hashlib.sha256(
            canonicalize(grid_plan_material(provisional))
        ).hexdigest()
        plan = replace(provisional, plan_sha256=plan_sha256)
        validate_grid_plan_identity(plan)
        return plan

    def packet(self):
        return encode_vector(
            (0.25, -0.5, 1.0),
            basis_id="basis:7",
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role="critic",
            control_condition="BASELINE",
        )

    def consumed(self, packet=None):
        packet = packet or self.packet()
        return b'{"system":"hcu"}\n' + packet_bytes(packet) + b'\n{"prompt":"solve"}'

    def binding(self, plan, consumed=None):
        packet = self.packet()
        consumed = consumed if consumed is not None else self.consumed(packet)
        return bind_direct_unique_packet_input(
            packet,
            consumed,
            generation=GENERATION,
            entry_event_sha256=plan.entry_event_sha256,
            entry_admission_sha256=plan.entry_admission_sha256,
            route_decision_sha256=plan.route_decision_sha256,
            grid_plan_sha256=plan.plan_sha256,
            cell_id="critic.0",
            role="critic",
            executor_id="local-qwen-executor:v1",
            invocation_id="invocation:episode-1:step-1",
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )

    def observation(self, binding):
        return ModelExecutionObservation(
            schema=OBSERVATION_SCHEMA,
            evidence_source=ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
            entity_generation=binding.generation,
            executor_id=binding.executor_id,
            invocation_id=binding.invocation_id,
            engine_load_consumption_receipt_sha256=h(11),
            grid_plan_sha256=binding.grid_plan_sha256,
            output_producing_cell_id=binding.cell_id,
            role=binding.role,
            input_sha256=binding.input_sha256,
            input_size=binding.input_size,
            output_ref="unifieddb:model-output:1",
            output_sha256=h(12),
            output_size=17,
        )

    def seed_model_execution(self, observation):
        record = model_execution_observation_record(observation)
        observation_sha = model_execution_observation_sha256(observation)
        invocation_key = model_execution_invocation_binding_key(observation)
        self.db.execute(
            "INSERT INTO hcu_model_execution_observations "
            "(observation_sha256,observation_jcs,entity_generation,executor_id,invocation_id) "
            "VALUES(?,?,?,?,?)",
            (
                observation_sha,
                canonicalize(record),
                record["entity_generation"],
                record["executor_id"],
                record["invocation_id"],
            ),
        )
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            (
                invocation_key,
                record["executor_id"],
                record["invocation_id"],
                record["entity_generation"],
                observation_sha,
            ),
        )
        self.db.commit()
        return observation_sha

    def dataset_admission(self, binding, **overrides):
        values = dict(
            training_trace_sha256=h(20),
            generation=binding.generation,
            entry_event_sha256=binding.entry_event_sha256,
            entry_admission_sha256=binding.entry_admission_sha256,
            route_decision_sha256=binding.route_decision_sha256,
            grid_plan_sha256=binding.grid_plan_sha256,
            cell_id=binding.cell_id,
            role=binding.role,
            jspace_basis_id=binding.jspace_basis_id,
            jspace_basis_sha256=binding.jspace_basis_sha256,
            vector_control_packet_sha256=binding.vector_control_packet_sha256,
            vector_control_condition=binding.vector_control_condition,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def inference_binding(self, binding, observation_sha, **overrides):
        values = dict(
            inference_receipt_sha256=h(21),
            model_execution_executor_id=binding.executor_id,
            model_execution_invocation_id=binding.invocation_id,
            model_execution_observation_sha256=observation_sha,
            input_sha256=binding.input_sha256,
            input_size=binding.input_size,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def seed_full_parent(self):
        plan = self.plan()
        consumed = self.consumed()
        binding = self.binding(plan, consumed)
        observation_sha = self.seed_model_execution(self.observation(binding))
        store_admission = admit_model_input_control_binding(
            self.db,
            binding,
            consumed,
            plan,
            current_generation=GENERATION,
        )
        admission = self.dataset_admission(binding)
        inference = self.inference_binding(binding, observation_sha)
        return plan, consumed, binding, observation_sha, store_admission, admission, inference

    def require(self, consumed, admission, inference):
        with (
            patch.object(
                parent_module,
                "require_admitted_inference_receipt_parent",
                return_value={"receipt": "admitted"},
            ) as inference_parent,
            patch.object(
                parent_module,
                "require_admitted_vector_control_packet_parent",
                return_value=self.packet(),
            ) as vector_parent,
        ):
            result = require_admitted_model_input_training_parent(
                self.db,
                admission,
                inference,
                consumed,
                admitted_inference_receipts={h(21): {"receipt": "admitted"}},
                admitted_vector_control_packets={
                    admission.vector_control_packet_sha256: self.packet()
                },
            )
            self.assertEqual(inference_parent.call_count, 1)
            self.assertEqual(vector_parent.call_count, 1)
            return result

    def test_exact_canonical_parent_readback_cross_binds_training_row(self):
        (
            _plan,
            consumed,
            binding,
            observation_sha,
            store_admission,
            admission,
            inference,
        ) = self.seed_full_parent()
        observed = self.require(consumed, admission, inference)
        self.assertEqual(observed.schema, parent_module.PARENT_SCHEMA)
        self.assertEqual(observed.model_input_binding_sha256, binding.binding_sha256)
        self.assertEqual(
            observed.model_input_admission_sha256,
            store_admission.admission_sha256,
        )
        self.assertEqual(observed.model_execution_observation_sha256, observation_sha)
        self.assertEqual(observed.training_trace_sha256, h(20))
        self.assertEqual(observed.input_sha256, binding.input_sha256)

    def test_missing_canonical_input_parent_fails_closed(self):
        plan = self.plan()
        consumed = self.consumed()
        binding = self.binding(plan, consumed)
        observation_sha = self.seed_model_execution(self.observation(binding))
        admission = self.dataset_admission(binding)
        inference = self.inference_binding(binding, observation_sha)
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_CONTROL_CANONICAL_ADMISSION_STORE_REQUIRED",
        ):
            self.require(consumed, admission, inference)

    def test_mutated_executor_input_bytes_fail_revalidation(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_CONTROL_BINDING_REVALIDATION_FAILED",
        ):
            self.require(consumed + b"!", admission, inference)

    def test_inference_input_cross_splice_fails_closed(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(**{**vars(inference), "input_sha256": h(99)})
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:inference.input_sha256",
        ):
            self.require(consumed, admission, forged)

    def test_inference_observation_cross_splice_fails_closed(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(
            **{**vars(inference), "model_execution_observation_sha256": h(98)}
        )
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:inference.model_execution_observation_sha256",
        ):
            self.require(consumed, admission, forged)

    def test_dataset_admission_route_cross_splice_fails_closed(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(**{**vars(admission), "route_decision_sha256": h(97)})
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:admission.route_decision_sha256",
        ):
            self.require(consumed, forged, inference)

    def test_dataset_admission_vector_cross_splice_fails_closed(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(
            **{**vars(admission), "vector_control_packet_sha256": h(96)}
        )
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:admission.vector_control_packet_sha256",
        ):
            self.require(consumed, forged, inference)

    def test_stored_binding_bytes_cannot_be_mutated_without_detection(self):
        _plan, consumed, binding, _obs, _store, admission, inference = self.seed_full_parent()
        record = asdict(binding)
        record["role"] = "world"
        self.db.execute(
            "UPDATE hcu_model_input_control_bindings SET binding_jcs=? WHERE binding_sha256=?",
            (canonicalize(record), binding.binding_sha256),
        )
        self.db.commit()
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_CONTROL_BINDING_REVALIDATION_FAILED",
        ):
            self.require(consumed, admission, inference)

    def test_inference_parent_rejection_is_fail_closed(self):
        _plan, consumed, _binding, _obs, _store, admission, inference = self.seed_full_parent()
        with patch.object(
            parent_module,
            "require_admitted_inference_receipt_parent",
            side_effect=parent_module.JSpaceInferenceParentAdmissionError("PARENT_BAD"),
        ):
            with self.assertRaisesRegex(
                ModelInputTrainingParentError,
                "INFERENCE_PARENT_ADMISSION_REJECTED:PARENT_BAD",
            ):
                require_admitted_model_input_training_parent(
                    self.db,
                    admission,
                    inference,
                    consumed,
                    admitted_inference_receipts={},
                    admitted_vector_control_packets={},
                )


if __name__ == "__main__":
    unittest.main()
