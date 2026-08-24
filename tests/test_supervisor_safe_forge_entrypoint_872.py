from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools" / "run_6000_free_swarm_supervisor.sh"


class SupervisorSafeForgeEntrypoint872(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SUPERVISOR.read_text(encoding="utf-8")
        start = cls.text.index("start_forge(){")
        end = cls.text.index("\n}\n\nrefresh_root_results", start) + 2
        cls.start_forge = cls.text[start:end]

    def test_long_run_starts_safe_wrapper(self):
        self.assertIn('local x="$ROOT/tools/run_free_evidence_forge_safe_871.py"', self.start_forge)
        self.assertIn('nohup python3 "$x"', self.start_forge)

    def test_legacy_base_is_retired_before_safe_start(self):
        self.assertIn('pgrep -f "$ROOT/tools/[r]un_free_evidence_forge.py"', self.start_forge)
        self.assertIn('kill "$pid"', self.start_forge)

    def test_supervisor_status_observes_safe_entrypoint(self):
        self.assertIn("'forge_running':running('run_free_evidence_forge_safe_871.py')", self.text)
        self.assertIn("'forge_entrypoint':'tools/run_free_evidence_forge_safe_871.py'", self.text)
        self.assertIn("'legacy_base_forge_running':running('/tools/run_free_evidence_forge.py')", self.text)

    def test_start_forge_does_not_launch_base_entrypoint(self):
        self.assertNotIn('local x="$ROOT/tools/run_free_evidence_forge.py"', self.start_forge)


if __name__ == "__main__":
    unittest.main()
