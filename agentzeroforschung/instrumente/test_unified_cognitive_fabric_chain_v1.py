#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
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
from test_validate_jspace_gwt_boot_binding_v1 import (  # noqa: E402
    D6,
    manifest_bytes,
    source_lock_for,
    valid_manifest,
    valid_receipt as make_boot_receipt,
)
from validate_unified_cognitive_fabric_chain_v1 import (  # noqa: E402
    BOOT_SCHEMA,
    _canonical_sha256,
    _file_sha256,
    validate_chain,
)


def build_cycle_from_boot(boot: dict, manifest_path: Path, source_lock: dict) -> dict:
    cycle = base_cycle()
    cycle["boot_binding"] = {
        "schema": BOOT_SCHEMA,
        "receipt_sha256": _canonical_sha256(boot),
        "manifest_file_sha256": _file_sha256(manifest_path),
        "source_lock_sha256": _canonical_sha256(source_lock),
    }
    cycle["source"].update(
        commit=boot["source"]["main_sha"],
        tree=boot["source"]["tree_sha"],
        dirty=False,
    )
    cycle["bundled_core"].update(
        manifest_digest=boot["bundled_core"]["manifest_sha256"],
        checkpoint_digest=boot["bundled_core"]["checkpoint_sha256"],
        tokenizer_digest=boot["bundled_core"]["tokenizer_sha256"],
        runtime_digest=boot["bundled_core"]["runtime_sha256"],
    )
    cycle["identity"].update(
        zero_digest=boot["zero_grf"]["zero_identity_sha256"],
        grf_digest=boot["zero_grf"]["grf_sha256"],
    )
    cycle["fabric"].update(
        jspace_profile_digest=boot["jspace"]["jspace_profile_sha256"],
        lens_profile_digest=boot["jspace"]["lens_profile_sha256"],
        workspace_policy_digest=boot["gwt"]["workspace_policy_sha256"],
        workspace_calibration_digest=boot["gwt"]["calibration_sha256"],
    )
    cycle["inference"].update(
        adapter_version=boot["claude_adapter"]["adapter_version"],
        capability_profile_digest=boot["claude_adapter"]["capability_profile_sha256"],
    )
    return cycle


class UnifiedCognitiveFabricChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = valid_manifest()
        self.raw = manifest_bytes(self.manifest)
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_bytes(self.raw)
        self.source_lock = source_lock_for(self.manifest, self.raw)
        self.boot = make_boot_receipt(self.manifest, self.raw)
        self.cycle = build_cycle_from_boot(self.boot, self.manifest_path, self.source_lock)

    def test_valid_cycle_requires_full_canonical_boot_ancestry(self) -> None:
        self.assertEqual(
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
            [],
        )

    def test_structurally_valid_cycle_without_boot_binding_fails(self) -> None:
        self.cycle.pop("boot_binding")
        self.assertIn(
            "BOOT_BINDING_OBJECT_REQUIRED",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_boot_receipt_digest_is_part_of_cycle_identity(self) -> None:
        self.cycle["boot_binding"]["receipt_sha256"] = "f" * 64
        self.assertIn(
            "BOOT_RECEIPT_DIGEST_MISMATCH",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_source_lock_digest_is_part_of_cycle_identity(self) -> None:
        self.cycle["boot_binding"]["source_lock_sha256"] = "f" * 64
        self.assertIn(
            "BOOT_SOURCE_LOCK_DIGEST_MISMATCH",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_cycle_cannot_substitute_boot_manifest_identity(self) -> None:
        self.cycle["bundled_core"]["manifest_digest"] = "f" * 64
        self.assertIn(
            "BOOT_CORE_MANIFEST_MISMATCH",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_cycle_cannot_substitute_claude_capability_identity(self) -> None:
        self.cycle["inference"]["capability_profile_digest"] = "f" * 64
        self.assertIn(
            "BOOT_CLAUDE_CAPABILITY_PROFILE_MISMATCH",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_dirty_boot_cannot_anchor_clean_cycle(self) -> None:
        self.boot["source"]["dirty"] = True
        self.boot["source"]["dirty_diff_sha256"] = D6
        self.cycle["boot_binding"]["receipt_sha256"] = _canonical_sha256(self.boot)
        self.assertIn(
            "BOOT_SOURCE_DIRTY_FOR_CYCLE",
            validate_chain(self.cycle, self.boot, self.manifest_path, self.source_lock),
        )

    def test_self_consistent_false_bundle_is_stopped_by_repository_source_lock(self) -> None:
        original_lock = copy.deepcopy(self.source_lock)
        poisoned_manifest = copy.deepcopy(self.manifest)
        poisoned_manifest["checkpoint_digest"] = "f" * 64
        poisoned_manifest["tokenizer_digest"] = "e" * 64
        poisoned_manifest["jspace_profile_digest"] = "d" * 64
        poisoned_manifest["lens_profile_digest"] = "c" * 64
        poisoned_manifest["workspace_calibration_digest"] = "b" * 64
        poisoned_raw = manifest_bytes(poisoned_manifest)
        poisoned_path = self.root / "poisoned_manifest.json"
        poisoned_path.write_bytes(poisoned_raw)
        poisoned_boot = make_boot_receipt(poisoned_manifest, poisoned_raw)
        poisoned_cycle = build_cycle_from_boot(poisoned_boot, poisoned_path, original_lock)

        errors = validate_chain(poisoned_cycle, poisoned_boot, poisoned_path, original_lock)
        self.assertTrue(
            any("SOURCE_LOCK_MANIFEST_FILE_MISMATCH" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
