import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "causal",
    ROOT / "tools" / "validate_jspace_gwt_causal_discriminator_receipt_v1.py",
)
causal = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(causal)

D = "1" * 64
E = "2" * 64
F = "3" * 64
G = "4" * 64
H = "5" * 64
I = "6" * 64
J = "7" * 64
K = "8" * 64
L = "9" * 64
A = "a" * 64
B = "b" * 64
C = "c" * 64


def _arm(name, kind, intervention_digest, result_digest):
    return {
        "run_id": f"run:{name}",
        "entity_generation": 276,
        "input_digest": F,
        "decoding_config_digest": G,
        "engine_identity_digest": H,
        "intervention_kind": kind,
        "intervention_digest": intervention_digest,
        "workspace_projection_digest": I,
        "candidate_result_digest": result_digest,
        "behavior_measurement_digest": J,
        "telemetry_digest": K,
        "executed": True,
        "hidden_state_access": True,
        "provider_hidden_state_claimed": False,
    }


def valid_local_receipt():
    receipt = {
        "schema": causal.SCHEMA,
        "source": {
            "commit": "86dcc1fec8add7888773aea0425be3931b5a78f9",
            "tree": "f630df18c405bbf5567327e02b0eeb66d3f4e737",
            "dirty": False,
        },
        "runtime": {
            "entity_generation": 276,
            "runtime_identity_digest": D,
            "bundled_manifest_digest": E,
            "boot_binding_receipt_digest": A,
            "jspace_profile_digest": B,
            "lens_artifact_digest": C,
            "workspace_calibration_digest": L,
        },
        "identity": {
            "zero_identity_digest": D,
            "grf_digest": E,
            "workspace_policy_digest": A,
        },
        "experiment": {
            "mode": "LOCAL_LATENT",
            "metric": "TASK_SCORE_DELTA",
            "task_digest": B,
            "input_digest": F,
            "decoding_config_digest": G,
            "engine_identity_digest": H,
            "inference_packet_digest": C,
            "local_activation_access": True,
            "external_hidden_state_claimed": False,
            "arms": {
                "baseline": _arm("baseline", "NONE", None, A),
                "target": _arm("target", "JSPACE_TARGET_ABLATION", B, B),
                "control": _arm("control", "MATCHED_NON_JSPACE_ABLATION", C, C),
            },
        },
        "pairing": {
            "same_task": True,
            "same_input": True,
            "same_decoding_config": True,
            "same_engine_identity": True,
            "same_generation": True,
            "only_intervention_differs": True,
            "control_capacity_matched": True,
        },
        "comparison": {
            "target_effect": 0.30,
            "control_effect": 0.08,
            "target_minus_control_margin": 0.22,
            "minimum_margin": 0.10,
            "matched_controls_passed": True,
            "causal_use_claimed": False,
            "causal_use_credit": "ZERO_SINGLE_TRIAL",
            "whole_gwt_credit": "ZERO",
            "whole_product_credit": "ZERO",
        },
        "execution": {
            "free_only": True,
            "lane_cost_class": "LOCAL",
            "lane_admitted": True,
            "secret_lookup_count": 0,
            "network_touch_count": 0,
            "policy_authority_digest": J,
        },
        "receipt_envelope_digest": "0" * 64,
    }
    receipt["receipt_envelope_digest"] = causal.canonical_digest(receipt)
    return receipt


def redigest(receipt):
    receipt["receipt_envelope_digest"] = "0" * 64
    receipt["receipt_envelope_digest"] = causal.canonical_digest(receipt)
    return receipt


