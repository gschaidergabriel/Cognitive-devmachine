import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "xeno_current_authority_protocol",
    ROOT / "tools/xeno_current_authority_protocol.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


class LiveAuthorityProtocolTests(unittest.TestCase):
    def make_root(self, *, inbox_epoch="9.01", steering_epoch="9.01", admission_epoch="9.01",
                  paid_fallback=0, implementation="tools/free_lane_provenance.py + exact gate"):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        auto = root / "research_entity/claycode/autonomous"
        auto.mkdir(parents=True)
        steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_01.json"
        inbox = {
            "schema_version": inbox_epoch,
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "steering": steering_rel,
        }
        steering = {
            "schema_version": steering_epoch,
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "free_only": {
                "enabled": True,
                "no_paid_fallback": True,
                "together_forbidden": True,
                "unknown_or_unlisted_route": "FAIL_CLOSED",
            },
        }
        admission = {
            "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1",
            "authority_epoch": admission_epoch,
            "mode": "FREE_ONLY",
            "product": "EntityOS",
            "compute_architecture": "HCU",
            "providers": {"groq": {"admitted": True, "cost_class": "FREE"}},
            "route_level_gate": {
                "implementation": implementation,
                "receipt_schema": "FREE_LANE_EXECUTION_RECEIPT/v1",
                "unknown_or_unbound_route": "FAIL_CLOSED",
                "paid_fallback_attempt_count": paid_fallback,
            },
        }
        (auto / "SUPERVISOR_INBOX.json").write_text(json.dumps(inbox), encoding="utf-8")
        (root / steering_rel).write_text(json.dumps(steering), encoding="utf-8")
        (auto / "FREE_PROVIDER_ADMISSION.json").write_text(json.dumps(admission), encoding="utf-8")
        return td, root

    def test_protocol_requires_no_legacy_worker_directive(self):
        td, root = self.make_root()
        self.addCleanup(td.cleanup)
        # No CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE*.md exists in this fixture.
        protocol = MOD.build_protocol(root)
        self.assertTrue(protocol.startswith(MOD.PROTOCOL_BEGIN))
        self.assertTrue(protocol.endswith(MOD.PROTOCOL_END))
        self.assertIn(MOD.LIVE_MARKER, protocol)
        self.assertIn("current_supervisor_epoch=9.01", protocol)
        self.assertIn("FREE_LANE_EXECUTION_RECEIPT/v1", protocol)

    def test_successor_epoch_mismatch_fails_closed(self):
        td, root = self.make_root(admission_epoch="9.00")
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(MOD.AuthorityProtocolError, "PROVIDER_ADMISSION_EPOCH_MISMATCH"):
            MOD.resolve_current_authority(root)

    def test_composed_route_implementation_is_accepted(self):
        td, root = self.make_root(
            implementation="tools/free_lane_provenance.py + tools/run_6000_free_swarm_v3.py exact fingerprint gate"
        )
        self.addCleanup(td.cleanup)
        authority = MOD.resolve_current_authority(root)
        self.assertIn("tools/free_lane_provenance.py", authority["route_implementation"])

    def test_missing_provenance_or_paid_fallback_fails_closed(self):
        td, root = self.make_root(implementation="tools/something_else.py")
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(MOD.AuthorityProtocolError, "FREE_LANE_PROVENANCE_IMPLEMENTATION_MISSING"):
            MOD.resolve_current_authority(root)

        td2, root2 = self.make_root(paid_fallback=1)
        self.addCleanup(td2.cleanup)
        with self.assertRaisesRegex(MOD.AuthorityProtocolError, "FREE_LANE_PAID_FALLBACK_NONZERO"):
            MOD.resolve_current_authority(root2)

    def test_pointer_escape_fails_closed(self):
        td, root = self.make_root()
        self.addCleanup(td.cleanup)
        inbox_path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
        inbox = json.loads(inbox_path.read_text(encoding="utf-8"))
        inbox["steering"] = "../../../../outside.json"
        inbox_path.write_text(json.dumps(inbox), encoding="utf-8")
        with self.assertRaisesRegex(MOD.AuthorityProtocolError, "STEERING_ESCAPES_REPO"):
            MOD.resolve_current_authority(root)

    def test_current_repository_authority_resolves(self):
        authority = MOD.resolve_current_authority(ROOT)
        protocol = MOD.build_protocol(ROOT)
        self.assertEqual(authority["epoch"], protocol.split("current_supervisor_epoch=", 1)[1].splitlines()[0])
        self.assertEqual(authority["receipt_schema"], "FREE_LANE_EXECUTION_RECEIPT/v1")


if __name__ == "__main__":
    unittest.main()
