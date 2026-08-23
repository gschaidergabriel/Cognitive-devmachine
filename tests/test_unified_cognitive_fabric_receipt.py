import copy
import unittest

from tools.validate_unified_cognitive_fabric_receipt import ReceiptError, validate_receipt

D40 = "a" * 40
D64A = "a" * 64
D64B = "b" * 64
D64C = "c" * 64
D64D = "d" * 64


def valid_receipt():
    return {
        "schema": "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
        "source": {
            "commit_sha": D40,
            "tree_sha": "b" * 40,
            "dirty": False,
            "executor_identity": "isolated-local-source-validator",
        },
        "entity": {
            "mini_entity_version": "0.7.0-dev1",
            "entityos_version": "source-contract",
            "zero_identity_digest": D64A,
            "grf_digest": D64B,
            "generation": 277,
        },
        "bundled_core": {
            "manifest_digest": D64A,
            "checkpoint_digest": D64B,
            "tokenizer_digest": D64C,
            "jspace_profile_digest": D64D,
            "lens_profile_digest": D64A,
            "workspace_calibration_digest": D64B,
        },
        "workspace": {
            "before_digest": D64A,
            "after_digest": D64B,
            "gwt_admitted_digests": [D64A, D64B],
            "gwt_winner_digests": [D64B],
            "jspace_observation_digests": [D64C],
            "thalamus_decisions_digest": D64D,
            "epq_telemetry_digest": D64A,
            "hyperposition_digests": [D64B],
            "claycode_digests": [D64C],
            "omega_digests": [D64D],
        },
        "inference": {
            "engine_class": "BUNDLED_08B",
            "jspace_mode": "FULL_LOCAL_LATENT",
            "capability_profile_digest": D64A,
            "inference_packet_digest": D64B,
            "candidate_result_digest": D64C,
            "candidate_authority": "CANDIDATE_ONLY",
            "epistemic_status": "MEASURED_SUPPORTED",
        },
        "admission": {
            "free_only": True,
            "cost_class": "LOCAL",
            "admitted": True,
            "secret_lookup_count": 0,
            "network_attempt_count": 0,
            "reason_codes": ["LOCAL_FREE_ONLY_ADMITTED"],
        },
        "bindings": {
            "zero_identity_match": True,
            "bundled_manifest_match": True,
            "capability_match": True,
            "stale_generation": False,
        },
        "reconciliation": {
            "decision": "ACCEPT",
            "canonical_write": True,
            "effect_authorized": False,
            "reason_codes": ["MEASURED_SUPPORTED_WRITE"],
        },
        "replay": {
            "stochasticity_disabled": True,
            "replay_performed": True,
            "scheduler_input_digest": D64A,
            "scheduler_decision_digest": D64B,
            "replay_match": True,
        },
        "terminal_result_digest": D64D,
    }


class ReceiptContractTests(unittest.TestCase):
    def test_valid_local_bundled_path(self):
        checks = validate_receipt(valid_receipt())
        self.assertIn("AUTHORITY_SPLIT_VALID", checks)

    def test_gwt_winner_must_have_been_admitted(self):
        r = valid_receipt()
        r["workspace"]["gwt_winner_digests"] = [D64D]
        with self.assertRaisesRegex(ReceiptError, "GWT_WINNER_NOT_ADMITTED"):
            validate_receipt(r)

    def test_claude_cannot_claim_local_latent_jspace(self):
        r = valid_receipt()
        r["inference"]["engine_class"] = "CLAUDE_CODE"
        r["inference"]["jspace_mode"] = "FULL_LOCAL_LATENT"
        with self.assertRaisesRegex(ReceiptError, "CLAUDE_JSPACE_MODE_MUST_BE_COMPILED_EXTERNAL"):
            validate_receipt(r)

    def test_free_only_paid_lane_touches_neither_secret_nor_network(self):
        r = valid_receipt()
        r["admission"].update({"cost_class": "SUBSCRIPTION", "admitted": False, "network_attempt_count": 1})
        with self.assertRaisesRegex(ReceiptError, "FREE_ONLY_NETWORK_TOUCH"):
            validate_receipt(r)

    def test_stale_generation_cannot_write(self):
        r = valid_receipt()
        r["bindings"]["stale_generation"] = True
        with self.assertRaisesRegex(ReceiptError, "STALE_OR_MISMATCHED_BINDING_AUTHORITY"):
            validate_receipt(r)

    def test_deterministic_replay_mismatch_fails_closed(self):
        r = valid_receipt()
        r["replay"]["replay_match"] = False
        with self.assertRaisesRegex(ReceiptError, "DETERMINISTIC_REPLAY_MISMATCH"):
            validate_receipt(r)

    def test_unusual_workspace_stability_truth_confusion_mutation(self):
        # Exactly one unusual experiment for this go macrocycle.
        # Workspace/J-Space/GWT geometry remains byte-identical while only the
        # epistemic truth status is mutated to REFUTED and authority is left on.
        baseline = valid_receipt()
        mutated = copy.deepcopy(baseline)
        mutated["inference"]["epistemic_status"] = "REFUTED"
        self.assertEqual(mutated["workspace"], baseline["workspace"])
        with self.assertRaisesRegex(ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            validate_receipt(mutated)


if __name__ == "__main__":
    unittest.main()
