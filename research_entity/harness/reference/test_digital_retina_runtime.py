import tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from .state_ledger import StateLedger
from dataclasses import replace
from .digital_retina_runtime import DigitalRetinaRuntime, FEATURE_VERSION, LearningBudget


def img(kind,shift=0):
    im=Image.new('RGB',(64,64),'black'); d=ImageDraw.Draw(im)
    if kind=='left': d.rectangle((6+shift,12,26+shift,52),fill=(240,40,40))
    elif kind=='right': d.rectangle((38-shift,12,58-shift,52),fill=(40,240,40))
    elif kind=='cross':
        d.rectangle((27,8,37,56),fill=(40,80,240)); d.rectangle((8,27,56,37),fill=(40,80,240))
    elif kind=='noise':
        a=np.random.default_rng(123).integers(0,256,(64,64,3),dtype=np.uint8); return Image.fromarray(a,'RGB')
    return im

class RetinaTests(unittest.TestCase):
    def make(self): l=StateLedger(); return l,DigitalRetinaRuntime(l)
    def test_pixel_capture_is_deterministic(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); b,_=r.capture(img('left'),source_id='cam2',capture_epoch=1); self.assertEqual(a.frame_hash,b.frame_hash); self.assertEqual(a.feature_vector,b.feature_vector); self.assertEqual(a.feature_version,FEATURE_VERSION); l.close()
    def test_change_gate_detects_same_vs_changed(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); b,_=r.capture(img('left'),source_id='cam',capture_epoch=2); c,_=r.capture(img('right'),source_id='cam',capture_epoch=3); self.assertTrue(a.changed); self.assertFalse(b.changed); self.assertTrue(c.changed); self.assertGreater(c.change_score,b.change_score); l.close()
    def test_gold_example_becomes_familiar(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); t=r.admit_example('left_app',e,tier='GOLD',evidence_ref='gold:user'); self.assertTrue(t['trained']); x,_=r.capture(img('left',1),source_id='cam',capture_epoch=2); f=r.classify(x); self.assertIn(f.outcome,{'KNOWN_HIGH_CONFIDENCE','KNOWN_NEEDS_CONFIRMATION'}); self.assertEqual(f.candidate_label,'left_app'); l.close()
    def test_unseen_pattern_rejects_open_set(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',e,tier='GOLD',evidence_ref='gold:user'); x,_=r.capture(img('noise'),source_id='cam',capture_epoch=2); f=r.classify(x); self.assertEqual(f.outcome,'UNKNOWN'); self.assertIsNone(f.candidate_label); l.close()
    def test_bronze_never_trains(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); t=r.admit_example('left_app',e,tier='BRONZE',evidence_ref='self'); self.assertFalse(t['trained']); self.assertIsNone(l.get('visual_learning','prototype_current:left_app')); l.close()
    def test_silver_requires_two_distinct_frames(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); x=r.admit_example('left_app',a,tier='SILVER',evidence_ref='silver:1'); self.assertEqual(x['status'],'SILVER_BUFFERED'); b,_=r.capture(img('left',1),source_id='cam',capture_epoch=2); y=r.admit_example('left_app',b,tier='SILVER',evidence_ref='silver:2'); self.assertTrue(y['trained']); l.close()
    def test_context_conflict_stays_conflict(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',e,tier='GOLD',evidence_ref='gold:user'); x,_=r.capture(img('left'),source_id='cam',capture_epoch=2); f=r.classify(x,context_prior='right_app'); self.assertEqual(f.outcome,'CONFLICT'); l.close()
    def test_version_and_rollback(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',a,tier='GOLD',evidence_ref='g1'); b,_=r.capture(img('left',1),source_id='cam',capture_epoch=2); t=r.admit_example('left_app',b,tier='GOLD',evidence_ref='g2'); self.assertEqual(t['version'],2); rb=r.rollback('left_app'); self.assertEqual(rb['status'],'ROLLED_BACK'); self.assertEqual(l.get('visual_learning','prototype_current:left_app')['value']['version'],1); l.close()
    def test_materialized_percept_preserves_evidence_vs_familiarity(self):
        l,r=self.make(); e,_=r.capture(img('cross'),source_id='screen',capture_epoch=5); f=r.classify(e); p=r.materialize_visual_percept(e,f); self.assertEqual(p['authority'],'OBSERVATION_ONLY'); self.assertEqual(p['familiarity']['authority'],'FAMILIARITY_ROUTING_ONLY'); self.assertEqual(p['frame_hash'],e.frame_hash); l.close()
    def test_png_file_input_matches_in_memory(self):
        l,r=self.make(); im=img('right'); a,_=r.capture(im,source_id='a',capture_epoch=1)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td,'x.png'); im.save(path); b,_=r.capture(path,source_id='b',capture_epoch=1); self.assertEqual(a.frame_hash,b.frame_hash); self.assertEqual(a.feature_vector,b.feature_vector)
        l.close()
    def test_ledger_replay_preserves_learning_state(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',e,tier='GOLD',evidence_ref='gold:user'); events=l.export_events(); x=StateLedger.replay(events); self.assertEqual(x.semantic_state_hash,l.semantic_state_hash); self.assertEqual(x.trace_root_hash,l.trace_root_hash); self.assertEqual(x.get('visual_learning','prototype_current:left_app')['value']['version'],1); x.close(); l.close()
    def test_resource_budget_can_pause_learning_without_disabling_perception(self):
        l=StateLedger(); r=DigitalRetinaRuntime(l,LearningBudget(max_classes=0)); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); t=r.admit_example('left_app',e,tier='GOLD',evidence_ref='gold'); self.assertEqual(t['status'],'PAUSED_RESOURCE_BUDGET_CLASSES'); self.assertFalse(t['trained']); self.assertEqual(r.classify(e).outcome,'UNKNOWN'); l.close()
    def test_feature_version_mismatch_is_rejected(self):
        l,r=self.make(); e,_=r.capture(img('left'),source_id='cam',capture_epoch=1); bad=replace(e,feature_version='other-backbone'); t=r.admit_example('left_app',bad,tier='GOLD',evidence_ref='gold'); self.assertEqual(t['status'],'REJECTED_FEATURE_VERSION'); self.assertFalse(t['trained']); l.close()
    def test_sequential_classes_retain_first_prototype(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',a,tier='GOLD',evidence_ref='g1'); b,_=r.capture(img('right'),source_id='cam',capture_epoch=2); r.admit_example('right_app',b,tier='GOLD',evidence_ref='g2'); a2,_=r.capture(img('left',1),source_id='cam',capture_epoch=3); f=r.classify(a2); self.assertEqual(f.candidate_label,'left_app'); self.assertTrue(f.outcome.startswith('KNOWN')); l.close()
    def test_routing_decision_distinguishes_familiar_from_unknown(self):
        l,r=self.make(); a,_=r.capture(img('left'),source_id='cam',capture_epoch=1); r.admit_example('left_app',a,tier='GOLD',evidence_ref='g'); a2,_=r.capture(img('left',1),source_id='cam',capture_epoch=2); pf=r.materialize_visual_percept(a2,r.classify(a2)); self.assertEqual(pf['routing_decision'],'FAMILIAR_FAST_PATH'); n,_=r.capture(img('noise'),source_id='cam',capture_epoch=3); pn=r.materialize_visual_percept(n,r.classify(n)); self.assertEqual(pn['routing_decision'],'DEEP_PERCEPTION_ESCALATION'); l.close()
if __name__=='__main__': unittest.main()
