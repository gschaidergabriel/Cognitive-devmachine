import json
import sys

import pytest

from clayverse import service


def test_final_service_effect_policy_defaults_to_entityos(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRE_EFFECT", "1")
    monkeypatch.delenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", raising=False)
    assert service._acceptance_effect_policy() == (True, "entityos.exec")


def test_final_service_rejects_noop_as_required_capability(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "state.noop")
    with pytest.raises(RuntimeError, match="entityos.exec"):
        service._acceptance_effect_policy()


def test_retired_mistral_only_service_mode_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setattr(sys, "argv", ["clayverse.service", "--mistral-once"])
    with pytest.raises(RuntimeError, match="retired"):
        service.main()


def test_provider_generic_api_service_mode_is_the_direct_acceptance_entry(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setattr(sys, "argv", ["clayverse.service", "--api-once"])
    monkeypatch.setattr(
        service,
        "_run_api_once",
        lambda db, *, state_root, pod_uid: {
            "service": "clayverse",
            "status": "api_canonical_turn_pass",
            "scope": "internal_direct_api_probe",
            "auth_credit": False,
            "whole_product_pass": False,
        },
    )
    monkeypatch.setattr(
        service,
        "_admit_tier2_after_recovery",
        lambda db, state_root, pod_uid, prior_fence: None,
    )
    assert service.main() == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["status"] == "api_canonical_turn_pass"
    assert payload["scope"] == "internal_direct_api_probe"
    assert payload["auth_credit"] is False
    assert payload["whole_product_pass"] is False
