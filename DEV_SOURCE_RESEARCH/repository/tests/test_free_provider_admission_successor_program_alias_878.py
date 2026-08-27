from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "free_provider_admission.py"
spec = importlib.util.spec_from_file_location("free_provider_admission_878", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class FreeProviderAdmissionSuccessorProgramAliasTests(unittest.TestCase):
    def _tree(
        self,
        *,
        steering_program: str | None = "ENTITYOS_HCU",
        steering_active_program: str | None = None,
        admission_epoch: str = "8.78",
    ):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        autonomous = root / "research_entity/claycode/autonomous"
        autonomous.mkdir(parents=True, exist_ok=True)

        steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_78.json"
        inbox = autonomous / "SUPERVISOR_INBOX.json"
        inbox.write_text(
            json.dumps(
                {
                    "schema_version": "8.78",
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "steering": steering_rel,
                }
            ),
            encoding="utf-8",
        )

        steering = {
            "schema_version": "8.78",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
        }
        if steering_program is not None:
            steering["program"] = steering_program
        if steering_active_program is not None:
            steering["active_program"] = steering_active_program
        (root / steering_rel).write_text(json.dumps(steering), encoding="utf-8")

        admission = autonomous / "FREE_PROVIDER_ADMISSION.json"
        admission.write_text(
            json.dumps(
                {
                    "schema": mod.SCHEMA,
                    "authority_epoch": admission_epoch,
                    "mode": "FREE_ONLY",
                    "product": "EntityOS",
                    "compute_architecture": "HCU",
                    "source": "ENTITYOS_HCU_CONTROL_PLANE",
                    "providers": {
                        name: {
                            "admitted": True,
                            "cost_class": "FREE",
                            "evidence_ref": f"evidence#{name}",
                        }
                        for name in mod.ALLOWED_PROVIDERS
                    },
                }
            ),
            encoding="utf-8",
        )
        return td, root, inbox, admission

    def test_current_878_program_field_is_accepted(self):
        td, root, inbox, admission = self._tree(); self.addCleanup(td.cleanup)
        epoch, ref = mod._resolve_current_supervisor(inbox_path=inbox, root=root)
        self.assertEqual(epoch, "8.78")
        self.assertTrue(ref.endswith("SUPERVISOR_STEERING_8_78.json"))
        payload = mod.load_provider_admission(
            path=admission,
            supervisor_inbox_path=inbox,
            root=root,
        )
        self.assertEqual(payload["authority_epoch"], "8.78")

    def test_legacy_active_program_field_remains_accepted(self):
        td, root, inbox, admission = self._tree(
            steering_program=None,
            steering_active_program="ENTITYOS_HCU",
        ); self.addCleanup(td.cleanup)
        payload = mod.load_provider_admission(
            path=admission,
            supervisor_inbox_path=inbox,
            root=root,
        )
        self.assertEqual(payload["product"], "EntityOS")

    def test_conflicting_program_aliases_fail_closed(self):
        td, root, inbox, _ = self._tree(
            steering_program="ENTITYOS_HCU",
            steering_active_program="OTHER_PROGRAM",
        ); self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(mod.ProviderAdmissionError, "SUPERVISOR_PROGRAM_ALIAS_CONFLICT"):
            mod._resolve_current_supervisor(inbox_path=inbox, root=root)

    def test_missing_program_authority_fails_closed(self):
        td, root, inbox, _ = self._tree(
            steering_program=None,
            steering_active_program=None,
        ); self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(mod.ProviderAdmissionError, "SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH"):
            mod._resolve_current_supervisor(inbox_path=inbox, root=root)

    def test_stale_admission_epoch_still_fails_closed(self):
        td, root, inbox, admission = self._tree(admission_epoch="8.72"); self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(mod.ProviderAdmissionError, "PROVIDER_ADMISSION_AUTHORITY_EPOCH_MISMATCH"):
            mod.load_provider_admission(
                path=admission,
                supervisor_inbox_path=inbox,
                root=root,
            )


if __name__ == "__main__":
    unittest.main()
