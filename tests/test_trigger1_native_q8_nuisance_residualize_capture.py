from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_native_q8_nuisance_residualize_capture as nuisance


class NativeQ8NuisanceResidualizeCaptureTests(unittest.TestCase):
    def test_design_contains_exact_required_calibration_only_nuisance_families(self):
        design = nuisance.nuisance_design()
        self.assertEqual("CALIBRATION", design["fit_split"])
        self.assertTrue(design["frozen_before_semantic_holdout"])
        self.assertFalse(design["semantic_holdout_rows_present"])
        self.assertEqual(
            set(nuisance.REQUIRED_FAMILIES),
            {row["nuisance_family"] for row in design["rows"]},
        )
        self.assertTrue(all(row["purpose"] == "NUISANCE_AXIS_CALIBRATION_ONLY" for row in design["rows"]))
        self.assertEqual(len(design["rows"]), len({row["row_id"] for row in design["rows"]}))
        self.assertEqual(len(design["rows"]), len({row["prompt_sha256"] for row in design["rows"]}))

    def test_deliberate_shortcut_words_are_quarantined_to_nuisance_design(self):
        design = nuisance.nuisance_design()
        text = "\n".join(row["prompt"].lower() for row in design["rows"])
        self.assertIn("affirmative", text)
        self.assertIn("reject", text)
        self.assertIn("comply", text)
        self.assertIn("opaque output symbol", text)
        self.assertTrue(all("CALIBRATION_ONLY" in row["purpose"] for row in design["rows"]))

    def test_synthetic_native_observations_derive_all_nuisance_vectors(self):
        design = nuisance.nuisance_design()
        observations = {}
        for index, row in enumerate(design["rows"]):
            # Deterministic nondegenerate synthetic activation. Different row identities map
            # to distinct directions; no model/runtime credit is implied by this unit fixture.
            vector = np.zeros(nuisance.native_donor.N_EMBD, dtype=np.float64)
            vector[index % nuisance.native_donor.N_EMBD] = float(index + 1)
            vector[(index + 37) % nuisance.native_donor.N_EMBD] = 0.25 * float(index + 1)
            observations[row["row_id"]] = {"primary_activation": vector.tolist()}
        out = nuisance.derive_nuisance_vectors(design, observations)
        self.assertEqual(set(nuisance.REQUIRED_FAMILIES), set(out))
        self.assertEqual(6, len(out["CANONICAL_LABEL_LEXEME"]))
        self.assertEqual(9, len(out["SEMANTIC_SYNONYM_LEXICON"]))
        self.assertEqual(3, len(out["GENERIC_INSTRUCTION_COMPLIANCE"]))
        self.assertEqual(6, len(out["OUTPUT_CODE_IDENTITY"]))
        for family in nuisance.REQUIRED_FAMILIES:
            self.assertTrue(all(np.linalg.norm(np.asarray(v)) > 0 for v in out[family]))

    def test_missing_observation_fails_case_universe(self):
        design = nuisance.nuisance_design()
        observations = {}
        for index, row in enumerate(design["rows"]):
            vector = np.zeros(nuisance.native_donor.N_EMBD, dtype=np.float64)
            vector[index] = 1.0
            observations[row["row_id"]] = {"primary_activation": vector.tolist()}
        observations.pop(next(iter(observations)))
        with self.assertRaisesRegex(nuisance.NuisanceCaptureError, "CASE_UNIVERSE_MISMATCH"):
            nuisance.derive_nuisance_vectors(design, observations)


if __name__ == "__main__":
    unittest.main()
