import importlib.util
import subprocess
from pathlib import Path

TOOL = (
    Path(__file__).resolve().parents[1]
    / "DEV_SOURCE_RESEARCH"
    / "repository"
    / "trigger3_root_inventory.py"
)
spec = importlib.util.spec_from_file_location("trigger3_root_inventory", TOOL)
inventory = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(inventory)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Trigger3 Test")
    (repo / "README.md").write_text("root\n", encoding="utf-8")
    (repo / "odd root file").write_text("payload\n", encoding="utf-8")
    (repo / "consumer.txt").write_text("no reference yet\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


def _entry(report: dict, path: str) -> dict:
    return next(row for row in report["entries"] if row["path"] == path)


def test_reference_scan_is_bound_to_reported_committed_head(tmp_path):
    repo = _repo(tmp_path)
    committed_head = _git(repo, "rev-parse", "HEAD")

    (repo / "consumer.txt").write_text('open("odd root file")\n', encoding="utf-8")

    report = inventory.build_inventory(repo, scan_references=True)
    row = _entry(report, "odd root file")

    assert report["schema"] == "TRIGGER3_ROOT_INVENTORY/v2"
    assert report["head"] == committed_head
    assert report["reference_tree"] == "HEAD"
    assert report["reference_scope"] == "TRACKED_COMMITTED_HEAD_ONLY"
    assert report["working_tree_affects_reference_scan"] is False
    assert row["literal_reference_count"] == 0
    assert row["literal_reference_files_sample"] == []


def test_committed_reference_is_reported_without_treeish_prefix(tmp_path):
    repo = _repo(tmp_path)
    (repo / "consumer.txt").write_text('open("odd root file")\n', encoding="utf-8")
    _git(repo, "add", "consumer.txt")
    _git(repo, "commit", "-m", "add committed reference")

    report = inventory.build_inventory(repo, scan_references=True)
    row = _entry(report, "odd root file")

    assert row["literal_reference_count"] == 1
    assert row["literal_reference_files_sample"] == ["consumer.txt"]
    assert row["classification"] == "BLOCKED_LITERAL_DEPENDENCY_CANDIDATES"


def test_staged_reference_does_not_mutate_head_evidence(tmp_path):
    repo = _repo(tmp_path)
    (repo / "consumer.txt").write_text("odd root file\n", encoding="utf-8")
    _git(repo, "add", "consumer.txt")

    report = inventory.build_inventory(repo, scan_references=True)
    row = _entry(report, "odd root file")

    assert row["literal_reference_count"] == 0
    assert _git(repo, "diff", "--cached", "--name-only") == "consumer.txt"


def test_zero_literal_refs_never_becomes_move_authorization(tmp_path):
    repo = _repo(tmp_path)
    report = inventory.build_inventory(repo, scan_references=True)
    row = _entry(report, "odd root file")

    assert row["classification"] == "MOVE_CANDIDATE_ZERO_LITERAL_REFS_NOT_PROOF"
    assert "does not authorize a move" in report["warning"]
