import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import model_input_training_parent_v1 as parent_module
from entry_canonicalization_v1 import canonicalize
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

    def binding(self, consumed=None):
        packet = self.packet()
        consumed = consumed if consumed is not None else self.consumed(packet)
        return bind_direct_unique_packet_input(
            packet,
            consumed,
            generation=GENERATION,
            entry_event_sha256=h(2),
            entry_admission_sha256=h(3),
            route_decision_sha256=h(4),
            grid_plan_sha256=h(5),
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

    def training_parent(self):
        return SimpleNamespace(
            training_trace_sha256=h(20),
            inference_receipt_sha256=h(21),
            vector_control_packet_sha256=self.packet().packet_sha256,
            generation=GENERATION,
            entry_event_sha256=h(2),
            entry_admission_sha256=h(3),
            route_decision_sha256=h(4),
            grid_plan_sha256=h(5),
            cell_id="critic.0",
            role="critic",
            jspace_basis_id="basis:7",
            jspace_basis_sha256=BASIS_SHA256,
            vector_control_condition="BASELINE",
        )

    def seed_full_parent(self):
        consumed = self.consumed()
        binding = self.binding(consumed)
        observation_sha = self.seed_model_execution(self.observation(binding))
        store_admission = admit_model_input_control_binding(
            self.db,
            binding,
            consumed,
            current_generation=GENERATION,
        )
        inference = SimpleNamespace(
            model_execution_executor_id=binding.executor_id,
            model_execution_invocation_id=binding.invocation_id,
            model_execution_observation_sha256=observation_sha,
            input_sha256=binding.input_sha256,
            input_size=binding.input_size,
        )
        return consumed, binding, observation_sha, store_admission, inference

    def require(self, consumed, inference, *, training_parent=None):
        with patch.object(
            parent_module,
            "require_admitted_training_parent_closure",
            return_value=training_parent or self.training_parent(),
        ):
            return require_admitted_model_input_training_parent(
                self.db,
                SimpleNamespace(),
                inference,
                consumed,
                admitted_inference_receipts={"receipt": object()},
                admitted_vector_control_packets={"packet": object()},
            )

    def test_reads_back_exact_canonical_input_parent_and_cross_binds_training(self):
        consumed, binding, observation_sha, store_admission, inference = self.seed_full_parent()
        observed = self.require(consumed, inference)
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
        consumed = self.consumed()
        binding = self.binding(consumed)
        observation_sha = self.seed_model_execution(self.observation(binding))
        inference = SimpleNamespace(
            model_execution_executor_id=binding.executor_id,
            model_execution_invocation_id=binding.invocation_id,
            model_execution_observation_sha256=observation_sha,
            input_sha256=binding.input_sha256,
            input_size=binding.input_size,
        )
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_CONTROL_CANONICAL_ADMISSION_STORE_REQUIRED",
        ):
            self.require(consumed, inference)

    def test_mutated_executor_input_bytes_fail_revalidation(self):
        consumed, _binding, _observation_sha, _store_admission, inference = self.seed_full_parent()
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_CONTROL_BINDING_REVALIDATION_FAILED",
        ):
            self.require(consumed + b"!", inference)

    def test_inference_input_cross_splice_fails_closed(self):
        consumed, _binding, observation_sha, _store_admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(
            model_execution_executor_id=inference.model_execution_executor_id,
            model_execution_invocation_id=inference.model_execution_invocation_id,
            model_execution_observation_sha256=observation_sha,
            input_sha256=h(99),
            input_size=inference.input_size,
        )
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:inference.input_sha256",
        ):
            self.require(consumed, forged)

    def test_inference_observation_cross_splice_fails_closed(self):
        consumed, _binding, _observation_sha, _store_admission, inference = self.seed_full_parent()
        forged = SimpleNamespace(
            model_execution_executor_id=inference.model_execution_executor_id,
            model_execution_invocation_id=inference.model_execution_invocation_id,
            model_execution_observation_sha256=h(98),
            input_sha256=inference.input_sha256,
            input_size=inference.input_size,
        )
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:inference.model_execution_observation_sha256",
        ):
            self.require(consumed, forged)

    def test_training_parent_route_cross_splice_fails_closed(self):
        consumed, _binding, _observation_sha, _store_admission, inference = self.seed_full_parent()
        forged_parent = self.training_parent()
        forged_parent.route_decision_sha256 = h(97)
        with self.assertRaisesRegex(
            ModelInputTrainingParentError,
            "MODEL_INPUT_TRAINING_PARENT_MISMATCH:route_decision_sha256",
        ):
            self.require(consumed, inference, training_parent=forged_parent)

    def test_stored_binding_bytes_cannot_be_mutated_without_detection(self):
        consumed, binding, _observation_sha, _store_admission, inference = self.seed_full_parent()
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
            self.require(consumed, inference)


if __name__ == "__main__":
    unittest.main()
