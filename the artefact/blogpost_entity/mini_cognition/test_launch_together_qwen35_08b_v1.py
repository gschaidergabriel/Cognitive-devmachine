#!/usr/bin/env python3
import importlib.util
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
    def __init__(self, jobs=None):
        self._jobs = list(jobs or [])

    def list(self):
        return types.SimpleNamespace(data=list(self._jobs))


class ClientFake:
    def __init__(self, jobs=None):
        self.fine_tuning = FineTuningFake(jobs)


class TogetherCtorFake:
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = dict(kwargs)


class Launch08BSafetyTests(unittest.TestCase):
    def setUp(self):
        self.old_confirm = os.environ.pop(mod.CREATE_CONFIRM_ENV, None)
        self.old_ledger = os.environ.get(mod.CREATE_LEDGER_DIR_ENV)

    def tearDown(self):
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

    def test_suffix_is_campaign_bound(self):
        fp = "a" * 64
        self.assertEqual(mod.campaign_suffix(fp), "claycog08b-v1-" + "a" * 24)

    def test_account_duplicate_blocks_exact_campaign(self):
        suffix = "claycog08b-v1-deadbeef"
        client = ClientFake(
            [
                {
                    "id": "ft-1",
                    "status": "running",
                    "model": mod.MODEL,
                    "model_output_name": "account/model-" + suffix,
                }
            ]
        )
        with self.assertRaises(SystemExit) as cm:
            mod.assert_no_duplicate_campaign(client, suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT", str(cm.exception))

    def test_other_model_does_not_match_campaign(self):
        suffix = "claycog08b-v1-deadbeef"
        client = ClientFake(
            [
                {
                    "id": "ft-other",
                    "status": "running",
                    "model": "Qwen/Qwen3.5-2B",
                    "model_output_name": "account/model-" + suffix,
                }
            ]
        )
        self.assertEqual(mod.matching_campaign_jobs(client, suffix), [])

    def test_create_requires_exact_fingerprint(self):
        fp = "0123456789abcdef" * 4
        with self.assertRaises(SystemExit) as cm:
            mod.require_create_confirmation(fp)
        self.assertIn("CREATE_CONFIRMATION_REQUIRED", str(cm.exception))
        os.environ[mod.CREATE_CONFIRM_ENV] = fp
        mod.require_create_confirmation(fp)

    def test_create_intent_is_exclusive_and_private(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ[mod.CREATE_LEDGER_DIR_ENV] = td
            fp = mod.campaign_fingerprint()
            suffix = mod.campaign_suffix(fp)
            path = mod.arm_create_intent(fp, suffix)
            self.assertTrue(path.exists())
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            payload = mod.read_create_ledger(fp)
            self.assertEqual(payload["status"], "CREATE_ARMED")
            self.assertEqual(payload["campaign"]["model"], mod.MODEL)
            with self.assertRaises(SystemExit) as cm:
                mod.assert_no_local_create_intent(fp)
            self.assertIn("LOCAL_CREATE_INTENT_ABORT", str(cm.exception))

    def test_zero_retry_client_is_explicit(self):
        TogetherCtorFake.last_kwargs = None
        mod.new_zero_retry_create_client(TogetherCtorFake)
        self.assertEqual(TogetherCtorFake.last_kwargs, {"max_retries": 0})


if __name__ == "__main__":
    unittest.main()
