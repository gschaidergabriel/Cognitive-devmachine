#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("provider_admission_v1", HERE / "provider_admission_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ProbeEnv(dict):
    def __init__(self, values=None):
        super().__init__(values or {})
        self.lookups = []

    def get(self, key, default=None):
        self.lookups.append(key)
        if key == "TOGETHER_API_KEY":
            raise AssertionError("TOGETHER_API_KEY_LOOKUP_FORBIDDEN_BEFORE_ADMISSION")
        return super().get(key, default)


class Tests(unittest.TestCase):
    def test_default_is_free_only_and_blocks_before_secret_lookup(self):
        env = ProbeEnv({"TOGETHER_API_KEY": "poison"})
        with self.assertRaisesRegex(SystemExit, "FREE_ONLY_PROVIDER_BLOCK"):
            m.require_together_paid_provider_admission(env)
        self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV])

    def test_explicit_free_only_blocks_before_paid_auth_and_secret_lookup(self):
        env = ProbeEnv({
            m.EXECUTION_MODE_ENV: m.FREE_ONLY_MODE,
            m.PAID_PROVIDER_AUTH_ENV: m.PAID_PROVIDER_AUTH_VALUE,
            "TOGETHER_API_KEY": "poison",
        })
        with self.assertRaisesRegex(SystemExit, "FREE_ONLY_PROVIDER_BLOCK"):
            m.require_together_paid_provider_admission(env)
        self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV])

    def test_unknown_mode_fails_closed_before_paid_auth_lookup(self):
        env = ProbeEnv({m.EXECUTION_MODE_ENV: "UNKNOWN"})
        with self.assertRaisesRegex(SystemExit, "PROVIDER_MODE_REJECTED"):
            m.require_together_paid_provider_admission(env)
        self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV])

    def test_paid_mode_requires_exact_authorization(self):
        env = ProbeEnv({m.EXECUTION_MODE_ENV: m.PAID_AUTHORIZED_MODE})
        with self.assertRaisesRegex(SystemExit, "PAID_PROVIDER_AUTHORIZATION_REQUIRED"):
            m.require_together_paid_provider_admission(env)
        self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV, m.PAID_PROVIDER_AUTH_ENV])

    def test_mode_variants_do_not_normalize_into_authority(self):
        for mode in ("free_only", " FREE_ONLY", "FREE_ONLY ", "paid_authorized"):
            with self.subTest(mode=mode):
                env = ProbeEnv({m.EXECUTION_MODE_ENV: mode})
                with self.assertRaisesRegex(SystemExit, "PROVIDER_MODE_REJECTED"):
                    m.require_together_paid_provider_admission(env)
                self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV])

    def test_exact_paid_authorization_admits_preflight_without_secret_lookup(self):
        env = ProbeEnv({
            m.EXECUTION_MODE_ENV: m.PAID_AUTHORIZED_MODE,
            m.PAID_PROVIDER_AUTH_ENV: m.PAID_PROVIDER_AUTH_VALUE,
            "TOGETHER_API_KEY": "poison",
        })
        out = m.require_together_paid_provider_admission(env)
        self.assertEqual(out, {
            "execution_mode": m.PAID_AUTHORIZED_MODE,
            "provider": "together",
            "provider_class": "PAID",
            "authorization": "EXPLICIT_PREFLIGHT_ADMISSION",
        })
        self.assertEqual(env.lookups, [m.EXECUTION_MODE_ENV, m.PAID_PROVIDER_AUTH_ENV])


if __name__ == "__main__":
    unittest.main()
