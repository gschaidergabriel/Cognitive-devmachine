from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_abstract_state_deconfound_gate_v1 as deconf
import trigger1_scope_equivalence_gate_v1 as scope
import trigger1_jspace_promotion_gate_v11 as v11


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def deconf_payload() -> dict:
    partitions: dict[str, list[dict]] = {}
    target_orders = {
        "AFFIRMATIVE": (0, 1, 2),
        "NEGATIVE": (1, 2, 0),
        "NEUTRAL": (2, 0, 1),
    }
    code_rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    vocab = {
        "BASIS": [
            (("mira", "velo", "sanu"), (101, 102, 103)),
            (("keto", "lumi", "rava"), (104, 105, 106)),
            (("nari", "pelo", "tuma"), (107, 108, 109)),
        ],
        "CALIBRATION": [
            (("beko", "davi", "fenu"), (201, 202, 203)),
            (("gori", "hama", "juto"), (204, 205, 206)),
            (("lena", "moku", "pira"), (207, 208, 209)),
        ],
        "HOLDOUT": [
            (("qesa", "rimo", "tavi"), (301, 302, 303)),
            (("vona", "weli", "xaru"), (304, 305, 306)),
            (("yeni", "zopa", "cumi"), (307, 308, 309)),
        ],
    }
    for partition, families in vocab.items():
        rows: list[dict] = []
        for family_index, (lexemes, token_ids) in enumerate(families):
            for target in deconf.TARGETS:
                order = target_orders[target]
                ordered_words = [lexemes[i] for i in order]
                ordered_tokens = [token_ids[i] for i in order]
                content = " ".join(ordered_words)
                prompt = f"/no_think\n{content}"
                rows.append(
                    {
                        "row_id": f"{partition.lower()}-{family_index}-{target.lower()}",
                        "family_id": f"{partition.lower()}-family-{family_index}",
                        "semantic_target": target,
                        "output_code_identity": code_rotations[family_index][target] if partition != "BASIS" else None,
                        "prompt": prompt,
                        "prompt_sha256": h(prompt),
                        "content_text": content,
                        "content_token_ids": ordered_tokens,
                        "model_facing_target_identity_exposed": False,
                        "model_facing_explicit_semantic_labels": False,
                    }
                )
        partitions[partition] = rows
    return {
        "schema": deconf.SCHEMA,
        "tokenizer_identity": {
            "tokenizer_json_sha256": "a" * 64,
            "content_token_ids_recomputed_from_exact_tokenizer": True,
        },
        "partitions": partitions,
    }


def scope_payload() -> dict:
    identity = {
        "basis_vector_sha256": "b" * 64,
        "case_plan_sha256": "c" * 64,
        "control_family_sha256": "d" * 64,
        "layer": 20,
        "gain": 1.0,
    }
    scopes = {
        "PYTORCH_LAST_TOKEN": "LAST_TOKEN_ONLY_AT_SELECTED_BLOCK_OUTPUT",
        "PYTORCH_ALL_PROMPT_TOKENS": "ALL_PROMPT_TOKEN_POSITIONS_AT_SELECTED_BLOCK_OUTPUT",
        "NATIVE_CVEC_ALL_PROMPT_TOKENS": "ALL_PROMPT_TOKEN_POSITIONS_PRESENT_IN_DECODE_BATCH",
    }
    base_scores = {
        "BASELINE": 0.0,
        "+VECTOR": 2.0,
        "SIGN_FLIP": -2.0,
        "NULL_VECTOR": 0.0,
        "ORTHOGONAL_SAME_NORM": 0.5,
        "PERMUTED_SAME_NORM": 0.25,
    }
    scales = {"PYTORCH_LAST_TOKEN": 1.0, "PYTORCH_ALL_PROMPT_TOKENS": 1.02, "NATIVE_CVEC_ALL_PROMPT_TOKENS": 1.01}
    rows: list[dict] = []
    for case_index in range(2):
        case_id = h(f"case-{case_index}")
        for condition in scope.CONDITIONS:
            for control in scope.CONTROLS:
                rows.append(
                    {
                        "condition": condition,
                        "case_identity_sha256": case_id,
                        "control": control,
                        "basis_vector_sha256": identity["basis_vector_sha256"],
                        "layer": 20,
                        "gain": 1.0,
                        "target_score": base_scores[control] * scales[condition],
                        "intervention_scope": scopes[condition],
                        "native_cvec_rc": 0 if condition == "NATIVE_CVEC_ALL_PROMPT_TOKENS" and control != "BASELINE" else None,
                    }
                )
    return {
        "schema": scope.SCHEMA,
        "preregistration": {
            "receipt_sha256": "e" * 64,
            "thresholds_frozen_before_holdout": True,
            "thresholds": {
                "min_effect_pattern_cosine": 0.995,
                "max_effect_pattern_relative_l2": 0.05,
                "max_null_drift": 1e-6,
            },
        },
        "frozen_identity": identity,
        "observations": rows,
    }


