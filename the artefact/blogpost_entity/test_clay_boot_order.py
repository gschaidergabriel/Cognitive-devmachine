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
