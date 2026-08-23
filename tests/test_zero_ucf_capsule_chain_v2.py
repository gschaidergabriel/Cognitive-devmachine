from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chain = load(ROOT / "tools" / "validate_zero_ucf_capsule_chain_v2.py", "zero_ucf_chain_v2")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class FakeCapsule:
    @staticmethod
    def validate(capsule):
        if capsule.get("schema") != "ZERO_WORKSPACE_CAPSULE/v1":
            raise ValueError("BAD_CAPSULE")
        return {"ok": True}


class FakePacketV2:
    ENGINE_TO_UCF = {"CLAUDE_CODE": "claude_code"}

    @staticmethod
    def validate(packet, capsule, *, inference, system, user, require_context=False):
        if packet.get("schema") != "ZERO_INFERENCE_PACKET/v2":
            raise ValueError("BAD_PACKET")
        if require_context is not True:
            raise ValueError("CONTEXT_NOT_REQUIRED")
        expected = digest({"inference": inference, "system": system, "user": user})
        if packet.get("admitted_context_digest") != expected:
            raise ValueError("DOWNSTREAM_CONTEXT_DIGEST_MISMATCH")
        if packet.get("workspace_capsule_digest") != capsule.get("capsule_digest"):
            raise ValueError("CAPSULE_BINDING_MISMATCH")
        return {"ok": True}


class FakeBaseChain:
    errors = []

    @classmethod
    def validate_chain(cls, cycle, boot, manifest, lock):
        return list(cls.errors)


def fixtures():
    inference = {"kind": "claude_code", "model": "fixed"}
    system = "system-context-v1"
    user = "user-context-v1"
    capsule = {
        "schema": "ZERO_WORKSPACE_CAPSULE/v1",
        "mode": "WORKSPACE_BOUND",
        "entity_generation": 19,
        "causal_turn_id": "turn-19",
        "capsule_digest": "12" * 32,
        "zero_identity_digest": "34" * 32,
        "grf_digest": "56" * 32,
        "workspace_digest": "78" * 32,
    }
    packet = {
        "schema": "ZERO_INFERENCE_PACKET/v2",
        "workspace_capsule_digest": capsule["capsule_digest"],
        "packet_digest": "9a" * 32,
        "target_engine_class": "CLAUDE_CODE",
        "jspace_mode": "COMPILED_EXTERNAL",
        "admitted_context_digest": digest({"inference": inference, "system": system, "user": user}),
    }
    cycle = {
        "runtime": {"generation": 19},
        "identity": {
            "zero_identity_digest": capsule["zero_identity_digest"],
            "grf_digest": capsule["grf_digest"],
        },
        "binding": {
            "causal_turn_id": capsule["causal_turn_id"],
            "zero_workspace_capsule_digest": capsule["capsule_digest"],
        },
        "workspace": {"after_digest": capsule["workspace_digest"]},
        "inference": {
            "inference_packet_digest": packet["packet_digest"],
            "engine_class": "claude_code",
            "jspace_mode": "COMPILED_EXTERNAL",
            "executed": False,
            "candidate_result_digest": None,
        },
        "authority": {
            "validation_decision": "BLOCKED",
            "canonical_write_committed": False,
            "effect_committed": False,
        },
    }
    return cycle, capsule, packet, inference, system, user


class ZeroUcfCapsuleChainV2Tests(unittest.TestCase):
    def call(self, cycle, capsule, packet, inference, system, user):
        return chain.validate_zero_bindings(
            cycle,
            capsule,
            packet,
            downstream_inference=inference,
            downstream_system=system,
            downstream_user=user,
            capsule_module=FakeCapsule,
            packet_module=FakePacketV2,
        )

    def test_exact_downstream_context_is_accepted(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        self.assertEqual(self.call(cycle, capsule, packet, inference, system, user), [])

    def test_unusual_downstream_system_context_swap_fails_closed(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        errors = self.call(cycle, capsule, packet, inference, system + "-POISON", user)
        self.assertEqual(
            errors,
            ["PACKET_VALIDATION_FAILED:ValueError:DOWNSTREAM_CONTEXT_DIGEST_MISMATCH"],
        )

    def test_downstream_inference_config_swap_fails_closed(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        poisoned = dict(inference)
        poisoned["model"] = "unbound-model"
        errors = self.call(cycle, capsule, packet, poisoned, system, user)
        self.assertEqual(
            errors,
            ["PACKET_VALIDATION_FAILED:ValueError:DOWNSTREAM_CONTEXT_DIGEST_MISMATCH"],
        )

    def test_ucf_packet_digest_mismatch_is_rejected(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        cycle["inference"]["inference_packet_digest"] = "bc" * 32
        self.assertIn(
            "ZERO_INFERENCE_PACKET_DIGEST_MISMATCH",
            self.call(cycle, capsule, packet, inference, system, user),
        )

    def test_generation_and_workspace_mismatch_are_rejected(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        cycle["runtime"]["generation"] = 20
        cycle["workspace"]["after_digest"] = "de" * 32
        errors = self.call(cycle, capsule, packet, inference, system, user)
        self.assertIn("ZERO_CAPSULE_GENERATION_MISMATCH", errors)
        self.assertIn("ZERO_WORKSPACE_AFTER_DIGEST_MISMATCH", errors)

    def test_base_chain_errors_are_preserved(self):
        cycle, capsule, packet, inference, system, user = fixtures()
        FakeBaseChain.errors = ["BOOT_SOURCE_COMMIT_MISMATCH"]
        try:
            errors = chain.validate_chain(
                cycle,
                {},
                Path("manifest"),
                {},
                capsule,
                packet,
                downstream_inference=inference,
                downstream_system=system,
                downstream_user=user,
                base_chain=FakeBaseChain,
                capsule_module=FakeCapsule,
                packet_module=FakePacketV2,
            )
        finally:
            FakeBaseChain.errors = []
        self.assertEqual(errors, ["BOOT_SOURCE_COMMIT_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
