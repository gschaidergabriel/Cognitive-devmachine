import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "assert_clayverse_swarm_admission.py"
spec = importlib.util.spec_from_file_location("swarm_gate", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class ClayVerseSwarmAdmissionTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        values = {
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "active_program": mod.EXPECTED_PROGRAM,
                "active_stage": mod.EXPECTED_STAGE,
                "sole_owner_directive": mod.OWNER_DIRECTIVE,
                "together_api": "FORBIDDEN",
                "vps_testing": "FORBIDDEN",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": mod.EXPECTED_PROGRAM_ID,
                "stage": mod.EXPECTED_STAGE,
                "owner_directive": mod.OWNER_DIRECTIVE,
                "execution_policy": {
                    "free_only": True,
                    "together_forbidden": True,
                    "vps_testing_forbidden": True,
                    "isolated_sandbox_only": True,
                },
            },
            mod.CONTROL44: {
                "status": "ACTIVE",
                "program_identity_override": {
                    "active_program": mod.EXPECTED_PROGRAM,
                    "target_stage": mod.EXPECTED_STAGE,
                },
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                },
            },
        }
        for rel, value in values.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value), encoding="utf-8")
        controller = "\n".join([
            "CLAYVERSE_AUTHORITY_GUARD_BEFORE_SECRET_LOOKUP = True",
            "OWNER = 'CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md'",
            "PROTOCOL = '[CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]'",
            "macrocycle_id = 'm'",
            "unusual_experiment = None",
            'child_trigger="go"',
            "HTTP_429_PROVIDER_COOLDOWN = True",
            "def key_fingerprint(x): return x",
            "if status == 402: pass",
        ])
        base = "def key_fingerprint(x): return x\nif status == 429: pass\nif status == 402: pass\n"
        for rel, text in ((mod.DEFAULT_CONTROLLER, controller), (mod.DEFAULT_BASE_CONTROLLER, base)):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return td, root

    def test_clean_clayverse_controller_source_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertTrue(mod.validate(root)["pass"])

    def test_mini_entity_authority_is_rejected(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.DEFAULT_CONTROLLER
        path.write_text(path.read_text() + "\ncurrent Mini Entity\n", encoding="utf-8")
        self.assertTrue(any(x.startswith("LEGACY_MINI_ENTITY_ACTIVE_MARKER") for x in mod.validate(root)["errors"]))

    def test_missing_pre_secret_guard_is_rejected(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.DEFAULT_CONTROLLER
        path.write_text(path.read_text().replace("CLAYVERSE_AUTHORITY_GUARD_BEFORE_SECRET_LOOKUP = True\n", ""), encoding="utf-8")
        self.assertIn(
            "CONTROLLER_REQUIRED_MARKER_MISSING:CLAYVERSE_AUTHORITY_GUARD_BEFORE_SECRET_LOOKUP",
            mod.validate(root)["errors"],
        )

    def test_free_only_weakening_is_rejected(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["execution_policy"]["free_only"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_FREE_ONLY_MISSING", mod.validate(root)["errors"])

    def test_control44_is_required(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "INACTIVE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("CONTROL44_NOT_ACTIVE", mod.validate(root)["errors"])

    def test_macrocycle_and_unusual_lease_markers_are_required(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.DEFAULT_CONTROLLER
        text = path.read_text(encoding="utf-8").replace("macrocycle_id = 'm'\n", "").replace("unusual_experiment = None\n", "")
        path.write_text(text, encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROLLER_REQUIRED_MARKER_MISSING:macrocycle_id", errors)
        self.assertIn("CONTROLLER_REQUIRED_MARKER_MISSING:unusual_experiment", errors)


if __name__ == "__main__":
    unittest.main()
