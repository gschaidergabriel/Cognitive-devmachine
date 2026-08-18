from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def test_microvm_template_selects_kata_and_fails_closed_on_networking() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "runtimeClassName: kata-qemu-runtime-rs" in text
    assert "kind: NetworkPolicy" in text
    assert "name: clayverse-default-deny" in text
    assert "- Ingress" in text
    assert "- Egress" in text
    assert "ingress: []" in text
    assert "egress: []" in text


def test_microvm_contract_fences_known_vulnerable_kata_runtime_rs() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "GHSA-2gv2-cffp-j227" in text
    assert "CVE-2026-47243" in text
    assert "runtime-rs <= 3.30.0" in text
    assert "3.31.0" in text
    assert "fresh upstream advisory/release review" in text


def test_microvm_contract_requires_effective_network_policy_enforcement() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "CNI" in text
    assert "actually support and enforce Kubernetes `NetworkPolicy`" in text
    assert "matching NetworkPolicies combine additively" in text
