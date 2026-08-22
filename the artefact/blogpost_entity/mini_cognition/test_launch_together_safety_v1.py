#!/usr/bin/env python3
import importlib.util
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("launcher", HERE / "launch_together_v1.py")
launcher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(launcher)


class SafetyTests(unittest.TestCase):
    def test_revision_requires_exact_commit(self):
        good = "a" * 40
        self.assertEqual(launcher.normalize_revision(good.upper()), good)
        self.assertIsNone(launcher.normalize_revision(None))
        for bad in ("main", "a" * 39, "g" * 40, " a" * 20):
            with self.assertRaises(ValueError):
                launcher.normalize_revision(bad)

    def test_fingerprint_changes_on_provenance(self):
        base = launcher.campaign_descriptor(
            hf_model="Qwen/Qwen2.5-0.5B",
            hf_revision="1" * 40,
            template="Qwen/Qwen2.5-7B-Instruct-Turbo",
            train_sha256="a" * 64,
            validation_sha256="b" * 64,
        )
        f1 = launcher.campaign_fingerprint(base)
        changed = dict(base)
        changed["hf_model_revision"] = "2" * 40
        f2 = launcher.campaign_fingerprint(changed)
        self.assertNotEqual(f1, f2)
        self.assertEqual(launcher.campaign_suffix(f1), "claycog05b-" + f1[:16])

    def test_duplicate_active_or_completed_always_aborts(self):
        for status in ("pending", "running", "completed"):
            jobs = [types.SimpleNamespace(id="ft-1", status=status, suffix="same")]
            with self.assertRaisesRegex(RuntimeError, "DUPLICATE_ABORT"):
                launcher.duplicate_create_gate(jobs, suffix="same", retry_job_id=None)

    def test_failed_job_requires_exact_explicit_retry_id(self):
        jobs = [types.SimpleNamespace(id="ft-failed", status="error", suffix="same")]
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE_ABORT"):
            launcher.duplicate_create_gate(jobs, suffix="same", retry_job_id=None)
        with self.assertRaisesRegex(RuntimeError, "RETRY_ABORT"):
            launcher.duplicate_create_gate(jobs, suffix="same", retry_job_id="ft-other")
        admitted = launcher.duplicate_create_gate(
            jobs, suffix="same", retry_job_id="ft-failed"
        )
        self.assertEqual(admitted["id"], "ft-failed")

    def test_find_same_campaign_uses_server_suffix(self):
        response = types.SimpleNamespace(data=[
            types.SimpleNamespace(id="ft-1", status="error", suffix="other"),
            types.SimpleNamespace(id="ft-2", status="queued", suffix="wanted"),
        ])
        fine_tuning = types.SimpleNamespace(list=lambda: response)
        client = types.SimpleNamespace(fine_tuning=fine_tuning)
        jobs = launcher.find_same_campaign_jobs(client, "wanted")
        self.assertEqual([job.id for job in jobs], ["ft-2"])

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x"
            path.write_bytes(b"abc")
            self.assertEqual(
                launcher.sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )


if __name__ == "__main__":
    unittest.main()
