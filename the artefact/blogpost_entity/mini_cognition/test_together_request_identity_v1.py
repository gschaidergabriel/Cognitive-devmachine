#!/usr/bin/env python3
import os
import launch_together_v1 as m


def main():
    base_model,base_rev=m.resolve_hf_checkpoint(False)
    assert base_model==m.PRIMARY_MODEL
    assert base_rev==m.PRIMARY_REVISION
    inst_model,inst_rev=m.resolve_hf_checkpoint(True)
    assert inst_model==m.INSTRUCT_MODEL
    assert inst_rev==m.INSTRUCT_REVISION

    core=m.request_core("file-train","file-valid",base_model,base_rev)
    est=m.estimate_kwargs(core)
    create=m.create_kwargs(core)
    assert est==core
    for key,value in core.items():
        assert create[key]==value, (key,create.get(key),value)
    assert core["from_hf_model"]==m.PRIMARY_MODEL
    assert core["hf_model_revision"]==m.PRIMARY_REVISION
    assert core["training_type"]=={"type":"Full"}
    assert core["training_method"]=={"method":"sft","train_on_inputs":"auto"}
    assert core["random_seed"]==20260822

    class Meta:
        training_file="file-train"
        validation_file="file-valid"
        model=m.TEMPLATE
        from_hf_model=m.PRIMARY_MODEL
        hf_model_revision=m.PRIMARY_REVISION
    assert m.verify_created_job(Meta(),core)=={}
    Meta.hf_model_revision="deadbeef"
    mismatch=m.verify_created_job(Meta(),core)
    assert set(mismatch)=={"hf_model_revision"}

    old_model=os.environ.get("CLAYCOG_HF_MODEL")
    old_rev=os.environ.get("CLAYCOG_HF_REVISION")
    try:
        os.environ["CLAYCOG_HF_MODEL"]="example/custom-qwen2"
        os.environ.pop("CLAYCOG_HF_REVISION",None)
        try:
            m.resolve_hf_checkpoint(False)
        except SystemExit as exc:
            assert "requires explicit" in str(exc)
        else:
            raise AssertionError("unpinned custom model was accepted")
    finally:
        if old_model is None: os.environ.pop("CLAYCOG_HF_MODEL",None)
        else: os.environ["CLAYCOG_HF_MODEL"]=old_model
        if old_rev is None: os.environ.pop("CLAYCOG_HF_REVISION",None)
        else: os.environ["CLAYCOG_HF_REVISION"]=old_rev

    print("PASS together request identity/parity")


if __name__=="__main__":
    main()
