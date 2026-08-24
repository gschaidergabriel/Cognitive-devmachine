import hashlib
import unittest
from dataclasses import replace

from entry_stream_authority_binding_v1 import (
    EntryStreamAuthorityBindingError,
    bind_external_stream_authority,
    validate_entry_stream_authority_binding,
)
from xeno_entry_fabric_v1 import ENTRY_SCHEMA, admit_entry


def h(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class EntryStreamAuthorityBindingTests(unittest.TestCase):
    generation = 7
    source_kind = "HUMAN_PROMPT"
    source_id = "source:human-ui"
    stream_id = "thread:alpha"
    authority_sha = h("canonical-stream-authority:7")

    def packet(self, *, stream=None, source_id=None, generation=None):
        stream = self.stream_id if stream is None else stream
        source_id = self.source_id if source_id is None else source_id
        generation = self.generation if generation is None else generation
        capability_sha = h("capability-view:7")
        budget = {"max_model_calls": 1, "max_tokens": 512, "max_wall_ms": 2000}
        return admit_entry(
            {
                "schema": ENTRY_SCHEMA,
                "ingress_id": "ingress:1",
                "causal_id": "event:1",
                "entity_generation": generation,
                "source_kind": self.source_kind,
                "source_id": source_id,
                "modality": "TEXT",
                "observed_time": None,
                "received_time": "2026-08-24T02:00:00Z",
                "provenance_ref": "conversation:user-message",
                "provenance_sha256": h("provenance:event:1"),
                "capabilities": ["hcu.route"],
                "capability_binding_sha256": capability_sha,
                "parent_id": "conversation:root",
                "stream_id": stream,
                "budget": budget,
                "payload_ref": "payload:event:1",
                "payload_sha256": h("payload:event:1"),
            },
            current_generation=generation,
            expected_capability_binding_sha256=capability_sha,
            admitted_capabilities=["hcu.route"],
            admitted_budget=budget,
        )

    def authority(self, *, stream=None, source_id=None, generation=None, authority_sha=None):
        return bind_external_stream_authority(
            generation=self.generation if generation is None else generation,
            source_kind=self.source_kind,
            source_id=self.source_id if source_id is None else source_id,
            authorized_stream_id=self.stream_id if stream is None else stream,
            authority_kind="CANONICAL_INGRESS_CONTROL_PLANE",
            authority_ref="canonical:stream-registry:7",
            authority_binding_sha256=self.authority_sha if authority_sha is None else authority_sha,
        )

    def test_exact_external_authority_matches_entry_stream(self):
        validate_entry_stream_authority_binding(
            self.authority(),
            self.packet(),
            expected_authority_binding_sha256=self.authority_sha,
        )

    def test_self_consistent_entry_stream_label_cannot_override_external_authority(self):
        packet = self.packet(stream="thread:forged")
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "ENTRY_STREAM_AUTHORITY_STREAM_ID_MISMATCH",
        ):
            validate_entry_stream_authority_binding(
                self.authority(),
                packet,
                expected_authority_binding_sha256=self.authority_sha,
            )

    def test_external_authority_identity_is_not_taken_from_entry(self):
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "ENTRY_STREAM_EXTERNAL_AUTHORITY_BINDING_MISMATCH",
        ):
            validate_entry_stream_authority_binding(
                self.authority(),
                self.packet(),
                expected_authority_binding_sha256=h("different-canonical-authority"),
            )

    def test_source_and_generation_are_authority_bound(self):
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "ENTRY_STREAM_AUTHORITY_SOURCE_ID_MISMATCH",
        ):
            validate_entry_stream_authority_binding(
                self.authority(),
                self.packet(source_id="source:other"),
                expected_authority_binding_sha256=self.authority_sha,
            )
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "ENTRY_STREAM_AUTHORITY_GENERATION_MISMATCH",
        ):
            validate_entry_stream_authority_binding(
                self.authority(),
                self.packet(generation=8),
                expected_authority_binding_sha256=self.authority_sha,
            )

    def test_digest_validity_is_rechecked(self):
        forged = replace(self.authority(), stream_id="thread:forged")
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "ENTRY_STREAM_AUTHORITY_BINDING_DIGEST_MISMATCH",
        ):
            validate_entry_stream_authority_binding(
                forged,
                self.packet(),
                expected_authority_binding_sha256=self.authority_sha,
            )

    def test_unknown_authority_kind_fails_closed(self):
        with self.assertRaisesRegex(
            EntryStreamAuthorityBindingError,
            "STREAM_AUTHORITY_KIND_UNSUPPORTED",
        ):
            bind_external_stream_authority(
                generation=self.generation,
                source_kind=self.source_kind,
                source_id=self.source_id,
                authorized_stream_id=self.stream_id,
                authority_kind="ENTRY_PACKET_SELF_ASSERTED",
                authority_ref="untrusted",
                authority_binding_sha256=self.authority_sha,
            )


if __name__ == "__main__":
    unittest.main()
