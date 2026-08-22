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
    def __init__(self,**kwargs):
        type(self).calls.append(dict(kwargs)); self.fine_tuning=FineTuningFake()

class SafetyTests(unittest.TestCase):
    ENV_KEYS=(
        "CLAYCOG_HF_MODEL","CLAYCOG_HF_REVISION",
        "CLAYCOG_INSTRUCT_HF_MODEL","CLAYCOG_INSTRUCT_HF_REVISION",
        "TOGETHER_API_KEY",
    )
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name)
        self.old_constants=(mod.TRAIN,mod.VALID,mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B)
        self.old_env={k:os.environ.get(k) for k in self.ENV_KEYS}
        for k in self.ENV_KEYS: os.environ.pop(k,None)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        mod.TEMPLATE="Together/Qwen2-test-template"
        mod.TEMPLATE_ARCH="qwen2"
        mod.TEMPLATE_PARAMS_B="1.5"
        os.environ[mod.CREATE_LEDGER_DIR_ENV]=str(p/"ledger")
        self.hf=mod.PRIMARY_HF_MODEL; self.rev=mod.PRIMARY_HF_REVISION
    def tearDown(self):
        mod.TRAIN,mod.VALID,mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B=self.old_constants
        self.tmp.cleanup(); os.environ.pop(mod.CREATE_CONFIRM_ENV,None); os.environ.pop(mod.CREATE_LEDGER_DIR_ENV,None)
        for k,v in self.old_env.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
        ConstructorFake.calls.clear()

    def fp(self): return mod.campaign_fingerprint(self.hf,self.rev)

    def test_default_hf_sources_are_exact_revision_pinned(self):
        self.assertEqual((mod.PRIMARY_HF_MODEL,mod.PRIMARY_HF_REVISION),mod.resolve_hf_source(False))
        self.assertEqual((mod.INSTRUCT_HF_MODEL,mod.INSTRUCT_HF_REVISION),mod.resolve_hf_source(True))

    def test_custom_hf_model_requires_exact_revision(self):
        os.environ["CLAYCOG_HF_MODEL"]="example/custom-qwen2"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="abc"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="a"*40
        self.assertEqual(("example/custom-qwen2","a"*40),mod.resolve_hf_source(False))

    def test_template_must_be_explicit_qwen2_catalog_claim(self):
        with self.assertRaises(SystemExit): mod.require_compatible_template_claim("","qwen2","1.5")
        with self.assertRaises(SystemExit): mod.require_compatible_template_claim("Qwen/Qwen3.5-0.8B","qwen3_5","0.8")
        with self.assertRaises(SystemExit): mod.require_compatible_template_claim("candidate","qwen2","")
        meta=mod.require_compatible_template_claim("candidate","qwen2","7")
        self.assertEqual({"model":"candidate","architecture":"qwen2","params_b":7.0},meta)

    def test_fingerprint_binds_dataset_revision_template_and_training_config(self):
        a=self.fp(); self.assertEqual(a,self.fp())
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,self.fp())
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,"b"*40))
        old=mod.TEMPLATE_PARAMS_B; mod.TEMPLATE_PARAMS_B="7"
        try: self.assertNotEqual(a,self.fp())
        finally: mod.TEMPLATE_PARAMS_B=old

    def test_create_confirmation_requires_full_exact_fingerprint(self):
        fp=self.fp()
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp; mod.require_create_confirmation(fp)

    def test_account_duplicate_guard_matches_campaign_suffix_and_revision(self):
        c=ClientFake(); fp=self.fp(); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-existing",status="running",model=mod.TEMPLATE,from_hf_model=self.hf,
            hf_model_revision=self.rev,model_output_name="acct/output-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,self.rev,mod.TEMPLATE,suffix)
        self.assertIn("ft-existing",str(ctx.exception))
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,"c"*40,mod.TEMPLATE,suffix))

    def test_ambiguous_create_visible_in_account_is_blocked(self):
        c=ClientFake(); fp=self.fp(); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-ambiguous",status="pending",model=mod.TEMPLATE,from_hf_model=self.hf,
            hf_model_revision=self.rev,model_output_name="acct/qwen-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,self.rev,mod.TEMPLATE,suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT",str(ctx.exception)); self.assertEqual(1,len(c.fine_tuning.jobs))

    def test_local_intent_blocks_retry_even_if_provider_list_is_stale(self):
        c=ClientFake(); fp=self.fp(); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,self.rev,mod.TEMPLATE,suffix))
        path=mod.arm_create_intent(fp,self.hf,self.rev,suffix)
        mod.update_create_intent(path,"UNKNOWN_REMOTE_CREATE",error_class="TimeoutError")
        with self.assertRaises(SystemExit) as ctx: mod.assert_no_local_create_intent(fp)
        self.assertIn("UNKNOWN_REMOTE_CREATE",str(ctx.exception)); self.assertIn("reconcile exact provider state",str(ctx.exception))

    def test_create_intent_is_atomic_exclusive_and_contains_no_secret(self):
        fp=self.fp(); suffix=mod.campaign_suffix(fp); os.environ["TOGETHER_API_KEY"]="SHOULD_NOT_ENTER_LEDGER"
        path=mod.arm_create_intent(fp,self.hf,self.rev,suffix); data=path.read_text(encoding="utf-8"); payload=json.loads(data)
        self.assertEqual("CREATE_ARMED",payload["status"]); self.assertEqual(self.rev,payload["campaign"]["hf_model_revision"])
        self.assertNotIn("SHOULD_NOT_ENTER_LEDGER",data); self.assertEqual(0o600,path.stat().st_mode & 0o777)
        with self.assertRaises(SystemExit): mod.arm_create_intent(fp,self.hf,self.rev,suffix)

    def test_billed_create_client_disables_sdk_retries(self):
        mod.new_zero_retry_create_client(ConstructorFake); self.assertEqual([{"max_retries":0}],ConstructorFake.calls)

    def test_known_job_is_durably_bound_to_exact_fingerprint(self):
        fp=self.fp(); suffix=mod.campaign_suffix(fp); path=mod.arm_create_intent(fp,self.hf,self.rev,suffix)
        mod.update_create_intent(path,"JOB_KNOWN",job_id="ft-known"); payload=mod.read_create_ledger(fp)
        self.assertEqual("JOB_KNOWN",payload["status"]); self.assertEqual("ft-known",payload["job_id"]); self.assertEqual(fp,payload["fingerprint"])
        with self.assertRaises(SystemExit): mod.assert_no_local_create_intent(fp)

if __name__=="__main__": unittest.main(verbosity=2)
