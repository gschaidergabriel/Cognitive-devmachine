import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/clay-direct-dev-roundtrip.yml"
PROTOCOL = ROOT / "research_entity/continuity/ORDINARY_DISPATCH_IDEMPOTENCY_PROTOCOL.md"
SPEC = ROOT / "research_entity/continuity/ordinary_dispatch_specs/clay-direct-dev-roundtrip-v1.json"
CLAIM = ROOT / "research_entity/continuity/ordinary_dispatch_claims/clay-direct-dev-roundtrip-v1-g0000.json"
GO_IDENTITY = ROOT / "research_entity/continuity/GO_MACROCYCLE_IDENTITY_CONTRACT.md"


class ClayDirectDevDispatchSingleton878(unittest.TestCase):
    def test_spec_identity_is_semantic_not_go_or_timestamp_keyed(self):
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertEqual(spec["dispatch_class"], "clay-direct-dev-roundtrip-v1")
        self.assertEqual(spec["retry_generation"], 0)
        self.assertEqual(spec["current_dispatch_key"], "clay-direct-dev-roundtrip-v1-g0000")
        excluded = set(spec["identity_excludes"])
        for required in {
            "go_text",
            "macrocycle_id",
            "timestamp",
            "issue_number",
            "workflow_run_id",
            "unrelated_main_sha",
            "organ_model_session_identity",
        }:
            self.assertIn(required, excluded)

    def test_generation_zero_is_quarantined_after_legacy_fanout(self):
        claim = json.loads(CLAIM.read_text(encoding="utf-8"))
        self.assertEqual(claim["dispatch_key"], "clay-direct-dev-roundtrip-v1-g0000")
        self.assertEqual(claim["state"], "LEGACY_FANOUT_QUARANTINED_NO_NEW_TRIGGER")
        self.assertFalse(claim["new_issue_authorized_by_this_claim"])
        self.assertTrue(claim["no_new_trigger_until_generation_advance"])
        self.assertEqual(claim["scientific_replication_credit"], 0)

    def test_workflow_requires_typed_claim_and_serializes_probe_class(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("dispatch_schema: CLAY_ORDINARY_DISPATCH/v1", text)
        self.assertIn("group: clay-direct-dev-roundtrip-v1", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("ordinary_dispatch_specs/clay-direct-dev-roundtrip-v1.json", text)
        self.assertIn("ordinary_dispatch_claims/{key}.json", text)
        self.assertIn("ordinary_dispatch_results/{key}.json", text)
        self.assertIn("ALREADY_SATISFIED", text)
        self.assertIn("stale/noncanonical dispatch key", text)
        self.assertIn("claim is quarantine-only", text)

    def test_persistent_identity_is_dispatch_key_not_run_id(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('clay-direct-dev-roundtrip-${DISPATCH_KEY}.json', text)
        self.assertNotIn('target="research_entity/runtime/tool_results/clay-direct-dev-roundtrip-${GITHUB_RUN_ID}.json"', text)
        self.assertIn("'event_sha'", text)
        self.assertIn("'checkout_head'", text)

    def test_go_contract_points_all_organs_to_dispatch_protocol(self):
        protocol = PROTOCOL.read_text(encoding="utf-8")
        go = GO_IDENTITY.read_text(encoding="utf-8")
        self.assertIn("CREATE-ONLY", protocol)
        self.assertIn("A new `go` alone NEVER increments generation", protocol)
        self.assertIn("ORDINARY_DISPATCH_IDEMPOTENCY_PROTOCOL.md", go)
        self.assertIn("create **zero** additional issues/workflow triggers", go)


if __name__ == "__main__":
    unittest.main()
