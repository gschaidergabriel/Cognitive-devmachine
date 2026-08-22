#!/usr/bin/env python3
"""Dependency-free falsifier for the Together BYOM static compatibility gate.

This intentionally replays the previously configured 7B template against the required
0.5B BYOM model. It must be rejected before any Together client/network construction.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAUNCHER=HERE/"launch_together_v1.py"

# The launcher imports Together at module import time. Supply a sentinel module so this
# test has zero API/network dependency. Instantiating the sentinel is a hard failure.
fake=types.ModuleType("together")
class NetworkMustNotStart:
    def __init__(self,*args,**kwargs):
        raise AssertionError("Together client/network construction reached during static gate test")
fake.Together=NetworkMustNotStart
sys.modules["together"]=fake

spec=importlib.util.spec_from_file_location("claycog_launch_together_v1",LAUNCHER)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def expect_abort(template,needle):
    try:
        mod.static_byom_template_gate("Qwen/Qwen2.5-0.5B",template)
    except SystemExit as exc:
        msg=str(exc)
        assert needle in msg,(needle,msg)
        return msg
    raise AssertionError(f"expected fail-closed rejection for {template}")


def main():
    old=expect_abort("Qwen/Qwen2.5-7B-Instruct-Turbo","BYOM_SIZE_ABORT")
    exact=mod.static_byom_template_gate("Qwen/Qwen2.5-0.5B","Qwen/Qwen2.5-0.5B")
    instruct=mod.static_byom_template_gate("Qwen/Qwen2.5-0.5B-Instruct","Qwen/Qwen2.5-0.5B-Instruct")
    wrong_arch=expect_abort("meta-llama/Llama-3.2-1B","BYOM_ARCH_ABORT")
    report={
        "schema":"claycog-byom-static-gate-test/v1",
        "unusual_experiment":"BYOM_TEMPLATE_SIZE_MISMATCH_TRAP",
        "old_7b_template":"REJECTED_BEFORE_NETWORK",
        "exact_05b_template":"STATIC_PAIR_ADMITTED_API_COMPATIBILITY_STILL_OPEN",
        "instruct_05b_template":"STATIC_PAIR_ADMITTED_API_COMPATIBILITY_STILL_OPEN",
        "wrong_architecture":"REJECTED_BEFORE_NETWORK",
        "network_constructor_called":False,
        "old_7b_detail":old,
        "wrong_arch_detail":wrong_arch,
        "exact_gate":exact,
        "instruct_gate":instruct,
    }
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
