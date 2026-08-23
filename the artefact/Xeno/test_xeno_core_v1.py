import copy
import hashlib
import unittest

from xeno_core_v1 import (
    XenoAdmissionError,
    admit_ingress,
    build_grid10_plan,
    make_compute_packet,
)

PAYLOAD = "sha256:" + "a" * 64
OUT = "sha256:" + "b" * 64


def base_event():
    return {
        "causal_id": "turn-42",
        "generation": 7,
        "source_class": "HUMAN_PROMPT",
        "source": "user:andreas",
        "source_event_id": "prompt-0001",
        "provenance": ["ui:web", "auth:session-7"],
        "modality": "TEXT",
        "observed_at": 1000,
        "received_at": 1001,
        "permissions": ["read.state"],
        "capability_scope": ["state.noop"],
        "parent_or_stream_id": None,
        "resource_budget": {
            "logical_cells_max": 10,
            "active_decodes_max": 2,
            "token_budget_total": 20_000,
            "wall_time_ms": 30_000,
            "payload_bytes_max": 200_000,
        },
        "payload_ref": PAYLOAD,
    }


class EntryFabricTests(unittest.TestCase):
    def admit(self, raw=None):
        return admit_ingress(raw or base_event(), current_generation=7, allowed_capabilities={"state.noop", "entityos.exec"})

    def test_exact_replay_is_deterministic(self):
        a = self.admit()
        b = self.admit(copy.deepcopy(base_event()))
        self.assertEqual(a.ingress_id, b.ingress_id)

    def test_order_only_noise_canonicalizes(self):
        a = base_event()
        b = copy.deepcopy(a)
        b["provenance"] = list(reversed(a["provenance"]))
        self.assertEqual(self.admit(a).ingress_id, self.admit(b).ingress_id)

    def test_causal_identity_changes_ingress_identity(self):
        a = self.admit()
        b = base_event(); b["causal_id"] = "turn-43"
        self.assertNotEqual(a.ingress_id, self.admit(b).ingress_id)

    def test_provenance_changes_ingress_identity(self):
        a = self.admit()
        b = base_event(); b["provenance"] = ["ui:web", "auth:session-8"]
        self.assertNotEqual(a.ingress_id, self.admit(b).ingress_id)

    def test_source_event_key_binds_producer_identity_not_payload(self):
        a = self.admit()
        b = base_event(); b["payload_ref"] = "sha256:" + "c" * 64
        admitted_b = self.admit(b)
        self.assertEqual(a.source_event_key, admitted_b.source_event_key)
        self.assertNotEqual(a.ingress_id, admitted_b.ingress_id)

    def test_stale_generation_fails_closed(self):
        x = base_event(); x["generation"] = 6
        with self.assertRaises(XenoAdmissionError): self.admit(x)

    def test_unknown_key_fails_closed(self):
        x = base_event(); x["inline_payload"] = "secret-ish"
        with self.assertRaises(XenoAdmissionError): self.admit(x)

    def test_malformed_integer_bool_fails_closed(self):
        x = base_event(); x["resource_budget"]["active_decodes_max"] = True
        with self.assertRaises(XenoAdmissionError): self.admit(x)

    def test_capability_escalation_fails_closed(self):
        x = base_event(); x["capability_scope"] = ["host.process.exec"]
        with self.assertRaises(XenoAdmissionError): self.admit(x)

    def test_payload_ref_must_be_content_addressed(self):
        x = base_event(); x["payload_ref"] = "raw:hello"
        with self.assertRaises(XenoAdmissionError): self.admit(x)

    def test_receive_before_observe_fails(self):
        x = base_event(); x["received_at"] = 999
        with self.assertRaises(XenoAdmissionError): self.admit(x)


class GridTests(unittest.TestCase):
    def packet(self):
        return admit_ingress(base_event(), current_generation=7, allowed_capabilities={"state.noop"})

    def test_grid_has_ten_logical_cells_but_two_active_decodes(self):
        plan = build_grid10_plan(self.packet(), ["hypothesis", "counterhypothesis", "falsifier"], physical_worker_slots=8)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(len(plan.cells), 10)
        self.assertEqual(plan.active_decode_limit, 2)
        self.assertEqual(plan.to_dict()["source_event_key"], self.packet().source_event_key)

    def test_physical_worker_limit_is_separate(self):
        plan = build_grid10_plan(self.packet(), ["analysis"], physical_worker_slots=1)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(plan.active_decode_limit, 1)

    def test_grid_requires_budget_for_ten_cells(self):
        x = base_event(); x["resource_budget"]["logical_cells_max"] = 9; x["resource_budget"]["active_decodes_max"] = 2
        packet = admit_ingress(x, current_generation=7, allowed_capabilities={"state.noop"})
        with self.assertRaises(XenoAdmissionError): build_grid10_plan(packet, ["analysis"], physical_worker_slots=2)

    def test_grid_rejects_total_token_budget_below_cell_count(self):
        x = base_event(); x["resource_budget"]["token_budget_total"] = 9
        packet = admit_ingress(x, current_generation=7, allowed_capabilities={"state.noop"})
        with self.assertRaises(XenoAdmissionError): build_grid10_plan(packet, ["analysis"], physical_worker_slots=2)

    def test_plan_is_deterministic(self):
        packet = self.packet()
        a = build_grid10_plan(packet, ["a", "b"], physical_worker_slots=2, mode="XENO_COGSIM10")
        b = build_grid10_plan(packet, ["a", "b"], physical_worker_slots=2, mode="XENO_COGSIM10")
        self.assertEqual(a.plan_id, b.plan_id)

    def test_candidate_packet_inherits_causal_fences(self):
        packet = self.packet()
        plan = build_grid10_plan(packet, ["analysis"], physical_worker_slots=2)
        out = make_compute_packet(plan, producer_cell="cell-00", payload_ref=OUT, evidence_refs=[packet.payload_ref])
        self.assertEqual(out.causal_id, packet.causal_id)
        self.assertEqual(out.generation, packet.generation)
        self.assertEqual(out.ingress_id, packet.ingress_id)
        self.assertEqual(out.authority_class, "CANDIDATE_ONLY")
        self.assertEqual(out.to_dict()["source_event_key"], packet.source_event_key)

    def test_unplanned_producer_fails_closed(self):
        plan = build_grid10_plan(self.packet(), ["analysis"], physical_worker_slots=2)
        with self.assertRaises(XenoAdmissionError): make_compute_packet(plan, producer_cell="cell-99", payload_ref=OUT)


class UnusualDiscriminatorTests(unittest.TestCase):
    def test_payload_only_identity_aliases_causes_but_full_ingress_does_not(self):
        # One unusual discriminator for this GO: same content, distinct causal/provenance context.
        event_a = base_event()
        event_b = copy.deepcopy(event_a)
        event_b["causal_id"] = "turn-99"
        event_b["provenance"] = ["ui:web", "auth:session-99"]

        payload_only_a = hashlib.sha256(event_a["payload_ref"].encode()).hexdigest()
        payload_only_b = hashlib.sha256(event_b["payload_ref"].encode()).hexdigest()
        self.assertEqual(payload_only_a, payload_only_b)

        full_a = admit_ingress(event_a, current_generation=7, allowed_capabilities={"state.noop"})
        full_b = admit_ingress(event_b, current_generation=7, allowed_capabilities={"state.noop"})
        self.assertNotEqual(full_a.ingress_id, full_b.ingress_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
