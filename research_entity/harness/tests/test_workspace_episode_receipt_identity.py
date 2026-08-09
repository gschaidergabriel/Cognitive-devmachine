import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
from workspace_episode import BasisWitness, ReceiverPolicy, WorkspaceCandidate, WorkspaceIntervention, run_workspace_episode

class ReceiptIdentityT(unittest.TestCase):
    def run_ep(self, **kw):
        args = dict(
            episode_id="identity-ep",
            witness=BasisWitness(3, "sem", "ver", "trace", "contract-v1"),
            candidates=[WorkspaceCandidate("c", .8, {"x": 1}, 3)],
            receivers=[ReceiverPolicy("memory"), ReceiverPolicy("planner")],
        )
        args.update(kw)
        return run_workspace_episode(**args)

    def test_semantic_contract_and_input_identities_are_bound(self):
        a = self.run_ep()
        b = self.run_ep(intervention=WorkspaceIntervention(intervention_id="changed", disable_reentry=True))
        self.assertEqual(a["semantic_contract_hash"], "contract-v1")
        self.assertEqual(len(a["input_identity"]["candidate_set_hash"]), 64)
        self.assertEqual(len(a["input_identity"]["receiver_policy_hash"]), 64)
        self.assertNotEqual(a["input_identity"]["intervention_hash"], b["input_identity"]["intervention_hash"])
        self.assertNotEqual(a["receipt_root_hash"], b["receipt_root_hash"])

    def test_default_contract_keeps_existing_callers_valid(self):
        w = BasisWitness(3, "sem", "ver", "trace")
        r = run_workspace_episode(
            episode_id="compat", witness=w,
            candidates=[WorkspaceCandidate("c", .8, {}, 3)],
            receivers=[ReceiverPolicy("r")],
        )
        self.assertEqual(r["basis"], {"basis_epoch":3,"semantic_state_hash":"sem","state_version_hash":"ver","trace_root_hash":"trace"})
        self.assertEqual(r["semantic_contract_hash"], "frank.workspace-contract.v0")

if __name__ == "__main__": unittest.main(verbosity=2)