def resign(receipt: dict) -> dict:
    core = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    return {**core, "receipt_sha256": v11.canonical_sha(core)}


class AbstractStateDeconfoundGateTests(unittest.TestCase):
    def test_balanced_disjoint_synthetic_design_passes(self):
        verdict = deconf.adjudicate(deconf_payload())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertTrue(verdict["within_family_lexical_counterbalance"])
        self.assertTrue(verdict["within_family_token_counterbalance"])
        self.assertTrue(verdict["cross_partition_lexically_disjoint"])
        self.assertTrue(verdict["cross_partition_model_token_disjoint"])

    def test_canonical_label_or_compliance_proxy_fails_closed(self):
        for leaked in ("AFFIRMATIVE", "approve"):
            payload = deconf_payload()
            row = payload["partitions"]["BASIS"][0]
            row["content_text"] += " " + leaked
            row["prompt"] += " " + leaked
            row["prompt_sha256"] = h(row["prompt"])
            verdict = deconf.adjudicate(payload)
            self.assertFalse(verdict["pass"], leaked)
            self.assertTrue(any("PROXY_LEAK" in x for x in verdict["failures"]), verdict["failures"])

    def test_unigram_or_model_token_target_shortcut_fails(self):
        payload = deconf_payload()
        row = payload["partitions"]["CALIBRATION"][0]
        row["content_text"] += " qiru"
        row["prompt"] += " qiru"
        row["prompt_sha256"] = h(row["prompt"])
        row["content_token_ids"].append(999)
        verdict = deconf.adjudicate(payload)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("MULTISET_NOT_COUNTERBALANCED" in x for x in verdict["failures"]))

    def test_cross_partition_lexeme_or_token_overlap_fails(self):
        payload = deconf_payload()
        basis = payload["partitions"]["BASIS"][0]
        holdout = payload["partitions"]["HOLDOUT"][0]
        holdout["content_text"] += " " + basis["content_text"].split()[0]
        holdout["prompt"] += " " + basis["content_text"].split()[0]
        holdout["prompt_sha256"] = h(holdout["prompt"])
        holdout["content_token_ids"].append(basis["content_token_ids"][0])
        verdict = deconf.adjudicate(payload)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("CONTENT_LEXEME_OVERLAP" in x for x in verdict["failures"]))
        self.assertTrue(any("MODEL_TOKEN_ID_OVERLAP" in x for x in verdict["failures"]))


