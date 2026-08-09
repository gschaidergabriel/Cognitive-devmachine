import tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from .frank_h1_organism_runtime import FrankH1OrganismRuntime
from .claude_peer_fabric import ClaudeCapability

CAP=ClaudeCapability('CLAUDE_CODE_A','CAN_NOW',('repo_read','test_run'),ttl_epochs=4)
def familiar(shift=0):
    im=Image.new('RGB',(64,64),'black'); ImageDraw.Draw(im).rectangle((6+shift,12,26+shift,52),fill=(240,40,40)); return im
def novel():
    im=Image.new('RGB',(64,64),'black'); d=ImageDraw.Draw(im); d.ellipse((15,15,50,50),fill=(30,40,250)); return im

class OrganismTests(unittest.TestCase):
    def test_pixel_peer_gwt_effect_reentry_are_one_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1OrganismRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=1); o=r.run(text='inspect and write',image=familiar(1),source_id='screen',capture_epoch=2,options=[{'name':'local','salience':.7}],peer_capability=CAP,peer_semantics={'claim_key':'peer_hint','value':'ok'},effect_id='e1',relative_path='out.txt',content='done'); self.assertTrue(o['organism_audit']['pass'],o['organism_audit']); self.assertEqual(Path(td,'out.txt').read_text(),'done'); self.assertTrue(o['visual']['full_runtime']['peer']['peer_selected_by_workspace']); self.assertEqual(o['visual']['familiarity'].candidate_label,'left_app'); self.assertEqual(o['effect_outcome']['authority'],'HOST_GATEWAY_ONLY'); r.close()
    def test_unknown_visual_state_does_not_gain_authority(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1OrganismRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=1); o=r.run(text='inspect',image=novel(),source_id='screen',capture_epoch=2,options=[{'name':'inspect','salience':.9}]); self.assertTrue(o['organism_audit']['pass']); self.assertEqual(o['visual']['familiarity'].outcome,'UNKNOWN'); self.assertEqual(o['visual']['visual_percept']['epistemic_state'],'UNKNOWN'); self.assertEqual(o['organism_audit']['familiarity_authority'],'FAMILIARITY_ROUTING_ONLY'); r.close()
    def test_after_replace_effect_crash_recovers_inside_organism(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1OrganismRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=1); o=r.run(text='write',image=familiar(),source_id='screen',capture_epoch=2,options=[{'name':'write','salience':.8}],effect_id='e1',relative_path='x.txt',content='x',crash_at='after_replace'); self.assertTrue(o['organism_audit']['pass']); self.assertTrue(o['crash_injected']); self.assertEqual(o['effect_outcome']['status'],'RECOVERED_COMMITTED_VERIFIED'); r.close()
    def test_visual_only_mode_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1OrganismRuntime(td); o=r.run(text='look',image=novel(),source_id='screen',capture_epoch=1,options=[{'name':'inspect','salience':.9}]); self.assertTrue(o['organism_audit']['pass']); self.assertFalse(o['organism_audit']['effect_requested']); self.assertIsNone(o['effect_outcome']); r.close()
    def test_long_organism_replay_exact(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1OrganismRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=1)
            for i in range(20):
                o=r.run(text=str(i),image=familiar(i%2),source_id='screen',capture_epoch=i+2,options=[{'name':'work','salience':.8}],effect_id=f'e{i}',relative_path=f'f{i}.txt',content=str(i),crash_at='after_replace' if i%10==0 else None); self.assertTrue(o['organism_audit']['pass'])
            rec=r.recovery(); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); self.assertTrue(rec['epoch_equal']); self.assertEqual(len(list(Path(td).glob('f*.txt'))),20); r.close()
if __name__=='__main__': unittest.main()
