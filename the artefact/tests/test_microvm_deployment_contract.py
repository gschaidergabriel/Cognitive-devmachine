from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


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


def test_kata_template_network_is_fail_closed_until_explicit_allow_policy():
    text = TEMPLATE.read_text()
    policies = [doc for doc in _yaml_documents(text) if "kind: NetworkPolicy" in doc]
    assert len(policies) == 1
    policy = policies[0]
    assert "name: clayverse-default-deny" in policy
    assert "podSelector:" in policy
    assert "app: clayverse" in policy
    assert "policyTypes:" in policy
    assert "- Ingress" in policy
    assert "- Egress" in policy
    assert "ingress: []" in policy
    assert "egress: []" in policy
    assert "0.0.0.0/0" not in policy
    assert "::/0" not in policy
    assert "hostNetwork: false alone is NOT a network-isolation policy" in text


def test_network_contract_requires_real_enforcement_not_yaml_only():
    text = CONTRACT.read_text()
    assert "network plugin/CNI" in text
    assert "actually support and enforce Kubernetes `NetworkPolicy`" in text
    assert "zero network-isolation evidence" in text
    assert "combine additively" in text
    assert "complete additive set of policies" in text
    assert "representative undeclared ingress and egress remain denied" in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
