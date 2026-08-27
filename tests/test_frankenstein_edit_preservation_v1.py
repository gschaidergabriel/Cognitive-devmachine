import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_edit_preservation_v1.py"
)
if not MODULE_PATH.exists():
    MODULE_PATH = Path(__file__).resolve().parents[1] / "frankenstein_edit_preservation_v1.py"

spec = importlib.util.spec_from_file_location("frankenstein_edit_preservation_v1", MODULE_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

EditContract = m.EditContract
EditPreservationError = m.EditPreservationError
LineRange = m.LineRange
sha256_text = m.sha256_text
validate_changed_path_set = m.validate_changed_path_set
validate_edit = m.validate_edit


def contract_for(text, *, ranges=(LineRange(2, 2),), path="tools/grid10_fabric.py", **kw):
    return EditContract(
        path=path,
        preimage_sha256=sha256_text(text),
        allowed_preimage_ranges=tuple(ranges),
        declared_changed_paths=(path,),
        **kw,
    )


def test_narrow_declared_change_passes_and_receipt_binds_both_images():
    before = "a\nb\nc\n"
    after = "a\nB\nc\n"
    receipt = validate_edit(before, after, contract_for(before))
    assert receipt["preservation_gate"] == "PASS"
    assert receipt["preimage_sha256"] == sha256_text(before)
    assert receipt["postimage_sha256"] == sha256_text(after)


def test_stale_preimage_fails_closed():
    before = "a\nb\nc\n"
    c = contract_for(before)
    with pytest.raises(EditPreservationError, match="stale or wrong preimage"):
        validate_edit("a\nchanged-before-apply\nc\n", "a\nB\nc\n", c)


def test_undeclared_large_deletion_is_rejected_even_if_feature_line_survives():
    before = "feature = old\n" + "\n".join(f"keep_{i}" for i in range(1, 10)) + "\n"
    after = "feature = new\nkeep_9\n"
    c = contract_for(before, ranges=(LineRange(1, 1),))
    with pytest.raises(EditPreservationError, match="undeclared preimage regions"):
        validate_edit(before, after, c)


def test_below_fifty_percent_deletion_still_fails_when_outside_declared_scope():
    before = "\n".join(f"line_{i}" for i in range(1, 11)) + "\n"
    after = "\n".join(["line_1", "line_2", "line_3", "line_8", "line_9", "line_10"]) + "\n"
    c = contract_for(before, ranges=(LineRange(1, 1),))
    with pytest.raises(EditPreservationError, match="undeclared preimage regions"):
        validate_edit(before, after, c)


def test_task_local_success_cannot_override_preservation_failure():
    before = "feature = old\ncritical = preserve\nother = preserve\n"
    after = "feature = new\n"
    assert "feature = new" in after
    c = contract_for(before, ranges=(LineRange(1, 1),))
    with pytest.raises(EditPreservationError):
        validate_edit(before, after, c)


def test_deletion_budget_is_defense_in_depth_not_scope_substitute():
    before = "a\nb\nc\nd\n"
    after = "a\nB\n"
    c = contract_for(before, ranges=(LineRange(2, 2),), max_deleted_preimage_lines=10)
    with pytest.raises(EditPreservationError, match="undeclared preimage regions"):
        validate_edit(before, after, c)


def test_explicit_broad_refactor_can_be_authorized_but_requires_reason():
    before = "a\nb\nc\nd\n"
    after = "replacement\n"
    with pytest.raises(EditPreservationError, match="requires an explicit reason"):
        contract_for(before, ranges=(), allow_full_file_replacement=True)
    c = contract_for(
        before,
        ranges=(),
        allow_full_file_replacement=True,
        full_file_replacement_reason="owner-approved mechanical rewrite with independent regression suite",
    )
    assert validate_edit(before, after, c)["full_file_replacement_authorized"] is True


def test_changed_file_set_must_match_declared_scope_exactly():
    with pytest.raises(EditPreservationError, match="changed-file set mismatch"):
        validate_changed_path_set(
            ["tools/grid10_fabric.py", "unrelated.py"],
            ["tools/grid10_fabric.py"],
        )


def test_path_traversal_and_absolute_paths_fail_closed():
    before = "a\nb\n"
    for bad in ("../escape.py", "/abs/path.py", "dir/../escape.py", "dir\\file.py"):
        with pytest.raises(EditPreservationError):
            contract_for(before, path=bad)
