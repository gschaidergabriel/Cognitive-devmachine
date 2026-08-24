#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import trigger1_midlayer_v3_pipeline as p


STABLE = {
    "repo_head": "a" * 40,
    "repo_tree": "b" * 40,
    "source_identity_sha256": "c" * 64,
}
DRIFTED = {
    "repo_head": "a" * 40,
    "repo_tree": "b" * 40,
    "source_identity_sha256": "d" * 64,
}


def envelope() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_EXACT_SOURCE_ENVELOPE/v1",
        "status": "PASS_EXACT_SOURCE_BINDING",
        "source_identity_pre": dict(STABLE),
        "source_identity_post": dict(STABLE),
        "source_stable_across_run": True,
        "runtime_required_fields_bound": True,
        "model_identity_bound": True,
        "provider_fence_pass": True,
        "promotion_candidate_retained": True,
        "receipt_sha256": "e" * 64,
    }


def write_intermediate(out: Path, *, status: str) -> None:
    result = {
        "schema": "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1",
        "status": status,
        "source": {"repo_head": "a" * 40, "repo_tree": "b" * 40},
        "runtime_manifest": {"python_version": "3.x"},
        "runtime_build_sha256": "1" * 64,
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "rev",
        "checkpoint_sha256": "2" * 64,
        "tokenizer_sha256": "3" * 64,
        "api_endpoint": "http://127.0.0.1:1234/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
        "credit_scope": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY" if status == "PASS" else "NONE",
        "verdict": {"pass": status == "PASS"},
    }
    (out / p.INTERMEDIATE_RESULT_NAME).write_text(json.dumps(result), encoding="utf-8")
    if status == "PASS":
        (out / p.INTERMEDIATE_CANDIDATE_NAME).write_text(json.dumps({"schema": "candidate"}), encoding="utf-8")


class Trigger1MidlayerV3PipelineTests(unittest.TestCase):
    def test_compat_launcher_routes_v3_pipeline_not_legacy_executor(self):
        launcher = (ROOT / "tools/trigger1_local_qwen06_midlayer_causal.sh").read_text(encoding="utf-8")
        self.assertIn("trigger1_midlayer_v3_pipeline.py", launcher)
        self.assertNotIn("trigger1_local_qwen06_midlayer_causal_execute.py", launcher)
        paths = p.pipeline_paths(ROOT)
        self.assertEqual("trigger1_local_qwen06_intermediate.sh", paths["launcher"].name)
        self.assertEqual("trigger1_intermediate_promotion_bridge.py", paths["bridge"].name)
        self.assertEqual("trigger1_jspace_promotion_gate.py", paths["gate"].name)
        self.assertEqual("trigger1_local_qwen06_midlayer_causal.sh", paths["workflow_launcher"].name)

    def test_positive_path_requires_intermediate_then_bridge_then_gate(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            calls: list[list[str]] = []

            def fake_run(cmd, **kwargs):
                calls.append([str(x) for x in cmd])
                if len(calls) == 1:
                    write_intermediate(out, status="PASS")
                    return SimpleNamespace(returncode=0)
                if len(calls) == 2:
                    output = Path(cmd[cmd.index("--output") + 1])
                    output.write_text(json.dumps({"schema": "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"}), encoding="utf-8")
                    return SimpleNamespace(returncode=0)
                kwargs["stdout"].write(b'{"schema":"CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v3","mechanism_runtime_vector_credit_candidate":true}')
                return SimpleNamespace(returncode=0)

            with patch.object(p, "capture_source_identity", side_effect=[dict(STABLE), dict(STABLE), dict(STABLE)]), \
                 patch.object(p, "build_envelope", return_value=(envelope(), True)), \
                 patch.object(p.subprocess, "run", side_effect=fake_run):
                rc = p.run_pipeline(ROOT, out)

            self.assertEqual(0, rc)
            self.assertIn("trigger1_local_qwen06_intermediate.sh", calls[0][1])
            self.assertIn("trigger1_intermediate_promotion_bridge.py", calls[1][1])
            self.assertIn("trigger1_jspace_promotion_gate.py", calls[2][1])
            self.assertTrue((out / p.DIRECT_CANDIDATE_NAME).is_file())
            compat = json.loads((out / p.COMPAT_RESULT_NAME).read_text(encoding="utf-8"))
            self.assertEqual("PASS", compat["status"])
            self.assertTrue(compat["pipeline"]["direct_candidate_present"])
            self.assertTrue(compat["pipeline"]["source_stable_through_gate"])
            self.assertEqual(0, compat["pipeline"]["canonical_credit_minted"])
            receipt = json.loads((out / p.EXACT_SOURCE_RECEIPT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(p.PIPELINE_SCHEMA, receipt["pipeline_schema"])
            self.assertTrue(receipt["source_stable_through_gate"])

    def test_source_drift_after_bridge_removes_candidate_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            call_count = 0

            def fake_run(cmd, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    write_intermediate(out, status="PASS")
                    return SimpleNamespace(returncode=0)
                if call_count == 2:
                    output = Path(cmd[cmd.index("--output") + 1])
                    output.write_text("{}", encoding="utf-8")
                    return SimpleNamespace(returncode=0)
                kwargs["stdout"].write(b'{}')
                return SimpleNamespace(returncode=0)

            with patch.object(p, "capture_source_identity", side_effect=[dict(STABLE), dict(STABLE), dict(DRIFTED)]), \
                 patch.object(p, "build_envelope", return_value=(envelope(), True)), \
                 patch.object(p.subprocess, "run", side_effect=fake_run):
                rc = p.run_pipeline(ROOT, out)

            self.assertEqual(4, rc)
            self.assertFalse((out / p.DIRECT_CANDIDATE_NAME).exists())
            self.assertFalse((out / p.PROMOTION_GATE_NAME).exists())
            compat = json.loads((out / p.COMPAT_RESULT_NAME).read_text(encoding="utf-8"))
            self.assertFalse(compat["pipeline"]["source_stable_through_gate"])
            self.assertFalse(compat["pipeline"]["direct_candidate_present"])

    def test_scientific_negative_is_preserved_without_promotion_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            def fake_run(_cmd, **_kwargs):
                write_intermediate(out, status="SCIENTIFIC_NEGATIVE")
                return SimpleNamespace(returncode=2)

            with patch.object(p, "capture_source_identity", side_effect=[dict(STABLE), dict(STABLE), dict(STABLE)]), \
                 patch.object(p, "build_envelope", return_value=(envelope(), True)), \
                 patch.object(p.subprocess, "run", side_effect=fake_run):
                rc = p.run_pipeline(ROOT, out)

            self.assertEqual(2, rc)
            self.assertFalse((out / p.DIRECT_CANDIDATE_NAME).exists())
            compat = json.loads((out / p.COMPAT_RESULT_NAME).read_text(encoding="utf-8"))
            self.assertEqual("SCIENTIFIC_NEGATIVE", compat["status"])
            self.assertIsNone(compat["pipeline"]["promotion_bridge_returncode"])
            self.assertEqual(0, compat["pipeline"]["jspace_model_runtime_credit"])


if __name__ == "__main__":
    unittest.main()
