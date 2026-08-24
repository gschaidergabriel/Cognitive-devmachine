import hashlib
import sqlite3
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import canonicalize
from jspace_inference_binding_v1 import validate_binding
from model_execution_receipt_v1 import (
    ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
    OBSERVATION_SCHEMA,
    ModelExecutionObservation,
    model_execution_invocation_binding_key,
    model_execution_observation_record,
    model_execution_observation_sha256,
)
from preinvocation_canonical_predecessor_guard_v1 import (
    PreInvocationCanonicalPredecessorError,
    require_canonical_predecessor_execution,
)
from test_jspace_training_control_delivery_gate_v1 import _binding


GENERATION = 19


def _db(*, with_store=True, generation=GENERATION):
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    if with_store:
        db.execute(
            """CREATE TABLE hcu_model_execution_observations(
              observation_sha256 TEXT PRIMARY KEY,
              observation_jcs BLOB NOT NULL,
              entity_generation INTEGER NOT NULL,
              executor_id TEXT NOT NULL,
              invocation_id TEXT NOT NULL
            )"""
        )
        db.execute(
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
    db.commit()
    return db


def _rehash_binding(binding, **changes):
    value = replace(binding, **changes)
    material = asdict(value)
    material.pop("binding_sha256", None)
    value = replace(
        value,
        binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
    )
    validate_binding(value)
    return value


def _observation(binding):
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


def _admit_exact_predecessor(db):
    binding = _binding()
    observation = _observation(binding)
    observation_sha256 = model_execution_observation_sha256(observation)
    binding = _rehash_binding(
        binding,
        model_execution_observation_sha256=observation_sha256,
    )
    observation_jcs = canonicalize(model_execution_observation_record(observation))
    db.execute(
        "INSERT INTO hcu_model_execution_observations "
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
    db.execute(
        "INSERT INTO hcu_model_execution_invocations "
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
    db.commit()
    return binding, observation, observation_sha256


class PreInvocationCanonicalPredecessorGuardTests(unittest.TestCase):
    def test_exact_canonical_predecessor_is_admitted(self):
        db = _db()
        binding, _observation_value, observation_sha256 = _admit_exact_predecessor(db)
        self.assertEqual(
            require_canonical_predecessor_execution(
                db,
                binding,
                current_generation=GENERATION,
            ),
            observation_sha256,
        )

    def test_self_consistent_binding_without_canonical_store_fails_closed(self):
        db = _db(with_store=False)
        with self.assertRaisesRegex(
            PreInvocationCanonicalPredecessorError,
            "PREDECESSOR_MODEL_EXECUTION_STORE_REQUIRED",
        ):
            require_canonical_predecessor_execution(
                db,
                _binding(),
                current_generation=GENERATION,
            )

    def test_self_consistent_binding_without_admitted_observation_fails_closed(self):
        db = _db()
        with self.assertRaisesRegex(
            PreInvocationCanonicalPredecessorError,
            "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_NOT_UNIQUELY_ADMITTED",
        ):
            require_canonical_predecessor_execution(
                db,
                _binding(),
                current_generation=GENERATION,
            )

    def test_binding_cannot_relabel_canonical_predecessor_input(self):
        db = _db()
        binding, _observation_value, _observation_sha256 = _admit_exact_predecessor(db)
        forged = _rehash_binding(binding, input_sha256="c3" * 32)
        with self.assertRaisesRegex(
            PreInvocationCanonicalPredecessorError,
            "PREDECESSOR_MODEL_EXECUTION_BINDING_MISMATCH:input_sha256",
        ):
            require_canonical_predecessor_execution(
                db,
                forged,
                current_generation=GENERATION,
            )

    def test_duplicate_invocation_alias_fails_closed(self):
        db = _db()
        binding, observation, observation_sha256 = _admit_exact_predecessor(db)
        db.execute(
            "INSERT INTO hcu_model_execution_invocations "
            "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
            "VALUES(?,?,?,?,?)",
            (
                "ab" * 32,
                observation.executor_id,
                observation.invocation_id,
                observation.entity_generation,
                observation_sha256,
            ),
        )
        db.commit()
        with self.assertRaisesRegex(
            PreInvocationCanonicalPredecessorError,
            "PREDECESSOR_MODEL_EXECUTION_INVOCATION_NOT_UNIQUELY_ADMITTED",
        ):
            require_canonical_predecessor_execution(
                db,
                binding,
                current_generation=GENERATION,
            )

    def test_generation_change_invalidates_predecessor(self):
        db = _db()
        binding, _observation_value, _observation_sha256 = _admit_exact_predecessor(db)
        db.execute("UPDATE entity_state SET generation=? WHERE id=1", (GENERATION + 1,))
        db.commit()
        with self.assertRaisesRegex(
            PreInvocationCanonicalPredecessorError,
            "STALE_PREDECESSOR_MODEL_EXECUTION_GENERATION",
        ):
            require_canonical_predecessor_execution(
                db,
                binding,
                current_generation=GENERATION,
            )


if __name__ == "__main__":
    unittest.main()
