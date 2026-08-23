from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import mini_execution_identity_v1 as sut


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def identity(**overrides):
    args = {
        "source_commit": hashlib.sha1(b"commit").hexdigest(),
        "source_tree": hashlib.sha1(b"tree").hexdigest(),
        "source_dirty": False,
        "runtime_module_digest": h("runtime"),
        "artifact_sha256": h("artifact"),
        "mini_entity_version": "mini/0.8",
        "entityos_version": "entityos/0.1",
        "source_lock_digest": h("source-lock"),
        "provenance_refs": ["build:receipt:1"],
    }
    args.update(overrides)
    return sut.compile_identity(**args)


def prepare(**overrides):
    out = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "turn-7",
        "turn_binding_digest": h("turn-binding"),
        "boot_source_lock_digest": h("source-lock"),
    }
    out.update(overrides)
    return out


class ExecutionIdentityTests(unittest.TestCase):
    def test_valid_identity_binds_to_prepare(self):
        doc = identity()
        bound = sut.bind_to_prepare(doc, prepare(), expected_generation=7)
        self.assertTrue(bound["ok"])
        self.assertEqual(bound["execution_identity_digest"], doc["identity_digest"])
        self.assertEqual(bound["authority"], sut.AUTHORITY)

    def test_dirty_source_fails_closed(self):
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "SOURCE_DIRTY_OR_UNKNOWN"):
            identity(source_dirty=True)

    def test_placeholder_runtime_digest_fails_closed(self):
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "PLACEHOLDER_REJECTED"):
            identity(runtime_module_digest="0" * 64)

    def test_profile_or_model_fields_cannot_be_smuggled(self):
        doc = identity()
        doc["model"] = "self-asserted"
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "EXECUTION_IDENTITY_FIELDS_MISMATCH"):
            sut.validate_identity(doc)

    def test_source_lock_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "EXECUTION_IDENTITY_SOURCE_LOCK_MISMATCH"):
            sut.bind_to_prepare(identity(), prepare(boot_source_lock_digest=h("other-lock")), expected_generation=7)

    def test_generation_mismatch_fails_closed(self):
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "STALE_GENERATION"):
            sut.bind_to_prepare(identity(), prepare(entity_generation=8), expected_generation=7)

    def test_artifact_change_changes_identity(self):
        a = identity(artifact_sha256=h("artifact-a"))
        b = identity(artifact_sha256=h("artifact-b"))
        self.assertNotEqual(a["identity_digest"], b["identity_digest"])

    def test_tampered_identity_digest_fails_closed(self):
        doc = identity()
        doc["runtime_module_digest"] = h("different-runtime")
        with self.assertRaisesRegex(sut.ExecutionIdentityError, "EXECUTION_IDENTITY_DIGEST_MISMATCH"):
            sut.validate_identity(doc)


if __name__ == "__main__":
    unittest.main()
