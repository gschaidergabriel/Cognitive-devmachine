import unittest

from research_entity.harness.reference.active_assembly_pressure import (
    ActiveAssemblyPressureError,
    diagnose_active_assembly_pressure,
)


def assembly(roles, max_items=8, reexpand=None):
    return {
        "assembly_sha256": "a" * 64,
        "max_items": max_items,
        "items": [{"packet_id": f"p{i}", "selection_role": role} for i, role in enumerate(roles)],
        "reexpand_refs": list(reexpand or []),
    }


class PressureTests(unittest.TestCase):
    def test_conflict_only_full_budget_is_saturated(self):
        out = diagnose_active_assembly_pressure(assembly(["CONFLICT_VISIBILITY"] * 8))
        self.assertEqual(out["pressure_band"], "SATURATED")
        self.assertEqual(out["ordinary_capacity_remaining"], 0)
        self.assertEqual(out["conflict_slot_fraction"], 1.0)
        self.assertFalse(out["selection_policy_changed"])
        self.assertFalse(out["execution_authority"])

    def test_half_conflict_is_medium_and_preserves_capacity_signal(self):
        out = diagnose_active_assembly_pressure(assembly(
            ["CONFLICT_VISIBILITY"] * 4 + ["ORDINARY"] * 4,
            reexpand=["x", "y"],
        ))
        self.assertEqual(out["pressure_band"], "MEDIUM")
        self.assertEqual(out["ordinary_capacity_remaining"], 4)
        self.assertEqual(out["reexpand_ref_count"], 2)

    def test_unknown_roles_are_observed_not_reinterpreted(self):
        out = diagnose_active_assembly_pressure(assembly(["OTHER", "ORDINARY"], max_items=4))
        self.assertEqual(out["unknown_selection_role_count"], 1)
        self.assertEqual(out["ordinary_selected_count"], 1)

    def test_budget_violation_fails_closed(self):
        with self.assertRaisesRegex(ActiveAssemblyPressureError, "BUDGET_VIOLATION"):
            diagnose_active_assembly_pressure(assembly(["ORDINARY"] * 3, max_items=2))

    def test_diagnostic_hash_is_deterministic(self):
        a = diagnose_active_assembly_pressure(assembly(["CONFLICT_VISIBILITY", "ORDINARY"], max_items=4))
        b = diagnose_active_assembly_pressure(assembly(["CONFLICT_VISIBILITY", "ORDINARY"], max_items=4))
        self.assertEqual(a["diagnostic_sha256"], b["diagnostic_sha256"])


if __name__ == "__main__":
    unittest.main()
