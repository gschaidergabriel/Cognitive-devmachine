from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-runtime-annotation-admission.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_annotation_admission_policy_is_fail_closed_and_bound():
    text = POLICY.read_text()
    docs = _yaml_documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "name: clayverse-kata-runtime-annotations" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert 'object.metadata.labels["app"] != "clayverse"' in policy
    assert 'k.startsWith("io.katacontainers.")' in policy
    assert "reason: Forbidden" in policy

    assert "apiVersion: admissionregistration.k8s.io/v1" in binding
    assert "policyName: clayverse-kata-runtime-annotations" in binding
    assert "validationActions: [Deny]" in binding


def test_kata_annotation_admission_baseline_has_no_runtime_exception():
    text = POLICY.read_text()
    assert "io.katacontainers.*" in text
    assert "wildcards" in text
    assert "validationActions: [Deny]" in text
    assert "Warn" not in text
    assert "Audit" not in text
    assert "allowed_annotations" not in text
    assert "exception:" not in text


def test_microvm_contract_requires_runtime_annotation_admission_fence():
    contract = CONTRACT.read_text()
    assert "deployment admission policy MUST fail closed" in contract
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in contract
    assert "effective admitted Pod annotations" in contract
