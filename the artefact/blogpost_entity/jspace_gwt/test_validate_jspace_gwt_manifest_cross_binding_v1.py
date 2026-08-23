import copy
import hashlib
import json
import unittest

from validate_jspace_gwt_manifest_cross_binding_v1 import CrossBindingError, cross_validate

D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64
D5 = "5" * 64


def manifest():
    return {
        "schema": "mini-entity-bundled-cognition-manifest/v1",
        "engine_id": "bundled-qwen35-08b",
        "model_family": "Qwen3.5-0.8B",
        "checkpoint_digest": D0,
        "tokenizer_digest": D1,
        "jspace_profile_digest": D2,
        "lens_profile_digest": D3,
        "workspace_calibration_digest": D4,
        "steering_calibration_digest": D5,
    }


def raw(m):
    return json.dumps(m, sort_keys=True, separators=(",", ":")).encode()


def raw_sha(m):
    return hashlib.sha256(raw(m)).hexdigest()


def receipt(m=None):
    m = manifest() if m is None else m
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "bundled_core": {
            "manifest_sha256": raw_sha(m),
            "engine_id": m["engine_id"],
            "model_family": m["model_family"],
            "checkpoint_sha256": m["checkpoint_digest"],
            "tokenizer_sha256": m["tokenizer_digest"],
        },
        "jspace": {
            "jspace_profile_sha256": m["jspace_profile_digest"],
            "lens_profile_sha256": m["lens_profile_digest"],
            "steering_calibration_sha256": m["steering_calibration_digest"],
        },
        "gwt": {"calibration_sha256": m["workspace_calibration_digest"]},
    }


class CrossBindingTests(unittest.TestCase):
    def assert_ok(self, m, r):
        cross_validate(m, r, manifest_raw_sha256=raw_sha(m))

    def test_exact_pair_passes(self):
        m = manifest()
        self.assert_ok(m, receipt(m))

    def test_raw_manifest_byte_substitution_is_rejected(self):
        m = manifest()
        r = receipt(m)
        alternate_raw_hash = hashlib.sha256(raw(m) + b"\n").hexdigest()
        with self.assertRaisesRegex(CrossBindingError, "manifest_raw_sha256"):
            cross_validate(m, r, manifest_raw_sha256=alternate_raw_hash)

    def test_rebound_manifest_hash_cannot_shadow_stale_checkpoint(self):
        old = manifest()
        r = receipt(old)
        changed = copy.deepcopy(old)
        changed["checkpoint_digest"] = "9" * 64
        r["bundled_core"]["manifest_sha256"] = raw_sha(changed)
        with self.assertRaisesRegex(CrossBindingError, "checkpoint_digest"):
            self.assert_ok(changed, r)

    def test_missing_jspace_profile_binding_fails_closed(self):
        m = manifest()
        r = receipt(m)
        del r["jspace"]["jspace_profile_sha256"]
        with self.assertRaisesRegex(CrossBindingError, "jspace_profile_sha256"):
            self.assert_ok(m, r)

    def test_lens_profile_mismatch_fails_closed(self):
        m = manifest()
        r = receipt(m)
        r["jspace"]["lens_profile_sha256"] = "8" * 64
        with self.assertRaisesRegex(CrossBindingError, "lens_profile_digest"):
            self.assert_ok(m, r)

    def test_workspace_calibration_mismatch_fails_closed(self):
        m = manifest()
        r = receipt(m)
        r["gwt"]["calibration_sha256"] = "7" * 64
        with self.assertRaisesRegex(CrossBindingError, "workspace_calibration_digest"):
            self.assert_ok(m, r)

    def test_optional_steering_profile_must_cross_bind_when_present(self):
        m = manifest()
        r = receipt(m)
        r["jspace"]["steering_calibration_sha256"] = "6" * 64
        with self.assertRaisesRegex(CrossBindingError, "steering_calibration_digest"):
            self.assert_ok(m, r)

    def test_no_steering_in_manifest_requires_no_receipt_binding(self):
        m = manifest()
        del m["steering_calibration_digest"]
        r = receipt(manifest())
        r["bundled_core"]["manifest_sha256"] = raw_sha(m)
        self.assert_ok(m, r)


if __name__ == "__main__":
    unittest.main()
