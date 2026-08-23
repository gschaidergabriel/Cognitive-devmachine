import copy
import unittest

from pipeline_cognitive_fabric_runtime_bridge_v1 import (
    RuntimeCognitiveFabricBridgeError,
    admit_phase,
)

H = "1" * 64
P = "2" * 64
I = "3" * 64
A = "4" * 64


def phase_payload():
    return {
        "entity_db": "mini.db",
        "source_db": "source.db",
        "profile": {"profile_id": "default", "inference": {"kind": "mock"}},
        "previous": {"generation": 7},
        "data": {
            "compiled": {"canonical_state_hash": H, "packet_hash": P},
            "prompt": {"system": "s", "user": "u"},
            "invocation": {
                "expected_generation": 7,
                "causal_turn_id": "ct1:g7:a2",
                "task_text": "task",
                "turn_binding_digest": "5" * 64,
            },
        },
    }


def admission(**changes):
    result = {
        "ok": True,
        "schema": "mini-entity-cognitive-fabric-admission/v1",
        "generation": 7,
        "canonical_state_hash": H,
        "packet_hash": P,
        "inference_packet_digest": I,
        "cognitive_fabric_receipt_digest": A,
        "inference": {"kind": "mock"},
        "system": "s",
        "user": "u",
        "admission_receipt": {
            "authority": "CANDIDATE_INFERENCE_ONLY",
            "real_effect_executed": False,
        },
    }
    result.update(changes)
    return result


class RuntimeBridgeTests(unittest.TestCase):
    def test_exact_phase_material_is_forwarded_once(self):
        seen = {}

        def compositor(db, **kwargs):
            seen["db"] = db
            seen.update(kwargs)
            return admission()

        marker = object()
        p = phase_payload()
        out = admit_phase(marker, p, compositor=compositor)
        self.assertTrue(out["ok"])
        self.assertIs(seen["db"], marker)
        self.assertEqual(seen["entity_generation"], 7)
        self.assertIs(seen["compiled"], p["data"]["compiled"])
        self.assertIs(seen["prompt"], p["data"]["prompt"])
        self.assertIs(seen["invocation"], p["data"]["invocation"])
        self.assertIs(seen["profile"], p["profile"])
        self.assertEqual(seen["origin"], "ProfilePipelineRuntime")

    def test_missing_canonical_phase_material_fails_closed(self):
        p = phase_payload()
        del p["data"]["invocation"]
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "COGNITION_PHASE_DATA_INCOMPLETE"):
            admit_phase(object(), p, compositor=lambda *_a, **_k: admission())

    def test_returned_generation_drift_fails_closed(self):
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "GENERATION_DRIFT"):
            admit_phase(object(), phase_payload(), compositor=lambda *_a, **_k: admission(generation=8))

    def test_returned_compiled_identity_drift_fails_closed(self):
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "CANONICAL_STATE_DRIFT"):
            admit_phase(
                object(),
                phase_payload(),
                compositor=lambda *_a, **_k: admission(canonical_state_hash="6" * 64),
            )
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "PACKET_DRIFT"):
            admit_phase(
                object(),
                phase_payload(),
                compositor=lambda *_a, **_k: admission(packet_hash="7" * 64),
            )

    def test_candidate_only_authority_is_enforced(self):
        bad = admission()
        bad["admission_receipt"] = {
            "authority": "CANONICAL_TRUTH",
            "real_effect_executed": False,
        }
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "AUTHORITY_ESCALATION"):
            admit_phase(object(), phase_payload(), compositor=lambda *_a, **_k: bad)

    def test_preinference_effect_or_final_receipt_is_forbidden(self):
        bad_effect = admission()
        bad_effect["admission_receipt"] = copy.deepcopy(bad_effect["admission_receipt"])
        bad_effect["admission_receipt"]["real_effect_executed"] = True
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "EFFECT_EXECUTION_FORBIDDEN"):
            admit_phase(object(), phase_payload(), compositor=lambda *_a, **_k: bad_effect)

        bad_final = admission(ucf_runtime_receipt_digest="8" * 64)
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "FINAL_UCF_RECEIPT_FORBIDDEN"):
            admit_phase(object(), phase_payload(), compositor=lambda *_a, **_k: bad_final)

    def test_digest_placeholders_fail_closed(self):
        bad = admission(inference_packet_digest="0" * 64)
        with self.assertRaisesRegex(RuntimeCognitiveFabricBridgeError, "PLACEHOLDER_REJECTED"):
            admit_phase(object(), phase_payload(), compositor=lambda *_a, **_k: bad)


if __name__ == "__main__":
    unittest.main()
