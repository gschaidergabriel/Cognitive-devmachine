#!/usr/bin/env python3
from __future__ import annotations

import unittest

from claygraph_semantic_head_compile_gate_v16 import SemanticHeadEvidence, decide_semantic_head


class SemanticHeadCompileGateV16Tests(unittest.TestCase):
    @staticmethod
    def measured(reads: float, **overrides):
        values = dict(
            rebuild_cost_us=200754.0,
            strict_query_us=6709.521,
            head_query_us=21.9675,
            expected_reads_before_invalidation=reads,
            strict_current_row_count=38400,
            head_current_row_count=38400,
            full_row_mismatch_count=0,
            ambiguity_count=0,
            safety_factor=1.20,
        )
        values.update(overrides)
        return SemanticHeadEvidence(**values)

    def test_measured_guarded_break_even_is_about_36_reads(self):
        d = decide_semantic_head(self.measured(37))
        self.assertAlmostEqual(d.break_even_reads, 30.0190495672, places=6)
        self.assertAlmostEqual(d.guarded_break_even_reads, 36.0228594807, places=6)
        self.assertEqual(d.mode, 'COMPILE_HEAD')
        self.assertGreater(d.expected_net_savings_us, 0)

    def test_36_reads_stays_online_below_guarded_break_even(self):
        d = decide_semantic_head(self.measured(36))
        self.assertEqual(d.mode, 'ONLINE_STRICT')
        self.assertEqual(d.reason, 'EXPECTED_LIFETIME_BELOW_GUARDED_BREAK_EVEN')

    def test_any_full_row_mismatch_blocks_compile_even_for_large_read_lifetime(self):
        d = decide_semantic_head(self.measured(100000, full_row_mismatch_count=1))
        self.assertEqual(d.mode, 'ONLINE_STRICT')
        self.assertEqual(d.reason, 'STRICT_HEAD_EQUIVALENCE_FAILED')

    def test_row_count_mismatch_blocks_compile(self):
        d = decide_semantic_head(self.measured(100000, head_current_row_count=38399))
        self.assertEqual(d.mode, 'ONLINE_STRICT')
        self.assertEqual(d.reason, 'STRICT_HEAD_EQUIVALENCE_FAILED')

    def test_same_epoch_ambiguity_blocks_compile(self):
        d = decide_semantic_head(self.measured(100000, ambiguity_count=1))
        self.assertEqual(d.mode, 'ONLINE_STRICT')
        self.assertEqual(d.reason, 'AMBIGUOUS_LATEST_VERSION_HEADS')


if __name__ == '__main__':
    unittest.main(verbosity=2)
