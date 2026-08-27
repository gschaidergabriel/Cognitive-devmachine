import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "preimage_bound_edit_guard_v1.py"
spec = importlib.util.spec_from_file_location("edit_guard", MODULE)
edit_guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(edit_guard)


def H(text: str) -> str:
    return edit_guard.sha256_text(text)


def base_lines(n=10):
    return "".join(f"line-{i}\n" for i in range(1, n + 1))


def test_narrow_additive_edit_inside_declared_scope_passes():
    old = base_lines()
    new = old.replace("line-5\n", "line-5\ninserted\n")
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=new,
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(5, 5)],
    )
    assert d.accepted, d


def test_stale_preimage_fails_closed():
    old = base_lines()
    current = old + "concurrent-change\n"
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        current_text=current,
        proposed_text=old.replace("line-5", "changed-5"),
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(5, 5)],
    )
    assert not d.accepted
    assert d.reason == "STALE_PREIMAGE"


def test_change_outside_declared_scope_rejected_even_if_feature_change_is_valid():
    old = base_lines()
    new = old.replace("line-5", "feature-ok").replace("line-9", "silent-unrelated-delete")
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=new,
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(5, 5)],
    )
    assert not d.accepted
    assert d.reason == "CHANGE_OUTSIDE_DECLARED_SCOPE"


def test_large_deletion_requires_explicit_broad_deletion():
    old = base_lines(20)
    new = "".join(f"line-{i}\n" for i in range(1, 6))
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=new,
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(6, 20)],
        max_undeclared_deletion_fraction=0.35,
    )
    assert not d.accepted
    assert d.reason == "BROAD_DELETION_NOT_EXPLICITLY_AUTHORIZED"


def test_broad_deletion_can_be_explicit_but_still_must_match_declared_scope():
    old = base_lines(20)
    new = "".join(f"line-{i}\n" for i in range(1, 6))
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=new,
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(6, 20)],
        explicit_broad_deletion=True,
    )
    assert d.accepted, d


def test_path_traversal_rejected():
    old = base_lines()
    d = edit_guard.evaluate_edit(
        path="../outside.py",
        preimage_text=old,
        proposed_text=old.replace("line-5", "changed"),
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[(5, 5)],
    )
    assert not d.accepted
    assert d.reason == "UNSAFE_PATH"


def test_wrong_expected_hash_rejected():
    old = base_lines()
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=old.replace("line-5", "changed"),
        expected_preimage_sha256="0" * 64,
        allowed_old_line_ranges=[(5, 5)],
    )
    assert not d.accepted
    assert d.reason == "EXPECTED_PREIMAGE_HASH_MISMATCH"


def test_no_declared_scope_rejected():
    old = base_lines()
    d = edit_guard.evaluate_edit(
        path="tools/example.py",
        preimage_text=old,
        proposed_text=old.replace("line-5", "changed"),
        expected_preimage_sha256=H(old),
        allowed_old_line_ranges=[],
    )
    assert not d.accepted
    assert d.reason == "NO_DECLARED_EDIT_SCOPE"
