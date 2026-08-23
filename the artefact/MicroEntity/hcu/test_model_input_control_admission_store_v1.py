import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

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
from model_input_control_admission_store_v1 import (
    ADMISSION_SCHEMA,
    ModelInputControlAdmissionStoreError,
    admit_model_input_control_binding,
)
from model_input_control_binding_v1 import bind_direct_unique_packet_input


GENERATION = 7
BASIS_SHA256 = "1" * 64


def h(n: int) -> str:
    return f"{n:064x}"


class ModelInputControlAdmissionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "miniunified.db"
        self.db = sqlite3.connect(self.db_path)
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

    def packet(self, **overrides):
        kwargs = dict(
            basis_id="basis:7",
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role="critic",
            control_condition="BASELINE",
        )
        kwargs.update(overrides)
        return encode_vector((0.25, -0.5, 1.0), **kwargs)

    def consumed(self, packet=None):
        packet = packet or self.packet()
        return b'{"system":"hcu"}\n' + packet_bytes(packet) + b'\n{"prompt":"solve"}'

    def binding(self, *, packet=None, consumed=None, **overrides):
        packet = packet or self.packet()
        consumed = consumed if consumed is not None else self.consumed(packet)
        kwargs = dict(
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
        kwargs.update(overrides)
        return bind_direct_unique_packet_input(packet, consumed, **kwargs)

    def observation(self, binding, **overrides):
        value = dict(
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
        value.update(overrides)
        return ModelExecutionObservation(**value)

    def seed_parent(self, observation):
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

    def test_exact_binding_requires_and_persists_admitted_model_execution_parent(self):
        consumed = self.consumed()
        binding = self.binding(consumed=consumed)
        observation_sha = self.seed_parent(self.observation(binding))

        admission = admit_model_input_control_binding(
            self.db,
            binding,
            consumed,
            current_generation=GENERATION,
        )
        self.assertEqual(admission.schema, ADMISSION_SCHEMA)
        self.assertEqual(admission.binding_sha256, binding.binding_sha256)
        self.assertEqual(admission.model_execution_observation_sha256, observation_sha)
        self.assertEqual(admission.input_sha256, binding.input_sha256)
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_model_input_control_bindings").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_model_input_control_invocations").fetchone()[0],
            1,
        )

        replay = admit_model_input_control_binding(
            self.db,
            binding,
            consumed,
            current_generation=GENERATION,
        )
        self.assertEqual(replay, admission)

    def test_missing_model_execution_parent_fails_before_control_rows_are_created(self):
        consumed = self.consumed()
        binding = self.binding(consumed=consumed)
        with self.assertRaisesRegex(
            ModelInputControlAdmissionStoreError,
            "EXACTLY_ONE_ADMITTED_MODEL_EXECUTION_INVOCATION_REQUIRED",
        ):
            admit_model_input_control_binding(
                self.db,
                binding,
                consumed,
                current_generation=GENERATION,
            )
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hcu_model_input_control_bindings'"
            ).fetchone()
        )

    def test_parent_input_identity_mismatch_fails_closed_and_rolls_back(self):
        consumed = self.consumed()
        binding = self.binding(consumed=consumed)
        self.seed_parent(self.observation(binding, input_sha256=h(99)))
        with self.assertRaisesRegex(
            ModelInputControlAdmissionStoreError,
            "MODEL_INPUT_CONTROL_PARENT_MISMATCH:input_sha256",
        ):
            admit_model_input_control_binding(
                self.db,
                binding,
                consumed,
                current_generation=GENERATION,
            )
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hcu_model_input_control_bindings'"
            ).fetchone()
        )

    def test_same_model_invocation_cannot_acquire_divergent_control_binding(self):
        consumed = self.consumed()
        first = self.binding(consumed=consumed)
        self.seed_parent(self.observation(first))
        admit_model_input_control_binding(
            self.db,
            first,
            consumed,
            current_generation=GENERATION,
        )

        second = self.binding(consumed=consumed, entry_event_sha256=h(88))
        with self.assertRaisesRegex(
            ModelInputControlAdmissionStoreError,
            "MODEL_INPUT_CONTROL_INVOCATION_REPLAY_DIVERGENCE",
        ):
            admit_model_input_control_binding(
                self.db,
                second,
                consumed,
                current_generation=GENERATION,
            )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_model_input_control_bindings").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM hcu_model_input_control_invocations").fetchone()[0],
            1,
        )

    def test_stale_generation_fails_before_any_control_write(self):
        consumed = self.consumed()
        binding = self.binding(consumed=consumed)
        self.seed_parent(self.observation(binding))
        with self.assertRaisesRegex(
            ModelInputControlAdmissionStoreError,
            "STALE_MODEL_INPUT_CONTROL_ADMISSION_GENERATION",
        ):
            admit_model_input_control_binding(
                self.db,
                binding,
                consumed,
                current_generation=GENERATION + 1,
            )
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hcu_model_input_control_bindings'"
            ).fetchone()
        )

    def test_semantically_invalid_parent_bytes_cannot_be_laundered_by_valid_hash(self):
        consumed = self.consumed()
        binding = self.binding(consumed=consumed)
        observation = self.observation(binding)
        record = model_execution_observation_record(observation)
        record["evidence_source"] = "CALLER_ASSERTED_EXECUTION"
        raw = canonicalize(record)
        observation_sha = hashlib.sha256(raw).hexdigest()
        invocation_key = model_execution_invocation_binding_key(observation)
        self.db.execute(
            "INSERT INTO hcu_model_execution_observations "
            "(observation_sha256,observation_jcs,entity_generation,executor_id,invocation_id) "
            "VALUES(?,?,?,?,?)",
            (
                observation_sha,
                raw,
                GENERATION,
                binding.executor_id,
                binding.invocation_id,
            ),
        )
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            (
                invocation_key,
                binding.executor_id,
                binding.invocation_id,
                GENERATION,
                observation_sha,
            ),
        )
        self.db.commit()

        with self.assertRaisesRegex(
            ModelInputControlAdmissionStoreError,
            "MODEL_EXECUTION_OBSERVATION_SEMANTIC_REVALIDATION_FAILED",
        ):
            admit_model_input_control_binding(
                self.db,
                binding,
                consumed,
                current_generation=GENERATION,
            )


if __name__ == "__main__":
    unittest.main()
