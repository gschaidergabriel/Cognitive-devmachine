#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JSPACE_GWT = ROOT / "the artefact" / "blogpost_entity" / "jspace_gwt"
if str(JSPACE_GWT) not in sys.path:
    sys.path.insert(0, str(JSPACE_GWT))

from test_unified_cognitive_fabric_receipt_v1 import valid_receipt as base_cycle  # noqa: E402
from test_validate_jspace_gwt_boot_binding_v1 import D6, manifest_bytes, source_lock_for, valid_manifest, valid_receipt as make_boot_receipt  # noqa: E402
from validate_unified_cognitive_fabric_chain_v1 import BOOT_SCHEMA, _canonical_sha256, _file_sha256, validate_chain  # noqa: E402

ALT_A = "a" * 64
ALT_B = "b" * 64
ALT_C = "c" * 64
ALT_D = "d" * 64
ALT_E = "e" * 64


def build_cycle_from_boot(boot: dict, manifest_path: Path, source_lock: dict) -> dict:
    cycle = base_cycle()
    cycle["boot_binding"] = {
        "schema": BOOT_SCHEMA,
        "receipt_sha256": _canonical_sha256(boot),
        "manifest_file_sha256": _file_sha256(manifest_path),
        "source_lock_sha256": _canonical_sha256(source_lock),
    }
    cycle["source"].update(commit=boot["source"]["main_sha"], tree=boot["source"]["tree_sha"], dirty=False)
    cycle["bundled_core"].update(
        manifest_digest=boot["bundled_core"]["manifest_sha256"],
        checkpoint_digest=boot["bundled_core"]["checkpoint_sha256"],
        tokenizer_digest=boot["bundled_core"]["tokenizer_sha256"],
        runtime_digest=boot["bundled_core"]["runtime_sha256"],
    )
    cycle["identity"].update(zero_digest=boot["zero_grf"]["zero_identity_sha256"], grf_digest=boot["zero_grf"]["grf_sha256"])
    cycle["fabric"].update(
        jspace_profile_digest=boot["jspace"]["jspace_profile_sha256"],
        lens_profile_digest=boot["jspace"]["lens_profile_sha256"],
        workspace_policy_digest=boot["gwt"]["workspace_policy_sha256"],
        workspace_calibration_digest=boot["gwt"]["calibration_sha256"],
    )
    cycle["inference"].update(adapter_version=boot["claude_adapter"]["adapter_version"], capability_profile_digest=boot["claude_adapter"]["capability_profile_sha256"])
    return cycle


class UnifiedCognitiveFabricChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = valid_manifest(); self.raw = manifest_bytes(self.manifest)
        self.manifest_path = self.root / "manifest.json"; self.manifest_path.write_bytes(self.raw)
        self.source_lock = source_lock_for(self.manifest, self.raw)
        self.boot = make_boot_receipt(self.manifest, self.raw)
        self.cycle = build_cycle_from_boot(self.boot, self.manifest_path, self.source_lock)

    def test_valid_cycle_requires_full_canonical_boot_ancestry(self):
        self.assertEqual(validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock), [])

    def test_missing_boot_binding_fails(self):
        self.cycle.pop("boot_binding")
        self.assertIn("BOOT_BINDING_OBJECT_REQUIRED", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_boot_receipt_digest_mismatch_fails(self):
        self.cycle["boot_binding"]["receipt_sha256"] = ALT_A
        self.assertIn("BOOT_RECEIPT_DIGEST_MISMATCH", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_source_lock_digest_mismatch_fails(self):
        self.cycle["boot_binding"]["source_lock_sha256"] = ALT_A
        self.assertIn("BOOT_SOURCE_LOCK_DIGEST_MISMATCH", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_placeholder_boot_binding_digest_fails_typed(self):
        self.cycle["boot_binding"]["source_lock_sha256"] = "f" * 64
        self.assertIn("BOOT_BINDING_SOURCE_LOCK_DIGEST_INVALID:PLACEHOLDER_FORBIDDEN", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_cycle_cannot_substitute_boot_runtime_identity(self):
        self.cycle["bundled_core"]["runtime_digest"] = ALT_A
        self.assertIn("BOOT_CORE_RUNTIME_MISMATCH", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_dirty_boot_cannot_anchor_clean_cycle(self):
        self.boot["source"]["dirty"] = True; self.boot["source"]["dirty_diff_sha256"] = D6
        self.cycle["boot_binding"]["receipt_sha256"] = _canonical_sha256(self.boot)
        self.assertIn("BOOT_SOURCE_DIRTY_FOR_CYCLE", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))

    def test_self_consistent_false_bundle_is_stopped_by_repository_source_lock(self):
        original_lock = copy.deepcopy(self.source_lock)
        poisoned_manifest = copy.deepcopy(self.manifest)
        poisoned_manifest["checkpoint_digest"] = ALT_A
        poisoned_manifest["tokenizer_digest"] = ALT_E
        poisoned_manifest["jspace_profile_digest"] = ALT_D
        poisoned_manifest["lens_profile_digest"] = ALT_C
        poisoned_manifest["workspace_calibration_digest"] = ALT_B
        poisoned_raw = manifest_bytes(poisoned_manifest)
        poisoned_path = self.root / "poisoned_manifest.json"; poisoned_path.write_bytes(poisoned_raw)
        poisoned_boot = make_boot_receipt(poisoned_manifest, poisoned_raw)
        poisoned_cycle = build_cycle_from_boot(poisoned_boot, poisoned_path, original_lock)
        errors = validate_chain(poisoned_cycle, poisoned_boot, poisoned_path, original_lock)
        self.assertTrue(any("SOURCE_LOCK_MANIFEST_FILE_MISMATCH" in error for error in errors), errors)

    def test_claude_capability_identity_is_cross_bound(self):
        self.cycle["inference"]["capability_profile_digest"] = ALT_A
        self.assertIn("BOOT_CLAUDE_CAPABILITY_PROFILE_MISMATCH", validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock))


if __name__ == "__main__":
    unittest.main()
