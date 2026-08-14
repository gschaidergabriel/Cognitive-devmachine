#!/usr/bin/env python3
"""Executable contract reference for q23 scope-bound visual embedding handles.

This is deliberately a synthetic ownership/state-machine test. It does NOT emulate Qwen
numerics or prove target llama.cpp behavior. The current llama.cpp source establishes the
upstream ownership facts; this test checks the proposed Frank generation-fence contract.
"""
from dataclasses import dataclass
import hashlib
import json
import numpy as np


class InvalidHandle(RuntimeError):
    pass


class MockMtmdOwner:
    def __init__(self, n_embd: int = 2560):
        self.n_embd = n_embd
        self.generation = 0
        self.alive = True
        self.buffer = None
        self.frame_id = None

    def encode(self, frame_id: str, n_tokens: int):
        if not self.alive:
            raise InvalidHandle("owner dead")
        self.generation += 1
        self.frame_id = frame_id
        seed = int(hashlib.sha256(f"{frame_id}:{n_tokens}:{self.n_embd}".encode()).hexdigest()[:16], 16) % (2**32)
        rng = np.random.default_rng(seed)
        self.buffer = rng.standard_normal((n_tokens, self.n_embd), dtype=np.float32)
        return EphemeralMediaEmbeddingView(self, self.generation, frame_id)

    def reset(self):
        self.generation += 1
        self.buffer = None
        self.frame_id = None

    def free(self):
        self.generation += 1
        self.alive = False
        self.buffer = None
        self.frame_id = None


@dataclass(frozen=True)
class EphemeralMediaEmbeddingView:
    owner: MockMtmdOwner
    generation: int
    frame_id: str

    def _check(self):
        if (
            not self.owner.alive
            or self.owner.generation != self.generation
            or self.owner.frame_id != self.frame_id
            or self.owner.buffer is None
        ):
            raise InvalidHandle("stale/invalid view")

    def pooled_descriptor(self):
        self._check()
        # Deliberately materialize only the compact descriptor; the raw token tensor stays owner-scoped.
        return self.owner.buffer.mean(axis=0).astype(np.float32, copy=True)


def digest(arr):
    return hashlib.sha256(arr.tobytes()).hexdigest()


def expect_invalid(fn):
    try:
        fn()
        return False
    except InvalidHandle:
        return True


def run():
    tests = {}
    owner = MockMtmdOwner()

    view_a = owner.encode("A", 256)
    descriptor_a = view_a.pooled_descriptor()
    tests["descriptor_shape"] = list(descriptor_a.shape) == [2560]

    owner.encode("B", 512)
    tests["next_encode_invalidates"] = expect_invalid(view_a.pooled_descriptor)

    view_b = owner.encode("B2", 128)
    owner.reset()
    tests["reset_invalidates"] = expect_invalid(view_b.pooled_descriptor)

    view_c = owner.encode("C", 64)
    descriptor_c = view_c.pooled_descriptor()
    descriptor_hash = digest(descriptor_c)
    owner.free()
    tests["free_invalidates"] = expect_invalid(view_c.pooled_descriptor)
    tests["durable_descriptor_survives_owner_free"] = digest(descriptor_c.copy()) == descriptor_hash

    raw_bytes_256_tokens = 256 * owner.n_embd * 4
    descriptor_bytes = owner.n_embd * 4
    tests["descriptor_bytes"] = descriptor_bytes
    tests["raw_bytes_at_256_tokens"] = raw_bytes_256_tokens
    tests["materialization_reduction_factor_at_256_tokens"] = raw_bytes_256_tokens / descriptor_bytes

    result = {
        "schema_version": "1.0",
        "experiment": "REFERENCE_PEH_SCOPE_TEST",
        "evidence_class": "SYNTHETIC_EXECUTABLE_CONTRACT_TEST_NOT_TARGET_RUNTIME",
        "tests": tests,
        "all_boolean_contract_tests_pass": all(v for v in tests.values() if isinstance(v, bool)),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
