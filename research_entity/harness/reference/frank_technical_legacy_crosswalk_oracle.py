#!/usr/bin/env python3
"""Cross-check recovered historical technical modules against NEW CLAY-FRANK module surfaces.

Sandbox-reference oracle. Technical service/process identity stays separate from cognitive organ
identity. A service boundary may dissolve only if its successor component reaches at least one
transitional module that itself has a final single-module collapse mapping.
"""
from __future__ import annotations
import json
from frank_final_collapse_oracle import MODULES, COLLAPSE

TECHNICAL = {
'aicore-core':'workspace_core','aicore-router':'deliberation','aicore-micro-llm':'deliberation',
'aicore-llama3-gpu':'deliberation','aicore-chat-llm':'deliberation','llm-guard':'safety_recovery',
'aicore-whisper-gpu':'perception_gate','aicore-modeld':'deliberation','aicore-toolboxd':'agency_tools',
'aicore-desktopd':'agency_tools','aicore-webd':'agency_tools','aicore-ingestd':'perception_gate',
'aicore-consciousness':'workspace_core','aicore-genesis':'deliberation','aicore-genesis-watchdog':'safety_recovery',
'aicore-invariants':'safety_recovery','aicore-asrs':'safety_recovery','aicore-rooms':'agency_tools',
'aicore-gaming-mode':'perception_gate','aicore-quantum-reflector':'deliberation','aura-headless':'agency_tools','aura-analyzer':'agency_tools','aicore-swarm':'agency_tools',
'aicore-dream':'memory_identity','aicore-dream-watchdog':'safety_recovery','aicore-dream-watchdog-meta':'safety_recovery',
'aicore-fas':'agency_tools','aicore-therapist':'agency_tools','aicore-atlas':'agency_tools','aicore-muse':'agency_tools',
'aicore-mirror':'memory_identity','aicore-ui-webui':'workspace_core','aicore-notruf':'safety_recovery',
'aicore-whisper-cpu':'perception_gate','aicore-zustand-auto':'memory_identity','aicore-zustand-snapshot':'memory_identity',
}

COMPONENT_TO_TRANSITIONAL = {
'workspace_core': ('frank_workspace','frank_runtime','frank_attention_schema'),
'deliberation': ('frank_hyperposition','frank_grt','frank_prospection','frank_causal_credit'),
'agency_tools': ('frank_api_fabric','frank_effects','frank_device','frank_hive'),
'memory_identity': ('frank_memory','frank_instance_memory','frank_self_model','frank_entity','frank_state'),
'perception_gate': ('frank_device','frank_world','frank_self_observation','frank_attention_schema'),
'safety_recovery': ('frank_security','frank_effects','frank_state','frank_release'),
}

def validate():
    assert len(TECHNICAL)==36
    components=set(TECHNICAL.values())
    assert components==set(COMPONENT_TO_TRANSITIONAL), (components,set(COMPONENT_TO_TRANSITIONAL))
    module_set=set(MODULES)
    for legacy, component in TECHNICAL.items():
        targets=COMPONENT_TO_TRANSITIONAL[component]
        assert targets, legacy
        assert set(targets) <= module_set, (legacy, component, targets)
        assert all(t in COLLAPSE and COLLAPSE[t] for t in targets), (legacy, component)
    return {
      'status':'PASS',
      'historical_technical_modules':len(TECHNICAL),
      'successor_components':len(COMPONENT_TO_TRANSITIONAL),
      'transitional_modules':len(MODULES),
      'all_technical_modules_reach_final_single_module':True,
      'technical_inventory_separate_from_cognitive_organ_inventory':True,
    }

if __name__=='__main__':
    print(json.dumps(validate(),sort_keys=True))
