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


def make_file(repo: Path, rel: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n", encoding="utf-8")


def clean_git_responses():
    return [(0, "a" * 40, ""), (0, "b" * 40, ""), (0, "", "")]


class HealthReceiptTests(unittest.TestCase):
    def test_provider_env_names_never_include_values(self):
        env = {"GROQ_API_KEY": "secret-value", "HF_TOKEN": "hf-secret", "PATH": "/bin", "NOT_A_PROVIDER_KEY": "safe"}
        self.assertEqual(health.provider_env_names(env), ["GROQ_API_KEY", "HF_TOKEN"])

    def test_qwen_disk_threshold_matches_launcher_contract(self):
        self.assertEqual(health.QWEN_MIN_AVAILABLE_KB, 3_000_000)

    def test_receipt_is_credit_zero_and_fail_closed_on_dirty_source(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            for rel in health.QWEN_EFFECTIVE_CHAIN:
                make_file(repo, rel)
            make_file(repo, "tools/run_go871_forge_distillery_runtime_gate.py")
            out = repo / "receipt.json"
            responses = [(0, "a" * 40, ""), (0, "b" * 40, ""), (0, " M dirty", "")]
            with mock.patch.object(health, "run_text", side_effect=responses), \
                 mock.patch.object(health, "available_kb", return_value=4_000_000), \
                 mock.patch.object(health.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
                 mock.patch.dict(os.environ, {"RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "runner"}, clear=False):
                payload = health.build_receipt(repo, out)
            self.assertFalse(payload["readiness"]["bridge_health_pass"])
            self.assertFalse(payload["readiness"]["qwen_preflight_ready"])
            self.assertEqual(payload["credit"]["runtime_credit_minted"], 0)
            self.assertTrue(out.is_file())

    def test_qwen_preflight_fails_closed_when_only_historical_executor_exists(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            make_file(repo, "tools/trigger1_local_qwen06_midlayer_causal.sh")
            make_file(repo, "tools/trigger1_local_qwen06_midlayer_causal_execute.py")
            make_file(repo, "tools/run_go871_forge_distillery_runtime_gate.py")
            out = repo / "receipt.json"
            with mock.patch.object(health, "run_text", side_effect=clean_git_responses()), \
                 mock.patch.object(health, "available_kb", return_value=4_000_000), \
                 mock.patch.object(health.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
                 mock.patch.dict(os.environ, {"RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "runner"}, clear=False):
                payload = health.build_receipt(repo, out)
            self.assertTrue(payload["readiness"]["bridge_health_pass"])
            self.assertFalse(payload["readiness"]["qwen_preflight_ready"])
            self.assertFalse(payload["frontier_sources"]["qwen_effective_chain_complete"])
            self.assertNotIn("tools/trigger1_local_qwen06_midlayer_causal_execute.py", health.QWEN_EFFECTIVE_CHAIN)

    def test_qwen_preflight_requires_complete_effective_strongest_intermediate_chain(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            for rel in health.QWEN_EFFECTIVE_CHAIN:
                make_file(repo, rel)
            make_file(repo, "tools/run_go871_forge_distillery_runtime_gate.py")
            out = repo / "receipt.json"
            with mock.patch.object(health, "run_text", side_effect=clean_git_responses()), \
                 mock.patch.object(health, "available_kb", return_value=4_000_000), \
                 mock.patch.object(health.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
                 mock.patch.dict(os.environ, {"RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "runner"}, clear=False):
                payload = health.build_receipt(repo, out)
            self.assertTrue(payload["readiness"]["bridge_health_pass"])
            self.assertTrue(payload["readiness"]["qwen_preflight_ready"])
            self.assertTrue(payload["frontier_sources"]["qwen_effective_chain_complete"])
            self.assertEqual(set(payload["frontier_sources"]["qwen_effective_chain_presence"]), set(health.QWEN_EFFECTIVE_CHAIN))

    def test_missing_one_effective_qwen_source_blocks_qwen_only(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            for rel in health.QWEN_EFFECTIVE_CHAIN:
                if rel != "tools/trigger1_intermediate_promotion_bridge.py":
                    make_file(repo, rel)
            make_file(repo, "tools/run_go871_forge_distillery_runtime_gate.py")
            out = repo / "receipt.json"
            with mock.patch.object(health, "run_text", side_effect=clean_git_responses()), \
                 mock.patch.object(health, "available_kb", return_value=4_000_000), \
                 mock.patch.object(health.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
                 mock.patch.dict(os.environ, {"RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "runner"}, clear=False):
                payload = health.build_receipt(repo, out)
            self.assertTrue(payload["readiness"]["bridge_health_pass"])
            self.assertFalse(payload["readiness"]["qwen_preflight_ready"])
            self.assertTrue(payload["readiness"]["forge_preflight_ready"])
            self.assertFalse(payload["frontier_sources"]["qwen_effective_chain_presence"]["tools/trigger1_intermediate_promotion_bridge.py"])


if __name__ == "__main__":
    unittest.main()
