from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _statefulset(text: str) -> str:
    return next(
        doc.strip()
        for doc in text.split("\n---\n")
        if "kind: StatefulSet" in doc
    )


def test_kata_pod_rejects_implicit_image_supplemental_groups():
    stateful = _statefulset(TEMPLATE.read_text())
    pod_spec = stateful.split("    spec:\n", 1)[1]
    pod_security = pod_spec.split("      securityContext:\n", 1)[1].split(
        "      containers:\n", 1
    )[0]

    assert "fsGroup: 10001" in pod_security
    assert 'fsGroupChangePolicy: "OnRootMismatch"' in pod_security
    assert "supplementalGroupsPolicy: Strict" in pod_security
    assert "supplementalGroupsPolicy: Merge" not in stateful


def test_final_acceptance_attests_strict_group_support_and_effective_identity():
    contract = CONTRACT.read_text()

    assert "default `Merge` policy is not admissible" in contract
    assert "status.features.supplementalGroupsPolicy: true" in contract
    assert "reject unsupported/unknown support rather than silently downgrade" in contract
    assert "status.containerStatuses[].user.linux" in contract
    assert "no implicit image-derived GID" in contract
    assert "before and after full appliance replacement" in contract
