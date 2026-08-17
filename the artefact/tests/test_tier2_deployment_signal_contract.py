from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "clayverse" / "service.py"
SIGNAL = ROOT / "clayverse" / "tier2_signal.py"
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def test_recovery_integrity_error_requests_full_sandbox_replacement():
    service = SERVICE.read_text()
    assert "RecoveryIntegrityError" in service
    assert 'request_tier2_replacement("RECOVERY_INTEGRITY_ERROR", str(exc))' in service
    assert "return exit_code" in service


def test_tier2_signal_is_allowlisted_redacted_and_no_replay():
    signal = SIGNAL.read_text()
    assert 'TIER2_EXIT_CODE = 86' in signal
    assert 'TIER2_SIGNAL_SCHEMA = "clayverse.tier2-fatal/v1"' in signal
    assert '_ALLOWED_REASONS = frozenset({"RECOVERY_INTEGRITY_ERROR"})' in signal
    assert '"action": "REPLACE_FULL_SANDBOX"' in signal
    assert '"replay_external_effects": False' in signal
    assert "detail_sha256" in signal
    assert "write_bytes(encoded)" in signal


def test_kata_profile_exposes_typed_termination_channel_without_weakening_tier2():
    template = TEMPLATE.read_text()
    contract = CONTRACT.read_text()
    assert "reserved exit code" in template
    assert "86" in template
    assert "terminationMessagePath: /dev/termination-log" in template
    assert "terminationMessagePolicy: File" in template
    assert "exit 86 remains authoritative" in template
    assert "external-full-sandbox-required" in template
    assert "in-place-container-restart: not-tier2" in template
    assert "container restart inside an existing VM/microVM is not Tier 2" in contract
    assert "TIER2_REPLACEMENT_BLOCKED" in contract
