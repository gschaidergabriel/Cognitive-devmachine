#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from validate_unified_cognitive_fabric_receipt_v1 import (
    canonical_receipt_digest,
    validate_receipt,
)


def _h(char: str) -> str:
    return char * 64


def valid_receipt() -> dict:
    receipt = {
        "receipt_version": "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
        "source": {
            "commit": "d8ff57c2edc4c9eecde99ce1f9b089702d71b1cf",
            "tree": "66a8ba9d0dd88669083dbc1fa1c900a73d6c5ce4",
            "dirty": False,
        },
        "runtime": {
            "entityos_version": "candidate",
            "mini_entity_version": "candidate",
            "entity_generation": 276,
        },
        "identity": {"zero_digest": _h("1"), "grf_digest": _h("2")},
        "bundled_core": {
            "manifest_digest": _h("3"),
            "checkpoint_digest": _h("4"),
            "tokenizer_digest": _h("5"),
            "runtime_digest": _h("6"),
        },
        "fabric": {
            "jspace_profile_digest": _h("7"),
            "lens_profile_digest": _h("8"),
            "workspace_policy_digest": _h("9"),
            "workspace_calibration_digest": _h("a"),
            "intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
        },
        "workspace": {
            "digest_before": _h("b"),
            "digest_after": _h("c"),
            "gwt_candidates": [{"candidate_id": "c1"}],
            "gwt_winners": ["c1"],
            "jspace_observation_refs": ["j1"],
            "thalamus_decisions": ["admit:c1"],
            "epq_refs": ["epq1"],
            "hyperposition_refs": [],
            "claycode_refs": ["cc1"],
            "omega_refs": [],
        },
        "inference": {
            "engine_class": "BUNDLED_08B",
            "executed": True,
            "epistemic_status": "MEASURED_SUPPORTED",
            "jspace_mode": "LOCAL_OBSERVE_ONLY",
            "adapter_version": "bundled-08b-candidate-v1",
            "capability_profile_digest": _h("d"),
            "adapter_contract_digest": _h("e"),
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "inference_packet_digest": _h("f"),
            "candidate_result_digest": _h("0"),
        },
        "validation": {
            "decision": "ACCEPT_CANDIDATE",
            "reconciliation_digest": _h("1"),
            "candidate_attempted_direct_state_mutation": False,
            "candidate_attempted_direct_effect": False,
            "canonical_state_write_committed": False,
            "effect_executed": False,
        },
        "execution_policy": {
            "free_only": True,
            "cost_class": "LOCAL",
            "backend_admitted": True,
            "policy_authority_digest": _h("a"),
            "secret_touch_count": 0,
            "network_touch_count": 0,
        },
        "freshness": {
            "stale_zero_identity": False,
            "stale_bundled_manifest": False,
            "stale_generation": False,
        },
        "terminal_result_digest": _h("2"),
        "receipt_envelope_digest": _h("0"),
    }
    receipt["receipt_envelope_digest"] = canonical_receipt_digest(receipt)
    return receipt


def redigest(receipt: dict) -> dict:
    receipt["receipt_envelope_digest"] = _h("0")
    receipt["receipt_envelope_digest"] = canonical_receipt_digest(receipt)
    return receipt


