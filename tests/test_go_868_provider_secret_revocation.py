#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class ProviderSecretRevocationTests(unittest.TestCase):
    def _function_text(self) -> str:
        text = SUPERVISOR.read_text(encoding="utf-8")
        start = text.index("clear_unadmitted_provider_secret_env(){")
        end = text.index("\n}\n\ntyped_admission_compat_flags", start) + 2
        return text[start:end]

    def test_revocation_scrub_runs_before_compat_flags_and_secret_loading(self) -> None:
        text = SUPERVISOR.read_text(encoding="utf-8")
        required_order = (
            "clear_unadmitted_provider_secret_env\n"
            "  typed_admission_compat_flags\n"
            "  load_admitted_secret_sources"
        )
        self.assertIn(required_order, text)
        self.assertIn("compgen -v", text)
        self.assertIn("OPENROUTER_API_KEY", text)
        self.assertIn("TAVILY_API_KEY EXA_API_KEY", text)
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_exact_scrub_function_preserves_admitted_and_removes_revoked_without_value_scan(self) -> None:
        function = self._function_text()
        script = f"""
set -Eeuo pipefail
provider_admitted() {{ [[ "$1" == "groq" ]]; }}
{function}
export GROQ_API_KEY='keep-admitted'
export GROQ_API_KEY_7='keep-admitted-suffix'
export MISTRAL_API_KEY='drop-revoked'
export NVIDIA_API_KEY='drop-revoked'
export NVIDIA_API_KEY_9='drop-revoked-suffix'
export OPENROUTER_API_KEY='drop-revoked'
export TAVILY_API_KEY='drop-untyped'
export EXA_API_KEY='drop-untyped'
export CLAY_UNRELATED='preserve'
clear_unadmitted_provider_secret_env
[[ "${{GROQ_API_KEY:-}}" == 'keep-admitted' ]]
[[ "${{GROQ_API_KEY_7:-}}" == 'keep-admitted-suffix' ]]
[[ -z "${{MISTRAL_API_KEY:-}}" ]]
[[ -z "${{NVIDIA_API_KEY:-}}" ]]
[[ -z "${{NVIDIA_API_KEY_9:-}}" ]]
[[ -z "${{OPENROUTER_API_KEY:-}}" ]]
[[ -z "${{TAVILY_API_KEY:-}}" ]]
[[ -z "${{EXA_API_KEY:-}}" ]]
[[ "${{CLAY_UNRELATED:-}}" == 'preserve' ]]
"""
        proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
