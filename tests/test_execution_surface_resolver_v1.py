import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "execution_surface_resolver_v1.py"
spec = importlib.util.spec_from_file_location("esr", MOD_PATH)
esr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(esr)
REGISTRY = json.loads((ROOT / "governance" / "EXECUTION_SURFACE_REGISTRY_V1.json").read_text())


def req(*caps, allowed=True, economic_required=False, economic_allowed=True, generation="g1"):
    return {
        "capabilities": list(caps),
        "authority_identity": "CLAY_EXECUTION_AUTHORITY.md@test",
        "authority_generation": generation,
        "authority": {"allowed": allowed},
        "economic": {"required": economic_required, "allowed": economic_allowed},
    }


class ResolverTests(unittest.TestCase):
    def test_direct_ssh_absent_runner_unknown_requires_discovery(self):
        out = esr.resolve(REGISTRY, req("shell"), {"direct": {"shell": False}, "routes": {}})
        self.assertEqual(out["classification"], esr.DISCOVERY_REQUIRED)
        self.assertFalse(out["global_absence_proven"])

    def test_direct_ssh_absent_runner_pass_reachable_via_bridge(self):
        obs = {"direct": {"shell": False}, "routes": {"chat_to_clay_direct_dev_via_self_hosted_runner": {"status": "PASS"}}}
        out = esr.resolve(REGISTRY, req("shell"), obs)
        self.assertEqual(out["classification"], esr.REACHABLE_VIA_BRIDGE)
        self.assertEqual(out["selected_route"], "chat_to_clay_direct_dev_via_self_hosted_runner")

    def test_provider_hardoff_does_not_disable_local_vps(self):
        # Economic/provider denial is only consulted when the requested route requires it.
        out = esr.resolve(REGISTRY, req("local_model", economic_required=False, economic_allowed=False), {"direct": {}, "routes": {"configured_bridge_to_clay_direct_dev": "PASS"}})
        self.assertEqual(out["classification"], esr.REACHABLE_VIA_BRIDGE)

    def test_concrete_external_provider_economic_denial_is_separate(self):
        out = esr.resolve(REGISTRY, req("sandbox_exec", economic_required=True, economic_allowed=False), {"direct": {}, "routes": {"chat_to_vercel_sandbox_via_repository_bridge": "PASS"}})
        self.assertEqual(out["classification"], esr.ECONOMICALLY_DENIED)
        self.assertFalse(out["global_absence_proven"])

    def test_runner_queued_is_transient_not_absent(self):
        obs = {"direct": {"shell": False}, "routes": {
            "chat_to_clay_direct_dev_via_self_hosted_runner": "QUEUED",
            "configured_bridge_to_clay_direct_dev": "OFFLINE",
        }}
        out = esr.resolve(REGISTRY, req("shell"), obs)
        self.assertEqual(out["classification"], esr.TRANSIENTLY_UNREACHABLE)
        self.assertFalse(out["global_absence_proven"])

    def test_explicit_owner_denial_is_authority_denied(self):
        out = esr.resolve(REGISTRY, req("shell", allowed=False), {"direct": {"shell": True}})
        self.assertEqual(out["classification"], esr.AUTHORITY_DENIED)

    def test_all_registered_routes_terminal_absent_allows_absence_proof(self):
        obs = {"direct": {"shell": False}, "routes": {
            "chat_to_clay_direct_dev_via_self_hosted_runner": "ABSENT_PROVEN",
            "configured_bridge_to_clay_direct_dev": "TERMINAL_ABSENT",
        }}
        out = esr.resolve(REGISTRY, req("shell"), obs)
        self.assertEqual(out["classification"], esr.CAPABILITY_ABSENT_PROVEN)
        self.assertTrue(out["global_absence_proven"])

    def test_generation_change_invalidates_resolution(self):
        out = esr.resolve(REGISTRY, req("shell", generation="g1"), {"direct": {"shell": True}})
        validation = esr.validate_generation(out, "g2")
        self.assertFalse(validation["valid"])
        self.assertEqual(validation["classification"], esr.STALE_RESOLUTION)

    def test_direct_connector_absent_repository_bridge_still_reachable(self):
        obs = {"direct": {"sandbox_exec": False}, "routes": {"chat_to_vercel_sandbox_via_repository_bridge": "PASS"}}
        out = esr.resolve(REGISTRY, req("sandbox_exec", economic_required=True, economic_allowed=True), obs)
        self.assertEqual(out["classification"], esr.REACHABLE_VIA_BRIDGE)


if __name__ == "__main__":
    unittest.main()