def blocked_external(receipt: dict, cost_class: str = "SUBSCRIPTION") -> dict:
    receipt["inference"]["engine_class"] = "CLAUDE_CODE"
    receipt["inference"]["jspace_mode"] = "COMPILED_EXTERNAL"
    receipt["inference"]["adapter_version"] = "claude-code-candidate-v1"
    receipt["inference"]["executed"] = False
    receipt["inference"]["epistemic_status"] = "NOT_APPLICABLE"
    receipt["inference"]["candidate_result_digest"] = None
    receipt["validation"]["decision"] = "BLOCKED"
    receipt["execution_policy"]["cost_class"] = cost_class
    receipt["execution_policy"]["backend_admitted"] = False
    return receipt


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_valid_local_observe_receipt(self) -> None:
        self.assertEqual(validate_receipt(valid_receipt()), [])

    def test_valid_compiled_external_claude_receipt_when_upstream_admits_free_lane(self) -> None:
        receipt = valid_receipt()
        receipt["inference"].update(
            engine_class="CLAUDE_CODE",
            jspace_mode="COMPILED_EXTERNAL",
            adapter_version="claude-code-candidate-v1",
            local_activation_access=False,
            external_hidden_state_claimed=False,
        )
        receipt["execution_policy"]["cost_class"] = "FREE"
        receipt["execution_policy"]["network_touch_count"] = 1
        redigest(receipt)
        self.assertEqual(validate_receipt(receipt), [])

    def test_full_local_latent_requires_real_activation_access(self) -> None:
        receipt = valid_receipt()
        receipt["inference"].update(jspace_mode="FULL_LOCAL_LATENT", local_activation_access=False)
        redigest(receipt)
        self.assertIn("FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS", validate_receipt(receipt))

    def test_local_jspace_requires_exact_lens_profile(self) -> None:
        receipt = valid_receipt()
        receipt["fabric"]["lens_profile_digest"] = None
        redigest(receipt)
        self.assertIn("LOCAL_JSPACE_REQUIRES_LENS_PROFILE", validate_receipt(receipt))

    def test_calibrated_local_intervention_can_be_structurally_admitted(self) -> None:
        receipt = valid_receipt()
        receipt["inference"].update(jspace_mode="FULL_LOCAL_LATENT", local_activation_access=True)
        receipt["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": _h("3"),
            "calibration_digest": _h("4"),
        }
        redigest(receipt)
        self.assertEqual(validate_receipt(receipt), [])

    def test_intervention_requires_executed_inference(self) -> None:
        receipt = valid_receipt()
        receipt["inference"].update(
            executed=False,
            epistemic_status="NOT_APPLICABLE",
            candidate_result_digest=None,
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=True,
        )
        receipt["validation"]["decision"] = "BLOCKED"
        receipt["execution_policy"]["backend_admitted"] = False
        receipt["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": _h("3"),
            "calibration_digest": _h("4"),
        }
        redigest(receipt)
        self.assertIn("INTERVENTION_REQUIRES_EXECUTED_INFERENCE", validate_receipt(receipt))

    def test_direct_authority_attempt_cannot_be_accepted(self) -> None:
        receipt = valid_receipt()
        receipt["validation"]["candidate_attempted_direct_state_mutation"] = True
        redigest(receipt)
        self.assertIn("DIRECT_AUTHORITY_ATTEMPT_ACCEPTED", validate_receipt(receipt))

    def test_workspace_stability_does_not_upgrade_refuted_candidate(self) -> None:
        # Regression-only fusion of the already-consumed go intervention:
        # WORKSPACE_STABILITY_TRUTH_CONFUSION_MUTATION.
        baseline = valid_receipt()
        receipt = copy.deepcopy(baseline)
        receipt["inference"]["epistemic_status"] = "REFUTED"
        receipt["validation"]["canonical_state_write_committed"] = True
        self.assertEqual(receipt["workspace"], baseline["workspace"])
        redigest(receipt)
        self.assertIn("UNSUPPORTED_EPISTEMIC_AUTHORITY", validate_receipt(receipt))

    def test_effect_authority_requires_measured_supported_epistemic_status(self) -> None:
        receipt = valid_receipt()
        receipt["inference"]["epistemic_status"] = "UNKNOWN"
        receipt["validation"]["effect_executed"] = True
        redigest(receipt)
        self.assertIn("UNSUPPORTED_EPISTEMIC_AUTHORITY", validate_receipt(receipt))

    def test_nonexecuted_inference_cannot_carry_result_or_epistemic_credit(self) -> None:
        receipt = valid_receipt()
        receipt["inference"]["executed"] = False
        receipt["execution_policy"]["backend_admitted"] = False
        receipt["validation"]["decision"] = "BLOCKED"
        redigest(receipt)
        errors = validate_receipt(receipt)
        self.assertIn("NONEXECUTED_INFERENCE_RESULT_DIGEST_MUST_BE_NULL", errors)
        self.assertIn("NONEXECUTED_INFERENCE_EPISTEMIC_STATUS_MUST_BE_NOT_APPLICABLE", errors)

    def test_free_only_nonfree_backend_is_blocked_before_secret_or_network_touch(self) -> None:
        receipt = blocked_external(valid_receipt())
        redigest(receipt)
        self.assertEqual(validate_receipt(receipt), [])

        receipt = valid_receipt()
        receipt["execution_policy"]["cost_class"] = "SUBSCRIPTION"
        redigest(receipt)
        self.assertIn("FREE_ONLY_NONFREE_BACKEND_ADMITTED", validate_receipt(receipt))

        for field, expected in (
            ("secret_touch_count", "FREE_ONLY_SECRET_TOUCH"),
            ("network_touch_count", "FREE_ONLY_NETWORK_TOUCH"),
        ):
            with self.subTest(field=field):
                receipt = blocked_external(valid_receipt())
                receipt["execution_policy"][field] = 1
                redigest(receipt)
                self.assertIn(expected, validate_receipt(receipt))

    def test_free_only_does_not_forbid_admitted_free_network_by_itself(self) -> None:
        receipt = valid_receipt()
        receipt["execution_policy"]["cost_class"] = "FREE"
        receipt["execution_policy"]["network_touch_count"] = 1
        redigest(receipt)
        self.assertEqual(validate_receipt(receipt), [])

    def test_inference_cannot_execute_without_backend_admission(self) -> None:
        receipt = valid_receipt()
        receipt["execution_policy"]["backend_admitted"] = False
        redigest(receipt)
        self.assertIn("INFERENCE_EXECUTED_WITHOUT_BACKEND_ADMISSION", validate_receipt(receipt))

    def test_stale_generation_blocks_admission_execution_and_acceptance(self) -> None:
        receipt = valid_receipt()
        receipt["freshness"]["stale_generation"] = True
        redigest(receipt)
        self.assertIn("STALE_INPUT_AUTHORITY_OR_EXECUTION", validate_receipt(receipt))

    def test_claude_cannot_claim_private_hidden_state_or_local_jspace(self) -> None:
        receipt = valid_receipt()
        receipt["inference"].update(
            engine_class="CLAUDE_CODE",
            jspace_mode="FULL_LOCAL_LATENT",
            adapter_version="claude-code-candidate-v1",
            local_activation_access=True,
        )
        receipt["execution_policy"]["cost_class"] = "FREE"
        redigest(receipt)
        self.assertIn("CLAUDE_MUST_BE_COMPILED_EXTERNAL", validate_receipt(receipt))

        receipt["inference"].update(
            jspace_mode="COMPILED_EXTERNAL",
            local_activation_access=False,
            external_hidden_state_claimed=True,
        )
        redigest(receipt)
        self.assertIn("CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN", validate_receipt(receipt))

    def test_gwt_winner_must_be_a_candidate(self) -> None:
        receipt = valid_receipt()
        receipt["workspace"]["gwt_winners"] = ["ghost"]
        redigest(receipt)
        self.assertIn("GWT_WINNER_NOT_CANDIDATE", validate_receipt(receipt))

    def test_envelope_digest_detects_post_receipt_mutation(self) -> None:
        receipt = valid_receipt()
        receipt["workspace"]["thalamus_decisions"] = ["tampered"]
        self.assertIn("RECEIPT_ENVELOPE_DIGEST_MISMATCH", validate_receipt(receipt))

    def test_nonfinite_json_is_rejected(self) -> None:
        receipt = valid_receipt()
        receipt["telemetry"] = {"score": float("nan")}
        self.assertTrue(any(error.startswith("NONFINITE_JSON") for error in validate_receipt(receipt)))

    def test_git_sha256_oid_shape_is_admitted(self) -> None:
        receipt = valid_receipt()
        receipt["source"]["commit"] = "a" * 64
        receipt["source"]["tree"] = "b" * 64
        redigest(receipt)
        self.assertEqual(validate_receipt(receipt), [])

    def test_authority_alias_poison_regression_v1(self) -> None:
        """Deterministic adversarial regression; not an unusual-experiment slot claim."""
        base = valid_receipt()
        poisons: dict[str, tuple[dict, str]] = {}

        r = copy.deepcopy(base)
        r["inference"].update(
            engine_class="CLAUDE_CODE",
            jspace_mode="COMPILED_EXTERNAL",
            adapter_version="claude-code-candidate-v1",
            external_hidden_state_claimed=True,
        )
        r["execution_policy"]["cost_class"] = "FREE"
        redigest(r)
        poisons["claude_hidden_state_spoof"] = (r, "CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN")

        r = blocked_external(copy.deepcopy(base))
        r["execution_policy"]["network_touch_count"] = 1
        redigest(r)
        poisons["nonfree_network_touch"] = (r, "FREE_ONLY_NETWORK_TOUCH")

        r = copy.deepcopy(base)
        r["validation"].update(candidate_attempted_direct_effect=True, effect_executed=True)
        redigest(r)
        poisons["candidate_direct_effect"] = (r, "DIRECT_EFFECT_BYPASS")

        r = copy.deepcopy(base)
        r["freshness"]["stale_zero_identity"] = True
        redigest(r)
        poisons["stale_identity_execute"] = (r, "STALE_INPUT_AUTHORITY_OR_EXECUTION")

        r = copy.deepcopy(base)
        r["inference"].update(
            engine_class="CLAUDE_CODE",
            jspace_mode="COMPILED_EXTERNAL",
            adapter_version="claude-code-candidate-v1",
            local_activation_access=False,
        )
        r["execution_policy"]["cost_class"] = "FREE"
        r["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": None,
            "calibration_digest": None,
        }
        redigest(r)
        poisons["external_mode_intervention_spoof"] = (r, "INTERVENTION_REQUIRES_FULL_LOCAL_LATENT")

        r = copy.deepcopy(base)
        r["workspace"]["gwt_winners"] = ["ghost"]
        redigest(r)
        poisons["winner_not_candidate"] = (r, "GWT_WINNER_NOT_CANDIDATE")

        r = copy.deepcopy(base)
        r["source"]["dirty"] = True
        redigest(r)
        poisons["dirty_source_credit"] = (r, "SOURCE_NOT_CLEAN")

        r = copy.deepcopy(base)
        r["validation"].update(decision="REJECT_CANDIDATE", canonical_state_write_committed=True)
        redigest(r)
        poisons["write_after_reject"] = (r, "STATE_WRITE_WITHOUT_ACCEPT")

        self.assertEqual(len(poisons), 8)
        for name, (receipt, expected_error) in poisons.items():
            with self.subTest(poison=name):
                self.assertIn(expected_error, validate_receipt(receipt))


if __name__ == "__main__":
    unittest.main()
