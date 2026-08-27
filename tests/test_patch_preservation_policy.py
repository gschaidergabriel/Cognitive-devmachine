from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import patch_preservation_policy as policy  # noqa: E402


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def make_repo(tmp_path: Path, *, lines: int = 20) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "policy@example.invalid")
    git(repo, "config", "user.name", "policy test")
    (repo / "sample.py").write_text(
        "".join(f"value_{i} = {i}\n" for i in range(lines)), encoding="utf-8"
    )
    git(repo, "add", "sample.py")
    git(repo, "commit", "-q", "-m", "source")
    return repo, git(repo, "rev-parse", "HEAD")


def test_one_line_edit_passes(tmp_path):
    repo, source = make_repo(tmp_path)
    path = repo / "sample.py"
    text = path.read_text()
    path.write_text(text.replace("value_3 = 3\n", "value_3 = 300\n"), encoding="utf-8")
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is True
    assert got["files"][0]["deleted_lines"] == 1


def test_pure_addition_passes(tmp_path):
    repo, source = make_repo(tmp_path)
    with (repo / "sample.py").open("a", encoding="utf-8") as fh:
        fh.write("requested_feature = True\n")
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is True
    assert got["files"][0]["deleted_lines"] == 0


def test_forty_percent_deletion_rejected_even_though_git_diff_is_valid(tmp_path):
    repo, source = make_repo(tmp_path, lines=20)
    lines = (repo / "sample.py").read_text().splitlines(keepends=True)
    (repo / "sample.py").write_text(
        "".join(lines[8:]) + "requested_feature = True\n", encoding="utf-8"
    )
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is False
    assert any(v["reason"] == "DELETION_FRACTION_EXCEEDED" for v in got["violations"])


def test_ninety_percent_deletion_rejected(tmp_path):
    repo, source = make_repo(tmp_path, lines=20)
    lines = (repo / "sample.py").read_text().splitlines(keepends=True)
    (repo / "sample.py").write_text("".join(lines[-2:]), encoding="utf-8")
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is False
    assert any(v["reason"] == "NET_SHRINK_FRACTION_EXCEEDED" for v in got["violations"])


def test_same_size_single_line_broad_rewrite_is_caught_by_old_content_fraction(tmp_path):
    repo, _source = make_repo(tmp_path, lines=20)
    before = "A" * 1200 + "\n"
    (repo / "sample.py").write_text(before, encoding="utf-8")
    git(repo, "add", "sample.py")
    git(repo, "commit", "-q", "-m", "single-line source")
    source = git(repo, "rev-parse", "HEAD")
    after = "B" * 600 + "A" * 600 + "\n"
    (repo / "sample.py").write_text(after, encoding="utf-8")
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is False
    assert got["files"][0]["deleted_lines"] == 1
    assert any(v["reason"] == "OLD_CONTENT_CHANGE_FRACTION_EXCEEDED" for v in got["violations"])


def test_file_deletion_requires_separate_authority(tmp_path):
    repo, source = make_repo(tmp_path)
    (repo / "sample.py").unlink()
    got = policy.evaluate_worktree(repo, source, ["sample.py"])
    assert got["ok"] is False
    assert got["violations"][0]["reason"] == "FILE_DELETION_REQUIRES_SEPARATE_AUTHORITY"


def test_unexpected_changed_path_fails_closed(tmp_path):
    repo, source = make_repo(tmp_path)
    (repo / "other.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", "other.py")
    git(repo, "commit", "-q", "-m", "add other")
    source = git(repo, "rev-parse", "HEAD")
    (repo / "sample.py").write_text((repo / "sample.py").read_text() + "a = 1\n")
    (repo / "other.py").write_text("x = 2\n", encoding="utf-8")
    with pytest.raises(policy.PreservationError, match="CHANGED_PATH_SET_MISMATCH"):
        policy.evaluate_worktree(repo, source, ["sample.py"])


def test_stale_or_wrong_source_head_fails_closed(tmp_path):
    repo, source = make_repo(tmp_path)
    (repo / "sample.py").write_text((repo / "sample.py").read_text() + "x = 1\n")
    git(repo, "add", "sample.py")
    git(repo, "commit", "-q", "-m", "move head")
    with pytest.raises(policy.PreservationError, match="SOURCE_HEAD_MISMATCH"):
        policy.evaluate_worktree(repo, source, ["sample.py"])


def test_controller_can_supply_explicit_broader_policy_without_worker_payload(tmp_path):
    repo, source = make_repo(tmp_path, lines=20)
    lines = (repo / "sample.py").read_text().splitlines(keepends=True)
    (repo / "sample.py").write_text(
        "".join(lines[8:]) + "requested_feature = True\n", encoding="utf-8"
    )
    broad = policy.Policy(
        max_deleted_fraction=0.50,
        deleted_lines_floor=5,
        max_net_shrink_fraction=0.50,
        net_shrink_lines_floor=5,
        max_old_changed_fraction=0.60,
        old_changed_chars_floor=200,
    )
    got = policy.evaluate_worktree(repo, source, ["sample.py"], policy=broad)
    assert got["ok"] is True
    assert got["policy_authority"] == "CONTROLLER_ARGUMENT_ONLY_NOT_WORKER_PAYLOAD"
