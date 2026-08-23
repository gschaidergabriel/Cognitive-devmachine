import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class AuthorityConsistencyTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        current_authority, version, discovery_errors = mod.discover_current_authority(REPO)
        self.assertFalse(discovery_errors, discovery_errors)
        self.assertIsNotNone(current_authority)
        self.assertIsNotNone(version)

        required = [
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
            "research_entity/rooms/PROGRAM_STATE.json",
            current_authority,
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            mod.TRAINING_PROVENANCE,
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
            "the artefact/manifest.json",
            "the artefact/ARCHITECTURE.md",
            "the artefact/README.md",
            mod.ROOT_CLAUDE,
            mod.CONTROL41,
            mod.CONTROL42,
            mod.CONTROL43,
            mod.CONTROL44,
        ]
        for rel in required:
            src = REPO / rel
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return td, root, current_authority, version

    @staticmethod
    def mutate(root, rel, fn):
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        fn(data)
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

    def test_current_repository_authority_closure_passes(self):
        result = mod.validate(REPO)
        self.assertTrue(result["pass"], result["errors"])
        self.assertGreaterEqual(tuple(map(int, result["current_authority_version"].split("."))), (8, 62))

    def test_successor_partial_promotion_split_poison_fails_closed(self):
        """Unusual falsifier: a newer steering file cannot coexist with stale current pointers."""
        td, root, current_authority, version = self.make_tree(); self.addCleanup(td.cleanup)
        successor = (version[0], version[1] + 1)
        successor_rel = f"{mod.AUTHORITY_DIR}/SUPERVISOR_STEERING_{successor[0]}_{successor[1]}.json"
        supervisor = json.loads((root / current_authority).read_text(encoding="utf-8"))
        supervisor["schema_version"] = f"{successor[0]}.{successor[1]}"
        target = root / successor_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(supervisor, sort_keys=True), encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("INBOX_STEERING_NOT_NEWEST", errors)
        self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", errors)
        self.assertIn("PROGRAM_AUTHORITY_POINTER_MISMATCH", errors)
        self.assertIn("MANIFEST_AUTHORITY_POINTER_MISMATCH", errors)

    def test_bootstrap_stale_predecessor_pointer_fails_closed(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
            lambda d: d.__setitem__("authority_correction", "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_61.json"),
        )
        self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_program_cannot_fake_remaining_quota_observation(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "research_entity/rooms/PROGRAM_STATE.json",
            lambda d: d["execution_policy"].__setitem__("remaining_monthly_sandbox_quota_directly_observed", True),
        )
        self.assertIn("PROGRAM_QUOTA_MUST_NOT_BE_ASSUMED", mod.validate(root)["errors"])

    def test_manifest_requires_fixed_capsule_admission(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "the artefact/manifest.json",
            lambda d: d["execution_policy"].__setitem__("vercel_hobby_bounded_included_tier_fixed_capsules", False),
        )
        self.assertIn("MANIFEST_FIXED_CAPSULE_ADMISSION_MISSING", mod.validate(root)["errors"])

    def test_manifest_forbids_generic_sandbox_command_credit(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "the artefact/manifest.json",
            lambda d: d["execution_policy"].__setitem__("generic_caller_supplied_sandbox_command_credit", "ALLOWED"),
        )
        self.assertIn("MANIFEST_GENERIC_SANDBOX_COMMAND_NOT_FORBIDDEN", mod.validate(root)["errors"])

    def test_supervisor_paid_fallback_cannot_reopen(self):
        td, root, current_authority, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, current_authority, lambda d: d["free_only_policy"].__setitem__("no_paid_fallback", False))
        self.assertIn("SUPERVISOR_PAID_FALLBACK_WEAKENED", mod.validate(root)["errors"])

    def test_program_effect_authority_cannot_move_to_hcu(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "research_entity/rooms/PROGRAM_STATE.json",
            lambda d: d["authority"].__setitem__("external_effects", "HCU"),
        )
        self.assertIn("PROGRAM_EFFECT_AUTHORITY_MISMATCH", mod.validate(root)["errors"])

    def test_whole_runtime_credit_cannot_self_promote(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(
            root,
            "the artefact/manifest.json",
            lambda d: d["runtime_credit"].__setitem__("entityos_hcu_whole_runtime_credit", 1),
        )
        self.assertIn("MANIFEST_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_legacy_together_fence_remains_hash_bound(self):
        td, root, _, _ = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, mod.CONTROL42, lambda d: d["preserved_hard_rules"].__setitem__("together_forbidden", False))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)


if __name__ == "__main__":
    unittest.main()
