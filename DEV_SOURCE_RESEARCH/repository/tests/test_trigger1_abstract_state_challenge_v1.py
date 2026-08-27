from __future__ import annotations

from copy import deepcopy
import unittest

from tools import trigger1_abstract_state_challenge_v1 as challenge


def rehash(value: dict) -> None:
    value.pop("challenge_sha256", None)
    value["challenge_sha256"] = challenge.canonical_sha(value)


class Trigger1AbstractStateChallengeTests(unittest.TestCase):
    def test_built_challenge_passes_all_structural_shortcut_guards(self):
        value = challenge.build_challenge()
        verdict = challenge.validate(value)
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual(verdict["calibration_family_count"], 6)
        self.assertEqual(verdict["holdout_family_count"], 6)
        self.assertTrue(verdict["calibration_instruction_free"])
        self.assertTrue(verdict["holdout_target_blind"])
        self.assertTrue(verdict["repeated_target_lexical_marker_absent"])
        self.assertTrue(verdict["cross_split_content_lexically_disjoint"])
        self.assertTrue(verdict["semantic_target_x_code_counterbalanced"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_canonical_semantic_label_in_calibration_fails_closed(self):
        value = challenge.build_challenge()
        row = value["calibration_rows"][0]
        row["prompt"] += " affirmative"
        row["state_surface"] = row["prompt"]
        row["prompt_sha256"] = challenge.text_sha(row["prompt"])
        row["state_surface_sha256"] = challenge.text_sha(row["state_surface"])
        row["state_content_tokens"] = list(challenge.content_tokens(row["state_surface"]))
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("CANONICAL_LABEL_PRESENT" in item for item in verdict["failures"]))

    def test_repeated_target_specific_calibration_marker_fails_even_with_valid_hashes(self):
        value = challenge.build_challenge()
        affirmative = [
            row for row in value["calibration_rows"] if row["semantic_target"] == "AFFIRMATIVE"
        ][:2]
        for row in affirmative:
            row["prompt"] += " quasar"
            row["state_surface"] = row["prompt"]
            row["prompt_sha256"] = challenge.text_sha(row["prompt"])
            row["state_surface_sha256"] = challenge.text_sha(row["state_surface"])
            row["state_content_tokens"] = list(challenge.content_tokens(row["state_surface"]))
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertIn(
            "REPEATED_TARGET_ASSOCIATED_CALIBRATION_TOKEN:quasar:[2, 0, 0]",
            verdict["failures"],
        )

    def test_holdout_prompt_must_be_byte_identical_across_all_three_targets(self):
        value = challenge.build_challenge()
        family = value["holdout_rows"][0]["family_id"]
        row = next(
            item
            for item in value["holdout_rows"]
            if item["family_id"] == family and item["semantic_target"] == "AFFIRMATIVE"
        )
        row["prompt"] += " extra"
        row["prompt_sha256"] = challenge.text_sha(row["prompt"])
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertIn(
            f"HOLDOUT_TARGET_BLIND_PROMPT_BYTES_MUST_MATCH:{family}",
            verdict["failures"],
        )

    def test_calibration_holdout_content_overlap_fails_even_when_metadata_is_recomputed(self):
        value = challenge.build_challenge()
        family = value["holdout_rows"][0]["family_id"]
        rows = [item for item in value["holdout_rows"] if item["family_id"] == family]
        # "amber" is a calibration content token.  Put it into one holdout branch and
        # regenerate all derived holdout bytes for the family so only the lexical leak is fatal.
        branches = dict(rows[0]["branch_surfaces"])
        branches["AFFIRMATIVE"] += " Amber marker appears."
        target_to_code = {row["semantic_target"]: row["output_code_identity"] for row in rows}
        prompt = challenge._holdout_prompt(branches, target_to_code)
        branch_sha = {target: challenge.text_sha(branches[target]) for target in challenge.TARGETS}
        branch_tokens = {
            target: list(challenge.content_tokens(branches[target])) for target in challenge.TARGETS
        }
        for row in rows:
            row["branch_surfaces"] = dict(branches)
            row["branch_surface_sha256"] = dict(branch_sha)
            row["branch_content_tokens"] = deepcopy(branch_tokens)
            row["prompt"] = prompt
            row["prompt_sha256"] = challenge.text_sha(prompt)
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertTrue(
            any(item.startswith("CALIBRATION_HOLDOUT_CONTENT_LEXICON_MUST_BE_DISJOINT") for item in verdict["failures"])
        )

    def test_target_code_balance_cannot_drift(self):
        value = challenge.build_challenge()
        row = value["holdout_rows"][0]
        row["output_code_identity"] = "B" if row["output_code_identity"] != "B" else "C"
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertIn(
            "HOLDOUT_TARGET_X_CODE_LATIN_SQUARE_MUST_BE_EXACTLY_BALANCED_TWICE",
            verdict["failures"],
        )

    def test_declared_lexical_metadata_cannot_override_derived_prompt_content(self):
        value = challenge.build_challenge()
        row = value["calibration_rows"][0]
        row["state_content_tokens"] = []
        rehash(value)
        verdict = challenge.validate(value)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("DERIVED_TOKEN_SIGNATURE_MISMATCH" in item for item in verdict["failures"]))


if __name__ == "__main__":
    unittest.main()
