#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import unittest

from grid10_glm_inference_provider_v1 import (
    DEFAULT_MODEL,
    GLMInferenceConfig,
    GLMProviderError,
    build_payload,
    infer,
    load_api_key,
)


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self):
        return self._raw


class GLMProviderTests(unittest.TestCase):
    def test_default_model_is_small_flash(self):
        self.assertEqual(DEFAULT_MODEL, "glm-4.7-flash")
        cfg = GLMInferenceConfig()
        self.assertFalse(cfg.thinking)
        self.assertLessEqual(cfg.max_tokens, 128)

    def test_key_only_from_runtime_env(self):
        self.assertEqual(load_api_key({"ZAI_API_KEY": " runtime-secret "}), "runtime-secret")
        with self.assertRaises(GLMProviderError):
            load_api_key({})

    def test_payload_is_bounded_and_thinking_off(self):
        cfg = GLMInferenceConfig(max_tokens=64, thinking=False, temperature=0.1)
        payload = build_payload([{"role": "user", "content": "x"}], cfg)
        self.assertEqual(payload["model"], "glm-4.7-flash")
        self.assertEqual(payload["max_tokens"], 64)
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertFalse(payload["stream"])

    def test_receipt_never_contains_secret(self):
        secret = "DO_NOT_RECORD_THIS_SECRET"
        def opener(request, timeout):
            self.assertIn(secret, request.headers.get("Authorization", ""))
            return _FakeHTTPResponse({
                "id": "r-1",
                "model": "glm-4.7-flash",
                "choices": [{"finish_reason": "stop", "message": {"content": "GRID10_GLM_OK"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            })
        result = infer(
            [{"role": "user", "content": "probe"}],
            config=GLMInferenceConfig(max_tokens=16, thinking=False),
            api_key=secret,
            opener=opener,
        )
        receipt_text = json.dumps(result.receipt.__dict__, sort_keys=True)
        self.assertNotIn(secret, receipt_text)
        self.assertFalse(result.receipt.secret_recorded)
        self.assertEqual(result.content, "GRID10_GLM_OK")
        self.assertEqual(result.receipt.total_tokens, 8)

    def test_test_token_cap_rejects_accidental_huge_output(self):
        with self.assertRaises(ValueError):
            GLMInferenceConfig(max_tokens=65536)


if __name__ == "__main__":
    unittest.main()
