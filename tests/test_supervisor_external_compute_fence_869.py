from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class SupervisorExternalComputeFence869Tests(unittest.TestCase):
    def test_supervisor_starts_forge_with_zero_e2b_jobs(self) -> None:
        text=SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("--e2b-jobs-per-cycle 0", text)
        self.assertIn("--e2b-parallel 1", text)

    def test_preexisting_unfenced_forge_is_stopped_before_restart(self) -> None:
        text=SUPERVISOR.read_text(encoding="utf-8")
        loop=text.split("while (( $(date +%s) < DEADLINE )); do",1)[1]
        self.assertLess(loop.index("stop_unsafe_forge"), loop.index("start_forge"))
        self.assertIn('if [[ "$cmd" != *"--e2b-jobs-per-cycle 0"* ]]', text)

    def test_supervisor_provider_gate_uses_runtime_boundary_not_static_admission(self) -> None:
        text=SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("from provider_call_boundary import provider_call_is_allowed", text)
        self.assertNotIn('ADMISSION_TOOL="$ROOT/tools/free_provider_admission.py"', text)

    def test_blocked_provider_credentials_include_hf_and_together(self) -> None:
        text=SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("unset HF_TOKEN HUGGINGFACE_API_KEY", text)
        self.assertIn("unset TOGETHER_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
