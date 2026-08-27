import hashlib
from pathlib import Path
import subprocess

import pytest
import importlib.util

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_edit_contract_v1.py"
)
spec = importlib.util.spec_from_file_location("frankenstein_edit_contract_v1", MODULE_PATH)
assert spec is not None and spec.loader is not None
edit_contract = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = edit_contract
spec.loader.exec_module(edit_contract)

EditContract = edit_contract.EditContract
EditContractError = edit_contract.EditContractError
apply_validated_edit = edit_contract.apply_validated_edit
validate_edit_contract = edit_contract.validate_edit_contract


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _repo(tmp_path: Path, text: str = "alpha\nbeta\ngamma\ndelta\n") -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Trigger3 Test")
    target = root / "sample.txt"
    target.write_text(text, encoding="utf-8")
    _git(root, "add", "sample.txt")
    _git(root, "commit", "-qm", "base")
    return root, target


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch(old: str, new: str, path: str = "sample.txt") -> str:
    import difflib

    body = "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    return f"diff --git a/{path} b/{path}\n" + body


def test_narrow_additive_patch_validates_and_applies(tmp_path):
    old = "alpha\nbeta\ngamma\ndelta\n"
    new = "alpha\nbeta\ninserted\ngamma\ndelta\n"
    root, target = _repo(tmp_path, old)
    contract = EditContract(
        path="sample.txt",
        preimage_sha256=_sha(target),
        patch=_patch(old, new),
        max_deleted_lines=0,
        max_added_lines=1,
    )

    validated = validate_edit_contract(root, contract)
    assert validated.added_lines == 1
    assert validated.deleted_lines == 0
    assert target.read_text() == old  # validation is non-mutating

    apply_validated_edit(root, validated)
    assert target.read_text() == new
    assert _git(root, "diff", "--name-only") == "sample.txt"


def test_stale_preimage_hash_rejected(tmp_path):
    root, target = _repo(tmp_path)
    contract = EditContract(
        path="sample.txt",
        preimage_sha256="0" * 64,
        patch=_patch(target.read_text(), target.read_text() + "extra\n"),
        max_added_lines=1,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "PREIMAGE_HASH_MISMATCH"


def test_patch_for_different_path_rejected(tmp_path):
    root, target = _repo(tmp_path)
    other = root / "other.txt"
    other.write_text("one\ntwo\n", encoding="utf-8")
    _git(root, "add", "other.txt")
    _git(root, "commit", "-qm", "other")

    contract = EditContract(
        path="sample.txt",
        preimage_sha256=_sha(target),
        patch=_patch("one\ntwo\n", "one\nchanged\ntwo\n", "other.txt"),
        max_added_lines=1,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "PATCH_TARGET_MISMATCH"


def test_path_traversal_rejected(tmp_path):
    root, _ = _repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    contract = EditContract(
        path="../outside.txt",
        preimage_sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        patch=_patch("outside\n", "changed\n", "../outside.txt"),
        max_deleted_lines=1,
        max_added_lines=1,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "PATH_ESCAPES_REPOSITORY"


def test_deletion_below_old_50_percent_guard_still_requires_declared_budget(tmp_path):
    old = "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\n"
    new = "a\nb\nc\nd\ne\nf\ng\n"  # 30% deletion: would evade a 50%-shrink heuristic
    root, target = _repo(tmp_path, old)
    contract = EditContract(
        path="sample.txt",
        preimage_sha256=_sha(target),
        patch=_patch(old, new),
        max_deleted_lines=0,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "DELETION_BUDGET_EXCEEDED"


def test_explicit_deletion_budget_allows_declared_refactor(tmp_path):
    old = "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\n"
    new = "a\nb\nc\nd\ne\nf\ng\n"
    root, target = _repo(tmp_path, old)
    validated = validate_edit_contract(
        root,
        EditContract(
            path="sample.txt",
            preimage_sha256=_sha(target),
            patch=_patch(old, new),
            max_deleted_lines=3,
            max_added_lines=0,
        ),
    )
    assert validated.deleted_lines == 3
    assert validated.added_lines == 0


def test_dirty_worktree_path_rejected_before_patch_check(tmp_path):
    old = "alpha\nbeta\ngamma\ndelta\n"
    root, target = _repo(tmp_path, old)
    target.write_text(old + "local-uncommitted\n", encoding="utf-8")
    contract = EditContract(
        path="sample.txt",
        preimage_sha256=_sha(target),
        patch=_patch(target.read_text(), target.read_text() + "proposed\n"),
        max_added_lines=1,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "WORKTREE_PATH_DIRTY"


def test_toctou_change_after_validation_rejected(tmp_path):
    old = "alpha\nbeta\ngamma\ndelta\n"
    new = "alpha\nbeta\ninserted\ngamma\ndelta\n"
    root, target = _repo(tmp_path, old)
    validated = validate_edit_contract(
        root,
        EditContract(
            path="sample.txt",
            preimage_sha256=_sha(target),
            patch=_patch(old, new),
            max_added_lines=1,
        ),
    )

    # Simulate a concurrent canonical change, then commit it so the path is clean but preimage differs.
    target.write_text("concurrent\n" + old, encoding="utf-8")
    _git(root, "add", "sample.txt")
    _git(root, "commit", "-qm", "concurrent")

    with pytest.raises(EditContractError) as exc:
        apply_validated_edit(root, validated)
    assert exc.value.code == "PREIMAGE_CHANGED_AFTER_VALIDATION"


def test_symlink_escape_rejected(tmp_path):
    root, _ = _repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = root / "link.txt"
    link.symlink_to(outside)
    contract = EditContract(
        path="link.txt",
        preimage_sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        patch=_patch("outside\n", "changed\n", "link.txt"),
        max_deleted_lines=1,
        max_added_lines=1,
    )
    with pytest.raises(EditContractError) as exc:
        validate_edit_contract(root, contract)
    assert exc.value.code == "PATH_ESCAPES_REPOSITORY"
