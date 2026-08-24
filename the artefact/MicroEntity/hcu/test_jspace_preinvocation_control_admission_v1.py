import hashlib
import sqlite3
import unittest

from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from jspace_preinvocation_control_admission_v1 import (
    ADMISSION_SCHEMA,
    JSpacePreInvocationControlAdmissionError,
    admit_preinvocation_control,
)
from test_grid10_scheduler_v1 import capacity, compile, model_decision, packet


BASIS_SHA256 = "1" * 64


class JSpacePreInvocationControlAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        self.db.commit()

        p = packet()
        d = model_decision(p)
        c = capacity()
        self.plan = compile(p, d, c)
        self.model_cell = next(cell for cell in self.plan.cells if cell.function.startswith("MODEL:"))
        self.role = self.model_cell.function.split(":", 1)[1]

    def tearDown(self):
        self.db.close()

    def vector_packet(self, *, control_condition="AMPLIFY", vector=(0.25, -0.5, 1.0)):
        return encode_vector(
            vector,
            basis_id="basis:preinvoke:1",
            basis_sha256=BASIS_SHA256,
            generation=7,
            role=self.role,
            control_condition=control_condition,
        )

    def binding(self, *, control_packet=None, invocation_id="invocation:preinvoke:1", grid_plan_sha256=None):
        control_packet = control_packet or self.vector_packet()
        wire = packet_bytes(control_packet)
        prepared = b'{"system":"entityos-hcu"}\n' + wire + b'\n{"prompt":"solve the same task"}'
        binding = bind_direct_unique_packet_input(
            control_packet,
            prepared,
            generation=7,
            entry_event_sha256=self.plan.entry_event_sha256,
            entry_admission_sha256=self.plan.entry_admission_sha256,
            route_decision_sha256=self.plan.route_decision_sha256,
            grid_plan_sha256=grid_plan_sha256 or self.plan.plan_sha256,
            cell_id=self.model_cell.cell_id,
            role=self.role,
            executor_id="free-api-executor:test:v1",
            invocation_id=invocation_id,
            executor_observed_input_sha256=hashlib.sha256(prepared).hexdigest(),
            executor_observed_input_size=len(prepared),
        )
        return binding, prepared

    def test_control_is_admitted_only_before_model_execution(self):
        binding, prepared = self.binding()
        receipt = admit_preinvocation_control(
            self.db,
            binding,
            prepared,
            self.plan,
            current_generation=7,
        )
        self.assertEqual(receipt.schema, ADMISSION_SCHEMA)
        self.assertTrue(receipt.model_execution_absent_at_admission)
        self.assertEqual(receipt.binding_sha256, binding.binding_sha256)
        self.assertEqual(receipt.vector_control_packet_sha256, binding.vector_control_packet_sha256)
        self.assertEqual(receipt.input_sha256, hashlib.sha256(prepared).hexdigest())
        row = self.db.execute(
            "SELECT admission_sha256 FROM hcu_jspace_preinvocation_control_admissions WHERE invocation_key=?",
            (receipt.invocation_key,),
        ).fetchone()
        self.assertEqual(row, (receipt.admission_sha256,))

    def test_same_preinvocation_replay_is_idempotent(self):
        binding, prepared = self.binding()
        a = admit_preinvocation_control(self.db, binding, prepared, self.plan, current_generation=7)
        b = admit_preinvocation_control(self.db, binding, prepared, self.plan, current_generation=7)
        self.assertEqual(a, b)

    def test_divergent_control_for_same_invocation_fails_closed(self):
        first, prepared_first = self.binding(control_packet=self.vector_packet(vector=(0.25, -0.5, 1.0)))
        admit_preinvocation_control(self.db, first, prepared_first, self.plan, current_generation=7)
        second, prepared_second = self.binding(control_packet=self.vector_packet(vector=(-0.25, 0.5, -1.0)))
        with self.assertRaisesRegex(JSpacePreInvocationControlAdmissionError, "PREINVOCATION_CONTROL_REPLAY_DIVERGENCE"):
            admit_preinvocation_control(self.db, second, prepared_second, self.plan, current_generation=7)

    def test_execution_already_admitted_for_same_invocation_is_rejected(self):
        binding, prepared = self.binding()
        self.db.execute(
            "CREATE TABLE hcu_model_execution_invocations("
            "invocation_binding_key TEXT PRIMARY KEY, executor_id TEXT NOT NULL, "
            "invocation_id TEXT NOT NULL, entity_generation INTEGER NOT NULL, observation_sha256 TEXT NOT NULL)"
        )
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations VALUES(?,?,?,?,?)",
            ("a" * 64, binding.executor_id, binding.invocation_id, 7, "b" * 64),
        )
        self.db.commit()
        with self.assertRaisesRegex(JSpacePreInvocationControlAdmissionError, "MODEL_EXECUTION_ALREADY_ADMITTED_BEFORE_CONTROL"):
            admit_preinvocation_control(self.db, binding, prepared, self.plan, current_generation=7)

    def test_stale_generation_fails_before_admission(self):
        binding, prepared = self.binding()
        with self.assertRaisesRegex(JSpacePreInvocationControlAdmissionError, "STALE_PREINVOCATION_CONTROL_GENERATION"):
            admit_preinvocation_control(self.db, binding, prepared, self.plan, current_generation=8)
        self.assertIsNone(
            self.db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='hcu_jspace_preinvocation_control_admissions'"
            ).fetchone()
        )

    def test_binding_to_wrong_grid_parent_fails_closed(self):
        binding, prepared = self.binding(grid_plan_sha256="e" * 64)
        with self.assertRaisesRegex(JSpacePreInvocationControlAdmissionError, "PREINVOCATION_GRID_PLAN_IDENTITY_MISMATCH"):
            admit_preinvocation_control(self.db, binding, prepared, self.plan, current_generation=7)

    def test_post_binding_input_mutation_fails_before_admission(self):
        binding, prepared = self.binding()
        with self.assertRaisesRegex(Exception, "EXECUTOR_INPUT_SHA256_MISMATCH"):
            admit_preinvocation_control(self.db, binding, prepared + b"!", self.plan, current_generation=7)

    def test_foreign_keys_must_be_enabled_before_transaction(self):
        binding, prepared = self.binding()
        db = sqlite3.connect(":memory:")
        try:
            db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
            db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
            db.commit()
            with self.assertRaisesRegex(JSpacePreInvocationControlAdmissionError, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION"):
                admit_preinvocation_control(db, binding, prepared, self.plan, current_generation=7)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
