#!/usr/bin/env python3
import importlib.util, os, tempfile, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_revision_seed", HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class RevisionSeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name)
        self.old_paths=(mod.TRAIN,mod.VALID)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old_paths
        self.tmp.cleanup()

    def test_default_checkpoint_revisions_are_exact_and_pinned(self):
        model,rev=mod.resolve_hf_checkpoint(False)
        self.assertEqual(mod.PRIMARY_MODEL,model)
        self.assertEqual(mod.PRIMARY_REVISION,rev)
        self.assertEqual(40,len(rev))
        model,rev=mod.resolve_hf_checkpoint(True)
        self.assertEqual(mod.INSTRUCT_MODEL,model)
        self.assertEqual(mod.INSTRUCT_REVISION,rev)
        self.assertEqual(40,len(rev))

    def test_campaign_fingerprint_changes_when_revision_changes(self):
        a=mod.campaign_fingerprint(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION)
        b=mod.campaign_fingerprint(mod.PRIMARY_MODEL,"1"*40)
        self.assertNotEqual(a,b)
        d=mod.campaign_descriptor(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION)
        self.assertEqual("claycog-05b-together-campaign/v2",d["schema"])
        self.assertEqual(mod.PRIMARY_REVISION,d["hf_model_revision"])
        self.assertEqual(mod.RANDOM_SEED,d["random_seed"])
        self.assertEqual(mod.LEARNING_RATE,d["learning_rate"])
        self.assertEqual(mod.WARMUP_RATIO,d["warmup_ratio"])

    def test_custom_model_requires_explicit_exact_revision(self):
        old=mod.HF_MODEL; old_rev=os.environ.get("CLAYCOG_HF_REVISION")
        try:
            mod.HF_MODEL="example/custom-qwen2"
            os.environ.pop("CLAYCOG_HF_REVISION",None)
            with self.assertRaises(SystemExit): mod.resolve_hf_checkpoint(False)
            os.environ["CLAYCOG_HF_REVISION"]="short"
            with self.assertRaises(SystemExit): mod.resolve_hf_checkpoint(False)
            os.environ["CLAYCOG_HF_REVISION"]="a"*40
            self.assertEqual(("example/custom-qwen2","a"*40),mod.resolve_hf_checkpoint(False))
        finally:
            mod.HF_MODEL=old
            if old_rev is None: os.environ.pop("CLAYCOG_HF_REVISION",None)
            else: os.environ["CLAYCOG_HF_REVISION"]=old_rev

    def test_create_ledger_binds_revision_and_seed(self):
        os.environ[mod.CREATE_LEDGER_DIR_ENV]=str(Path(self.tmp.name)/"ledger")
        try:
            fp=mod.campaign_fingerprint(mod.PRIMARY_MODEL,mod.PRIMARY_REVISION)
            suffix=mod.campaign_suffix(fp)
            path=mod.arm_create_intent(fp,mod.PRIMARY_MODEL,suffix,mod.PRIMARY_REVISION)
            payload=mod.read_create_ledger(fp)
            campaign=payload["campaign"]
            self.assertEqual("claycog-together-create-intent/v2",payload["schema"])
            self.assertEqual(mod.PRIMARY_REVISION,campaign["hf_model_revision"])
            self.assertEqual(mod.RANDOM_SEED,campaign["random_seed"])
            self.assertEqual(fp,payload["fingerprint"])
        finally:
            os.environ.pop(mod.CREATE_LEDGER_DIR_ENV,None)

    def test_provider_job_identity_mismatch_is_fail_closed_data(self):
        expected={
            "training_file":"train-id","validation_file":"valid-id","model":mod.TEMPLATE,
            "from_hf_model":mod.PRIMARY_MODEL,"hf_model_revision":mod.PRIMARY_REVISION,
            "n_epochs":mod.EPOCHS,"n_evals":mod.EVALS,"random_seed":mod.RANDOM_SEED,
        }
        meta=types.SimpleNamespace(**expected)
        self.assertEqual({},mod.created_job_identity_mismatches(meta,expected))
        meta.hf_model_revision="b"*40
        mismatches=mod.created_job_identity_mismatches(meta,expected)
        self.assertEqual({"hf_model_revision"},set(mismatches))
        self.assertEqual(mod.PRIMARY_REVISION,mismatches["hf_model_revision"]["expected"])

if __name__=="__main__": unittest.main(verbosity=2)
