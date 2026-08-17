import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
MANIFEST = ROOT / "manifest.json"


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


def test_kata_statefulset_uses_headless_governing_service_and_separate_client_service():
    text = TEMPLATE.read_text()
    docs = _yaml_documents(text)
    services = [doc for doc in docs if "kind: Service" in doc]
    assert len(services) == 2

    client = next(doc for doc in services if "\n  name: clayverse\n" in doc)
    headless = next(doc for doc in services if "\n  name: clayverse-headless\n" in doc)
    stateful = next(doc for doc in docs if "kind: StatefulSet" in doc)

    assert "clusterIP: None" not in client
    assert "clusterIP: None" in headless
    assert "serviceName: clayverse-headless" in stateful
    assert "serviceName: clayverse\n" not in stateful


def test_kata_template_keeps_root_immutable_and_state_explicit():
    text = TEMPLATE.read_text()
    assert "readOnlyRootFilesystem: true" in text
    assert "allowPrivilegeEscalation: false" in text
    assert 'drop: ["ALL"]' in text
    assert "mountPath: /var/lib/clayverse" in text
    assert "mountPath: /workspace" in text
    assert "medium: Memory" in text
    assert "hostPath:" not in text


def test_kata_persistent_volumes_are_bound_to_nonroot_runtime_group():
    text = TEMPLATE.read_text()
    assert "runAsUser: 10001" in text
    assert "runAsGroup: 10001" in text
    assert "fsGroup: 10001" in text
    assert 'fsGroupChangePolicy: "OnRootMismatch"' in text
    assert "privileged: true" not in text
    assert "initContainers:" not in text

    contract = CONTRACT.read_text()
    assert "VOLUME_MOUNT_GROUP" in contract
    assert "create/write/fsync/read/rename/delete" in contract
    assert "uid=10001,gid=10001" in contract
    assert "unsupported or uncertain non-root volume ownership is `BLOCKED`" in contract


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


def test_kata_template_separates_liveness_from_full_readiness():
    text = TEMPLATE.read_text()
    stateful = next(doc for doc in _yaml_documents(text) if "kind: StatefulSet" in doc)
    readiness = stateful.split("readinessProbe:", 1)[1].split("livenessProbe:", 1)[0]
    liveness = stateful.split("livenessProbe:", 1)[1].split("resources:", 1)[0]
    assert "path: /readyz" in readiness
    assert "path: /healthz" in liveness
    assert "path: /readyz" not in liveness


def test_network_contract_requires_real_enforcement_not_yaml_only():
    text = CONTRACT.read_text()
    assert "network plugin/CNI" in text
    assert "actually support and enforce Kubernetes `NetworkPolicy`" in text
    assert "zero network-isolation evidence" in text
    assert "combine additively" in text
    assert "complete additive set of policies" in text
    assert "representative undeclared ingress and egress remain denied" in text


def test_manifest_network_gates_match_the_deployment_contract():
    manifest = json.loads(MANIFEST.read_text())
    outer = manifest["outer_isolation"]

    assert outer["required_for_final_pass"] is True
    assert outer["network_policy_baseline"] == "DEFAULT_DENY_INGRESS_AND_EGRESS_FOR_APP_CLAYVERSE"
    assert outer["functional_network_access"] == "SEPARATE_DEPLOYMENT_SPECIFIC_REVIEWED_ALLOW_POLICY_REQUIRED"
    assert "ENFORCES_NETWORKPOLICY" in outer["network_policy_enforcement"]

    required = set(manifest["requires_for_final_pass"])
    assert "baseline ClayVerse NetworkPolicy default-deny ingress+egress actually enforced by the deployed CNI" in required
    assert "exact reviewed deployment network allow policy identity captured and only admitted flows open while tested non-admitted flows remain denied" in required


def test_tier2_requires_full_kata_sandbox_replacement_not_container_restart():
    contract = CONTRACT.read_text()
    template = TEMPLATE.read_text()
    assert "container restart inside an existing VM/microVM is not Tier 2" in contract
    assert "Pod sandbox" in contract
    assert "old Pod UID" in contract
    assert "new Pod UID" in contract
    assert "new sandbox/VM identity" in contract
    assert "TIER2_REPLACEMENT_BLOCKED" in contract
    assert "external-full-sandbox-required" in template
    assert "in-place-container-restart: not-tier2" in template
    assert "restartPolicy: Never" not in template
    assert "restartPolicy: OnFailure" not in template


def test_kata_runtime_security_floor_is_bound_and_refreshed():
    text = CONTRACT.read_text()
    assert "GHSA-2gv2-cffp-j227 / CVE-2026-47243" in text
    assert "`runtime-rs <= 3.30.0` is explicitly forbidden" in text
    assert "`3.31.0` as the first patched release" in text
    assert "historical minimum fence, not a permanent safety claim" in text
    assert "refresh current Kata upstream security advisories" in text
    assert "bind the exact installed Kata/runtime-rs version and configuration" in text
    assert "shared-filesystem/virtiofs mode" in text
    assert "A version string alone is not microVM security evidence" in text


def test_kata_final_acceptance_requires_current_supported_rolling_release():
    text = CONTRACT.read_text()
    assert "rolling-release project" in text
    assert "only the current monthly release is security-supported" in text
    assert "then-current upstream-supported Kata release" in text
    assert "unsupported prior release is `BLOCKED`" in text
    assert "GHSA-mp2j-xm59-qfgw / CVE-2026-50540" in text
    assert "GHSA-7fhf-v3p3-rp56" in text
    assert "GHSA-fgm4-mv68-h344" in text
    assert "Dragonball hypervisor path" in text
    assert "selected hypervisor path" in text
    assert "`3.31.0` is **not an admissible current final-acceptance target**" in text
    assert "reject unreviewed `io.katacontainers.*` workload annotations" in text
    assert "effective admitted Pod annotations" in text


def test_provider_credentials_remain_bounded():
    text = TEMPLATE.read_text()
    assert "GLM_API_TOKEN" in text
    assert "secretKeyRef:" in text
    assert "CLAYVERSE_REQUIRE_CLAUDE" in text
    assert "CLAUDE_API_KEY" not in text
