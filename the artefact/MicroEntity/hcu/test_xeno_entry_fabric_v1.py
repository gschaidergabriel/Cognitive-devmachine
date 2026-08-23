import copy
import json
import unittest

from xeno_entry_fabric_v1 import (
    EntryFabricError,
    admit_entry,
    admit_entry_json,
    parse_entry_json,
    to_hcu_reactive_event,
)


CAPABILITY_BINDING_SHA256 = "b" * 64
ADMITTED_CAPABILITIES = ("memory.read", "hcu.route")


def base_entry():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:24:00+07:00",
        "received_time": "2026-08-23T23:24:01+07:00",
        "provenance_ref": "unifieddb:source:test:1",
        "provenance_sha256": "a" * 64,
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:test",
        "budget": {
            "max_model_calls": 2,
            "max_tokens": 2048,
            "max_wall_ms": 5000,
        },
        "payload_ref": "unifieddb:payload:test:1",
        "payload_sha256": "c" * 64,
    }


def raw_entry():
    return json.dumps(base_entry(), separators=(",", ":"), ensure_ascii=True)


def admit(entry, *, current_generation=7, binding=CAPABILITY_BINDING_SHA256, capabilities=ADMITTED_CAPABILITIES):
    return admit_entry(
        entry,
        current_generation=current_generation,
        expected_capability_binding_sha256=binding,
        admitted_capabilities=capabilities,
    )


def admit_raw(raw, *, current_generation=7, binding=CAPABILITY_BINDING_SHA256, capabilities=ADMITTED_CAPABILITIES):
    return admit_entry_json(
        raw,
        current_generation=current_generation,
        expected_capability_binding_sha256=binding,
        admitted_capabilities=capabilities,
    )


