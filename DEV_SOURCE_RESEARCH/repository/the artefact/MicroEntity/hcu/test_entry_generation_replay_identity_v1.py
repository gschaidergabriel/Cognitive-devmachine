import copy
import unittest

from xeno_entry_fabric_v1 import EntryFabricError, admit_entry


CAPABILITY_BINDING_SHA256 = "b" * 64
ADMITTED_CAPABILITIES = ("memory.read", "hcu.route")
ADMITTED_BUDGET = {
    "max_model_calls": 4,
    "max_tokens": 4096,
    "max_wall_ms": 10_000,
}


def base_entry(generation: int) -> dict:
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": f"ingress:g{generation}",
        "causal_id": "causal:immutable:recovery-replay:1",
        "entity_generation": generation,
        "source_kind": "TOOL_OUTCOME",
        "source_id": "effect-journal:request:1",
        "modality": "EVENT",
        "observed_time": "2026-08-24T00:00:00Z",
        "received_time": f"2026-08-24T00:00:0{generation % 10}Z",
        "provenance_ref": "unifieddb:effect:request:1",
        "provenance_sha256": "a" * 64,
        "capabilities": ["memory.read"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": "episode:1",
        "stream_id": "recovery:1",
        "budget": {
            "max_model_calls": 1,
            "max_tokens": 512,
            "max_wall_ms": 1000,
        },
        "payload_ref": f"unifieddb:payload:admission:g{generation}",
        "payload_sha256": "c" * 64,
    }


def admit(entry: dict, generation: int):
    return admit_entry(
        entry,
        current_generation=generation,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=ADMITTED_CAPABILITIES,
        admitted_budget=ADMITTED_BUDGET,
    )


class EntryGenerationReplayIdentityTests(unittest.TestCase):
    def test_same_immutable_event_survives_generation_rollover(self):
        """Unusual discriminator: recovery generation must fence admission, not rewrite event history."""
        before_restart = admit(base_entry(7), 7)
        replay = base_entry(8)
        after_restart = admit(replay, 8)

        self.assertEqual(before_restart.event_sha256, after_restart.event_sha256)
        self.assertNotEqual(before_restart.admission_sha256, after_restart.admission_sha256)
        self.assertNotEqual(before_restart.entity_generation, after_restart.entity_generation)

    def test_old_generation_admission_still_fails_closed_after_restart(self):
        stale = copy.deepcopy(base_entry(7))
        with self.assertRaisesRegex(EntryFabricError, "STALE_ENTITY_GENERATION"):
            admit(stale, 8)


if __name__ == "__main__":
    unittest.main()