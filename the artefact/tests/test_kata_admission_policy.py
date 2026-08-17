from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-admission-policy.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_admission_policy_is_v1_fail_closed_and_denying():
    text = POLICY.read_text()
    docs = _yaml_documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "validationActions: [Deny]" in binding
    assert "policyName: clayverse-kata-runtime-boundary" in binding
    assert "app: clayverse" in binding
    assert "validationActions: [Warn]" not in binding
    assert "validationActions: [Audit]" not in binding


def test_kata_admission_policy_rejects_runtime_annotation_prefix_and_runtimeclass_drift():
    text = POLICY.read_text()
    assert "object.metadata.annotations.all(k, !k.startsWith('io.katacontainers.'))" in text
    assert "object.spec.runtimeClassName == 'kata-qemu-runtime-rs'" in text
    assert "forbids unreviewed io.katacontainers.* runtime annotations" in text
    assert "blanket prefix allowlist" in text


def test_kata_admission_policy_matches_the_canonical_workload_and_contract():
    policy = POLICY.read_text()
    contract = CONTRACT.read_text()
    template = TEMPLATE.read_text()

    assert "runtimeClassName: kata-qemu-runtime-rs" in template
    assert "app: clayverse" in template
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in contract
    assert "effective admitted Pod annotations" in contract
    assert "objectSelector:" in policy
    assert "app: clayverse" in policy
