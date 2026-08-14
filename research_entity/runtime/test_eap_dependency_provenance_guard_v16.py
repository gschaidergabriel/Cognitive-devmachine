from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)
from research_entity.runtime.eap_dependency_provenance_guard_v16 import (
    ProvenanceGuardedEmergentAssemblyPreprocessor,
    decide_dependency_proof,
    latest_write_receipts,
)


class EAPDependencyProvenanceGuardV16Tests(unittest.TestCase):
    def make_poisoned(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="nodes",
            idem="nodes",
            base_epoch=ledger.epoch,
            event_type="SEED_NODES",
            writer="test",
            provenance={"evidence_class": "VERIFIED"},
            source={"fixture": "u16"},
            ops=[
                {"op":"SET","domain":"semantic","key":"anchor","value":{"label":"anchor"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"semantic","key":"target","value":{"label":"target"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"semantic","key":"decoy","value":{"label":"decoy"},"epistemic":"KNOWN","status":"CURRENT"},
            ],
        )
        ledger.append_event(
            event_id="good-edge",
            idem="good-edge",
            base_epoch=ledger.epoch,
            event_type="DEPENDENCY_EVIDENCE",
            writer="test",
            provenance={"evidence_class": "VERIFIED"},
            source={"fixture": "u16-good"},
            ops=[{
                "op":"SET","domain":"dependency","key":"good",
                "value":{"source":"semantic:anchor","target":"semantic:target","strength":0.55,"relation_type":"requires"},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        ledger.append_event(
            event_id="poison-edge",
            idem="poison-edge",
            base_epoch=ledger.epoch,
            event_type="MODEL_PROPOSAL",
            writer="adversary",
            provenance={"evidence_class": "MODEL_INFERRED"},
            source={"fixture": "u16-poison"},
            ops=[{
                "op":"SET","domain":"dependency","key":"poison",
                "value":{"source":"semantic:anchor","target":"semantic:decoy","strength":1.0,"relation_type":"requires"},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        return ledger

    def spec(self, ledger):
        return PossibilitySpec(
            assembly_id="u16-probe",
            seed_refs=("semantic:anchor",),
            max_items=2,
            max_hops=1,
            frontier_budget=16,
            basis_epoch=ledger.epoch,
        )

    def test_baseline_eap_reproduces_trusted_but_wrong_dependency_poisoning(self):
        ledger = self.make_poisoned()
        out = EmergentAssemblyPreprocessor(ledger).compile_active_assembly(self.spec(ledger))
        self.assertEqual([x["ref"] for x in out["selected"]], ["semantic:anchor", "semantic:decoy"])
        ledger.close()

    def test_strict_guard_blocks_untrusted_dependency_and_recovers_target(self):
        ledger = self.make_poisoned()
        out = ProvenanceGuardedEmergentAssemblyPreprocessor(ledger).compile_active_assembly(self.spec(ledger))
        self.assertEqual([x["ref"] for x in out["selected"]], ["semantic:anchor", "semantic:target"])
        self.assertIn("dependency:poison", out["blocked_dependency_refs"])
        self.assertEqual(out["edge_proof_audit"]["EVIDENCE_CLASS_UNTRUSTED"], 1)
        self.assertEqual(out["edge_proof_audit"]["ADMITTED"], 1)
        self.assertEqual(out["authority"], "CONTEXT_ONLY")
        ledger.close()

    def test_missing_provenance_fails_closed(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="nodes", idem="nodes", base_epoch=0,
            event_type="SEED", writer="test",
            provenance={"evidence_class":"VERIFIED"},
            ops=[
                {"op":"SET","domain":"semantic","key":"a","value":{},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"semantic","key":"b","value":{},"epistemic":"KNOWN","status":"CURRENT"},
            ],
        )
        ledger.append_event(
            event_id="edge", idem="edge", base_epoch=ledger.epoch,
            event_type="EDGE", writer="test", provenance={},
            ops=[{
                "op":"SET","domain":"dependency","key":"e",
                "value":{"source":"semantic:a","target":"semantic:b","strength":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        pp = ProvenanceGuardedEmergentAssemblyPreprocessor(ledger)
        out = pp.compile_active_assembly(PossibilitySpec(
            "missing", seed_refs=("semantic:a",), max_items=2, max_hops=1,
            basis_epoch=ledger.epoch,
        ))
        self.assertEqual([x["ref"] for x in out["selected"]], ["semantic:a"])
        self.assertEqual(out["edge_proof_audit"]["PROVENANCE_MISSING"], 1)
        ledger.close()

    def test_expired_provenance_fails_closed_at_current_epoch(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="nodes", idem="nodes", base_epoch=0,
            event_type="SEED", writer="test",
            provenance={"evidence_class":"VERIFIED"},
            ops=[
                {"op":"SET","domain":"semantic","key":"a","value":{},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"semantic","key":"b","value":{},"epistemic":"KNOWN","status":"CURRENT"},
            ],
        )
        ledger.append_event(
            event_id="edge", idem="edge", base_epoch=ledger.epoch,
            event_type="EDGE", writer="test",
            provenance={"evidence_class":"VERIFIED", "valid_until_epoch":2},
            ops=[{
                "op":"SET","domain":"dependency","key":"e",
                "value":{"source":"semantic:a","target":"semantic:b","strength":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        ledger.append_event(
            event_id="later", idem="later", base_epoch=ledger.epoch,
            event_type="LATER", writer="test",
            provenance={"evidence_class":"VERIFIED"},
            ops=[{"op":"SET","domain":"semantic","key":"later","value":{},"epistemic":"KNOWN","status":"CURRENT"}],
        )
        out = ProvenanceGuardedEmergentAssemblyPreprocessor(ledger).compile_active_assembly(
            PossibilitySpec("expired", seed_refs=("semantic:a",), max_items=2, max_hops=1, basis_epoch=ledger.epoch)
        )
        self.assertEqual([x["ref"] for x in out["selected"]], ["semantic:a"])
        self.assertEqual(out["edge_proof_audit"]["PROVENANCE_EXPIRED"], 1)
        ledger.close()

    def test_latest_write_receipt_tracks_dependency_writer_event(self):
        ledger = self.make_poisoned()
        receipts = latest_write_receipts(ledger)
        self.assertEqual(receipts["dependency:good"].event_id, "good-edge")
        self.assertEqual(receipts["dependency:good"].event_epoch, 2)
        self.assertEqual(receipts["dependency:poison"].event_epoch, 3)
        ledger.close()

    def test_require_source_is_independent_fail_closed_dimension(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="e", idem="e", base_epoch=0, event_type="EDGE", writer="test",
            provenance={"evidence_class":"VERIFIED"}, source={},
            ops=[{"op":"SET","domain":"dependency","key":"e","value":{},"epistemic":"KNOWN","status":"CURRENT"}],
        )
        receipt = latest_write_receipts(ledger)["dependency:e"]
        decision = decide_dependency_proof("dependency:e", receipt, current_epoch=ledger.epoch, require_source=True)
        self.assertFalse(decision.admitted)
        self.assertEqual(decision.reason, "SOURCE_RECEIPT_MISSING")
        ledger.close()


if __name__ == "__main__":
    unittest.main()
