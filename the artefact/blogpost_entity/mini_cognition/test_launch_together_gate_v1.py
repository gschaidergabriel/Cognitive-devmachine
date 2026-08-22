#!/usr/bin/env python3
"""Offline deterministic regressions for Together BYOM admission helpers.

These tests deliberately do not call Together and do not create a job. They prove only
local fail-closed template/revision behavior. API compatibility remains a separate gate.
"""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
MODULE_PATH=HERE/"launch_together_v1.py"
spec=importlib.util.spec_from_file_location("claycog_launch_together_v1",MODULE_PATH)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def expect_exit(fn, contains):
    try:
        fn()
    except SystemExit as exc:
        assert contains in str(exc), (contains,str(exc))
        return
    raise AssertionError(f"expected SystemExit containing {contains!r}")


def main():
    # No implicit template: public documentation currently exposes no admitted Qwen2/Qwen2.5 base.
    expect_exit(lambda: mod.resolve_template(""),"TOGETHER_TEMPLATE_BLOCKED")

    # The tempting currently documented Qwen3.5-0.8B substitution must fail before network use.
    expect_exit(lambda: mod.resolve_template("Qwen/Qwen3.5-0.8B"),"ARCHITECTURE_ABORT")

    # A caller-supplied Qwen2-family name may proceed only to the later authenticated model_limits gate.
    candidate="Qwen/Qwen2.5-7B-Instruct-Turbo"
    assert mod.resolve_template(candidate)==candidate

    # Known target checkpoints are immutable at the campaign boundary.
    assert mod.resolve_revision("Qwen/Qwen2.5-0.5B","")=="285c998059f3e217fe1f05e241d55b5c5eef5bd3"
    assert mod.resolve_revision("Qwen/Qwen2.5-0.5B-Instruct","")=="7ae557604adf67be50417f59c2c2f167def9a775"

    # Unknown replacement checkpoints need an explicit immutable revision rather than mutable HF main.
    expect_exit(lambda: mod.resolve_revision("example/unknown", ""),"HF_REVISION_REQUIRED")
    assert mod.resolve_revision("example/unknown","deadbeef")=="deadbeef"

    source=MODULE_PATH.read_text()
    assert "hf_model_revision=hf_revision" in source
    assert 'CLAYCOG_TOGETHER_TEMPLATE","").strip()' in source
    assert '"BYOM_UNPROVEN_PRICE_ENDPOINT_HAS_NO_FROM_HF_MODEL"' in source
    print("PASS test_launch_together_gate_v1")


if __name__=="__main__": main()
