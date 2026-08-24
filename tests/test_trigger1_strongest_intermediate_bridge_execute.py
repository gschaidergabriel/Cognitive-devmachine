from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_strongest_intermediate_bridge_execute as bridge_exec

HEAD40 = "a" * 40
TREE40 = "b" * 40
HEX64 = "c" * 64


def source() -> dict:
    return {
        "repo_head": HEAD40,
        "repo_tree": TREE40,
        "repo_dirty": False,
        "repo_status_sha256": HEX64,
    }


def result(status: str = "PASS") -> dict:
    obj = {
        "schema": "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1",
        "status": status,
        "source": {"repo_head": HEAD40, "repo_tree": TREE40},
        "verdict": {"pass": status == "PASS"},
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
    }
    obj["result_sha256"] = bridge_exec.canonical_sha(obj)
    return obj


def candidate() -> dict:
    obj = {
        "schema": "CLAY_TRIGGER1_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE/v1",
        "verdict": {"pass": True},
        "source_identity": {"repo_head": HEAD40, "repo_tree": TREE40},
    }
    obj["candidate_sha256"] = bridge_exec.canonical_sha(obj)
    return obj


class Trigger1StrongestIntermediateBridgeExecuteTests(unittest.TestCase):
    def run_main(self, out: Path, rc: int, *, pre=None, post=None, direct=None) -> int:
        pre = pre or source()
        post = post or pre
        direct = direct or {
            "schema": "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1",
            "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        }
        argv = [
            "trigger1_strongest_intermediate_bridge_execute.py",
            "--output-dir",
            str(out),
            "--cache-dir",
            str(out / "cache"),
        ]
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(bridge_exec, "require_clean_source", side_effect=[pre, post]), \
             mock.patch.object(bridge_exec.subprocess, "run", return_value=mock.Mock(returncode=rc)), \
             mock.patch.object(bridge_exec, "build_direct_candidate", return_value=direct):
            return bridge_exec.main()

    def test_pass_emits_direct_candidate_and_compatibility_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(result()), encoding="utf-8")
            (out / "trigger1_intermediate_candidate.json").write_text(json.dumps(candidate()), encoding="utf-8")
            rc = self.run_main(out, 0)
            self.assertEqual(0, rc)
            direct = json.loads((out / "trigger1_direct_steering_candidate.json").read_text(encoding="utf-8"))
            alias = json.loads((out / "trigger1_local_activation_api_result.json").read_text(encoding="utf-8"))
            self.assertEqual("CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1", direct["schema"])
            record = alias["strongest_intermediate_execution_bridge"]
            self.assertEqual("PASS", record["status"])
            self.assertFalse(record["credit_boundary"]["canonical_credit_minted"])
            observed = alias.pop("result_sha256")
            self.assertEqual(bridge_exec.canonical_sha(alias), observed)

    def test_scientific_negative_is_preserved_without_direct_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "trigger1_intermediate_result.json").write_text(
                json.dumps(result("SCIENTIFIC_NEGATIVE")), encoding="utf-8"
            )
            rc = self.run_main(out, 2)
            self.assertEqual(2, rc)
            self.assertFalse((out / "trigger1_direct_steering_candidate.json").exists())
            alias = json.loads((out / "trigger1_local_activation_api_result.json").read_text(encoding="utf-8"))
            self.assertEqual("SCIENTIFIC_NEGATIVE", alias["status"])
            self.assertEqual("NOT_PROMOTED", alias["strongest_intermediate_execution_bridge"]["status"])

    def test_source_change_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(result()), encoding="utf-8")
            changed = dict(source())
            changed["repo_tree"] = "d" * 40
            with self.assertRaisesRegex(RuntimeError, "SOURCE_CHANGED_DURING_INTERMEDIATE_EXECUTION"):
                self.run_main(out, 0, pre=source(), post=changed)
            self.assertFalse((out / "trigger1_direct_steering_candidate.json").exists())

    def test_tampered_intermediate_result_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            bad = result()
            bad["status"] = "SCIENTIFIC_NEGATIVE"
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SELF_DIGEST_MISMATCH:result_sha256"):
                self.run_main(out, 0)

    def test_tampered_intermediate_candidate_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "trigger1_intermediate_result.json").write_text(json.dumps(result()), encoding="utf-8")
            bad = candidate()
            bad["verdict"] = {"pass": False}
            (out / "trigger1_intermediate_candidate.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SELF_DIGEST_MISMATCH:candidate_sha256"):
                self.run_main(out, 0)


if __name__ == "__main__":
    unittest.main()
