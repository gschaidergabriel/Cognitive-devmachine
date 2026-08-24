from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_local as local


class DistilleryLocalProvisionalFence871Tests(unittest.TestCase):
    def test_high_scoring_correlated_local_panel_remains_noncanonical(self):
        votes=[
            ("local_reviewer_logic","local",local.LOCAL_LOGICAL_ID,0.96,0.95,0.92,0.90,0),
            ("local_reviewer_grf","local",local.LOCAL_LOGICAL_ID,0.95,0.94,0.91,0.89,0),
            ("local_reviewer_falsifier","local",local.LOCAL_LOGICAL_ID,0.94,0.93,0.90,0.88,0),
        ]
        con=mock.MagicMock()
        con.execute.return_value.fetchall.return_value=votes
        reviewers=[(row[0],row[1],row[2]) for row in votes]
        with mock.patch.object(local,"_PREV_REVIEW",return_value=(False,{})), \
             mock.patch.object(local.d,"bump") as bump, \
             mock.patch.object(local.d,"emit") as emit:
            accepted,agg=local.review_candidate(con,"c-local",reviewers)
        self.assertFalse(accepted)
        self.assertEqual(agg["panel_class"],"PROVISIONAL_LOCAL_CORRELATED")
        self.assertEqual(agg["independence_class"],"CORRELATED_SAME_MODEL_MULTI_PASS")
        self.assertFalse(agg["canonical_dataset_commit_allowed"])
        con.execute.assert_any_call("UPDATE candidates SET status='PROVISIONAL_ACCEPTED' WHERE id=?",("c-local",))
        bump.assert_any_call(con,"provisional_local_accept",1)
        emit.assert_called_once()


if __name__=="__main__":
    unittest.main()
