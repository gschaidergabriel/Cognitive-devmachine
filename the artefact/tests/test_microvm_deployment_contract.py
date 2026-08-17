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


def test_kata_template_requires_vm_runtime_and_single_entity():
    text = TEMPLATE.read_text()
    assert "runtimeClassName: kata-qemu-runtime-rs" in text
    assert "replicas: 1" in text
    assert "registry.example.invalid/clayverse@sha256:REPLACE_WITH_ACCEPTED_DIGEST" in text
    assert "type: ClusterIP" in text
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
    assert "kind: NetworkPolicy" in text
    assert "name: clayverse-default-deny" in text
    assert "policyTypes:" in text
    assert "- Ingress" in text
    assert "- Egress" in text
    assert "ingress: []" in text
    assert "egress: []" in text
    assert "hostNetwork: false alone is NOT a network-isolation policy" in text
    assert "selected CNI actually enforces" in text
    assert "node-local traffic exceptions" in text
    assert "0.0.0.0/0" not in text
    assert "::/0" not in text


def test_microvm_contract_does_not_overclaim_networkpolicy():
    text = CONTRACT.read_text()
    assert "CNI MUST be verified" in text
    assert "merely creating the API object is not evidence of enforcement" in text
    assert "node-local traffic" in text
    assert "metadata-service" in text
    assert "NetworkPolicy is not a substitute" in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
