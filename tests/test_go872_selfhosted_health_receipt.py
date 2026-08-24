import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "go872_selfhosted_health_receipt.py"
spec = importlib.util.spec_from_file_location("health", MODULE_PATH)
health = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(health)


class HealthReceiptTests(unittest.TestCase):
    def test_provider_env_names_never_include_values(self):
        env = {"GROQ_API_KEY": "secret-value", "HF_TOKEN": "hf-secret", "PATH": "/bin", "NOT_A_PROVIDER_KEY": "safe"}
        self.assertEqual(health.provider_env_names(env), ["GROQ_API_KEY", "HF_TOKEN"])

    def test_qwen_disk_threshold_matches_launcher_contract(self):
        self.assertEqual(health.QWEN_MIN_AVAILABLE_KB, 3_000_000)

    def test_receipt_is_credit_zero_and_fail_closed_on_dirty_source(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "tools").mkdir()
            for name in ("trigger1_local_qwen06_midlayer_causal.sh", "trigger1_local_qwen06_midlayer_causal_execute.py", "run_go871_forge_distillery_runtime_gate.py"):
                (repo / "tools" / name).write_text("x", encoding="utf-8")
            out = repo / "receipt.json"
            responses = [(0, "abc", ""), (0, "tree", ""), (0, " M dirty", "")]
            with mock.patch.object(health, "run_text", side_effect=responses), \
                 mock.patch.object(health, "available_kb", return_value=4_000_000), \
                 mock.patch.object(health.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
                 mock.patch.dict(os.environ, {"RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "runner"}, clear=False):
                payload = health.build_receipt(repo, out)
            self.assertFalse(payload["readiness"]["bridge_health_pass"])
            self.assertEqual(payload["credit"]["runtime_credit_minted"], 0)
            self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
