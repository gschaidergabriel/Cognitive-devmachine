from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/update_system_analysis_v5.py"
spec = importlib.util.spec_from_file_location("update_system_analysis_v5", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: dict) -> None:
    write(path, json.dumps(obj))


def test_legacy_staging_never_touches_real_canonical_output(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    fs = repo / "free swarm"
    fs.mkdir(parents=True)
    sentinel = {"sentinel": "REAL_CANONICAL_MUST_NOT_CHANGE"}
    write_json(fs / "SYSTEM_ANALYSIS_LIVE.json", sentinel)
    write_json(fs / "LIVE_METRICS.json", {})
    write_json(fs / "DISTILLERY_LIVE.json", {})
    write(fs / "README.md", "# real readme\n")

    fake = tmp_path / "fake_legacy.py"
    write(fake, '''
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("--repo"); p.add_argument("--artifacts"); a=p.parse_args()
r=Path(a.repo)/"free swarm"; r.mkdir(parents=True,exist_ok=True)
(r/"SYSTEM_ANALYSIS_LIVE.json").write_text(json.dumps({"runtime":{"provider_admission":{"openrouter":True}},"metric":7}))
(r/"README.md").write_text("# staged readme\\nLEGACY-STAGED\\n")
''')

    rc, staged, staged_readme, _ = mod.run_legacy_staged(repo, art, fake)
    assert rc == 0
    assert staged["metric"] == 7
    assert "LEGACY-STAGED" in staged_readme
    assert json.loads((fs / "SYSTEM_ANALYSIS_LIVE.json").read_text()) == sentinel
    assert (fs / "README.md").read_text() == "# real readme\n"


def test_harden_replaces_legacy_runtime_and_authority_before_publish() -> None:
    legacy = {
        "runtime": {"go_swarm": "RUNNING", "provider_admission": {"openrouter": True}},
        "costs": {"x": 1},
    }
    p = {
        "runtime": {"live_proc_observed": {"go_swarm": False}},
        "authority": {"authority_state": "HARD_OFF", "provider_routes_admitted": False},
        "snapshot_provenance": {"trusted_for_execution_authority": False},
    }
    out = mod.harden(legacy, p)
    assert out["schema"] == "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v5"
    assert out["runtime"] == p["runtime"]
    assert out["provider_authority"] == p["authority"]
    assert out["legacy_untrusted_runtime_snapshot"] == legacy["runtime"]
    assert out["costs"] == {"x": 1}
    assert "STAGED_OFF_CANONICAL_PATH" in out["publication_rule"]


def test_atomic_write_replaces_complete_file(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    p.write_text("old", encoding="utf-8")
    mod.atomic_write_text(p, '{"new":true}\n')
    assert p.read_text(encoding="utf-8") == '{"new":true}\n'
    assert not list(tmp_path.glob("x.json.*.tmp"))


def test_replace_block_text_never_duplicates_provenance_block() -> None:
    b1 = mod.v4.PROVENANCE_BEGIN + "\nold\n" + mod.v4.PROVENANCE_END
    b2 = mod.v4.PROVENANCE_BEGIN + "\nnew\n" + mod.v4.PROVENANCE_END
    out = mod.replace_block_text("# x\n\n" + b1 + "\n", b2)
    assert out.count(mod.v4.PROVENANCE_BEGIN) == 1
    assert out.count(mod.v4.PROVENANCE_END) == 1
    assert "new" in out and "old" not in out


def test_staged_legacy_failure_is_not_a_publishable_metrics_result(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    art = tmp_path / "art"
    (repo / "free swarm").mkdir(parents=True)
    fake = tmp_path / "fail.py"
    write(fake, "raise SystemExit(3)\n")
    rc, staged, _, _ = mod.run_legacy_staged(repo, art, fake)
    assert rc == 3
    assert staged == {}
