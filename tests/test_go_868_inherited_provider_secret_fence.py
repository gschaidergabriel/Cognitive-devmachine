#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class Go868InheritedProviderSecretFence(unittest.TestCase):
    def test_blocked_provider_secret_names_are_cleared_before_child_start(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("clear_unadmitted_provider_secret_env", text)
        for provider in ("groq", "mistral", "nvidia", "openrouter"):
            self.assertIn(f"if ! provider_admitted {provider}; then", text)
        for blocked_name in (
            "GROQ_API_KEY", "MISTRAL_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY",
            "OPENROUTER_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY",
        ):
            self.assertIn(blocked_name, text)
        self.assertIn("compgen -v", text)
        loop = text[text.index("while (( $(date +%s) < DEADLINE )); do"):]
        fence = loop.index("clear_unadmitted_provider_secret_env")
        self.assertLess(fence, loop.index("start_dashboard"))
        self.assertLess(fence, loop.index("start_distillery"))
        self.assertLess(fence, loop.index("start_forge"))
        self.assertLess(fence, loop.index("start_go_swarm_if_admitted"))

    def test_fence_is_name_only_and_shell_syntax_is_valid(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        function = text.split("clear_unadmitted_provider_secret_env(){", 1)[1].split("\n}\n\ntyped_admission_compat_flags", 1)[0]
        self.assertNotIn("printenv", function)
        self.assertNotIn("env |", function)
        self.assertNotIn("${!", function)
        self.assertNotIn("source ", function)
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
