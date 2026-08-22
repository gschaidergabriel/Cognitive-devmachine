#!/usr/bin/env python3

import importlib.util
import json
import os
import stat
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("launch08", HERE / "launch_together_qwen35_08b_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FT:
    def __init__(self, jobs=None, full=True):
        self.jobs = list(jobs or [])
        self.full = full
        self.limits_kwargs = None
        self.estimate_kwargs = None

    def list(self):
        return types.SimpleNamespace(data=self.jobs)

    def model_limits(self, **kwargs):
        self.limits_kwargs = kwargs
        return types.SimpleNamespace(
            supports_full_training=self.full,
            full_training=types.SimpleNamespace() if self.full else None,
        )

    def estimate_price(self, **kwargs):
        self.estimate_kwargs = kwargs
        return types.SimpleNamespace(estimated_total_price=4.0, allowed_to_proceed=True)


class Client:
    def __init__(self, jobs=None, full=True):
        self.fine_tuning = FT(jobs, full)


class TogetherCtor:
    last = None

    def __init__(self, **kwargs):
        type(self).last = kwargs


# Mirrors the currently documented high-level together-py create call shape only for
# the fields ClayCog supplies. A nested REST training_type dict must not bind here.
def current_sdk_create_shape(
    *,
    training_file,
    model=None,
    n_epochs=1,
    validation_file="",
    n_evals=0,
    n_checkpoints=1,
    learning_rate=0.00001,
    warmup_ratio=0.0,
    lora=None,
    suffix=None,
    random_seed=None,
    model_limits=None,
    train_on_inputs=None,
    training_method="sft",
):
    return None


class Tests(unittest.TestCase):
    def setUp(self):
        self.confirmation = os.environ.pop(m.CREATE_CONFIRM_ENV, None)
        self.ledger_dir = os.environ.get(m.CREATE_LEDGER_DIR_ENV)
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.old_train, self.old_valid = m.TRAIN, m.VALID
        m.TRAIN = root / "t.jsonl"
        m.VALID = root / "v.jsonl"
        m.TRAIN.write_text('{"messages":[]}\n')
        m.VALID.write_text('{"messages":[]}\n')

    def tearDown(self):
        m.TRAIN, m.VALID = self.old_train, self.old_valid
        self.temp.cleanup()
        if self.confirmation is None:
            os.environ.pop(m.CREATE_CONFIRM_ENV, None)
        else:
            os.environ[m.CREATE_CONFIRM_ENV] = self.confirmation
        if self.ledger_dir is None:
            os.environ.pop(m.CREATE_LEDGER_DIR_ENV, None)
        else:
            os.environ[m.CREATE_LEDGER_DIR_ENV] = self.ledger_dir

    def test_model_and_direct_campaign(self):
        self.assertEqual(m.MODEL, "Qwen/Qwen3.5-0.8B")
        m.validate_static_contract()
        descriptor = m.campaign_descriptor()
        self.assertEqual(descriptor["schema"], "claycog-08b-together-direct-campaign/v3")
        self.assertEqual(descriptor["training_type"], {"type": "Full"})
        self.assertEqual(descriptor["random_seed"], 3407)
        self.assertEqual(len(descriptor["launcher_sha256"]), 64)
        self.assertEqual(descriptor["launcher_sha256"], m.sha256_file(m.LAUNCHER))
        raw = json.dumps(descriptor)
        self.assertNotIn("from_hf_model", raw)
        self.assertNotIn("template_model", raw)

    def test_sdk_v2_model_limits(self):
        client = Client()
        m.get_full_training_limits(client)
        self.assertEqual(client.fine_tuning.limits_kwargs, {"model_name": m.EXPECTED_MODEL})
        with self.assertRaises(SystemExit):
            m.get_full_training_limits(Client(full=False))

    def test_estimate_schema_subset(self):
        client = Client()
        m.estimate_price(client, "t", "v")
        query = client.fine_tuning.estimate_kwargs
        self.assertEqual(query["training_type"], {"type": "Full"})
        self.assertEqual(query["training_method"], {"method": "sft", "train_on_inputs": "auto"})
        for forbidden in ("random_seed", "learning_rate", "warmup_ratio", "from_hf_model"):
            self.assertNotIn(forbidden, query)

    def test_create_uses_high_level_sdk_shape_for_full_sft(self):
        limits = object()
        payload = m.create_payload("t", "v", "s", model_limits=limits)
        self.assertIs(payload["model_limits"], limits)
        self.assertIs(payload["lora"], False)
        self.assertEqual(payload["training_method"], "sft")
        self.assertEqual(payload["train_on_inputs"], "auto")
        self.assertEqual(payload["random_seed"], 3407)
        self.assertEqual(payload["learning_rate"], 1e-5)
        self.assertEqual(payload["warmup_ratio"], 0.03)
        for forbidden in ("training_type", "from_hf_model", "hf_model_revision"):
            self.assertNotIn(forbidden, payload)
        m.assert_sdk_create_signature(current_sdk_create_shape, payload)

    def test_pinned_together_sdk_create_signature_if_installed(self):
        try:
            from together import Together
        except ImportError:
            self.skipTest("together SDK not installed in this execution surface")
        client = Together(api_key="test-only-not-a-real-secret")
        payload = m.create_payload("t", "v", "s")
        m.assert_sdk_create_signature(client.fine_tuning.create, payload)
        legacy_rest_payload = dict(payload)
        legacy_rest_payload.pop("lora")
        legacy_rest_payload.pop("train_on_inputs")
        legacy_rest_payload["training_method"] = {"method": "sft", "train_on_inputs": "auto"}
        legacy_rest_payload["training_type"] = {"type": "Full"}
        with self.assertRaises(SystemExit):
            m.assert_sdk_create_signature(client.fine_tuning.create, legacy_rest_payload)

    def test_rest_create_shape_falsifier_is_rejected_before_intent(self):
        # Reproduces the pre-repair bug: estimate/REST dictionaries were passed to
        # FineTuningResource.create(), whose Python signature does not accept training_type
        # and expects training_method as a string rather than an object.
        old_payload = {
            "training_file": "t",
            "validation_file": "v",
            "model": m.MODEL,
            "n_epochs": 3,
            "n_evals": 2,
            "n_checkpoints": 1,
            "random_seed": 3407,
            "learning_rate": 1e-5,
            "warmup_ratio": 0.03,
            "suffix": "s",
            "training_method": {"method": "sft", "train_on_inputs": "auto"},
            "training_type": {"type": "Full"},
        }
        with self.assertRaises(SystemExit) as ctx:
            m.assert_sdk_create_signature(current_sdk_create_shape, old_payload)
        self.assertIn("SDK_CREATE_SIGNATURE_REJECT", str(ctx.exception))

    def test_fingerprint_binds_dataset_and_launcher(self):
        first = m.campaign_fingerprint()
        m.TRAIN.write_text('{"messages":[1]}\n')
        self.assertNotEqual(first, m.campaign_fingerprint())
        descriptor = m.campaign_descriptor()
        self.assertEqual(descriptor["launcher_sha256"], m.sha256_file(m.LAUNCHER))

    def test_duplicate_guard(self):
        suffix = "claycog08b-v3-dead"
        client = Client(
            [
                {
                    "id": "j",
                    "status": "running",
                    "model": m.MODEL,
                    "model_output_name": "x" + suffix,
                }
            ]
        )
        with self.assertRaises(SystemExit):
            m.assert_no_duplicate_campaign(client, suffix)

    def test_confirmation_and_private_intent(self):
        fingerprint = "a" * 64
        with self.assertRaises(SystemExit):
            m.require_create_confirmation(fingerprint)
        os.environ[m.CREATE_CONFIRM_ENV] = fingerprint
        m.require_create_confirmation(fingerprint)
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ[m.CREATE_LEDGER_DIR_ENV] = temp_dir
            fingerprint = m.campaign_fingerprint()
            path = m.arm_create_intent(fingerprint, m.campaign_suffix(fingerprint))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            entry = m.read_create_ledger(fingerprint)
            self.assertEqual(entry["schema"], "claycog-together-create-intent/v3")
            self.assertEqual(entry["campaign"]["training_type"], {"type": "Full"})
            self.assertEqual(entry["campaign"]["launcher_sha256"], m.sha256_file(m.LAUNCHER))

    def test_created_job_identity_mismatch_detection(self):
        expected = {
            "training_file": "t",
            "validation_file": "v",
            "model": m.MODEL,
            "n_epochs": 3,
            "n_evals": 2,
            "random_seed": 3407,
        }
        good = types.SimpleNamespace(**expected)
        self.assertEqual(m.created_job_identity_mismatches(good, expected), {})
        bad = types.SimpleNamespace(**{**expected, "random_seed": 9})
        mismatches = m.created_job_identity_mismatches(bad, expected)
        self.assertEqual(mismatches["random_seed"], {"expected": 3407, "observed": 9})

    def test_zero_retry(self):
        TogetherCtor.last = None
        m.new_zero_retry_create_client(TogetherCtor)
        self.assertEqual(TogetherCtor.last, {"max_retries": 0})


if __name__ == "__main__":
    unittest.main()
