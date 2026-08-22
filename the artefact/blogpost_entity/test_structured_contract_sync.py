from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_structured_contract_sync.py"
spec = importlib.util.spec_from_file_location("check_structured_contract_sync", CHECKER)
assert spec and spec.loader
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def test_dead_string_effect_names_cannot_spoof_runtime_support():
    runtime = '''
class Runtime:
    def __init__(self):
        self.allowed_effects = {"pipeline_init"}

    def effect(self, kind, payload=None):
        # Decoys that fooled the old substring-based checker:
        note = "pipeline_profile_read inference_generate"
        if kind == "pipeline_init":
            return {"ok": True}
        raise RuntimeError(note)
'''
    allowed, dispatched = sync.extract_runtime_effect_contract(runtime)
    assert allowed == {"pipeline_init"}
    assert dispatched == {"pipeline_init"}
    assert "pipeline_profile_read" not in allowed | dispatched
    assert "inference_generate" not in allowed | dispatched


def test_clay_surface_includes_literal_phase_and_effect_calls():
    source = '''
fn run()->Map {
  let a = phase("pipeline_init","x","y",map_new(),map_new(),map_new())
  let b = effect("pipeline_profile_read",map_new())
  let c = effect("inference_generate",map_new())
  return c
}
'''
    assert sync.extract_clay_effect_surface(source) == {
        "pipeline_init",
        "pipeline_profile_read",
        "inference_generate",
    }
