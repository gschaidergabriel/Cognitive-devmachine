from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "system_analysis_authority_consumer_audit_v1.py"
spec = importlib.util.spec_from_file_location("audit_mod", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_authority_consumer_direct_mirror_fails(tmp_path: Path):
    write(tmp_path, "tools/runtime_authority_gate.py", "from pathlib import Path\np=Path('free swarm/SYSTEM_ANALYSIS_LIVE.json')\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "FAIL_CLOSED"
    assert r["violations"][0]["path"] == "tools/runtime_authority_gate.py"


def test_verified_reader_consumer_passes(tmp_path: Path):
    write(tmp_path, "tools/runtime_authority_gate.py", "from tools.system_analysis_current_reader_v1 import read_current_publication\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "PASS"
    assert "tools/runtime_authority_gate.py" in r["verified_reader_consumers"]


def test_non_authority_direct_ref_is_review_not_credit_pass_violation(tmp_path: Path):
    write(tmp_path, "scripts/dashboard_export.py", "P='SYSTEM_ANALYSIS_LIVE.json'\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "PASS"
    assert r["review_non_authority_direct_mirror_refs"]


def test_publisher_is_exempt(tmp_path: Path):
    write(tmp_path, "free swarm/update_system_analysis_v6.py", "P='SYSTEM_ANALYSIS_LIVE.json'\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "PASS"
    assert not r["violations"]


def test_parse_error_fails_closed(tmp_path: Path):
    write(tmp_path, "tools/runtime_authority_gate.py", "def broken(:\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "FAIL_CLOSED"
    assert r["parse_errors"]


def test_provenance_mirror_is_also_forbidden(tmp_path: Path):
    write(tmp_path, "tools/quiescence_authority.py", "P='free swarm/SYSTEM_ANALYSIS_PROVENANCE.json'\n")
    r = mod.audit(tmp_path)
    assert r["state"] == "FAIL_CLOSED"
    assert "SYSTEM_ANALYSIS_PROVENANCE.json" in r["violations"][0]["mirror_hits"]
