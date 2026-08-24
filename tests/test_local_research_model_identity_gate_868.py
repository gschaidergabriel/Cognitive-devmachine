from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/local_research_model_server.sh"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LocalResearchModelIdentityGate868(unittest.TestCase):
    def make_fixture(self, td: Path):
        model = td / "model.gguf"
        model.write_bytes(b"GGUF-exact-test-bytes-v1")
        call_log = td / "runtime-args.json"
        runtime = td / "llama-server"
        runtime.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "open(os.environ['FAKE_RUNTIME_CALL_LOG'],'w',encoding='utf-8').write(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)
        artifacts = td / "artifacts"
        env = os.environ.copy()
        env.update({
            "CLAY_LLAMA_SERVER_BIN": str(runtime),
            "CLAY_LLAMA_SERVER_SHA256": digest(runtime),
            "CLAY_LOCAL_MODEL_FILE": str(model),
            "CLAY_LOCAL_MODEL_SHA256": digest(model),
            "CLAY_LOCAL_RESEARCH_ARTIFACT_ROOT": str(artifacts),
            "CLAY_LOCAL_RESEARCH_DISABLE_PORT_PROBE": "1",
            "FAKE_RUNTIME_CALL_LOG": str(call_log),
        })
        return model, runtime, call_log, artifacts, env

    def run_gate(self, env: dict[str, str]):
        return subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, env=env, text=True, capture_output=True)

    def test_source_contains_no_remote_materialization_path(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("git clone", " -hf ", "huggingface", "Qwen/Qwen", "integrate.api", "openrouter.ai"):
            self.assertNotIn(forbidden, text)
        for required in ("CLAY_LLAMA_SERVER_SHA256", "CLAY_LOCAL_MODEL_SHA256", 'exec "$RUNTIME_BIN"', '-m "$MODEL_FILE"'):
            self.assertIn(required, text)

    def test_exact_runtime_and_model_bytes_execute_once_with_bounded_state(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            model, runtime, call_log, artifacts, env = self.make_fixture(td)
            proc = self.run_gate(env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            args = json.loads(call_log.read_text(encoding="utf-8"))
            self.assertEqual(args[0:2], ["-m", str(model)])
            self.assertIn("--host", args)
            self.assertEqual(args[args.index("--host") + 1], "127.0.0.1")
            state = json.loads((artifacts / "local-model.json").read_text(encoding="utf-8"))
            self.assertEqual(state["schema"], "CLAY_LOCAL_RESEARCH_MODEL/v2")
            self.assertEqual(state["runtime_sha256"], digest(runtime))
            self.assertEqual(state["model_sha256"], digest(model))
            self.assertFalse(state["remote_download_performed_by_execution_path"])
            self.assertFalse(state["provider_secret_lookup_performed_by_execution_path"])
            self.assertEqual(state["loader_consumption_evidence"], "PENDING_RUNTIME_RECEIPT")
            self.assertEqual(state["runtime_credit"], 0)

    def test_model_hash_mismatch_fails_before_runtime(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, _, call_log, _, env = self.make_fixture(td)
            env["CLAY_LOCAL_MODEL_SHA256"] = "0" * 64
            proc = self.run_gate(env)
            self.assertEqual(proc.returncode, 64)
            self.assertIn("MODEL_SHA256_MISMATCH", proc.stderr)
            self.assertFalse(call_log.exists())

    def test_runtime_hash_mismatch_fails_before_runtime(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, _, call_log, _, env = self.make_fixture(td)
            env["CLAY_LLAMA_SERVER_SHA256"] = "f" * 64
            proc = self.run_gate(env)
            self.assertEqual(proc.returncode, 64)
            self.assertIn("RUNTIME_SHA256_MISMATCH", proc.stderr)
            self.assertFalse(call_log.exists())

    def test_missing_or_malformed_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, _, call_log, _, env = self.make_fixture(td)
            for key, value, marker in (
                ("CLAY_LOCAL_MODEL_SHA256", "", "MODEL_SHA256_REQUIRED"),
                ("CLAY_LLAMA_SERVER_SHA256", "not-a-sha", "RUNTIME_SHA256_REQUIRED"),
            ):
                case_env = env.copy()
                case_env[key] = value
                proc = self.run_gate(case_env)
                self.assertEqual(proc.returncode, 64)
                self.assertIn(marker, proc.stderr)
                self.assertFalse(call_log.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
