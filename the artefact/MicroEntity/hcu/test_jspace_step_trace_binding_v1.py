import unittest
from dataclasses import replace

from global_jspace_gwt_v1 import CellContribution, JSpaceError, step


BASIS_SHA256 = "1" * 64


class JSpaceStepTraceBindingTests(unittest.TestCase):
    def prototype(self):
        return step(
            [
                CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
                CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
            ],
            generation=7,
            basis_id="basis:7",
            basis_sha256=BASIS_SHA256,
        )

    def test_top_level_relabels_cannot_reuse_digest_bound_trace(self):
        proto = self.prototype()
        cases = (
            ("winner_cell_id", "forged.cell", "TRACE_STEP_BINDING_MISMATCH:winner_cell_id"),
            ("winner_role", "simulation", "TRACE_STEP_BINDING_MISMATCH:winner_role"),
            ("generation", 8, "TRACE_STEP_BINDING_MISMATCH:generation"),
            ("global_vector", tuple(reversed(proto.global_vector)), "TRACE_STEP_BINDING_MISMATCH:global_vector_q127"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                with self.assertRaisesRegex(JSpaceError, code):
                    replace(proto, **{field: value})

    def test_mutated_trace_cannot_be_reconstructed_as_same_step(self):
        proto = self.prototype()
        proto.trace["winner_role"] = "simulation"
        with self.assertRaisesRegex(JSpaceError, "TRACE_STEP_BINDING_MISMATCH:winner_role"):
            replace(proto)

    def test_wire_hash_relabel_is_rejected(self):
        proto = self.prototype()
        with self.assertRaisesRegex(JSpaceError, "CONTROL_PACKET_WIRE_SHA256_MISMATCH"):
            replace(proto, control_packet_sha256="2" * 64)


if __name__ == "__main__":
    unittest.main()
