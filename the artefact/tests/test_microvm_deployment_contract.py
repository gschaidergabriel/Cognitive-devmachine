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


def test_kata_template_defaults_network_to_fail_closed():
    text = TEMPLATE.read_text()
    assert "kind: NetworkPolicy" in text
    assert "name: clayverse-default-deny" in text
    assert "name: clayverse-allow-ingress-gateway" in text
    assert "name: clayverse-allow-dns" in text
    assert "policyTypes:\n    - Ingress\n    - Egress" in text
    assert 'clayverse.network/ingress: "true"' in text
    assert "kubernetes.io/metadata.name: kube-system" in text
    assert "k8s-app: kube-dns" in text
    assert "port: 3000" in text
    assert "port: 53" in text


def test_kata_template_does_not_grant_wildcard_public_egress():
    text = TEMPLATE.read_text()
    # Provider egress is deployment-specific and must be separately admitted.
    assert "cidr: 0.0.0.0/0" not in text
    assert "cidr: ::/0" not in text
    assert "allow-all" not in text


def test_microvm_contract_requires_actual_network_policy_enforcement():
    text = CONTRACT.read_text()
    assert "NetworkPolicy-capable network plugin" in text
    assert "default-deny ingress and egress" in text
    assert "provider-specific egress" in text
    assert "node-local traffic" in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
