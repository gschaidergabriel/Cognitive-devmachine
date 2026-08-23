import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from entry_fabric import (
    DispatchBindingError,
    EntryFabricError,
    IngressKind,
    IngressRequest,
    ReplayRejectedError,
    ResourceBudget,
    StaleGenerationError,
    admit_ingress,
    validate_for_dispatch,
)


def request(generation=7):
    return IngressRequest(
        event_id="evt-001",
        source="urn:xeno:user:andreas",
        event_type="xeno.user.prompt.v1",
        kind=IngressKind.HUMAN_PROMPT,
        causal_id="causal-001",
        generation=generation,
        modality="text/plain",
        observed_at="2026-08-23T23:23:00+07:00",
        received_at="2026-08-23T23:23:00.050000+07:00",
        permissions=("cognition.request",),
        capability_scope=(),
        resource_budget=ResourceBudget(
            max_logical_cells=10,
            max_tokens=2048,
            max_wall_ms=20000,
            max_branches=10,
        ),
        payload_ref="unifieddb://ingress/evt-001",
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    )


class EntryFabricTests(unittest.TestCase):
    def test_valid_admission_and_dispatch(self):
        packet, receipt = admit_ingress(request(), current_generation=7)
        validate_for_dispatch(
            packet,
            receipt,
            current_generation=7,
            canonical_receipt_digest=receipt.receipt_digest(),
        )
        self.assertEqual(packet.generation, 7)
        self.assertEqual(packet.resource_budget.max_logical_cells, 10)

    def test_duplicate_source_event_identity_rejected(self):
        packet, _ = admit_ingress(request(), current_generation=7)
        changed = request()
        changed = IngressRequest(**{**changed.__dict__, "causal_id": "causal-other", "payload_ref": "unifieddb://other"})
        with self.assertRaises(ReplayRejectedError):
            admit_ingress(changed, current_generation=7, canonical_seen_event_keys=(packet.event_key,))

    def test_stale_generation_rejected_at_admission(self):
        with self.assertRaises(StaleGenerationError):
            admit_ingress(request(generation=6), current_generation=7)

    def test_canonical_receipt_binding_is_required(self):
        packet, receipt = admit_ingress(request(), current_generation=7)
        with self.assertRaises(DispatchBindingError):
            validate_for_dispatch(
                packet,
                receipt,
                current_generation=7,
                canonical_receipt_digest="0" * 64,
            )

    def test_mapping_input_fails_closed_on_unknown_keys(self):
        raw = {
            "event_id": "evt-002",
            "source": "urn:xeno:tool:weather",
            "event_type": "xeno.tool.outcome.v1",
            "kind": "TOOL_OUTCOME",
            "causal_id": "causal-002",
            "generation": 7,
            "modality": "application/json",
            "observed_at": "2026-08-23T23:23:00+07:00",
            "received_at": "2026-08-23T23:23:01+07:00",
            "permissions": [],
            "capability_scope": [],
            "resource_budget": {
                "max_logical_cells": 10,
                "max_tokens": 1024,
                "max_wall_ms": 5000,
                "max_branches": 4,
            },
            "payload_ref": "unifieddb://ingress/evt-002",
            "surprise": "fail-closed",
        }
        with self.assertRaises(EntryFabricError):
            IngressRequest.from_mapping(raw)

    def test_permissions_must_be_sorted_unique(self):
        bad = request()
        bad = IngressRequest(**{**bad.__dict__, "permissions": ("z", "a", "a")})
        with self.assertRaises(EntryFabricError):
            bad.validate()

    def test_received_time_cannot_precede_observation(self):
        bad = request()
        bad = IngressRequest(
            **{
                **bad.__dict__,
                "received_at": "2026-08-23T23:22:59+07:00",
            }
        )
        with self.assertRaises(EntryFabricError):
            bad.validate()

    def test_boolean_generation_is_rejected(self):
        bad = request()
        bad = IngressRequest(**{**bad.__dict__, "generation": True})
        with self.assertRaises(EntryFabricError):
            bad.validate()

    def test_unusual_generation_toctou_replay_is_rejected(self):
        """One bounded GO unusual discriminator: admission-only vs dispatch-fenced generation."""
        packet, receipt = admit_ingress(request(generation=7), current_generation=7)

        # Lesion/counterfactual: an admission-only queue would still accept this object after rollover.
        naive_admission_only_dispatch = packet.generation == receipt.admitted_generation
        self.assertTrue(naive_admission_only_dispatch)

        # Xeno Entry Fabric re-checks the live generation immediately before cognition.
        with self.assertRaises(StaleGenerationError):
            validate_for_dispatch(
                packet,
                receipt,
                current_generation=8,
                canonical_receipt_digest=receipt.receipt_digest(),
            )


if __name__ == "__main__":
    unittest.main()
