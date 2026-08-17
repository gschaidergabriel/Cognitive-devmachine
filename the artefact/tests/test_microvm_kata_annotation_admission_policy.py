from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-annotation-admission-policy.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_annotation_admission_fence_is_fail_closed_and_not_label_bypassable():
    text = POLICY.read_text()
    docs = _yaml_documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "object.metadata.annotations.all(k, !k.startsWith('io.katacontainers.'))" in policy
    assert "reason: Forbidden" in policy

    assert "policyName: clayverse-kata-runtime-annotation-fence.seimensch.net" in binding
    assert "validationActions:" in binding
    assert "- Deny" in binding
    assert "objectSelector:" not in binding
    assert "app: clayverse" not in binding
    assert "Warn" not in binding
    assert "binding intentionally has no objectSelector" in text
    assert "namespaceSelector" in text


def test_reference_kata_workload_does_not_preapprove_runtime_mutating_annotations():
    template = TEMPLATE.read_text()
    assert "io.katacontainers." not in template

    policy = POLICY.read_text()
    assert "no io.katacontainers.* Pod annotation is admitted" in policy
    assert "exact annotation/value MUST be separately reviewed" in policy
    assert "Do not replace this baseline with a Pod-label selector" in policy


def test_microvm_contract_requires_admission_time_runtime_annotation_enforcement():
    contract = CONTRACT.read_text()
    assert "deployment admission policy MUST fail closed" in contract
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in contract
    assert "absence of these annotations in the repository template alone is not sufficient" in contract
    assert "effective admitted Pod annotations after all admission mutation" in contract
