#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class Go868InheritedProviderSecretFence(unittest.TestCase):
    def test_unadmitted_external_llm_credentials_are_cleared_before_children(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("clear_unadmitted_provider_secret_env", text)
        for provider in ("groq", "mistral", "nvidia", "openrouter"):
            self.assertIn(f"if ! provider_admitted {provider}; then", text)
        for name in (
            "GROQ_API_KEY", "MISTRAL_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY",
            "OPENROUTER_API_KEY",
        ):
            self.assertIn(name, text)
        self.assertIn("compgen -v", text)

        loop = text[text.index("while (( $(date +%s) < DEADLINE )); do"):]
        fence = loop.index("clear_unadmitted_provider_secret_env")
        for child_start in (
            "start_local_model", "start_dashboard", "start_distillery", "start_forge",
            "start_go_swarm_if_admitted",
        ):
            self.assertLess(fence, loop.index(child_start), child_start)

    def test_fence_does_not_expand_blocked_values_and_shell_is_valid(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("clear_unadmitted_provider_secret_env(){", 1)[1].split(
            "\n}\n\ntyped_admission_compat_flags", 1
        )[0]
        for forbidden in ("printenv", "env |", "${!", "source "):
            self.assertNotIn(forbidden, body)
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
