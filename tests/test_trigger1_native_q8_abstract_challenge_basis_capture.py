from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_abstract_state_challenge_v1 as challenge
from tools import trigger1_native_q8_abstract_challenge_basis_capture as bridge
from tools import trigger1_native_q8_jspace_basis_build as historical_basis


class NativeAbstractChallengeBasisBridgeTests(unittest.TestCase):
    def test_current_challenge_maps_exactly_to_eighteen_native_basis_rows(self):
        value = challenge.build_challenge()
        verdict, rows = bridge.prepare_basis_rows(value)
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual(18, len(rows))
        self.assertEqual(6, len({row["family_group_id"] for row in rows}))
        self.assertEqual(set(challenge.TARGETS), {row["semantic_class"] for row in rows})

        source = {
            (row["family_id"], row["semantic_target"]): row
            for row in value["calibration_rows"]
        }
        for row in rows:
            original = source[(row["family_group_id"], row["semantic_class"])]
            self.assertEqual(original["prompt"], row["prompt"])
            self.assertEqual(original["prompt_sha256"], row["prompt_sha256"])
            self.assertEqual(original["state_surface_sha256"], row["source_state_surface_sha256"])
            self.assertEqual("CALIBRATION", row["source_split"])

    def test_holdout_bytes_are_never_selected_for_basis_capture(self):
        value = challenge.build_challenge()
        _, rows = bridge.prepare_basis_rows(value)
        selected_hashes = {row["prompt_sha256"] for row in rows}
        holdout_hashes = {row["prompt_sha256"] for row in value["holdout_rows"]}
        self.assertTrue(selected_hashes.isdisjoint(holdout_hashes))
        self.assertTrue(all(row["source_split"] == "CALIBRATION" for row in rows))

    def test_mutated_challenge_cannot_cross_bridge_even_with_rehashed_top_level(self):
        value = challenge.build_challenge()
        row = value["calibration_rows"][0]
        row["prompt"] += " approve"
        row["state_surface"] = row["prompt"]
        row["prompt_sha256"] = challenge.text_sha(row["prompt"])
        row["state_surface_sha256"] = challenge.text_sha(row["state_surface"])
        row["state_content_tokens"] = list(challenge.content_tokens(row["state_surface"]))
        value.pop("challenge_sha256")
        value["challenge_sha256"] = challenge.canonical_sha(value)
        with self.assertRaisesRegex(bridge.BridgeError, "ABSTRACT_CHALLENGE_VALIDATION_FAILED"):
            bridge.prepare_basis_rows(value)

    def test_repeated_target_marker_cannot_cross_bridge(self):
        value = challenge.build_challenge()
        mutated = deepcopy(value)
        rows = [
            row for row in mutated["calibration_rows"]
            if row["semantic_target"] == "AFFIRMATIVE"
        ][:2]
        for row in rows:
            row["prompt"] += " quasar"
            row["state_surface"] = row["prompt"]
            row["prompt_sha256"] = challenge.text_sha(row["prompt"])
            row["state_surface_sha256"] = challenge.text_sha(row["state_surface"])
            row["state_content_tokens"] = list(challenge.content_tokens(row["state_surface"]))
        mutated.pop("challenge_sha256")
        mutated["challenge_sha256"] = challenge.canonical_sha(mutated)
        with self.assertRaisesRegex(bridge.BridgeError, "REPEATED_TARGET_ASSOCIATED_CALIBRATION_TOKEN"):
            bridge.prepare_basis_rows(mutated)

    def test_historical_native_basis_still_contains_direct_shortcut_vocabulary(self):
        actual = "\n".join(
            prompt.lower()
            for _, prompts in historical_basis.MATCHED_TRIPLETS
            for prompt in prompts.values()
        )
        direct = challenge.DIRECT_CALIBRATION_SHORTCUTS
        observed = {token for token in direct if token in set(actual.replace("/", " ").replace(".", " ").split())}
        self.assertTrue(
            observed,
            "historical native basis should remain classified as proxy-heavy until replaced",
        )


if __name__ == "__main__":
    unittest.main()
