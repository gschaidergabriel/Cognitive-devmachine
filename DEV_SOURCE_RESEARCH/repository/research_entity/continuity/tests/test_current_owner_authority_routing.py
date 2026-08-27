from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / "AGENTS.md"
BLOGPOST = ROOT / "research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md"
CURRENT = "research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md"
CONTROL = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_5_MINI_ENTITY_GO_AUTHORITY.json"
STALE_CLAYVERSE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"


class CurrentOwnerAuthorityRoutingTests(unittest.TestCase):
    def test_root_bootstrap_selects_current_mini_entity_owner(self):
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn(CURRENT, text)
        self.assertIn(CONTROL, text)
        self.assertIn("MINI_ENTITY_PIPELINE_ALL_IN_ONE", text)
        self.assertNotIn("## Sole active directive\n\nRead first:\n\n`research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`", text)

    def test_historical_blogpost_redirect_points_to_current_owner(self):
        text = BLOGPOST.read_text(encoding="utf-8")
        self.assertIn("SUPERSEDED / HISTORICAL DONOR EVIDENCE ONLY", text)
        self.assertIn(CURRENT, text)
        self.assertIn(CONTROL, text)
        self.assertNotIn(STALE_CLAYVERSE, text)
        self.assertIn("MINI_ENTITY_PIPELINE_ALL_IN_ONE", text)
        self.assertIn("MiniUnifiedDB", text)

    def test_no_redirect_chain_can_reactivate_clayverse_work_selection(self):
        agents = AGENTS.read_text(encoding="utf-8")
        blogpost = BLOGPOST.read_text(encoding="utf-8")
        combined = agents + "\n" + blogpost
        self.assertIn("ClayVerse 4.4 directive", combined)
        self.assertIn("historical compatibility/donor paths only", combined)
        self.assertNotIn(STALE_CLAYVERSE, combined)


if __name__ == "__main__":
    unittest.main()
