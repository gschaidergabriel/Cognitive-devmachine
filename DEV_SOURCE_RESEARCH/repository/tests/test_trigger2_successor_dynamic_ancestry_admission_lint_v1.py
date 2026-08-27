from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger2_successor_dynamic_ancestry_admission_lint_v1.py"
spec = importlib.util.spec_from_file_location("trigger2_successor_dynamic_ancestry_admission_lint_v1", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, check=True, text=True, stdout=subprocess.PIPE)
    return p.stdout.strip()


def commit(root: Path, message: str) -> str:
    git(root, "add", ".")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def ledger_path(v: int) -> str:
    return f"research_entity/global/j-space/research/2026-08-25_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V{v}_GPT56SOL.json"


def write_ledger(root: Path, v: int, supersedes=None):
    path = root / ledger_path(v)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": f"CLAY_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER/v{v}",
        "status": "CURRENT_RESEARCH_LEDGER_NONCANONICAL",
    }
    if supersedes is not None:
        data["supersedes"] = supersedes
    path.write_text(json.dumps(data), encoding="utf-8")


def setup_repo(tmp_path: Path) -> tuple[Path, str, str]:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    write_ledger(root, 18)
    c18 = commit(root, "ledger18")
    write_ledger(root, 21, ledger_path(18))
    c21 = commit(root, "ledger21")
    return root, c18, c21


def add_candidate(root: Path, name: str) -> str:
    p = root / "research_entity/global/j-space/research" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}", encoding="utf-8")
    return commit(root, name)


def test_stale_declared_ledger_forces_donor_only(tmp_path):
    root, _, _ = setup_repo(tmp_path)
    candidate = add_candidate(root, "candidate_stale.json")
    out = mod.lint(
        root=root,
        candidate_commit=candidate,
        declared_ledger="T2-LEDGER-V18",
        scope=mod.CURRENT_SCOPE,
    )
    assert out["pass"] is False
    assert "STALE_ON_ARRIVAL_CURRENTNESS" in out["failures"]
    assert out["stale_on_arrival_currentness"] is True
    assert out["classification"] == "DONOR_ONLY_NEEDS_REENTRY"
    assert out["eligible_for_next_gate"] is False
    assert out["resolved_parent_ledger_id"] == "T2-LEDGER-V21"
    assert out["training_credit_minted"] is False


def test_matching_declared_ledger_is_only_eligible_next_gate(tmp_path):
    root, _, _ = setup_repo(tmp_path)
    candidate = add_candidate(root, "candidate_current.json")
    out = mod.lint(
        root=root,
        candidate_commit=candidate,
        declared_ledger="T2-LEDGER-V21",
        scope=mod.CURRENT_SCOPE,
    )
    assert out["pass"] is True
    assert out["stale_on_arrival_currentness"] is False
    assert out["classification"] == "ELIGIBLE_FOR_NEXT_GATE_NOT_ADMITTED"
    assert out["eligible_for_next_gate"] is True
    assert out["canonical_dataset_admission"] is False


def test_explicit_historical_scope_preserves_old_donor(tmp_path):
    root, _, _ = setup_repo(tmp_path)
    candidate = add_candidate(root, "candidate_history.json")
    out = mod.lint(
        root=root,
        candidate_commit=candidate,
        declared_ledger="T2-LEDGER-V18",
        scope=mod.DONOR_SCOPE,
    )
    assert out["pass"] is True
    assert out["classification"] == "DONOR_ONLY_HISTORICAL_VALID_SCOPE"
    assert out["eligible_for_next_gate"] is False
    assert out["stale_on_arrival_currentness"] is False


def test_ambiguous_heads_fail_closed(tmp_path):
    root, _, _ = setup_repo(tmp_path)
    write_ledger(root, 22, ledger_path(21))
    write_ledger(root, 23, ledger_path(21))
    commit(root, "forked ledgers")
    candidate = add_candidate(root, "candidate_ambiguous.json")
    out = mod.lint(
        root=root,
        candidate_commit=candidate,
        declared_ledger="T2-LEDGER-V22",
        scope=mod.CURRENT_SCOPE,
    )
    assert out["pass"] is False
    assert any(x.startswith("AMBIGUOUS_REACHABLE_LEDGER_HEADS:") for x in out["failures"])
    assert out["classification"] == "BLOCKED"


def test_unknown_declared_ledger_fails_closed(tmp_path):
    root, _, _ = setup_repo(tmp_path)
    candidate = add_candidate(root, "candidate_unknown.json")
    out = mod.lint(
        root=root,
        candidate_commit=candidate,
        declared_ledger="T2-LEDGER-V999",
        scope=mod.CURRENT_SCOPE,
    )
    assert out["pass"] is False
    assert "DECLARED_LEDGER_NOT_REACHABLE_FROM_PARENT" in out["failures"]
    assert out["classification"] == "BLOCKED"