class CausalDiscriminatorReceiptTests(unittest.TestCase):
    def test_valid_local_three_arm_receipt_is_bounded_not_promoted(self):
        result = causal.validate(valid_local_receipt())
        self.assertTrue(result["ok"])
        self.assertEqual(result["causal_use_credit"], "ZERO_SINGLE_TRIAL")
        self.assertTrue(result["margin_meets_declared_threshold"])

    def test_single_trial_cannot_claim_causal_use(self):
        r = valid_local_receipt()
        r["comparison"]["causal_use_claimed"] = True
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "SINGLE_DISCRIMINATOR_CANNOT_CLAIM_CAUSAL_USE"):
            causal.validate(r)

    def test_target_requires_matched_non_jspace_control_not_same_intervention(self):
        r = valid_local_receipt()
        r["experiment"]["arms"]["control"]["intervention_digest"] = B
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "TARGET_CONTROL_INTERVENTION_ALIAS"):
            causal.validate(r)

    def test_baseline_cannot_carry_intervention(self):
        r = valid_local_receipt()
        r["experiment"]["arms"]["baseline"]["intervention_digest"] = A
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "BASELINE_INTERVENTION_MUST_BE_NULL"):
            causal.validate(r)

    def test_pairing_mismatch_fails_closed(self):
        r = valid_local_receipt()
        r["experiment"]["arms"]["control"]["input_digest"] = A
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "control:INPUT_MISMATCH"):
            causal.validate(r)

        r = valid_local_receipt()
        r["pairing"]["control_capacity_matched"] = False
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "PAIRING_REQUIRED:control_capacity_matched"):
            causal.validate(r)

    def test_margin_is_recomputed_not_trusted(self):
        r = valid_local_receipt()
        r["comparison"]["target_minus_control_margin"] = 0.30
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "COMPARISON_MARGIN_MISMATCH"):
            causal.validate(r)

    def test_local_latent_requires_hidden_state_access_and_offline_execution(self):
        r = valid_local_receipt()
        r["experiment"]["arms"]["target"]["hidden_state_access"] = False
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "target:LOCAL_LATENT_REQUIRES_HIDDEN_STATE_ACCESS"):
            causal.validate(r)

        r = valid_local_receipt()
        r["execution"]["network_touch_count"] = 1
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "LOCAL_LATENT_DISCRIMINATOR_MUST_BE_OFFLINE"):
            causal.validate(r)

    def test_compiled_external_never_claims_hidden_state_access(self):
        r = valid_local_receipt()
        r["experiment"].update(
            mode="COMPILED_EXTERNAL",
            local_activation_access=False,
            external_hidden_state_claimed=False,
        )
        r["execution"].update(lane_cost_class="FREE", network_touch_count=1)
        r["experiment"]["arms"]["baseline"].update(
            intervention_kind="NONE", hidden_state_access=False
        )
        r["experiment"]["arms"]["target"].update(
            intervention_kind="JSPACE_WORKSPACE_PROJECTION_ABLATION", hidden_state_access=False
        )
        r["experiment"]["arms"]["control"].update(
            intervention_kind="MATCHED_NON_JSPACE_CONTEXT_CONTROL", hidden_state_access=False
        )
        redigest(r)
        self.assertTrue(causal.validate(r)["ok"])

        r["experiment"]["arms"]["target"]["provider_hidden_state_claimed"] = True
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "target:EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN"):
            causal.validate(r)

    def test_free_only_rejects_nonfree_executed_discriminator(self):
        for cost in ("PAID", "SUBSCRIPTION", "UNKNOWN"):
            with self.subTest(cost=cost):
                r = valid_local_receipt()
                r["execution"]["lane_cost_class"] = cost
                redigest(r)
                with self.assertRaisesRegex(causal.ReceiptError, "FREE_ONLY_NONFREE_DISCRIMINATOR_FORBIDDEN"):
                    causal.validate(r)

    def test_result_digest_and_envelope_placeholders_fail_closed(self):
        r = valid_local_receipt()
        r["experiment"]["arms"]["target"]["candidate_result_digest"] = "0" * 64
        redigest(r)
        with self.assertRaisesRegex(causal.ReceiptError, "candidate_result_digest:IDENTITY_PLACEHOLDER"):
            causal.validate(r)

        r = valid_local_receipt()
        r["pairing"]["same_task"] = False
        with self.assertRaisesRegex(causal.ReceiptError, "PAIRING_REQUIRED:same_task"):
            causal.validate(r)

    def test_post_receipt_mutation_is_detected(self):
        r = valid_local_receipt()
        r["runtime"]["runtime_identity_digest"] = "d" * 64
        with self.assertRaisesRegex(causal.ReceiptError, "RECEIPT_ENVELOPE_DIGEST_MISMATCH"):
            causal.validate(r)

    def test_nonfinite_metric_is_rejected(self):
        r = valid_local_receipt()
        r["comparison"]["target_effect"] = float("nan")
        with self.assertRaisesRegex(causal.ReceiptError, "NONFINITE_JSON"):
            causal.validate(r)


if __name__ == "__main__":
    unittest.main()
