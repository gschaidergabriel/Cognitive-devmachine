from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chain = load(ROOT / "tools" / "validate_ucf_boot_ancestry_chain_v1.py", "ucf_boot_chain")
ucf = load(ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py", "canonical_ucf")
ucf_fixture = load(ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py", "canonical_ucf_fixture")

JSPACE_GWT = ROOT / "the artefact" / "blogpost_entity" / "jspace_gwt"
if str(JSPACE_GWT) not in sys.path:
    sys.path.insert(0, str(JSPACE_GWT))
boot_fixture = load(JSPACE_GWT / "test_validate_jspace_gwt_boot_binding_v1.py", "canonical_boot_fixture")

ALT = "9" * 64


def redigest(cycle: dict) -> dict:
    cycle["receipt_envelope_digest"] = "0" * 64
    cycle["receipt_envelope_digest"] = ucf.canonical_digest(cycle)
    return cycle


def cycle_from_boot(boot: dict) -> dict:
    cycle = ucf_fixture.valid_receipt()
    cycle["source"].update(commit=boot["source"]["main_sha"], tree=boot["source"]["tree_sha"], dirty=False)
    cycle["identity"].update(
        zero_identity_digest=boot["zero_grf"]["zero_identity_sha256"],
        grf_digest=boot["zero_grf"]["grf_sha256"],
    )
    cycle["bundled_core"].update(
        manifest_digest=boot["bundled_core"]["manifest_sha256"],
        checkpoint_digest=boot["bundled_core"]["checkpoint_sha256"],
        tokenizer_digest=boot["bundled_core"]["tokenizer_sha256"],
        jspace_profile_digest=boot["jspace"]["jspace_profile_sha256"],
        lens_profile_digest=boot["jspace"]["lens_profile_sha256"],
        workspace_calibration_digest=boot["gwt"]["calibration_sha256"],
    )
    cycle["runtime"]["generation"] = boot["runtime"]["entity_generation"]
    cycle["binding"].update(
        zero_identity_digest=cycle["identity"]["zero_identity_digest"],
        grf_digest=cycle["identity"]["grf_digest"],
        bundled_manifest_digest=cycle["bundled_core"]["manifest_digest"],
        boot_binding_receipt_digest=chain.canonical_sha256(boot),
    )
    return redigest(cycle)


def claude_cycle_from_boot(boot: dict) -> dict:
    cycle = cycle_from_boot(boot)
    ucf_fixture.blocked_nonfree(cycle)
    cycle["inference"].update(
        adapter_version=boot["claude_adapter"]["adapter_version"],
        capability_profile_digest=boot["claude_adapter"]["capability_profile_sha256"],
    )
    return redigest(cycle)


class UcfBootAncestryChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.manifest = boot_fixture.valid_manifest()
        self.raw = boot_fixture.manifest_bytes(self.manifest)
        self.manifest_path = root / "manifest.json"; self.manifest_path.write_bytes(self.raw)
        self.lock = boot_fixture.source_lock_for(self.manifest, self.raw)
        self.boot = boot_fixture.valid_receipt(self.manifest, self.raw)
        self.cycle = cycle_from_boot(self.boot)

    def test_valid_canonical_cycle_descends_from_valid_boot(self):
        self.assertEqual(chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock), [])

    def test_structurally_valid_wrong_boot_digest_fails_ancestry(self):
        self.cycle["binding"]["boot_binding_receipt_digest"] = ALT
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn("BOOT_RECEIPT_ANCESTRY_MISMATCH", chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock))

    def test_structurally_valid_wrong_source_commit_fails_ancestry(self):
        self.cycle["source"]["commit"] = "b" * 40
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn("BOOT_SOURCE_COMMIT_MISMATCH", chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock))

    def test_self_consistent_wrong_manifest_binding_fails_ancestry(self):
        self.cycle["bundled_core"]["manifest_digest"] = ALT
        self.cycle["binding"]["bundled_manifest_digest"] = ALT
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn("BOOT_CORE_MANIFEST_MISMATCH", chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock))

    def test_wrong_checkpoint_fails_ancestry(self):
        self.cycle["bundled_core"]["checkpoint_digest"] = ALT
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn("BOOT_CORE_CHECKPOINT_MISMATCH", chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock))

    def test_wrong_jspace_profile_fails_ancestry(self):
        self.cycle["bundled_core"]["jspace_profile_digest"] = ALT
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn("BOOT_JSPACE_PROFILE_MISMATCH", chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock))

    def test_self_reported_generation_freshness_cannot_replace_boot_crossbind(self):
        self.cycle["runtime"]["generation"] += 1
        self.cycle["freshness"]["stale_generation"] = False
        redigest(self.cycle)
        self.assertTrue(ucf.validate(self.cycle)["ok"])
        self.assertIn(
            "BOOT_ENTITY_GENERATION_MISMATCH",
            chain.validate_chain(self.cycle, self.boot, self.manifest_path, self.lock),
        )

    def test_missing_boot_generation_fails_before_composition(self):
        poisoned = copy.deepcopy(self.boot)
        poisoned.pop("runtime")
        errors = chain.validate_chain(self.cycle, poisoned, self.manifest_path, self.lock)
        self.assertTrue(any("MISSING_OBJECT:runtime" in error for error in errors), errors)

    def test_boolean_boot_generation_fails_before_composition(self):
        poisoned = copy.deepcopy(self.boot)
        poisoned["runtime"]["entity_generation"] = True
        errors = chain.validate_chain(self.cycle, poisoned, self.manifest_path, self.lock)
        self.assertTrue(any("INVALID_INT:entity_generation" in error for error in errors), errors)

    def test_boot_runtime_substitution_is_stopped_upstream(self):
        poisoned = copy.deepcopy(self.boot)
        poisoned["bundled_core"]["runtime_sha256"] = ALT
        errors = chain.validate_chain(self.cycle, poisoned, self.manifest_path, self.lock)
        self.assertTrue(any("BOOT_RUNTIME_DIGEST_MISMATCH" in error for error in errors), errors)

    def test_nonplaceholder_false_bundle_is_stopped_by_source_lock(self):
        poisoned_manifest = copy.deepcopy(self.manifest)
        poisoned_manifest["checkpoint_digest"] = ALT
        poisoned_raw = boot_fixture.manifest_bytes(poisoned_manifest)
        poisoned_path = Path(self.temp.name) / "poisoned.json"; poisoned_path.write_bytes(poisoned_raw)
        poisoned_boot = boot_fixture.valid_receipt(poisoned_manifest, poisoned_raw)
        poisoned_cycle = cycle_from_boot(poisoned_boot)
        errors = chain.validate_chain(poisoned_cycle, poisoned_boot, poisoned_path, self.lock)
        self.assertTrue(any("SOURCE_LOCK_MANIFEST_FILE_MISMATCH" in error for error in errors), errors)

    def test_claude_cycle_fails_if_bound_boot_adapter_is_disabled(self):
        cycle = claude_cycle_from_boot(self.boot)
        self.assertTrue(ucf.validate(cycle)["ok"])
        self.assertFalse(self.boot["claude_adapter"]["enabled"])
        self.assertIn("BOOT_CLAUDE_ADAPTER_DISABLED", chain.validate_chain(cycle, self.boot, self.manifest_path, self.lock))

    def test_claude_cycle_can_descend_from_matching_enabled_boot_adapter(self):
        boot = copy.deepcopy(self.boot)
        boot["claude_adapter"]["enabled"] = True
        cycle = claude_cycle_from_boot(boot)
        self.assertTrue(ucf.validate(cycle)["ok"])
        self.assertEqual(chain.validate_chain(cycle, boot, self.manifest_path, self.lock), [])


if __name__ == "__main__":
    unittest.main()
