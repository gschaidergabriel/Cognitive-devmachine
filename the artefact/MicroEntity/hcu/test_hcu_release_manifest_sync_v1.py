#!/usr/bin/env python3
"""Successor-dynamic coherence guard for retained EntityOS/HCU release metadata.

Deterministic source regression only: no model, Sandbox, provider, effect, or training
execution occurs here, and this test grants zero runtime/model/training/product credit.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA
from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA as DATASET_ADMISSION_SCHEMA
from jspace_inference_binding_v1 import SCHEMA as JSPACE_BINDING_SCHEMA
from model_execution_receipt_v1 import VERIFIED_EXECUTION_SCHEMA

HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = HERE.parent
DATA_INDEX_PATH = HERE / "HCU_DATA_INDEX.json"
PACKAGE_MANIFEST_PATH = PACKAGE_ROOT / "PACKAGE_MANIFEST.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: top-level object required")
    return value


def _find_canonical_bootstrap() -> Path | None:
    for parent in (HERE, *HERE.parents):
        candidate = parent / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json"
        if candidate.is_file():
            return candidate
    return None


class HCUReleaseManifestSyncV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = _load_json(DATA_INDEX_PATH)
        self.package = _load_json(PACKAGE_MANIFEST_PATH)

    def test_current_schema_metadata_matches_live_source_constants(self) -> None:
        engine = self.index["current_engine_path"]
        training = self.index["current_jspace_training_path"]
        self.assertEqual(engine["verified_model_execution_schema"], VERIFIED_EXECUTION_SCHEMA)
        self.assertEqual(engine["inference_receipt_schema"], INFERENCE_RECEIPT_SCHEMA)
        self.assertEqual(training["dataset_admission_schema"], DATASET_ADMISSION_SCHEMA)
        self.assertEqual(training["inference_binding_schema"], JSPACE_BINDING_SCHEMA)

    def test_package_manifest_matches_live_source_constants(self) -> None:
        hcu = self.package["hyperposition_compute"]
        self.assertEqual(hcu["verified_model_execution_schema"], VERIFIED_EXECUTION_SCHEMA)
        self.assertEqual(hcu["inference_receipt_schema"], INFERENCE_RECEIPT_SCHEMA)
        self.assertEqual(hcu["jspace_dataset_admission_schema"], DATASET_ADMISSION_SCHEMA)
        self.assertEqual(hcu["jspace_inference_binding_schema"], JSPACE_BINDING_SCHEMA)

    def test_package_manifest_covers_all_indexed_generated_files(self) -> None:
        indexed = {
            path
            for path in self.index["generated_release_artifacts"]
            if isinstance(path, str) and path and not path.endswith("/")
        }
        packaged = set(self.package["archive_members_required"])
        missing = sorted(indexed - packaged)
        self.assertEqual(missing, [], f"indexed generated HCU files omitted from package manifest: {missing}")

    def test_runtime_and_truth_credit_boundaries_remain_fail_closed(self) -> None:
        self.assertEqual(self.index["product"], "EntityOS")
        self.assertEqual(self.index["compute_architecture"], "HCU")
        self.assertEqual(self.index["current_engine_path"]["runtime_credit"], 0)
        self.assertEqual(self.package["hyperposition_compute"]["runtime_credit"], 0)
        self.assertFalse(self.package["whole_product_pass"])
        self.assertFalse(self.index["authority"]["training_trace_causal_hash_labels_are_authority"])
        self.assertFalse(self.index["authority"]["raw_training_trace_can_bypass_dataset_admission"])

    def test_supervisor_pointer_matches_canonical_bootstrap_in_repo_context(self) -> None:
        bootstrap_path = _find_canonical_bootstrap()
        if bootstrap_path is None:
            self.skipTest("canonical repo bootstrap absent in standalone package context")
        bootstrap = _load_json(bootstrap_path)
        self.assertEqual(
            self.index["current_supervisor_authority"],
            bootstrap["authority_correction"],
            "HCU_DATA_INDEX supervisor pointer drifted from canonical successor authority",
        )


if __name__ == "__main__":
    unittest.main()
