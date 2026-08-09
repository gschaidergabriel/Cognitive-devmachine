import tempfile, unittest
from PIL import Image, ImageDraw
from .frank_h1_loop_of_loops import FrankH1LoopOfLoopsRuntime


def familiar(shift=0):
    im=Image.new('RGB',(64,64),'black'); ImageDraw.Draw(im).rectangle((6+shift,12,26+shift,52),fill=(240,40,40)); return im

def novel():
    im=Image.new('RGB',(64,64),'black'); d=ImageDraw.Draw(im); d.ellipse((12,12,50,50),fill=(30,40,250)); return im

class LoopOfLoopsTests(unittest.TestCase):
    def test_repeated_familiar_state_converges(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=0); x=r.run_episode(episode_id='e',text='work',images=[familiar(),familiar()],max_fast_cycles=6,slow_period=1); self.assertEqual(x['terminal_decision'],'HALT_CANDIDATE_CONVERGED'); self.assertEqual(x['fast_cycle_count'],2); self.assertTrue(x['slow_reentry_observed']); self.assertFalse(x['emergence_claim']); r.close()
    def test_repeated_unknown_state_escalates_stalled(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); x=r.run_episode(episode_id='e',text='inspect',images=[novel(),novel()],max_fast_cycles=6,slow_period=1); self.assertEqual(x['terminal_decision'],'ESCALATE_STALLED'); self.assertEqual(x['fast_cycle_count'],2); self.assertGreaterEqual(x['fast_cycles'][-1]['pressure'],.8); r.close()
    def test_changing_state_runs_until_budget_then_halts(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=0); x=r.run_episode(episode_id='e',text='work',images=[familiar(),novel(),familiar()],max_fast_cycles=3,slow_period=1); self.assertEqual(x['fast_cycle_count'],3); self.assertIn(x['terminal_decision'],{'HALT_CANDIDATE_CONVERGED','ESCALATE_STALLED'}); r.close()
    def test_slow_state_is_same_ledger_and_reenters_memory_support(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=0); x=r.run_episode(episode_id='e',text='work',images=[familiar(),familiar()],max_fast_cycles=4,slow_period=1,options=[{'name':'user','salience':.8}]); row=r.ledger.get('loop_control','episode:e'); self.assertIsNotNone(row); self.assertEqual(row['value']['authority'],'CONTROL_STATE_ONLY'); self.assertTrue(x['slow_reentry_observed']); r.close()
    def test_loop_controller_lesion_halts_episode(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); r.spine.lesion('loop_dynamics_controller'); x=r.run_episode(episode_id='e',text='work',images=[familiar()],max_fast_cycles=5); self.assertEqual(x['terminal_decision'],'HALT_LESIONED'); self.assertEqual(x['fast_cycle_count'],1); r.close()
    def test_replay_exact_after_nested_loops(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1LoopOfLoopsRuntime(td); r.learn_visual('left_app',familiar(),capture_epoch=0); r.run_episode(episode_id='e',text='work',images=[familiar(),familiar()],max_fast_cycles=6,slow_period=1); rec=r.recovery(); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); self.assertTrue(rec['epoch_equal']); r.close()
if __name__=='__main__': unittest.main()
