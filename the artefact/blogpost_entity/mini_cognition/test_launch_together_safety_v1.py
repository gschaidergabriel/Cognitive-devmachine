#!/usr/bin/env python3
import importlib.util,json,os,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; SPEC=importlib.util.spec_from_file_location("launch_together_v1",HERE/"launch_together_v1.py"); mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
class FineTuningFake:
 def __init__(self):self.jobs=[]
 def list(self):return types.SimpleNamespace(data=list(self.jobs))
class ClientFake:
 def __init__(self):self.fine_tuning=FineTuningFake()
class ConstructorFake:
 calls=[]
 def __init__(self,**kwargs):type(self).calls.append(dict(kwargs));self.fine_tuning=FineTuningFake()
class SafetyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.old_paths=(mod.TRAIN,mod.VALID);self.old_template=(mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B);mod.TRAIN=p/'train.jsonl';mod.VALID=p/'valid.jsonl';mod.TRAIN.write_text('{"messages":[]}\n');mod.VALID.write_text('{"messages":[1]}\n');mod.TEMPLATE='provider/qwen2-0.5b-training';mod.TEMPLATE_ARCH='qwen2';mod.TEMPLATE_PARAMS_B='0.5';os.environ[mod.CREATE_LEDGER_DIR_ENV]=str(p/'ledger');self.hf='Qwen/Qwen2.5-0.5B'
 def tearDown(self):
  mod.TRAIN,mod.VALID=self.old_paths;mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B=self.old_template;self.tmp.cleanup();os.environ.pop(mod.CREATE_CONFIRM_ENV,None);os.environ.pop(mod.CREATE_LEDGER_DIR_ENV,None);ConstructorFake.calls.clear()
 def test_template_claim_requires_explicit_same_architecture_and_size(self):
  mod.require_compatible_template_claim()
  for template,arch,size in [('', 'qwen2','0.5'),('provider/qwen2-7b','qwen2','7'),('provider/other-0.5b','other','0.5'),('provider/qwen2-0.5b','qwen2','bad')]:
   mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B=template,arch,size
   with self.assertRaises(SystemExit):mod.require_compatible_template_claim()
 def test_fingerprint_binds_dataset_and_template_metadata(self):
  a=mod.campaign_fingerprint(self.hf);self.assertEqual(a,mod.campaign_fingerprint(self.hf));mod.VALID.write_text('{"messages":[2]}\n');self.assertNotEqual(a,mod.campaign_fingerprint(self.hf));mod.VALID.write_text('{"messages":[1]}\n');b=mod.campaign_fingerprint(self.hf);mod.TEMPLATE='provider/qwen2-0.5b-v2';self.assertNotEqual(b,mod.campaign_fingerprint(self.hf))
 def test_create_confirmation_requires_full_exact_fingerprint(self):
  fp=mod.campaign_fingerprint(self.hf)
  with self.assertRaises(SystemExit):mod.require_create_confirmation(fp)
  os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
  with self.assertRaises(SystemExit):mod.require_create_confirmation(fp)
  os.environ[mod.CREATE_CONFIRM_ENV]=fp;mod.require_create_confirmation(fp)
 def test_account_duplicate_guard_matches_campaign_suffix(self):
  c=ClientFake();fp=mod.campaign_fingerprint(self.hf);suffix=mod.campaign_suffix(fp);c.fine_tuning.jobs.append(types.SimpleNamespace(id='ft-existing',status='running',model=mod.TEMPLATE,from_hf_model=self.hf,model_output_name='acct/'+suffix))
  with self.assertRaises(SystemExit):mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
 def test_regression_local_intent_blocks_stale_provider_list(self):
  c=ClientFake();fp=mod.campaign_fingerprint(self.hf);suffix=mod.campaign_suffix(fp);path=mod.arm_create_intent(fp,self.hf,suffix);mod.update_create_intent(path,'UNKNOWN_REMOTE_CREATE',error_class='TimeoutError');self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
  with self.assertRaises(SystemExit) as ctx:mod.assert_no_local_create_intent(fp)
  self.assertIn('UNKNOWN_REMOTE_CREATE',str(ctx.exception))
 def test_create_intent_atomic_exclusive_no_secret(self):
  fp=mod.campaign_fingerprint(self.hf);suffix=mod.campaign_suffix(fp);os.environ['TOGETHER_API_KEY']='SECRET_SENTINEL'
  try:
   path=mod.arm_create_intent(fp,self.hf,suffix);data=path.read_text();self.assertNotIn('SECRET_SENTINEL',data);self.assertEqual(0o600,path.stat().st_mode&0o777)
   with self.assertRaises(SystemExit):mod.arm_create_intent(fp,self.hf,suffix)
  finally:os.environ.pop('TOGETHER_API_KEY',None)
 def test_billed_create_client_disables_sdk_retries(self):mod.new_zero_retry_create_client(ConstructorFake);self.assertEqual([{'max_retries':0}],ConstructorFake.calls)
 def test_known_job_durably_bound(self):
  fp=mod.campaign_fingerprint(self.hf);suffix=mod.campaign_suffix(fp);path=mod.arm_create_intent(fp,self.hf,suffix);mod.update_create_intent(path,'JOB_KNOWN',job_id='ft-known');payload=mod.read_create_ledger(fp);self.assertEqual('ft-known',payload['job_id']);self.assertEqual(fp,payload['fingerprint'])
if __name__=='__main__':unittest.main(verbosity=2)
