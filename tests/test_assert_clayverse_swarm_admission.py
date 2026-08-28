import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "assert_clayverse_swarm_admission.py"
spec = importlib.util.spec_from_file_location("swarm_admission", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class SwarmAdmissionTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        files = {
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "active_program": mod.EXPECTED_PROGRAM,
                "active_stage": mod.EXPECTED_STAGE,
                "sole_owner_directive": mod.EXPECTED_OWNER,
            },
            "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json": {
                "status": "ACTIVE",
                "preserved_hard_rules": {
                    "free_only": True,
                    "together_forbidden": True,
                    "secret_lookup_before_admission": False,
                    "legacy_mini_entity_swarm_controller": mod.LEGACY_BLOCK,
                },
            },
        }
        for rel, data in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")
        contract = root / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(
            "Status: FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION\n"
            "Legacy: LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED\n",
            encoding="utf-8",
        )
        legacy = root / "tools/run_free_go_swarm.py"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text(
            'OWNER_DIRECTIVE_PATH = "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md"\n'
            'prompt = "continuous FREE_ONLY Mini Entity `go` macrocycle"\n',
            encoding="utf-8",
        )
        return td, root

    def test_current_quarantine_state_passes_but_never_admits_provider(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.evaluate(root)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["provider_swarm_admitted"])
        self.assertEqual(result["gate_mode"], "QUARANTINE_ONLY")

    def test_stale_legacy_copy_at_current_controller_path_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        legacy = root / "tools/run_free_go_swarm.py"
        (root / "tools/run_go_zero_swarm.py").write_bytes(legacy.read_bytes())
        with self.assertRaisesRegex(mod.AdmissionError, "CURRENT_CONTROLLER_PRESENT_REQUIRES_SEPARATE_VALIDATION"):
            mod.evaluate(root)

    def test_even_clayverse_named_current_controller_requires_separate_validation(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        (root / "tools/run_go_zero_swarm.py").write_text("# ClayVerse controller candidate\n", encoding="utf-8")
        with self.assertRaisesRegex(mod.AdmissionError, "CURRENT_CONTROLLER_PRESENT_REQUIRES_SEPARATE_VALIDATION"):
            mod.evaluate(root)

    def test_free_only_weakening_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
        data = json.loads(path.read_text(encoding="utf-8")); data["preserved_hard_rules"]["free_only"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(mod.AdmissionError, "FREE_ONLY_WEAKENED"):
            mod.evaluate(root)

    def test_bootstrap_product_regression_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text(encoding="utf-8")); data["active_program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(mod.AdmissionError, "BOOT_PROGRAM"):
            mod.evaluate(root)

    def test_missing_quarantine_contract_marker_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
        path.write_text("LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED\n", encoding="utf-8")
        with self.assertRaisesRegex(mod.AdmissionError, "MISSING_FAIL_CLOSED_CONTRACT"):
            mod.evaluate(root)

    def test_assertion_source_has_no_secret_or_network_api(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("os.environ", text)
        self.assertNotIn("os.getenv", text)
        self.assertNotIn("urllib", text)
        self.assertNotIn("requests", text)


if __name__ == "__main__":
    unittest.main()
