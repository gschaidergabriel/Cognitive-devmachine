#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from validate_unified_cognitive_fabric_receipt_v1 import (
    BOOT_RECEIPT_SCHEMA,
    canonical_json_sha256,
    validate_receipt,
)


def _h(char: str) -> str:
    return char * 64


COMMIT = "a" * 40
TREE = "b" * 40


def valid_boot_receipt() -> dict:
    return {
        "schema": BOOT_RECEIPT_SCHEMA,
        "source": {"main_sha": COMMIT, "tree_sha": TREE, "dirty": False},
        "executor": {
            "host_class": "UBUNTU",
            "host_identity_sha256": _h("0"),
            "kernel": "linux-test",
        },
        "bundled_core": {
            "manifest_version": "v1",
            "engine_id": "bundled-08b",
            "model_family": "Qwen3.5-0.8B",
            "checkpoint_sha256": _h("4"),
            "tokenizer_sha256": _h("5"),
            "runtime_sha256": _h("6"),
            "manifest_sha256": _h("3"),
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": "c" * 40,
            "lens_file_sha256": _h("7"),
            "lens_profile_sha256": _h("8"),
            "fit_corpus_sha256": _h("9"),
            "n_prompts": 100,
            "skip_first_positions": 1,
            "storage_dtype": "fp32",
            "numeric_integrity": {
                "pre_save_all_finite": True,
                "post_load_all_finite": True,
                "max_abs_pre_save": 2.0,
                "max_abs_post_load": 2.0,
            },
            "measurement_policy": {
                "minimum_readout_position": 1,
                "observed_readout_positions": [1, 2],
                "prompt_copy_confound_guard_enabled": True,
            },
        },
        "gwt": {
            "workspace_policy_sha256": _h("9"),
            "calibration_sha256": _h("a"),
            "slot_count": 2,
            "calibration_status": "MEASURED_EXACT_BUNDLE",
        },
        "zero_grf": {
            "zero_identity_sha256": _h("1"),
            "grf_sha256": _h("2"),
            "projection_policy_sha256": _h("b"),
        },
        "claude_adapter": {
            "adapter_version": "claude-code-candidate-v1",
            "capability_profile_sha256": _h("d"),
            "enabled": True,
        },
        "inference": {
            "first_engine_choice": "CLAUDE_CODE",
            "origin_attribution": "boot-test",
            "first_actions": [
                {
                    "action_id": "boot-action-1",
                    "origin": "CLAUDE_CODE",
                    "effect_requested": False,
                }
            ],
        },
        "authority": {
            "miniunifieddb_is_truth_authority": True,
            "claude_result_is_candidate_only": True,
            "jspace_measurement_is_not_truth": True,
            "gwt_workspace_is_not_truth": True,
            "effect_gate_required": True,
        },
        "claims": {"whole_gwt_credit": "ZERO", "whole_product": "IN_PROGRESS"},
    }


