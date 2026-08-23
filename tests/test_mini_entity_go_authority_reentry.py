from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHIM = ROOT / "tools/run_mini_entity_go_swarm.py"


def load_shim():
    spec = importlib.util.spec_from_file_location("mini_entity_go_swarm_admission_test", SHIM)
    if spec is None or spec.loader is None:
        raise RuntimeError("SHIM_IMPORT_FAILED")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMiniEntityGoAuthorityReentry(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_shim()
        self.old_attestation = os.environ.get("CLAY_FREE_ONLY_ATTESTED")
        os.environ["CLAY_FREE_ONLY_ATTESTED"] = "attested"

    def tearDown(self) -> None:
        if self.old_attestation is None:
            os.environ.pop("CLAY_FREE_ONLY_ATTESTED", None)
        else:
            os.environ["CLAY_FREE_ONLY_ATTESTED"] = self.old_attestation

    def test_current_repository_authority_preflight_passes_without_provider_lookup(self):
        self.mod.preflight()

    def test_clayverse_worker_protocol_marker_fails_closed(self):
        old = self.mod.PROTOCOL
        with tempfile.TemporaryDirectory() as td:
            poison = Path(td) / "protocol.md"
            poison.write_text(
                "[CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]\n"
                "research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md\n"
                "MINI_ENTITY_PIPELINE_ALL_IN_ONE\n"
                "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT\n"
                "[/CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]\n",
                encoding="utf-8",
            )
            self.mod.PROTOCOL = poison
            with self.assertRaisesRegex(RuntimeError, "WORKER_PROTOCOL_MARKER_MISSING"):
                self.mod.preflight()
        self.mod.PROTOCOL = old

    def test_root_clayverse_program_fails_closed(self):
        old = self.mod.ROOT_CLAUDE
        with tempfile.TemporaryDirectory() as td:
            poison = Path(td) / "CLAUDE.md"
            poison.write_text(
                "PROGRAM=CLAYVERSE_SINGLE_CONTAINER\n"
                "STAGE=MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT\n"
                "research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md\n",
                encoding="utf-8",
            )
            self.mod.ROOT_CLAUDE = poison
            with self.assertRaisesRegex(RuntimeError, "ROOT_CLAUDE_PROGRAM_MISMATCH"):
                self.mod.preflight()
        self.mod.ROOT_CLAUDE = old

    def test_root_owner_drift_fails_closed(self):
        old = self.mod.ROOT_CLAUDE
        with tempfile.TemporaryDirectory() as td:
            poison = Path(td) / "CLAUDE.md"
            poison.write_text(
                "PROGRAM=MINI_ENTITY_PIPELINE_ALL_IN_ONE\n"
                "STAGE=MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT\n"
                "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md\n",
                encoding="utf-8",
            )
            self.mod.ROOT_CLAUDE = poison
            with self.assertRaisesRegex(RuntimeError, "ROOT_CLAUDE_OWNER_MISMATCH"):
                self.mod.preflight()
        self.mod.ROOT_CLAUDE = old

    def test_missing_free_only_attestation_fails_before_controller_handoff(self):
        os.environ.pop("CLAY_FREE_ONLY_ATTESTED", None)
        with self.assertRaisesRegex(RuntimeError, "CLAY_FREE_ONLY_ATTESTED_REQUIRED"):
            self.mod.preflight()


if __name__ == "__main__":
    unittest.main()
