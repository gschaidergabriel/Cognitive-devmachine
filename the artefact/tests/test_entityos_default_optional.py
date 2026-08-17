import json
from pathlib import Path

from clayverse.service import _entityos_config

ROOT = Path(__file__).resolve().parents[1]


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


def test_manifest_cannot_reintroduce_mandatory_entityos_into_baseline():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["entityos_role"].startswith("optional ")
    assert "baseline may omit EntityOS" in manifest["entityos_transport"]
    assert "baseline may omit EntityOS" in manifest["entityos_admission"]
    assert "staged bytes are mandatory and verified" not in manifest["entityos_admission"]
    assert any(
        "where EntityOS is deliberately admitted" in gate
        for gate in manifest["requires_for_final_pass"]
    )
