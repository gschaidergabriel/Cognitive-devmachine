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


def test_kata_template_has_default_deny_and_explicit_network_admission():
    text = TEMPLATE.read_text()
    assert text.count("kind: NetworkPolicy") == 3
    assert "name: clayverse-default-deny" in text
    assert "name: clayverse-explicit-ingress" in text
    assert "name: clayverse-explicit-egress" in text
    assert "clayverse.network/ingress: \"allowed\"" in text
    assert "kubernetes.io/metadata.name: kube-system" in text
    assert "k8s-app: kube-dns" in text
    assert "cidr: 0.0.0.0/0" in text
    assert "- 10.0.0.0/8" in text
    assert "- 169.254.0.0/16" in text
    assert "- 172.16.0.0/12" in text
    assert "- 192.168.0.0/16" in text
    assert "port: 3000" in text
    assert "port: 53" in text
    assert "port: 443" in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
