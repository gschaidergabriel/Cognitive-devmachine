from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/update_root_results.py"
spec = importlib.util.spec_from_file_location("update_root_results", MODULE_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_classify_detects_stale_fabric_epoch():
    canonical = {"ok": True, "authority_epoch": "8.71"}
    runtime = {"ok": True, "authority_epoch": "8.71"}
    manifest = {"provider_admission_epoch": "8.69"}
    result = m.classify_authority(canonical, runtime, manifest, supervisor_running=True, fabric_running=True)
    assert result["state"] == "FABRIC_RESTART_REQUIRED_ADMISSION_EPOCH_STALE"


def test_classify_detects_stale_supervisor_snapshot_first():
    canonical = {"ok": True, "authority_epoch": "8.71"}
    runtime = {"ok": True, "authority_epoch": "8.69"}
    manifest = {"provider_admission_epoch": "8.69"}
    result = m.classify_authority(canonical, runtime, manifest, supervisor_running=True, fabric_running=True)
    assert result["state"] == "SUPERVISOR_RUNTIME_ADMISSION_STALE"


def test_classify_aligned_871():
    canonical = {"ok": True, "authority_epoch": "8.71"}
    runtime = {"ok": True, "authority_epoch": "8.71"}
    manifest = {"provider_admission_epoch": "8.71"}
    result = m.classify_authority(canonical, runtime, manifest, supervisor_running=True, fabric_running=True)
    assert result["state"] == "ALIGNED"


def test_compatibility_maps_current_6000_fields():
    sup = {"schema": "CLAY_6000_SWARM_SUPERVISOR/v4", "provider_admission": {"authority_epoch": "8.69"}}
    canonical = {"ok": True, "authority_epoch": "8.71", "admitted_free_providers": ["nvidia"]}
    result = m.compatibility_supervisor(sup, canonical, supervisor_running=True, fabric_running=True, local_ready=True)
    assert result["go_swarm_running"] is True
    assert result["local_research_model_ready"] is True
    assert result["provider_admission"]["authority_epoch"] == "8.71"
    assert result["provider_admission_runtime"]["authority_epoch"] == "8.69"


def test_readme_runtime_rewrites_legacy_rows(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# x\n### 3. Script-by-Script — live\n"
        "| **24h Supervisor** `run_24h_entityos_swarm_supervisor.sh` | old | STOPPED/QUARANTINED | old |\n"
        "| **GO Free Swarm** `run_24h_entityos_swarm.py` | old | STOPPED/QUARANTINED | old |\n"
        "| **Local 4B lane** `local_research_model_server.sh` | old | NOT_READY | old |\n",
        encoding="utf-8",
    )
    truth = {"runtime": {
        "supervisor": "RUNNING",
        "go_swarm": "RUNNING",
        "local_model": "READY",
        "local_model_bootstrap": "IDLE",
        "authority_alignment": {"state": "ALIGNED", "canonical_epoch": "8.71", "runtime_supervisor_epoch": "8.71", "fabric_manifest_epoch": "8.71"},
    }}
    m.patch_readme_runtime(readme, truth)
    text = readme.read_text(encoding="utf-8")
    assert "**6000 Supervisor**" in text
    assert "authority `ALIGNED`" in text
    assert "| RUNNING |" in text
    assert "| READY |" in text
    assert "8.69" not in text


def test_atomic_json_roundtrip(tmp_path: Path):
    target = tmp_path / "x.json"
    m.atomic_json(target, {"epoch": "8.71"})
    assert json.loads(target.read_text())["epoch"] == "8.71"