class ScopeEquivalenceGateTests(unittest.TestCase):
    def test_three_way_scope_invariant_replication_passes(self):
        verdict = scope.adjudicate(scope_payload())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual(verdict["classification"], "SCOPE_INVARIANT_THREE_WAY_REPLICATION")
        self.assertTrue(verdict["strict_last_token_native_identity"])

    def test_native_all_can_match_pytorch_all_without_last_token_identity(self):
        payload = scope_payload()
        for row in payload["observations"]:
            if row["condition"] == "PYTORCH_LAST_TOKEN":
                # Preserve six-control directionality but deliberately alter geometry.
                if row["control"] == "+VECTOR":
                    row["target_score"] = 9.0
                elif row["control"] == "SIGN_FLIP":
                    row["target_score"] = -0.2
                elif row["control"] == "ORTHOGONAL_SAME_NORM":
                    row["target_score"] = 8.0
                elif row["control"] == "PERMUTED_SAME_NORM":
                    row["target_score"] = 7.5
        verdict = scope.adjudicate(payload)
        self.assertFalse(verdict["pass"])
        self.assertTrue(verdict["broadcast_scope_carrier_replication"])
        self.assertFalse(verdict["strict_last_token_native_identity"])
        self.assertEqual(verdict["classification"], "BROADCAST_SCOPE_CARRIER_REPLICATION")

    def test_native_cvec_failure_fails_closed(self):
        payload = scope_payload()
        next(row for row in payload["observations"] if row["condition"] == "NATIVE_CVEC_ALL_PROMPT_TOKENS" and row["control"] == "+VECTOR")["native_cvec_rc"] = 3
        verdict = scope.adjudicate(payload)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("NATIVE_CVEC_RC_NOT_ZERO" in x for x in verdict["failures"]))

    def test_wrong_scope_attestation_fails_closed(self):
        payload = scope_payload()
        next(row for row in payload["observations"] if row["condition"] == "PYTORCH_ALL_PROMPT_TOKENS")["intervention_scope"] = "LAST_TOKEN_ONLY_AT_SELECTED_BLOCK_OUTPUT"
        verdict = scope.adjudicate(payload)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("SCOPE_ATTESTATION_INVALID" in x for x in verdict["failures"]))


class PromotionV11Tests(unittest.TestCase):
    def test_strongest_semantic_candidate_requires_v10_deconfound_and_strict_scope(self):
        deconf_receipt = deconf.adjudicate(deconf_payload())
        scope_receipt = scope.adjudicate(scope_payload())
        candidate = {
            "abstract_state_deconfound_receipt": deconf_receipt,
            "intervention_scope_equivalence_receipt": scope_receipt,
        }
        v10_pass = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v10",
            "scientifically_independent_vector_candidate": True,
            "v10_failures": [],
            "canonical_credit_minted": False,
        }
        with patch.object(v11.v10, "adjudicate", return_value=v10_pass):
            verdict = v11.adjudicate(candidate)
        self.assertTrue(verdict["native_broadcast_abstract_state_candidate"])
        self.assertTrue(verdict["abstract_state_cross_scope_replication_candidate"])
        self.assertTrue(verdict["semantic_jspace_abstract_state_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_broadcast_only_never_upgrades_to_cross_scope_semantic_candidate(self):
        deconf_receipt = deconf.adjudicate(deconf_payload())
        scope_input = scope_payload()
        for row in scope_input["observations"]:
            if row["condition"] == "PYTORCH_LAST_TOKEN" and row["control"] == "+VECTOR":
                row["target_score"] = 8.0
            if row["condition"] == "PYTORCH_LAST_TOKEN" and row["control"] == "ORTHOGONAL_SAME_NORM":
                row["target_score"] = 7.0
        scope_receipt = scope.adjudicate(scope_input)
        candidate = {
            "abstract_state_deconfound_receipt": deconf_receipt,
            "intervention_scope_equivalence_receipt": scope_receipt,
        }
        with patch.object(v11.v10, "adjudicate", return_value={"scientifically_independent_vector_candidate": True, "v10_failures": []}):
            verdict = v11.adjudicate(candidate)
        self.assertTrue(verdict["native_broadcast_abstract_state_candidate"])
        self.assertFalse(verdict["semantic_jspace_abstract_state_candidate"])

    def test_tampered_receipt_fails_closed(self):
        deconf_receipt = deconf.adjudicate(deconf_payload())
        deconf_receipt["pass"] = not deconf_receipt["pass"]
        candidate = {
            "abstract_state_deconfound_receipt": deconf_receipt,
            "intervention_scope_equivalence_receipt": scope.adjudicate(scope_payload()),
        }
        with patch.object(v11.v10, "adjudicate", return_value={"scientifically_independent_vector_candidate": True, "v10_failures": []}):
            verdict = v11.adjudicate(candidate)
        self.assertFalse(verdict["semantic_jspace_abstract_state_candidate"])
        self.assertIn("ABSTRACT_STATE_DECONFOUND_RECEIPT_INVALID_OR_UNBOUND", verdict["v11_failures"])


if __name__ == "__main__":
    unittest.main()
