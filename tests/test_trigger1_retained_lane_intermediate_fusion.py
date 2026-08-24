from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1RetainedLaneIntermediateFusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = LAUNCHER.read_text(encoding="utf-8")

    def test_retained_compatibility_launcher_uses_intermediate_executor(self) -> None:
        self.assertIn("trigger1_local_qwen06_intermediate_execute.py", self.text)
        self.assertNotIn("trigger1_local_qwen06_midlayer_causal_execute.py", self.text)

    def test_pass_candidate_must_cross_intermediate_promotion_bridge(self) -> None:
        self.assertIn("trigger1_intermediate_promotion_bridge.py", self.text)
        self.assertIn("--result \"$INTERMEDIATE_RESULT\"", self.text)
        self.assertIn("--candidate \"$INTERMEDIATE_CANDIDATE\"", self.text)
        self.assertIn("--output \"$DIRECT_CANDIDATE\"", self.text)

    def test_nonzero_scientific_or_runtime_result_cannot_mint_direct_candidate(self) -> None:
        nonzero_gate = self.text.index('if [[ "$experiment_rc" -ne 0 ]]')
        bridge = self.text.index("trigger1_intermediate_promotion_bridge.py")
        self.assertLess(nonzero_gate, bridge)
        self.assertIn('rm -f "$DIRECT_CANDIDATE"', self.text)
        self.assertIn("BLOCKED_INTERMEDIATE_PROMOTION_BRIDGE", self.text)

    def test_workflow_compatibility_result_is_preserved(self) -> None:
        self.assertIn('COMPAT_RESULT="$OUT_DIR/trigger1_local_activation_api_result.json"', self.text)
        self.assertIn('cp "$INTERMEDIATE_RESULT" "$COMPAT_RESULT"', self.text)

    def test_provider_credential_fence_covers_hf_and_paid_llm_tokens(self) -> None:
        for name in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "TOGETHER_API_KEY",
            "HF_TOKEN",
            "HUGGING_FACE_HUB_TOKEN",
            "HUGGINGFACE_HUB_TOKEN",
        ):
            self.assertIn(name, self.text)
        self.assertIn("HF_HUB_DISABLE_IMPLICIT_TOKEN=1", self.text)


if __name__ == "__main__":
    unittest.main()
