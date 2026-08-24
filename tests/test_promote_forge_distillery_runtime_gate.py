#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import promote_forge_distillery_runtime_gate as p

SOURCE = "a" * 40
TREE = "b" * 40
RUN = "12345"


def git(root: Path, *args: str) -> None:
    cp = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if cp.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {cp.stderr}")


def base_result(**overrides) -> dict:
    obj = {
        "github_run_id": RUN,
        "github_event_name": "pull_request",
        "source_selection": p.CANONICAL_SOURCE_SELECTION,
        "execution_source_sha": SOURCE,
        "source_tree": TREE,
        "execution_source_tree": TREE,
    }
    obj.update(overrides)
    return obj


class RepositoryBoundForgeGateReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Clay Test")
        git(self.root, "config", "user.email", "clay-test@localhost")
        self.results = self.root / p.CANONICAL_RESULTS_REL
        self.results.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def commit_receipt(self, obj: dict | None = None, filename: str = RUN + ".json") -> Path:
        path = self.results / filename
        path.write_text(json.dumps(obj or base_result(), sort_keys=True) + "\n", encoding="utf-8")
        git(self.root, "add", path.relative_to(self.root).as_posix())
        git(self.root, "commit", "-q", "-m", "runtime receipt")
        return path

    def reset_repo(self) -> None:
        self.tmp.cleanup()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Clay Test")
        git(self.root, "config", "user.email", "clay-test@localhost")
        self.results = self.root / p.CANONICAL_RESULTS_REL
        self.results.mkdir(parents=True)

    def test_accepts_clean_tracked_canonical_receipt(self):
        path = self.commit_receipt()
        result, raw = p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)
        self.assertEqual(result["github_run_id"], RUN)
        self.assertEqual(result["execution_source_sha"], SOURCE)
        self.assertEqual(raw, path.read_bytes())

    def test_rejects_copy_outside_canonical_results_root(self):
        canonical = self.commit_receipt()
        copy = self.root / "copy.json"
        copy.write_bytes(canonical.read_bytes())
        with self.assertRaisesRegex(p.PromotionError, "GATE_RECEIPT_OUTSIDE_CANONICAL_RESULTS_ROOT"):
            p.load_repository_bound_gate_receipt(copy, SOURCE, root=self.root)

    def test_rejects_untracked_or_dirty_receipt(self):
        untracked = self.results / "67890.json"
        untracked.write_text(json.dumps(base_result(github_run_id="67890")) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(p.PromotionError, "GATE_RECEIPT_NOT_TRACKED"):
            p.load_repository_bound_gate_receipt(untracked, SOURCE, root=self.root)

        path = self.commit_receipt()
        path.write_text(json.dumps(base_result(extra="mutation")) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(p.PromotionError, "GATE_RECEIPT_DIRTY"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)

    def test_rejects_run_id_metadata_mismatch(self):
        path = self.commit_receipt(base_result(github_run_id="99999"))
        with self.assertRaisesRegex(p.PromotionError, "GATE_RUN_ID_PATH_MISMATCH"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)

    def test_rejects_wrong_execution_source_or_source_selection(self):
        path = self.commit_receipt(base_result(execution_source_sha="c" * 40))
        with self.assertRaisesRegex(p.PromotionError, "EXECUTION_SOURCE_SHA_MISSING_OR_MISMATCH"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)

        self.reset_repo()
        path = self.commit_receipt(base_result(source_selection="CALLER_SELECTED_FILE"))
        with self.assertRaisesRegex(p.PromotionError, "GATE_SOURCE_SELECTION_INVALID"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)

    def test_rejects_tree_mismatch_or_invalid_event(self):
        path = self.commit_receipt(base_result(execution_source_tree="c" * 40))
        with self.assertRaisesRegex(p.PromotionError, "EXECUTION_SOURCE_TREE_MISMATCH"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)

        self.reset_repo()
        path = self.commit_receipt(base_result(github_event_name="repository_dispatch"))
        with self.assertRaisesRegex(p.PromotionError, "GATE_WORKFLOW_EVENT_INVALID"):
            p.load_repository_bound_gate_receipt(path, SOURCE, root=self.root)


if __name__ == "__main__":
    unittest.main()
