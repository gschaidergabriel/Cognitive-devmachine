from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import trigger1_attested_local_qwen_api as envelope
import trigger1_source_attestation as attest

HEX64 = "a" * 64
HEAD40 = "b" * 40
TREE40 = "c" * 40


class Trigger1SourceExecutionEnvelopeTests(unittest.TestCase):
    def test_clean_porcelain_status_is_explicit_false_and_digest_bound(self):
        def fake_git(_root: Path, *args: str, strip: bool = True) -> str:
            if args == ("rev-parse", "HEAD"):
                return HEAD40
            if args == ("rev-parse", "HEAD^{tree}"):
                return TREE40
            if args == ("status", "--porcelain=v1", "--untracked-files=all"):
                self.assertFalse(strip)
                return ""
            raise AssertionError(args)

        with mock.patch.object(attest, "_git", side_effect=fake_git):
            identity = attest.exact_source_identity(ROOT)
        self.assertEqual(HEAD40, identity["repo_head"])
        self.assertEqual(TREE40, identity["repo_tree"])
        self.assertFalse(identity["repo_dirty"])
        self.assertEqual(hashlib.sha256(b"").hexdigest(), identity["repo_status_sha256"])

    def test_require_clean_source_rejects_dirty_checkout(self):
        dirty = {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": True,
            "repo_status_sha256": HEX64,
        }
        with mock.patch.object(attest, "exact_source_identity", return_value=dirty):
            with self.assertRaisesRegex(RuntimeError, "DIRTY_SOURCE_TREE_FAIL_CLOSED"):
                attest.require_clean_source(ROOT)

    def test_sensitive_env_names_strip_provider_and_hf_tokens(self):
        self.assertTrue(envelope.sensitive_env_name("OPENROUTER_API_KEY"))
        self.assertTrue(envelope.sensitive_env_name("HF_TOKEN"))
        self.assertFalse(envelope.sensitive_env_name("HF_HOME"))

    def test_output_dir_must_be_fresh_and_outside_repo(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as out_td:
            old_root = envelope.ROOT
            envelope.ROOT = Path(repo_td)
            try:
                with self.assertRaisesRegex(RuntimeError, "OUTPUT_DIR_MUST_BE_OUTSIDE_REPO"):
                    envelope.require_fresh_output(Path(repo_td) / "run")
                stale = Path(out_td) / "trigger1_direct_steering_candidate.json"
                stale.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "PRIOR_TRIGGER1_EVIDENCE"):
                    envelope.require_fresh_output(Path(out_td))
            finally:
                envelope.ROOT = old_root

    def test_declared_result_digest_fails_closed_on_mutation(self):
        result = {"schema": "x", "value": 1}
        result["result_sha256"] = envelope.canonical_sha(result)
        envelope.verify_declared_result(result)
        result["value"] = 2
        with self.assertRaisesRegex(RuntimeError, "RESULT_DECLARED_SHA256_MISMATCH"):
            envelope.verify_declared_result(result)

    def test_loopback_endpoint_rejects_remote_host(self):
        envelope.require_loopback_endpoint("http://127.0.0.1:8080/v1/jspace/logits")
        envelope.require_loopback_endpoint("http://localhost:8080/v1/jspace/logits")
        with self.assertRaisesRegex(RuntimeError, "NON_LOOPBACK_ENDPOINT_FAIL_CLOSED"):
            envelope.require_loopback_endpoint("http://example.com/v1/jspace/logits")

    def test_guard_blocks_provider_and_hf_credential_lookup_and_remote_dns(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            audit = td / "audit.jsonl"
            guard = td / "guard.py"
            guard.write_text(envelope.guard_code(), encoding="utf-8")
            old_provider = os.environ.get("OPENROUTER_API_KEY")
            old_hf = os.environ.get("HF_TOKEN")
            os.environ["OPENROUTER_API_KEY"] = "secret"
            os.environ["HF_TOKEN"] = "hf-secret"
            try:
                env, removed = envelope.guarded_env(audit)
            finally:
                if old_provider is None:
                    os.environ.pop("OPENROUTER_API_KEY", None)
                else:
                    os.environ["OPENROUTER_API_KEY"] = old_provider
                if old_hf is None:
                    os.environ.pop("HF_TOKEN", None)
                else:
                    os.environ["HF_TOKEN"] = old_hf
            self.assertIn("OPENROUTER_API_KEY", removed)
            self.assertIn("HF_TOKEN", removed)
            code = '''import json, os, socket
r = {}
for k in ("OPENROUTER_API_KEY", "HF_TOKEN"):
    try:
        os.getenv(k); r[k] = False
    except Exception:
        r[k] = True
try:
    socket.getaddrinfo("example.com", 443); r["remote"] = False
except Exception:
    r["remote"] = True
try:
    socket.getaddrinfo("localhost", 80); r["loopback"] = True
except Exception:
    r["loopback"] = False
print(json.dumps(r, sort_keys=True))'''
            boot = "import pathlib,sys;exec(pathlib.Path(sys.argv[1]).read_text(),{});exec(sys.argv[2],{})"
            proc = subprocess.run([sys.executable, "-I", "-c", boot, str(guard), code], env=env, text=True, capture_output=True, timeout=20)
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertEqual({"HF_TOKEN": True, "OPENROUTER_API_KEY": True, "loopback": True, "remote": True}, json.loads(proc.stdout))
            events = [row["event"] for row in envelope.audit_rows(audit)]
            self.assertIn("guard_installed", events)
            self.assertEqual(2, events.count("blocked_provider_credential_lookup"))
            self.assertIn("blocked_non_loopback_dns", events)

    def test_guard_denies_unlisted_child_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            audit = td / "audit.jsonl"
            guard = td / "guard.py"
            guard.write_text(envelope.guard_code(), encoding="utf-8")
            env, _ = envelope.guarded_env(audit)
            code = '''import json, subprocess
r = {}
try:
    subprocess.run(["echo", "escape"], check=False); r["blocked"] = False
except Exception:
    r["blocked"] = True
print(json.dumps(r))'''
            boot = "import pathlib,sys;exec(pathlib.Path(sys.argv[1]).read_text(),{});exec(sys.argv[2],{})"
            proc = subprocess.run([sys.executable, "-I", "-c", boot, str(guard), code], env=env, text=True, capture_output=True, timeout=20)
            self.assertEqual({"blocked": True}, json.loads(proc.stdout))
            events = [row["event"] for row in envelope.audit_rows(audit)]
            self.assertIn("blocked_child_subprocess", events)

    def test_binding_requires_valid_pass_result_and_preserves_original_receipt(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as out_td:
            old_root = envelope.ROOT
            envelope.ROOT = Path(repo_td)
            try:
                tools = envelope.ROOT / "tools"
                tools.mkdir(parents=True)
                executor = tools / "trigger1_local_qwen06_intermediate_api_execute.py"
                executor.write_text("# executor\n", encoding="utf-8")
                source = {"repo_head": HEAD40, "repo_tree": TREE40, "repo_dirty": False, "repo_status_sha256": hashlib.sha256(b"").hexdigest()}
                runtime_manifest = {
                    "python_version": "x",
                    "torch_version": "2.0",
                    "torch_module_sha256": HEX64,
                    "transformers_version": "4.51",
                    "transformers_module_sha256": HEX64,
                }
                runtime_build = envelope.canonical_sha(runtime_manifest)
                result = {
                    "schema": "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_ACTIVATION_API_EXPERIMENT/v1",
                    "status": "PASS",
                    "promotion_candidate_written": True,
                    "source": {"repo_head": HEAD40, "repo_tree": TREE40},
                    "model": envelope.MODEL_ID,
                    "model_revision": envelope.MODEL_REVISION,
                    "zero_provider_billing": True,
                    "external_provider_credentials_read": False,
                    "api_loopback_only": True,
                    "api_endpoint": "http://127.0.0.1:8089/v1/jspace/logits",
                    "runtime_build_sha256": runtime_build,
                    "checkpoint_sha256": HEX64,
                    "tokenizer_sha256": HEX64,
                    "runtime_manifest": runtime_manifest,
                    "calibration_rows": [{"runtime_receipt_sha256": "1" * 64}],
                    "holdout_rows": [{"runtime_receipt_sha256": "2" * 64}],
                    "selected_layer": 14,
                    "selected_gain": 4.0,
                }
                result["result_sha256"] = envelope.canonical_sha(result)
                original_material = {
                    "endpoint": result["api_endpoint"],
                    "runtime_build_sha256": runtime_build,
                    "checkpoint_sha256": HEX64,
                    "tokenizer_sha256": HEX64,
                    "source": result["source"],
                    "api_invocations": 2,
                    "selected_layer": 14,
                    "selected_gain": 4.0,
                }
                original_receipt = envelope.canonical_sha(original_material)
                candidate = {
                    "source_identity": {"repo_head": HEAD40, "runtime_build_sha256": runtime_build, "checkpoint_sha256": HEX64, "tokenizer_sha256": HEX64},
                    "transport": {"endpoint": result["api_endpoint"], "loopback_only": True, "api_served": True},
                    "target": {
                        "local_runtime_execution_receipt_sha256": original_receipt,
                        "zero_provider_billing": True,
                        "provider": "local",
                        "model_or_route": f"{envelope.MODEL_ID}@{envelope.MODEL_REVISION}",
                    },
                }
                out = Path(out_td)
                candidate_path = out / "trigger1_direct_steering_candidate.json"
                result_path = out / "trigger1_local_activation_api_result.json"
                candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
                result_path.write_text(json.dumps(result), encoding="utf-8")
                binding_sha = envelope.bind_candidate(candidate_path, result_path, "intermediate", source, executor, {"guard_sha256": HEX64})
                rebound = json.loads(candidate_path.read_text(encoding="utf-8"))
                self.assertEqual(original_receipt, rebound["target"]["executor_local_runtime_receipt_sha256"])
                self.assertEqual(binding_sha, rebound["target"]["local_runtime_execution_receipt_sha256"])
                self.assertEqual(source, {k: rebound["source_identity"][k] for k in source})
            finally:
                envelope.ROOT = old_root

    def test_recompute_original_runtime_receipt_rejects_mismatch(self):
        result = {
            "api_endpoint": "http://127.0.0.1:8080/v1/jspace/logits",
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
            "source": {"repo_head": HEAD40},
            "calibration_rows": [],
            "holdout_rows": [],
            "selected_layer": 7,
            "selected_gain": 1.0,
        }
        candidate = {"target": {"local_runtime_execution_receipt_sha256": "f" * 64}}
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_LOCAL_RUNTIME_RECEIPT_MISMATCH"):
            envelope.recompute_original_runtime_receipt(result, candidate, "intermediate")


if __name__ == "__main__":
    unittest.main()
