import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
MANIFEST = ROOT / "manifest.json"


def _yaml_document_with(text: str, needle: str) -> str:
    docs = [doc.strip() for doc in text.split("\n---\n")]
    matches = [doc for doc in docs if needle in doc]
    assert len(matches) == 1, f"expected exactly one document containing {needle!r}"
    return matches[0]


def test_kata_reference_profile_has_explicit_fail_closed_networkpolicy():
    text = DEPLOYMENT.read_text()
    policy = _yaml_document_with(text, "kind: NetworkPolicy")

    assert "name: clayverse-default-deny" in policy
    assert "app: clayverse" in policy
    assert "- Ingress" in policy
    assert "- Egress" in policy
    assert "ingress: []" in policy
    assert "egress: []" in policy


def test_hostnetwork_false_is_present_but_not_treated_as_network_isolation():
    text = DEPLOYMENT.read_text()
    statefulset = _yaml_document_with(text, "kind: StatefulSet")

    assert "hostNetwork: false" in statefulset
    assert "hostPID: false" in statefulset
    assert "hostIPC: false" in statefulset

    contract = CONTRACT.read_text()
    assert "`hostNetwork: false` is necessary but is not sufficient network isolation" in contract
    assert "MUST actually support and enforce Kubernetes `NetworkPolicy`" in contract


def test_manifest_and_deployment_agree_on_network_acceptance_boundary():
    manifest = json.loads(MANIFEST.read_text())
    outer = manifest["outer_isolation"]

    assert outer["required_for_final_pass"] is True
    assert outer["network_policy_baseline"] == "DEFAULT_DENY_INGRESS_AND_EGRESS_FOR_APP_CLAYVERSE"
    assert outer["functional_network_access"] == "SEPARATE_DEPLOYMENT_SPECIFIC_REVIEWED_ALLOW_POLICY_REQUIRED"
    assert "ENFORCES_NETWORKPOLICY" in outer["network_policy_enforcement"]

    required = set(manifest["requires_for_final_pass"])
    assert "baseline ClayVerse NetworkPolicy default-deny ingress+egress actually enforced by the deployed CNI" in required
    assert "exact reviewed deployment network allow policy identity captured and only admitted flows open while tested non-admitted flows remain denied" in required
