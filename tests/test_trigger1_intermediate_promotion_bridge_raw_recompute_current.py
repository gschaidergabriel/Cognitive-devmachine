from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_contrastive_protocol as protocol
import trigger1_intermediate_promotion_bridge as bridge

HEX64 = "a" * 64
HEAD40 = "b" * 40

SCORES = {
    "BASELINE": 0.0,
    "+VECTOR": 2.0,
    "SIGN_FLIP": -2.0,
    "NULL_VECTOR": 0.0,
    "ORTHOGONAL_SAME_NORM": 0.1,
    "PERMUTED_SAME_NORM": -0.1,
}


def _row(
    *,
    split: str,
    case_id: str,
    control: str,
    target_score: float,
    seed: int,
    prompt_sha256: str,
    label_map_id: str | None = None,
    positive_label: str = "A",
    negative_label: str = "B",
) -> dict:
    row = {
        "split": split,
        "case_id": case_id,
        "layer": 12,
        "gain": 1.0,
        "control": control,
        "target_score": target_score,
        "seed": seed,
        "prompt_sha256": prompt_sha256,
        "runtime_receipt_sha256": HEX64,
        "hook_calls": 1,
        "applied_vector_sha256": HEX64,
        "positive_label": positive_label,
        "negative_label": negative_label,
    }
    if label_map_id is not None:
        row["label_map_id"] = label_map_id
    return row


def _control_family(
    *,
    split: str,
    case_id: str,
    seed: int,
    prompt_sha256: str,
    label_map_id: str | None = None,
    positive_label: str = "A",
    negative_label: str = "B",
) -> list[dict]:
    rows = [
        _row(
            split=split,
            case_id=case_id,
            control=control,
            target_score=score,
            seed=seed,
            prompt_sha256=prompt_sha256,
            label_map_id=label_map_id,
            positive_label=positive_label,
            negative_label=negative_label,
        )
        for control, score in SCORES.items()
    ]
    if split == "holdout":
        plus = next(row for row in rows if row["control"] == "+VECTOR")
        plus.update(
            {
                "wrong_layer": 18,
                "wrong_layer_vector_source_layer": 12,
                "wrong_layer_same_selected_vector": True,
                "wrong_layer_delta": -0.25,
                "lesion_delta": -0.5,
                "rescue_delta": 1.0,
                "wrong_layer_receipt_sha256": HEX64,
                "lesion_receipt_sha256": HEX64,
                "rescue_receipt_sha256": HEX64,
            }
        )
    return rows


