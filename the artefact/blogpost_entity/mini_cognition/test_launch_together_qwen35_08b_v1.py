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
        self.assertEqual(m.MODEL,"Qwen/Qwen3.5-0.8B");m.validate_static_contract();d=m.campaign_descriptor();self.assertEqual(d["schema"],"claycog-08b-together-direct-campaign/v3");self.assertEqual(d["training_type"],{"type":"Full"});self.assertEqual(d["random_seed"],3407);self.assertEqual(len(d["source_identity"]["repo_head"]),40);self.assertEqual(set(d["source_identity"]["files_sha256"]),{"launcher","generator","validator"});raw=json.dumps(d);self.assertNotIn("from_hf_model",raw);self.assertNotIn("template_model",raw)
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
    def test_fingerprint_binds_source_identity(self):
        original=m.source_identity
        a={"repo_head":"1"*40,"files_sha256":{"launcher":"a"*64,"generator":"b"*64,"validator":"c"*64}}
        b={"repo_head":"2"*40,"files_sha256":{"launcher":"a"*64,"generator":"b"*64,"validator":"c"*64}}
        try:
            m.source_identity=lambda:a;fa=m.campaign_fingerprint()
            m.source_identity=lambda:b;fb=m.campaign_fingerprint()
        finally:m.source_identity=original
        self.assertNotEqual(fa,fb)
    def test_source_identity_binds_real_bytes(self):
        s=m.source_identity();self.assertEqual(s["files_sha256"]["launcher"],m.sha256_file(m.SOURCE_IDENTITY_PATHS["launcher"]));self.assertEqual(s["files_sha256"]["generator"],m.sha256_file(m.SOURCE_IDENTITY_PATHS["generator"]));self.assertEqual(s["files_sha256"]["validator"],m.sha256_file(m.SOURCE_IDENTITY_PATHS["validator"]));self.assertEqual(m.SOURCE_IDENTITY_PATHS["validator"],m.V2_VALIDATOR)
    def test_duplicate_guard(self):
        s="claycog08b-v3-dead";c=Client([{"id":"j","status":"running","model":m.MODEL,"model_output_name":"x"+s}])
        with self.assertRaises(SystemExit):m.assert_no_duplicate_campaign(c,s)
    def test_confirmation_and_private_intent(self):
        fp="a"*64
        with self.assertRaises(SystemExit):m.require_create_confirmation(fp)
        os.environ[m.CREATE_CONFIRM_ENV]=fp;m.require_create_confirmation(fp)
        with tempfile.TemporaryDirectory() as td:
            os.environ[m.CREATE_LEDGER_DIR_ENV]=td;fp=m.campaign_fingerprint();p=m.arm_create_intent(fp,m.campaign_suffix(fp));self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600);self.assertEqual(m.read_create_ledger(fp)["campaign"]["training_type"],{"type":"Full"});self.assertIn("source_identity",m.read_create_ledger(fp)["campaign"])
    def test_created_job_identity_mismatch_detection(self):
        expected={"training_file":"t","validation_file":"v","model":m.MODEL,"n_epochs":3,"n_evals":2,"random_seed":3407}
        good=types.SimpleNamespace(**expected);self.assertEqual(m.created_job_identity_mismatches(good,expected),{})
        bad=types.SimpleNamespace(**{**expected,"random_seed":9});mm=m.created_job_identity_mismatches(bad,expected);self.assertEqual(mm["random_seed"],{"expected":3407,"observed":9})
    def test_zero_retry(self):
        TogetherCtor.last=None;m.new_zero_retry_create_client(TogetherCtor);self.assertEqual(TogetherCtor.last,{"max_retries":0})
if __name__=="__main__":unittest.main()
