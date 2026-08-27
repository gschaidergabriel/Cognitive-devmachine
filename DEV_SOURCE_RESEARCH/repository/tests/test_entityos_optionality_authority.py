"""Compatibility-named regression for the current EntityOS + HCU authority.

The filename is historical.  EntityOS is no longer an optional substrate inside
ClayVerse: current owner authority makes EntityOS the sole current product/system and
HCU the sole current integrated cognition/compute architecture.  This regression exists
to prevent the old optionality contract from silently becoming current again.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


CURRENT_AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
MANIFEST = "the artefact/manifest.json"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"

# These keys belonged to the superseded ClayVerse manifest contract where EntityOS was
# an optional internal substrate.  Their reappearance at current-manifest authority
# scope is a regression, not compatibility.
SUPERSEDED_OPTIONALITY_KEYS = {
    "entityos_role",
    "entityos_execution_default",
    "entityos_whole_product_gate",
    "entityos_development_baseline",
    "entityos_admission",
}


def validate_entityos_current_authority(root: Path) -> list[str]:
    errors: list[str] = []
    authority_path = root / CURRENT_AUTHORITY
    manifest_path = root / MANIFEST
    if not authority_path.is_file():
        return ["MISSING_CURRENT_AUTHORITY"]
    if not manifest_path.is_file():
        return ["MISSING_MANIFEST"]

    try:
        authority = json.loads(authority_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"JSON_LOAD_ERROR:{type(exc).__name__}"]

    if authority.get("schema_version") != "8.52":
        errors.append("AUTHORITY_SCHEMA_MISMATCH")
    if authority.get("status") != "CURRENT_OWNER_AUTHORITY_CORRECTION":
        errors.append("AUTHORITY_STATUS_MISMATCH")
    if authority.get("program") != "ENTITYOS_HCU":
        errors.append("AUTHORITY_PROGRAM_MISMATCH")
    if authority.get("product") != CURRENT_PRODUCT:
        errors.append("AUTHORITY_PRODUCT_MISMATCH")
    if authority.get("integrated_cognition_compute_architecture") != CURRENT_COMPUTE_ARCHITECTURE:
        errors.append("AUTHORITY_COMPUTE_ARCHITECTURE_MISMATCH")

    adjudication = authority.get("adjudication") or {}
    if adjudication.get("entityos") != "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY":
        errors.append("AUTHORITY_ENTITYOS_NOT_SOLE_CURRENT_PRODUCT")
    if adjudication.get("hcu") != "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE":
        errors.append("AUTHORITY_HCU_NOT_SOLE_CURRENT_COMPUTE_ARCHITECTURE")
    if adjudication.get("clayverse") != "HISTORICAL_DONOR_PROVENANCE_ONLY":
        errors.append("AUTHORITY_CLAYVERSE_NOT_HISTORICAL_DONOR")

    if manifest.get("schema") != "ENTITYOS_HCU_ARTIFACT_MANIFEST/v1":
        errors.append("MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("artifact") != CURRENT_PRODUCT:
        errors.append("MANIFEST_ARTIFACT_MISMATCH")
    if manifest.get("product_endpoint") != CURRENT_PRODUCT:
        errors.append("MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    if manifest.get("integrated_cognition_compute_architecture") != CURRENT_COMPUTE_ARCHITECTURE:
        errors.append("MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    if manifest.get("stage") != CURRENT_STAGE:
        errors.append("MANIFEST_STAGE_MISMATCH")
    if manifest.get("authority_correction") != CURRENT_AUTHORITY:
        errors.append("MANIFEST_AUTHORITY_POINTER_MISMATCH")
    if manifest.get("effect_authority") != "EffectGate+EffectJournal":
        errors.append("MANIFEST_EFFECT_AUTHORITY_MISMATCH")

    reintroduced = sorted(SUPERSEDED_OPTIONALITY_KEYS.intersection(manifest))
    if reintroduced:
        errors.append("SUPERSEDED_ENTITYOS_OPTIONALITY_KEYS_REINTRODUCED:" + ",".join(reintroduced))

    donor = manifest.get("legacy_donor") or {}
    if donor.get("prior_product") != "ClayVerse":
        errors.append("MANIFEST_CLAYVERSE_DONOR_PROVENANCE_MISSING")
    if donor.get("scope") != "HISTORICAL_DONOR_PROVENANCE_ONLY":
        errors.append("MANIFEST_CLAYVERSE_DONOR_SCOPE_MISMATCH")

    execution = manifest.get("execution_policy") or {}
    if execution.get("free_only") is not True:
        errors.append("MANIFEST_FREE_ONLY_FENCE_WEAKENED")
    if execution.get("isolated_sandbox_only") is not True:
        errors.append("MANIFEST_ISOLATED_EXECUTION_FENCE_WEAKENED")
    if execution.get("vps_testing_forbidden") is not True:
        errors.append("MANIFEST_VPS_TEST_FENCE_WEAKENED")
    if execution.get("self_hosted_vps_test_runners_forbidden") is not True:
        errors.append("MANIFEST_SELF_HOSTED_TEST_FENCE_WEAKENED")
    if execution.get("production_host_testing_forbidden") is not True:
        errors.append("MANIFEST_PRODUCTION_TEST_FENCE_WEAKENED")
    if execution.get("together_forbidden") is not True:
        errors.append("MANIFEST_TOGETHER_FENCE_WEAKENED")
    if execution.get("paid_fallback") is not False:
        errors.append("MANIFEST_PAID_FALLBACK_FENCE_WEAKENED")

    runtime = manifest.get("runtime_credit") or {}
    if runtime.get("entityos_hcu_whole_runtime_credit") != 0:
        errors.append("MANIFEST_RUNTIME_CREDIT_NONZERO")
    if runtime.get("whole_product_pass") is not False:
        errors.append("MANIFEST_WHOLE_PRODUCT_PASS_PREMATURE")
    return errors


class EntityOSCurrentAuthorityCompatibilityTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        authority_path = root / CURRENT_AUTHORITY
        manifest_path = root / MANIFEST
        authority_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        authority_path.write_text(
            json.dumps(
                {
                    "schema_version": "8.52",
                    "status": "CURRENT_OWNER_AUTHORITY_CORRECTION",
                    "program": "ENTITYOS_HCU",
                    "product": CURRENT_PRODUCT,
                    "integrated_cognition_compute_architecture": CURRENT_COMPUTE_ARCHITECTURE,
                    "adjudication": {
                        "entityos": "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY",
                        "hcu": "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE",
                        "clayverse": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": "ENTITYOS_HCU_ARTIFACT_MANIFEST/v1",
                    "artifact": CURRENT_PRODUCT,
                    "product_endpoint": CURRENT_PRODUCT,
                    "integrated_cognition_compute_architecture": CURRENT_COMPUTE_ARCHITECTURE,
                    "stage": CURRENT_STAGE,
                    "authority_correction": CURRENT_AUTHORITY,
                    "effect_authority": "EffectGate+EffectJournal",
                    "execution_policy": {
                        "free_only": True,
                        "isolated_sandbox_only": True,
                        "vps_testing_forbidden": True,
                        "self_hosted_vps_test_runners_forbidden": True,
                        "production_host_testing_forbidden": True,
                        "together_forbidden": True,
                        "paid_fallback": False,
                    },
                    "runtime_credit": {
                        "entityos_hcu_whole_runtime_credit": 0,
                        "whole_product_pass": False,
                    },
                    "legacy_donor": {
                        "prior_product": "ClayVerse",
                        "scope": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return td, root

    def test_current_repository_contract(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], validate_entityos_current_authority(root))

    def test_coherent_current_contract_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertEqual([], validate_entityos_current_authority(root))

    def test_clayverse_product_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["artifact"] = "ClayVerse"
        data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = validate_entityos_current_authority(root)
        self.assertIn("MANIFEST_ARTIFACT_MISMATCH", errors)
        self.assertIn("MANIFEST_PRODUCT_ENDPOINT_MISMATCH", errors)

    def test_old_entityos_optionality_contract_cannot_return_as_current(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entityos_role"] = "STAGED_INTERNAL_EXECUTION_SECURITY_RUNTIME_SUBSTRATE_EXECUTION_OPTIONAL"
        data["entityos_execution_default"] = "DISABLED"
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = validate_entityos_current_authority(root)
        self.assertTrue(any(e.startswith("SUPERSEDED_ENTITYOS_OPTIONALITY_KEYS_REINTRODUCED:") for e in errors))

    def test_hcu_compute_authority_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["integrated_cognition_compute_architecture"] = "XCU"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH", validate_entityos_current_authority(root))

    def test_runtime_credit_cannot_be_minted_by_manifest(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["runtime_credit"]["entityos_hcu_whole_runtime_credit"] = 1
        data["runtime_credit"]["whole_product_pass"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = validate_entityos_current_authority(root)
        self.assertIn("MANIFEST_RUNTIME_CREDIT_NONZERO", errors)
        self.assertIn("MANIFEST_WHOLE_PRODUCT_PASS_PREMATURE", errors)


if __name__ == "__main__":
    unittest.main()
