from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_emergent_preprocessor import PossibilitySpec
from research_entity.runtime.eap_dependency_provenance_guard_v16 import (
    ProvenanceGuardedEmergentAssemblyPreprocessor,
)


def make(evidence_class: str) -> StateLedger:
    ledger = StateLedger()
    ledger.append_event(
        event_id="nodes", idem="nodes", base_epoch=0, event_type="SEED", writer="test",
        provenance={"evidence_class":"VERIFIED"}, source={"fixture":"u16-receipt"},
        ops=[
            {"op":"SET","domain":"semantic","key":"a","value":{},"epistemic":"KNOWN","status":"CURRENT"},
            {"op":"SET","domain":"semantic","key":"b","value":{},"epistemic":"KNOWN","status":"CURRENT"},
        ],
    )
    ledger.append_event(
        event_id="edge", idem="edge", base_epoch=ledger.epoch,
        event_type="EDGE", writer="test",
        provenance={"evidence_class":evidence_class}, source={"fixture":"u16-receipt"},
        ops=[{
            "op":"SET","domain":"dependency","key":"e",
            "value":{"source":"semantic:a","target":"semantic:b","strength":1.0},
            "epistemic":"KNOWN","status":"CURRENT",
        }],
    )
    return ledger


class U16ReceiptBindingTests(unittest.TestCase):
    def compile(self, evidence_class: str):
        ledger = make(evidence_class)
        try:
            pp = ProvenanceGuardedEmergentAssemblyPreprocessor(ledger)
            out = pp.compile_active_assembly(
                PossibilitySpec("q", seed_refs=("semantic:a",), max_items=2, max_hops=1, basis_epoch=ledger.epoch)
            )
            manifest = pp.edge_proof_manifest()
            return out, manifest
        finally:
            ledger.close()

    def test_same_semantic_state_different_admitted_provenance_changes_guard_receipt(self):
        verified, vmanifest = self.compile("VERIFIED")
        authoritative, amanifest = self.compile("AUTHORITATIVE")
        self.assertEqual(verified["semantic_state_hash"], authoritative["semantic_state_hash"])
        self.assertEqual(verified["selection_hash"], authoritative["selection_hash"])
        self.assertNotEqual(
            verified["edge_provenance_receipt_hash"],
            authoritative["edge_provenance_receipt_hash"],
        )
        self.assertNotEqual(vmanifest["manifest_hash"], amanifest["manifest_hash"])
        self.assertEqual(vmanifest["decisions"][0]["evidence_class"], "VERIFIED")
        self.assertEqual(amanifest["decisions"][0]["evidence_class"], "AUTHORITATIVE")

    def test_untrusted_provenance_changes_both_decision_and_selection(self):
        verified, _ = self.compile("VERIFIED")
        inferred, imanifest = self.compile("MODEL_INFERRED")
        self.assertEqual([x["ref"] for x in verified["selected"]], ["semantic:a", "semantic:b"])
        self.assertEqual([x["ref"] for x in inferred["selected"]], ["semantic:a"])
        self.assertNotEqual(verified["edge_provenance_receipt_hash"], inferred["edge_provenance_receipt_hash"])
        self.assertEqual(imanifest["decisions"][0]["reason"], "EVIDENCE_CLASS_UNTRUSTED")


if __name__ == "__main__":
    unittest.main()
