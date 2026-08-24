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

import provider_call_boundary as boundary
import free_provider_admission


class ProviderCallBoundary869Tests(unittest.TestCase):
    def make_root(self, execution: str = "RUNTIME_QUARANTINED"):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        auto = root / "research_entity/claycode/autonomous"
        auto.mkdir(parents=True)
        steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_69.json"
        (auto / "SUPERVISOR_INBOX.json").write_text(json.dumps({"schema_version": "8.69", "steering": steering_rel}), encoding="utf-8")
        (root / steering_rel).write_text(json.dumps({
            "schema_version": "8.69",
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "free_only": {"enabled": True, "external_llm_provider_execution": execution},
        }), encoding="utf-8")
        return td, root, auto / "SUPERVISOR_INBOX.json"

    def test_runtime_quarantine_overrides_even_positive_typed_free_record(self):
        td, root, inbox = self.make_root("RUNTIME_QUARANTINED")
        self.addCleanup(td.cleanup)
        with mock.patch.object(boundary, "ROOT", root), mock.patch.object(boundary, "INBOX_PATH", inbox), mock.patch.object(free_provider_admission, "provider_is_admitted_free", return_value=True):
            self.assertFalse(boundary.provider_call_is_allowed("groq"))
            with self.assertRaisesRegex(boundary.ProviderCallBoundaryError, "PROVIDER_CALL_BLOCKED"):
                boundary.assert_provider_call_allowed("groq")

    def test_unknown_execution_state_fails_closed(self):
        td, root, inbox = self.make_root("UNKNOWN")
        self.addCleanup(td.cleanup)
        with mock.patch.object(boundary, "ROOT", root), mock.patch.object(boundary, "INBOX_PATH", inbox), mock.patch.object(free_provider_admission, "provider_is_admitted_free", return_value=True):
            self.assertFalse(boundary.provider_call_is_allowed("groq"))

    def test_explicit_runtime_enable_still_requires_typed_free(self):
        td, root, inbox = self.make_root("ENABLED")
        self.addCleanup(td.cleanup)
        with mock.patch.object(boundary, "ROOT", root), mock.patch.object(boundary, "INBOX_PATH", inbox), mock.patch.object(free_provider_admission, "provider_is_admitted_free", return_value=False):
            self.assertFalse(boundary.provider_call_is_allowed("groq"))
        with mock.patch.object(boundary, "ROOT", root), mock.patch.object(boundary, "INBOX_PATH", inbox), mock.patch.object(free_provider_admission, "provider_is_admitted_free", return_value=True):
            self.assertTrue(boundary.provider_call_is_allowed("groq"))

    def test_current_branch_supervisor_is_quarantined(self):
        state = boundary.current_boundary_state()
        self.assertEqual(state["authority_epoch"], "8.69")
        self.assertTrue(state["runtime_quarantined"])


if __name__ == "__main__":
    unittest.main()
