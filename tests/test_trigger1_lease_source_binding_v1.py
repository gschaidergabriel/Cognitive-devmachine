from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "tools" / "trigger1_lease_source_binding_v1.py"
SOURCE_PATH = ROOT / "tools" / "git_source_identity_v1.py"
GATE_PATH = ROOT / "tools" / "trigger1_atomic_lease_gate.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helper = load(HELPER_PATH, "trigger1_lease_source_binding_v1_test")
source_mod = load(SOURCE_PATH, "git_source_identity_v1_test")
gate = load(GATE_PATH, "trigger1_atomic_lease_gate_test")


class Trigger1LeaseSourceBindingTests(unittest.TestCase):
    def make_repo_and_claim(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name)
        root = base / "repo"
        claims = base / "claims"
        root.mkdir()
        claims.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Clay Test"], check=True)
        (root / "tracked.txt").write_text("alpha\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        tree = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"], text=True).strip()

        key = "rid_" + "a" * 64
        claim = {
            "schema": gate.CLAIM_SCHEMA,
            "trigger_key": key,
            "trigger": "go",
            "experiment_name": gate.EXPECTED_EXPERIMENT,
            "status": "CLAIMED",
            "claimant_organ": "unit-test-organ",
            "claimed_at": "2026-08-24T16:34:00Z",
            "observed_canonical_main": head,
            "intervention_contract": {"kind": "unit-test-no-intervention"},
        }
        claim_path = claims / f"{key}.json"
        raw = (json.dumps(claim, indent=2, sort_keys=True) + "\n").encode()
        claim_path.write_bytes(raw)
        return root, claims, key, hashlib.sha256(raw).hexdigest(), head, tree

    def test_exact_claim_workflow_and_execution_source_chain_passes(self):
        root, claims, key, claim_sha, head, tree = self.make_repo_and_claim()
        source = source_mod.source_identity(root)
        got = helper.validate_binding(
            repo=root,
            source_identity=source,
            claims_root=claims,
            trigger_key=key,
            expected_claim_sha256=claim_sha,
            expected_source_head=head,
            expected_source_tree=tree,
        )
        self.assertTrue(got["pass"], got)
        self.assertTrue(all(got["checks"].values()))

    def test_workflow_source_head_mismatch_fails_closed(self):
        root, claims, key, claim_sha, _head, tree = self.make_repo_and_claim()
        source = source_mod.source_identity(root)
        got = helper.validate_binding(
            repo=root,
            source_identity=source,
            claims_root=claims,
            trigger_key=key,
            expected_claim_sha256=claim_sha,
            expected_source_head="b" * 40,
            expected_source_tree=tree,
        )
        self.assertFalse(got["pass"])
        self.assertFalse(got["checks"]["workflow_source_head_matches"])

    def test_claim_sha_mismatch_fails_closed(self):
        root, claims, key, _claim_sha, head, tree = self.make_repo_and_claim()
        source = source_mod.source_identity(root)
        got = helper.validate_binding(
            repo=root,
            source_identity=source,
            claims_root=claims,
            trigger_key=key,
            expected_claim_sha256="0" * 64,
            expected_source_head=head,
            expected_source_tree=tree,
        )
        self.assertFalse(got["pass"])
        self.assertFalse(got["checks"]["workflow_claim_sha_matches"])

    def test_repository_change_after_pre_identity_fails_remeasurement(self):
        root, claims, key, claim_sha, head, tree = self.make_repo_and_claim()
        source = source_mod.source_identity(root)
        (root / "tracked.txt").write_text("mutated\n", encoding="utf-8")
        got = helper.validate_binding(
            repo=root,
            source_identity=source,
            claims_root=claims,
            trigger_key=key,
            expected_claim_sha256=claim_sha,
            expected_source_head=head,
            expected_source_tree=tree,
        )
        self.assertFalse(got["pass"])
        self.assertFalse(got["checks"]["source_identity_matches_current_repo"])

    def test_existing_result_rejects_reuse_of_claim(self):
        root, claims, key, claim_sha, head, tree = self.make_repo_and_claim()
        source = source_mod.source_identity(root)
        (claims / f"{key}.result.json").write_text("{}\n", encoding="utf-8")
        got = helper.validate_binding(
            repo=root,
            source_identity=source,
            claims_root=claims,
            trigger_key=key,
            expected_claim_sha256=claim_sha,
            expected_source_head=head,
            expected_source_tree=tree,
        )
        self.assertFalse(got["pass"])
        self.assertIn("UNUSUAL_EXPERIMENT_RESULT_ALREADY_EXISTS", got["reason"])


if __name__ == "__main__":
    unittest.main()