class EntryFabricTests(unittest.TestCase):
    def test_entry_admission_is_deterministic_and_canonical(self):
        a = admit(base_entry())
        reversed_entry = dict(reversed(list(base_entry().items())))
        reversed_entry["capabilities"] = list(reversed(reversed_entry["capabilities"]))
        b = admit(reversed_entry)
        self.assertEqual(a, b)
        self.assertEqual(len(a.event_sha256), 64)
        self.assertEqual(len(a.admission_sha256), 64)

    def test_raw_json_roundtrip_preserves_current_typed_identities(self):
        parsed = admit_raw(raw_entry())
        mapped = admit(base_entry())
        self.assertEqual(parsed, mapped)
        self.assertEqual(parsed.event_sha256, mapped.event_sha256)
        self.assertEqual(parsed.admission_sha256, mapped.admission_sha256)

    def test_raw_json_duplicate_top_level_property_rejected_before_mapping(self):
        raw = raw_entry()
        needle = '"capabilities":["memory.read","hcu.route"],'
        poisoned = raw.replace(needle, needle + '"capabilities":["effect.request"],', 1)
        self.assertNotEqual(raw, poisoned)
        with self.assertRaisesRegex(EntryFabricError, "RAW_JSON_DUPLICATE_PROPERTY:capabilities"):
            parse_entry_json(poisoned)

    def test_raw_json_duplicate_nested_budget_property_rejected_before_mapping(self):
        raw = raw_entry()
        needle = '"max_tokens":2048,'
        poisoned = raw.replace(needle, needle + '"max_tokens":999999,', 1)
        self.assertNotEqual(raw, poisoned)
        with self.assertRaisesRegex(EntryFabricError, "RAW_JSON_DUPLICATE_PROPERTY:max_tokens"):
            parse_entry_json(poisoned)

    def test_raw_json_nonfinite_number_and_lone_surrogate_fail_closed(self):
        raw = raw_entry()
        nonfinite = raw.replace('"max_tokens":2048', '"max_tokens":NaN', 1)
        with self.assertRaisesRegex(EntryFabricError, "RAW_JSON_NONFINITE_NUMBER_FORBIDDEN:NaN"):
            parse_entry_json(nonfinite)

        surrogate = raw.replace(
            '"payload_ref":"unifieddb:payload:test:1"',
            '"payload_ref":"\\ud800"',
            1,
        )
        with self.assertRaisesRegex(EntryFabricError, "RAW_JSON_LONE_SURROGATE_FORBIDDEN"):
            parse_entry_json(surrogate)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(EntryFabricError, "STALE_ENTITY_GENERATION"):
            admit(base_entry(), current_generation=8)

    def test_current_generation_authority_must_be_real_nonnegative_integer(self):
        e = base_entry()
        e["entity_generation"] = 1
        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e, current_generation=True)

        e = base_entry()
        e["entity_generation"] = 0
        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e, current_generation=False)

        with self.assertRaisesRegex(EntryFabricError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
            admit(base_entry(), current_generation=-1)

    def test_unknown_field_cannot_smuggle_effect_or_truth_authority(self):
        e = base_entry()
        e["effect_request"] = {"capability": "host.exec"}
        with self.assertRaisesRegex(EntryFabricError, "ENTRY_UNKNOWN_FIELDS:effect_request"):
            admit(e)

    def test_provenance_and_payload_hashes_are_mandatory(self):
        e = base_entry()
        e["provenance_sha256"] = "bad"
        with self.assertRaisesRegex(EntryFabricError, "provenance_sha256"):
            admit(e)

        e = base_entry()
        e["payload_sha256"] = None
        with self.assertRaisesRegex(EntryFabricError, "payload_sha256"):
            admit(e)

    def test_capability_binding_must_match_external_authority(self):
        e = base_entry()
        e["capability_binding_sha256"] = "d" * 64
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_BINDING_MISMATCH"):
            admit(e)

    def test_entry_cannot_self_grant_capability(self):
        e = base_entry()
        e["capabilities"].append("effect.request")
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_NOT_ADMITTED:effect.request"):
            admit(e)

    def test_entry_may_narrow_authorized_capabilities(self):
        e = base_entry()
        e["capabilities"] = ["hcu.route"]
        packet = admit(e)
        self.assertEqual(packet.capabilities, ("hcu.route",))

    def test_capability_lists_and_bindings_are_typed(self):
        e = base_entry()
        e["capabilities"] = ["hcu.route", "hcu.route"]
        with self.assertRaisesRegex(EntryFabricError, "DUPLICATE_FORBIDDEN"):
            admit(e)

        e = base_entry()
        e["capability_binding_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(EntryFabricError, "capability_binding_sha256"):
            admit(e)

        with self.assertRaisesRegex(EntryFabricError, "expected_capability_binding_sha256"):
            admit(base_entry(), binding="not-a-digest")

    def test_budget_is_complete_bounded_and_typed(self):
        e = base_entry()
        e["budget"]["max_model_calls"] = -1
        with self.assertRaisesRegex(EntryFabricError, "NONNEGATIVE_INTEGER_REQUIRED"):
            admit(e)

        e = base_entry()
        del e["budget"]["max_tokens"]
        with self.assertRaisesRegex(EntryFabricError, "ALL_FIELDS_REQUIRED"):
            admit(e)

    def test_hcu_projection_preserves_causal_and_admission_identity(self):
        packet = admit(base_entry())
        event = to_hcu_reactive_event(
            packet,
            novelty=0.8,
            contradiction=0.2,
            zero_relevance=0.7,
        )
        self.assertEqual(event["schema"], "HCU_REACTIVE_EVENT/v1")
        self.assertEqual(event["ingress_id"], packet.ingress_id)
        self.assertEqual(event["causal_id"], packet.causal_id)
        self.assertEqual(event["entry_event_sha256"], packet.event_sha256)
        self.assertEqual(event["entry_admission_sha256"], packet.admission_sha256)
        self.assertEqual(event["entity_generation"], 7)

    def test_hcu_projection_rejects_invalid_signal(self):
        packet = admit(base_entry())
        with self.assertRaisesRegex(EntryFabricError, "UNIT_INTERVAL_REQUIRED"):
            to_hcu_reactive_event(packet, novelty=1.1)

    def test_transport_replay_preserves_event_identity_but_changes_admission_identity(self):
        # Regression-only fusion of the already-selected causal-alias discriminator.
        # Transport/admission metadata must not redefine the causal event.
        original = admit(base_entry())
        replay_entry = copy.deepcopy(base_entry())
        replay_entry["ingress_id"] = "ingress:test:replay"
        replay_entry["received_time"] = "2026-08-23T23:24:03+07:00"
        replay_entry["payload_ref"] = "object:alternate-location"
        replay_entry["capabilities"] = ["hcu.route"]
        replay_entry["budget"] = {
            "max_model_calls": 1,
            "max_tokens": 1024,
            "max_wall_ms": 2500,
        }
        replay = admit(replay_entry)
        self.assertEqual(original.event_sha256, replay.event_sha256)
        self.assertNotEqual(original.admission_sha256, replay.admission_sha256)

    def test_causal_payload_or_provenance_change_changes_event_identity(self):
        original = admit(base_entry())

        payload_change = copy.deepcopy(base_entry())
        payload_change["payload_sha256"] = "d" * 64
        changed_payload = admit(payload_change)
        self.assertNotEqual(original.event_sha256, changed_payload.event_sha256)
        self.assertNotEqual(original.admission_sha256, changed_payload.admission_sha256)

        provenance_change = copy.deepcopy(base_entry())
        provenance_change["provenance_sha256"] = "e" * 64
        changed_provenance = admit(provenance_change)
        self.assertNotEqual(original.event_sha256, changed_provenance.event_sha256)
        self.assertNotEqual(original.admission_sha256, changed_provenance.admission_sha256)

    def test_distinct_causal_occurrence_changes_event_identity(self):
        a = admit(base_entry())
        e = copy.deepcopy(base_entry())
        e["causal_id"] = "causal:test:2"
        b = admit(e)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.admission_sha256, b.admission_sha256)


if __name__ == "__main__":
    unittest.main()
