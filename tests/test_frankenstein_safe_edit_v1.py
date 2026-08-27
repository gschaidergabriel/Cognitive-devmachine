import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_safe_edit_v1.py"
)
spec = importlib.util.spec_from_file_location("frankenstein_safe_edit_v1", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SafeEditTests(unittest.TestCase):
    def make_repo(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Test"],
            check=True,
        )
        (root / "tools").mkdir()
        (root / "tools/grid10_fabric.py").write_text("alpha\nbeta\ngamma\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
        return td, root

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def patch(self, old="beta", new="beta2"):
        return (
            "diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py\n"
            "index 85c3040..0000000 100644\n"
            "--- a/tools/grid10_fabric.py\n"
            "+++ b/tools/grid10_fabric.py\n"
            "@@ -1,3 +1,3 @@\n"
            " alpha\n"
            f"-{old}\n"
            f"+{new}\n"
            " gamma\n"
        )

    def test_exact_preimage_patch_and_verify_pass(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            receipt = mod.safe_apply_verified_patch(
                root,
                self.patch(),
                allowed_paths=["tools/grid10_fabric.py"],
                base_sha256={"tools/grid10_fabric.py": self.digest(p)},
                verify_argv=[
                    "python3",
                    "-c",
                    "from pathlib import Path; assert 'beta2' in Path('tools/grid10_fabric.py').read_text()",
                ],
            )
            self.assertEqual(receipt.changed_paths, ("tools/grid10_fabric.py",))
            self.assertEqual(p.read_text(), "alpha\nbeta2\ngamma\n")
        finally:
            td.cleanup()

    def test_stale_preimage_rejected_without_mutation(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            before = p.read_bytes()
            with self.assertRaises(mod.SafeEditError):
                mod.safe_apply_verified_patch(
                    root,
                    self.patch(),
                    allowed_paths=["tools/grid10_fabric.py"],
                    base_sha256={"tools/grid10_fabric.py": "0" * 64},
                    verify_argv=["true"],
                )
            self.assertEqual(p.read_bytes(), before)
        finally:
            td.cleanup()

    def test_context_mismatch_rejected_even_with_declared_hash(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            before = p.read_bytes()
            bad_patch = self.patch(old="NOT_PRESENT", new="x")
            with self.assertRaises(mod.SafeEditError):
                mod.safe_apply_verified_patch(
                    root,
                    bad_patch,
                    allowed_paths=["tools/grid10_fabric.py"],
                    base_sha256={"tools/grid10_fabric.py": self.digest(p)},
                    verify_argv=["true"],
                )
            self.assertEqual(p.read_bytes(), before)
        finally:
            td.cleanup()

    def test_unapproved_path_rejected(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            with self.assertRaises(mod.SafeEditError):
                mod.safe_apply_verified_patch(
                    root,
                    self.patch(),
                    allowed_paths=["other.py"],
                    base_sha256={"tools/grid10_fabric.py": self.digest(p)},
                    verify_argv=["true"],
                )
        finally:
            td.cleanup()

    def test_dirty_checkout_rejected(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            base = self.digest(p)
            p.write_text(p.read_text() + "dirty\n")
            with self.assertRaises(mod.SafeEditError):
                mod.safe_apply_verified_patch(
                    root,
                    self.patch(),
                    allowed_paths=["tools/grid10_fabric.py"],
                    base_sha256={"tools/grid10_fabric.py": base},
                    verify_argv=["true"],
                )
        finally:
            td.cleanup()

    def test_verify_failure_rolls_back_exactly(self):
        td, root = self.make_repo()
        try:
            p = root / "tools/grid10_fabric.py"
            before = p.read_bytes()
            with self.assertRaises(mod.SafeEditError):
                mod.safe_apply_verified_patch(
                    root,
                    self.patch(),
                    allowed_paths=["tools/grid10_fabric.py"],
                    base_sha256={"tools/grid10_fabric.py": self.digest(p)},
                    verify_argv=["python3", "-c", "raise SystemExit(7)"],
                )
            self.assertEqual(p.read_bytes(), before)
            status = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain"],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(status.stdout, "")
        finally:
            td.cleanup()

    def test_static_donor_gate_rejects_legacy_and_requires_safe_call(self):
        legacy = "def dispatch_helper_task_direct():\n    apply_file_blocks(root, blocks)\n"
        safe = "def dispatch_helper_task_direct():\n    safe_apply_verified_patch(root, patch)\n"
        mixed = (
            "def dispatch_helper_task_direct():\n"
            "    safe_apply_verified_patch(root, patch)\n"
            "    apply_file_blocks(root, blocks)\n"
        )
        self.assertFalse(mod.donor_dispatch_uses_safe_patch(legacy))
        self.assertTrue(mod.donor_dispatch_uses_safe_patch(safe))
        self.assertFalse(mod.donor_dispatch_uses_safe_patch(mixed))


if __name__ == "__main__":
    unittest.main()
