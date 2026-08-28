import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_forge_repair as repair  # noqa: E402


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Clay Test")
    (repo / "tools").mkdir()
    (repo / "tools/x.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(repo, "add", "tools/x.py")
    git(repo, "commit", "-qm", "seed")
    return repo


def make_db(tmp_path: Path, proposal: dict, *, state: str = "PATCH_REJECTED", repo_head: str = "f" * 40) -> Path:
    db = tmp_path / "forge.sqlite3"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE candidates("
        "candidate_hash TEXT PRIMARY KEY, delta_id TEXT, proposal_json TEXT NOT NULL, "
        "state TEXT NOT NULL, last_reason TEXT, ingested_at TEXT, evaluated_at TEXT, repo_head TEXT)"
    )
    con.execute(
        "INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?)",
        (
            "a" * 64,
            "old-delta",
            json.dumps(proposal),
            state,
            "error: patch does not apply",
            "2026-08-24T00:00:00Z",
            "2026-08-24T00:01:00Z",
            repo_head,
        ),
    )
    con.commit()
    con.close()
    return db


def proposal(**overrides):
    obj = {
        "hypothesis": "repair exact source",
        "mechanism": "replace stale hunk",
        "target_files": ["tools/x.py"],
        "patch_unified_diff": (
            "--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n"
            "-VALUE = 0\n+VALUE = 2\n"
        ),
    }
    obj.update(overrides)
    return obj


def test_repair_packet_uses_exact_committed_blob_not_dirty_worktree(tmp_path):
    repo = make_repo(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    db = make_db(tmp_path, proposal(), repo_head="e" * 40)
    (repo / "tools/x.py").write_text("DIRTY = 999\n", encoding="utf-8")

    packets = repair.load_repair_packets(db_path=db, repo_root=repo)
    assert len(packets) == 1
    packet = packets[0]
    assert packet["repair_source_commit"] == head
    assert packet["previous_candidate_source_head"] == "e" * 40
    source = packet["target_sources"][0]
    assert source["state"] == "TRACKED_COMMITTED_SOURCE"
    assert source["content"] == "VALUE = 1\n"
    assert source["blob_sha"] == git(repo, "rev-parse", "HEAD:tools/x.py")
    assert source["sha256"]
    assert packet["execution_authority"] == "NONE"
    assert packet["canonical_truth"] is False


def test_unsafe_or_untracked_target_never_enters_repair_prompt(tmp_path):
    repo = make_repo(tmp_path)
    db = make_db(tmp_path, proposal(target_files=["../secret.env"]))
    assert repair.load_repair_packets(db_path=db, repo_root=repo) == []

    db.unlink()
    db = make_db(tmp_path, proposal(target_files=["tools/new.py"]))
    assert repair.load_repair_packets(db_path=db, repo_root=repo) == []


def test_large_file_anchor_excerpt_is_bounded_and_marked_truncated(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    anchor = "TARGET_CONTEXT = 'old-value'"
    (repo / "tools/x.py").write_text("A" * 400 + "\n" + anchor + "\n" + "Z" * 400, encoding="utf-8")
    git(repo, "add", "tools/x.py")
    git(repo, "commit", "-qm", "large")
    monkeypatch.setattr(repair, "MAX_SOURCE_BYTES_PER_TARGET", 160)
    p = proposal(
        patch_unified_diff=(
            "--- a/tools/x.py\n+++ b/tools/x.py\n@@ -2 +2 @@\n"
            f"-{anchor}\n+TARGET_CONTEXT = 'new-value'\n"
        )
    )
    source = repair.load_repair_packets(db_path=make_db(tmp_path, p), repo_root=repo)[0]["target_sources"][0]
    assert source["truncated"] is True
    assert source["excerpt_strategy"] == "PATCH_CONTEXT_ANCHOR"
    assert anchor in source["content"]
    assert len(source["content"].encode("utf-8")) <= 160


def test_only_even_serials_receive_backlog_repair_and_lineage_is_preserved(tmp_path):
    repo = make_repo(tmp_path)
    packets = repair.load_repair_packets(db_path=make_db(tmp_path, proposal()), repo_root=repo)
    assert repair.repair_suffix(1, packets) == ""
    text = repair.repair_suffix(2, packets)
    assert "FORGE SOURCE-BOUND REPAIR PACKET" in text
    assert '"repair_of_candidate_hash":"' + "a" * 64 + '"' in text
    assert '"repair_of_delta_id":"old-delta"' in text
    assert "never defend it by weakening Forge" in text


def test_legacy_db_without_repo_head_is_read_without_inventing_old_identity(tmp_path):
    repo = make_repo(tmp_path)
    db = tmp_path / "legacy.sqlite3"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE candidates("
        "candidate_hash TEXT PRIMARY KEY, delta_id TEXT, proposal_json TEXT NOT NULL, "
        "state TEXT NOT NULL, last_reason TEXT, ingested_at TEXT, evaluated_at TEXT)"
    )
    con.execute(
        "INSERT INTO candidates VALUES(?,?,?,?,?,?,?)",
        ("b" * 64, "legacy", json.dumps(proposal()), "PATCH_REJECTED", "old", "x", "y"),
    )
    con.commit()
    con.close()
    packet = repair.load_repair_packets(db_path=db, repo_root=repo)[0]
    assert packet["previous_candidate_source_head"] is None
    assert packet["repair_source_commit"] == git(repo, "rev-parse", "HEAD")
