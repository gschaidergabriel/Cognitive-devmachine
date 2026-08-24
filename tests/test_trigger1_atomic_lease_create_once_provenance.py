from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.trigger1_atomic_lease_gate import EXPECTED_EXPERIMENT, validate_claim

RID = "rid_" + "c" * 64
HEAD = "d" * 40


def claim() -> dict:
    return {
        "schema": "clay-go-experiment-claim/v1",
        "trigger_key": RID,
        "trigger": "go",
        "experiment_name": EXPECTED_EXPERIMENT,
        "claimant_organ": "gpt56sol",
        "claimed_at": "2026-08-24T16:40:00Z",
        "observed_canonical_main": HEAD,
        "intervention_contract": {"mode": "bounded_midlayer_causal"},
        "status": "CLAIMED",
    }


class Trigger1AtomicLeaseCreateOnceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.claims = self.repo / "research_entity/continuity/go_experiment_claims"
        self.claims.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Clay Test"], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    @property
    def path(self) -> Path:
        return self.claims / f"{RID}.json"

    def write_claim(self, obj: dict) -> None:
        self.path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")

    def commit_all(self, message: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", message], check=True)

    def gate(self):
        return validate_claim(
            issue_body=f"trigger_key: {RID}\n",
            claims_root=self.claims,
            require_create_once_provenance=True,
        )

    def test_single_add_unmodified_claim_passes(self):
        self.write_claim(claim())
        self.commit_all("claim once")
        result = self.gate()
        self.assertTrue(result["pass"])
        self.assertTrue(result["claim_create_once_provenance_verified"])
        self.assertEqual(result["claim_touch_commit_count"], 1)
        self.assertTrue(result["claim_create_commit"])
        self.assertTrue(result["claim_blob_oid"])

    def test_committed_rewrite_fails_closed(self):
        self.write_claim(claim())
        self.commit_all("claim once")
        changed = claim()
        changed["note"] = "post-create mutation"
        self.write_claim(changed)
        self.commit_all("mutate claim")
        result = self.gate()
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CLAIM_NOT_CREATE_ONCE")

    def test_dirty_worktree_rewrite_fails_closed(self):
        self.write_claim(claim())
        self.commit_all("claim once")
        changed = claim()
        changed["note"] = "uncommitted mutation"
        self.write_claim(changed)
        result = self.gate()
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CLAIM_WORKTREE_DIFFERS_FROM_TRACKED_CREATE")


if __name__ == "__main__":
    unittest.main()
