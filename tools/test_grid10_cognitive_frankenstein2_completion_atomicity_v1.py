#!/usr/bin/env python3
"""Triggerword-4 regression pin for Frankenstein-2 completion atomicity.

This is an explicit NEGATIVE_RESULT test.  It expresses the desired invariant and remains
an expected failure until EffectLifecycleStore.issue_completion_evidence validates all
bound receipts and mints completion_evidence inside one BEGIN IMMEDIATE transaction.

It grants no runtime, effect, completion, Physical-GRID10, HCU, or EntityOS credit.
"""
from __future__ import annotations

import inspect
import unittest

from frankenstein2_effect_lifecycle_v1 import EffectLifecycleStore


class Frankenstein2CompletionAtomicityTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_validation_reads_and_completion_mint_share_one_writer_transaction(self):
        source = inspect.getsource(EffectLifecycleStore.issue_completion_evidence)

        begin = source.find("BEGIN IMMEDIATE")
        first_bound_read = source.find("SELECT decision FROM admission_decisions")
        mint = source.find("INSERT INTO completion_evidence")

        self.assertGreaterEqual(begin, 0)
        self.assertGreaterEqual(first_bound_read, 0)
        self.assertGreaterEqual(mint, 0)

        # Desired invariant: acquire the writer snapshot before the first receipt read,
        # keep that same connection through validation, then mint before COMMIT.
        self.assertLess(begin, first_bound_read)
        self.assertLess(first_bound_read, mint)
        self.assertEqual(source.count("con = self._con()"), 1)


if __name__ == "__main__":
    unittest.main()