def valid_inputs(
    *,
    calibration_prompt: str = "1" * 64,
    calibration_seed: int = 1701,
    hold_ab_prompt: str = "2" * 64,
    hold_ab_seed: int = 2718,
    hold_ba_prompt: str = "3" * 64,
    hold_ba_seed: int = 3141,
) -> tuple[dict, dict]:
    calibration = _control_family(
        split="calibration",
        case_id="cal-1",
        seed=calibration_seed,
        prompt_sha256=calibration_prompt,
    )
    holdout: list[dict] = []
    holdout.extend(
        _control_family(
            split="holdout",
            case_id="hold-1",
            seed=hold_ab_seed,
            prompt_sha256=hold_ab_prompt,
            label_map_id="MAP_AB",
            positive_label="A",
            negative_label="B",
        )
    )
    holdout.extend(
        _control_family(
            split="holdout",
            case_id="hold-2",
            seed=hold_ba_seed,
            prompt_sha256=hold_ba_prompt,
            label_map_id="MAP_BA",
            positive_label="B",
            negative_label="A",
        )
    )
    selected = protocol.select_layer_gain(calibration)
    if not selected.get("selected"):
        raise AssertionError(selected)
    verdict = protocol.adjudicate_holdout(
        holdout,
        selected_layer=int(selected["layer"]),
        selected_gain=float(selected["gain"]),
    )
    if not verdict.get("pass"):
        raise AssertionError(verdict)

    source = {"repo_head": HEAD40, "repo_tree": "c" * 40}
    derivation_prompt_hashes = sorted(["4" * 64, "5" * 64])
    derivation = {
        "sources": [
            {
                "polarity": "positive",
                "prompt_sha256": "4" * 64,
                "activation_sha256": {"12": HEX64},
            },
            {
                "polarity": "negative",
                "prompt_sha256": "5" * 64,
                "activation_sha256": {"12": HEX64},
            },
        ],
        "directions": {
            "12": {
                "construction": "mean(calibration_positive_residual)-mean(calibration_negative_residual); unit_normalized",
                "direction_sha256": HEX64,
                "positive_activation_family_sha256": HEX64,
                "negative_activation_family_sha256": HEX64,
            }
        },
        "label_independence": {
            "schema": bridge.LABEL_INDEPENDENCE_SCHEMA,
            "derivation_input_family_sha256": bridge.digest(derivation_prompt_hashes),
            "evaluation_output_labels_resolved_before_derivation": False,
            "uses_evaluation_output_labels": False,
            "construction": "fixed semantic positive/negative intermediate activations only",
        },
    }
    result = {
        "schema": bridge.INTERMEDIATE_SCHEMA,
        "status": "PASS",
        "source": source,
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "d" * 40,
        "checkpoint_sha256": HEX64,
        "tokenizer_sha256": HEX64,
        "runtime_build_sha256": HEX64,
        "derivation": derivation,
        "calibration_rows": calibration,
        "selected": selected,
        "holdout_rows": holdout,
        "verdict": verdict,
        "api_endpoint": "http://127.0.0.1:8089/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
        "credit_scope": bridge.CREDIT_SCOPE,
    }
    candidate = {
        "schema": bridge.INTERMEDIATE_CANDIDATE_SCHEMA,
        "credit_scope": bridge.CREDIT_SCOPE,
        "source_identity": source,
        "model": result["model"],
        "model_revision": result["model_revision"],
        "checkpoint_sha256": result["checkpoint_sha256"],
        "tokenizer_sha256": result["tokenizer_sha256"],
        "runtime_build_sha256": result["runtime_build_sha256"],
        "selected_layer": selected["layer"],
        "selected_gain": selected["gain"],
        "direction_sha256": HEX64,
        "calibration_family_sha256": bridge.digest(calibration),
        "holdout_family_sha256": bridge.digest(holdout),
        "verdict": verdict,
    }
    candidate["candidate_sha256"] = bridge.digest(candidate)
    return result, candidate


