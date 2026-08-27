import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "vps_control_sync_guard_v1.py"
spec = importlib.util.spec_from_file_location("vps_control_sync_guard_v1", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def good_supervisor():
    return {
        "schema_version": "9.13",
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": False,
            "together_forbidden": True,
            "no_paid_fallback": True,
            "free_swarm_owner_emergency_stop": True,
        },
    }


def good_admission():
    return {
        "authority_epoch": "9.13",
        "mode": "FREE_ONLY",
        "execution_state": "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF",
        "default_policy": "TOGETHER_FORBIDDEN; NO_PAID_FALLBACK",
        "providers": {
            "groq": {"admitted": False},
            "mistral": {"admitted": False},
            "nvidia": {"admitted": False},
            "openrouter": {"admitted": False},
        },
    }


def test_authority_happy_path():
    assert mod.validate_authority(good_supervisor(), good_admission()) == []


def test_epoch_split_brain_fails_closed():
    sup = good_supervisor()
    adm = good_admission()
    adm["authority_epoch"] = "9.12"
    errors = mod.validate_authority(sup, adm)
    assert any(e.startswith("authority_epoch_mismatch") for e in errors)


def test_any_provider_admitted_fails_closed():
    adm = good_admission()
    adm["providers"]["nvidia"]["admitted"] = True
    errors = mod.validate_authority(good_supervisor(), adm)
    assert "admission.provider_admitted:nvidia" in errors


def test_together_or_paid_fallback_policy_missing_fails_closed():
    adm = good_admission()
    adm["default_policy"] = "OWNER_EMERGENCY_STOP_FREE_SWARM"
    errors = mod.validate_authority(good_supervisor(), adm)
    assert "admission.default_policy_missing_paid_prohibitions" in errors


def test_supervisor_route_admission_true_fails_closed():
    sup = good_supervisor()
    sup["free_only"]["provider_routes_admitted"] = True
    errors = mod.validate_authority(sup, good_admission())
    assert "supervisor.provider_routes_admitted_not_false" in errors


def test_emergency_stop_must_be_explicit_true():
    sup = good_supervisor()
    sup["free_only"]["free_swarm_owner_emergency_stop"] = False
    errors = mod.validate_authority(sup, good_admission())
    assert "supervisor.emergency_stop_not_true" in errors


def test_sha256_file_is_content_bound(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"alpha")
    a = mod.sha256_file(p)
    p.write_bytes(b"beta")
    b = mod.sha256_file(p)
    assert len(a) == len(b) == 64
    assert a != b
