#!/usr/bin/env python3
import importlib.util, os, tempfile, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_v1_identity", HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FineTuningFake:
    def __init__(self): self.jobs=[]
    def list(self): return types.SimpleNamespace(data=list(self.jobs))

class ClientFake:
    def __init__(self): self.fine_tuning=FineTuningFake()

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name)
        self.old_paths=(mod.TRAIN,mod.VALID)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old_paths
        self.tmp.cleanup()

    def test_default_hf_revisions_are_exact_and_pinned(self):
        model,revision=mod.resolve_hf_checkpoint(False)
        self.assertEqual(mod.PRIMARY_MODEL,model)
        self.assertEqual(mod.PRIMARY_REVISION,revision)
        model,revision=mod.resolve_hf_checkpoint(True)
        self.assertEqual(mod.INSTRUCT_MODEL,model)
        self.assertEqual(mod.INSTRUCT_REVISION,revision)
        self.assertEqual(40,len(revision))

    def test_campaign_fingerprint_binds_hf_revision(self):
        a=mod.campaign_fingerprint(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION)
        b=mod.campaign_fingerprint(mod.PRIMARY_MODEL,"1"*40)
        self.assertNotEqual(a,b)
        desc=mod.campaign_descriptor(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION)
        self.assertEqual(mod.PRIMARY_REVISION,desc["hf_model_revision"])
        self.assertEqual(mod.RANDOM_SEED,desc["random_seed"])
        self.assertEqual("claycog-05b-together-campaign/v2",desc["schema"])

    def test_custom_model_requires_explicit_revision(self):
        old_model=mod.HF_MODEL
        old_env=os.environ.get("CLAYCOG_HF_REVISION")
        try:
            mod.HF_MODEL="example/custom-qwen2"
            os.environ.pop("CLAYCOG_HF_REVISION",None)
            with self.assertRaises(SystemExit): mod.resolve_hf_checkpoint(False)
        finally:
            mod.HF_MODEL=old_model
            if old_env is None: os.environ.pop("CLAYCOG_HF_REVISION",None)
            else: os.environ["CLAYCOG_HF_REVISION"]=old_env

    def test_duplicate_guard_can_fence_revision(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-other-revision",status="running",model=mod.TEMPLATE,from_hf_model=mod.PRIMARY_MODEL,
            hf_model_revision="2"*40,model_output_name="acct/output-"+suffix,
        ))
        self.assertEqual([],mod.matching_campaign_jobs(c,mod.PRIMARY_MODEL,mod.TEMPLATE,suffix,mod.PRIMARY_REVISION))
        c.fine_tuning.jobs[0].hf_model_revision=mod.PRIMARY_REVISION
        with self.assertRaises(SystemExit):
            mod.assert_no_duplicate_campaign(c,mod.PRIMARY_MODEL,mod.TEMPLATE,suffix,mod.PRIMARY_REVISION)

    def test_created_job_identity_mismatch_is_explicit(self):
        core={
            "training_file":"file-train","validation_file":"file-valid","model":mod.TEMPLATE,
            "from_hf_model":mod.PRIMARY_MODEL,"hf_model_revision":mod.PRIMARY_REVISION,
            "n_epochs":mod.EPOCHS,"n_evals":mod.EVALS,"random_seed":mod.RANDOM_SEED,
        }
        meta=types.SimpleNamespace(**core)
        self.assertEqual({},mod.created_job_identity_mismatches(meta,core))
        meta.hf_model_revision="deadbeef"
        self.assertEqual({"hf_model_revision"},set(mod.created_job_identity_mismatches(meta,core)))

if __name__=="__main__": unittest.main(verbosity=2)
