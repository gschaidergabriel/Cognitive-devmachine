#!/usr/bin/env python3
import importlib.util,json,os,stat,tempfile,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("launch08",HERE/"launch_together_qwen35_08b_v1.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FT:
    def __init__(self,jobs=None,full=True):self.jobs=list(jobs or []);self.full=full;self.limits_kwargs=None;self.estimate_kwargs=None
    def list(self):return types.SimpleNamespace(data=self.jobs)
    def model_limits(self,**kw):self.limits_kwargs=kw;return types.SimpleNamespace(supports_full_training=self.full,full_training=types.SimpleNamespace() if self.full else None)
    def estimate_price(self,**kw):self.estimate_kwargs=kw;return types.SimpleNamespace(estimated_total_price=4.0,allowed_to_proceed=True)
class Client:
    def __init__(self,jobs=None,full=True):self.fine_tuning=FT(jobs,full)
class TogetherCtor:
    last=None
    def __init__(self,**kw):type(self).last=kw
class ProviderModel:
    def __init__(self,value):self.value=value
    def model_dump(self):return self.value
class Tests(unittest.TestCase):
    def setUp(self):
        self.c=os.environ.pop(m.CREATE_CONFIRM_ENV,None);self.l=os.environ.get(m.CREATE_LEDGER_DIR_ENV);self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.ot,self.ov=m.TRAIN,m.VALID;m.TRAIN=r/"t.jsonl";m.VALID=r/"v.jsonl";m.TRAIN.write_text('{"messages":[]}\n');m.VALID.write_text('{"messages":[]}\n')
    def tearDown(self):
        m.TRAIN,m.VALID=self.ot,self.ov;self.t.cleanup()
        if self.c is None:os.environ.pop(m.CREATE_CONFIRM_ENV,None)
        else:os.environ[m.CREATE_CONFIRM_ENV]=self.c
        if self.l is None:os.environ.pop(m.CREATE_LEDGER_DIR_ENV,None)
        else:os.environ[m.CREATE_LEDGER_DIR_ENV]=self.l
    def test_model_and_direct_campaign(self):
        self.assertEqual(m.MODEL,"Qwen/Qwen3.5-0.8B");m.validate_static_contract();d=m.campaign_descriptor();self.assertEqual(d["training_type"],{"type":"Full"});self.assertEqual(d["random_seed"],3407);raw=json.dumps(d);self.assertNotIn("from_hf_model",raw);self.assertNotIn("template_model",raw)
    def test_local_checks_use_canonical_v2_validator(self):
        with mock.patch.object(m.subprocess,"run") as run:
            m.local_checks()
        self.assertEqual(run.call_count,2)
        generate=run.call_args_list[0].args[0];validate=run.call_args_list[1].args[0]
        self.assertEqual(Path(generate[1]).name,"generate_sft_v2.py")
        self.assertEqual(Path(validate[1]).name,"validate_corpus_v2.py")
        self.assertEqual(validate[2:],[str(m.TRAIN),str(m.VALID)])
        self.assertTrue(run.call_args_list[0].kwargs["check"]);self.assertTrue(run.call_args_list[1].kwargs["check"])
    def test_sdk_v2_model_limits(self):
        c=Client();m.get_full_training_limits(c);self.assertEqual(c.fine_tuning.limits_kwargs,{"model_name":m.EXPECTED_MODEL})
        with self.assertRaises(SystemExit):m.get_full_training_limits(Client(full=False))
    def test_estimate_schema_subset(self):
        c=Client();m.estimate_price(c,"t","v");q=c.fine_tuning.estimate_kwargs;self.assertEqual(q["training_type"],{"type":"Full"});self.assertEqual(q["training_method"],{"method":"sft","train_on_inputs":"auto"})
        for x in ("random_seed","learning_rate","warmup_ratio","from_hf_model"):self.assertNotIn(x,q)
    def test_create_explicit_full_and_seed(self):
        p=m.create_payload("t","v","s");self.assertEqual(p["training_type"],{"type":"Full"});self.assertEqual(p["random_seed"],3407);self.assertEqual(p["learning_rate"],1e-5);self.assertEqual(p["warmup_ratio"],.03)
        for x in ("lora","from_hf_model","hf_model_revision","train_on_inputs"):self.assertNotIn(x,p)
    def test_fingerprint_binds_dataset(self):
        a=m.campaign_fingerprint();m.TRAIN.write_text('{"messages":[1]}\n');self.assertNotEqual(a,m.campaign_fingerprint())
    def test_duplicate_guard(self):
        s="claycog08b-v2-dead";c=Client([{"id":"j","status":"running","model":m.MODEL,"model_output_name":"x"+s}])
        with self.assertRaises(SystemExit):m.assert_no_duplicate_campaign(c,s)
    def test_confirmation_and_private_intent(self):
        fp="a"*64
        with self.assertRaises(SystemExit):m.require_create_confirmation(fp)
        os.environ[m.CREATE_CONFIRM_ENV]=fp;m.require_create_confirmation(fp)
        with tempfile.TemporaryDirectory() as td:
            os.environ[m.CREATE_LEDGER_DIR_ENV]=td;fp=m.campaign_fingerprint();p=m.arm_create_intent(fp,m.campaign_suffix(fp));self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600);self.assertEqual(m.read_create_ledger(fp)["campaign"]["training_type"],{"type":"Full"})
    def test_created_job_identity_mismatch_detection(self):
        expected={"training_file":"t","validation_file":"v","model":m.MODEL,"n_epochs":3,"n_evals":2,"n_checkpoints":1,"random_seed":3407,"learning_rate":1e-5,"warmup_ratio":.03,"training_method":m.training_method(),"training_type":m.training_type()}
        good=types.SimpleNamespace(**expected);self.assertEqual(m.created_job_identity_mismatches(good,expected),{})
        for field,bad_value in (("random_seed",9),("learning_rate",2e-5),("warmup_ratio",.2),("training_type",{"type":"LoRA"}),("training_method",{"method":"sft","train_on_inputs":"false"}),("n_checkpoints",2)):
            meta=types.SimpleNamespace(**{**expected,field:bad_value});mm=m.created_job_identity_mismatches(meta,expected);self.assertIn(field,mm)
    def test_created_job_identity_normalizes_provider_models(self):
        expected={"training_method":m.training_method(),"training_type":m.training_type()}
        meta=types.SimpleNamespace(training_method=ProviderModel(m.training_method()),training_type=ProviderModel(m.training_type()))
        self.assertEqual(m.created_job_identity_mismatches(meta,expected),{})
    def test_zero_retry(self):
        TogetherCtor.last=None;m.new_zero_retry_create_client(TogetherCtor);self.assertEqual(TogetherCtor.last,{"max_retries":0})
if __name__=="__main__":unittest.main()
