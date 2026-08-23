import unittest

from global_jspace_gwt_v1 import (
    CellContribution,
    JSpaceError,
    VectorControlPacket,
    lesion,
    step,
)


class GlobalJSpaceGWTTests(unittest.TestCase):
    def cells(self):
        return [
            CellContribution("world.0", "world", (0.9, 0.2, -0.1), 0.8, 0.2, 0.3, 0.2, 0.1, 1.0),
            CellContribution("critic.0", "critic", (-0.4, 0.7, 0.4), 0.3, 0.95, 0.7, 0.1, 0.2, 1.0),
            CellContribution("goal.0", "goal", (0.1, 0.1, 0.8), 0.2, 0.1, 0.2, 0.8, 0.2, 0.9),
        ]

    def test_step_is_deterministic_and_packet_roundtrips(self):
        a = step(self.cells(), generation=11, basis_id="B42")
        b = step(self.cells(), generation=11, basis_id="B42")
        self.assertEqual(a.trace_sha256, b.trace_sha256)
        self.assertEqual(a.control_packet_text, b.control_packet_text)
        decoded = VectorControlPacket.decode_text(
            a.control_packet_text,
            expected_basis_id="B42",
            expected_role=a.winner_role,
            expected_generation=11,
        )
        self.assertEqual(len(decoded.vector), 3)
        for observed, expected in zip(decoded.vector, a.global_vector):
            self.assertLessEqual(abs(observed - max(-1.0, min(1.0, expected))), 1 / 127 + 1e-12)

    def test_contradiction_can_win_gwt_without_minting_truth(self):
        result = step(self.cells(), generation=11, basis_id="B42")
        self.assertEqual(result.winner_cell_id, "critic.0")
        self.assertEqual(result.trace["authority"], "CANDIDATE_MEASUREMENT_ONLY_NOT_TRUTH_OR_EFFECT")

    def test_hyperposition_keeps_near_gate_alternatives(self):
        cells = [
            CellContribution("a", "hypothesis", (0.2, 0.2), 0.8, 0.2, 0.5, 0.2, 0.2),
            CellContribution("b", "critic", (-0.2, 0.4), 0.75, 0.25, 0.5, 0.2, 0.2),
        ]
        result = step(cells, generation=2, basis_id="B")
        self.assertEqual(set(result.hyperposition_cells), {"a", "b"})

    def test_wrong_dimension_and_duplicate_cell_fail_closed(self):
        cells = self.cells()
        bad = cells + [CellContribution("bad", "world", (0.1, 0.2), 0, 0, 0, 0, 0)]
        with self.assertRaisesRegex(JSpaceError, "VECTOR_DIMENSION_MISMATCH"):
            step(bad, generation=1, basis_id="B")
        with self.assertRaisesRegex(JSpaceError, "CELL_ID_DUPLICATE"):
            step([cells[0], cells[0]], generation=1, basis_id="B")

    def test_packet_rejects_wrong_basis_role_generation(self):
        result = step(self.cells(), generation=11, basis_id="B42")
        for kwargs, code in [
            ({"expected_basis_id": "B99"}, "JCTL_BASIS_MISMATCH"),
            ({"expected_role": "simulation"}, "JCTL_ROLE_MISMATCH"),
            ({"expected_generation": 12}, "JCTL_GENERATION_MISMATCH"),
        ]:
            with self.assertRaisesRegex(JSpaceError, code):
                VectorControlPacket.decode_text(result.control_packet_text, **kwargs)

    def test_lesion_changes_causal_field_and_can_change_winner(self):
        baseline = step(self.cells(), generation=11, basis_id="B42")
        lesioned = lesion(
            self.cells(),
            lesion_cell_id="critic.0",
            generation=11,
            basis_id="B42",
        )
        self.assertNotEqual(baseline.trace_sha256, lesioned.trace_sha256)
        self.assertNotEqual(baseline.control_packet_text, lesioned.control_packet_text)
        self.assertNotEqual(baseline.winner_cell_id, lesioned.winner_cell_id)


if __name__ == "__main__":
    unittest.main()
