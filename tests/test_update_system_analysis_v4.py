from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/update_system_analysis_v4.py"
spec = importlib.util.spec_from_file_location("update_system_analysis_v4", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_snapshot_running_never_becomes_live_proc(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": "9.07",
        "current_frontier": {"current_free_provider_admission": "9.07_ALL_PROVIDERS_FALSE_OWNER_EMERGENCY_STOP"},
        "free_only": {
            "provider_routes_admitted": False,
            "free_swarm_owner_emergency_stop": True,
            "together_forbidden": True,
        },
    })
    write_json(art / "SUPERVISOR.json", {
        "go_swarm_running": True,
        "distillery_running": True,
        "forge_running": True,
        "dashboard_running": True,
        "provider_admission": {"openrouter": True},
    })

    p = mod.provenance(repo, art, proc)
    assert p["authority"]["authority_state"] == "HARD_OFF"
    assert p["authority"]["provider_routes_admitted"] is False
    for name in ("go_swarm", "distillery", "evidence_forge", "dashboard"):
        assert p["runtime"]["live_proc_observed"][name] is False
        assert p["runtime"]["snapshot_fallback"][name] is True
        assert p["runtime"]["effective_status"][name] == "SNAPSHOT_ONLY_UNTRUSTED"


def test_missing_current_authority_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    p = mod.provenance(repo, art, proc)
    a = p["authority"]
    assert a["valid"] is False
    assert a["provider_routes_admitted"] is False
    assert a["authority_state"] == "FAIL_CLOSED"
    assert a["free_swarm_owner_emergency_stop"] is True


def test_live_proc_and_snapshot_are_independent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    (proc / "123").mkdir(parents=True)
    (proc / "123/cmdline").write_bytes(b"python\0run_free_evidence_forge.py\0")
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": "9.07",
        "current_frontier": {"current_free_provider_admission": "HARD_OFF"},
        "free_only": {
            "provider_routes_admitted": False,
            "free_swarm_owner_emergency_stop": True,
            "together_forbidden": True,
        },
    })
    write_json(art / "SUPERVISOR.json", {"forge_running": False})
    p = mod.provenance(repo, art, proc)
    assert p["runtime"]["live_proc_observed"]["evidence_forge"] is True
    assert p["runtime"]["snapshot_fallback"]["evidence_forge"] is False
    assert p["runtime"]["effective_status"]["evidence_forge"] == "LIVE_PROC_OBSERVED"


def test_snapshot_provider_admission_is_never_authority(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": "9.07",
        "current_frontier": {"current_free_provider_admission": "9.07_ALL_PROVIDERS_FALSE_OWNER_EMERGENCY_STOP"},
        "free_only": {
            "provider_routes_admitted": False,
            "free_swarm_owner_emergency_stop": True,
            "together_forbidden": True,
        },
    })
    write_json(art / "SUPERVISOR.json", {
        "provider_admission": {"openrouter": True, "groq": True},
        "policy": "LEGACY_ALLOW",
    })
    p = mod.provenance(repo, art, proc)
    assert p["authority"]["provider_routes_admitted"] is False
    assert p["snapshot_provenance"]["trusted_for_execution_authority"] is False
    assert p["snapshot_provenance"]["trusted_for_host_local_process_proof"] is False
