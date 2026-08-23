import json
import tempfile
import unittest
from pathlib import Path

MANIFEST = "the artefact/manifest.json"
STEERING = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
LEGACY_MANIFEST_BLOB = "fe6a601efdbe350a7b34816c4ffceb182df5cab8"


def validate_entityos_current_authority(root: Path) -> list[str]:
    """Compatibility test module: EntityOS is now the product, not a ClayVerse option."""
    errors: list[str] = []
    manifest_path = root / MANIFEST
    steering_path = root / STEERING
    if not manifest_path.is_file():
        return ["MISSING_MANIFEST"]
    if not steering_path.is_file():
        return ["MISSING_STEERING_852"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    steering = json.loads(steering_path.read_text(encoding="utf-8"))

    if steering.get("status") != "CURRENT_OWNER_AUTHORITY_CORRECTION":
        errors.append("STEERING_852_NOT_CURRENT")
    if steering.get("product") != "EntityOS":
        errors.append("STEERING_ENTITYOS_NOT_PRODUCT")
    if steering.get("integrated_cognition_compute_architecture") != "HCU":
        errors.append("STEERING_HCU_NOT_COMPUTE_ARCHITECTURE")
    adjudication = steering.get("adjudication") or {}
    if adjudication.get("clayverse") != "HISTORICAL_DONOR_PROVENANCE_ONLY":
        errors.append("STEERING_CLAYVERSE_NOT_HISTORICAL")

    if manifest.get("artifact") != "EntityOS":
        errors.append("MANIFEST_ENTITYOS_NOT_ARTIFACT")
    if manifest.get("product_endpoint") != "EntityOS":
        errors.append("MANIFEST_ENTITYOS_NOT_PRODUCT_ENDPOINT")
    if manifest.get("integrated_cognition_compute_architecture") != "HCU":
        errors.append("MANIFEST_HCU_NOT_COMPUTE_ARCHITECTURE")
    provenance = manifest.get("legacy_manifest_provenance") or {}
    if provenance.get("prior_manifest_git_blob_sha1") != LEGACY_MANIFEST_BLOB:
        errors.append("LEGACY_CLAYVERSE_MANIFEST_PROVENANCE_MISMATCH")
    if provenance.get("classification") != "HISTORICAL_DONOR_PROVENANCE_ONLY":
        errors.append("LEGACY_CLAYVERSE_MANIFEST_NOT_HISTORICAL")
    acceptance = manifest.get("acceptance") or {}
    if acceptance.get("entityos_hcu_whole_runtime_credit") != 0:
        errors.append("ENTITYOS_HCU_RUNTIME_CREDIT_INFLATED")
    if acceptance.get("whole_product_pass") is not False:
        errors.append("ENTITYOS_HCU_WHOLE_PASS_UNJUSTIFIED")
    return errors


class EntityOSCurrentAuthorityTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        manifest = root / MANIFEST
        steering = root / STEERING
        manifest.parent.mkdir(parents=True, exist_ok=True)
        steering.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "artifact": "EntityOS",
                    "product_endpoint": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "legacy_manifest_provenance": {
                        "prior_manifest_git_blob_sha1": LEGACY_MANIFEST_BLOB,
                        "classification": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                    },
                    "acceptance": {
                        "entityos_hcu_whole_runtime_credit": 0,
                        "whole_product_pass": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        steering.write_text(
            json.dumps(
                {
                    "status": "CURRENT_OWNER_AUTHORITY_CORRECTION",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "adjudication": {"clayverse": "HISTORICAL_DONOR_PROVENANCE_ONLY"},
                }
            ),
            encoding="utf-8",
        )
        return td, root

    def test_current_repository_contract(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], validate_entityos_current_authority(root))

    def test_coherent_entityos_hcu_contract_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertEqual([], validate_entityos_current_authority(root))

    def test_clayverse_product_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_ENTITYOS_NOT_PRODUCT_ENDPOINT", validate_entityos_current_authority(root))

    def test_hcu_alias_cannot_become_second_compute_architecture(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["integrated_cognition_compute_architecture"] = "XCU"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_HCU_NOT_COMPUTE_ARCHITECTURE", validate_entityos_current_authority(root))

    def test_legacy_manifest_provenance_cannot_be_silently_rewritten(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["legacy_manifest_provenance"]["prior_manifest_git_blob_sha1"] = "f" * 40
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("LEGACY_CLAYVERSE_MANIFEST_PROVENANCE_MISMATCH", validate_entityos_current_authority(root))

    def test_runtime_promotion_without_evidence_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["acceptance"] = {"entityos_hcu_whole_runtime_credit": 1, "whole_product_pass": True}
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = validate_entityos_current_authority(root)
        self.assertIn("ENTITYOS_HCU_RUNTIME_CREDIT_INFLATED", errors)
        self.assertIn("ENTITYOS_HCU_WHOLE_PASS_UNJUSTIFIED", errors)


if __name__ == "__main__":
    unittest.main()
