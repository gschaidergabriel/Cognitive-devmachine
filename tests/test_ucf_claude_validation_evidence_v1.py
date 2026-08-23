import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ucf", ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
)
ucf = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ucf)

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
P = "7" * 64


def redigest(receipt):
    receipt["receipt_envelope_digest"] = "0" * 64
    receipt["receipt_envelope_digest"] = ucf.canonical_digest(receipt)
    return receipt


def claude_accept_receipt():
    receipt = {
        "schema": ucf.SCHEMA,
        "source": {
            "commit": "86dcc1fec8add7888773aea0425be3931b5a78f9",
            "tree": "f630df18c405bbf5567327e02b0eeb66d3f4e737",
            "dirty": False,
        },
        "runtime": {
            "mini_entity_version": "mini-entity/ucf-source-candidate",
            "entityos_version": "entityos/offline-source-candidate",
            "generation": 276,
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
            "boot_binding_receipt_digest": G,
        },
        "workspace": {
            "before_digest": L,
            "after_digest": M,
            "gwt_candidates": ["slot:grf", "slot:hyper"],
            "gwt_winners": ["slot:grf"],
            "jspace_observation_refs": [],
            "thalamus_gate_decisions": ["dispatch:claude"],
            "epq_ref": "epq:1",
            "hyperposition_ref": "hp:1",
            "claycode_ref": "clay:1",
            "omega_ref": "omega:1",
        },
        "inference": {
            "engine_class": "claude_code",
            "executed": True,
            "jspace_mode": "COMPILED_EXTERNAL",
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "jspace_intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
            "adapter_version": "claude-code-adapter/v1",
            "capability_profile_digest": H,
            "adapter_contract_digest": I,
            "inference_packet_digest": D,
            "candidate_result_digest": E,
            "epistemic_status": "MEASURED_SUPPORTED",
            "candidate_only": True,
            "adapter_capability_match": True,
            "provider_observability_claim_supported": True,
        },
        "authority": {
            "candidate_requested_direct_state_mutation": False,
            "candidate_requested_direct_effect_mutation": False,
            "validation_decision": "ACCEPT",
            "canonical_write_committed": True,
            "effect_committed": False,
        },
        "execution": {
            "free_only": False,
            "lane_cost_class": "SUBSCRIPTION",
            "lane_admitted": True,
            "policy_authority_digest": J,
            "secret_lookup_count": 0,
            "network_touch_count": 1,
            "terminal_result_digest": F,
        },
        "freshness": {
            "stale_zero_identity": False,
            "stale_bundled_manifest": False,
            "stale_generation": False,
        },
        "receipt_envelope_digest": "0" * 64,
    }
    return redigest(receipt)


def add_validation_evidence(receipt):
    receipt["authority"]["validation_evidence"] = {
        "schema": ucf.VALIDATION_EVIDENCE_SCHEMA,
        "candidate_result_digest": E,
        "validator_class": "DETERMINISTIC_GATE",
        "validator_identity_digest": N,
        "evidence_receipt_digest": P,
        "decision": "ACCEPT",
    }
    return redigest(receipt)


class ClaudeValidationEvidenceTests(unittest.TestCase):
    def test_claude_accept_without_separate_validation_evidence_fails_closed(self):
        r = claude_accept_receipt()
        with self.assertRaisesRegex(
            ucf.ReceiptError,
            "CLAUDE_ACCEPT_REQUIRES_SEPARATE_VALIDATION_EVIDENCE_BINDING",
        ):
            ucf.validate(r)

    def test_claude_accept_with_bound_validation_evidence_passes(self):
        r = add_validation_evidence(claude_accept_receipt())
        self.assertTrue(ucf.validate(r)["ok"])

    def test_validation_evidence_must_bind_exact_candidate(self):
        r = add_validation_evidence(claude_accept_receipt())
        r["authority"]["validation_evidence"]["candidate_result_digest"] = F
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "VALIDATION_EVIDENCE_SUBJECT_MISMATCH"):
            ucf.validate(r)

    def test_validation_receipt_identity_cannot_alias_candidate_or_adapter(self):
        for alias in (E, I, D):
            with self.subTest(alias=alias[:1]):
                r = add_validation_evidence(claude_accept_receipt())
                r["authority"]["validation_evidence"]["evidence_receipt_digest"] = alias
                redigest(r)
                with self.assertRaisesRegex(
                    ucf.ReceiptError,
                    "VALIDATION_EVIDENCE_RECEIPT_IDENTITY_NOT_SEPARATE",
                ):
                    ucf.validate(r)

    def test_nonaccept_claude_receipt_does_not_require_validation_evidence(self):
        r = claude_accept_receipt()
        r["authority"].update(
            validation_decision="REJECT",
            canonical_write_committed=False,
            effect_committed=False,
        )
        r["inference"]["epistemic_status"] = "REFUTED"
        redigest(r)
        self.assertTrue(ucf.validate(r)["ok"])


if __name__ == "__main__":
    unittest.main()
