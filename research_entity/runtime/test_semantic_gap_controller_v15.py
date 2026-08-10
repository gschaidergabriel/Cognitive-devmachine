from __future__ import annotations

import unittest

from .semantic_gap_controller_v15 import (
    EvidenceItem,
    EvidenceRequirement,
    SufficiencyGapControllerV15,
)


class SemanticGapControllerV15Tests(unittest.TestCase):
    def test_sufficient_compiled_field_never_deepens(self):
        calls = []
        def expand(*args):
            calls.append(args)
            return []
        ctl = SufficiencyGapControllerV15(expand=expand)
        out = ctl.assemble(
            query_id="q1", query_text="need alpha", source_epoch=4, graph_epoch=7,
            initial_items=[EvidenceItem("a", frozenset({"alpha"}))],
            requirements=[EvidenceRequirement("r", required_tags=frozenset({"alpha"}))],
        )
        self.assertTrue(out.initial_sufficient)
        self.assertTrue(out.final_sufficient)
        self.assertFalse(out.deepening_used)
        self.assertEqual(calls, [])

    def test_only_explicit_gap_terms_drive_deepening(self):
        seen = []
        def expand(query, terms, selected, source_epoch, graph_epoch, budget):
            seen.append((query, terms, selected, source_epoch, graph_epoch, budget))
            return [EvidenceItem("b", frozenset({"beta"}))]
        ctl = SufficiencyGapControllerV15(expand=expand, max_rounds=2)
        out = ctl.assemble(
            query_id="q2", query_text="alpha and beta", source_epoch=4, graph_epoch=7,
            initial_items=[EvidenceItem("a", frozenset({"alpha"}))],
            requirements=[
                EvidenceRequirement("ra", required_tags=frozenset({"alpha"})),
                EvidenceRequirement("rb", required_tags=frozenset({"beta"})),
            ],
        )
        self.assertFalse(out.initial_sufficient)
        self.assertTrue(out.final_sufficient)
        self.assertEqual(out.deepening_rounds, 1)
        self.assertEqual(seen[0][1], ("beta", "rb"))

    def test_invalid_provenance_cannot_close_gap(self):
        def expand(*_args):
            return [EvidenceItem("bad", frozenset({"beta"}), provenance_valid=False)]
        ctl = SufficiencyGapControllerV15(expand=expand, max_rounds=1)
        out = ctl.assemble(
            query_id="q3", query_text="beta", source_epoch=1, graph_epoch=1,
            initial_items=[],
            requirements=[EvidenceRequirement("rb", required_tags=frozenset({"beta"}))],
        )
        self.assertFalse(out.final_sufficient)
        self.assertEqual(out.deepening_rounds, 1)

    def test_no_novel_evidence_stops_without_burning_round_budget(self):
        calls = 0
        def expand(*_args):
            nonlocal calls
            calls += 1
            return []
        ctl = SufficiencyGapControllerV15(expand=expand, max_rounds=5)
        out = ctl.assemble(
            query_id="q4", query_text="missing gamma", source_epoch=1, graph_epoch=1,
            initial_items=[],
            requirements=[EvidenceRequirement("rg", required_tags=frozenset({"gamma"}))],
        )
        self.assertFalse(out.final_sufficient)
        self.assertEqual(out.deepening_rounds, 1)
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
