from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
MIN_PASSES = 64


class HistoricalBackfillCapsulePolicy878Tests(unittest.TestCase):
    def test_capsule_installs_shared_completion_policy_in_fresh_process(self):
        """The evidence-producing capsule must not retain legacy core semantics."""
        code = f"""
import sys
sys.path.insert(0, {str(TOOLS)!r})
import free_swarm_historical_backfill as backfill
import run_free_swarm_historical_backfill_capsule_878 as capsule
print(backfill.MAX_PASSES)
print(backfill._record_batch_progress.__module__)
print(capsule.ingest_artifact_history is backfill.ingest_artifact_history)
"""
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.strip().splitlines()
        self.assertGreaterEqual(int(lines[-3]), MIN_PASSES)
        self.assertEqual(lines[-2], "free_swarm_backfill_exhaustiveness_878")
        self.assertEqual(lines[-1], "True")


if __name__ == "__main__":
    unittest.main()
