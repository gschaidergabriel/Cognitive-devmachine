#!/usr/bin/env python3
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "run_6000_free_swarm_supervisor.sh"


class Supervisor6000SafeForge872(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SCRIPT.read_text(encoding="utf-8")

    def test_start_forge_selects_safe_wrapper(self):
        block = self.text.split("start_forge(){", 1)[1].split("\n}\n\nrefresh_root_results", 1)[0]
        self.assertIn('local x="$ROOT/tools/run_free_evidence_forge_safe.py"', block)
        self.assertIn("pgrep -f '[r]un_free_evidence_forge_safe.py'", block)
        self.assertNotIn('local x="$ROOT/tools/run_free_evidence_forge.py"', block)

    def test_start_forge_retires_legacy_process_before_spawn(self):
        block = self.text.split("start_forge(){", 1)[1].split("\n}\n\nrefresh_root_results", 1)[0]
        legacy = block.index("pgrep -f '[r]un_free_evidence_forge.py'")
        spawn = block.index('nohup python3 "$x"')
        self.assertLess(legacy, spawn)
        self.assertIn('kill "$pid"', block)

    def test_supervisor_status_distinguishes_safe_and_legacy(self):
        self.assertIn("'forge_running':running('run_free_evidence_forge_safe.py')", self.text)
        self.assertIn("'legacy_forge_running':running('run_free_evidence_forge.py')", self.text)
        self.assertIn("SAFE_FORGE_ONLY", self.text)

    def test_safe_wrapper_exists_in_repo(self):
        self.assertTrue((ROOT / "tools" / "run_free_evidence_forge_safe.py").is_file())
        self.assertTrue((ROOT / "tools" / "run_free_evidence_forge_safe_871.py").is_file())


if __name__ == "__main__":
    unittest.main()
