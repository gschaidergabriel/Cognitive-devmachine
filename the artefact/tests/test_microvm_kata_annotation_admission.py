from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-annotation-admission.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_annotation_policy_is_fail_closed_and_pod_scoped():
    text = POLICY.read_text()
    docs = _yaml_documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "io.katacontainers." in policy
    assert "annotations.exists" in policy

    assert "validationActions: [Deny]" in binding
    assert "clayverse.seimensch.net/runtime: \"true\"" in binding
    assert "Warn" not in binding


def test_kata_annotation_policy_matches_current_microvm_contract():
    contract = CONTRACT.read_text()
    policy = POLICY.read_text()

    assert "admission policy MUST fail closed" in contract
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in contract
    assert "absence of these annotations in the repository template alone is not sufficient" in contract
    assert "io.katacontainers." in policy
    assert "runtime/containerd configuration remains a" in policy.lower()
    assert "separate acceptance surface" in policy.lower()


def test_policy_has_no_allowlisted_kata_escape_in_baseline():
    text = POLICY.read_text()
    assert "startsWith('io.katacontainers.')" in text
    assert "validationActions: [Deny]" in text
    assert "allowlist" not in text.lower()
    assert "exception" in text.lower()
