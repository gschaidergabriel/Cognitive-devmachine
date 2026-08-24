from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools" / "run_24h_entityos_swarm_supervisor.sh"
FORGE = ROOT / "tools" / "run_free_evidence_forge.py"


class SupervisorE2BFreeOnlyFence868Tests(unittest.TestCase):
    def test_supervisor_starts_forge_with_zero_e2b_jobs(self) -> None:
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("--e2b-jobs-per-cycle 0", text)
        self.assertIn("--e2b-parallel 1", text)

    def test_preexisting_unfenced_forge_is_stopped_before_restart(self) -> None:
        text = SUPERVISOR.read_text(encoding="utf-8")
        loop = text.split("while (( $(date +%s) < DEADLINE )); do", 1)[1]
        self.assertLess(loop.index("stop_unsafe_forge"), loop.index("start_forge"))
        self.assertIn('if [[ "$cmd" != *"--e2b-jobs-per-cycle 0"* ]]', text)
        self.assertIn('kill "$pid"', text)

    def test_status_policy_exposes_e2b_quarantine(self) -> None:
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("E2B_EXTERNAL_SANDBOX_QUARANTINED_PENDING_TYPED_FREE_ADMISSION", text)

    def test_zero_job_budget_makes_current_forge_e2b_selection_empty(self) -> None:
        text = FORGE.read_text(encoding="utf-8")
        self.assertIn('[:args.e2b_jobs_per_cycle]', text)
        self.assertIn('if github: await asyncio.gather', text)
        self.assertIn('p.add_argument("--e2b-jobs-per-cycle",type=int,default=8)', text)


if __name__ == "__main__":
    unittest.main()
