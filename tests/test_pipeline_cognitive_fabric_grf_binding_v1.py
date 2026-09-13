import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
for path in (TOOLS, IMPL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import grf_brain_v1 as grf
import grf_zero_binding_v1 as grf_binding
import pipeline_cognitive_fabric_grf_binding_v1 as sut


def h(label):
    return hashlib.sha256(label.encode()).hexdigest()


def node(node_id, stage, kind, reality, epistemic, claim, **kw):
    return grf.make_node(
        node_id=node_id, stage=stage, kind=kind, reality_class=reality,
        epistemic_status=epistemic, claim=claim, provenance_refs=[f"prov:{node_id}"], **kw,
    )


def trace():
    t = grf.new_trace(entity_generation=7, causal_turn_id="turn-1", question="measure first",
                      authority_digest=h("authority"), source_state_digest=h("state"))
    t = grf.append_node(t, node("r0", "R0_OBSERVED", "OBSERVATION", "OBSERVED", "EVIDENCE", "o", evidence_refs=["e0"]))
    t = grf.append_node(t, node("r1", "R1_INFERRED", "HYPOTHESIS", "INFERRED", "CANDIDATE", "h", depends_on=["r0"]))
    t = grf.append_node(t, node("r2", "R2_GENERATED", "POSSIBLE_WORLD", "HYPOTHETICAL", "CANDIDATE", "g", depends_on=["r1"]))
    t = grf.append_node(t, node("r3", "R3_COUNTER_REALITY", "COUNTERHYPOTHESIS", "HYPOTHETICAL", "CANDIDATE", "c", depends_on=["r2"]))
    t = grf.append_node(t, node("r4", "R4_DISCRIMINATED", "DISCRIMINATOR", "INTERVENTIONAL", "SUPPORTED", "d", depends_on=["r3"], evidence_refs=["e4"], interventions=["do:x"]))
    t = grf.append_node(t, node("r5", "R5_EMERGENT", "SYNTHESIS", "INFERRED", "SUPPORTED", "s", depends_on=["r4"], evidence_refs=["e5"]))
    t = grf.append_node(t, node("r6", "R6_VERIFIED", "SCOPE_DECISION", "INFERRED", "VERIFIED", "v", depends_on=["r5"], evidence_refs=["e6"], decision_scope="component", credit_scope="component-only"))
    return grf.seal_trace(t)


class Active:
    calls = 0
    grf_digest = None

    @classmethod
    def resolve_active_prepare(cls, db, *, entity_generation, expected_activation_digest=None):
        cls.calls += 1
        return {
            "ok": True,
            "entity_generation": entity_generation,
            "causal_turn_id": "turn-1",
            "task_text": "measure first",
            "task_sha256": h("measure first"),
            "activation_digest": h("activation"),
            "turn_binding_digest": h("turn-binding"),
            "boot_binding_digest": h("boot-binding"),
            "grf_digest": cls.grf_digest,
        }


class Compositor:
    frozen_calls = 0

    @classmethod
    def build_pre_inference_admission(cls, db, **kw):
        prepare = kw["active_turn_module"].resolve_active_prepare(
            db,
            entity_generation=kw["entity_generation"],
            expected_activation_digest=kw.get("expected_activation_digest"),
        )
        cls.frozen_calls += 1
        receipt = {
            "authority": "CANDIDATE_INFERENCE_ONLY",
            "real_effect_executed": False,
            "grf_digest": prepare["grf_digest"],
        }
        return {
            "ok": True,
            "schema": sut.ADMISSION_SCHEMA,
            "generation": prepare["entity_generation"],
            "causal_turn_id": prepare["causal_turn_id"],
            "turn_binding_digest": prepare["turn_binding_digest"],
            "boot_binding_digest": prepare["boot_binding_digest"],
            "admission_receipt": receipt,
        }


class GRFPipelineBindingTests(unittest.TestCase):
    def setUp(self):
        Active.calls = 0
        Compositor.frozen_calls = 0

    def call(self, current_trace=None, **overrides):
        current_trace = current_trace or trace()
        Active.grf_digest = current_trace["grf_digest"]
        args = dict(
            db=object(),
            entity_generation=7,
            grf_trace=current_trace,
            invocation={"x": 1},
            compiled={"x": 1},
            prompt={"x": 1},
            profile={"x": 1},
            expected_activation_digest=h("activation"),
            active_turn_module=Active,
            compositor_module=Compositor,
            grf_binding_module=grf_binding,
        )
        args.update(overrides)
        return sut.build_grf_bound_pre_inference_admission(**args)

    def test_binds_once_then_delegates_frozen_prepare(self):
        out = self.call()
        self.assertEqual(Active.calls, 1)
        self.assertEqual(Compositor.frozen_calls, 1)
        self.assertEqual(out["admission_receipt"]["authority"], "CANDIDATE_INFERENCE_ONLY")
        self.assertEqual(out["grf_binding_receipt"]["effect_credit"], "ZERO")
        self.assertEqual(out["grf_binding_version"], sut.BINDING_VERSION)

    def test_grf_prepare_digest_mismatch_fails_before_compositor(self):
        t = trace()
        Active.grf_digest = h("wrong")
        with self.assertRaisesRegex(sut.CognitiveFabricGRFBindingError, "GRF_PREPARE_BINDING_FAILED"):
            sut.build_grf_bound_pre_inference_admission(
                object(), entity_generation=7, grf_trace=t,
                invocation={"x": 1}, compiled={"x": 1}, prompt={"x": 1}, profile={"x": 1},
                expected_activation_digest=h("activation"), active_turn_module=Active,
                compositor_module=Compositor, grf_binding_module=grf_binding,
            )
        self.assertEqual(Compositor.frozen_calls, 0)

    def test_canonical_result_grf_drift_fails_closed(self):
        class BadCompositor(Compositor):
            @classmethod
            def build_pre_inference_admission(cls, db, **kw):
                out = super().build_pre_inference_admission(db, **kw)
                out["admission_receipt"] = dict(out["admission_receipt"])
                out["admission_receipt"]["grf_digest"] = h("drift")
                return out

        with self.assertRaisesRegex(sut.CognitiveFabricGRFBindingError, "ADMISSION_GRF_DIGEST_DRIFT"):
            self.call(compositor_module=BadCompositor)

    def test_canonical_authority_escalation_fails_closed(self):
        class BadCompositor(Compositor):
            @classmethod
            def build_pre_inference_admission(cls, db, **kw):
                out = super().build_pre_inference_admission(db, **kw)
                out["admission_receipt"] = dict(out["admission_receipt"])
                out["admission_receipt"]["authority"] = "TRUTH_AUTHORITY"
                return out

        with self.assertRaisesRegex(sut.CognitiveFabricGRFBindingError, "ADMISSION_AUTHORITY_ESCALATION"):
            self.call(compositor_module=BadCompositor)

    def test_activation_drift_inside_frozen_prepare_fails(self):
        with self.assertRaisesRegex(sut.CognitiveFabricGRFBindingError, "FROZEN_PREPARE_ACTIVATION_DRIFT"):
            self.call(expected_activation_digest=h("wrong-activation"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
