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


def write_authority(repo: Path, *, epoch: str = "9.09", routes: bool = False,
                    emergency: bool = True, provider_value: bool = False,
                    together_forbidden: bool = True) -> None:
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": epoch,
        "current_frontier": {"current_free_provider_admission": f"{epoch}_TEST"},
        "free_only": {
            "provider_routes_admitted": routes,
            "free_swarm_owner_emergency_stop": emergency,
            "together_forbidden": together_forbidden,
        },
    })
    write_json(repo / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json", {
        "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1",
        "authority_epoch": epoch,
        "mode": "FREE_ONLY",
        "providers": {
            "groq": {"admitted": provider_value},
            "mistral": {"admitted": provider_value},
            "nvidia": {"admitted": provider_value},
            "openrouter": {"admitted": provider_value},
        },
    })


def test_snapshot_running_never_becomes_live_proc(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_authority(repo)
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
    assert p["authority"]["valid"] is True
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
    write_authority(repo)
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
    write_authority(repo)
    write_json(art / "SUPERVISOR.json", {
        "provider_admission": {"openrouter": True, "groq": True},
        "policy": "LEGACY_ALLOW",
    })
    p = mod.provenance(repo, art, proc)
    assert p["authority"]["provider_routes_admitted"] is False
    assert p["snapshot_provenance"]["trusted_for_execution_authority"] is False
    assert p["snapshot_provenance"]["trusted_for_host_local_process_proof"] is False


def test_epoch_split_between_inbox_and_provider_admission_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_authority(repo, epoch="9.09")
    adm = repo / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
    data = json.loads(adm.read_text())
    data["authority_epoch"] = "9.08"
    write_json(adm, data)
    a = mod.provenance(repo, art, proc)["authority"]
    assert a["valid"] is False
    assert a["authority_state"] == "FAIL_CLOSED"
    assert a["coherence_reason"] == "AUTHORITY_EPOCH_SPLIT"


def test_route_provider_map_split_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_authority(repo, routes=False, emergency=False, provider_value=True)
    a = mod.provenance(repo, art, proc)["authority"]
    assert a["valid"] is False
    assert a["provider_routes_admitted"] is False
    assert a["coherence_reason"] == "ROUTE_PROVIDER_MAP_SPLIT"


def test_emergency_stop_cannot_coexist_with_admitted_provider(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_authority(repo, routes=True, emergency=True, provider_value=True)
    a = mod.provenance(repo, art, proc)["authority"]
    assert a["valid"] is False
    assert a["provider_routes_admitted"] is False
    assert a["coherence_reason"] == "EMERGENCY_STOP_PROVIDER_SPLIT"


def test_paid_fallback_policy_split_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    write_authority(repo, together_forbidden=False)
    a = mod.provenance(repo, art, proc)["authority"]
    assert a["valid"] is False
    assert a["coherence_reason"] == "TOGETHER_POLICY_SPLIT"
