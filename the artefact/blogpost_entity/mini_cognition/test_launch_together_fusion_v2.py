#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("launch_together_v1", HERE / "launch_together_v1.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class FineTuningFake:
    def __init__(self):
        self.jobs = []
    def list(self):
        return types.SimpleNamespace(data=list(self.jobs))


class ClientFake:
    def __init__(self):
        self.fine_tuning = FineTuningFake()


class LimitsCurrent:
    def get_model_limits(self, model):
        return types.SimpleNamespace(full_training={"max_epochs": 10}, model=model)


class LimitsLegacy:
    def model_limits(self, model_name):
        return types.SimpleNamespace(supports_full_training=True, model=model_name)


class LimitClient:
    def __init__(self, ft):
        self.fine_tuning = ft


class FusionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        p = Path(self.tmp.name)
        self.train = p / "train.jsonl"
        self.valid = p / "valid.jsonl"
        self.train.write_text('{"messages":["a"]}\n', encoding="utf-8")
        self.valid.write_text('{"messages":["b"]}\n', encoding="utf-8")
        self.kw = dict(
            hf_model=mod.DEFAULT_HF_MODEL,
            hf_revision=mod.DEFAULT_HF_REVISION,
            template=mod.DEFAULT_HF_MODEL,
            train=self.train,
            valid=self.valid,
            corpus_version="v2",
        )

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop(mod.CREATE_CONFIRM_ENV, None)
        os.environ.pop("CLAYCOG_TOGETHER_TEMPLATE", None)
        os.environ.pop("CLAYCOG_HF_MODEL", None)
        os.environ.pop("CLAYCOG_HF_REVISION", None)

    def test_default_template_is_exact_hf_model(self):
        hf, rev, template, explicit = mod.resolve_models()
        self.assertEqual(mod.DEFAULT_HF_MODEL, hf)
        self.assertEqual(mod.DEFAULT_HF_REVISION, rev)
        self.assertEqual(hf, template)
        self.assertFalse(explicit)

    def test_different_template_is_create_blocked(self):
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_create_template_safe(mod.DEFAULT_HF_MODEL, "Qwen/Qwen2.5-7B-Instruct-Turbo")
        self.assertIn("TEMPLATE_COMPATIBILITY_ABORT", str(ctx.exception))
        mod.assert_create_template_safe(mod.DEFAULT_HF_MODEL, mod.DEFAULT_HF_MODEL)

    def test_floating_revision_is_rejected(self):
        for bad in ("", "main", "master", "latest", "HEAD"):
            with self.assertRaises(SystemExit):
                mod.assert_immutable_revision(bad)
        self.assertEqual(mod.DEFAULT_HF_REVISION, mod.assert_immutable_revision(mod.DEFAULT_HF_REVISION))

    def test_fingerprint_binds_bytes_revision_and_template(self):
        a = mod.campaign_fingerprint(**self.kw)
        self.assertEqual(a, mod.campaign_fingerprint(**self.kw))
        self.valid.write_text('{"messages":["changed"]}\n', encoding="utf-8")
        b = mod.campaign_fingerprint(**self.kw)
        self.assertNotEqual(a, b)
        self.valid.write_text('{"messages":["b"]}\n', encoding="utf-8")
        c = mod.campaign_fingerprint(**{**self.kw, "hf_revision": "deadbeef"})
        d = mod.campaign_fingerprint(**{**self.kw, "template": "other/model"})
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, d)

    def test_create_confirmation_requires_full_fingerprint(self):
        fp = mod.campaign_fingerprint(**self.kw)
        with self.assertRaises(SystemExit):
            mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV] = fp[:24]
        with self.assertRaises(SystemExit):
            mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV] = fp
        mod.require_create_confirmation(fp)

    def test_duplicate_guard_catches_account_visible_campaign(self):
        c = ClientFake()
        fp = mod.campaign_fingerprint(**self.kw)
        suffix = mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-existing",
            status="running",
            model=self.kw["template"],
            from_hf_model=self.kw["hf_model"],
            hf_model_revision=self.kw["hf_revision"],
            model_output_name="acct/output-" + suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(
                c,
                hf_model=self.kw["hf_model"],
                hf_revision=self.kw["hf_revision"],
                template=self.kw["template"],
                suffix=suffix,
            )
        self.assertIn("ft-existing", str(ctx.exception))

    def test_ambiguous_prior_create_is_not_blindly_retried(self):
        c = ClientFake()
        fp = mod.campaign_fingerprint(**self.kw)
        suffix = mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-ambiguous",
            status="pending",
            model=self.kw["template"],
            from_hf_model=self.kw["hf_model"],
            hf_model_revision=self.kw["hf_revision"],
            suffix=suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(
                c,
                hf_model=self.kw["hf_model"],
                hf_revision=self.kw["hf_revision"],
                template=self.kw["template"],
                suffix=suffix,
            )
        self.assertIn("DUPLICATE_CREATE_ABORT", str(ctx.exception))
        self.assertEqual(1, len(c.fine_tuning.jobs))

    def test_model_limits_current_and_legacy_surfaces_are_fail_closed(self):
        _, surface = mod.get_full_training_limits(LimitClient(LimitsCurrent()), mod.DEFAULT_HF_MODEL)
        self.assertEqual("get_model_limits", surface)
        _, surface = mod.get_full_training_limits(LimitClient(LimitsLegacy()), mod.DEFAULT_HF_MODEL)
        self.assertEqual("model_limits", surface)
        class Missing: pass
        with self.assertRaises(SystemExit):
            mod.get_full_training_limits(LimitClient(Missing()), mod.DEFAULT_HF_MODEL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
