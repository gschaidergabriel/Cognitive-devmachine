#!/usr/bin/env python3
"""Deterministic no-network contract tests for the ClayCog Together v2 launcher.

These tests deliberately do not require a Together key and never create a billed job.
The V2-only fake is the bounded API-surface collision falsifier for this go: it exposes
only current SDK-v2 method/field names, so any regression to the stale launcher surface
(`model_limits`, `supports_full_training`, dict estimate arguments, processing_status-only)
fails immediately.
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("claycog_together_launcher", HERE / "launch_together_v1.py")
launcher = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(launcher)


class V2OnlyFineTuning:
    def __init__(self, *, full_training=True, allowed=True, price=4.0):
        self.full_training = full_training
        self.allowed = allowed
        self.price = price
        self.limit_calls = []
        self.estimate_calls = []
        self.create_calls = []

    def get_model_limits(self, *, model):
        self.limit_calls.append(model)
        return SimpleNamespace(full_training=SimpleNamespace(max_batch_size=16) if self.full_training else None)

    def estimate_price(self, **kwargs):
        self.estimate_calls.append(kwargs)
        if not isinstance(kwargs.get("training_type"), str):
            raise AssertionError("training_type must be SDK-v2 string")
        if not isinstance(kwargs.get("training_method"), str):
            raise AssertionError("training_method must be SDK-v2 string")
        return SimpleNamespace(
            estimated_total_price=self.price,
            allowed_to_proceed=self.allowed,
            model_dump=lambda: {"estimated_total_price": self.price, "allowed_to_proceed": self.allowed},
        )

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return SimpleNamespace(id="ft-test-v2")


class V2OnlyFiles:
    def __init__(self, processed=True):
        self.processed = processed
        self.retrieve_calls = []

    def retrieve(self, file_id):
        self.retrieve_calls.append(file_id)
        return SimpleNamespace(id=file_id, processed=self.processed)


class V2OnlyClient:
    def __init__(self, *, full_training=True, allowed=True, price=4.0, processed=True):
        self.fine_tuning = V2OnlyFineTuning(
            full_training=full_training,
            allowed=allowed,
            price=price,
        )
        self.files = V2OnlyFiles(processed=processed)


class TogetherLauncherV2ContractTests(unittest.TestCase):
    def test_default_template_is_exact_hf_model_not_larger_guess(self):
        with patch.dict(os.environ, {}, clear=True):
            hf_model, template, explicit = launcher.resolve_models()
        self.assertEqual(hf_model, "Qwen/Qwen2.5-0.5B")
        self.assertEqual(template, hf_model)
        self.assertFalse(explicit)
        self.assertNotIn("7B", template)

    def test_instruct_ablation_defaults_to_exact_instruct_template(self):
        with patch.dict(os.environ, {}, clear=True):
            hf_model, template, explicit = launcher.resolve_models(instruct_ablation=True)
        self.assertEqual(hf_model, "Qwen/Qwen2.5-0.5B-Instruct")
        self.assertEqual(template, hf_model)
        self.assertFalse(explicit)

    def test_explicit_template_override_is_visible(self):
        with patch.dict(os.environ, {}, clear=True):
            hf_model, template, explicit = launcher.resolve_models(
                template_override="vendor/explicit-compatible-template"
            )
        self.assertEqual(hf_model, "Qwen/Qwen2.5-0.5B")
        self.assertEqual(template, "vendor/explicit-compatible-template")
        self.assertTrue(explicit)

    def test_full_training_limits_use_sdk_v2_method_and_field(self):
        client = V2OnlyClient(full_training=True)
        limits = launcher.get_full_training_limits(client, "Qwen/Qwen2.5-0.5B")
        self.assertIsNotNone(limits.full_training)
        self.assertEqual(client.fine_tuning.limit_calls, ["Qwen/Qwen2.5-0.5B"])

    def test_missing_full_training_fails_closed(self):
        client = V2OnlyClient(full_training=False)
        with self.assertRaises(SystemExit):
            launcher.get_full_training_limits(client, "Qwen/Qwen2.5-0.5B")

    def test_estimate_uses_sdk_v2_string_contract(self):
        client = V2OnlyClient(price=4.0)
        estimate = launcher.estimate_full_sft_price(client, "train-id", "valid-id", "Qwen/Qwen2.5-0.5B")
        self.assertEqual(float(estimate.estimated_total_price), 4.0)
        [call] = client.fine_tuning.estimate_calls
        self.assertEqual(call["training_type"], "full")
        self.assertEqual(call["training_method"], "sft")
        self.assertEqual(call["training_file"], "train-id")
        self.assertEqual(call["validation_file"], "valid-id")

    def test_create_binds_template_and_hf_checkpoint_without_lora(self):
        client = V2OnlyClient()
        job = launcher.create_full_sft_job(
            client,
            "train-id",
            "valid-id",
            "Qwen/Qwen2.5-0.5B",
            "Qwen/Qwen2.5-0.5B",
        )
        self.assertEqual(job.id, "ft-test-v2")
        [call] = client.fine_tuning.create_calls
        self.assertEqual(call["model"], "Qwen/Qwen2.5-0.5B")
        self.assertEqual(call["from_hf_model"], "Qwen/Qwen2.5-0.5B")
        self.assertFalse(call["lora"])
        self.assertEqual(call["train_on_inputs"], "auto")

    def test_wait_file_accepts_current_processed_boolean(self):
        client = V2OnlyClient(processed=True)
        meta = launcher.wait_file(client, "file-v2", timeout_seconds=1)
        self.assertTrue(meta.processed)
        self.assertEqual(client.files.retrieve_calls, ["file-v2"])

    def test_v2_only_surface_collision_falsifier_never_needs_old_names_or_create(self):
        """The one bounded unusual experiment: old API names simply do not exist."""
        client = V2OnlyClient(full_training=True, allowed=True, price=4.0, processed=True)
        hf_model, template, explicit = launcher.resolve_models()
        self.assertFalse(explicit)
        launcher.get_full_training_limits(client, template)
        launcher.wait_file(client, "file-v2", timeout_seconds=1)
        estimate = launcher.estimate_full_sft_price(client, "train-v2", "valid-v2", template)
        self.assertTrue(estimate.allowed_to_proceed)
        self.assertEqual(template, hf_model)
        self.assertEqual(len(client.fine_tuning.create_calls), 0, "preflight must not create a billed job")
        self.assertFalse(hasattr(client.fine_tuning, "model_limits"))
        self.assertFalse(hasattr(client.fine_tuning, "supports_full_training"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
