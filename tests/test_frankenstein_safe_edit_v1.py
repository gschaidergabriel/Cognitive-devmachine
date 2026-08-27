import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_safe_edit_v1.py"
)
spec = importlib.util.spec_from_file_location("frankenstein_safe_edit_v1", MODULE_PATH)
assert spec is not None and spec.loader is not None
safe_edit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safe_edit)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    return root


def test_escape_path_is_rejected_before_any_target_write(tmp_path):
    root = _root(tmp_path)
    safe = root / "safe.txt"
    safe.write_text("ORIGINAL", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("SECRET", encoding="utf-8")

    blocks = {
        "safe.txt": "CHANGED",
        "../outside.txt": "OVERWRITE",
    }
    with pytest.raises(safe_edit.UnsafePath):
        safe_edit.SafeEditTransaction(root, blocks)

    assert safe.read_text(encoding="utf-8") == "ORIGINAL"
    assert outside.read_text(encoding="utf-8") == "SECRET"


def test_normalized_duplicate_targets_are_rejected(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(safe_edit.UnsafePath):
        safe_edit.SafeEditTransaction(
            root,
            {"dir/../same.txt": "one", "same.txt": "two"},
        )


def test_stale_preimage_is_rejected_without_clobbering_parallel_change(tmp_path):
    root = _root(tmp_path)
    target = root / "state.txt"
    target.write_text("BASE", encoding="utf-8")
    tx = safe_edit.SafeEditTransaction(root, {"state.txt": "PROPOSAL"})

    target.write_text("PARALLEL_CHANGE", encoding="utf-8")
    with pytest.raises(safe_edit.StalePreimage):
        tx.apply()

    assert target.read_text(encoding="utf-8") == "PARALLEL_CHANGE"


def test_context_exit_before_apply_does_not_restore_stale_preimage(tmp_path):
    root = _root(tmp_path)
    target = root / "state.txt"
    target.write_text("BASE", encoding="utf-8")
    tx = safe_edit.SafeEditTransaction(root, {"state.txt": "PROPOSAL"})
    target.write_text("PARALLEL_CHANGE", encoding="utf-8")

    with tx:
        pass

    assert target.read_text(encoding="utf-8") == "PARALLEL_CHANGE"


def test_multi_file_failure_rolls_back_every_attempted_file(tmp_path):
    root = _root(tmp_path)
    first = root / "a.txt"
    second = root / "b.txt"
    first.write_text("A0", encoding="utf-8")
    second.write_text("B0", encoding="utf-8")

    def fail_after_second_write(path: Path, data: bytes) -> None:
        path.write_bytes(data)
        if path.name == "b.txt":
            raise OSError("synthetic second-write failure")

    tx = safe_edit.SafeEditTransaction(
        root,
        {"a.txt": "A1", "b.txt": "B1"},
        writer=fail_after_second_write,
    )
    with pytest.raises(safe_edit.PartialWriteError):
        tx.apply()

    assert first.read_text(encoding="utf-8") == "A0"
    assert second.read_text(encoding="utf-8") == "B0"


def test_failed_multi_file_edit_removes_new_file_created_by_transaction(tmp_path):
    root = _root(tmp_path)
    existing = root / "existing.txt"
    existing.write_text("OLD", encoding="utf-8")
    created = root / "created.txt"

    def fail_on_existing(path: Path, data: bytes) -> None:
        path.write_bytes(data)
        if path.name == "existing.txt":
            raise OSError("synthetic failure")

    tx = safe_edit.SafeEditTransaction(
        root,
        {"created.txt": "NEW", "existing.txt": "CHANGED"},
        writer=fail_on_existing,
    )
    with pytest.raises(safe_edit.PartialWriteError):
        tx.apply()

    assert not created.exists()
    assert existing.read_text(encoding="utf-8") == "OLD"


def test_python_symbol_loss_is_rejected_even_without_large_shrink(tmp_path):
    root = _root(tmp_path)
    target = root / "module.py"
    old = "def keep():\n    return 1\n\n" + ("# old padding\n" * 30)
    proposed = "def replacement():\n    return 2\n\n" + ("# new padding\n" * 40)
    target.write_text(old, encoding="utf-8")

    tx = safe_edit.SafeEditTransaction(root, {"module.py": proposed})
    with pytest.raises(safe_edit.PreservationViolation, match="symbols disappeared"):
        tx.apply()

    assert target.read_text(encoding="utf-8") == old
    assert len(proposed) > len(old) * 0.5


def test_explicit_symbol_removal_can_be_declared(tmp_path):
    root = _root(tmp_path)
    target = root / "module.py"
    target.write_text("def keep():\n    return 1\n", encoding="utf-8")
    proposed = "def replacement():\n    return 2\n"

    tx = safe_edit.SafeEditTransaction(
        root,
        {"module.py": proposed},
        allowed_removed_symbols={"module.py": {"keep"}},
    )
    tx.apply()
    tx.commit()

    assert target.read_text(encoding="utf-8") == proposed


def test_context_manager_rolls_back_when_not_committed(tmp_path):
    root = _root(tmp_path)
    target = root / "value.txt"
    target.write_text("OLD", encoding="utf-8")

    with safe_edit.SafeEditTransaction(root, {"value.txt": "NEW"}) as tx:
        tx.apply()
        assert target.read_text(encoding="utf-8") == "NEW"

    assert target.read_text(encoding="utf-8") == "OLD"


def test_context_manager_keeps_exact_postimage_after_commit(tmp_path):
    root = _root(tmp_path)
    target = root / "value.txt"
    target.write_text("OLD", encoding="utf-8")

    with safe_edit.SafeEditTransaction(root, {"value.txt": "NEW"}) as tx:
        postimages = tx.apply()
        committed = tx.commit()
        assert committed["value.txt"].sha256 == postimages["value.txt"].sha256

    assert target.read_text(encoding="utf-8") == "NEW"


def test_postimage_tamper_before_commit_is_rejected_and_rolled_back(tmp_path):
    root = _root(tmp_path)
    target = root / "value.txt"
    target.write_text("OLD", encoding="utf-8")
    tx = safe_edit.SafeEditTransaction(root, {"value.txt": "NEW"})
    tx.apply()
    target.write_text("TAMPER", encoding="utf-8")

    with pytest.raises(safe_edit.StalePreimage, match="postimage changed"):
        tx.commit()

    assert target.read_text(encoding="utf-8") == "OLD"
