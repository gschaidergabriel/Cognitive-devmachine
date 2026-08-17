import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-runtime-annotation-admission.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
MANIFEST = ROOT / "manifest.json"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_runtime_annotation_policy_is_fail_closed_and_bound():
    text = POLICY.read_text(encoding="utf-8")
    docs = _yaml_documents(text)

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "object.metadata.name.startsWith('clayverse-')" in policy
    assert "object.spec.runtimeClassName == 'kata-qemu-runtime-rs'" in policy
    assert "object.metadata.annotations.all(k, !k.startsWith('io.katacontainers.'))" in policy
    assert "reason: Forbidden" in policy

    assert "policyName: clayverse-kata-runtime-annotations" in binding
    assert "validationActions: [Deny]" in binding


def test_kata_annotation_policy_matches_existing_acceptance_authority():
    contract = CONTRACT.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert "deployment admission policy MUST fail closed" in contract
    assert "effective admitted Pod annotations" in contract
    assert "FAIL_CLOSED_ON_UNREVIEWED_IO_KATACONTAINERS" in manifest["outer_isolation"]["runtime_annotation_policy"]

    required = set(manifest["requires_for_final_pass"])
    assert any("effective io.katacontainers.* workload annotations" in gate for gate in required)
