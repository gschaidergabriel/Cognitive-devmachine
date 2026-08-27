from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1LauncherAtomicLeaseFenceTests(unittest.TestCase):
    def test_github_actions_without_admitted_lease_blocks_before_runtime_setup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "out"
            home = root / "home"
            runner_temp = root / "runner-temp"
            home.mkdir()
            runner_temp.mkdir()

            env = os.environ.copy()
            env["GITHUB_ACTIONS"] = "true"
            env.pop("TRIGGER1_LEASE_ADMITTED", None)
            env["HOME"] = str(home)
            env["RUNNER_TEMP"] = str(runner_temp)

            proc = subprocess.run(
                ["bash", str(LAUNCHER), str(out)],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )

            self.assertEqual(proc.returncode, 42, msg=proc.stderr)
            result_path = out / "trigger1_local_activation_api_result.json"
            self.assertTrue(result_path.is_file())
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["schema"], "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1")
            self.assertEqual(result["status"], "BLOCKED_CANONICAL_ATOMIC_LEASE_NOT_ADMITTED")
            self.assertEqual(
                result["reason"],
                "GITHUB_ACTIONS_TRIGGER1_REQUIRES_WORKFLOW_ATOMIC_LEASE_GATE",
            )
            self.assertIs(result["unusual_experiment_executed"], False)
            self.assertIs(result["zero_provider_billing"], True)
            self.assertEqual(result["provider_network_calls"], 0)
            self.assertEqual(result["credit_scope"], "NONE")
            self.assertFalse((out / "disk_preflight.json").exists())
            self.assertFalse((home / ".cache" / "clay-trigger1-local").exists())


if __name__ == "__main__":
    unittest.main()
