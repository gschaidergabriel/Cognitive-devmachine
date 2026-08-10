from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)
from research_entity.runtime.eap_query_aware_gate_v17 import (
    IMPLEMENTATION_ID,
    QueryAwareEmergentAssemblyPreprocessor,
    QueryAwarePossibilitySpec,
)


def _fixture(*, conflict_relevant_bridge: bool = False) -> StateLedger:
    ledger = StateLedger()
    ops = [
        {"op": "SET", "domain": "memory", "key": "seed", "value": {"text": "router root"}},
        {
            "op": "SET",
            "domain": "memory",
            "key": "alpha_bridge",
            "value": {"text": "alpha pathway bridge"},
            "epistemic": "CONFLICT" if conflict_relevant_bridge else "KNOWN",
        },
        {"op": "SET", "domain": "memory", "key": "alpha_target", "value": {"text": "alpha target evidence"}},
        {"op": "SET", "domain": "memory", "key": "noise_bridge", "value": {"text": "unrelated noise branch"}},
        {"op": "SET", "domain": "memory", "key": "noise_target", "value": {"text": "unrelated noise target"}},
        {
            "op": "SET",
            "domain": "dependency",
            "key": "seed_alpha",
            "value": {"source": "memory:seed", "target": "memory:alpha_bridge", "strength": 0.90},
        },
        {
            "op": "SET",
            "domain": "dependency",
            "key": "alpha_target",
            "value": {"source": "memory:alpha_bridge", "target": "memory:alpha_target", "strength": 0.90},
        },
        {
            "op": "SET",
            "domain": "dependency",
            "key": "seed_noise",
            "value": {"source": "memory:seed", "target": "memory:noise_bridge", "strength": 0.99},
        },
        {
            "op": "SET",
            "domain": "dependency",
            "key": "noise_target",
            "value": {"source": "memory:noise_bridge", "target": "memory:noise_target", "strength": 0.99},
        },
    ]
    ledger.append_event(
        event_id="fixture",
        idem="fixture",
        base_epoch=ledger.epoch,
        event_type="TEST_FIXTURE",
        writer="test",
        ops=ops,
        provenance={"evidence_class": "TEST_FIXTURE"},
    )
    return ledger


def _base_spec(ledger: StateLedger, *, query: str = "alpha target") -> PossibilitySpec:
    return PossibilitySpec(
        assembly_id="a",
        seed_refs=("memory:seed",),
        query_text=query,
        allowed_domains=("memory",),
        max_items=3,
        max_hops=2,
        frontier_budget=32,
        min_edge_weight=0.30,
        hop_decay=0.88,
        lexical_weight=0.0,
        basis_epoch=ledger.epoch,
    )


def _query_spec(
    ledger: StateLedger,
    *,
    query: str = "alpha target",
    strength: float = 0.85,
    floor: float = 0.10,
) -> QueryAwarePossibilitySpec:
    return QueryAwarePossibilitySpec(
        assembly_id="a",
        seed_refs=("memory:seed",),
        query_text=query,
        allowed_domains=("memory",),
        max_items=3,
        max_hops=2,
        frontier_budget=32,
        min_edge_weight=0.30,
        hop_decay=0.88,
        lexical_weight=0.0,
        basis_epoch=ledger.epoch,
        query_gate_strength=strength,
        query_gate_floor=floor,
    )


