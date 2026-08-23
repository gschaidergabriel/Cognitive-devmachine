import unittest

from global_jspace_gwt_v1 import (
    CellContribution,
    JSpaceError,
    lesion,
    step,
)
from jspace_vector_control_v1 import (
    JSpaceVectorControlError,
    decode_vector,
    parse_packet_text,
)

BASIS_ID = "basis:test:42"
BASIS_SHA256 = "a" * 64
ALT_BASIS_SHA256 = "b" * 64


class GlobalJSpaceGWTTests(unittest.TestCase):
    def cells(self):
        return [
            CellContribution("world.0", "world", (0.9, 0.2, -0.1), 0.8, 0.2, 0.3, 0.2, 0.1, 1.0),
            CellContribution("critic.0", "critic", (-0.4, 0.7, 0.4), 0.3, 0.95, 0.7, 0.1, 0.2, 1.0),
            CellContribution("goal.0", "goal", (0.1, 0.1, 0.8), 0.2, 0.1, 0.2, 0.8, 0.2, 0.9),
        ]

    def run_step(self, cells=None, *, generation=11, basis_sha256=BASIS_SHA256):
        return step(
            self.cells() if cells is None else cells,
            generation=generation,
            basis_id=BASIS_ID,
            basis_sha256=basis_sha256,
        )

    def test_step_is_deterministic_and_packet_roundtrips(self):
        a = self.run_step()
        b = self.run_step()
        self.assertEqual(a.trace_sha256, b.trace_sha256)
        self.assertEqual(a.control_packet_text, b.control_packet_text)
        parsed = parse_packet_text(a.control_packet_text)
        decoded = decode_vector(
            parsed,
            current_generation=11,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=a.winner_role,
        )
        self.assertEqual(len(decoded), 3)
        for observed, expected in zip(decoded, a.global_vector):
            self.assertLessEqual(abs(observed - expected), 1 / 127 + 1e-12)

    def test_contradiction_can_win_gwt_without_minting_truth(self):
        result = self.run_step()
        self.assertEqual(result.winner_cell_id, "critic.0")
        self.assertEqual(result.trace["authority"], "CANDIDATE_MEASUREMENT_ONLY_NOT_TRUTH_OR_EFFECT")

    def test_hyperposition_keeps_near_gate_alternatives(self):
        cells = [
            CellContribution("a", "hypothesis", (0.2, 0.2), 0.8, 0.2, 0.5, 0.2, 0.2),
            CellContribution("b", "critic", (-0.2, 0.4), 0.75, 0.25, 0.5, 0.2, 0.2),
        ]
        result = self.run_step(cells, generation=2)
        self.assertEqual(set(result.hyperposition_cells), {"a", "b"})

    def test_out_of_coalition_cells_cannot_reverse_role_broadcast(self):
        winner = CellContribution("winner", "world", (1.0,), 0.9, 0.9, 0.9, 0.9, 0.9, 0.9)
        losers = [
            CellContribution(f"loser.{index}", "critic", (-1.0,), 0.8, 0.8, 0.8, 0.8, 0.8, 0.8)
            for index in range(6)
        ]
        result = self.run_step([winner, *losers], generation=3)
        self.assertEqual(result.winner_cell_id, "winner")
        self.assertEqual(result.hyperposition_cells, ("winner",))
        self.assertEqual(result.trace["broadcast_contributor_cells"], ["winner"])
        self.assertGreater(result.global_vector[0], 0.99)
        self.assertEqual(len(result.trace["contributions"]), 7)

    def test_wrong_dimension_and_duplicate_cell_fail_closed(self):
        cells = self.cells()
        bad = cells + [CellContribution("bad", "world", (0.1, 0.2), 0, 0, 0, 0, 0)]
        with self.assertRaisesRegex(JSpaceError, "VECTOR_DIMENSION_MISMATCH"):
            self.run_step(bad, generation=1)
        with self.assertRaisesRegex(JSpaceError, "CELL_ID_DUPLICATE"):
            self.run_step([cells[0], cells[0]], generation=1)

    def test_packet_rejects_wrong_basis_role_generation(self):
        result = self.run_step()
        common = dict(
            packet=result.control_packet,
            current_generation=11,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=result.winner_role,
        )
        cases = [
            ({"expected_basis_id": "basis:test:99"}, "JSPACE_BASIS_ID_MISMATCH"),
            ({"expected_basis_sha256": ALT_BASIS_SHA256}, "JSPACE_BASIS_SHA256_MISMATCH"),
            ({"expected_role": "simulation"}, "JSPACE_ROLE_MISMATCH"),
            ({"current_generation": 12}, "STALE_VECTOR_CONTROL_GENERATION"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(JSpaceVectorControlError, code):
                    decode_vector(**{**common, **overrides})

    def test_lesion_changes_causal_field_and_can_change_winner(self):
        baseline = self.run_step()
        lesioned = lesion(
            self.cells(),
            lesion_cell_id="critic.0",
            generation=11,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
        )
        self.assertNotEqual(baseline.trace_sha256, lesioned.trace_sha256)
        self.assertNotEqual(baseline.control_packet_text, lesioned.control_packet_text)
        self.assertNotEqual(baseline.winner_cell_id, lesioned.winner_cell_id)

    def test_same_basis_id_different_basis_bytes_do_not_alias(self):
        """Unusual discriminator: basis labels cannot hide different admitted basis bytes."""
        baseline = self.run_step(basis_sha256=BASIS_SHA256)
        substituted = self.run_step(basis_sha256=ALT_BASIS_SHA256)
        self.assertEqual(baseline.basis_id, substituted.basis_id)
        self.assertNotEqual(baseline.control_packet_sha256, substituted.control_packet_sha256)
        self.assertNotEqual(baseline.trace_sha256, substituted.trace_sha256)
        with self.assertRaisesRegex(JSpaceVectorControlError, "JSPACE_BASIS_SHA256_MISMATCH"):
            decode_vector(
                baseline.control_packet,
                current_generation=11,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=ALT_BASIS_SHA256,
                expected_role=baseline.winner_role,
            )


if __name__ == "__main__":
    unittest.main()
