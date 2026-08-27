import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "assert_clayverse_execution_boundary.py"
spec = importlib.util.spec_from_file_location("execution_boundary", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class ExecutionBoundaryTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        json_files = {
            mod.BOOTSTRAP: {
                "execution_surface": mod.EXPECTED_SURFACE,
                "vps_testing": "FORBIDDEN",
                "vps_disposable_independent_kernel_guest_testing": "FORBIDDEN",
                "self_hosted_vps_test_runners": "FORBIDDEN",
                "production_host_testing": "FORBIDDEN",
            },
            mod.PROGRAM: {
                "execution_policy": {
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "vps_disposable_independent_kernel_guest_testing_admitted": False,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                }
            },
            mod.CONTROL44: {
                "composition_rule": "PRESERVE ALL 4.2 EXECUTION-BOUNDARY RULES",
                "preserved_hard_rules": {
                    "vps_testing": False,
                    "vps_disposable_independent_kernel_guest_testing": False,
                    "self_hosted_vps_test_runners": False,
                    "production_host_testing": False,
                    "authorized_isolated_sandbox_only": True,
                },
            },
            mod.STEERING844: {
                "adjudication": {
                    "vps_testing": False,
                    "vps_disposable_independent_kernel_guest_testing": False,
                    "self_hosted_vps_test_runners": False,
                    "production_host_testing": False,
                    "authorized_isolated_sandbox_only": True,
                }
            },
        }
        text_files = {
            mod.SANDBOX_DIRECTIVE: (
                "Current authority: 2026-08-23\n"
                "VPS testing is **FORBIDDEN**.\n"
                "VPS-hosted disposable KVM/VM/microVM/TCG guest testing is **FORBIDDEN**.\n"
                "Self-hosted VPS test runners are **FORBIDDEN**.\n"
                "Production/deployment-host testing is **FORBIDDEN**.\n"
            ),
            mod.VPS_GUEST_DIRECTIVE: (
                "Original authority time: 2026-08-18\n"
                "**Status:** **SUPERSEDED**\n"
                "superseded by the newer owner-directed ClayVerse bootstrap dated **2026-08-23**\n"
                "VPS-hosted disposable KVM/VM/microVM/TCG guest testing is forbidden\n"
            ),
        }
        for rel, data in json_files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")
        for rel, text in text_files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return td, root

    def test_current_sandbox_only_contract_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["credit"], "SOURCE_POLICY_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT")

    def test_program_guest_readmission_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.PROGRAM
        data = json.loads(path.read_text(encoding="utf-8"))
        data["execution_policy"]["vps_disposable_independent_kernel_guest_testing_admitted"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_VPS_GUEST_REAUTHORIZED", mod.validate(root)["errors"])

    def test_control_guest_readmission_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text(encoding="utf-8"))
        data["preserved_hard_rules"]["vps_disposable_independent_kernel_guest_testing"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("CONTROL44_VPS_GUEST_REAUTHORIZED", mod.validate(root)["errors"])

    def test_stale_vps_directive_current_status_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.VPS_GUEST_DIRECTIVE
        path.write_text(
            "Original authority time: 2026-08-18\n"
            "**Status:** **CURRENT**\n"
            "disposable independent-kernel guest is admitted\n",
            encoding="utf-8",
        )
        self.assertIn("VPS_GUEST_DIRECTIVE_NOT_SUPERSEDED", mod.validate(root)["errors"])

    def test_bootstrap_stale_directive_pointer_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.BOOTSTRAP
        data = json.loads(path.read_text(encoding="utf-8"))
        data["vps_execution_directive"] = mod.VPS_GUEST_DIRECTIVE
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_STALE_VPS_DIRECTIVE_POINTER", mod.validate(root)["errors"])

    def test_self_hosted_vps_readmission_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.PROGRAM
        data = json.loads(path.read_text(encoding="utf-8"))
        data["execution_policy"]["self_hosted_vps_test_runners_forbidden"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_SELF_HOSTED_BAN_MISSING", mod.validate(root)["errors"])

    def test_production_host_readmission_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.STEERING844
        data = json.loads(path.read_text(encoding="utf-8"))
        data["adjudication"]["production_host_testing"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("STEERING844_PRODUCTION_REAUTHORIZED", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
