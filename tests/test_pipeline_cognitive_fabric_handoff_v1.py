from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
for path in (ROOT / "tools", IMPL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pipeline_cognitive_fabric_handoff_v1 as handoff
import zero_workspace_capsule_v1 as capsule_v1


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ucf = load(ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py", "ucf_handoff_test")
fixture = load(ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py", "ucf_fixture_handoff_test")

D1 = "12" * 32
D2 = "34" * 32
D3 = "56" * 32
D4 = "78" * 32
D5 = "9a" * 32
D6 = "bc" * 32
TASK = "investigate the discriminating observation"


def workspace_capsule():
    return capsule_v1.compile_workspace_capsule(
        entity_generation=17,
        causal_turn_id="turn-17",
        task_text=TASK,
        zero_identity_digest=D1,
        grf_digest=D2,
        hyperposition_digest=D3,
        local_model_digest=D4,
        jacobian_lens_digest=D5,
        workspace_digest=D6,
        selected_workspace_slots=["slot:falsifier"],
        contradiction_state="UNRESOLVED",
        provenance_refs=["db:evidence:1"],
        required_zero_mode="DISCRIMINATE",
    )


def profile():
    return {
        "inference": {"kind": "mock", "model": "fixture"},
        "cognitive_fabric": {
            "target_engine_class": "CLAUDE_CODE",
            "jspace_mode": "COMPILED_EXTERNAL",
        },
    }


def admission():
    return handoff.admit_pre_inference(
        capsule=workspace_capsule(),
        profile=profile(),
        system="immutable system context",
        user=TASK,
        entity_generation=17,
        causal_turn_id="turn-17",
    )


def redigest(receipt):
    receipt["receipt_envelope_digest"] = "0" * 64
    receipt["receipt_envelope_digest"] = ucf.canonical_digest(receipt)
    return receipt


def cycle_for(admitted, generated, *, canonical_write=False):
    c = admitted["zero_workspace_capsule"]
    p = admitted["inference_packet"]
    cycle = fixture.valid_receipt()
    cycle["runtime"]["generation"] = c["entity_generation"]
    cycle["identity"].update(
        zero_identity_digest=c["zero_identity_digest"],
        grf_digest=c["grf_digest"],
    )
    cycle["binding"].update(
        zero_identity_digest=c["zero_identity_digest"],
        grf_digest=c["grf_digest"],
        causal_turn_id=c["causal_turn_id"],
        zero_workspace_capsule_digest=c["capsule_digest"],
    )
    cycle["workspace"]["after_digest"] = c["workspace_digest"]
    cycle["inference"].update(
        engine_class="claude_code",
        executed=True,
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        adapter_version="claude-code-adapter/v1",
        inference_packet_digest=p["packet_digest"],
        candidate_result_digest=handoff.sha256_obj(generated["payload"]),
        epistemic_status="MEASURED_SUPPORTED",
        candidate_only=True,
        adapter_capability_match=True,
        provider_observability_claim_supported=True,
    )
    cycle["authority"].update(
        validation_decision="ACCEPT",
        canonical_write_committed=canonical_write,
        effect_committed=False,
    )
    cycle["execution"].update(
        free_only=True,
        lane_cost_class="FREE",
        lane_admitted=True,
        secret_lookup_count=0,
    )
    return redigest(cycle)


class PipelineCognitiveFabricHandoffTests(unittest.TestCase):
    def test_pre_inference_admission_has_packet_but_no_runtime_receipt(self):
        admitted = admission()
        self.assertTrue(admitted["ok"])
        self.assertEqual(admitted["target_engine_class"], "CLAUDE_CODE")
        self.assertEqual(admitted["jspace_mode"], "COMPILED_EXTERNAL")
        self.assertEqual(admitted["cognitive_fabric_receipt_digest"], None)
        self.assertEqual(admitted["inference_packet"]["packet_digest"], admitted["inference_packet_digest"])

    def test_stale_generation_fails_before_packet_admission(self):
        with self.assertRaisesRegex(handoff.HandoffError, "CAPSULE_GENERATION_STALE"):
            handoff.admit_pre_inference(
                capsule=workspace_capsule(),
                profile=profile(),
                system="immutable system context",
                user=TASK,
                entity_generation=18,
                causal_turn_id="turn-17",
            )

    def test_abstention_cannot_become_executable_admission(self):
        c = capsule_v1.compile_abstention_capsule(
            entity_generation=17,
            causal_turn_id="turn-17",
            task_text=TASK,
            reason="JSPACE_UNAVAILABLE",
            zero_identity_digest=D1,
            grf_digest=D2,
            provenance_refs=["receipt:unavailable:1"],
        )
        with self.assertRaisesRegex(handoff.HandoffError, "WORKSPACE_ABSTAINED"):
            handoff.admit_pre_inference(
                capsule=c,
                profile=profile(),
                system="immutable system context",
                user=TASK,
                entity_generation=17,
                causal_turn_id="turn-17",
            )

    def test_post_inference_validates_exact_candidate_before_writeback(self):
        admitted = admission()
        generated = {"ok": True, "payload": {"candidate": "bounded"}}
        cycle = cycle_for(admitted, generated)
        result = handoff.validate_post_inference(
            cycle_receipt=cycle,
            admission=admitted,
            generated=generated,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_result_digest"], handoff.sha256_obj(generated["payload"]))
        self.assertFalse(result["canonical_write_committed"])
        self.assertFalse(result["effect_committed"])

    def test_candidate_digest_mismatch_fails_closed(self):
        admitted = admission()
        generated = {"ok": True, "payload": {"candidate": "bounded"}}
        cycle = cycle_for(admitted, generated)
        generated["payload"] = {"candidate": "changed-after-receipt"}
        with self.assertRaisesRegex(handoff.HandoffError, "CANDIDATE_RESULT_DIGEST_MISMATCH"):
            handoff.validate_post_inference(
                cycle_receipt=cycle,
                admission=admitted,
                generated=generated,
            )

    def test_ucf_cycle_cannot_precommit_canonical_write(self):
        admitted = admission()
        generated = {"ok": True, "payload": {"candidate": "bounded"}}
        cycle = cycle_for(admitted, generated, canonical_write=True)
        with self.assertRaisesRegex(handoff.HandoffError, "PREMATURE_CANONICAL_WRITE"):
            handoff.validate_post_inference(
                cycle_receipt=cycle,
                admission=admitted,
                generated=generated,
            )


if __name__ == "__main__":
    unittest.main()
