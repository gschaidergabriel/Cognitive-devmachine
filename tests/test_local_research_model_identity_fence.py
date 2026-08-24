from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/local_research_model_server.sh"
MODEL = "Qwen/Qwen3-4B-GGUF:Q4_K_M"


@unittest.skipUnless(
    Path("/proc/self/exe").exists() and shutil.which("git") and shutil.which("sleep"),
    "Linux /proc, git, and sleep are required",
)
class LocalResearchModelIdentityFenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.tools = self.root / "tools"
        self.tools.mkdir(parents=True)
        self.script = self.tools / "local_research_model_server.sh"
        shutil.copy(SCRIPT, self.script)
        self.script.chmod(0o755)

        self.cache = self.root / "cache"
        self.src = self.cache / "llama.cpp"
        self.build = self.src / "build/bin"
        self.build.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.src, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.src, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.src, check=True)
        (self.src / "tracked").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked"], cwd=self.src, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.src, check=True)
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.src, text=True).strip()

        shutil.copy(shutil.which("sleep"), self.build / "llama-server")
        (self.build / "llama-server").chmod(0o755)
        self.proc = subprocess.Popen([str(self.build / "llama-server"), "60"])

        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.state_dir = self.root / "state"
        self.state_dir.mkdir()
        self.state = self.state_dir / "local-model.json"
        exe_sha = hashlib.sha256((self.build / "llama-server").read_bytes()).hexdigest()
        self.base_state = {
            "schema": "CLAY_LOCAL_RESEARCH_MODEL/v2",
            "state": "READY_IDENTITY_OBSERVED",
            "backend": "llama.cpp",
            "backend_commit": self.commit,
            "runtime_process_bound_to_build_path": True,
            "server_pid": self.proc.pid,
            "server_exe_sha256": exe_sha,
            "model_selector": MODEL,
            "live_model_id": MODEL,
            "model_sha256_post_load_path": "a" * 64,
        }
        self._write_state(self.base_state)
        self._write_fake_curl(MODEL)

    def tearDown(self) -> None:
        self.proc.terminate()
        self.proc.wait(timeout=5)
        self.td.cleanup()

    def _write_state(self, payload: dict[str, object]) -> None:
        self.state.write_text(json.dumps(payload), encoding="utf-8")

    def _write_fake_curl(self, live_model: str) -> None:
        curl = self.bin / "curl"
        curl.write_text(
            "#!/usr/bin/env bash\n"
            "url=\"${@: -1}\"\n"
            "if [[ \"$url\" == */health ]]; then echo ok; exit 0; fi\n"
            f"if [[ \"$url\" == */v1/models ]]; then echo '{{\"data\":[{{\"id\":\"{live_model}\"}}]}}'; exit 0; fi\n"
            "exit 1\n",
            encoding="utf-8",
        )
        curl.chmod(0o755)

    def _run_script(self) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update({
            "PATH": str(self.bin) + os.pathsep + env["PATH"],
            "CLAY_LOCAL_MODEL_CACHE": str(self.cache),
            "CLAY_LOCAL_RESEARCH_STATE_DIR": str(self.state_dir),
        })
        return subprocess.run(["bash", str(self.script)], env=env, text=True, capture_output=True, timeout=10)

    def test_exact_existing_identity_can_be_reused(self) -> None:
        proc = self._run_script()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("LOCAL_RESEARCH_MODEL_ALREADY_READY_IDENTITY_BOUND", proc.stdout)

    def test_healthy_wrong_live_model_fails_closed(self) -> None:
        self._write_fake_curl("WRONG/MODEL")
        proc = self._run_script()
        self.assertEqual(proc.returncode, 21)
        self.assertIn("LOCAL_RESEARCH_MODEL_HEALTHY_BUT_IDENTITY_UNVERIFIED", proc.stderr)

    def test_stale_state_commit_fails_closed(self) -> None:
        payload = dict(self.base_state)
        payload["backend_commit"] = "0" * 40
        self._write_state(payload)
        proc = self._run_script()
        self.assertEqual(proc.returncode, 21)
        self.assertIn("LOCAL_RESEARCH_MODEL_HEALTHY_BUT_IDENTITY_UNVERIFIED", proc.stderr)


if __name__ == "__main__":
    unittest.main()
