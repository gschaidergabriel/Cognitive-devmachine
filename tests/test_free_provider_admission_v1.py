#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission


class ProviderAdmissionV1Tests(unittest.TestCase):
    def make_repo(
        self,
        *,
        supervisor_epoch: str = "8.67",
        steering_epoch: str = "8.67",
        admission_epoch: str = "8.67",
        provider_overrides: dict | None = None,
        steering_ref: str = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json",
    ):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        auto = root / "research_entity/claycode/autonomous"
        auto.mkdir(parents=True)

        inbox = {"schema_version": supervisor_epoch, "steering": steering_ref}
        inbox_path = auto / "SUPERVISOR_INBOX.json"
        inbox_path.write_text(json.dumps(inbox), encoding="utf-8")

        rel = Path(steering_ref)
        if not rel.is_absolute() and ".." not in rel.parts:
            steering_path = root / rel
            steering_path.parent.mkdir(parents=True, exist_ok=True)
            steering_path.write_text(
                json.dumps(
                    {
                        "schema_version": steering_epoch,
                        "active_program": "ENTITYOS_HCU",
                        "product": "EntityOS",
                        "integrated_cognition_compute_architecture": "HCU",
                    }
                ),
                encoding="utf-8",
            )

        providers = {
            provider: {
                "admitted": False,
                "cost_class": "UNKNOWN",
                "evidence_ref": "fixture:evidence",
            }
            for provider in sorted(admission.ALLOWED_PROVIDERS)
        }
        for provider, values in (provider_overrides or {}).items():
            providers[provider].update(values)

        admission_payload = {
            "schema": admission.SCHEMA,
            "authority_epoch": admission_epoch,
            "mode": "FREE_ONLY",
            "product": "EntityOS",
            "compute_architecture": "HCU",
            "source": "ENTITYOS_HCU_CONTROL_PLANE",
            "providers": providers,
        }
        admission_path = auto / "FREE_PROVIDER_ADMISSION.json"
        admission_path.write_text(json.dumps(admission_payload), encoding="utf-8")
        return td, root, admission_path, inbox_path

    def _patch_canonical_authority(self, root: Path, admission_path: Path, inbox_path: Path):
        return (
            mock.patch.object(admission, "ROOT", root),
            mock.patch.object(admission, "ADMISSION_PATH", admission_path),
            mock.patch.object(admission, "SUPERVISOR_INBOX_PATH", inbox_path),
        )

    def test_current_supervisor_outranks_lagging_bootstrap_cache(self):
        td, root, admission_path, inbox_path = self.make_repo(
            provider_overrides={"groq": {"admitted": True, "cost_class": "FREE"}}
        )
        try:
            continuity = root / "research_entity/continuity"
            continuity.mkdir(parents=True)
            (continuity / "BOOTSTRAP_MINIMAL.json").write_text(
                '{"schema_version":"8.66"}', encoding="utf-8"
            )
            payload = admission.load_provider_admission(
                admission_path, supervisor_inbox_path=inbox_path, root=root
            )
            self.assertTrue(payload["providers"]["groq"]["admitted"])
            p_root, p_admission, p_inbox = self._patch_canonical_authority(
                root, admission_path, inbox_path
            )
            with p_root, p_admission, p_inbox:
                self.assertTrue(admission.provider_is_admitted_free("groq"))
        finally:
            td.cleanup()

    def test_caller_supplied_payload_cannot_self_admit(self):
        td, root, admission_path, inbox_path = self.make_repo()
        try:
            forged = {
                "providers": {
                    "groq": {
                        "admitted": True,
                        "cost_class": "FREE",
                        "evidence_ref": "caller:forged",
                    }
                }
            }
            p_root, p_admission, p_inbox = self._patch_canonical_authority(
                root, admission_path, inbox_path
            )
            with p_root, p_admission, p_inbox:
                self.assertFalse(admission.provider_is_admitted_free("groq", forged))
                self.assertNotIn("groq", admission.admitted_provider_names(forged))
        finally:
            td.cleanup()

    def test_stale_provider_admission_epoch_fails_closed(self):
        td, root, admission_path, inbox_path = self.make_repo(admission_epoch="8.66")
        try:
            with self.assertRaisesRegex(
                admission.ProviderAdmissionError, "AUTHORITY_EPOCH_MISMATCH"
            ):
                admission.load_provider_admission(
                    admission_path, supervisor_inbox_path=inbox_path, root=root
                )
        finally:
            td.cleanup()

    def test_inbox_steering_epoch_mismatch_fails_closed(self):
        td, root, admission_path, inbox_path = self.make_repo(steering_epoch="8.66")
        try:
            with self.assertRaisesRegex(
                admission.ProviderAdmissionError, "INBOX_STEERING_EPOCH_MISMATCH"
            ):
                admission.load_provider_admission(
                    admission_path, supervisor_inbox_path=inbox_path, root=root
                )
        finally:
            td.cleanup()

    def test_steering_path_traversal_fails_closed(self):
        td, root, admission_path, inbox_path = self.make_repo(
            steering_ref="../outside.json"
        )
        try:
            with self.assertRaisesRegex(
                admission.ProviderAdmissionError, "STEERING_REF_INVALID"
            ):
                admission.load_provider_admission(
                    admission_path, supervisor_inbox_path=inbox_path, root=root
                )
        finally:
            td.cleanup()

    def test_nonfree_provider_cannot_be_admitted(self):
        td, root, admission_path, inbox_path = self.make_repo(
            provider_overrides={"groq": {"admitted": True, "cost_class": "PAID"}}
        )
        try:
            with self.assertRaisesRegex(
                admission.ProviderAdmissionError, "NONFREE_CANNOT_BE_ADMITTED"
            ):
                admission.load_provider_admission(
                    admission_path, supervisor_inbox_path=inbox_path, root=root
                )
        finally:
            td.cleanup()

    def test_unknown_provider_record_fails_closed(self):
        td, root, admission_path, inbox_path = self.make_repo()
        try:
            payload = json.loads(admission_path.read_text(encoding="utf-8"))
            payload["providers"]["other"] = {
                "admitted": False,
                "cost_class": "UNKNOWN",
                "evidence_ref": "fixture:evidence",
            }
            admission_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                admission.ProviderAdmissionError, "UNKNOWN_PROVIDER"
            ):
                admission.load_provider_admission(
                    admission_path, supervisor_inbox_path=inbox_path, root=root
                )
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
