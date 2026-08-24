import sqlite3
import unittest

import model_input_control_admission_read_v1 as read_module
from model_input_control_admission_read_v1 import (
    ModelInputControlAdmissionReadError,
    require_existing_model_input_control_admission,
)
from model_input_control_binding_v1 import ModelInputControlBinding


class ModelInputControlAdmissionReadSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        self.db.commit()

    def tearDown(self):
        if self.db.in_transaction:
            self.db.rollback()
        self.db.close()

    def binding(self):
        return ModelInputControlBinding(
            schema="HCU_MODEL_INPUT_CONTROL_BINDING/v1",
            canonicalization_schema="RFC8785_JCS/v1",
            transform_schema="HCU_MODEL_INPUT_DIRECT_UNIQUE_PACKET_EMBED/v1",
            generation=7,
            entry_event_sha256="1" * 64,
            entry_admission_sha256="2" * 64,
            route_decision_sha256="3" * 64,
            grid_plan_sha256="4" * 64,
            cell_id="model.0",
            role="critic",
            jspace_basis_id="basis:7",
            jspace_basis_sha256="5" * 64,
            vector_control_abi="JSPACE_VECTOR_CONTROL_ABI/v1",
            vector_control_packet_sha256="6" * 64,
            vector_control_packet_jcs_utf8="{}",
            vector_control_condition="BASELINE",
            executor_id="executor:local-08b",
            invocation_id="invocation:1",
            input_sha256="7" * 64,
            input_size=1,
            packet_offset=0,
            binding_sha256="8" * 64,
        )

    def test_first_canonical_read_is_inside_snapshot_and_failure_releases_it(self):
        observed_in_transaction = []
        before_changes = self.db.total_changes
        original = read_module._current_generation

        def snapshot_probe(db):
            observed_in_transaction.append(db.in_transaction)
            raise ModelInputControlAdmissionReadError("SNAPSHOT_PROBE_STOP")

        read_module._current_generation = snapshot_probe
        try:
            with self.assertRaisesRegex(
                ModelInputControlAdmissionReadError,
                "SNAPSHOT_PROBE_STOP",
            ):
                require_existing_model_input_control_admission(
                    self.db,
                    self.binding(),
                    b"x",
                    None,
                    current_generation=7,
                )
        finally:
            read_module._current_generation = original

        self.assertEqual(observed_in_transaction, [True])
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.db.total_changes, before_changes)

    def test_caller_owned_transaction_still_fails_before_reader_snapshot(self):
        self.db.execute("BEGIN")
        before_changes = self.db.total_changes
        with self.assertRaisesRegex(
            ModelInputControlAdmissionReadError,
            "CALLER_TRANSACTION_FORBIDDEN",
        ):
            require_existing_model_input_control_admission(
                self.db,
                self.binding(),
                b"x",
                None,
                current_generation=7,
            )
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.total_changes, before_changes)
        self.db.rollback()


if __name__ == "__main__":
    unittest.main()
