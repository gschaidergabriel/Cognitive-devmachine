from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "deployment" / "clayverse-kata-admission-policy.template.yaml"


def _documents(text: str) -> list[str]:
    return [doc.strip() for doc in text.split("\n---\n") if doc.strip()]


def test_kata_annotation_fence_is_fail_closed_and_bound():
    text = POLICY.read_text()
    docs = _documents(text)
    assert len(docs) == 2

    policy = next(doc for doc in docs if "kind: ValidatingAdmissionPolicy\n" in doc)
    binding = next(doc for doc in docs if "kind: ValidatingAdmissionPolicyBinding\n" in doc)

    assert "apiVersion: admissionregistration.k8s.io/v1" in policy
    assert "failurePolicy: Fail" in policy
    assert 'operations: ["CREATE", "UPDATE"]' in policy
    assert 'resources: ["pods"]' in policy
    assert "reason: Forbidden" in policy

    assert "policyName: clayverse-kata-annotation-fence.seimensch.net" in binding
    assert "validationActions:" in binding
    assert "- Deny" in binding
    assert "Warn" not in binding
    assert "Audit" not in binding


def test_kata_annotation_fence_covers_create_and_label_removal_update():
    text = POLICY.read_text()
    policy = next(doc for doc in _documents(text) if "kind: ValidatingAdmissionPolicy\n" in doc)

    # CREATE is identified from the incoming ClayVerse label; UPDATE is also
    # fenced from oldObject so removing the label cannot authorize annotation
    # injection in the same request.
    assert "object.metadata.labels['app'] == 'clayverse'" in policy
    assert "oldObject != null" in policy
    assert "oldObject.metadata.labels['app'] == 'clayverse'" in policy


def test_kata_annotation_fence_rejects_the_entire_unreviewed_namespace():
    text = POLICY.read_text()
    policy = next(doc for doc in _documents(text) if "kind: ValidatingAdmissionPolicy\n" in doc)

    assert "object.metadata.annotations.all(k, !k.startsWith('io.katacontainers.'))" in policy
    assert "io.katacontainers.config_path" not in policy
    assert "io.katacontainers.config.runtime.sandbox_bind_mounts" not in policy
    assert "unless" not in policy.lower()


def test_kata_annotation_fence_has_no_second_runtime_or_state_authority():
    text = POLICY.read_text()
    forbidden = (
        "Deployment\n",
        "StatefulSet\n",
        "DaemonSet\n",
        "hostPath:",
        "hostNetwork: true",
        "privileged: true",
        "process.exec",
    )
    for token in forbidden:
        assert token not in text
