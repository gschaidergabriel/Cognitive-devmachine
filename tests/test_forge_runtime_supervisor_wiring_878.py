from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools" / "run_6000_free_swarm_supervisor.sh"


class ForgeRuntimeSupervisorWiring878Tests(unittest.TestCase):
    def test_single_forge_path_is_identity_gated(self):
        source = SUPERVISOR.read_text(encoding="utf-8")
        start = source.index("start_forge(){")
        end = source.index("\n}\n\nrefresh_root_results", start)
        block = source[start:end]
        self.assertIn("verify_forge_runtime_identity_878.py", source)
        self.assertIn("CLAY_SUPERVISOR_GENERATION_NONCE", block)
        self.assertIn("forge-runtime-expectation.json", source)
        self.assertIn("FORGE_RUNTIME_IDENTITY_ADMISSION.json", source)
        self.assertIn("verify_running_forge", block)
        self.assertNotIn("pgrep -f '[r]un_free_evidence_forge_backfill.py' >/dev/null 2>&1 && return 0", block)

    def test_supervisor_status_surfaces_identity_admission(self):
        source = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("forge_runtime_identity_admission", source)
        self.assertIn("RESTART_FORGE_ON_RUNTIME_IDENTITY_MISMATCH", source)


if __name__ == "__main__":
    unittest.main()
