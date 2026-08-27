from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools/trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1MidlayerLowDiskCleanup872(unittest.TestCase):
    def test_low_disk_cleanup_preserves_current_output_and_removes_stale_siblings(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fakebin = tmp / "fakebin"
            fakebin.mkdir()
            fake_df = fakebin / "df"
            fake_df.write_text(
                "#!/usr/bin/env bash\n"
                "printf 'Filesystem 1024-blocks Used Available Capacity Mounted on\\n'\n"
                "printf 'fake 10000000 7500000 2500000 75%% /\\n'\n",
                encoding="utf-8",
            )
            fake_df.chmod(0o755)

            home = tmp / "home"
            runner_temp = tmp / "runner"
            cache = tmp / "cache"
            home.mkdir()
            runner_temp.mkdir()
            out = runner_temp / "clay-trigger1-v2-current"
            stale_v2 = runner_temp / "clay-trigger1-v2-stale"
            stale_qwen = runner_temp / "clay-trigger1-qwen06-stale"
            out.mkdir()
            stale_v2.mkdir()
            stale_qwen.mkdir()
            (out / "evidence-in-progress.txt").write_text("preserve\n", encoding="utf-8")
            (stale_v2 / "stale.txt").write_text("delete\n", encoding="utf-8")
            (stale_qwen / "stale.txt").write_text("delete\n", encoding="utf-8")

            env = os.environ.copy()
            env["PATH"] = f"{fakebin}:{env['PATH']}"
            env["HOME"] = str(home)
            env["RUNNER_TEMP"] = str(runner_temp)
            env["CLAY_TRIGGER1_LOCAL_CACHE"] = str(cache)
            env.pop("HF_HOME", None)

            proc = subprocess.run(
                ["bash", str(LAUNCHER), str(out)],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=30,
            )

            self.assertEqual(proc.returncode, 3, proc.stderr)
            self.assertTrue(out.is_dir(), "current evidence directory must survive its own cleanup")
            self.assertTrue((out / "evidence-in-progress.txt").is_file())
            self.assertFalse(stale_v2.exists(), "stale V2 sibling should be cleaned")
            self.assertFalse(stale_qwen.exists(), "stale legacy Qwen sibling should be cleaned")

            preflight = json.loads((out / "disk_preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(preflight["available_kb_before"], 2500000)
            self.assertEqual(preflight["available_kb_after"], 2500000)
            self.assertIs(preflight["current_output_preserved"], True)

            result = json.loads((out / "trigger1_local_activation_api_result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "BLOCKED_INSUFFICIENT_FREE_DISK_AFTER_BOUNDED_CLEANUP")
            self.assertIs(result["current_output_preserved"], True)
            self.assertIs(result["zero_provider_billing"], True)
            self.assertIs(result["external_provider_credentials_read"], False)


if __name__ == "__main__":
    unittest.main()
