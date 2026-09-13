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
import grf_zero_binding_v1 as binding


def d(label):
    return hashlib.sha256(label.encode()).hexdigest()


def node(node_id, stage, kind, reality, epistemic, claim, **kw):
    return grf.make_node(
        node_id=node_id,
        stage=stage,
        kind=kind,
        reality_class=reality,
        epistemic_status=epistemic,
        claim=claim,
        provenance_refs=[f"prov:{node_id}"],
        **kw,
    )


def full_trace():
    t = grf.new_trace(entity_generation=9, causal_turn_id="turn-9", question="q",
                      authority_digest=d("authority"), source_state_digest=d("state"))
    t = grf.append_node(t, node("r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=["e0"]))
    t = grf.append_node(t, node("r1", "R1_INFERRED", "HYPOTHESIS", "INFERRED", "CANDIDATE", "h", depends_on=["r0"]))
    t = grf.append_node(t, node("r2", "R2_GENERATED", "POSSIBLE_WORLD", "HYPOTHETICAL", "CANDIDATE", "g", depends_on=["r1"]))
    t = grf.append_node(t, node("r3", "R3_COUNTER_REALITY", "COUNTERHYPOTHESIS", "HYPOTHETICAL", "CANDIDATE", "c", depends_on=["r2"]))
    t = grf.append_node(t, node("r4", "R4_DISCRIMINATED", "DISCRIMINATOR", "INTERVENTIONAL", "SUPPORTED", "d", depends_on=["r3"], evidence_refs=["e4"], interventions=["do:x"]))
    t = grf.append_node(t, node("r5", "R5_EMERGENT", "SYNTHESIS", "INFERRED", "SUPPORTED", "s", depends_on=["r4"], evidence_refs=["e5"]))
    t = grf.append_node(t, node("r6", "R6_VERIFIED", "SCOPE_DECISION", "INFERRED", "VERIFIED", "v", depends_on=["r5"], evidence_refs=["e6"], decision_scope="component", credit_scope="component-only"))
    return grf.seal_trace(t)


def prepare_for(trace):
    return {
        "entity_generation": 9,
        "causal_turn_id": "turn-9",
        "grf_digest": trace["grf_digest"],
        "turn_binding_digest": d("turn-binding"),
        "boot_binding_digest": d("boot-binding"),
    }


class GRFZeroBindingTests(unittest.TestCase):
    def test_sealed_trace_binds_to_prepare(self):
        trace = full_trace()
        receipt = binding.bind_trace_to_prepare(trace, prepare_for(trace))
        self.assertTrue(binding.validate_binding(receipt)["ok"])
        self.assertEqual(receipt["grf_digest"], trace["grf_digest"])
        self.assertEqual(receipt["effect_credit"], "ZERO")

    def test_open_trace_rejected(self):
        trace = grf.new_trace(entity_generation=9, causal_turn_id="turn-9", question="q",
                              authority_digest=d("authority"), source_state_digest=d("state"))
        prepare = {
            "entity_generation": 9,
            "causal_turn_id": "turn-9",
            "grf_digest": d("fake"),
            "turn_binding_digest": d("turn-binding"),
            "boot_binding_digest": d("boot-binding"),
        }
        with self.assertRaisesRegex(binding.GRFZeroBindingError, "GRF_TRACE_INVALID:OPEN_TRACE_NOT_ADMITTED"):
            binding.bind_trace_to_prepare(trace, prepare)

    def test_digest_mismatch_rejected(self):
        trace = full_trace()
        prepare = prepare_for(trace)
        prepare["grf_digest"] = d("other")
        with self.assertRaisesRegex(binding.GRFZeroBindingError, "GRF_DIGEST_NOT_PREPARE_BOUND"):
            binding.bind_trace_to_prepare(trace, prepare)

    def test_generation_mismatch_rejected(self):
        trace = full_trace()
        prepare = prepare_for(trace)
        prepare["entity_generation"] = 10
        with self.assertRaisesRegex(binding.GRFZeroBindingError, "GRF_GENERATION_MISMATCH"):
            binding.bind_trace_to_prepare(trace, prepare)

    def test_turn_mismatch_rejected(self):
        trace = full_trace()
        prepare = prepare_for(trace)
        prepare["causal_turn_id"] = "turn-other"
        with self.assertRaisesRegex(binding.GRFZeroBindingError, "GRF_CAUSAL_TURN_MISMATCH"):
            binding.bind_trace_to_prepare(trace, prepare)

    def test_binding_tamper_rejected(self):
        trace = full_trace()
        receipt = binding.bind_trace_to_prepare(trace, prepare_for(trace))
        bad = copy.deepcopy(receipt)
        bad["effect_credit"] = "ONE"
        with self.assertRaisesRegex(binding.GRFZeroBindingError, "BINDING_EFFECT_CREDIT_FORBIDDEN"):
            binding.validate_binding(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
