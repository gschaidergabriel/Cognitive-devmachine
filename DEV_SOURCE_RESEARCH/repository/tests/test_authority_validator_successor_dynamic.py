from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator_successor", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class SuccessorDynamicAuthorityResolverTests(unittest.TestCase):
    def _tree(self, *, inbox_epoch: str = "8.70", steering_epoch: str = "8.70", steering_ref: str = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_70.json"):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        inbox = root / mod.SUPERVISOR_INBOX
        inbox.parent.mkdir(parents=True, exist_ok=True)
        inbox.write_text(json.dumps({
            "schema_version": inbox_epoch,
            "active_program": mod.CURRENT_PROGRAM,
            "product": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "steering": steering_ref,
        }), encoding="utf-8")
        if ".." not in Path(steering_ref).parts and not Path(steering_ref).is_absolute():
            steering = root / steering_ref
            steering.parent.mkdir(parents=True, exist_ok=True)
            steering.write_text(json.dumps({
                "schema_version": steering_epoch,
                "active_program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "free_only": {"enabled": True, "no_paid_fallback": True, "together_forbidden": True},
                "promotion": {"entityos_whole_runtime_pass": False, "provider_runtime_credit": 0, "training_credit": 0},
            }), encoding="utf-8")
        return td, root

    def test_inbox_outranks_stale_validator_fallback_constant(self):
        td, root = self._tree(); self.addCleanup(td.cleanup)
        epoch, rel, steering, inbox = mod.resolve_current_supervisor(
            root,
            {"authority_correction": mod.CURRENT_AUTHORITY},
        )
        self.assertEqual(epoch, "8.70")
        self.assertEqual(rel, "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_70.json")
        self.assertEqual(steering["schema_version"], "8.70")
        self.assertIsNotNone(inbox)
        self.assertNotEqual(rel, mod.CURRENT_AUTHORITY)

    def test_inbox_and_steering_epoch_mismatch_fails_closed(self):
        td, root = self._tree(inbox_epoch="8.70", steering_epoch="8.69"); self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(mod.AuthorityResolutionError, "SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH"):
            mod.resolve_current_supervisor(root, {"authority_correction": mod.CURRENT_AUTHORITY})

    def test_inbox_path_traversal_fails_closed(self):
        td, root = self._tree(steering_ref="../../evil.json"); self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(mod.AuthorityResolutionError, "CURRENT_STEERING_POINTER_INVALID"):
            mod.resolve_current_supervisor(root, {"authority_correction": mod.CURRENT_AUTHORITY})


if __name__ == "__main__":
    unittest.main()
