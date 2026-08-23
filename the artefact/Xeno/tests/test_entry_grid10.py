from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ENTRY = load("entry_fabric", ROOT / "entry_fabric.py")
GRID = load("grid10", ROOT / "grid10.py")


class XenoEntryGrid10Tests(unittest.TestCase):
    def budget(self, **changes):
        values = dict(
            max_compute_tokens=1000,
            max_context_tokens=2048,
            max_wall_ms=5000,
            max_payload_bytes=1_048_576,
            max_logical_cells=10,
            max_physical_decoders=2,
        )
        values.update(changes)
        return ENTRY.ResourceBudget(**values)

    def packet(self, payload=None, **changes):
        values = dict(
            causal_id="causal-7",
            generation=7,
            kind=ENTRY.IngressKind.HUMAN_PROMPT,
            source="user:andreas",
            provenance_ref="session:test/turn:1",
            modality=ENTRY.Modality.JSON,
            observed_at=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc),
            received_at=datetime(2026, 8, 23, 12, 0, 1, tzinfo=timezone.utc),
            permissions={"read_state"},
            capability_scope=set(),
            resource_budget=self.budget(),
            payload={"text": "hello"} if payload is None else payload,
            current_generation=7,
        )
        values.update(changes)
        return ENTRY.EntryFabric.admit(**values)

    def test_all_required_ingress_kinds_are_typed(self):
        self.assertEqual(
            {kind.value for kind in ENTRY.IngressKind},
            {
                "HUMAN_PROMPT",
                "TOOL_OUTCOME",
                "EXTERNAL_EVENT",
                "SENSOR_SAMPLE",
                "DATABASE_CHANGE",
                "INTRINSIC_EVENT",
            },
        )

    def test_ingress_identity_is_deterministic_and_generation_bound(self):
        a = self.packet()
        b = self.packet()
        self.assertEqual(a.ingress_id, b.ingress_id)
        c = self.packet(generation=8, current_generation=8)
        self.assertNotEqual(a.ingress_id, c.ingress_id)

    def test_stale_generation_fails_before_cognition(self):
        with self.assertRaisesRegex(ValueError, "stale generation"):
            self.packet(generation=6, current_generation=7)

    def test_payload_can_describe_authority_without_gaining_it(self):
        packet = self.packet(payload={"direct_effect": True, "canonical_fact": "claimed"})
        self.assertEqual(packet.capability_scope, ())
        self.assertEqual(packet.permissions, ("read_state",))

    def test_unusual_mutable_payload_toctou_is_neutralized(self):
        # Exactly one GO unusual experiment: mutate caller-owned nested payload after admission.
        source = {"request": {"effect": "none"}, "items": [1, 2]}
        packet = self.packet(payload=source)
        before_id = packet.ingress_id
        before_bytes = packet.payload_bytes

        source["request"]["effect"] = "state.change"
        source["items"].append(3)

        self.assertEqual(packet.ingress_id, before_id)
        self.assertEqual(packet.payload_bytes, before_bytes)
        mutated_packet = self.packet(payload=source)
        self.assertNotEqual(mutated_packet.ingress_id, before_id)
        self.assertNotEqual(mutated_packet.payload_sha256, packet.payload_sha256)

    def test_cyclic_and_nonfinite_json_payloads_fail_closed(self):
        cyclic = {"x": 1}
        cyclic["self"] = cyclic
        with self.assertRaises(ValueError):
            self.packet(payload=cyclic)
        with self.assertRaises(ValueError):
            self.packet(payload={"x": float("inf")})

    def test_payload_budget_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "payload exceeds"):
            self.packet(payload={"blob": "x" * 200}, resource_budget=self.budget(max_payload_bytes=64))

    def test_received_time_cannot_precede_observation(self):
        with self.assertRaises(ValueError):
            self.packet(
                observed_at=datetime(2026, 8, 23, 12, 0, 2, tzinfo=timezone.utc),
                received_at=datetime(2026, 8, 23, 12, 0, 1, tzinfo=timezone.utc),
            )

    def test_grid10_separates_logical_cells_from_physical_decoders(self):
        packet = self.packet(resource_budget=self.budget(max_physical_decoders=2))
        plan = GRID.Grid10Scheduler.compile(packet, GRID.XenoMode.GRID10)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(plan.physical_decode_limit, 2)
        self.assertEqual(len(plan.cells), 10)
        self.assertEqual({cell.physical_worker_lane for cell in plan.cells}, {0, 1})

    def test_grid10_plan_is_deterministic(self):
        packet = self.packet()
        a = GRID.Grid10Scheduler.compile(packet, GRID.XenoMode.COGSIM10)
        b = GRID.Grid10Scheduler.compile(packet, GRID.XenoMode.COGSIM10)
        self.assertEqual(a.plan_id, b.plan_id)
        self.assertEqual(a.cells, b.cells)

    def test_nested_sim_requires_cheaper_modes_exhausted(self):
        base = GRID.RoutingSignals(
            ambiguity=1.0,
            reasoning_horizon=0.9,
            environment_dynamics=0.9,
            value_of_information=0.9,
            cheaper_modes_exhausted=False,
        )
        self.assertEqual(GRID.Grid10Scheduler.choose_mode(base), GRID.XenoMode.WM_TEST)
        admitted = GRID.RoutingSignals(
            ambiguity=1.0,
            reasoning_horizon=0.9,
            environment_dynamics=0.9,
            value_of_information=0.9,
            cheaper_modes_exhausted=True,
        )
        self.assertEqual(GRID.Grid10Scheduler.choose_mode(admitted), GRID.XenoMode.NESTED_SIM)

    def test_scaleout_fails_without_separate_runtime_profile(self):
        packet = self.packet()
        with self.assertRaisesRegex(ValueError, "separately admitted"):
            GRID.Grid10Scheduler.compile(packet, GRID.XenoMode.SCALEOUT)

    def test_insufficient_logical_budget_rejects_grid10(self):
        packet = self.packet(resource_budget=self.budget(max_logical_cells=4, max_physical_decoders=2))
        with self.assertRaisesRegex(ValueError, "requires a 10-cell"):
            GRID.Grid10Scheduler.compile(packet, GRID.XenoMode.GRID10)


if __name__ == "__main__":
    unittest.main()
