import unittest
from PIL import Image, ImageDraw
from .frank_h1_pixel_runtime import FrankH1PixelRuntime


def left(shift=0):
    im=Image.new('RGB',(64,64),'black'); ImageDraw.Draw(im).rectangle((6+shift,12,26+shift,52),fill=(240,40,40)); return im

def cross():
    im=Image.new('RGB',(64,64),'black'); d=ImageDraw.Draw(im); d.rectangle((27,8,37,56),fill=(40,80,240)); d.rectangle((8,27,56,37),fill=(40,80,240)); return im

class PixelRuntimeTests(unittest.TestCase):
    def test_real_pixel_path_joins_full_runtime(self):
        r=FrankH1PixelRuntime(); r.learn('left_app',left(),capture_epoch=1); o=r.run_image(text='what is visible',image=left(1),source_id='screen',capture_epoch=2,options=[{'name':'inspect','salience':.8}]); self.assertTrue(o['pass'],o); self.assertEqual(o['familiarity'].candidate_label,'left_app'); self.assertTrue(o['full_runtime']['integration_audit']['all_current_modules_exercised']); self.assertTrue(o['full_runtime']['dynamic_claygraph_validation']['pass']); r.close()
    def test_unknown_pixel_content_escalates_without_false_truth(self):
        r=FrankH1PixelRuntime(); r.learn('left_app',left(),capture_epoch=1); o=r.run_image(text='inspect unknown',image=cross(),source_id='screen',capture_epoch=2,options=[{'name':'inspect','salience':.9}]); self.assertTrue(o['pass']); self.assertEqual(o['familiarity'].outcome,'UNKNOWN'); self.assertIsNone(o['familiarity'].candidate_label); self.assertEqual(o['visual_percept']['epistemic_state'],'UNKNOWN'); r.close()
    def test_pixel_context_conflict_survives_into_visual_receipt(self):
        r=FrankH1PixelRuntime(); r.learn('left_app',left(),capture_epoch=1); o=r.run_image(text='check conflict',image=left(),source_id='screen',capture_epoch=2,options=[{'name':'inspect','salience':.9}],context_prior='other_app'); self.assertTrue(o['pass']); self.assertEqual(o['familiarity'].outcome,'CONFLICT'); self.assertEqual(o['visual_percept']['epistemic_state'],'CONFLICT'); r.close()
    def test_long_pixel_loop_replays_exact(self):
        r=FrankH1PixelRuntime(); r.learn('left_app',left(),capture_epoch=1)
        for i in range(20):
            o=r.run_image(text=str(i),image=left(i%2),source_id='screen',capture_epoch=i+2,options=[{'name':'inspect','salience':.8}]); self.assertTrue(o['pass'])
        rec=r.full.recovery(); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); self.assertTrue(rec['epoch_equal']); r.close()
if __name__=='__main__': unittest.main()
