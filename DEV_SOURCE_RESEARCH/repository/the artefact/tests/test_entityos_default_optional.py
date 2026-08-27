from clayverse.service import _entityos_config


def test_entityos_is_optional_by_default_for_single_container_baseline(monkeypatch):
    for name in (
        "CLAYVERSE_REQUIRE_ENTITYOS",
        "CLAYVERSE_ENTITYOS_PATH",
        "CLAYVERSE_ENTITYOS_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)
    bridge, status = _entityos_config()
    assert bridge is None
    assert status == {"required": False, "bound": False}
