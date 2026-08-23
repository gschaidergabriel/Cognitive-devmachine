import json
import tempfile
import unittest
from pathlib import Path


OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
MANIFEST = "the artefact/manifest.json"
EXPECTED_ROLE = "STAGED_INTERNAL_EXECUTION_SECURITY_RUNTIME_SUBSTRATE_EXECUTION_OPTIONAL"
EXPECTED_DEFAULT = "DISABLED"
EXPECTED_GATE = "CONDITIONAL_ON_EXPLICIT_ADMISSION"
UNCONDITIONAL_FINAL_GATE = "complete accepted EntityOS embedded in final image"
CONDITIONAL_FINAL_GATE = "if EntityOS execution is enabled in the accepted profile"
OWNER_OPTIONALITY_SENTENCE = (
    "EntityOS is an internal execution/security/runtime substrate carried inside ClayVerse "
    "when separately admitted"
)


def validate_entityos_optionality(root: Path) -> list[str]:
    errors: list[str] = []
    directive_path = root / OWNER_DIRECTIVE
    manifest_path = root / MANIFEST
    if not directive_path.is_file():
        return ["MISSING_OWNER_DIRECTIVE"]
    if not manifest_path.is_file():
        return ["MISSING_MANIFEST"]

    directive = directive_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    final_gates = "\n".join(str(item) for item in manifest.get("requires_for_final_pass", []))

    if OWNER_OPTIONALITY_SENTENCE not in directive:
        errors.append("OWNER_ENTITYOS_OPTIONALITY_NOT_CURRENT")
    if manifest.get("entityos_role") != EXPECTED_ROLE:
        errors.append("MANIFEST_ENTITYOS_ROLE_NOT_OPTIONAL")
    if manifest.get("entityos_execution_default") != EXPECTED_DEFAULT:
        errors.append("MANIFEST_ENTITYOS_DEFAULT_NOT_DISABLED")
    if manifest.get("entityos_whole_product_gate") != EXPECTED_GATE:
        errors.append("MANIFEST_ENTITYOS_GATE_NOT_CONDITIONAL")
    if UNCONDITIONAL_FINAL_GATE in final_gates:
        errors.append("MANIFEST_ENTITYOS_UNCONDITIONAL_FINAL_GATE")
    if CONDITIONAL_FINAL_GATE not in final_gates:
        errors.append("MANIFEST_ENTITYOS_CONDITIONAL_FINAL_GATE_MISSING")
    if "CLAYVERSE_ENABLE_ENTITYOS_EXEC=0" not in final_gates:
        errors.append("MANIFEST_ENTITYOS_DISABLED_ACCEPTANCE_MISSING")
    return errors


class EntityOSOptionalityAuthorityTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        directive = root / OWNER_DIRECTIVE
        manifest = root / MANIFEST
        directive.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        directive.write_text(
            "# current owner\n- " + OWNER_OPTIONALITY_SENTENCE + "; it is not the product endpoint.\n",
            encoding="utf-8",
        )
        manifest.write_text(
            json.dumps(
                {
                    "entityos_role": EXPECTED_ROLE,
                    "entityos_execution_default": EXPECTED_DEFAULT,
                    "entityos_whole_product_gate": EXPECTED_GATE,
                    "requires_for_final_pass": [
                        CONDITIONAL_FINAL_GATE
                        + ", exact accepted EntityOS bytes are required; otherwise CLAYVERSE_ENABLE_ENTITYOS_EXEC=0 remains valid"
                    ],
                }
            ),
            encoding="utf-8",
        )
        return td, root

    def test_current_repository_contract(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], validate_entityos_optionality(root))

    def test_coherent_optional_contract_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertEqual([], validate_entityos_optionality(root))

    def test_mandatory_role_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entityos_role"] = "MANDATORY_IN_FINAL_ACCEPTED_IMAGE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_ENTITYOS_ROLE_NOT_OPTIONAL", validate_entityos_optionality(root))

    def test_unconditional_final_gate_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data["requires_for_final_pass"] = [UNCONDITIONAL_FINAL_GATE]
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = validate_entityos_optionality(root)
        self.assertIn("MANIFEST_ENTITYOS_UNCONDITIONAL_FINAL_GATE", errors)
        self.assertIn("MANIFEST_ENTITYOS_CONDITIONAL_FINAL_GATE_MISSING", errors)

    def test_owner_directive_change_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        (root / OWNER_DIRECTIVE).write_text("# changed owner law\nEntityOS mandatory.\n", encoding="utf-8")
        self.assertIn("OWNER_ENTITYOS_OPTIONALITY_NOT_CURRENT", validate_entityos_optionality(root))


if __name__ == "__main__":
    unittest.main()
