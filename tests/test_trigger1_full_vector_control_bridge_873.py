from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
import sys
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import jspace_vector_control_abi_v1 as abi
import trigger1_full_vector_control_bridge as full
import trigger1_intermediate_contrastive_protocol as protocol
import trigger1_intermediate_promotion_bridge as bridge

HEX = {
    "runtime": "1" * 64,
    "checkpoint": "2" * 64,
    "tokenizer": "3" * 64,
    "source_packet": "4" * 64,
    "adapter": "5" * 64,
    "local_vector": "6" * 64,
    "applied_vector": "7" * 64,
    "intervention": "8" * 64,
    "derivation": "9" * 64,
}
HEAD = "a" * 40


def calibration_rows() -> list[dict]:
    scores = {
        "BASELINE": 0.0,
        "+VECTOR": 2.0,
        "SIGN_FLIP": -2.0,
        "NULL_VECTOR": 0.0,
        "ORTHOGONAL_SAME_NORM": 0.1,
        "PERMUTED_SAME_NORM": 0.1,
    }
    rows: list[dict] = []
    for control in protocol.REQUIRED_CONTROLS:
        rows.append({
            "split": "calibration",
            "case_id": "cal-stance-map-ab",
            "prompt_sha256": "b" * 64,
            "seed": 1701,
            "positive_label": "A",
            "negative_label": "B",
            "layer": 12,
            "gain": 4.0,
            "control": control,
            "target_score": scores[control],
        })
    return rows


def holdout_rows() -> list[dict]:
    scores = {
        "BASELINE": 0.0,
        "+VECTOR": 2.0,
        "SIGN_FLIP": -2.0,
        "NULL_VECTOR": 0.0,
        "ORTHOGONAL_SAME_NORM": 0.1,
        "PERMUTED_SAME_NORM": 0.1,
    }
    rows: list[dict] = []
    for seed, label_map_id, positive_label, negative_label, prompt_sha in (
        (2718, "MAP_AB", "A", "B", "c" * 64),
        (3141, "MAP_BA", "B", "A", "d" * 64),
    ):
        for index, control in enumerate(protocol.REQUIRED_CONTROLS):
            receipt = format(seed + index, "064x")[-64:]
            row = {
                "split": "holdout",
                "case_id": f"hold-{seed}",
                "prompt_sha256": prompt_sha,
                "seed": seed,
                "positive_label": positive_label,
                "negative_label": negative_label,
                "label_map_id": label_map_id,
                "layer": 12,
                "gain": 4.0,
                "control": control,
                "target_score": scores[control],
                "runtime_receipt_sha256": receipt,
            }
            if control == "+VECTOR":
                row.update({
                    "hook_calls": 1,
                    "applied_vector_sha256": HEX["applied_vector"],
                    "wrong_layer": 18,
                    "wrong_layer_vector_source_layer": 12,
                    "wrong_layer_same_selected_vector": True,
                    "wrong_layer_delta": -1.0,
                    "wrong_layer_receipt_sha256": format(seed + 100, "064x")[-64:],
                    "lesion_delta": -1.0,
                    "rescue_delta": 2.0,
                    "lesion_receipt_sha256": format(seed + 200, "064x")[-64:],
                    "rescue_receipt_sha256": format(seed + 300, "064x")[-64:],
                })
            rows.append(row)
    return rows


def result_fixture() -> dict:
    calibration = calibration_rows()
    holdout = holdout_rows()
    selected = protocol.select_layer_gain(calibration)
    verdict = protocol.adjudicate_holdout(
        holdout,
        selected_layer=int(selected["layer"]),
        selected_gain=float(selected["gain"]),
    )
    assert selected["selected"] is True
    assert verdict["pass"] is True
    return {
        "schema": bridge.INTERMEDIATE_SCHEMA,
        "status": "PASS",
        "source": {"repo_head": HEAD, "repo_tree": "e" * 40},
        "runtime_build_sha256": HEX["runtime"],
        "checkpoint_sha256": HEX["checkpoint"],
        "tokenizer_sha256": HEX["tokenizer"],
        "calibration_rows": calibration,
        "holdout_rows": holdout,
        "selected": selected,
        "verdict": verdict,
    }


