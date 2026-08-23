from pathlib import Path

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def test_neutral_db_initializes_before_db_resident_profile_read():
    init = SRC.index('phase("pipeline_init"')
    profile = SRC.index('effect("pipeline_profile_read"')
    state = SRC.index('phase("pipeline_state_read"')

    assert init < profile < state
    assert SRC.count('phase("pipeline_init"') == 1
    assert 'effect("profile_load"' not in SRC
    assert 'effect("provider_chat_json"' not in SRC


def test_fresh_db_boot_does_not_require_application_profile_to_initialize_schema():
    init_call = 'phase("pipeline_init",entity_db,source_db,map_new(),map_new(),map_new())'
    assert init_call in SRC


def test_cognitive_fabric_is_mandatory_before_inference_and_carries_receipt_identity():
    prompt = SRC.index('phase("pipeline_build_prompt"')
    fabric = SRC.index('phase("pipeline_cognitive_fabric_admit"')
    infer = SRC.index('effect("inference_generate"')
    gate = SRC.index('phase("pipeline_gate"')

    assert prompt < fabric < infer < gate
    assert SRC.count('phase("pipeline_cognitive_fabric_admit"') == 1
    assert 'map_set(infer,"inference",admitted.inference)' in SRC
    assert 'map_set(infer,"system",admitted.system)' in SRC
    assert 'map_set(infer,"user",admitted.user)' in SRC
    assert 'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)' in SRC
    assert 'map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in SRC
    assert 'map_set(gate_data,"cognitive_fabric",admitted)' in SRC
    assert 'map_set(commit_data,"cognitive_fabric",admitted)' in SRC
    assert 'map_set(infer,"inference",profile.inference)' not in SRC
    assert 'map_set(infer,"system",prompt.system)' not in SRC
    assert 'map_set(infer,"user",prompt.user)' not in SRC
