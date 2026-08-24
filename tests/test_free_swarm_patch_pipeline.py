from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_patch_pipeline as pipe  # noqa: E402


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.strip()


class TwoStagePatchPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = tempfile.TemporaryDirectory()
        self.tmp = Path(self.ctx.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "patch-pipeline@example.invalid")
        git(self.repo, "config", "user.name", "Patch Pipeline Test")
        (self.repo / "sample.py").write_text(
            "value = 1\nname = 'old'\nflag = False\n", encoding="utf-8"
        )
        git(self.repo, "add", "sample.py")
        git(self.repo, "commit", "-q", "-m", "source")
        self.source_head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.ctx.cleanup()

    def test_rehydrate_binds_exact_commit_blob_and_digest(self) -> None:
        result = pipe.rehydrate_targets(
            self.repo, self.source_head, ["sample.py"], per_file_chars=5000
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["source_head"], self.source_head)
        row = result["files"][0]
        self.assertEqual(row["path"], "sample.py")
        self.assertRegex(row["git_blob"], r"^[0-9a-f]{40,64}$")
        self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("value = 1", row["content"])
        self.assertFalse(row["truncated"])

    def test_rehydrate_rejects_path_traversal(self) -> None:
        result = pipe.rehydrate_targets(
            self.repo, self.source_head, ["../secret.txt"]
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "UNSAFE_TARGET_PATH")

    def test_valid_patch_passes_without_repair(self) -> None:
        patch = (
            "diff --git a/sample.py b/sample.py\n"
            "--- a/sample.py\n"
            "+++ b/sample.py\n"
            "@@ -1,3 +1,3 @@\n"
            "-value = 1\n"
            "+value = 2\n"
            " name = 'old'\n"
            " flag = False\n"
        )
        result = pipe.normalize_patch_against_source(
            self.repo, self.source_head, patch, ["sample.py"]
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["repair_mode"], "NONE")
        self.assertEqual(result["patch"], patch)

    def test_bad_hunk_counts_are_recounted_then_standard_rechecked(self) -> None:
        patch = (
            "diff --git a/sample.py b/sample.py\n"
            "--- a/sample.py\n"
            "+++ b/sample.py\n"
            "@@ -1,9 +1,9 @@\n"
            "-value = 1\n"
            "+value = 2\n"
            " name = 'old'\n"
            " flag = False\n"
        )
        result = pipe.normalize_patch_against_source(
            self.repo, self.source_head, patch, ["sample.py"]
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["repair_mode"], "RECOUNT_NORMALIZED")
        self.assertIn("@@ -1,3 +1,3 @@", result["patch"])
        self.assertNotIn("@@ -1,9 +1,9 @@", result["patch"])

    def test_context_mismatch_is_not_fuzzy_repaired(self) -> None:
        patch = (
            "diff --git a/sample.py b/sample.py\n"
            "--- a/sample.py\n"
            "+++ b/sample.py\n"
            "@@ -1,3 +1,3 @@\n"
            "-value = 999\n"
            "+value = 2\n"
            " name = 'old'\n"
            " flag = False\n"
        )
        result = pipe.normalize_patch_against_source(
            self.repo, self.source_head, patch, ["sample.py"]
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "PATCH_APPLY_REJECTED")
        self.assertEqual(result["repair_mode"], "NONE")

    def test_patch_target_set_must_equal_stage1_targets(self) -> None:
        patch = (
            "diff --git a/sample.py b/sample.py\n"
            "--- a/sample.py\n"
            "+++ b/sample.py\n"
            "@@ -1 +1 @@\n"
            "-value = 1\n"
            "+value = 2\n"
        )
        result = pipe.normalize_patch_against_source(
            self.repo, self.source_head, patch, ["sample.py", "other.py"]
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "PATCH_TARGET_SET_MISMATCH")

    def test_controller_can_force_non_apply_clean_delta_not_ready(self) -> None:
        text = (
            "DEUTSCHE_ZUSAMMENFASSUNG\n"
            'ARCHITECTURE_DELTA_JSON={"delta_id":"d","target_files":["sample.py"],'
            '"patch_unified_diff":"bad","test_commands":["true"],'
            '"falsifier":"fails","ready_for_forge":true}\n'
            'OPEN_RESEARCH_QUESTIONS_JSON=[]\n'
        )
        obj = pipe.architecture_delta(text)
        self.assertIsInstance(obj, dict)
        assert obj is not None
        obj["ready_for_forge"] = False
        obj["patch_pipeline_stage"] = "APPLY_CHECK_BLOCKED"
        updated = pipe.canonicalize_architecture_delta(text, obj)
        reparsed = pipe.architecture_delta(updated)
        self.assertIsInstance(reparsed, dict)
        assert reparsed is not None
        self.assertFalse(reparsed["ready_for_forge"])
        self.assertEqual(reparsed["patch_pipeline_stage"], "APPLY_CHECK_BLOCKED")

    def test_stage2_prompt_contains_exact_binding_and_forces_fail_closed_default(self) -> None:
        proposal = {
            "delta_id": "d",
            "hypothesis": "h",
            "target_files": ["sample.py"],
            "test_commands": ["true"],
            "falsifier": "f",
            "patch_unified_diff": "invented",
            "ready_for_forge": True,
        }
        binding = pipe.rehydrate_targets(self.repo, self.source_head, ["sample.py"])
        prompt = pipe.stage2_prompt("PROTOCOL", proposal, binding)
        self.assertIn(self.source_head, prompt)
        self.assertIn(binding["files"][0]["git_blob"], prompt)
        self.assertIn("value = 1", prompt)
        self.assertIn('"patch_unified_diff":""', prompt)
        self.assertIn('"ready_for_forge":false', prompt)


if __name__ == "__main__":
    unittest.main()
