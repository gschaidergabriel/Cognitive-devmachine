from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_abstract_lexical_token_audit_v1 as lexical
import trigger1_nuisance_subspace_residualize_v1 as nuisance
import trigger1_cross_scope_paired_tost_v1 as tost


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lexical_payload() -> dict:
    target_orders = {
        "AFFIRMATIVE": (0, 1, 2),
        "NEGATIVE": (1, 2, 0),
        "NEUTRAL": (2, 0, 1),
    }
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    vocab = {
        "BASIS": [
            (("mira", "velo", "sanu"), (101, 102, 103)),
            (("keto", "lumi", "rava"), (104, 105, 106)),
            (("nari", "pelo", "tuma"), (107, 108, 109)),
            (("cavo", "deli", "fira"), (110, 111, 112)),
            (("ganu", "hemi", "jora"), (113, 114, 115)),
            (("lavo", "mepi", "nura"), (116, 117, 118)),
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
    parts = {}
    for part, families in vocab.items():
        rows = []
        for fi, (ws, ids) in enumerate(families):
            for target in lexical.TARGETS:
                order = target_orders[target]
                content = " ".join(ws[i] for i in order)
                prompt = "/no_think\n" + content
                rows.append(
                    {
                        "row_id": f"{part.lower()}-{fi}-{target.lower()}",
                        "family_id": f"{part.lower()}-family-{fi}",
                        "semantic_target": target,
                        "output_code_identity": rotations[fi % 3][target] if part != "BASIS" else None,
                        "prompt": prompt,
                        "prompt_sha256": h(prompt),
                        "content_text": content,
                        "content_token_ids": [ids[i] for i in order],
                        "model_facing_target_identity_exposed": False,
                        "model_facing_explicit_semantic_labels": False,
                    }
                )
        parts[part] = rows
    return {
        "schema": lexical.INPUT_SCHEMA,
        "frozen_before_holdout": True,
        "tokenizer_identity": {"tokenizer_json_sha256": "a" * 64, "content_token_ids_recomputed_from_exact_tokenizer": True},
        "partitions": parts,
    }


def nuisance_payload() -> dict:
    dimension = 8
    semantic0 = [1.0, 0.0, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0]
    semantic1 = [0.0, 1.0, 0.0, 0.1, 0.2, 0.0, 0.0, 0.0]
    nuisance_vectors = {
        "CANONICAL_LABEL_LEXEME": np.eye(dimension)[2],
        "SEMANTIC_SYNONYM_LEXICON": np.eye(dimension)[3],
        "GENERIC_INSTRUCTION_COMPLIANCE": np.eye(dimension)[4],
        "OUTPUT_CODE_IDENTITY": np.eye(dimension)[5],
    }
    pairs = []
    for axis, vector in nuisance_vectors.items():
        for i in range(3):
            center = np.zeros(dimension)
            center[6] = 0.01 * i
            pairs.append(
                {
                    "nuisance_axis": axis,
                    "pair_id": f"{axis}-{i}",
                    "positive_activation": list(center + 0.5 * vector),
                    "negative_activation": list(center - 0.5 * vector),
                }
            )
    return {
        "schema": nuisance.INPUT_SCHEMA,
        "calibration_only": True,
        "holdout_opened": False,
        "frozen_before_holdout": True,
        "dimension": dimension,
        "semantic_basis_receipt_sha256": "b" * 64,
        "calibration_case_plan_sha256": "c" * 64,
        "semantic_basis": {"H1": semantic0, "H2": semantic1},
        "nuisance_pairs": pairs,
    }


def tost_payload(delta: float = 0.01) -> dict:
    rows = []
    for i in range(12):
        legacy = 0.8 + 0.03 * i
        native = legacy + delta + (0.002 if i % 2 else -0.002)
        rows.append(
            {
                "pair_id": f"p{i}",
                "legacy_control_normalized_effect": legacy,
                "native_control_normalized_effect": native,
            }
        )
    return {
        "schema": tost.INPUT_SCHEMA,
        "legacy_scope": "LAST_TOKEN_ONLY",
        "native_scope": "ALL_PROMPT_TOKENS",
        "same_case_universe": True,
        "same_layer": True,
        "same_projected_vector_identity": True,
        "same_control_family": True,
        "equivalence_protocol_frozen_before_observation": True,
        "equivalence_protocol_sha256": "d" * 64,
        "case_universe_sha256": "e" * 64,
        "projected_vector_sha256": "f" * 64,
        "control_family_sha256": "1" * 64,
        "alpha": 0.05,
        "equivalence_rope_abs_standardized_effect": 0.20,
        "paired_effect_rows": rows,
    }


class LexicalAuditTests(unittest.TestCase):
    def test_hard_counterbalanced_disjoint_design_passes(self):
        r = lexical.audit(lexical_payload())
        self.assertTrue(r["pass"], r["failures"])
        self.assertTrue(r["basis_holdout_lexically_disjoint"])
        self.assertTrue(r["within_family_word_and_token_multiset_counterbalanced"])
        self.assertTrue(r["full_three_by_three_target_x_output_code"])

    def test_generic_compliance_proxy_fails(self):
        p = lexical_payload()
        row = p["partitions"]["BASIS"][0]
        row["content_text"] += " approve"
        row["prompt"] += " approve"
        row["prompt_sha256"] = h(row["prompt"])
        r = lexical.audit(p)
        self.assertFalse(r["pass"])
        self.assertTrue(any("SEMANTIC_PROXY_LEAK" in x for x in r["failures"]))

    def test_cross_split_token_overlap_fails(self):
        p = lexical_payload()
        p["partitions"]["HOLDOUT"][0]["content_token_ids"][0] = p["partitions"]["BASIS"][0]["content_token_ids"][0]
        r = lexical.audit(p)
        self.assertFalse(r["pass"])
        self.assertIn("BASIS_HOLDOUT_CONTENT_TOKEN_OVERLAP", r["failures"])

    def test_target_specific_word_multiset_fails(self):
        p = lexical_payload()
        row = p["partitions"]["CALIBRATION"][0]
        row["content_text"] += " qiru"
        row["prompt"] += " qiru"
        row["prompt_sha256"] = h(row["prompt"])
        row["content_token_ids"].append(999)
        r = lexical.audit(p)
        self.assertFalse(r["pass"])
        self.assertTrue(any("MULTISET_NOT_COUNTERBALANCED" in x for x in r["failures"]))


class NuisanceResidualizationTests(unittest.TestCase):
    def test_projection_removes_all_four_nuisance_axes_and_retains_signal(self):
        r = nuisance.residualize(nuisance_payload())
        receipt = r["nuisance_receipt"]
        self.assertTrue(receipt["pass"])
        self.assertLessEqual(receipt["post_projection_max_abs_nuisance_cosine"], nuisance.MAX_ABS_COS)
        self.assertGreater(receipt["retained_semantic_subspace_norm_fraction"], nuisance.MIN_RETAINED)
        self.assertEqual(set(receipt["nuisance_axes"]), set(nuisance.AXES))

    def test_missing_nuisance_axis_pairs_fails_closed(self):
        p = nuisance_payload()
        p["nuisance_pairs"] = [x for x in p["nuisance_pairs"] if x["nuisance_axis"] != "GENERIC_INSTRUCTION_COMPLIANCE"]
        with self.assertRaisesRegex(ValueError, "AT_LEAST_THREE_MATCHED_PAIRS"):
            nuisance.residualize(p)

    def test_projection_that_erases_semantic_basis_fails(self):
        p = nuisance_payload()
        p["semantic_basis"] = {"H1": list(np.eye(8)[2])}
        with self.assertRaisesRegex(ValueError, "ERASED_BY_NUISANCE"):
            nuisance.residualize(p)


class PairedTostTests(unittest.TestCase):
    def test_student_t_cdf_symmetry(self):
        self.assertAlmostEqual(tost.t_cdf(0.0, 10), 0.5, places=12)
        self.assertAlmostEqual(tost.t_cdf(1.5, 10) + tost.t_cdf(-1.5, 10), 1.0, places=10)

    def test_equivalent_paired_effects_pass(self):
        r = tost.adjudicate(tost_payload(0.01))
        self.assertTrue(r["paired_tost_pass"])
        self.assertTrue(r["control_normalized_effect_sign_structure_agrees"])
        self.assertTrue(r["pass"])
        self.assertFalse(r["strict_micro_mechanistic_identity_claimed"])

    def test_non_equivalent_scope_effects_fail(self):
        r = tost.adjudicate(tost_payload(0.35))
        self.assertFalse(r["paired_tost_pass"])
        self.assertFalse(r["pass"])


if __name__ == "__main__":
    unittest.main()
