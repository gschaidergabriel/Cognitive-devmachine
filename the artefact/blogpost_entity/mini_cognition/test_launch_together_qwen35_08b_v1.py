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
SPEC = importlib.util.spec_from_file_location(
    "launch_together_qwen35_08b_v1", HERE / "launch_together_qwen35_08b_v1.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class FineTuningFake:
    def __init__(self, jobs=None, supports_full=True):
        self._jobs = list(jobs or [])
        self.supports_full = supports_full
        self.model_limits_kwargs = None
        self.estimate_kwargs = None

    def list(self):
        return types.SimpleNamespace(data=list(self._jobs))

    def model_limits(self, **kwargs):
        self.model_limits_kwargs = dict(kwargs)
        return types.SimpleNamespace(
            supports_full_training=self.supports_full,
            full_training=types.SimpleNamespace() if self.supports_full else None,
        )

    def estimate_price(self, **kwargs):
        self.estimate_kwargs = dict(kwargs)
        return types.SimpleNamespace(estimated_total_price=4.0, allowed_to_proceed=True)


class ClientFake:
    def __init__(self, jobs=None, supports_full=True):
        self.fine_tuning = FineTuningFake(jobs=jobs, supports_full=supports_full)


class TogetherCtorFake:
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = dict(kwargs)


class Launch08BFusionTests(unittest.TestCase):
    def setUp(self):
        self.old_confirm = os.environ.pop(mod.CREATE_CONFIRM_ENV, None)
        self.old_ledger = os.environ.get(mod.CREATE_LEDGER_DIR_ENV)
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.old_train, self.old_valid = mod.TRAIN, mod.VALID
        mod.TRAIN = root / "train_v2.jsonl"
        mod.VALID = root / "validation_v2.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n', encoding="utf-8")
        mod.VALID.write_text('{"messages":[]}\n', encoding="utf-8")

    def tearDown(self):
        mod.TRAIN, mod.VALID = self.old_train, self.old_valid
        self.tmp.cleanup()
        if self.old_confirm is None:
            os.environ.pop(mod.CREATE_CONFIRM_ENV, None)
        else:
            os.environ[mod.CREATE_CONFIRM_ENV] = self.old_confirm
        if self.old_ledger is None:
            os.environ.pop(mod.CREATE_LEDGER_DIR_ENV, None)
        else:
            os.environ[mod.CREATE_LEDGER_DIR_ENV] = self.old_ledger

    def test_model_is_exact_native_together_08b(self):
        self.assertEqual(mod.MODEL, "Qwen/Qwen3.5-0.8B")
        self.assertEqual(mod.MODEL, mod.EXPECTED_MODEL)
        mod.validate_static_contract()

    def test_campaign_identity_is_direct_full_seed_bound_no_byom(self):
        d = mod.campaign_descriptor()
        self.assertEqual(d["model"], mod.EXPECTED_MODEL)
        self.assertEqual(d["training_type"], {"type": "Full"})
        self.assertEqual(d["training_method"], {"method": "sft", "train_on_inputs": "auto"})
        self.assertEqual(d["random_seed"], 3407)
        raw = json.dumps(d, sort_keys=True)
        for forbidden in ("from_hf_model", "hf_model_revision", "template_model"):
            self.assertNotIn(forbidden, raw)

    def test_sdk_v2_model_limits_contract_and_fail_closed(self):
        client = ClientFake(supports_full=True)
        mod.get_full_training_limits(client)
        self.assertEqual(client.fine_tuning.model_limits_kwargs, {"model_name": mod.EXPECTED_MODEL})
        with self.assertRaises(SystemExit) as cm:
            mod.get_full_training_limits(ClientFake(supports_full=False))
        self.assertIn("MODEL_LIMITS_REJECT", str(cm.exception))

    def test_estimate_price_uses_only_current_price_schema_subset(self):
        client = ClientFake()
        out = mod.estimate_price(client, "train-file", "valid-file")
        self.assertTrue(out.allowed_to_proceed)
        q = client.fine_tuning.estimate_kwargs
        self.assertEqual(q["model"], mod.EXPECTED_MODEL)
        self.assertEqual(q["training_type"], {"type": "Full"})
        self.assertEqual(q["training_method"], {"method": "sft", "train_on_inputs": "auto"})
        for forbidden in ("random_seed", "learning_rate", "warmup_ratio", "from_hf_model"):
            self.assertNotIn(forbidden, q)

    def test_create_payload_explicit_full_sft_and_hyperparameters(self):
        p = mod.create_payload("t", "v", "suffix")
        self.assertEqual(p["model"], mod.EXPECTED_MODEL)
        self.assertEqual(p["training_type"], {"type": "Full"})
        self.assertEqual(p["training_method"], {"method": "sft", "train_on_inputs": "auto"})
        self.assertEqual(p["random_seed"], 3407)
        self.assertEqual(p["learning_rate"], 1e-5)
        self.assertEqual(p["warmup_ratio"], 0.03)
        for forbidden in ("lora", "from_hf_model", "hf_model_revision", "train_on_inputs"):
            self.assertNotIn(forbidden, p)

    def test_fingerprint_changes_with_exact_dataset_bytes(self):
        a = mod.campaign_fingerprint()
        mod.TRAIN.write_text('{"messages":[1]}\n', encoding="utf-8")
        b = mod.campaign_fingerprint()
        self.assertNotEqual(a, b)

    def test_account_duplicate_blocks_exact_campaign(self):
        suffix = "claycog08b-v2-deadbeef"
        client = ClientFake(jobs=[{
            "id": "ft-1",
            "status": "running",
            "model": mod.MODEL,
            "model_output_name": "account/model-" + suffix,
        }])
        with self.assertRaises(SystemExit) as cm:
            mod.assert_no_duplicate_campaign(client, suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT", str(cm.exception))

    def test_other_model_does_not_match_campaign(self):
        suffix = "claycog08b-v2-deadbeef"
        client = ClientFake(jobs=[{
            "id": "ft-other",
            "status": "running",
            "model": "Qwen/Qwen3.5-2B",
            "model_output_name": "account/model-" + suffix,
        }])
        self.assertEqual(mod.matching_campaign_jobs(client, suffix), [])

    def test_create_requires_exact_fingerprint(self):
        fp = "0123456789abcdef" * 4
        with self.assertRaises(SystemExit) as cm:
            mod.require_create_confirmation(fp)
        self.assertIn("CREATE_CONFIRMATION_REQUIRED", str(cm.exception))
        os.environ[mod.CREATE_CONFIRM_ENV] = fp
        mod.require_create_confirmation(fp)

    def test_create_intent_is_exclusive_private_and_campaign_bound(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[mod.CREATE_LEDGER_DIR_ENV] = td
            fp = mod.campaign_fingerprint()
            suffix = mod.campaign_suffix(fp)
            path = mod.arm_create_intent(fp, suffix)
            self.assertTrue(path.exists())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            payload = mod.read_create_ledger(fp)
            self.assertEqual(payload["status"], "CREATE_ARMED")
            self.assertEqual(payload["campaign"]["model"], mod.MODEL)
            self.assertEqual(payload["campaign"]["training_type"], {"type": "Full"})
            with self.assertRaises(SystemExit):
                mod.assert_no_local_create_intent(fp)

    def test_zero_retry_client_is_explicit(self):
        TogetherCtorFake.last_kwargs = None
        mod.new_zero_retry_create_client(TogetherCtorFake)
        self.assertEqual(TogetherCtorFake.last_kwargs, {"max_retries": 0})


if __name__ == "__main__":
    unittest.main()
