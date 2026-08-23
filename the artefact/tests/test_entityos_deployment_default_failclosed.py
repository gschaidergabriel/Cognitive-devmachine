import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
MANIFEST = ROOT / "manifest.json"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _entityos_exec_values(template: str) -> list[str]:
    pattern = re.compile(
        r'^\s*- name: CLAYVERSE_ENABLE_ENTITYOS_EXEC\s*$'
        r'\n\s*value: ["\']?([^"\'\s]+)["\']?\s*$',
        re.MULTILINE,
    )
    return pattern.findall(template)


def test_reference_kata_profile_keeps_entityos_execution_fail_closed_by_default():
    template = TEMPLATE.read_text(encoding="utf-8")
    values = _entityos_exec_values(template)
    assert values == ["0"]
    assert "optional, separately admitted capability" in template
    assert "explicit capability admission contract" in template


def test_deployment_default_matches_manifest_and_microvm_contract():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = CONTRACT.read_text(encoding="utf-8")

    assert manifest["entityos_execution_default"] == "DISABLED"
    assert manifest["entityos_whole_product_gate"] == "CONDITIONAL_ON_EXPLICIT_ADMISSION"
    assert "execution is optional and defaults disabled" in manifest["entityos_admission"]
    assert "if EntityOS execution is enabled in the accepted profile" in "\n".join(
        manifest["requires_for_final_pass"]
    )
    assert "EntityOS execution" in contract
    assert "explicit admission" in contract


def test_reference_template_never_uses_entityos_enable_as_acceptance_shortcut():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC\n              value: \"1\"" not in template
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=1" not in template
