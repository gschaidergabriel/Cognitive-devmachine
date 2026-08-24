import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validator", ROOT / "tools" / "validate_hcu_jspace_local_activation_probe_v2.py"
)
v = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v)

D = [f"{i:x}" * 64 for i in range(1, 15)]


def condition(name, before, after=None, layer=2, metrics=True):
    row = {
        "condition": name,
        "model_execution_id_derived_local": D[0],
        "jspace_trace_id_derived_local": D[1],
        "derived_ids_are_canonical": False,
        "layer": layer,
        "activation_site": f"decoder_layer:{layer}:position:3",
        "activation_before_sha256_float32": before,
        "activation_after_sha256_float32": after or before,
        "activation_shape": [1024],
        "activation_dtype": "torch.float32",
        "final_logits_sha256_float32": D[2],
        "field_classification": "OBSERVED_RUNTIME_MEASUREMENT_WITH_DERIVED_LOCAL_IDS",
    }
    if metrics:
        row.update(
            target_token_id=1,
            target_logit=1.0,
            off_target_token_id=2,
            off_target_logit=0.2,
        )
    return row


def base(mode="intervention"):
    clean, corrupt, offref = D[3], D[4], D[6]
    if mode == "observation":
        conditions = [condition("OBSERVATION_BASELINE_CLEAN", clean, metrics=False)]
        lease = {
            "status": "NOT_REQUIRED_OBSERVATION_ONLY_NO_HIDDEN_STATE_MODIFICATION",
            "unusual_intervention_performed": False,
        }
        classification = "LOCAL_MODEL_SPECIFIC_OBSERVATION_CANDIDATE_EVIDENCE_ONLY"
        probe = {
            "layer": 2,
            "target_position": 3,
            "clean_token_ids_sha256": D[7],
            "conditions": conditions,
        }
    else:
        conditions = [
            condition("BASELINE_CLEAN", clean),
            condition("BASELINE_CORRUPTED", corrupt),
            condition("BASELINE_CLEAN_OFF_TARGET_REFERENCE", offref),
            condition("INTERVENTION_TARGET", corrupt, clean),
            condition("SHAM_CONTROL", corrupt, corrupt),
            condition("OFF_TARGET_CONTROL", D[8], offref),
        ]
        lease = {
            "trigger_key": "go-test",
            "claim_path": "research_entity/continuity/go_experiment_claims/go-test.json",
            "claim_sha256": D[9],
            "claimant_organ": "test",
            "experiment_name": "probe",
            "intervention_contract": "contract:v1",
            "lease_file_validated": True,
        }
        classification = "LOCAL_MODEL_SPECIFIC_CAUSAL_CANDIDATE_EVIDENCE_ONLY"
        probe = {
            "layer": 2,
            "target_position": 3,
            "off_target_position": 2,
            "clean_token_ids_sha256": D[7],
            "corrupted_token_ids_sha256": D[8],
            "conditions": conditions,
            "derived_metrics": {
                "target_patch_effect_on_target_logit": 0.8,
                "sham_effect_on_target_logit": 0.0,
                "off_target_patch_effect_on_target_logit": 0.1,
                "target_patch_effect_on_off_target_logit": 0.05,
            },
        }
    return {
        "schema": v.SCHEMA,
        "observed_at": "2026-08-24T11:35:58+00:00",
        "probe_mode": mode,
        "classification": classification,
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "mode": "FREE_ONLY_LOCAL_OFFLINE",
        "source_git_head": "052b861f1930167e232ad3e57f2a2d9eeeb325d2",
        "probe_source_sha256": D[10],
        "authority": {
            "epoch": "8.68",
            "inbox_sha256": D[11],
            "steering_sha256": D[12],
        },
        "atomic_experiment_lease": lease,
        "causal_binding": {
            "generation": "1",
            "causal_event_id": "e",
            "admission_id": "a",
            "route_id": "r",
            "inference_receipt_id": "i",
        },
        "model_source_identity": {
            "tree_sha256": D[13],
            "files": [{"path": "config.json", "size": 1, "sha256": D[0]}],
        },
        "network_attempt_count": 0,
        "credit": {
            "entityos_hcu_whole_runtime": 0,
            "hcu_full_runtime": 0,
            "jspace_model_runtime": 0,
            "training": 0,
            "whole_product_pass": False,
        },
        "runtime": {
            "python": "3.12",
            "torch": "x",
            "transformers": "x",
            "device": "cpu",
            "model_class": "M",
            "tokenizer_class": "T",
            "layers": 4,
        },
        "post_load_identity": {
            "post_load_parameter_value_sha256_float32_canonical": D[1],
            "parameter_tensors": 1,
            "parameter_elements": 1,
            "loader_consumption_attestation": False,
            "field_classification": "OBSERVED_POST_LOAD_VALUE_IDENTITY_PARTIAL",
            "note": "partial",
        },
        "probe": probe,
        "promotion": {"status": "UNASSESSED_CANDIDATE_ONLY", "reason": "raw probe only"},
    }


