from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1StrongestLauncherCredentialFence872Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = LAUNCHER.read_text(encoding="utf-8")

    def test_strongest_intermediate_bridge_is_retained_compatibility_entrypoint(self) -> None:
        self.assertIn("trigger1_strongest_intermediate_bridge_execute.py", self.text)
        self.assertNotIn("trigger1_local_qwen06_midlayer_causal_execute.py\"", self.text)

    def test_external_llm_provider_credentials_are_scrubbed(self) -> None:
        for name in (
            "OPENAI_API_KEY",
            "OPENAI_API_KEYS",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEYS",
            "GROQ_API_KEY",
            "MISTRAL_API_KEY",
            "NVIDIA_API_KEY",
            "OPENROUTER_API_KEY",
            "TOGETHER_API_KEY",
        ):
            self.assertIn(name, self.text)

    def test_hugging_face_implicit_credentials_are_disabled(self) -> None:
        for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
            self.assertIn(name, self.text)
        self.assertIn("HF_HUB_DISABLE_IMPLICIT_TOKEN=1", self.text)
        self.assertIn('HF_TOKEN_PATH="$OUT_DIR/no-hf-token"', self.text)
        self.assertIn('rm -f "$HF_TOKEN_PATH"', self.text)

    def test_low_disk_cleanup_preserves_current_evidence_directory(self) -> None:
        self.assertIn("OUT_DIR_CANONICAL", self.text)
        self.assertIn('candidate_canonical" == "$OUT_DIR_CANONICAL', self.text)
        self.assertIn('"current_output_preserved":true', self.text)


if __name__ == "__main__":
    unittest.main()
