from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-runtime-annotation-admission.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _yaml_documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_runtime_admission_policy_is_fail_closed_and_bound():
    text = POLICY.read_text()
    docs = _yaml_documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "name: clayverse-kata-runtime-boundary" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "name: requestClayVerse" in policy
    assert 'request.name == "clayverse-0"' in policy
    assert "name: currentClayVerse" in policy
    assert "name: previousClayVerse" in policy
    assert 'object.metadata.labels["app"] == "clayverse"' in policy
    assert 'c.name == "clayverse"' in policy
    assert "oldObject != null" in policy
    assert 'object.metadata.name == request.name' in policy
    assert 'object.spec.runtimeClassName == "kata-qemu-runtime-rs"' in policy
    assert 'k.startsWith("io.katacontainers.")' in policy
    assert policy.count("reason: Forbidden") == 3

    assert "apiVersion: admissionregistration.k8s.io/v1" in binding
    assert "policyName: clayverse-kata-runtime-boundary" in binding
    assert "validationActions: [Deny]" in binding


def test_kata_runtime_admission_baseline_has_no_runtime_exception():
    text = POLICY.read_text()
    assert "io.katacontainers.*" in text
    assert "wildcards" in text
    assert "validationActions: [Deny]" in text
    assert "Warn" not in text
    assert "Audit" not in text
    assert "allowed_annotations" not in text
    assert "exception:" not in text


def test_kata_runtime_admission_blocks_runtimeclass_fallback_and_identity_evasion():
    text = POLICY.read_text()
    assert "host-kernel fallback or runtime-class mutation is forbidden" in text
    assert "variables.requestClayVerse || variables.currentClayVerse || variables.previousClayVerse" in text
    assert "has(object.spec.runtimeClassName)" in text
    assert "oldObject.spec.containers.exists" in text
    assert "object.metadata.name == request.name" in text


def test_kata_runtime_admission_create_identity_survives_mutated_object_markers():
    text = POLICY.read_text()
    request_var = text.split("- name: requestClayVerse", 1)[1].split("- name: currentClayVerse", 1)[0]
    assert 'request.name == "clayverse-0"' in request_var
    assert "object.metadata.labels" not in request_var
    assert "object.spec.containers" not in request_var

    # CREATE has no oldObject. The independent request-name anchor must still
    # force both runtime and annotation validations even if a mutator rewrites
    # every current-object ClayVerse marker before validating admission runs.
    runtime_validation = text.split("host-kernel fallback or runtime-class mutation is forbidden", 1)[0]
    assert "variables.requestClayVerse" in runtime_validation
    annotation_validation = text.split("host-kernel fallback or runtime-class mutation is forbidden", 1)[1]
    assert "variables.requestClayVerse" in annotation_validation


def test_microvm_contract_requires_runtime_annotation_and_runtimeclass_fences():
    contract = CONTRACT.read_text()
    assert "deployment admission policy MUST fail closed" in contract
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in contract
    assert "effective admitted Pod annotations" in contract
    assert "sandboxed RuntimeClass explicitly" in contract
    assert "silently falling back to the default host-kernel runtime is a final-acceptance failure" in contract
