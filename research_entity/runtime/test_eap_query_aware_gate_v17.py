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

TARGET_ONLY_MODE = "LEXICAL_COSINE_TARGET_RELATION"
LOOKAHEAD_MODE = "LEXICAL_COSINE_TARGET_OR_ADMISSIBLE_SUCCESSOR_V1"
COUNTEREVIDENCE_POLICY = "PRESERVE_EXPLICIT_TYPED_COUNTER_RELATIONS_AT_PARENT_WEIGHT"


def _fixture(
    *,
    conflict_relevant_bridge: bool = False,
    opaque_relevant_bridge: bool = False,
    include_counterevidence: bool = False,
    counterevidence_epistemic: str = "KNOWN",
) -> StateLedger:
    ledger = StateLedger()
    bridge_text = "connector intermediate" if opaque_relevant_bridge else "alpha pathway bridge"
    ops = [
        {"op": "SET", "domain": "memory", "key": "seed", "value": {"text": "router root"}},
        {
            "op": "SET",
            "domain": "memory",
            "key": "alpha_bridge",
            "value": {"text": bridge_text},
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
    if include_counterevidence:
        ops.extend(
            [
                {
                    "op": "SET",
                    "domain": "memory",
                    "key": "refutation",
                    "value": {"text": "orthogonal rebuttal evidence"},
                    "epistemic": counterevidence_epistemic,
                    "status": "CURRENT",
                },
                {
                    "op": "SET",
                    "domain": "dependency",
                    "key": "seed_refutation",
                    "value": {
                        "source": "memory:seed",
                        "target": "memory:refutation",
                        "strength": 0.80,
                        "relation_type": "REFUTES",
                    },
                },
            ]
        )
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
    mode: str = LOOKAHEAD_MODE,
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
        query_gate_mode=mode,
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

    def test_target_only_ablation_fails_opaque_bridge_but_lookahead_recovers_it(self):
        ledger = _fixture(opaque_relevant_bridge=True)
        pre = QueryAwareEmergentAssemblyPreprocessor(ledger)
        target_only = pre.compile_active_assembly(
            _query_spec(ledger, mode=TARGET_ONLY_MODE)
        )
        lookahead = pre.compile_active_assembly(
            _query_spec(ledger, mode=LOOKAHEAD_MODE)
        )
        target_only_refs = [x["ref"] for x in target_only["selected"]]
        lookahead_refs = [x["ref"] for x in lookahead["selected"]]
        self.assertNotIn("memory:alpha_target", target_only_refs)
        self.assertEqual(
            lookahead_refs,
            ["memory:seed", "memory:alpha_bridge", "memory:alpha_target"],
        )
        self.assertEqual(target_only["query_gate"]["lookahead_edges_scanned"], 0)
        self.assertGreater(lookahead["query_gate"]["lookahead_edges_scanned"], 0)
        self.assertGreater(lookahead["query_gate"]["lookahead_affinity_wins"], 0)
        self.assertNotEqual(
            target_only["query_gate_manifest_hash"],
            lookahead["query_gate_manifest_hash"],
        )

    def test_explicit_refuting_edge_is_not_erased_by_query_relevance(self):
        ledger = _fixture(include_counterevidence=True)
        parent = EmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _base_spec(ledger)
        )
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger)
        )
        parent_refute = next(
            item for item in parent["selected"] if item["ref"] == "memory:refutation"
        )
        candidate_refute = next(
            item for item in candidate["selected"] if item["ref"] == "memory:refutation"
        )
        self.assertEqual(candidate_refute["relation_type"], "REFUTES")
        self.assertAlmostEqual(
            candidate_refute["activation_score"], parent_refute["activation_score"], places=12
        )
        self.assertGreaterEqual(candidate["query_gate"]["counterevidence_edges_preserved"], 1)
        self.assertEqual(
            candidate["query_gate"]["counterevidence_policy"], COUNTEREVIDENCE_POLICY
        )

    def test_counterevidence_guard_does_not_bypass_epistemic_negative_space(self):
        ledger = _fixture(
            include_counterevidence=True, counterevidence_epistemic="CONFLICT"
        )
        candidate = QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            _query_spec(ledger)
        )
        selected_refs = [x["ref"] for x in candidate["selected"]]
        self.assertNotIn("memory:refutation", selected_refs)
        self.assertIn("memory:refutation", candidate["blocked_propagation_refs"])
        self.assertTrue(
            any(x["ref"] == "memory:refutation" for x in candidate["suppressed"])
        )
        self.assertGreaterEqual(candidate["query_gate"]["counterevidence_edges_preserved"], 1)

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
        ledger = _fixture(conflict_relevant_bridge=True, opaque_relevant_bridge=True)
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
        with self.assertRaises(ValueError):
            QueryAwareEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
                _query_spec(ledger, mode="UNSUPPORTED")
            )


if __name__ == "__main__":
    unittest.main()