class QueryAwareGateV17Tests(unittest.TestCase):
    def test_query_blind_parent_prefers_structurally_stronger_distractor(self):
        ledger = _fixture()
        parent = EmergentAssemblyPreprocessor(ledger).compile_active_assembly(_base_spec(ledger))
        refs = [x["ref"] for x in parent["selected"]]
        self.assertEqual(refs[0], "memory:seed")
        self.assertEqual(refs[1], "memory:noise_bridge")
        self.assertNotIn("memory:alpha_target", refs)

    def test_query_gate_recovers_relevant_two_hop_target_and_prunes_noise(self):
        ledger = _fixture()
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger)
        )
        refs = [x["ref"] for x in candidate["selected"]]
        self.assertEqual(refs, ["memory:seed", "memory:alpha_bridge", "memory:alpha_target"])
        self.assertEqual(candidate["preprocessor_version"], IMPLEMENTATION_ID)
        self.assertTrue(candidate["query_gate"]["enabled"])
        self.assertGreaterEqual(candidate["query_gate"]["edges_damped"], 2)
        self.assertGreaterEqual(candidate["query_gate"]["edges_pruned_below_parent_min"], 1)
        self.assertFalse(candidate["persistent_second_store"])
        self.assertEqual(candidate["authority"], "ASSEMBLY_CONTEXT_ONLY")
        self.assertTrue(all(x["authority"] == "CONTEXT_ONLY" for x in candidate["selected"]))

    def test_zero_strength_is_exact_parent_lesion_for_selection_hash(self):
        ledger = _fixture()
        parent = EmergentAssemblyPreprocessor(ledger).compile_active_assembly(_base_spec(ledger))
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger, strength=0.0)
        )
        self.assertEqual(parent["selection_hash"], candidate["selection_hash"])
        self.assertEqual(parent["compiled_index_hash"], candidate["compiled_index_hash"])
        self.assertEqual(parent["selected"], candidate["selected"])
        self.assertFalse(candidate["query_gate"]["enabled"])
        self.assertEqual(candidate["query_gate"]["reason"], "ZERO_STRENGTH_PARENT_LESION")

    def test_empty_query_is_parent_lesion_even_when_strength_nonzero(self):
        ledger = _fixture()
        parent = EmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _base_spec(ledger, query="")
        )
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger, query="", strength=1.0)
        )
        self.assertEqual(parent["selection_hash"], candidate["selection_hash"])
        self.assertEqual(parent["selected"], candidate["selected"])
        self.assertEqual(candidate["query_gate"]["reason"], "NO_QUERY_TOKENS_PARENT_LESION")

    def test_query_changes_gate_manifest_and_switches_branch(self):
        ledger = _fixture()
        pre = QueryAwareEmergentAssemblyPreprocessor(ledger)
        alpha = pre.compile_active_assembly(_query_spec(ledger, query="alpha target"))
        noise = pre.compile_active_assembly(_query_spec(ledger, query="noise target"))
        self.assertNotEqual(alpha["query_gate_manifest_hash"], noise["query_gate_manifest_hash"])
        self.assertEqual(alpha["selected"][1]["ref"], "memory:alpha_bridge")
        self.assertEqual(noise["selected"][1]["ref"], "memory:noise_bridge")

    def test_epistemic_negative_space_still_blocks_query_relevant_bridge(self):
        ledger = _fixture(conflict_relevant_bridge=True)
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger)
        )
        refs = [x["ref"] for x in candidate["selected"]]
        self.assertNotIn("memory:alpha_target", refs)
        self.assertIn("memory:alpha_bridge", candidate["blocked_propagation_refs"])
        self.assertTrue(any(x["ref"] == "memory:alpha_bridge" for x in candidate["suppressed"]))

    def test_stale_epoch_fails_closed(self):
        ledger = _fixture()
        spec = _query_spec(ledger)
        stale = QueryAwarePossibilitySpec(
            **{
                **{field: getattr(spec, field) for field in spec.__dataclass_fields__},
                "basis_epoch": ledger.epoch - 1,
            }
        )
        with self.assertRaises(StaleEpoch):
            QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(stale)

    def test_gate_parameter_validation(self):
        ledger = _fixture()
        with self.assertRaises(ValueError):
            QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
                _query_spec(ledger, strength=1.01)
            )
        with self.assertRaises(ValueError):
            QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
                _query_spec(ledger, floor=-0.01)
            )


if __name__ == "__main__":
    unittest.main()
