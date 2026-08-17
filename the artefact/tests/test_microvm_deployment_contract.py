from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"


def test_microvm_contract_is_mandatory_for_final_acceptance():
    text = CONTRACT.read_text()
    assert "MANDATORY FOR FINAL ACCEPTANCE" in text
    assert "same immutable image" in text
    assert "Separate guest kernel" in text
    assert "WHOLE_CLAYVERSE_PASS" in text
    assert "selected CNI MUST enforce Kubernetes NetworkPolicy" in text
    assert "undeclared ingress/egress fails" in text


def test_kata_template_requires_vm_runtime_and_single_entity():
    text = TEMPLATE.read_text()
    assert "runtimeClassName: kata-qemu-runtime-rs" in text
    assert "replicas: 1" in text
    assert "registry.example.invalid/clayverse@sha256:REPLACE_WITH_ACCEPTED_DIGEST" in text
    assert "hostNetwork: false" in text
    assert "hostPID: false" in text
    assert "hostIPC: false" in text
    assert "automountServiceAccountToken: false" in text


def test_kata_template_keeps_root_immutable_and_state_explicit():
    text = TEMPLATE.read_text()
    assert "readOnlyRootFilesystem: true" in text
    assert "allowPrivilegeEscalation: false" in text
    assert 'drop: ["ALL"]' in text
    assert "mountPath: /var/lib/clayverse" in text
    assert "mountPath: /workspace" in text
    assert "medium: Memory" in text
    assert "hostPath:" not in text


def test_kata_template_network_is_fail_closed_until_explicit_allow_policy():
    text = TEMPLATE.read_text()
    policy_doc = text.split("\n---\n", 1)[0]
    assert "kind: NetworkPolicy" in policy_doc
    assert "name: clayverse-default-deny" in policy_doc
    assert "policyTypes:" in policy_doc
    assert "- Ingress" in policy_doc
    assert "- Egress" in policy_doc
    assert "ingress: []" in policy_doc
    assert "egress: []" in policy_doc
    assert "matchLabels:\n      app: clayverse" in policy_doc
    assert "hostNetwork: false alone is NOT a network-isolation policy" in policy_doc
    assert "0.0.0.0/0" not in text
    assert "::/0" not in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