class RawEvidenceRecomputeCurrentTests(unittest.TestCase):
    def test_positive_path_recomputes_raw_evidence(self) -> None:
        result, candidate = valid_inputs()
        direct = bridge.build_direct_candidate(result, candidate)
        self.assertTrue(direct["intermediate_protocol"]["raw_selection_recomputed"])
        self.assertTrue(direct["intermediate_protocol"]["raw_holdout_verdict_recomputed"])
        self.assertFalse(direct["vector_derivation"]["uses_evaluation_output_labels"])

    def test_stored_pass_verdict_cannot_override_raw_holdout(self) -> None:
        result, candidate = valid_inputs()
        row = next(r for r in result["holdout_rows"] if r["label_map_id"] == "MAP_AB" and r["control"] == "+VECTOR")
        row["target_score"] = -3.0
        with self.assertRaises(bridge.BridgeError):
            bridge.build_direct_candidate(result, candidate)

    def test_stored_selection_cannot_override_raw_calibration(self) -> None:
        result, candidate = valid_inputs()
        result["selected"] = dict(result["selected"])
        result["selected"]["gain"] = 4.0
        with self.assertRaisesRegex(bridge.BridgeError, "CALIBRATION_SELECTION_RECOMPUTE_MISMATCH"):
            bridge.build_direct_candidate(result, candidate)

    def test_candidate_verdict_must_match_recomputed_evidence(self) -> None:
        result, candidate = valid_inputs()
        candidate["verdict"] = copy.deepcopy(candidate["verdict"])
        candidate["verdict"]["classification"] = "FORGED_PASS"
        candidate["candidate_sha256"] = bridge._candidate_self_hash(candidate)
        with self.assertRaisesRegex(bridge.BridgeError, "INTERMEDIATE_CANDIDATE_VERDICT_MISMATCH"):
            bridge.build_direct_candidate(result, candidate)

    def test_candidate_family_hashes_bind_raw_rows(self) -> None:
        result, candidate = valid_inputs()
        candidate["calibration_family_sha256"] = "f" * 64
        candidate["candidate_sha256"] = bridge._candidate_self_hash(candidate)
        with self.assertRaisesRegex(bridge.BridgeError, "INTERMEDIATE_CALIBRATION_FAMILY_MISMATCH"):
            bridge.build_direct_candidate(result, candidate)

    def test_derivation_cannot_smuggle_evaluation_labels(self) -> None:
        result, candidate = valid_inputs()
        result["derivation"]["sources"][0]["positive_label"] = "A"
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_EVALUATION_LABEL_METADATA_FORBIDDEN"):
            bridge.build_direct_candidate(result, candidate)

    def test_missing_upstream_label_independence_receipt_blocks(self) -> None:
        result, candidate = valid_inputs()
        del result["derivation"]["label_independence"]
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_RECEIPT_REQUIRED"):
            bridge.build_direct_candidate(result, candidate)

    def test_true_upstream_evaluation_label_use_blocks(self) -> None:
        result, candidate = valid_inputs()
        result["derivation"]["label_independence"]["uses_evaluation_output_labels"] = True
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_MUST_PROVE_EVALUATION_LABEL_INDEPENDENCE"):
            bridge.build_direct_candidate(result, candidate)

    def test_label_independence_family_binds_derivation_inputs(self) -> None:
        result, candidate = valid_inputs()
        result["derivation"]["label_independence"]["derivation_input_family_sha256"] = "f" * 64
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_FAMILY_MISMATCH"):
            bridge.build_direct_candidate(result, candidate)

    def test_calibration_holdout_prompt_overlap_still_fails_closed(self) -> None:
        result, candidate = valid_inputs(calibration_prompt="2" * 64)
        with self.assertRaisesRegex(bridge.BridgeError, "CALIBRATION_HOLDOUT_PROMPTS_MUST_BE_DISJOINT"):
            bridge.build_direct_candidate(result, candidate)

    def test_calibration_holdout_seed_overlap_still_fails_closed(self) -> None:
        result, candidate = valid_inputs(calibration_seed=2718)
        with self.assertRaisesRegex(bridge.BridgeError, "CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT"):
            bridge.build_direct_candidate(result, candidate)

    def test_duplicate_raw_calibration_control_cannot_hide_behind_stored_pass(self) -> None:
        result, candidate = valid_inputs()
        duplicate = copy.deepcopy(next(r for r in result["calibration_rows"] if r["control"] == "+VECTOR"))
        result["calibration_rows"].append(duplicate)
        with self.assertRaisesRegex(bridge.BridgeError, "CALIBRATION_RECOMPUTE_DID_NOT_SELECT"):
            bridge.build_direct_candidate(result, candidate)

    def test_split_raw_holdout_family_cannot_hide_behind_stored_pass(self) -> None:
        result, candidate = valid_inputs()
        row = next(r for r in result["holdout_rows"] if r["label_map_id"] == "MAP_AB" and r["control"] == "SIGN_FLIP")
        row["prompt_sha256"] = "6" * 64
        with self.assertRaises(bridge.BridgeError):
            bridge.build_direct_candidate(result, candidate)


if __name__ == "__main__":
    unittest.main()
