from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_6000_free_swarm_supervisor.sh"
ACTIVATION = ROOT / "tools/activate_6000_free_swarm.sh"
BACKFILL = ROOT / "tools/run_free_evidence_forge_backfill.py"


class SafeForge6000Wiring872(unittest.TestCase):
    def test_active_6000_supervisor_uses_backlog_first_safe_forge_only(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        start = text.index("start_forge(){")
        end = text.index("\n}\n\nrefresh_root_results", start) + 3
        block = text[start:end]
        self.assertIn('local x="$ROOT/tools/run_free_evidence_forge_backfill.py"', block)
        self.assertIn("pgrep -f '[r]un_free_evidence_forge.py'", block)
        self.assertIn("pgrep -f '[r]un_free_evidence_forge_safe.py'", block)
        self.assertIn("kill \"$pid\"", block)
        self.assertIn("pgrep -f '[r]un_free_evidence_forge_backfill.py'", block)
        self.assertIn("--backpressure-questions-per-cycle 0", block)
        self.assertNotIn('local x="$ROOT/tools/run_free_evidence_forge.py"', block)
        self.assertNotIn('local x="$ROOT/tools/run_free_evidence_forge_safe.py"', block)

    def test_backfill_entrypoint_delegates_to_existing_safe_forge_authority(self):
        text = BACKFILL.read_text(encoding="utf-8")
        self.assertIn("import run_free_evidence_forge_safe_871 as safe", text)
        self.assertIn("base = safe.base", text)
        self.assertIn("ingest_artifact_history", text)
        self.assertIn("conversion_pressure", text)
        self.assertIn("backpressure_questions_per_cycle", text)

    def test_supervisor_status_exposes_backlog_first_and_legacy_process_state(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("'forge_running':running('run_free_evidence_forge_backfill.py')", text)
        self.assertIn("'legacy_safe_forge_running':running('run_free_evidence_forge_safe.py')", text)
        self.assertIn("'legacy_forge_running':running('run_free_evidence_forge.py')", text)
        self.assertIn("'forge_entrypoint':'tools/run_free_evidence_forge_backfill.py'", text)
        self.assertIn("'forge_backpressure_policy':'BACKLOG_FIRST; DISCOVERY_ZERO_WHILE_PRESSURE_GTE_64'", text)
        self.assertIn("'forge_execution_policy':'CLAY_FORGE_EXECUTION_ADMISSION/v1'", text)
        self.assertIn("LEGACY_FORGE_TERMINATED; BACKLOG_FIRST_SAFE_FORGE_ONLY", text)

    def test_activation_preflights_backfill_and_safe_executor_and_cleans_old_forge(self):
        text = ACTIVATION.read_text(encoding="utf-8")
        for required in (
            "tools/forge_execution_admission_871.py",
            "tools/free_swarm_historical_backfill.py",
            "tools/run_free_evidence_forge_backfill.py",
            "tools/run_free_evidence_forge_safe_871.py",
            "tools/run_free_evidence_forge_safe.py",
            "tools/forge_evidence_credit_871.py",
            "tools/ingest_forge_accepts_into_distillery.py",
            "tools/run_forge_distillery_bridge_loop.py",
        ):
            self.assertIn(required, text)
        self.assertGreaterEqual(text.count("'tools/run_free_evidence_forge.py'"), 2)
        self.assertGreaterEqual(text.count("'tools/run_free_evidence_forge_safe.py'"), 2)
        self.assertIn("bash -n tools/run_6000_free_swarm_supervisor.sh", text)


if __name__ == "__main__":
    unittest.main()
