from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.trigger1_atomic_lease_gate import EXPECTED_EXPERIMENT, validate_claim

RID = "rid_" + "a" * 64
HEAD = "b" * 40
FUSED = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1"
SUPERSEDED = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"


def make_claim(experiment_name: str) -> dict:
    return {
        "schema": "clay-go-experiment-claim/v1",
        "trigger_key": RID,
        "trigger": "go",
        "experiment_name": experiment_name,
        "claimant_organ": "unit-test-organ",
        "claimed_at": "2026-08-24T16:50:00Z",
        "observed_canonical_main": HEAD,
        "intervention_contract": {
            "mode": "bounded_intermediate_contrastive",
            "result_schema": FUSED,
        },
        "status": "CLAIMED",
    }


class Trigger1FusedLeaseIdentityTests(unittest.TestCase):
    def test_gate_constant_tracks_effective_fused_experiment(self):
        self.assertEqual(FUSED, EXPECTED_EXPERIMENT)
        self.assertNotEqual(SUPERSEDED, EXPECTED_EXPERIMENT)

    def test_superseded_midlayer_claim_cannot_authorize_fused_intervention(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / f"{RID}.json").write_text(
                json.dumps(make_claim(SUPERSEDED)) + "\n",
                encoding="utf-8",
            )
            result = validate_claim(
                issue_body=f"trigger_key: {RID}\n",
                claims_root=root,
            )
        self.assertFalse(result["pass"])
        self.assertEqual("CLAIM_EXPERIMENT_MISMATCH", result["reason"])

    def test_fused_claim_is_admitted_at_identity_layer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / f"{RID}.json").write_text(
                json.dumps(make_claim(FUSED)) + "\n",
                encoding="utf-8",
            )
            result = validate_claim(
                issue_body=f"trigger_key: {RID}\n",
                claims_root=root,
            )
        self.assertTrue(result["pass"])
        self.assertEqual(FUSED, result["experiment_name"])


if __name__ == "__main__":
    unittest.main()
