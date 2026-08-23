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


class ClayVerseSwarmAdmissionV2Tests(unittest.TestCase):
    def make_tree(self, *, migrated: bool = True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        payloads = {
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "active_program": "CLAYVERSE_SINGLE_CONTAINER",
                "active_stage": "CLAYVERSE_ARTIFACT",
                "sole_owner_directive": mod.OWNER_DIRECTIVE,
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "clayverse-single-container",
                "stage": "CLAYVERSE_ARTIFACT",
                "owner_directive": mod.OWNER_DIRECTIVE,
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "together_forbidden": True,
                    "vps_testing_forbidden": True,
                },
            },
            "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json": {
                "status": "ACTIVE",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "secret_lookup_before_admission": False,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                    "legacy_mini_entity_swarm_controller": "FORBIDDEN_UNTIL_CLAYVERSE_PROMPT_AND_AUTHORITY_MIGRATION",
                },
            },
        }
        for rel, data in payloads.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")
        contract = root / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(
            "FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION\nLEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED\n",
            encoding="utf-8",
        )
        protocol = root / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
        protocol.parent.mkdir(parents=True, exist_ok=True)
        protocol.write_text(
            mod.CLAYVERSE_PROTOCOL if migrated else mod.LEGACY_PROTOCOL,
            encoding="utf-8",
        )
        current = root / "tools/run_go_zero_swarm.py"
        legacy = root / "tools/run_free_go_swarm.py"
        current.parent.mkdir(parents=True, exist_ok=True)
        if migrated:
            current.write_text(
                "\n".join(
                    [
                        mod.OWNER_DIRECTIVE,
                        mod.CLAYVERSE_PROTOCOL,
                        "subprocess assert_clayverse_swarm_admission.py --require-admitted",
                        "BASE.collect_keys(spec)",
                        "macrocycle_id unusual_experiment child_trigger=go",
                    ]
                ),
                encoding="utf-8",
            )
            legacy.write_text("generic base controller", encoding="utf-8")
        else:
            current.write_text(
                "current Mini Entity/EntityOS product boundary\n" + mod.LEGACY_PROTOCOL + "\nBASE.collect_keys(spec)\n",
                encoding="utf-8",
            )
            legacy.write_text(
                "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md\nMiniUnifiedDB\n" + mod.LEGACY_PROTOCOL,
                encoding="utf-8",
            )
        return td, root

    def test_migrated_controller_is_source_admitted(self):
        td, root = self.make_tree(migrated=True)
        self.addCleanup(td.cleanup)
        result = mod.inspect(root)
        self.assertTrue(result["assertion_pass"])
        self.assertTrue(result["provider_swarm_admitted"])
        self.assertEqual(result["status"], "PASS_CONTROLLER_SOURCE_ADMITTED")

    def test_existing_stale_controller_is_quarantined_not_admitted(self):
        td, root = self.make_tree(migrated=False)
        self.addCleanup(td.cleanup)
        result = mod.inspect(root)
        self.assertTrue(result["assertion_pass"])
        self.assertFalse(result["provider_swarm_admitted"])
        self.assertEqual(result["status"], "PASS_QUARANTINE_ENFORCED")
        self.assertIn("CURRENT_CONTROLLER_PRESECRET_ADMISSION_GUARD_MISSING", result["admission_errors"])
        self.assertTrue(any(x.startswith("CURRENT_CONTROLLER_LEGACY_MARKER:") for x in result["admission_errors"]))

    def test_file_existence_alone_cannot_admit_controller(self):
        td, root = self.make_tree(migrated=False)
        self.addCleanup(td.cleanup)
        result = mod.inspect(root)
        self.assertTrue(result["current_controller_exists"])
        self.assertFalse(result["provider_swarm_admitted"])

    def test_free_only_weakening_breaks_authority_assertion(self):
        td, root = self.make_tree(migrated=True)
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["execution_policy"]["free_only"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        result = mod.inspect(root)
        self.assertFalse(result["assertion_pass"])
        self.assertIn("PROGRAM_FREE_ONLY", result["authority_errors"])

    def test_guard_text_after_first_key_lookup_is_not_admitted(self):
        td, root = self.make_tree(migrated=True)
        self.addCleanup(td.cleanup)
        path = root / "tools/run_go_zero_swarm.py"
        path.write_text(
            mod.OWNER_DIRECTIVE
            + "\n"
            + mod.CLAYVERSE_PROTOCOL
            + "\nBASE.collect_keys(spec)\nassert_clayverse_swarm_admission.py --require-admitted\n",
            encoding="utf-8",
        )
        result = mod.inspect(root)
        self.assertFalse(result["provider_swarm_admitted"])
        self.assertIn("CURRENT_CONTROLLER_GUARD_NOT_BEFORE_KEY_LOOKUP", result["admission_errors"])

    def test_stale_worker_protocol_blocks_wrapper_admission(self):
        td, root = self.make_tree(migrated=True)
        self.addCleanup(td.cleanup)
        path = root / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
        path.write_text(mod.LEGACY_PROTOCOL, encoding="utf-8")
        result = mod.inspect(root)
        self.assertFalse(result["provider_swarm_admitted"])
        self.assertIn("WORKER_PROTOCOL_CLAYVERSE_MARKER_MISSING", result["admission_errors"])
        self.assertIn("WORKER_PROTOCOL_LEGACY_MARKER_ACTIVE", result["admission_errors"])


if __name__ == "__main__":
    unittest.main()