def direct_candidate_fixture() -> dict:
    controls = {
        name: {"runtime_receipt_sha256": format(5000 + i, "064x")[-64:]}
        for i, name in enumerate(abi.REQUIRED_CONTROLS)
    }
    return {
        "schema": bridge.DIRECT_SCHEMA,
        "source_identity": {
            "repo_head": HEAD,
            "runtime_build_sha256": HEX["runtime"],
            "checkpoint_sha256": HEX["checkpoint"],
            "tokenizer_sha256": HEX["tokenizer"],
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "invocation-1",
            "activation_site": "model.model.layers[12]:output:last_token",
            "source_packet_sha256": HEX["source_packet"],
            "adapter_sha256": HEX["adapter"],
            "local_vector_sha256": HEX["local_vector"],
            "applied_vector_sha256": HEX["applied_vector"],
            "runtime_intervention_receipt_sha256": HEX["intervention"],
            "gain": 4.0,
            "layer_start": 12,
            "layer_end": 12,
        },
        "controls": controls,
        "calibration": {"family_id": "cal-family"},
        "holdout": {
            "family_id": "hold-family",
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": bridge.digest(bridge.METRIC_DEFINITION),
            "label_mapping_counterbalanced": True,
        },
        "vector_derivation": {
            "method": "CALIBRATION_ONLY_INTERMEDIATE_RESIDUAL_CONTRAST",
            "derivation_family_id": "derivation-family",
            "derivation_receipt_sha256": HEX["derivation"],
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
        },
        "target": {
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@test",
            "execution_surface": "LOCAL_LOOPBACK_API",
        },
    }


class Trigger1FullVectorControlBridge873Tests(unittest.TestCase):
    def test_exact_source_and_measured_rows_build_full_control_packet(self):
        verdict = full.adjudicate(result_fixture(), direct_candidate_fixture())
        self.assertEqual("PASS", verdict["status"], verdict.get("failures"))
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit_minted"])
        self.assertFalse(verdict["training_credit_minted"])
        evidence = verdict["enriched_candidate"]["jspace_vector_control_evidence"]
        self.assertEqual("ADD", evidence["intervention_operator"])
        self.assertEqual("LAST_INPUT_TOKEN_AT_SELECTED_LAYER_OUTPUT", evidence["token_position_policy"])
        self.assertEqual(4.0, evidence["allowed_magnitude_envelope"]["gain_min"])
        self.assertEqual(4.0, evidence["allowed_magnitude_envelope"]["gain_max"])
        packet = verdict["abi_admission"]["packet"]
        self.assertEqual("JSPACE_VECTOR_CONTROL_ABI/v1", packet["schema"])
        self.assertEqual("FULL_CAUSAL_CONTROL_PACKET", packet["abi_role"])

    def test_activation_site_drift_fails_closed(self):
        candidate = direct_candidate_fixture()
        candidate["intervention"]["activation_site"] = "model.model.layers[12]:output:all_tokens"
        verdict = full.adjudicate(result_fixture(), candidate)
        self.assertEqual("BLOCKED", verdict["status"])
        self.assertTrue(any("DIRECT_ACTIVATION_SITE_CONTRACT_MISMATCH" in x for x in verdict["failures"]))

    def test_wrong_layer_nonlocalization_fails_closed(self):
        result = result_fixture()
        for row in result["holdout_rows"]:
            if row["control"] == "+VECTOR":
                row["wrong_layer_delta"] = 0.0
        result["verdict"] = protocol.adjudicate_holdout(
            result["holdout_rows"], selected_layer=12, selected_gain=4.0
        )
        verdict = full.adjudicate(result, direct_candidate_fixture())
        self.assertEqual("BLOCKED", verdict["status"])
        self.assertTrue(
            any(
                "INTERMEDIATE_PROTOCOL_PASS_REQUIRED" in x
                or "WRONG_LAYER_LOCALIZATION_EFFECT_NOT_STRICTLY_NEGATIVE" in x
                for x in verdict["failures"]
            )
        )

    def test_executor_blob_drift_fails_closed(self):
        contract = json.loads(full.CONTRACT_PATH.read_text(encoding="utf-8"))
        contract["executor_git_blob_sha1"] = "0" * 40
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(full.FullControlBridgeError, "EXECUTOR_SOURCE_CONTRACT_BLOB_MISMATCH"):
                full.load_source_contract(path)

    def test_target_metric_tamper_fails_closed(self):
        candidate = direct_candidate_fixture()
        candidate["holdout"]["metric_definition_sha256"] = "0" * 64
        verdict = full.adjudicate(result_fixture(), candidate)
        self.assertEqual("BLOCKED", verdict["status"])
        self.assertTrue(any("DIRECT_TARGET_METRIC_MISMATCH" in x for x in verdict["failures"]))


if __name__ == "__main__":
    unittest.main()
