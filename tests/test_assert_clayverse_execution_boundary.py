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
                "execution_surface": "AUTHORIZED_ISOLATED_SANDBOX_OR_INDEPENDENT_KERNEL_GUEST_ONLY",
                "vps_testing": "FORBIDDEN",
                "vps_testing_scope": mod.DIRECT_SCOPE,
                "vps_disposable_independent_kernel_guest_testing": mod.GUEST_ADMISSION,
                "vps_execution_directive": mod.VPS_GUEST_DIRECTIVE,
            },
            mod.PROGRAM: {
                "execution_policy": {
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "vps_testing_forbidden_scope": mod.DIRECT_SCOPE,
                    "vps_disposable_independent_kernel_guest_testing_admitted": True,
                    "qemu_tcg_guest_development_evidence_only": True,
                    "final_hardware_microvm_credit_requires_hardware_virtualized_guest": True,
                    "vps_execution_directive": mod.VPS_GUEST_DIRECTIVE,
                }
            },
            mod.CONTROL44: {
                "composition_rule": "PRESERVE ALL 4.2 EXECUTION-BOUNDARY RULES",
                "preserved_hard_rules": {
                    "vps_testing": False,
                    "vps_testing_scope": mod.DIRECT_SCOPE,
                    "vps_disposable_independent_kernel_guest_testing": True,
                    "qemu_tcg_guest_final_hardware_microvm_credit": False,
                    "vps_execution_directive": mod.VPS_GUEST_DIRECTIVE,
                },
            },
            mod.STEERING844: {
                "adjudication": {
                    "vps_testing": False,
                    "vps_testing_scope": mod.DIRECT_SCOPE,
                    "vps_disposable_independent_kernel_guest_testing": True,
                    "qemu_tcg_guest_final_hardware_microvm_credit": False,
                }
            },
        }
        text_files = {
            mod.SANDBOX_DIRECTIVE: (
                "direct test/build/experiment execution on a VPS host remains forbidden\n"
                "freshly created disposable independent-kernel guest test sandbox\n"
            ),
            mod.VPS_GUEST_DIRECTIVE: (
                "Direct execution of product/test commands on the VPS host remains forbidden.\n"
                "disposable independent-kernel guest\n"
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

    def test_current_host_guest_split_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["credit"], "SOURCE_POLICY_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT")

    def test_guest_lane_removal_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.PROGRAM
        data = json.loads(path.read_text(encoding="utf-8"))
        data["execution_policy"]["vps_disposable_independent_kernel_guest_testing_admitted"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_DISPOSABLE_GUEST_ADMISSION_MISSING", mod.validate(root)["errors"])

    def test_scope_broadening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.BOOTSTRAP
        data = json.loads(path.read_text(encoding="utf-8"))
        data["vps_testing_scope"] = "ALL_VPS_HOSTED_EXECUTION"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_VPS_SCOPE_NOT_DIRECT_HOST_ONLY", mod.validate(root)["errors"])

    def test_direct_host_ban_removal_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.VPS_GUEST_DIRECTIVE
        path.write_text("disposable independent-kernel guest\n", encoding="utf-8")
        self.assertIn("VPS_GUEST_DIRECTIVE_HOST_BAN_MISSING", mod.validate(root)["errors"])

    def test_tcg_cannot_mint_final_hardware_microvm_credit(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text(encoding="utf-8"))
        data["preserved_hard_rules"]["qemu_tcg_guest_final_hardware_microvm_credit"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("CONTROL44_TCG_FINAL_CREDIT_WEAKENED", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
