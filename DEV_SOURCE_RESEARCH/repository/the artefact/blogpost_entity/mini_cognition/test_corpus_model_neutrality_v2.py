#!/usr/bin/env python3
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generate_sft_v2.py"
EXPECTED_TRAIN_SHA256 = "3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93"
EXPECTED_VALIDATION_SHA256 = "ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62"
FORBIDDEN_TRAINING_LITERALS = (
    "Qwen/Qwen2.5-0.5B",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen3.5-0.8B",
    "Together AI",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CorpusModelNeutralityV2(unittest.TestCase):
    def test_manifest_amputation_preserves_exact_training_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copy2(GEN, root / GEN.name)
            subprocess.run([sys.executable, str(root / GEN.name)], check=True, cwd=root, capture_output=True, text=True)

            train = root / "train_v2.jsonl"
            valid = root / "validation_v2.jsonl"
            manifest = json.loads((root / "corpus_manifest_v2.json").read_text(encoding="utf-8"))

            self.assertEqual(sha256(train), EXPECTED_TRAIN_SHA256)
            self.assertEqual(sha256(valid), EXPECTED_VALIDATION_SHA256)
            self.assertEqual(manifest["train_sha256"], EXPECTED_TRAIN_SHA256)
            self.assertEqual(manifest["validation_sha256"], EXPECTED_VALIDATION_SHA256)

            self.assertNotIn("base_primary", manifest)
            self.assertNotIn("base_ablation", manifest)
            self.assertEqual(manifest["model_binding_policy"], "campaign_external_not_corpus_identity")
            self.assertEqual(manifest["provider_binding_policy"], "campaign_external_not_corpus_identity")

            training_text = train.read_text(encoding="utf-8") + valid.read_text(encoding="utf-8")
            for literal in FORBIDDEN_TRAINING_LITERALS:
                self.assertNotIn(literal, training_text)


if __name__ == "__main__":
    unittest.main()
