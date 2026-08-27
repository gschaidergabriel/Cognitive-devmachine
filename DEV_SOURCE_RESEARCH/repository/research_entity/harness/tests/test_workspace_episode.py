import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))

from workspace_episode import (
    AuthorityViolation,
    BasisWitness,
    ReceiverPolicy,
    WorkspaceCandidate,
    WorkspaceError,
    WorkspaceIntervention,
    run_workspace_episode,
)


class T(unittest.TestCase):
    def witness(self):
        return BasisWitness(7, 'sem-7', 'ver-7', 'trace-7')

    def candidates(self):
        return [
            WorkspaceCandidate('c-high', .8, {'intent': 'inspect'}, 7, 'assembly'),
            WorkspaceCandidate('c-low', .4, {'intent': 'wait'}, 7, 'assembly'),
        ]

    def receivers(self):
        return [ReceiverPolicy('memory'), ReceiverPolicy('planner')]

    def episode(self, **kw):
        x = dict(
            episode_id='ep-1', witness=self.witness(), candidates=self.candidates(),
            receivers=self.receivers(), ignition_threshold=.55,
        )
        x.update(kw)
        return run_workspace_episode(**x)

    def test_deterministic(self):
        a = self.episode(); b = self.episode()
        self.assertEqual(a['episode_hash'], b['episode_hash'])
        self.assertEqual(a['receipt_root_hash'], b['receipt_root_hash'])

    def test_stage_chain_is_distinct(self):
        r = self.episode()
        stages = [x['stage'] for x in r['receipts']]
        for name in ('competition','ignition','broadcast','receiver_delivery','receiver_reconstruction','receiver_uptake','receiver_causal_use','outcome','reentry'):
            self.assertIn(name, stages)
        self.assertEqual(r['integration_readout']['causal_use_fraction'], 1.0)
        self.assertTrue(r['reentry']['truthful'])

    def test_low_score_gwt_does_not_ignite(self):
        r = self.episode(candidates=[WorkspaceCandidate('c', .2, {'x': 1}, 7)])
        self.assertFalse(r['ignited'])
        self.assertEqual(r['integration_readout']['receiver_coverage'], 0.0)
        self.assertIsNone(r['reentry'])

    def test_event_bus_is_matched_admission_null(self):
        c = [WorkspaceCandidate('c', .2, {'x': 1}, 7)]
        g = self.episode(candidates=c, admission_mode='GWT')
        b = self.episode(candidates=c, admission_mode='EVENT_BUS')
        self.assertFalse(g['ignited'])
        self.assertTrue(b['ignited'])
        self.assertEqual(b['winner_id'], g['winner_id'])
        self.assertEqual(b['integration_readout']['causal_use_fraction'], 1.0)

    def test_delivery_reconstruction_uptake_use_are_not_collapsed(self):
        receivers = [
            ReceiverPolicy('a', deliver=True, reconstruct=False, uptake=True, causal_use=True),
            ReceiverPolicy('b', deliver=True, reconstruct=True, uptake=False, causal_use=True),
            ReceiverPolicy('c', deliver=True, reconstruct=True, uptake=True, causal_use=False),
        ]
        r = self.episode(receivers=receivers)
        s = {x['receiver_id']: x for x in r['receiver_states']}
        self.assertTrue(s['a']['delivered']); self.assertFalse(s['a']['reconstructed']); self.assertFalse(s['a']['uptake']); self.assertFalse(s['a']['causal_use'])
        self.assertTrue(s['b']['reconstructed']); self.assertFalse(s['b']['uptake']); self.assertFalse(s['b']['causal_use'])
        self.assertTrue(s['c']['uptake']); self.assertFalse(s['c']['causal_use'])

    def test_receiver_lesion_and_corruption(self):
        iv = WorkspaceIntervention(intervention_id='iv', lesion_receivers=frozenset({'memory'}), corrupt_reconstruction=frozenset({'planner'}))
        r = self.episode(intervention=iv)
        s = {x['receiver_id']: x for x in r['receiver_states']}
        self.assertFalse(s['memory']['delivered'])
        self.assertTrue(s['planner']['delivered']); self.assertFalse(s['planner']['reconstructed'])
        self.assertEqual(r['outcome']['causal_use_count'], 0)

    def test_uptake_and_causal_use_lesions(self):
        iv = WorkspaceIntervention(intervention_id='iv', disable_uptake=frozenset({'memory'}), disable_causal_use=frozenset({'planner'}))
        r = self.episode(intervention=iv)
        s = {x['receiver_id']: x for x in r['receiver_states']}
        self.assertTrue(s['memory']['reconstructed']); self.assertFalse(s['memory']['uptake'])
        self.assertTrue(s['planner']['uptake']); self.assertFalse(s['planner']['causal_use'])
        self.assertIsNone(r['reentry'])

    def test_truthful_vs_shuffled_reentry_changes_only_reentry_content(self):
        control = self.episode(intervention=WorkspaceIntervention(intervention_id='same'))
        shuffled = self.episode(intervention=WorkspaceIntervention(intervention_id='same', shuffle_reentry=True))
        self.assertEqual(control['outcome'], shuffled['outcome'])
        self.assertNotEqual(control['reentry']['used_receivers'], shuffled['reentry']['used_receivers'])
        self.assertNotEqual(control['episode_hash'], shuffled['episode_hash'])

    def test_reentry_can_be_disabled_without_erasing_causal_use(self):
        r = self.episode(intervention=WorkspaceIntervention(intervention_id='iv', disable_reentry=True))
        self.assertEqual(r['outcome']['causal_use_count'], 2)
        self.assertIsNone(r['reentry'])
        self.assertEqual(r['integration_readout']['reentry_fraction'], 0.0)

    def test_stale_candidate_filtered(self):
        r = self.episode(candidates=[WorkspaceCandidate('stale', .99, {'x':1}, 6), WorkspaceCandidate('live', .7, {'x':2}, 7)])
        self.assertEqual(r['winner_id'], 'live')
        stale = [x for x in r['receipts'] if x['stage']=='candidate_filter' and x['subject']=='stale'][0]
        self.assertEqual(stale['status'], 'STALE_EPOCH')

    def test_authority_mint_fails_closed(self):
        with self.assertRaises(AuthorityViolation):
            self.episode(candidates=[WorkspaceCandidate('bad', .8, {'x':1}, 7, requested_execution_authority=True)])

    def test_all_outputs_are_non_authoritative(self):
        r = self.episode()
        self.assertFalse(r['execution_authority'])
        self.assertTrue(all(x['execution_authority'] is False for x in r['receipts']))

    def test_witnesses_are_preserved(self):
        r = self.episode()
        self.assertEqual(r['basis'], {'basis_epoch':7,'semantic_state_hash':'sem-7','state_version_hash':'ver-7','trace_root_hash':'trace-7'})

    def test_tie_break_is_deterministic(self):
        r = self.episode(candidates=[WorkspaceCandidate('b', .8, {}, 7), WorkspaceCandidate('a', .8, {}, 7)])
        self.assertEqual(r['winner_id'], 'a')

    def test_receiver_closure_and_failure_classes(self):
        full = self.episode()
        self.assertEqual(full['closure_status'], 'REENTRY_CLOSED')
        partial = self.episode(receivers=[ReceiverPolicy('a'), ReceiverPolicy('b', causal_use=False)])
        self.assertEqual(partial['closure_status'], 'PARTIAL')
        classes = {x['receiver_id']: x['diagnostic_class'] for x in partial['receiver_states']}
        self.assertEqual(classes['a'], 'CAUSAL_USE')
        self.assertEqual(classes['b'], 'UPTAKE_NO_LOCAL_EFFECT')

    def test_shuffled_reentry_breaks_receiver_receipt_binding(self):
        control = self.episode(intervention=WorkspaceIntervention(intervention_id='same'))
        shuffled = self.episode(intervention=WorkspaceIntervention(intervention_id='same', shuffle_reentry=True))
        self.assertEqual(control['reentry']['source_binding_status'], 'PROVENANCE_BOUND')
        self.assertEqual(shuffled['reentry']['source_binding_status'], 'PROVENANCE_BROKEN')
        self.assertNotEqual(control['reentry']['receiver_evidence'], shuffled['reentry']['receiver_evidence'])

    def test_duplicate_ids_fail(self):
        with self.assertRaises(WorkspaceError):
            self.episode(candidates=[WorkspaceCandidate('x', .8, {}, 7), WorkspaceCandidate('x', .7, {}, 7)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
