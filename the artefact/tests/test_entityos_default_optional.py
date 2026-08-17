import json
from pathlib import Path

from clayverse.service import _entityos_config

ROOT = Path(__file__).resolve().parents[1]


def test_entityos_is_optional_by_default_for_single_container_development_baseline(monkeypatch):
    for name in (
        "CLAYVERSE_REQUIRE_ENTITYOS",
        "CLAYVERSE_ENTITYOS_PATH",
        "CLAYVERSE_ENTITYOS_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)
    bridge, status = _entityos_config()
    assert bridge is None
    assert status == {
        "staged": False,
        "verified": False,
        "execution_enabled": False,
    }


def test_manifest_allows_tokenless_development_baseline_but_requires_entityos_for_final_pass():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert "development/baseline builds may omit" in manifest["entityos_role"]
    assert "can never receive whole-product PASS" in manifest["entityos_transport"]
    assert "final acceptance requires" in manifest["entityos_transport"]
    assert "final accepted image requires" in manifest["entityos_admission"]
    assert any(
        "final accepted image contains the complete accepted EntityOS" in gate
        for gate in manifest["requires_for_final_pass"]
    )
    assert any(
        "accepted complete EntityOS embedded image runtime" in gate
        for gate in manifest["requires_for_final_pass"]
    )
