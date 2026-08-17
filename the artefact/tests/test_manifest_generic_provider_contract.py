import json
from pathlib import Path


def test_manifest_does_not_restore_unique_mandatory_mistral_provider():
    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "manifest.json").read_text(encoding="utf-8")
    )
    rendered = json.dumps(manifest, ensure_ascii=False, sort_keys=True).lower()

    superseded_unique_mistral_claims = (
        "mandatory final test-of-tests token/api inference path",
        "mistral is the mandatory token/api inference-only provider",
        "mandatory final test-of-tests provider is mistral",
    )
    for claim in superseded_unique_mistral_claims:
        assert claim not in rendered

    assert "provider-agnostic" in rendered or "provider-generic" in rendered
    assert "mistral" in rendered
    assert "first" in rendered or "profile" in rendered
