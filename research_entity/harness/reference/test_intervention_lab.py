import unittest
from .frank_integrated_spine import FrankIntegratedSpine, MODULES
from .intervention_lab import run_once, rescue_equivalence, graph_handle_coverage, DEFAULT_VISUAL

class InterventionLabTests(unittest.TestCase):
    def test_all_15_graph_handles_are_executable_module_names(self):
        x=graph_handle_coverage(); self.assertTrue(x['pass'],x); self.assertEqual(len(x['observed']),15)

    def test_all_15_rescue_to_exact_baseline(self):
        for m in MODULES:
            with self.subTest(module=m):
                x=rescue_equivalence(m); self.assertTrue(x['semantic_state_hash_equal'],x); self.assertTrue(x['trace_root_hash_equal'],x); self.assertTrue(x['signature_equal'],x)

    def test_critical_lesions_fail_closed(self):
        for m in ('needle_bridge','semantic_state','unifieddb_plane'):
            with self.subTest(module=m): self.assertEqual(run_once(m)['status'],'SYSTEM_UNAVAILABLE')

    def test_digital_retina_lesion_removes_sensor_confidence(self):
        x=run_once('digital_retina'); self.assertEqual(x['signature']['percept_epistemic'],'UNKNOWN'); self.assertEqual(x['signature']['mvc_outcome'],'UNKNOWN'); self.assertGreater(x['signature']['gate_gain'],run_once()['signature']['gate_gain'])

    def test_perceptual_field_lesion_forces_unknown(self):
        self.assertEqual(run_once('perceptual_field')['signature']['percept_epistemic'],'UNKNOWN')

    def test_micro_visual_classifier_lesion_forces_unknown_familiarity(self):
        self.assertEqual(run_once('micro_visual_classifier')['signature']['mvc_outcome'],'UNKNOWN')

    def test_claygraph_memory_lesion_removes_memory_support_and_changes_workspace(self):
        opts=[{'name':'memory_candidate','salience':.52,'memory_key':'semantic:self'}]
        base=run_once(options=opts); lesion=run_once('claygraph_memory',options=opts)
        self.assertTrue(base['signature']['memory_context_used']); self.assertTrue(base['signature']['ignition']);
        self.assertFalse(lesion['signature']['memory_context_used']); self.assertFalse(lesion['signature']['ignition']); self.assertEqual(lesion['signature']['effect_status'],'DENIED_NO_ACTION_PROPOSAL')

    def test_thalamus_lesion_blocks_relay_ignition_and_effect(self):
        s=run_once('thalamus_attention')['signature']; self.assertFalse(s['gate_relay']); self.assertFalse(s['ignition']); self.assertEqual(s['effect_status'],'DENIED_NO_ACTION_PROPOSAL')

    def test_hyperposition_lesion_collapses_alternatives_and_changes_selection(self):
        s=run_once('hyperposition')['signature']; self.assertEqual(s['alternative_count'],1); self.assertFalse(s['ignition']); self.assertEqual(s['effect_status'],'DENIED_NO_ACTION_PROPOSAL')

    def test_gwt_lesion_blocks_ignition(self):
        s=run_once('gwt_workspace')['signature']; self.assertFalse(s['ignition']); self.assertFalse(s['uptake']); self.assertEqual(s['effect_status'],'DENIED_NO_ACTION_PROPOSAL')

    def test_model_lesion_blocks_cognitive_proposal_and_effect(self):
        s=run_once('clay_model_4b')['signature']; self.assertEqual(s['proposal_kind'],'NOOP'); self.assertFalse(s['uptake']); self.assertEqual(s['effect_status'],'DENIED_NO_ACTION_PROPOSAL')

    def test_loop_controller_lesion_is_visible_and_not_emergence(self):
        s=run_once('loop_dynamics_controller')['signature']; self.assertEqual(s['loop_decision'],'HALT_LESIONED')

    def test_effect_gateway_lesion_denies_effect(self):
        self.assertEqual(run_once('effect_gateway')['signature']['effect_status'],'DENIED_LESIONED_EFFECT_GATEWAY')

    def test_causal_replay_lesion_removes_causal_use_and_reentry(self):
        s=run_once('causal_observability_replay')['signature']; self.assertEqual(s['effect_status'],'COMMITTED'); self.assertFalse(s['causal_use']); self.assertFalse(s['reentry'])

    def test_adaptive_promotion_lesion_blocks_learning_promotion_only(self):
        s=run_once('adaptive_state_promotion')['signature']; self.assertEqual(s['adaptive_status'],'LESIONED_NO_PROMOTION'); self.assertEqual(s['effect_status'],'COMMITTED')

if __name__=='__main__': unittest.main()
