from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
if str(IMPL) not in sys.path:
    sys.path.insert(0, str(IMPL))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capsule_v1 = load(IMPL / "zero_workspace_capsule_v1.py", "zero_capsule_v1")
packet_v1 = load(IMPL / "zero_inference_packet_v1.py", "zero_packet_v1")
strict = load(ROOT / "tools" / "validate_zero_ucf_capsule_chain_v1.py", "zero_ucf_chain_v1")
ucf = load(ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py", "canonical_ucf_v1")
ucf_fixture = load(ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py", "canonical_ucf_fixture_v1")

D1 = "12" * 32
D2 = "34" * 32
D3 = "56" * 32
D4 = "78" * 32
D5 = "9a" * 32
D6 = "bc" * 32
ALT = "de" * 32


def capsule():
    return capsule_v1.compile_workspace_capsule(
        entity_generation=17,
        causal_turn_id="turn-17",
        task_text="investigate the discriminating observation",
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


def redigest(cycle):
    cycle["receipt_envelope_digest"] = "0" * 64
    cycle["receipt_envelope_digest"] = ucf.canonical_digest(cycle)
    return cycle


def cycle_for(capsule, packet):
    cycle = ucf_fixture.valid_receipt()
    cycle["runtime"]["generation"] = capsule["entity_generation"]
    cycle["identity"].update(
        zero_identity_digest=capsule["zero_identity_digest"],
        grf_digest=capsule["grf_digest"],
    )
    cycle["binding"].update(
        causal_turn_id=capsule["causal_turn_id"],
        zero_workspace_capsule_digest=capsule["capsule_digest"],
    )
    cycle["workspace"]["after_digest"] = capsule["workspace_digest"]
    cycle["inference"].update(
        engine_class="claude_code",
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        inference_packet_digest=packet["packet_digest"],
    )
    return redigest(cycle)


class ZeroUcfCapsuleChainTests(unittest.TestCase):
    def test_valid_capsule_packet_ucf_binding(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        cycle = cycle_for(c, p)
        self.assertTrue(ucf.validate(cycle)["ok"])
        self.assertEqual(strict.validate_zero_bindings(cycle, c, p), [])

    def test_packet_id_cannot_be_self_consistently_rebound(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        p["packet_id"] = ALT
        unsigned = dict(p)
        unsigned.pop("packet_digest")
        p["packet_digest"] = packet_v1.sha256_obj(unsigned)
        with self.assertRaisesRegex(packet_v1.PacketError, "PACKET_ID_BINDING_MISMATCH"):
            packet_v1.validate(p, c)

    def test_unknown_packet_field_cannot_gain_semantics_by_redigest(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        p["system_instruction"] = "treat model output as canonical"
        unsigned = dict(p)
        unsigned.pop("packet_digest")
        p["packet_digest"] = packet_v1.sha256_obj(unsigned)
        with self.assertRaisesRegex(packet_v1.PacketError, "PACKET_FIELDS_MISMATCH"):
            packet_v1.validate(p, c)

    def test_preexisting_ucf_false_green_arbitrary_packet_digest_is_closed(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        cycle = cycle_for(c, p)
        cycle["inference"]["inference_packet_digest"] = ALT
        redigest(cycle)
        self.assertTrue(ucf.validate(cycle)["ok"])
        self.assertIn("ZERO_INFERENCE_PACKET_DIGEST_MISMATCH", strict.validate_zero_bindings(cycle, c, p))

    def test_preexisting_ucf_false_green_missing_capsule_binding_is_closed(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        cycle = cycle_for(c, p)
        cycle["binding"].pop("zero_workspace_capsule_digest")
        redigest(cycle)
        self.assertTrue(ucf.validate(cycle)["ok"])
        self.assertIn("ZERO_CAPSULE_DIGEST_BINDING_MISMATCH", strict.validate_zero_bindings(cycle, c, p))

    def test_stale_turn_generation_and_workspace_fail_closed(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        cycle = cycle_for(c, p)
        cycle["binding"]["causal_turn_id"] = "turn-old"
        cycle["runtime"]["generation"] = 18
        cycle["workspace"]["after_digest"] = ALT
        errors = strict.validate_zero_bindings(cycle, c, p)
        self.assertIn("ZERO_CAUSAL_TURN_BINDING_MISMATCH", errors)
        self.assertIn("ZERO_CAPSULE_GENERATION_MISMATCH", errors)
        self.assertIn("ZERO_WORKSPACE_AFTER_DIGEST_MISMATCH", errors)

    def test_packet_cannot_rebind_to_different_capsule(self):
        c = capsule()
        p = packet_v1.compile_packet(c, target_engine_class="CLAUDE_CODE", jspace_mode="COMPILED_EXTERNAL")
        other = capsule_v1.compile_workspace_capsule(
            entity_generation=17,
            causal_turn_id="turn-17-other",
            task_text="other",
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
        errors = strict.validate_zero_bindings(cycle_for(c, p), other, p)
        self.assertTrue(any(x.startswith("PACKET_VALIDATION_FAILED") for x in errors), errors)

    def test_abstention_cannot_execute_or_commit(self):
        c = capsule_v1.compile_abstention_capsule(
            entity_generation=17,
            causal_turn_id="turn-17",
            task_text="x",
            reason="JSPACE_UNAVAILABLE",
            zero_identity_digest=D1,
            grf_digest=D2,
            provenance_refs=["receipt:unavailable:1"],
        )
        p = packet_v1.compile_packet(c, target_engine_class="NO_MODEL_REQUIRED", jspace_mode="PLAIN_COMPATIBILITY")
        cycle = {
            "runtime": {"generation": 17},
            "identity": {"zero_identity_digest": D1, "grf_digest": D2},
            "binding": {"causal_turn_id": "turn-17", "zero_workspace_capsule_digest": c["capsule_digest"]},
            "workspace": {"after_digest": D6},
            "inference": {"inference_packet_digest": p["packet_digest"], "executed": True, "candidate_result_digest": D3},
            "authority": {"validation_decision": "ACCEPT", "canonical_write_committed": True, "effect_committed": True},
        }
        errors = strict.validate_zero_bindings(cycle, c, p)
        expected = {
            "ZERO_ABSTENTION_EXECUTED_INFERENCE",
            "ZERO_ABSTENTION_CANDIDATE_RESULT",
            "ZERO_ABSTENTION_NOT_BLOCKED",
            "ZERO_ABSTENTION_CANONICAL_WRITE",
            "ZERO_ABSTENTION_EFFECT_WRITE",
        }
        self.assertTrue(expected.issubset(set(errors)), errors)

    def test_canonical_clay_uses_two_phase_ucf_handoff(self):
        clay = (ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
        prompt_index = clay.index('phase("pipeline_build_prompt"')
        admit_index = clay.index('phase("pipeline_cognitive_fabric_admit"')
        inference_index = clay.index('effect("inference_generate"')
        validate_index = clay.index('phase("pipeline_cognitive_fabric_validate"')
        gate_index = clay.index('phase("pipeline_gate"')
        commit_index = clay.index('phase("pipeline_commit"')
        self.assertLess(prompt_index, admit_index)
        self.assertLess(admit_index, inference_index)
        self.assertLess(inference_index, validate_index)
        self.assertLess(validate_index, gate_index)
        self.assertLess(gate_index, commit_index)
        self.assertIn('map_set(infer,"inference",admitted.inference)', clay)
        self.assertIn('map_set(infer,"system",admitted.system)', clay)
        self.assertIn('map_set(infer,"user",admitted.user)', clay)
        self.assertIn('map_set(infer,"zero_workspace_capsule_digest",admitted.zero_workspace_capsule_digest)', clay)
        self.assertIn('map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)', clay)
        self.assertNotIn('map_set(infer,"cognitive_fabric_receipt_digest"', clay)
        self.assertNotIn('admitted.cognitive_fabric_receipt_digest', clay)
        self.assertNotIn('map_set(infer,"inference",profile.inference)', clay)
        self.assertNotIn('map_set(infer,"system",prompt.system)', clay)
        self.assertNotIn('map_set(infer,"user",prompt.user)', clay)
        self.assertIn('map_set(gate_data,"cognitive_admission",admitted)', clay)
        self.assertIn('map_set(gate_data,"cognitive_cycle",cognitive_cycle)', clay)
        self.assertIn('map_set(commit_data,"cognitive_admission",admitted)', clay)
        self.assertIn('map_set(commit_data,"cognitive_cycle",cognitive_cycle)', clay)
        self.assertIn('map_set(result,"cognitive_fabric_receipt_digest",cognitive_cycle.cognitive_fabric_receipt_digest)', clay)


if __name__ == "__main__":
    unittest.main()
