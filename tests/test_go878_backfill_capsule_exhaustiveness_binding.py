from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "tools" / "run_free_swarm_historical_backfill_capsule_878.py"


class BackfillCapsuleExhaustivenessBindingTests(unittest.TestCase):
    def source(self) -> str:
        return CAPSULE.read_text(encoding="utf-8")

    def test_capsule_installs_shared_policy_before_mutation_helpers_are_bound(self):
        source = self.source()
        self.assertIn(
            "import free_swarm_historical_backfill as historical_backfill_core",
            source,
        )
        self.assertIn(
            "from free_swarm_backfill_exhaustiveness_878 import install as install_exhaustiveness",
            source,
        )
        install_at = source.index("install_exhaustiveness(historical_backfill_core)")
        ingest_bind_at = source.index(
            "ingest_artifact_history = historical_backfill_core.ingest_artifact_history"
        )
        self.assertLess(install_at, ingest_bind_at)

    def test_capsule_binds_all_backfill_helpers_from_the_policy_installed_module(self):
        source = self.source()
        for binding in (
            "backfill_metrics = historical_backfill_core.backfill_metrics",
            "ensure_schema = historical_backfill_core.ensure_schema",
            "ingest_artifact_history = historical_backfill_core.ingest_artifact_history",
        ):
            self.assertIn(binding, source)
        self.assertNotIn("from free_swarm_historical_backfill import (", source)

    def test_capsule_remains_provider_free_by_contract(self):
        source = self.source()
        self.assertIn('"provider_model_network_io": False', source)
        self.assertIn('"paid_provider_io": False', source)
        self.assertIn('"together_io": False', source)
        self.assertIn('"canonical_effects": False', source)


if __name__ == "__main__":
    unittest.main()
