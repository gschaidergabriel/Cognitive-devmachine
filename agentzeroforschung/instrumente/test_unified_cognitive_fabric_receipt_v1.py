#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from validate_unified_cognitive_fabric_receipt_v1 import validate_receipt


def _h(char: str) -> str:
    return char * 64


def valid_receipt() -> dict:
    return {
        "receipt_version": "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
        "contract_revision": 2,
        "source": {
            "commit": "7ab0504f7815fe987bd6c4990395d232960aa538",
            "tree": "66a8ba9d0dd88669083dbc1fa1c900a73d6c5ce4",
            "dirty": False,
        },
        "runtime": {
            "entityos_version": "candidate",
            "mini_entity_version": "candidate",
            "entity_generation": 277,
        },
        "identity": {"zero_digest": _h("1"), "grf_digest": _h("2")},
        "bundled_core": {
            "manifest_digest": _h("3"),
            "checkpoint_digest": _h("4"),
            "tokenizer_digest": _h("5"),
            "runtime_digest": _h("6"),
            "exact_bytes_verified": True,
        },
        "fabric": {
            "local_jspace_mode": "LOCAL_OBSERVE_ONLY",
            "local_activation_access": True,
            "jspace_profile_digest": _h("7"),
            "lens_profile_digest": _h("8"),
            "workspace_policy_digest": _h("9"),
            "workspace_calibration_digest": _h("a"),
            "workspace_calibration_status": "MEASURED_EXACT_BUNDLE",
            "intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
        },
        "upstream": {
            "boot_binding_receipt_digest": _h("b"),
            "boot_binding_validated": True,
            "jlens_admission_receipt_digest": _h("c"),
            "jlens_admission_phase": "PASS_BOUNDED_JACOBIAN",
        },
        "workspace": {
            "digest_before": _h("d"),
            "digest_after": _h("e"),
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
            "engine_class": "CLAUDE_CODE",
            "engine_jspace_mode": "COMPILED_EXTERNAL",
            "adapter_version": "claude-code-candidate-v1",
            "capability_profile_digest": _h("f"),
            "adapter_contract_digest": _h("0"),
            "engine_local_activation_access": False,
            "external_hidden_state_claimed": False,
            "inference_packet_digest": _h("1"),
            "candidate_result_digest": _h("2"),
        },
        "validation": {
            "decision": "REJECT_CANDIDATE",
            "reconciliation_digest": _h("3"),
            "candidate_attempted_direct_state_mutation": False,
            "candidate_attempted_direct_effect": False,
            "canonical_state_write_committed": False,
            "effect_executed": False,
        },
        "execution_policy": {
            "free_only": True,
            "secret_touch_count": 0,
            "network_touch_count": 0,
        },
        "freshness": {
            "stale_zero_identity": False,
            "stale_bundled_manifest": False,
            "stale_generation": False,
        },
        "terminal_result_digest": _h("4"),
    }


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_valid_claude_compiled_external_with_local_observe_fabric(self) -> None:
        self.assertEqual(validate_receipt(valid_receipt()), [])

    def test_claude_compiled_external_with_local_full_latent_intervention_is_valid(self) -> None:
        """Regression for rev1 alias bug: engine mode must not control fabric mode."""
        receipt = valid_receipt()
        receipt["fabric"].update(local_jspace_mode="FULL_LOCAL_LATENT")
        receipt["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": _h("5"),
            "calibration_digest": _h("6"),
        }
        self.assertEqual(validate_receipt(receipt), [])

    def test_active_fabric_requires_measured_exact_calibration(self) -> None:
        receipt = valid_receipt()
        receipt["fabric"]["workspace_calibration_status"] = "UNMEASURED_SOURCE_ONLY"
        self.assertIn(
            "ACTIVE_FABRIC_REQUIRES_MEASURED_EXACT_CALIBRATION",
            validate_receipt(receipt),
        )

    def test_active_fabric_requires_boot_and_bounded_jacobian_admission(self) -> None:
        receipt = valid_receipt()
        receipt["upstream"]["boot_binding_validated"] = False
        receipt["upstream"]["jlens_admission_phase"] = "PASS_WEIGHTED_FORWARD_HOOKS"
        errors = validate_receipt(receipt)
        self.assertIn("ACTIVE_FABRIC_REQUIRES_VALIDATED_BOOT_BINDING", errors)
        self.assertIn("ACTIVE_FABRIC_REQUIRES_BOUNDED_JACOBIAN_ADMISSION", errors)

    def test_bundled_engine_must_match_active_local_fabric_mode(self) -> None:
        receipt = valid_receipt()
        receipt["fabric"]["local_jspace_mode"] = "FULL_LOCAL_LATENT"
        receipt["inference"].update(
            engine_class="BUNDLED_08B",
            engine_jspace_mode="LOCAL_OBSERVE_ONLY",
            engine_local_activation_access=True,
        )
        self.assertIn("BUNDLED_ENGINE_FABRIC_MODE_MISMATCH", validate_receipt(receipt))

    def test_fabric_intervention_requires_local_full_latent_not_engine_mode(self) -> None:
        receipt = valid_receipt()
        receipt["fabric"]["local_jspace_mode"] = "LOCAL_OBSERVE_ONLY"
        receipt["inference"].update(
            engine_class="BUNDLED_08B",
            engine_jspace_mode="LOCAL_OBSERVE_ONLY",
            engine_local_activation_access=True,
        )
        receipt["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": _h("7"),
            "calibration_digest": _h("8"),
        }
        self.assertIn(
            "FABRIC_INTERVENTION_REQUIRES_FULL_LOCAL_LATENT",
            validate_receipt(receipt),
        )

    def test_direct_authority_attempt_cannot_be_accepted(self) -> None:
        receipt = valid_receipt()
        receipt["validation"].update(
            decision="ACCEPT_CANDIDATE",
            candidate_attempted_direct_state_mutation=True,
        )
        self.assertIn("DIRECT_AUTHORITY_ATTEMPT_ACCEPTED", validate_receipt(receipt))

    def test_authority_alias_poison_regression_v1(self) -> None:
        """Deterministic adversarial regression; not an unusual-experiment slot claim."""
        base = valid_receipt()
        poisons: dict[str, tuple[dict, str]] = {}

        r = copy.deepcopy(base)
        r["inference"]["external_hidden_state_claimed"] = True
        poisons["claude_hidden_state_spoof"] = (r, "CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN")

        r = copy.deepcopy(base)
        r["execution_policy"]["network_touch_count"] = 1
        poisons["free_only_network_touch"] = (r, "FREE_ONLY_IO_VIOLATION")

        r = copy.deepcopy(base)
        r["validation"].update(
            decision="ACCEPT_CANDIDATE",
            candidate_attempted_direct_effect=True,
            effect_executed=True,
        )
        poisons["candidate_direct_effect"] = (r, "DIRECT_EFFECT_BYPASS")

        r = copy.deepcopy(base)
        r["freshness"]["stale_zero_identity"] = True
        r["validation"]["decision"] = "ACCEPT_CANDIDATE"
        poisons["stale_identity_accept"] = (r, "STALE_INPUT_ACCEPTED")

        r = copy.deepcopy(base)
        r["fabric"]["local_jspace_mode"] = "LOCAL_OBSERVE_ONLY"
        r["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": None,
            "calibration_digest": None,
        }
        poisons["fabric_intervention_without_full_mode"] = (
            r,
            "FABRIC_INTERVENTION_REQUIRES_FULL_LOCAL_LATENT",
        )

        r = copy.deepcopy(base)
        r["workspace"]["gwt_winners"] = ["ghost"]
        poisons["winner_not_candidate"] = (r, "GWT_WINNER_NOT_CANDIDATE")

        r = copy.deepcopy(base)
        r["source"]["dirty"] = True
        poisons["dirty_source_credit"] = (r, "SOURCE_NOT_CLEAN")

        r = copy.deepcopy(base)
        r["validation"].update(decision="REJECT_CANDIDATE", canonical_state_write_committed=True)
        poisons["write_after_reject"] = (r, "STATE_WRITE_WITHOUT_ACCEPT")

        self.assertEqual(len(poisons), 8)
        for name, (receipt, expected_error) in poisons.items():
            with self.subTest(poison=name):
                self.assertIn(expected_error, validate_receipt(receipt))


if __name__ == "__main__":
    unittest.main()
