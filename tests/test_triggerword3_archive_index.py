import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "DEV_SOURCE_RESEARCH"
    / "repository"
    / "tools"
    / "build_archive_index.py"
)
spec = importlib.util.spec_from_file_location("triggerword3_archive_index", MODULE_PATH)
idx = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(idx)


def test_deterministic_sorted_and_classified(tmp_path):
    (tmp_path / "research_entity/topic_packets/x").mkdir(parents=True)
    (tmp_path / "research_entity/topic_packets/x/GWT_NOTE.md").write_text(
        "# GWT Note\nbody\n", encoding="utf-8"
    )
    (tmp_path / "receipts").mkdir()
    (tmp_path / "receipts/z.json").write_text('{"ok": true}\n', encoding="utf-8")

    a = idx.build_index(tmp_path, ["receipts", "research_entity"])
    b = idx.build_index(tmp_path, ["research_entity", "receipts"])

    assert a == b
    assert [e["path"] for e in a["entries"]] == sorted(e["path"] for e in a["entries"])
    note = next(e for e in a["entries"] if e["path"].endswith("GWT_NOTE.md"))
    assert note["heading"] == "GWT Note"
    assert "topic_packet" in note["labels"]
    assert "gwt" in note["labels"]
    receipt = next(e for e in a["entries"] if e["path"].startswith("receipts/"))
    assert "receipt_or_evidence" in receipt["labels"]
    assert receipt["sha256"]


def test_missing_roots_are_explicit_but_not_errors(tmp_path):
    payload = idx.build_index(tmp_path, ["missing", "research_entity"])
    assert payload["entry_count"] == 0
    assert payload["roots_present"] == []
    assert payload["roots_requested"] == ["missing", "research_entity"]


def test_oversize_hash_skip(tmp_path):
    (tmp_path / "research_sources").mkdir()
    p = tmp_path / "research_sources/big.bin"
    p.write_bytes(b"x" * 20)
    payload = idx.build_index(tmp_path, ["research_sources"], max_hash_bytes=10)
    entry = payload["entries"][0]
    assert entry["sha256"] is None
    assert entry["hash_status"] == "SKIPPED_OVERSIZE"


def test_atomic_writer(tmp_path):
    out = tmp_path / "deep/index.json"
    idx.write_json_atomic(out, {"b": 2, "a": 1})
    assert json.loads(out.read_text()) == {"a": 1, "b": 2}
    assert not (out.parent / (out.name + ".tmp")).exists()