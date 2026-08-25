import copy
import itertools
import unittest

from tools import trigger1_abstract_state_evidence_gate_v1 as gate


def make_split(name):
    rows = []
    for family in range(6):
        for state_index, state in enumerate(gate.STATES):
            payload = f"{name}lexeme{family}state{state_index}"
            prefix = "Encode relation: "
            suffix = " silently."
            rows.append({
                "case_id": f"{name}-f{family}-{state}",
                "family_id": f"{name}-family-{family}",
                "state_id": state,
                "scaffold_prefix": prefix,
                "semantic_payload": payload,
                "scaffold_suffix": suffix,
                "prompt": prefix + payload + suffix,
            })
    return {"cases": rows}


def make_valid():
    prompt_design = {name: make_split(name) for name in gate.SPLITS}
    readout = []
    for row in prompt_design["holdout"]["cases"]:
        scores = {state: 0.0 for state in gate.STATES}
        scores[row["state_id"]] = 2.0
        readout.append({
            "case_id": row["case_id"],
            "family_id": row["family_id"],
            "true_state_id": row["state_id"],
            "scores": scores,
        })

    causal = []
    for carrier in range(6):
        for target in gate.STATES:
            for control in gate.INTERVENTION_CONTROLS:
                scores = {state: 0.0 for state in gate.STATES}
                if control == "TARGET":
                    scores[target] = 2.0
                elif control == "SHUFFLED":
                    scores[next(state for state in gate.STATES if state != target)] = 0.5
                elif control == "SIGN_FLIP":
                    scores[target] = -1.0
                causal.append({
                    "carrier_case_id": f"carrier-{carrier}",
                    "vector_state_id": target,
                    "control": control,
                    "scores": scores,
                })

    behavior = []
    for carrier in range(2):
        for mapping_index, permutation in enumerate(itertools.permutations(gate.CODES)):
            mapping = dict(zip(gate.STATES, permutation))
            for target in gate.STATES:
                mapped = mapping[target]
                for control in gate.INTERVENTION_CONTROLS:
                    logits = {code: 0.0 for code in gate.CODES}
                    if control == "TARGET":
                        logits[mapped] = 2.0
                    elif control == "SHUFFLED":
                        logits[mapped] = -0.5
                    elif control == "SIGN_FLIP":
                        logits[mapped] = -1.0
                    behavior.append({
                        "carrier_case_id": f"carrier-{carrier}",
                        "vector_state_id": target,
                        "mapping_id": f"p{mapping_index}",
                        "control": control,
                        "state_to_code": mapping,
                        "code_logits": logits,
                    })

    return {
        "schema": gate.ATTESTATION_SCHEMA,
        "intervention_contract": {
            "carrier": gate.PINNED_CARRIER,
            "token_scope": gate.PINNED_SCOPE,
            "injection_layer": gate.PINNED_LAYER,
            "gguf_sha256": gate.PINNED_GGUF_SHA256,
            "llama_cpp_commit": gate.PINNED_LLAMA_CPP_COMMIT,
            "last_token_witness_equivalence_claimed": False,
            "last_token_witness_role": "ANTECEDENT_ONLY_NOT_CAUSAL_EQUIVALENCE",
        },
        "prompt_design": prompt_design,
        "internal_readout": {
            "fit_split": "basis",
            "tuning_split": "calibration",
            "evaluation_split": "holdout",
            "model_facing_state_labels": False,
            "holdout_rows": readout,
        },
        "causal_internal_state": {"rows": causal},
        "opaque_code_behavior": {"rows": behavior},
    }


class AbstractStateGateTests(unittest.TestCase):
    def test_valid_native_scope_passes_without_equivalence(self):
        result = gate.adjudicate(make_valid())
        self.assertTrue(result["native_broadcast_abstract_state_candidate"], result["failures"])
        self.assertFalse(result["cross_intervention_equivalence_candidate"])
        self.assertEqual(result["support_matched_bridge"]["status"], "NOT_PROVIDED_NATIVE_SCOPE_ONLY")

    def test_model_facing_historical_label_leak_fails(self):
        value = make_valid()
        row = value["prompt_design"]["basis"]["cases"][0]
        row["semantic_payload"] = "affirmative"
        row["prompt"] = row["scaffold_prefix"] + row["semantic_payload"] + row["scaffold_suffix"]
        result = gate.adjudicate(value)
        self.assertFalse(result["native_broadcast_abstract_state_candidate"])
        self.assertTrue(any("FORBIDDEN_MODEL_FACING_LEXEME" in failure for failure in result["failures"]))

    def test_cross_split_state_payload_lexical_reuse_fails(self):
        value = make_valid()
        left = value["prompt_design"]["basis"]["cases"][0]
        right = value["prompt_design"]["holdout"]["cases"][0]
        right["semantic_payload"] = left["semantic_payload"]
        right["prompt"] = right["scaffold_prefix"] + right["semantic_payload"] + right["scaffold_suffix"]
        result = gate.adjudicate(value)
        self.assertFalse(result["native_broadcast_abstract_state_candidate"])
        self.assertTrue(any(failure.startswith("LEXICAL_PAYLOAD_OVERLAP:BASIS:HOLDOUT") for failure in result["failures"]))

    def test_old_last_token_equivalence_cannot_be_silently_claimed(self):
        value = make_valid()
        value["intervention_contract"]["last_token_witness_equivalence_claimed"] = True
        result = gate.adjudicate(value)
        self.assertFalse(result["native_broadcast_abstract_state_candidate"])
        self.assertIn("LAST_TOKEN_WITNESS_EQUIVALENCE_MUST_NOT_BE_CLAIMED", result["failures"])

    def test_support_matched_bridge_promotes_only_cross_scope(self):
        value = make_valid()
        value["support_matched_bridge"] = {
            "native_scope": gate.PINNED_SCOPE,
            "comparison_scope": gate.PINNED_SCOPE,
            "same_layer": True,
            "same_prompt_case_universe": True,
            "same_vector_digests": True,
            "same_metric": True,
            "bridge_pass": True,
        }
        result = gate.adjudicate(value)
        self.assertTrue(result["native_broadcast_abstract_state_candidate"], result["failures"])
        self.assertTrue(result["cross_intervention_equivalence_candidate"])

    def test_generic_code_identity_effect_fails_counterbalance(self):
        value = make_valid()
        for row in value["opaque_code_behavior"]["rows"]:
            if row["control"] == "TARGET":
                row["code_logits"] = {"A": 2.0, "B": 0.0, "C": 0.0}
        result = gate.adjudicate(value)
        self.assertFalse(result["native_broadcast_abstract_state_candidate"])
        self.assertTrue(any(failure.startswith("OPAQUE_") for failure in result["failures"]))


if __name__ == "__main__":
    unittest.main()
