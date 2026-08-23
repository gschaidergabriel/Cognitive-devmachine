import unittest
from unittest.mock import patch

from jspace_dataset_admission_gate_v1 import JSpaceDatasetAdmissionError
from jspace_vector_control_parent_admission_v1 import (
    JSpaceVectorControlParentAdmissionError,
    require_admitted_vector_control_packet_parent,
)
from test_jspace_vector_control_parent_admission_v1 import admission, packet


class VectorControlParentDelegationTests(unittest.TestCase):
    @patch("jspace_vector_control_parent_admission_v1._verify_vector_control_packet_binding")
    def test_compatibility_guard_delegates_exact_semantics_to_dataset_admission(self, canonical_gate):
        parent = packet()
        candidate = admission(parent)
        registry = {parent.packet_sha256: parent}

        observed = require_admitted_vector_control_packet_parent(candidate, registry)

        self.assertEqual(observed, parent)
        canonical_gate.assert_called_once_with(
            registry,
            packet_sha256=candidate.vector_control_packet_sha256,
            generation=candidate.generation,
            basis_id=candidate.jspace_basis_id,
            basis_sha256=candidate.jspace_basis_sha256,
            role=candidate.role,
            control_condition=candidate.vector_control_condition,
        )

    @patch("jspace_vector_control_parent_admission_v1._verify_vector_control_packet_binding")
    def test_canonical_missing_parent_error_preserves_compatibility_surface(self, canonical_gate):
        parent = packet()
        candidate = admission(parent)
        canonical_gate.side_effect = JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_NOT_ADMITTED")

        with self.assertRaisesRegex(
            JSpaceVectorControlParentAdmissionError,
            "VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED",
        ):
            require_admitted_vector_control_packet_parent(candidate, {})

    @patch("jspace_vector_control_parent_admission_v1._verify_vector_control_packet_binding")
    def test_canonical_packet_rejection_preserves_parent_error_prefix(self, canonical_gate):
        parent = packet()
        candidate = admission(parent)
        canonical_gate.side_effect = JSpaceDatasetAdmissionError(
            "VECTOR_CONTROL_PACKET_REJECTED:VECTOR_CONTROL_PACKET_DIGEST_MISMATCH"
        )

        with self.assertRaisesRegex(
            JSpaceVectorControlParentAdmissionError,
            "VECTOR_CONTROL_PACKET_PARENT_REJECTED:VECTOR_CONTROL_PACKET_DIGEST_MISMATCH",
        ):
            require_admitted_vector_control_packet_parent(candidate, {parent.packet_sha256: parent})


if __name__ == "__main__":
    unittest.main()
