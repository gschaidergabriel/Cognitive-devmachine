import unittest
from dataclasses import replace

from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA, DatasetAdmission
from jspace_vector_control_parent_admission_v1 import (
    JSpaceVectorControlParentAdmissionError,
    require_admitted_vector_control_packet_parent,
)
from jspace_vector_control_v1 import encode_vector


def h(ch):
    return ch * 64


BASIS_ID = "basis:test:vector-parent"
BASIS_SHA = h("d")
GENERATION = 7
ROLE = "world"


def packet(*, generation=GENERATION, role=ROLE, control_condition="BASELINE"):
    return encode_vector(
        [0.25, -0.5, 1.0],
        basis_id=BASIS_ID,
        basis_sha256=BASIS_SHA,
        generation=generation,
        role=role,
        control_condition=control_condition,
    )


def admission(parent=None, **overrides):
    parent = parent or packet()
    value = {
        "schema": ADMISSION_SCHEMA,
        "training_trace_sha256": h("a"),
        "transition_trace_sha256": h("b"),
        "prototype_trace_sha256": h("c"),
        "generation": GENERATION,
        "entry_event_sha256": h("1"),
        "entry_admission_sha256": h("2"),
        "route_decision_sha256": h("3"),
        "grid_plan_sha256": h("4"),
        "cell_id": "cell-02",
        "role": ROLE,
        "jspace_basis_id": BASIS_ID,
        "jspace_basis_sha256": BASIS_SHA,
        "vector_control_packet_sha256": parent.packet_sha256,
        "vector_control_condition": "BASELINE",
        "credit_label": "UNKNOWN",
        "outcome_receipt_sha256": None,
    }
    value.update(overrides)
    return DatasetAdmission(**value)


class VectorControlParentAdmissionTests(unittest.TestCase):
    def test_exact_admitted_packet_parent_passes(self):
        parent = packet()
        observed = require_admitted_vector_control_packet_parent(
            admission(parent),
            {parent.packet_sha256: parent},
        )
        self.assertEqual(observed, parent)

    def test_shared_fabricated_sha_without_packet_parent_fails(self):
        forged_sha = h("5")
        with self.assertRaisesRegex(
            JSpaceVectorControlParentAdmissionError,
            "VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED",
        ):
            require_admitted_vector_control_packet_parent(
                admission(vector_control_packet_sha256=forged_sha),
                {},
            )

    def test_registry_key_cannot_launder_different_packet_identity(self):
        parent = packet()
        other = packet(control_condition="LESION")
        with self.assertRaisesRegex(
            JSpaceVectorControlParentAdmissionError,
            "VECTOR_CONTROL_PACKET_PARENT_IDENTITY_MISMATCH",
        ):
            require_admitted_vector_control_packet_parent(
                admission(parent),
                {parent.packet_sha256: other},
            )

    def test_generation_basis_role_and_condition_are_crossbound(self):
        parent = packet()
        cases = [
            (admission(parent, generation=8), "VECTOR_CONTROL_PACKET_GENERATION_MISMATCH"),
            (admission(parent, jspace_basis_id="basis:other"), "VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH"),
            (admission(parent, jspace_basis_sha256=h("e")), "VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH"),
            (admission(parent, role="critic"), "VECTOR_CONTROL_PACKET_ROLE_MISMATCH"),
            (admission(parent, vector_control_condition="LESION"), "VECTOR_CONTROL_PACKET_CONDITION_MISMATCH"),
        ]
        for candidate, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(JSpaceVectorControlParentAdmissionError, code):
                    require_admitted_vector_control_packet_parent(
                        candidate,
                        {parent.packet_sha256: parent},
                    )

    def test_self_consistent_mutated_packet_bytes_do_not_reuse_old_identity(self):
        parent = packet()
        mutated = replace(parent, q8_values=tuple([126] + list(parent.q8_values[1:])))
        with self.assertRaisesRegex(
            JSpaceVectorControlParentAdmissionError,
            "VECTOR_CONTROL_PACKET_PARENT_REJECTED:VECTOR_CONTROL_PACKET_DIGEST_MISMATCH",
        ):
            require_admitted_vector_control_packet_parent(
                admission(parent),
                {parent.packet_sha256: mutated},
            )


if __name__ == "__main__":
    unittest.main()
