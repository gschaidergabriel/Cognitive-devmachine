import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


finalize = load("pipeline_cognitive_fabric_finalize_v1", ROOT / "tools" / "pipeline_cognitive_fabric_finalize_v1.py")
ucf = load("validate_unified_cognitive_fabric_receipt_v1", ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py")

D = "a" * 64
E = "b" * 64
F = "c" * 64
G = "d" * 64
H = "e" * 64
I = "5" * 64
J = "1" * 64
K = "2" * 64
L = "3" * 64
M = "4" * 64
N = "6" * 64
O = "7" * 64


def valid_case():
    admission_receipt = {
        "zero_identity_digest": D,
        "grf_digest": E,
        "bundled_manifest_digest": F,
        "local_model_digest": G,
        "tokenizer_digest": H,
        "jspace_profile_digest": I,
        "jacobian_lens_digest": J,
        "workspace_calibration_digest": K,
        "boot_binding_digest": N,
        "workspace_digest": L,
        "adapter_version": "bundled-08b-candidate-v1",
    }
    admitted = {
        "ok": True,
        "schema": "mini-entity-cognitive-fabric-admission/v1",
        "generation": 7,
        "canonical_state_hash": M,
        "packet_hash": O,
        "inference_packet_digest": D,
        "cognitive_fabric_receipt_digest": E,
        "ucf_engine_class": "local_08b",
        "jspace_mode": "LOCAL_OBSERVE_ONLY",
        "admission_receipt": admission_receipt,
    }
    evidence = {
        "schema": ucf.SCHEMA,
        "source": {
            "commit": "86dcc1fec8add7888773aea0425be3931b5a78f9",
            "tree": "f630df18c405bbf5567327e02b0eeb66d3f4e737",
            "dirty": False,
        },
        "runtime": {
            "mini_entity_version": "mini-entity/runtime-candidate",
            "entityos_version": "entityos/runtime-candidate",
        },
        "identity": {"zero_identity_digest": D, "grf_digest": E},
        "bundled_core": {
            "manifest_digest": F,
            "checkpoint_digest": G,
            "tokenizer_digest": H,
            "jspace_profile_digest": I,
            "lens_profile_digest": J,
            "workspace_calibration_digest": K,
        },
        "binding": {
            "zero_identity_digest": D,
            "grf_digest": E,
            "bundled_manifest_digest": F,
            "boot_binding_receipt_digest": N,
        },
        "workspace": {
            "before_digest": L,
            "after_digest": M,
            "gwt_candidates": ["slot:grf"],
            "gwt_winners": ["slot:grf"],
            "jspace_observation_refs": ["j:observed"],
            "thalamus_gate_decisions": ["admit:slot:grf"],
            "epq_ref": "epq:1",
            "hyperposition_ref": "hp:1",
            "claycode_ref": "clay:1",
            "omega_ref": "omega:1",
        },
        "inference": {
            "engine_class": "local_08b",
            "jspace_mode": "LOCAL_OBSERVE_ONLY",
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "jspace_intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
            "adapter_version": "bundled-08b-candidate-v1",
            "capability_profile_digest": H,
            "adapter_contract_digest": I,
            "epistemic_status": "MEASURED_SUPPORTED",
            "adapter_capability_match": True,
            "provider_observability_claim_supported": True,
        },
        "execution": {
            "free_only": True,
            "lane_cost_class": "LOCAL",
            "lane_admitted": True,
            "policy_authority_digest": J,
            "secret_lookup_count": 0,
            "network_touch_count": 0,
        },
        "freshness": {
            "stale_zero_identity": False,
            "stale_bundled_manifest": False,
            "stale_generation": False,
        },
    }
    generated = {
        "ok": True,
        "payload": {"candidate": "bounded"},
        "inference_packet_digest": D,
        "cognitive_fabric_admission_receipt_digest": E,
        "ucf_runtime_evidence": evidence,
    }
    gated = {"ok": True, "payload": {"candidate": "bounded"}}
    committed = {"ok": True, "output_id": "output:1", "generation": 8}
    compiled = {"canonical_state_hash": M, "packet_hash": O}
    prompt = {"system": "guard", "user": "context"}
    return admitted, generated, gated, committed, compiled, prompt


class PostCommitFinalizationTests(unittest.TestCase):
    def call(self, case):
        admitted, generated, gated, committed, compiled, prompt = case
        return finalize.finalize_post_commit(
            admitted=admitted,
            generated=generated,
            gated=gated,
            committed=committed,
            compiled=compiled,
            prompt=prompt,
            validator_module=ucf,
        )

    def test_valid_exact_ancestry_builds_canonical_receipt_after_commit(self):
        result = self.call(valid_case())
        self.assertTrue(result["ok"])
        self.assertEqual(result["committed_generation"], 8)
        self.assertEqual(result["receipt"]["authority"]["canonical_write_committed"], True)
        self.assertEqual(result["receipt"]["inference"]["inference_packet_digest"], D)
        self.assertTrue(ucf.validate(result["receipt"])["ok"])

    def test_preterminal_authority_smuggle_is_rejected(self):
        case = valid_case()
        case[1]["ucf_runtime_evidence"]["authority"] = {
            "validation_decision": "ACCEPT"
        }
        with self.assertRaisesRegex(
            finalize.CognitiveFabricFinalizationError,
            "PRETERMINAL_AUTHORITY_FIELD_FORBIDDEN:authority",
        ):
            self.call(case)

    def test_candidate_result_swap_after_gate_is_rejected(self):
        case = valid_case()
        case[2]["payload"] = {"candidate": "poison"}
        with self.assertRaisesRegex(
            finalize.CognitiveFabricFinalizationError,
            "GATE_CANDIDATE_IDENTITY_DRIFT",
        ):
            self.call(case)

    def test_workspace_ancestry_drift_is_rejected(self):
        case = valid_case()
        case[1]["ucf_runtime_evidence"]["workspace"]["before_digest"] = M
        with self.assertRaisesRegex(
            finalize.CognitiveFabricFinalizationError,
            "UCF_WORKSPACE_BEFORE_DRIFT",
        ):
            self.call(case)

    def test_unknown_epistemic_status_cannot_authorize_committed_write(self):
        case = valid_case()
        case[1]["ucf_runtime_evidence"]["inference"]["epistemic_status"] = "UNKNOWN"
        with self.assertRaisesRegex(ucf.ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            self.call(case)


if __name__ == "__main__":
    unittest.main()