def valid_receipt(boot: dict | None = None) -> dict:
    boot = boot or valid_boot_receipt()
    return {
        "receipt_version": "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
        "boot_binding": {
            "schema": BOOT_RECEIPT_SCHEMA,
            "receipt_sha256": canonical_json_sha256(boot),
        },
        "source": {"commit": COMMIT, "tree": TREE, "dirty": False},
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
            "engine_class": "CLAUDE_CODE",
            "jspace_mode": "COMPILED_EXTERNAL",
            "adapter_version": "claude-code-candidate-v1",
            "capability_profile_digest": _h("d"),
            "adapter_contract_digest": _h("e"),
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "inference_packet_digest": _h("f"),
            "candidate_result_digest": _h("0"),
        },
        "validation": {
            "decision": "REJECT_CANDIDATE",
            "reconciliation_digest": _h("1"),
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
        "terminal_result_digest": _h("2"),
    }


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_valid_compiled_external_claude_receipt_is_boot_bound(self) -> None:
        boot = valid_boot_receipt()
        self.assertEqual(validate_receipt(valid_receipt(boot), boot), [])

    def test_missing_boot_evidence_fails_closed(self) -> None:
        boot = valid_boot_receipt()
        self.assertIn("BOOT_RECEIPT_EVIDENCE_REQUIRED", validate_receipt(valid_receipt(boot)))

    def test_boot_digest_mismatch_fails(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["boot_binding"]["receipt_sha256"] = _h("f")
        self.assertIn("BOOT_RECEIPT_DIGEST_MISMATCH", validate_receipt(receipt, boot))

    def test_self_consistent_cycle_cannot_substitute_boot_manifest(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["bundled_core"]["manifest_digest"] = _h("f")
        self.assertIn("BOOT_CORE_MANIFEST_MISMATCH", validate_receipt(receipt, boot))

    def test_self_consistent_cycle_cannot_substitute_zero_identity(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["identity"]["zero_digest"] = _h("f")
        self.assertIn("BOOT_ZERO_IDENTITY_MISMATCH", validate_receipt(receipt, boot))

    def test_dirty_boot_cannot_anchor_clean_cycle(self) -> None:
        boot = valid_boot_receipt()
        boot["source"]["dirty"] = True
        boot["source"]["dirty_diff_sha256"] = _h("f")
        receipt = valid_receipt(boot)
        self.assertIn("BOOT_SOURCE_DIRTY_FOR_CYCLE", validate_receipt(receipt, boot))

    def test_workspace_calibration_must_match_boot(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["fabric"]["workspace_calibration_digest"] = _h("f")
        self.assertIn("BOOT_WORKSPACE_CALIBRATION_MISMATCH", validate_receipt(receipt, boot))

    def test_claude_capability_must_match_boot(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["inference"]["capability_profile_digest"] = _h("f")
        self.assertIn("BOOT_CLAUDE_CAPABILITY_PROFILE_MISMATCH", validate_receipt(receipt, boot))

    def test_full_local_latent_requires_real_activation_access(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["inference"].update(
            engine_class="BUNDLED_08B",
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=False,
            adapter_version="local-08b-v1",
        )
        self.assertIn("FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS", validate_receipt(receipt, boot))

    def test_local_jspace_requires_exact_lens_profile(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["inference"].update(
            engine_class="BUNDLED_08B",
            jspace_mode="LOCAL_OBSERVE_ONLY",
            adapter_version="local-08b-v1",
        )
        receipt["fabric"]["lens_profile_digest"] = None
        self.assertIn("LOCAL_JSPACE_REQUIRES_LENS_PROFILE", validate_receipt(receipt, boot))

    def test_calibrated_local_intervention_can_be_structurally_admitted(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["inference"].update(
            engine_class="BUNDLED_08B",
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=True,
            adapter_version="local-08b-v1",
        )
        receipt["fabric"]["intervention"] = {
            "executed": True,
            "implementation_digest": _h("3"),
            "calibration_digest": _h("4"),
        }
        self.assertEqual(validate_receipt(receipt, boot), [])

    def test_direct_authority_attempt_cannot_be_accepted(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["validation"].update(
            decision="ACCEPT_CANDIDATE",
            candidate_attempted_direct_state_mutation=True,
        )
        self.assertIn("DIRECT_AUTHORITY_ATTEMPT_ACCEPTED", validate_receipt(receipt, boot))

    def test_free_only_network_touch_still_fails(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["execution_policy"]["network_touch_count"] = 1
        self.assertIn("FREE_ONLY_IO_VIOLATION", validate_receipt(receipt, boot))

    def test_gwt_winner_must_have_competed(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["workspace"]["gwt_winners"] = ["ghost"]
        self.assertIn("GWT_WINNER_NOT_CANDIDATE", validate_receipt(receipt, boot))

    def test_stale_generation_cannot_accept_or_commit(self) -> None:
        boot = valid_boot_receipt()
        receipt = valid_receipt(boot)
        receipt["freshness"]["stale_generation"] = True
        receipt["validation"]["decision"] = "ACCEPT_CANDIDATE"
        self.assertIn("STALE_INPUT_ACCEPTED", validate_receipt(receipt, boot))


if __name__ == "__main__":
    unittest.main()
