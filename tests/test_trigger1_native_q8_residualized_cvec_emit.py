from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_native_q8_residualized_cvec_emit as emitter
from tools import trigger1_nuisance_residualize as residualizer

H = "a" * 64


def unit(index: int) -> list[float]:
    value = np.zeros(emitter.retained_emit.N_EMBD, dtype=np.float64)
    value[index] = 1.0
    return value.tolist()


def residualized_fixture() -> dict:
    a = np.zeros(emitter.retained_emit.N_EMBD, dtype=np.float64)
    n = np.zeros_like(a)
    u = np.zeros_like(a)
    a[0] = 1.0
    n[1] = 1.0
    u[0] = -1.0
    u[1] = -1.0
    payload = {
        "schema": residualizer.INPUT_SCHEMA,
        "dimension": emitter.retained_emit.N_EMBD,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "semantic_source_receipt_sha256": H,
        "nuisance_source_receipt_sha256": "b" * 64,
        "semantic_vectors": {
            "AFFIRMATIVE": a.tolist(),
            "NEGATIVE": n.tolist(),
            "NEUTRAL": u.tolist(),
        },
        "nuisance_vectors": {
            "CANONICAL_LABEL_LEXEME": [unit(10)],
            "SEMANTIC_SYNONYM_LEXICON": [unit(11)],
            "GENERIC_INSTRUCTION_COMPLIANCE": [unit(12)],
            "OUTPUT_CODE_IDENTITY": [unit(13)],
        },
    }
    return residualizer.residualize(payload)


class ResidualizedCvecEmitTests(unittest.TestCase):
    def test_valid_residualized_vectors_emit_exact_pinned_layout(self):
        value = residualized_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            result = emitter.emit(value, Path(tmp))
            self.assertEqual(set(emitter.CLASSES), set(result["target_cvecs"]))
            self.assertFalse(result["gain_selected_here"])
            self.assertFalse(result["model_executed"])
            expected_bytes = (emitter.retained_emit.N_LAYER - 1) * emitter.retained_emit.N_EMBD * 4
            for semantic, meta in result["target_cvecs"].items():
                self.assertEqual(expected_bytes, meta["cvec_bytes"])
                self.assertEqual([emitter.retained_emit.INJECTION_LAYER], meta["nonzero_layer_blocks"])
                self.assertTrue((Path(tmp) / meta["filename"]).is_file())

    def test_projected_vector_hash_tampering_fails_closed(self):
        value = residualized_fixture()
        value["projected_semantic_vector_sha256"]["AFFIRMATIVE"] = "0" * 64
        # Recompute the top-level result hash so only the vector-byte binding remains fatal.
        core = dict(value)
        core.pop("result_sha256")
        value["result_sha256"] = residualizer.canonical_sha(core)
        with self.assertRaisesRegex(emitter.ResidualizedEmitError, "PROJECTED_VECTOR_SHA256_MISMATCH"):
            emitter.validate_residualized(value)

    def test_failed_retained_norm_cannot_be_rehashed_into_emission(self):
        value = residualized_fixture()
        value["retained_semantic_subspace_norm_fraction"] = 0.01
        core = dict(value)
        core.pop("result_sha256")
        value["result_sha256"] = residualizer.canonical_sha(core)
        with self.assertRaisesRegex(emitter.ResidualizedEmitError, "SEMANTIC_RESIDUAL_TOO_SMALL"):
            emitter.validate_residualized(value)


if __name__ == "__main__":
    unittest.main()