class Tests(unittest.TestCase):
    def test_observation_pass(self):
        self.assertTrue(v.validate(base("observation"))["ok"])

    def test_intervention_pass_but_remains_unassessed(self):
        self.assertEqual(v.validate(base())["promotion"], "UNASSESSED_CANDIDATE_ONLY")

    def test_network_touch_fails(self):
        r = base()
        r["network_attempt_count"] = 1
        with self.assertRaisesRegex(v.ProbeReceiptError, "OFFLINE_NETWORK_ATTEMPT"):
            v.validate(r)

    def test_loader_self_attestation_fails(self):
        r = base()
        r["post_load_identity"]["loader_consumption_attestation"] = True
        with self.assertRaisesRegex(v.ProbeReceiptError, "RAW_PROBE_CANNOT_SELF_ATTEST"):
            v.validate(r)

    def test_credit_inflation_fails(self):
        r = base()
        r["credit"]["jspace_model_runtime"] = 1
        with self.assertRaisesRegex(v.ProbeReceiptError, "CREDIT_INFLATION"):
            v.validate(r)

    def test_raw_causal_promotion_fails(self):
        r = base()
        r["promotion"]["status"] = "PASS"
        with self.assertRaisesRegex(v.ProbeReceiptError, "RAW_PROBE_PROMOTION_FORBIDDEN"):
            v.validate(r)

    def test_observation_hidden_state_modification_fails(self):
        r = base("observation")
        r["probe"]["conditions"][0]["activation_after_sha256_float32"] = D[2]
        with self.assertRaisesRegex(v.ProbeReceiptError, "OBSERVATION_MODIFIED_HIDDEN_STATE"):
            v.validate(r)

    def test_missing_core_condition_fails(self):
        r = base()
        r["probe"]["conditions"] = [
            x for x in r["probe"]["conditions"] if x["condition"] != "SHAM_CONTROL"
        ]
        with self.assertRaisesRegex(v.ProbeReceiptError, "INTERVENTION_CONDITION_SET_INVALID"):
            v.validate(r)

    def test_target_patch_must_equal_clean_activation(self):
        r = base()
        target = next(
            x for x in r["probe"]["conditions"] if x["condition"] == "INTERVENTION_TARGET"
        )
        target["activation_after_sha256_float32"] = D[9]
        with self.assertRaisesRegex(v.ProbeReceiptError, "TARGET_PATCH_NOT_BOUND_TO_CLEAN_ACTIVATION"):
            v.validate(r)

    def test_atomic_lease_required_for_intervention(self):
        r = base()
        r["atomic_experiment_lease"]["lease_file_validated"] = False
        with self.assertRaisesRegex(v.ProbeReceiptError, "INTERVENTION_ATOMIC_LEASE_NOT_VALIDATED"):
            v.validate(r)


if __name__ == "__main__":
    unittest.main()
