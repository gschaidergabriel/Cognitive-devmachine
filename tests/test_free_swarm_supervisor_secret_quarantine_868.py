from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class TestSupervisor868(unittest.TestCase):
    def test_secret_quarantine_precedes_children(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("clear_unadmitted_provider_secret_env\n  typed_admission_compat_flags", text)
        loop = text.index("while (( $(date +%s) < DEADLINE )); do")
        clear = text.index("clear_unadmitted_provider_secret_env", loop)
        for child in ("start_local_model", "start_distillery", "start_forge", "start_go_swarm_if_admitted"):
            self.assertLess(clear, text.index(child, loop))
        self.assertIn("unset_provider_family openrouter OPENROUTER_API_KEY", text)
        self.assertIn("unset TAVILY_API_KEY EXA_API_KEY", text)
        self.assertIn("compgen -v", text)

    def test_no_mixed_bundle_or_shell_source(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        for forbidden in (
            "/run/secrets/clay_provider.env",
            "/artifacts/.clay_provider.env",
            "/cache/clay_provider.env",
            "research_entity/private/API_TOKENS.env",
            "source \"$f\"",
            "eval \"$f\"",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn(
            "load_provider_secret_file groq \"$ROOT/research_entity/private/GROQ_API.env\"",
            text,
        )

    def test_v8_features_preserved(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        for required in (
            "start_local_model",
            "run_research_distillery_local.py",
            "run_free_evidence_forge.py",
            "CLAY_ENTITYOS_SWARM_SUPERVISOR/v8",
            "LOOPBACK_4B+PUBLIC_FORGE_CONTINUE_DURING_QUARANTINE",
        ):
            self.assertIn(required, text)

    def test_shell_syntax(self):
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
