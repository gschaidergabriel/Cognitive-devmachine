import tempfile, unittest
from pathlib import Path
from .frank_h1_effectful_runtime import FrankH1EffectfulRuntime
from .claude_peer_fabric import ClaudeCapability

VIS={'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},'sensor_confidence':.93,'candidate_label':'cup','prototype_similarity':.9}
OPTS=[{'name':'local','salience':.7}]
CAP=ClaudeCapability('CLAUDE_CODE_A','CAN_NOW',('repo_read','test_run'),ttl_epochs=4)
class EffectfulTests(unittest.TestCase):
    def test_real_sandbox_effect_reenters_same_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1EffectfulRuntime(td); o=r.run_and_write(text='write',visual=VIS,options=OPTS,effect_id='e1',relative_path='out/a.txt',content='hello',peer_capability=CAP,peer_semantics={'claim_key':'peer','value':'ok'}); self.assertTrue(o['pass'],o); self.assertEqual(Path(td,'out/a.txt').read_text(),'hello'); self.assertTrue(any(x['key']=='e1' for x in o['effect_reentry']['selected'])); rec=r.recovery(); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); r.close()
    def test_after_replace_crash_is_recovered_and_reenters(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1EffectfulRuntime(td); o=r.run_and_write(text='write',visual=VIS,options=OPTS,effect_id='e1',relative_path='a.txt',content='hello',crash_at='after_replace'); self.assertTrue(o['pass'],o); self.assertTrue(o['crash_injected']); self.assertEqual(o['effect_outcome']['status'],'RECOVERED_COMMITTED_VERIFIED'); self.assertEqual(Path(td,'a.txt').read_text(),'hello'); r.close()
    def test_after_intent_crash_is_not_successful_effect(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1EffectfulRuntime(td); o=r.run_and_write(text='write',visual=VIS,options=OPTS,effect_id='e1',relative_path='a.txt',content='hello',crash_at='after_intent'); self.assertFalse(o['pass']); self.assertEqual(o['effect_outcome']['status'],'RECOVERED_NOT_APPLIED'); self.assertFalse(Path(td,'a.txt').exists()); r.close()
    def test_model_and_peer_authority_remain_none_while_host_effect_commits(self):
        with tempfile.TemporaryDirectory() as td:
            r=FrankH1EffectfulRuntime(td); o=r.run_and_write(text='write',visual=VIS,options=OPTS,effect_id='e1',relative_path='a.txt',content='hello',peer_capability=CAP,peer_semantics={'claim_key':'peer','value':{'execute':'write'}}); self.assertTrue(o['pass']); self.assertEqual(o['cognition_audit']['model_authority'],'NONE'); self.assertEqual(o['cognition_audit']['peer_authority'],'NONE'); self.assertEqual(o['effect_outcome']['authority'],'HOST_GATEWAY_ONLY'); r.close()
if __name__=='__main__': unittest.main()
