import importlib.util
from pathlib import Path
import stat
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "frankenstein_exact_patch_v1.py"
spec = importlib.util.spec_from_file_location("frankenstein_exact_patch_v1", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def _patch(path: str, original: str, edits: list[dict[str, str]]) -> dict:
    return {
        "schema": mod.SCHEMA,
        "path": path,
        "preimage_sha256": mod.sha256_text(original),
        "edits": edits,
    }


def test_exact_splice_preserves_all_undeclared_regions(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "tools" / "grid10_fabric.py"
    target.parent.mkdir(parents=True)
    prefix = "# unrelated prefix\n" * 20
    middle = "def target():\n    return 1\n"
    suffix = "# unrelated suffix\n" * 20
    original = prefix + middle + suffix
    target.write_text(original, encoding="utf-8")

    plan = mod.apply_exact_patch(repo, _patch(
        "tools/grid10_fabric.py",
        original,
        [{"find": middle, "replace": "def target():\n    return 2\n"}],
    ))

    final = target.read_text(encoding="utf-8")
    assert final.startswith(prefix)
    assert final.endswith(suffix)
    assert "return 2" in final
    assert plan.preimage_sha256 == mod.sha256_text(original)
    assert plan.postimage_sha256 == mod.sha256_text(final)


def test_preimage_hash_mismatch_fails_without_mutation(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "x.py"
    repo.mkdir()
    original = "a = 1\n" * 100
    target.write_text(original, encoding="utf-8")
    patch = _patch("x.py", original, [{"find": "a = 1\n", "replace": "a = 2\n"}])
    patch["preimage_sha256"] = "0" * 64

    try:
        mod.apply_exact_patch(repo, patch)
        assert False, "hash mismatch must fail"
    except mod.ExactPatchError as exc:
        assert "PREIMAGE_SHA256_MISMATCH" in str(exc)
    assert target.read_text(encoding="utf-8") == original


def test_ambiguous_find_fails_closed(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "x.py"
    repo.mkdir()
    original = "same\nsame\n" + ("padding\n" * 40)
    target.write_text(original, encoding="utf-8")

    try:
        mod.plan_exact_patch(repo, _patch("x.py", original, [{"find": "same\n", "replace": "changed\n"}]))
        assert False, "ambiguous find must fail"
    except mod.ExactPatchError as exc:
        assert "FIND_NOT_UNIQUE:2" in str(exc)


def test_overlapping_declared_spans_fail_closed(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "x.py"
    repo.mkdir()
    original = "abcdefghij" + ("z" * 100)
    target.write_text(original, encoding="utf-8")
    patch = _patch("x.py", original, [
        {"find": "abcdef", "replace": "A"},
        {"find": "defgh", "replace": "B"},
    ])

    try:
        mod.plan_exact_patch(repo, patch)
        assert False, "overlapping spans must fail"
    except mod.ExactPatchError as exc:
        assert "SPANS_OVERLAP" in str(exc)


def test_large_automatic_edit_fails_even_when_exact(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "x.py"
    repo.mkdir()
    removable = "important = 1\n" * 40
    rest = "keep = 2\n" * 40
    original = removable + rest
    target.write_text(original, encoding="utf-8")
    patch = _patch("x.py", original, [{"find": removable, "replace": "tiny = 3\n"}])

    try:
        mod.plan_exact_patch(repo, patch)
        assert False, "automatic patch touching >35% must fail"
    except mod.ExactPatchError as exc:
        assert "TOUCHED_FRACTION_EXCEEDED" in str(exc)
    assert target.read_text(encoding="utf-8") == original


def test_outside_repo_path_fails_closed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n", encoding="utf-8")
    patch = {
        "schema": mod.SCHEMA,
        "path": "../outside.py",
        "preimage_sha256": mod.sha256_text(outside.read_text(encoding="utf-8")),
        "edits": [{"find": "secret = 1\n", "replace": "secret = 0\n"}],
    }
    try:
        mod.plan_exact_patch(repo, patch)
        assert False, "outside path must fail"
    except mod.ExactPatchError as exc:
        assert "PATH_OUTSIDE_REPO" in str(exc)
    assert outside.read_text(encoding="utf-8") == "secret = 1\n"


def test_symlink_target_fails_closed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n", encoding="utf-8")
    link = repo / "x.py"
    link.symlink_to(outside)
    patch = {
        "schema": mod.SCHEMA,
        "path": "x.py",
        "preimage_sha256": mod.sha256_text(outside.read_text(encoding="utf-8")),
        "edits": [{"find": "secret = 1\n", "replace": "secret = 0\n"}],
    }
    try:
        mod.plan_exact_patch(repo, patch)
        assert False, "symlink target must fail"
    except mod.ExactPatchError as exc:
        assert "SYMLINK_FORBIDDEN" in str(exc)


def test_atomic_apply_preserves_executable_mode(tmp_path):
    repo = tmp_path / "repo"
    target = repo / "script.py"
    repo.mkdir()
    original = "#!/usr/bin/env python3\n" + ("x = 1\n" * 50)
    target.write_text(original, encoding="utf-8")
    target.chmod(0o755)
    original = original.replace("x = 1\n", "x = 1  # unique\n", 1)
    target.write_text(original, encoding="utf-8")
    target.chmod(0o755)
    patch = _patch("script.py", original, [{"find": "x = 1  # unique\n", "replace": "x = 2  # unique\n"}])

    mod.apply_exact_patch(repo, patch)
    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert "x = 2  # unique" in target.read_text(encoding="utf-8")


def test_new_file_is_not_silently_created_by_existing_file_patch_lane(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    patch = {
        "schema": mod.SCHEMA,
        "path": "new.py",
        "preimage_sha256": mod.sha256_text(""),
        "edits": [{"find": "x", "replace": "y"}],
    }
    try:
        mod.plan_exact_patch(repo, patch)
        assert False, "existing-file patch lane must not create files"
    except mod.ExactPatchError as exc:
        assert "TARGET_MUST_BE_EXISTING_FILE" in str(exc)
    assert not (repo / "new.py").exists()
