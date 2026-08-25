#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

from zero_entityos_variable_grid_fixture_v1 import RuntimeConfig, VariableGridFixture

CENSUS = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
ABI = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class VariableGridFixtureTests(unittest.TestCase):
    def setUp(self):
        self.census = load(CENSUS)
        self.abi = load(ABI)

    def run_semantics(self, n: int):
        rt = VariableGridFixture(self.census, self.abi, RuntimeConfig(requested_n=n, available_n=n))
        admission = rt.admit_task({"task": "fixture", "goal": "prove topology invariance"})
        rt.seed_canonical_state("project/fact", {"value": 7, "status": "CANONICAL_TEST_FIXTURE"})
        for process_id in ("ZECP03", "ZECP06", "ZECP08", "ZECP09", "ZECP10", "ZECP12", "ZECP18", "ZECP19"):
            rt.enqueue(admission, process_id, {"state_ref": "project/fact", "process": process_id})
        results = rt.execute_ready()
        fp = rt.semantic_fingerprint()
        work_process_pairs = sorted((r["semantic"]["work_id"], r["semantic"]["process_id"]) for r in results)
        executor_ids = sorted({r["executor_id"] for r in results})
        return rt, admission, fp, work_process_pairs, executor_ids

    def test_d1_n_invariance(self):
        runs = [self.run_semantics(n) for n in (1, 10, 20)]
        try:
            fingerprints = {r[2] for r in runs}
            pairs = {tuple(r[3]) for r in runs}
            self.assertEqual(1, len(fingerprints))
            self.assertEqual(1, len(pairs))
            self.assertEqual(["fixture-executor-0000"], runs[0][4])
            self.assertGreaterEqual(len(runs[1][4]), 2)
            self.assertGreaterEqual(len(runs[2][4]), 2)
        finally:
            for r in runs:
                r[0].close()

    def test_d2_db_fact_fence(self):
        rt, admission, *_ = self.run_semantics(10)
        try:
            work = rt.enqueue(admission, "ZECP15", {"proposal": "candidate"})
            rt.execute_ready()
            rt.propose_db_write(work["work_id"], "project/new_fact", {"value": 99})
            self.assertIsNone(rt.canonical_state("project/new_fact"))
            self.assertEqual(1, rt.count("db_write_proposals"))
        finally:
            rt.close()

    def test_d3_effect_fence(self):
        rt, admission, *_ = self.run_semantics(10)
        try:
            work = rt.enqueue(admission, "ZECP16", {"intent": "candidate effect"})
            rt.execute_ready()
            rt.propose_effect(work["work_id"], {"kind": "fixture-noop"})
            self.assertEqual(1, rt.count("effect_request_candidates"))
            self.assertEqual(0, rt.count("effect_journal"))
        finally:
            rt.close()

    def test_d4_claude_reentry_binding_stub_only(self):
        rt, admission, *_ = self.run_semantics(10)
        try:
            work = rt.enqueue(admission, "ZECP13", {"handoff": "fixture"})
            rt.execute_ready()
            roundtrip = rt.stub_claude_roundtrip(admission, work["work_id"], 7, ["project/fact"])
            self.assertTrue(roundtrip["result"]["stubbed"])
            self.assertEqual(0, roundtrip["result"]["runtime_credit"])
            self.assertEqual(admission["causal_event_id"], roundtrip["reentry"]["causal_event_id"])
            self.assertEqual(7, roundtrip["reentry"]["from_workspace_epoch"])
            self.assertEqual(8, roundtrip["reentry"]["to_workspace_epoch"])
            self.assertEqual("UNKNOWN", roundtrip["reentry"]["observed_downstream_change"])
            stored = rt.con.execute(
                "SELECT observed_downstream_change FROM workspace_reentry"
            ).fetchone()[0]
            self.assertEqual("UNKNOWN", stored)
            self.assertEqual(1, rt.count("workspace_reentry"))
        finally:
            rt.close()

    def test_d5_jspace_credit_not_minted_by_reentry(self):
        rt, admission, *_ = self.run_semantics(10)
        try:
            rt.enqueue(admission, "ZECP20", {"probe": "fixture"})
            rt.execute_ready()
            self.assertEqual(0, self.abi["credit_boundary"]["global_jspace_causal_runtime"])
            self.assertEqual(0, self.census["credit_boundary"]["global_jspace_causal_runtime"])
        finally:
            rt.close()


if __name__ == "__main__":
    unittest.main()
