#!/usr/bin/env python3
import importlib.util, json, os, tempfile, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_v1", HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FineTuningFake:
    def __init__(self): self.jobs=[]
    def list(self): return types.SimpleNamespace(data=list(self.jobs))
class ClientFake:
    def __init__(self): self.fine_tuning=FineTuningFake()
class ConstructorFake:
    calls=[]
    def __init__(self,**kwargs): type(self).calls.append(dict(kwargs)); self.fine_tuning=FineTuningFake()

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name); self.old=(mod.TRAIN,mod.VALID)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"; mod.TRAIN.write_text('{"messages":[]}\n'); mod.VALID.write_text('{"messages":[1]}\n')
        os.environ[mod.CREATE_LEDGER_DIR_ENV]=str(p/"ledger"); self.hf=mod.PRIMARY_HF_MODEL; self.rev=mod.PRIMARY_HF_REVISION
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old; self.tmp.cleanup()
        for name in (mod.CREATE_CONFIRM_ENV,mod.CREATE_LEDGER_DIR_ENV,"CLAYCOG_HF_MODEL","CLAYCOG_HF_REVISION","CLAYCOG_INSTRUCT_HF_MODEL","CLAYCOG_INSTRUCT_HF_REVISION"): os.environ.pop(name,None)
        ConstructorFake.calls.clear()
    def test_fingerprint_binds_dataset_training_config_and_hf_revision(self):
        a=mod.campaign_fingerprint(self.hf,self.rev); self.assertEqual(a,mod.campaign_fingerprint(self.hf,self.rev)); mod.VALID.write_text('{"messages":[2]}\n'); self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,self.rev)); mod.VALID.write_text('{"messages":[1]}\n'); self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,"1"*40))
    def test_exact_revision_defaults_and_custom_override_fail_closed(self):
        self.assertEqual((mod.PRIMARY_HF_MODEL,mod.PRIMARY_HF_REVISION),mod.resolve_hf_source(False)); self.assertEqual((mod.INSTRUCT_HF_MODEL,mod.INSTRUCT_HF_REVISION),mod.resolve_hf_source(True)); os.environ["CLAYCOG_HF_MODEL"]="example/custom-qwen2"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="abc"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="2"*40; self.assertEqual(("example/custom-qwen2","2"*40),mod.resolve_hf_source(False))
    def test_create_confirmation_requires_full_exact_fingerprint(self):
        fp=mod.campaign_fingerprint(self.hf,self.rev)
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp; mod.require_create_confirmation(fp)
    def test_account_duplicate_guard_matches_campaign_suffix(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp); c.fine_tuning.jobs.append(types.SimpleNamespace(id="ft-existing",status="running",model=mod.TEMPLATE,from_hf_model=self.hf,model_output_name="acct/output-"+suffix))
        with self.assertRaises(SystemExit) as ctx: mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
        self.assertIn("ft-existing",str(ctx.exception))
    def test_local_intent_blocks_retry_even_if_provider_list_is_stale(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp); path=mod.arm_create_intent(fp,self.hf,self.rev,suffix); mod.update_create_intent(path,"UNKNOWN_REMOTE_CREATE",error_class="TimeoutError"); self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
        with self.assertRaises(SystemExit) as ctx: mod.assert_no_local_create_intent(fp)
        self.assertIn("UNKNOWN_REMOTE_CREATE",str(ctx.exception))
    def test_create_intent_is_atomic_exclusive_secret_free_and_revision_bound(self):
        fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp); os.environ["TOGETHER_API_KEY"]="SHOULD_NOT_ENTER_LEDGER"
        try:
            path=mod.arm_create_intent(fp,self.hf,self.rev,suffix); data=path.read_text(); payload=json.loads(data); self.assertEqual("CREATE_ARMED",payload["status"]); self.assertEqual(self.rev,payload["campaign"]["hf_model_revision"]); self.assertNotIn("SHOULD_NOT_ENTER_LEDGER",data); self.assertEqual(0o600,path.stat().st_mode & 0o777)
            with self.assertRaises(SystemExit): mod.arm_create_intent(fp,self.hf,self.rev,suffix)
        finally: os.environ.pop("TOGETHER_API_KEY",None)
    def test_billed_create_client_disables_sdk_retries(self): mod.new_zero_retry_create_client(ConstructorFake); self.assertEqual([{"max_retries":0}],ConstructorFake.calls)
    def test_known_job_is_durably_bound_to_exact_fingerprint(self):
        fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp); path=mod.arm_create_intent(fp,self.hf,self.rev,suffix); mod.update_create_intent(path,"JOB_KNOWN",job_id="ft-known"); payload=mod.read_create_ledger(fp); self.assertEqual("ft-known",payload["job_id"]); self.assertEqual(fp,payload["fingerprint"])

if __name__=="__main__": unittest.main(verbosity=2)
