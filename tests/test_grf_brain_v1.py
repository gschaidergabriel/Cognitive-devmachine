import copy
import hashlib
import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
if str(IMPL) not in sys.path:
    sys.path.insert(0, str(IMPL))

import grf_brain_v1 as grf


def d(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def n(node_id, stage, kind, reality, epistemic, claim, **kw):
    return grf.make_node(
        node_id=node_id,
        stage=stage,
        kind=kind,
        reality_class=reality,
        epistemic_status=epistemic,
        claim=claim,
        provenance_refs=kw.pop("provenance_refs", [f"prov:{node_id}"]),
        **kw,
    )


def build_full():
    t = grf.new_trace(
        entity_generation=7,
        causal_turn_id="turn-7",
        question="Does candidate A survive an independent discriminator?",
        authority_digest=d("authority"),
        source_state_digest=d("state"),
        negative_evidence_refs=["negative:legacy"],
        not_promoted=["whole-system", "effect-authority", "training"],
    )
    t = grf.append_node(t, n(
        "r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE",
        "Current exact receipt reports baseline state.", evidence_refs=["receipt:r0"]
    ))
    t = grf.append_node(t, n(
        "r1", "R1_INFERRED", "HYPOTHESIS", "INFERRED", "CANDIDATE",
        "Candidate A may explain the observed transition.", depends_on=["r0"]
    ))
    t = grf.append_node(t, n(
        "r2", "R2_GENERATED", "POSSIBLE_WORLD", "HYPOTHETICAL", "CANDIDATE",
        "If A is causal, intervention X should preserve response Y.", depends_on=["r1"]
    ))
    t = grf.append_node(t, n(
        "r3", "R3_COUNTER_REALITY", "COUNTERHYPOTHESIS", "HYPOTHETICAL", "CANDIDATE",
        "Harness artifact B could produce the same apparent response.", depends_on=["r0", "r2"]
    ))
    t = grf.append_node(t, n(
        "r4", "R4_DISCRIMINATED", "DISCRIMINATOR", "INTERVENTIONAL", "SUPPORTED",
        "Run exact matched intervention with independent readback.", depends_on=["r2", "r3"],
        evidence_refs=["test:matched-ab"], interventions=["set:X"], causal_assumptions=["stable-subject"]
    ))
    t = grf.append_node(t, n(
        "r5", "R5_EMERGENT", "SYNTHESIS", "INFERRED", "SUPPORTED",
        "Matched evidence supports A at bounded component scope.", depends_on=["r4"],
        evidence_refs=["test:matched-ab"]
    ))
    t = grf.append_node(t, n(
        "r6", "R6_VERIFIED", "SCOPE_DECISION", "INFERRED", "VERIFIED",
        "A is accepted only for the tested component transition.", depends_on=["r5"],
        evidence_refs=["receipt:independent-readback"],
        decision_scope="component-transition-A", credit_scope="repository-component-only"
    ))
    return grf.seal_trace(t)


class GRFBrainV1Tests(unittest.TestCase):
    def test_full_trace_seals_and_is_deterministic(self):
        a = build_full()
        b = build_full()
        self.assertEqual(a["grf_digest"], b["grf_digest"])
        out = grf.validate(a, allow_open=False)
        self.assertTrue(out["ok"])
        self.assertEqual(out["runtime_credit"], "ZERO")
        self.assertEqual(out["effect_credit"], "ZERO")

    def test_stage_skip_fails_closed(self):
        t = grf.new_trace(entity_generation=1, causal_turn_id="t", question="q",
                          authority_digest=d("a"), source_state_digest=d("s"))
        t = grf.append_node(t, n("r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=["e"] ))
        r2 = n("r2", "R2_GENERATED", "POSSIBLE_WORLD", "HYPOTHETICAL", "CANDIDATE", "g", depends_on=["r0"])
        with self.assertRaisesRegex(grf.GRFError, "STAGE_SKIP_FORBIDDEN"):
            grf.append_node(t, r2)

    def test_observed_requires_independent_evidence(self):
        with self.assertRaisesRegex(grf.GRFError, "OBSERVED_REQUIRES_EVIDENCE"):
            n("r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=[])

    def test_generated_cannot_masquerade_as_observed(self):
        with self.assertRaisesRegex(grf.GRFError, "GENERATED_CANNOT_BE_OBSERVED"):
            n("r2", "R2_GENERATED", "POSSIBLE_WORLD", "OBSERVED", "CANDIDATE", "bad")

    def test_synthetic_class_cannot_self_verify(self):
        with self.assertRaisesRegex(grf.GRFError, "R4_CANNOT_MINT_VERIFIED"):
            grf.make_node(node_id="x", stage="R4_DISCRIMINATED", kind="DISCRIMINATOR",
                          reality_class="PREDICTED", epistemic_status="VERIFIED", claim="bad",
                          evidence_refs=["e"], provenance_refs=["p"])

    def test_counterfactual_needs_causal_contract(self):
        with self.assertRaisesRegex(grf.GRFError, "COUNTERFACTUAL_FACTUAL_PARENT_REQUIRED"):
            n("cf", "R3_COUNTER_REALITY", "POSSIBLE_WORLD", "COUNTERFACTUAL", "CANDIDATE", "cf")

    def test_counterfactual_with_contract_is_valid(self):
        node = n("cf", "R3_COUNTER_REALITY", "POSSIBLE_WORLD", "COUNTERFACTUAL", "CANDIDATE", "cf",
                 factual_parent="r0", interventions=["do:x"], causal_assumptions=["scm:v1"],
                 shared_factual_context=["fact:1"])
        self.assertEqual(node["reality_class"], "COUNTERFACTUAL")

    def test_r6_requires_external_evidence(self):
        with self.assertRaisesRegex(grf.GRFError, "R6_EXTERNAL_EVIDENCE_REQUIRED"):
            n("r6", "R6_VERIFIED", "SCOPE_DECISION", "INFERRED", "VERIFIED", "v",
              evidence_refs=[], decision_scope="s", credit_scope="c")

    def test_negative_evidence_cannot_be_repainted_positive(self):
        t = build_full()
        bad = copy.deepcopy(t)
        bad["nodes"][-1]["evidence_refs"] = ["negative:legacy"]
        unsigned = dict(bad["nodes"][-1]); unsigned.pop("node_digest")
        bad["nodes"][-1]["node_digest"] = grf.sha256_obj(unsigned)
        unsigned_trace = dict(bad); unsigned_trace.pop("grf_digest")
        bad["grf_digest"] = grf.sha256_obj(unsigned_trace)
        with self.assertRaisesRegex(grf.GRFError, "NEGATIVE_EVIDENCE_CANNOT_BECOME_POSITIVE_BY_REFERENCE"):
            grf.validate(bad, allow_open=False)

    def test_digest_tamper_fails(self):
        t = build_full()
        bad = copy.deepcopy(t)
        bad["nodes"][1]["claim"] = "tampered"
        unsigned_trace = dict(bad); unsigned_trace.pop("grf_digest")
        bad["grf_digest"] = grf.sha256_obj(unsigned_trace)
        with self.assertRaisesRegex(grf.GRFError, "NODE_DIGEST_MISMATCH"):
            grf.validate(bad, allow_open=False)

    def test_node_id_reuse_forbidden(self):
        t = grf.new_trace(entity_generation=1, causal_turn_id="t", question="q",
                          authority_digest=d("a"), source_state_digest=d("s"))
        r0 = n("same", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=["e"])
        t = grf.append_node(t, r0)
        r0b = n("same", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o2", evidence_refs=["e2"])
        with self.assertRaisesRegex(grf.GRFError, "NODE_ID_REUSE_FORBIDDEN"):
            grf.append_node(t, r0b)

    def test_authority_escalation_fails(self):
        t = grf.new_trace(entity_generation=1, causal_turn_id="t", question="q",
                          authority_digest=d("a"), source_state_digest=d("s"))
        bad = copy.deepcopy(t)
        bad["authority"]["direct_effect_authority"] = True
        with self.assertRaisesRegex(grf.GRFError, "AUTHORITY_ESCALATION"):
            grf.validate(bad, allow_open=True)

    def test_open_trace_cannot_claim_digest(self):
        t = grf.new_trace(entity_generation=1, causal_turn_id="t", question="q",
                          authority_digest=d("a"), source_state_digest=d("s"))
        t["grf_digest"] = d("fake")
        with self.assertRaisesRegex(grf.GRFError, "OPEN_TRACE_CANNOT_HAVE_GRF_DIGEST"):
            grf.validate(t, allow_open=True)

    def test_seal_requires_all_stages(self):
        t = grf.new_trace(entity_generation=1, causal_turn_id="t", question="q",
                          authority_digest=d("a"), source_state_digest=d("s"))
        t = grf.append_node(t, n("r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=["e"] ))
        with self.assertRaisesRegex(grf.GRFError, "SEALED_TRACE_REQUIRES_ALL_R0_R6"):
            grf.seal_trace(t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
